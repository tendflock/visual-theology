# Native API Expansion: Navigation Index, Article Titles, and Text Search

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace our slow Python heuristics for finding commentary sections (~35s per commentary) with native Logos APIs that provide instant reference-to-article mapping, proper article titles, and in-resource text search.

**Architecture:** Add 8 new P/Invoke declarations to LogosReader's Program.cs, expose them as new batch commands (`navindex`, `article-title`, `find-text`, `position`), integrate into study.py's commentary finder and logos_batch.py to replace the 35-second scan-60-articles approach with sub-second lookups.

**Tech Stack:** C# (.NET 8), P/Invoke to libSinaiInterop.dylib, Python 3 (study.py, logos_batch.py)

---

## File Structure

| File | Responsibility | Changes |
|------|---------------|---------|
| `tools/LogosReader/Program.cs` | C# P/Invoke to native Logos APIs | Add 8 new P/Invoke decls, 4 new commands |
| `tools/logos_batch.py` | Python wrapper for batch reader subprocess | Add 3 new methods |
| `tools/study.py` | Orchestrator / commentary finder | Replace heuristic with navindex lookup |
| `tools/logos_cache.py` | SQLite cache | Add navindex cache table |

## Background: What These Native APIs Do

### Navigation Index (`ExportNavigationIndex` + `ManagedNavigationIndexVisitor`)
Every Logos resource has a **navigation index** — a map of all reference points in the text. For a Romans commentary, this contains entries like:
- `OnReferenceItem("bible.66.1.16", article=1278, offset=0)` — "Romans 1:16 is at article 1278"
- `OnTopicItem("Righteousness", "Righteousness of God", article=1278, offset=500)`

This is exactly what we need to instantly find which article covers Romans 1:16-17, replacing our 35-second scanning approach.

### ManagedNavigationIndexVisitor Constructor
```
ManagedNavigationIndexVisitor(
    bool (*onReferenceItem)(char16_t const* reference, unsigned int article, unsigned int offset),
    bool (*onTopicItem)(char16_t const* key, char16_t const* name, unsigned int article, unsigned int offset)
)
```

### GetArticleTitle
```
GetArticleTitle(CTitle*, ResourceVolumeBase*, unsigned int articleNum, string& title)
```
Returns proper article titles — fixes our empty TOC labels.

### DoFindText
```
CTitle_DoFindText(CTitle*, MarshalTextRange const* startRange, string const& query, bool caseSensitive, bool wholeWord, bool (*)() cancelCallback)
```
Search for text within a resource.

---

## Chunk 1: Navigation Index in LogosReader

### Task 1: Add Navigation Index P/Invoke Declarations

**Files:**
- Modify: `tools/LogosReader/Program.cs:103-121` (after existing TOC declarations)

- [ ] **Step 1: Add the ManagedNavigationIndexVisitor P/Invoke declarations**

Add after the existing TOC function declarations (line ~121):

```csharp
    // Navigation index - maps Bible references to article positions
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    [return: MarshalAs(UnmanagedType.U1)]
    delegate bool NavIndexReferenceCallback(IntPtr reference, uint article, uint offset);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    [return: MarshalAs(UnmanagedType.U1)]
    delegate bool NavIndexTopicCallback(IntPtr key, IntPtr name, uint article, uint offset);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr ManagedNavigationIndexVisitor_New(
        IntPtr onReferenceItem,
        IntPtr onTopicItem);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void ManagedNavigationIndexVisitor_Delete(IntPtr visitor);

    // ResourceVolume - needed for ExportNavigationIndex
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_ResourceVolumeFromResource(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void SinaiInterop_ExportNavigationIndex(
        IntPtr title,
        IntPtr resourceVolume,
        IntPtr visitor);

    // Article title - gets proper title for an article (fixes empty TOC labels)
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void SinaiInterop_GetArticleTitle(
        IntPtr title,
        IntPtr resourceVolume,
        uint articleNum,
        [MarshalAs(UnmanagedType.LPWStr)] out string articleTitle);
```

- [ ] **Step 2: Build to verify declarations compile**

Run: `cd /Volumes/External/Logos4/tools/LogosReader && dotnet build 2>&1`
Expected: Build succeeded (warnings OK, no errors)

- [ ] **Step 3: Commit**

```bash
git add tools/LogosReader/Program.cs
git commit -m "feat: add P/Invoke decls for navigation index, article title"
```

### Task 2: Implement `navindex` Command

**Files:**
- Modify: `tools/LogosReader/Program.cs` (add command parsing + handler)

- [ ] **Step 1: Add `navindex` to CLI help text**

In the help text block (~line 272), add:

```csharp
Console.WriteLine("  LogosReader --navindex <file>                    Export navigation index (ref→article map)");
```

- [ ] **Step 2: Add command parsing for `--navindex`**

In the command parsing section (after `--toc` handling, ~line 315):

```csharp
else if (args[0] == "--navindex" && args.Length >= 2)
{
    mode = "navindex";
    resourceFile = args[1];
}
```

- [ ] **Step 3: Add the navindex case to the mode switch**

In the mode switch block (after the `toc` case), add:

```csharp
case "navindex":
    IntPtr resVol = SinaiInterop_ResourceVolumeFromResource(title);
    if (resVol == IntPtr.Zero)
    {
        Console.Error.WriteLine("[!] Could not get ResourceVolume");
        break;
    }
    Console.Error.WriteLine("[*] Exporting navigation index...");

    // Collect entries via callbacks
    var navRefEntries = new List<string>();
    var navTopicEntries = new List<string>();

    NavIndexReferenceCallback refCb = (IntPtr reference, uint article, uint offset) =>
    {
        string refStr = Marshal.PtrToStringUni(reference) ?? "";
        navRefEntries.Add($"REF\t{refStr}\t{article}\t{offset}");
        return true; // continue visiting
    };
    NavIndexTopicCallback topicCb = (IntPtr key, IntPtr name, uint article, uint offset) =>
    {
        string keyStr = Marshal.PtrToStringUni(key) ?? "";
        string nameStr = Marshal.PtrToStringUni(name) ?? "";
        navTopicEntries.Add($"TOPIC\t{keyStr}\t{nameStr}\t{article}\t{offset}");
        return true;
    };

    // Pin delegates to prevent GC during native call
    var refCbHandle = GCHandle.Alloc(refCb);
    var topicCbHandle = GCHandle.Alloc(topicCb);
    try
    {
        IntPtr visitor = ManagedNavigationIndexVisitor_New(
            Marshal.GetFunctionPointerForDelegate(refCb),
            Marshal.GetFunctionPointerForDelegate(topicCb));

        if (visitor != IntPtr.Zero)
        {
            SinaiInterop_ExportNavigationIndex(title, resVol, visitor);
            ManagedNavigationIndexVisitor_Delete(visitor);
        }
    }
    finally
    {
        refCbHandle.Free();
        topicCbHandle.Free();
    }

    // Output all entries as TSV
    foreach (var entry in navRefEntries)
        Console.WriteLine(entry);
    foreach (var entry in navTopicEntries)
        Console.WriteLine(entry);
    Console.Error.WriteLine($"[*] Navigation index: {navRefEntries.Count} references, {navTopicEntries.Count} topics");
    break;
```

- [ ] **Step 4: Build and test**

Run:
```bash
cd /Volumes/External/Logos4/tools/LogosReader && dotnet build 2>&1
```
Expected: Build succeeded

Then test with a commentary:
```bash
cd /Volumes/External/Logos4/tools/LogosReader && PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH" DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec" dotnet run -- --navindex SORHET66RO.logos4 2>/dev/null | head -20
```
Expected output: Lines like `REF\tbible.66.1.16\t1278\t0` showing reference→article mappings.

**If it crashes (SIGSEGV):** The `GetArticleTitle` or `ResourceVolumeFromResource` signature may need adjustment. Try removing the `SinaiInterop_GetArticleTitle` declaration and retest. The navindex is the critical path.

- [ ] **Step 5: Commit**

```bash
git add tools/LogosReader/Program.cs
git commit -m "feat: implement navindex command for reference→article mapping"
```

### Task 3: Implement `article-title` Command

**Files:**
- Modify: `tools/LogosReader/Program.cs`

- [ ] **Step 1: Add `article-title` to CLI help and command parsing**

Help text:
```csharp
Console.WriteLine("  LogosReader --article-title <file> <article#>    Get article title");
```

Command parsing:
```csharp
else if (args[0] == "--article-title" && args.Length >= 3)
{
    mode = "article-title";
    resourceFile = args[1];
    articleNum = int.Parse(args[2]);
}
```

- [ ] **Step 2: Add the article-title case**

```csharp
case "article-title":
    IntPtr artResVol = SinaiInterop_ResourceVolumeFromResource(title);
    if (artResVol != IntPtr.Zero)
    {
        SinaiInterop_GetArticleTitle(title, artResVol, (uint)articleNum, out string artTitle);
        Console.WriteLine(artTitle ?? "(no title)");
    }
    else
    {
        Console.Error.WriteLine("[!] Could not get ResourceVolume");
    }
    break;
```

- [ ] **Step 3: Build and test**

```bash
cd /Volumes/External/Logos4/tools/LogosReader && dotnet build && PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH" DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec" dotnet run -- --article-title SORHET66RO.logos4 1278 2>/dev/null
```
Expected: Something like "Propositio—1:16–17" (the actual title for CH3 article).

- [ ] **Step 4: Commit**

```bash
git add tools/LogosReader/Program.cs
git commit -m "feat: implement article-title command"
```

### Task 4: Add `navindex` and `article-title` to Batch Mode

**Files:**
- Modify: `tools/LogosReader/Program.cs` (batch mode command handler, ~line 930-950)

- [ ] **Step 1: Find the batch mode command handler section**

Look for the switch statement inside `RunBatchMode` that handles `read`, `list`, `toc`, etc.

- [ ] **Step 2: Add `navindex` batch command**

Add to the batch switch:

```csharp
case "navindex":
    if (parts.Length < 2)
    {
        Console.Error.WriteLine("[!] navindex requires: navindex <file>");
        break;
    }
    mode = "navindex";
    batchFile = parts[1];
    break;
```

Then add the navindex execution in the mode execution section (same logic as standalone, but using the batch-opened title).

**Note:** The batch mode may need to open a ResourceVolume, which requires keeping the title handle. Check if the batch mode's existing title-loading code exposes the right handle.

- [ ] **Step 3: Add `article-title` batch command**

```csharp
case "article-title":
    if (parts.Length < 3)
    {
        Console.Error.WriteLine("[!] article-title requires: article-title <file> <article#>");
        break;
    }
    mode = "article-title";
    batchFile = parts[1];
    articleNum = int.Parse(parts[2]);
    break;
```

- [ ] **Step 4: Build, test in batch mode**

```bash
echo -e "navindex SORHET66RO.logos4\narticle-title SORHET66RO.logos4 1278\n" | cd /Volumes/External/Logos4/tools/LogosReader && PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH" DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec" dotnet run -- --batch 2>/dev/null | head -20
```

- [ ] **Step 5: Commit**

```bash
git add tools/LogosReader/Program.cs
git commit -m "feat: add navindex and article-title to batch mode"
```

---

## Chunk 2: Python Integration

### Task 5: Add navindex to logos_batch.py

**Files:**
- Modify: `tools/logos_batch.py`

- [ ] **Step 1: Add `get_navigation_index` method to LogosBatchReader**

```python
def get_navigation_index(self, resource_file):
    """Get the navigation index (reference→article mapping) for a resource.

    Returns dict with keys:
        'references': list of {'ref': str, 'article': int, 'offset': int}
        'topics': list of {'key': str, 'name': str, 'article': int, 'offset': int}
    """
    stdout = self._send_command(f"navindex {resource_file}")
    refs = []
    topics = []
    for line in stdout.split("\n"):
        parts = line.split("\t")
        if len(parts) >= 4 and parts[0] == "REF":
            refs.append({"ref": parts[1], "article": int(parts[2]), "offset": int(parts[3])})
        elif len(parts) >= 5 and parts[0] == "TOPIC":
            topics.append({"key": parts[1], "name": parts[2], "article": int(parts[3]), "offset": int(parts[4])})
    return {"references": refs, "topics": topics}
```

- [ ] **Step 2: Add `get_article_title` method**

```python
def get_article_title(self, resource_file, article_num):
    """Get the title of an article."""
    stdout = self._send_command(f"article-title {resource_file} {article_num}")
    return stdout.strip() if stdout else None
```

- [ ] **Step 3: Test**

```bash
python3 -c "
from tools.logos_batch import LogosBatchReader
reader = LogosBatchReader()
nav = reader.get_navigation_index('SORHET66RO.logos4')
print(f'References: {len(nav[\"references\"])}')
print(f'Topics: {len(nav[\"topics\"])}')
# Find Romans 1:16
for r in nav['references']:
    if 'bible.66.1.16' in r['ref'] or 'bible.66.1.17' in r['ref']:
        print(f'  {r}')
reader.close()
"
```
Expected: References list with entries mapping `bible.66.1.16` to an article number.

- [ ] **Step 4: Commit**

```bash
git add tools/logos_batch.py
git commit -m "feat: add navindex and article-title to batch reader"
```

### Task 6: Add Navigation Index Cache

**Files:**
- Modify: `tools/logos_cache.py`

- [ ] **Step 1: Add `navindex_cache` table to schema**

In `_create_tables()`, add:

```python
CREATE TABLE IF NOT EXISTS navindex_cache (
    resource_file TEXT,
    entry_type TEXT,        -- 'REF' or 'TOPIC'
    ref_key TEXT,           -- reference string or topic key
    article_num INTEGER,
    offset INTEGER,
    name TEXT,              -- topic name (null for REF)
    cached_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_navindex_ref
    ON navindex_cache(resource_file, ref_key);
```

- [ ] **Step 2: Add cache methods**

```python
def get_navindex(self, resource_file):
    """Get cached navigation index for a resource, or None."""
    rows = self._conn.execute(
        "SELECT entry_type, ref_key, article_num, offset, name FROM navindex_cache WHERE resource_file = ?",
        (resource_file,),
    ).fetchall()
    if not rows:
        return None
    refs = []
    topics = []
    for r in rows:
        if r[0] == 'REF':
            refs.append({"ref": r[1], "article": r[2], "offset": r[3]})
        else:
            topics.append({"key": r[1], "name": r[4], "article": r[2], "offset": r[3]})
    return {"references": refs, "topics": topics}

def put_navindex(self, resource_file, references, topics):
    """Cache a navigation index."""
    self._conn.execute("DELETE FROM navindex_cache WHERE resource_file = ?", (resource_file,))
    for r in references:
        self._conn.execute(
            "INSERT INTO navindex_cache (resource_file, entry_type, ref_key, article_num, offset) VALUES (?, 'REF', ?, ?, ?)",
            (resource_file, r["ref"], r["article"], r["offset"]),
        )
    for t in topics:
        self._conn.execute(
            "INSERT INTO navindex_cache (resource_file, entry_type, ref_key, article_num, offset, name) VALUES (?, 'TOPIC', ?, ?, ?, ?)",
            (resource_file, t["key"], t["article"], t["offset"], t.get("name")),
        )
    self._conn.commit()

def find_article_for_reference(self, resource_file, bible_ref):
    """Find which article contains a Bible reference.

    bible_ref: e.g. 'bible.66.1.16' for Romans 1:16
    Returns (article_num, offset) or None.
    """
    # Try exact match first
    row = self._conn.execute(
        "SELECT article_num, offset FROM navindex_cache WHERE resource_file = ? AND ref_key = ?",
        (resource_file, bible_ref),
    ).fetchone()
    if row:
        return (row[0], row[1])
    # Try prefix match (chapter level)
    chapter_ref = '.'.join(bible_ref.split('.')[:4])  # bible.66.1
    row = self._conn.execute(
        "SELECT article_num, offset FROM navindex_cache WHERE resource_file = ? AND ref_key LIKE ? ORDER BY ref_key LIMIT 1",
        (resource_file, chapter_ref + '%'),
    ).fetchone()
    if row:
        return (row[0], row[1])
    return None
```

- [ ] **Step 3: Commit**

```bash
git add tools/logos_cache.py
git commit -m "feat: add navigation index cache with reference lookup"
```

### Task 7: Replace Commentary Heuristic with Navigation Index

**Files:**
- Modify: `tools/study.py` (`find_commentary_section` function)

This is the critical integration step. Replace the 35-second scanning approach.

- [ ] **Step 1: Add `_find_via_navindex` function**

Add before `find_commentary_section`:

```python
def _find_via_navindex(resource_file, ref):
    """Find commentary section using the native navigation index.

    The navigation index maps Bible references (e.g. 'bible.66.1.16')
    to article numbers. This is instant compared to scanning article text.

    Returns article text string, or None if navindex unavailable.
    """
    cache = _get_logos_cache()
    book_num = ref["book"]
    chapter = ref["chapter"]
    verse_start = ref["verse_start"]

    # Build Logos reference format: bible.{book}.{chapter}.{verse}
    if verse_start:
        bible_ref = f"bible.{book_num}.{chapter}.{verse_start}"
    else:
        bible_ref = f"bible.{book_num}.{chapter}"

    # Check cache first
    if cache:
        result = cache.find_article_for_reference(resource_file, bible_ref)
        if result:
            article_num, offset = result
            text = read_article_text(resource_file, article_num, max_chars=30000)
            if text and offset > 0 and offset < len(text):
                text = text[max(0, offset - 200):]
            return text

    # Not cached — try to build navindex via batch reader or subprocess
    global _batch_reader
    nav_data = None

    if _batch_reader and _batch_reader.is_alive():
        try:
            nav_data = _batch_reader.get_navigation_index(resource_file)
        except Exception:
            pass

    if nav_data is None:
        stdout, stderr = run_reader("--navindex", resource_file, timeout=120)
        if stdout:
            refs = []
            topics = []
            for line in stdout.split("\n"):
                parts = line.split("\t")
                if len(parts) >= 4 and parts[0] == "REF":
                    refs.append({"ref": parts[1], "article": int(parts[2]), "offset": int(parts[3])})
                elif len(parts) >= 5 and parts[0] == "TOPIC":
                    topics.append({"key": parts[1], "name": parts[2], "article": int(parts[3]), "offset": int(parts[4])})
            nav_data = {"references": refs, "topics": topics}

    if not nav_data or not nav_data["references"]:
        return None

    # Cache for future use
    if cache:
        try:
            cache.put_navindex(resource_file, nav_data["references"], nav_data.get("topics", []))
        except Exception:
            pass

    # Find best matching reference
    best_article = None
    best_offset = 0
    for r in nav_data["references"]:
        if r["ref"] == bible_ref:
            best_article = r["article"]
            best_offset = r["offset"]
            break
        # Partial match: same chapter
        if r["ref"].startswith(f"bible.{book_num}.{chapter}."):
            if best_article is None:
                best_article = r["article"]
                best_offset = r["offset"]

    if best_article is not None:
        text = read_article_text(resource_file, best_article, max_chars=30000)
        if text and best_offset > 0 and best_offset < len(text):
            text = text[max(0, best_offset - 200):]
        return text

    return None
```

- [ ] **Step 2: Update `find_commentary_section` to try navindex first**

Replace the beginning of `find_commentary_section`:

```python
def find_commentary_section(resource_file, ref, articles=None):
    """Find the relevant section in a commentary for a Bible reference.

    Priority:
    1. Navigation index (native API, instant via cache)
    2. Commentary verse index cache (from prior scans)
    3. TOC-based navigation
    4. Article-ID + text scanning (slow fallback)
    """
    # ── Try navigation index (fastest — native reference→article mapping) ──
    navindex_text = _find_via_navindex(resource_file, ref)
    if navindex_text:
        return navindex_text

    chapter = ref["chapter"]
    verse_start = ref["verse_start"]
    verse_end = ref["verse_end"] or verse_start

    # ── Check commentary verse index cache (from prior heuristic scans) ──
    cache = _get_logos_cache()
    if cache:
        cached_arts = cache.get_commentary_articles(resource_file, chapter, verse_start)
        if cached_arts:
            best = cached_arts[0]
            text = read_article_text(resource_file, best["article_num"], max_chars=30000)
            if text:
                return text

    # ── Try TOC-based navigation ──
    toc_text = find_commentary_section_via_toc(resource_file, ref)
    if toc_text:
        return toc_text

    # ── Fallback: article-ID + text scanning (slow, but caches results) ──
    return _find_commentary_section_heuristic(resource_file, ref, articles)
```

- [ ] **Step 3: Test the full pipeline**

```bash
python3 -c "
import time
from tools.study import find_commentary_section, parse_reference, init_batch_reader
init_batch_reader()
ref = parse_reference('Romans 1:16-17')
# First run builds navindex
t0 = time.time()
text = find_commentary_section('SORHET66RO.logos4', ref)
print(f'First: {time.time()-t0:.1f}s — {text[:80] if text else \"NONE\"}')
# Second run uses cache
t0 = time.time()
text2 = find_commentary_section('SORHET66RO.logos4', ref)
print(f'Cached: {time.time()-t0:.1f}s — {text2[:80] if text2 else \"NONE\"}')
"
```
Expected: First run ~1-5s (navindex export), cached run <0.1s.

- [ ] **Step 4: Commit**

```bash
git add tools/study.py
git commit -m "feat: use native navigation index for instant commentary lookup"
```

---

## Chunk 3: Text Search (Optional Enhancement)

### Task 8: Add `find-text` Command to LogosReader

**Files:**
- Modify: `tools/LogosReader/Program.cs`

- [ ] **Step 1: Add DoFindText P/Invoke declaration**

```csharp
    // Text search within a resource
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_DoFindText(
        IntPtr title,
        IntPtr startRange,    // null for beginning
        [MarshalAs(UnmanagedType.LPWStr)] string query,
        [MarshalAs(UnmanagedType.U1)] bool caseSensitive,
        [MarshalAs(UnmanagedType.U1)] bool wholeWord,
        IntPtr cancelCallback);  // null for no cancel
```

**Note:** The `MarshalTextRange` parameter may need special handling. The function takes a struct pointer and may return a modified range. If this crashes, skip this task — it's optional enhancement. The navigation index is the critical feature.

- [ ] **Step 2: Add `find-text` command**

```csharp
case "find-text":
    // Simple text search - outputs article numbers containing the query
    string searchQuery = findPattern; // reuse findPattern variable
    int hitCount = 0;
    int searchArticleCount = (int)CTitle_GetArticleCount(title);

    for (int a = 0; a < searchArticleCount && hitCount < 50; a++)
    {
        if (!SinaiInterop_CTitle_IsArticle(title, a)) continue;
        SinaiInterop_CTitle_GetExactText(title, a, 0, 2000, out string searchText);
        if (searchText != null && searchText.Contains(searchQuery, StringComparison.OrdinalIgnoreCase))
        {
            SinaiInterop_CTitle_ArticleNumberToArticleId(title, a, out string searchArtId);
            Console.WriteLine($"{a}\t{searchArtId ?? ""}\t{searchText.Substring(0, Math.Min(200, searchText.Length))}");
            hitCount++;
        }
    }
    Console.Error.WriteLine($"[*] Found {hitCount} articles containing \"{searchQuery}\"");
    break;
```

**Note:** This is a simple fallback search (iterates articles). The native `DoFindText` would be faster but has complex marshaling. Start with this approach and upgrade later.

- [ ] **Step 3: Build and test**

```bash
cd /Volumes/External/Logos4/tools/LogosReader && dotnet build && dotnet run -- --find-text SORHET66RO.logos4 "righteousness" 2>/dev/null | head -10
```

- [ ] **Step 4: Commit**

```bash
git add tools/LogosReader/Program.cs
git commit -m "feat: add find-text command for in-resource search"
```

---

## Chunk 4: Restart and Verify

### Task 9: Restart Workbench and End-to-End Test

- [ ] **Step 1: Restart the Flask server**

```bash
kill $(lsof -ti:5111) 2>/dev/null
sleep 1
cd /Volumes/External/Logos4/tools/workbench
PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH" DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec" python3 app.py &
```

- [ ] **Step 2: Test commentary survey via the UI**

Open http://localhost:5111, go to a Romans 1:16-17 project, click "Commentary Survey" phase, click "Survey the commentaries on this passage". Verify:
- Commentary sections are found correctly (about Romans 1:16-17, not introductions)
- Response time is reasonable (seconds, not minutes)
- Agent uses fewer tool calls (navindex means first try finds the right section)

- [ ] **Step 3: Test with a different passage**

Create a new project for "John 3:16" and run a commentary survey. First run builds navindex cache. Second run should be nearly instant.

---

## Risk Notes

1. **`ManagedNavigationIndexVisitor_New` may crash** — The callback function pointer marshaling is the trickiest part. If callbacks crash, try using `Marshal.GetFunctionPointerForDelegate` with explicit delegate instances stored as static fields (not local variables) to prevent GC collection during the native call.

2. **`SinaiInterop_GetArticleTitle` signature may be wrong** — The `out string` marshaling for this function may need `IntPtr` + manual `Marshal.PtrToStringUni` instead. If it crashes, change the declaration to return `IntPtr` and marshal manually.

3. **`ResourceVolumeFromResource` may need the title to be loaded with a specific hint** — If it returns null, try loading with `TitleLoadHint.Indexing` instead of `Normal`.

4. **Navigation index may be empty for some resources** — Not all resources have reference-type entries. Commentaries should, but general books may only have topic entries. The fallback to heuristic scanning handles this.

5. **Reference format may vary** — The `bible.{book}.{chapter}.{verse}` format is a guess based on Logos conventions. The actual format will be revealed by the first successful `navindex` export. Adjust the matching logic in Task 7 based on what you see.
