# Study Bible Verse Targeting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix study bible notes to show content for the target verse range (e.g., Romans 1:24-32) instead of starting from the chapter beginning (1:1) and truncating.

**Architecture:** Use existing navindex character offsets to slice article text to just the relevant verses. The navindex already maps Bible references to (article_num, offset) pairs — the code just needs to use the offsets after finding the article. Fallback paths (cache, TOC) get `_narrow_to_verses()` applied.

**Tech Stack:** Python, SQLite (logos_cache.db)

**Spec:** `docs/superpowers/specs/2026-03-24-study-bible-verse-targeting-design.md`

---

### Task 1: Add `get_article_navindex_refs()` to LogosCache

**Files:**
- Modify: `tools/logos_cache.py:91-103` (add index in `_create_tables`)
- Modify: `tools/logos_cache.py:378` (add new method after `find_article_for_reference`)
- Test: `tools/workbench/tests/test_study_bible_notes.py`

- [ ] **Step 1: Write the failing test**

Add to `tools/workbench/tests/test_study_bible_notes.py`:

```python
def test_get_article_navindex_refs():
    """Cache should return all navindex refs for a given article."""
    from logos_cache import LogosCache
    cache = LogosCache()
    # ESV SB article 1603 = Romans chapter 1 notes
    refs = cache.get_article_navindex_refs(
        "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources/ESVSB.logos4",
        1603
    )
    assert isinstance(refs, list)
    assert len(refs) > 10  # ESV SB has ~40 refs for Romans 1
    # Should be sorted by offset
    offsets = [r["offset"] for r in refs]
    assert offsets == sorted(offsets)
    # Each entry should have ref_key, article_num, offset
    for r in refs:
        assert "ref_key" in r
        assert "article_num" in r
        assert "offset" in r
        assert r["article_num"] == 1603
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py::test_get_article_navindex_refs -v`
Expected: FAIL — `LogosCache` has no `get_article_navindex_refs` method

- [ ] **Step 3: Implement `get_article_navindex_refs()` and add index**

In `tools/logos_cache.py`, add the index in `_create_tables()` after line 103:

```python
            CREATE INDEX IF NOT EXISTS idx_navindex_article
                ON navindex_cache(resource_file, article_num);
```

Add new method after `find_article_for_reference()` (~line 380):

```python
    def get_article_navindex_refs(self, resource_file, article_num):
        """Get all navindex refs for a specific article.

        Returns list of dicts sorted by offset:
        [{"ref_key": str, "article_num": int, "offset": int}, ...]
        """
        rows = self._conn.execute(
            """SELECT ref_key, article_num, offset FROM navindex_cache
               WHERE resource_file = ? AND article_num = ? AND entry_type = 'REF'
               ORDER BY offset""",
            (resource_file, article_num),
        ).fetchall()
        return [{"ref_key": r[0], "article_num": r[1], "offset": r[2]} for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py::test_get_article_navindex_refs -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/logos_cache.py tools/workbench/tests/test_study_bible_notes.py
git commit -m "feat: add get_article_navindex_refs() to LogosCache"
```

---

### Task 2: Add `_parse_verse_from_navref()` helper

**Files:**
- Modify: `tools/study.py:1370` (add helper before `_find_via_navindex`)
- Test: `tools/workbench/tests/test_study_bible_notes.py`

- [ ] **Step 1: Write the failing tests**

Add to `tools/workbench/tests/test_study_bible_notes.py`:

```python
def test_parse_verse_from_navref_direct():
    """Parse bible.66.1.24 format."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible.66.1.24", 66, 1)
    assert result == (24, 24)


def test_parse_verse_from_navref_versioned():
    """Parse bible+esv.66.1.24 format (strip version prefix)."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.1.24", 66, 1)
    assert result == (24, 24)


def test_parse_verse_from_navref_range_same_chapter():
    """Parse verse range within same chapter."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.1.26-66.1.27", 66, 1)
    assert result == (26, 27)


def test_parse_verse_from_navref_range_no_version_prefix():
    """Parse bible.66.1.24-66.1.32 (no version prefix, range)."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible.66.1.24-66.1.32", 66, 1)
    assert result == (24, 32)


def test_parse_verse_from_navref_range_cross_chapter():
    """Cross-chapter range: verse_end is None (indeterminate)."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.1.18-66.3.20", 66, 1)
    assert result == (18, None)


def test_parse_verse_from_navref_wrong_chapter():
    """Ref in different chapter returns None."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.2.1", 66, 1)
    assert result is None


def test_parse_verse_from_navref_non_bible():
    """Non-bible refs (page, topic) return None."""
    from study import _parse_verse_from_navref
    assert _parse_verse_from_navref("page.2157", 66, 1) is None
    assert _parse_verse_from_navref("topic.salvation", 66, 1) is None


def test_parse_verse_from_navref_chapter_only():
    """Chapter-only ref like bible.66.1 returns (None, None) — no verse info."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible.66.1", 66, 1)
    assert result is None  # Not useful for verse-level slicing
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -k "parse_verse" -v`
Expected: FAIL — `_parse_verse_from_navref` not defined

- [ ] **Step 3: Implement `_parse_verse_from_navref()`**

Add to `tools/study.py` before `_find_via_navindex()` (~line 1370):

```python
def _parse_verse_from_navref(ref_key, book_num, chapter):
    """Parse a navindex ref key to extract verse range for a specific chapter.

    Handles formats:
      bible.66.1.24           -> (24, 24)
      bible+esv.66.1.24       -> (24, 24)
      bible+esv.66.1.26-66.1.27 -> (26, 27)
      bible+esv.66.1.18-66.3.20 -> (18, None)  cross-chapter
      page.2157               -> None
      bible+esv.66.2.1        -> None  (wrong chapter)

    Returns (verse_start, verse_end) or None if ref doesn't match book+chapter.
    """
    if not ref_key.startswith("bible"):
        return None

    # Normalize: strip version prefix (bible+esv.X -> bible.X)
    if ref_key.startswith("bible+"):
        dot_idx = ref_key.index(".")
        ref_key = "bible" + ref_key[dot_idx:]

    # Split on hyphen for ranges: "bible.66.1.26-66.1.27"
    parts = ref_key.split("-", 1)
    start_part = parts[0]  # "bible.66.1.26"

    # Parse start: bible.{book}.{chapter}.{verse}
    segs = start_part.split(".")
    if len(segs) < 4:
        return None  # Chapter-only ref like bible.66.1
    try:
        ref_book = int(segs[1])
        ref_ch = int(segs[2])
        ref_vs = int(segs[3])
    except (ValueError, IndexError):
        return None

    if ref_book != book_num or ref_ch != chapter:
        return None

    # Single verse (no range)
    if len(parts) == 1:
        return (ref_vs, ref_vs)

    # Parse end of range
    end_part = parts[1]  # "66.1.27" or "66.3.20"
    end_segs = end_part.split(".")
    try:
        end_book = int(end_segs[0])
        end_ch = int(end_segs[1])
        end_vs = int(end_segs[2])
    except (ValueError, IndexError):
        return (ref_vs, None)

    # Cross-chapter range
    if end_book != book_num or end_ch != chapter:
        return (ref_vs, None)

    return (ref_vs, end_vs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -k "parse_verse" -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/study.py tools/workbench/tests/test_study_bible_notes.py
git commit -m "feat: add _parse_verse_from_navref() for navindex ref parsing"
```

---

### Task 3: Add `_slice_article_by_offsets()` helper

**Files:**
- Modify: `tools/study.py` (add helper after `_parse_verse_from_navref`)
- Test: `tools/workbench/tests/test_study_bible_notes.py`

- [ ] **Step 1: Write the failing tests**

Add to `tools/workbench/tests/test_study_bible_notes.py`:

```python
def test_slice_article_picks_narrowest_section():
    """Should prefer 1:18-32 (narrow) over 1:18-3:20 (broad) as start."""
    from study import _slice_article_by_offsets
    text = "A" * 15000  # Fake article text
    refs = [
        {"ref_key": "bible.66.1.1", "offset": 0},
        {"ref_key": "bible.66.1.18-66.3.20", "offset": 8677},
        {"ref_key": "bible.66.1.18-66.1.32", "offset": 8918},
        {"ref_key": "bible.66.1.24", "offset": 11259},
        {"ref_key": "bible.66.1.32", "offset": 13304},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    # Should start at 8918 (narrowest section containing v24), not 8677
    assert result == text[8918:]  # End of chapter = end of article


def test_slice_article_end_offset():
    """End offset should be the first ref after verse_end."""
    from study import _slice_article_by_offsets
    text = "A" * 20000
    refs = [
        {"ref_key": "bible.66.1.1", "offset": 0},
        {"ref_key": "bible.66.1.16", "offset": 6000},
        {"ref_key": "bible.66.1.18", "offset": 8000},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 1, 7)
    # verse 1-7 requested. Next ref after v7 is v16 at offset 6000
    assert result == text[0:6000].strip()


def test_slice_article_fallback_on_short_result():
    """Should return full text if slicing produces < 100 chars."""
    from study import _slice_article_by_offsets
    text = "Short text but real content here."
    refs = [
        {"ref_key": "bible.66.1.24", "offset": 30},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    assert result == text  # Falls back to full text


def test_slice_article_no_matching_refs():
    """Should return full text if no refs match target chapter."""
    from study import _slice_article_by_offsets
    text = "Full article text here."
    refs = [
        {"ref_key": "page.123", "offset": 0},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    assert result == text


def test_slice_article_sparse_sections():
    """Ancient Faith style: section-level refs only, no exact verse match."""
    from study import _slice_article_by_offsets
    text = "A" * 6000
    refs = [
        {"ref_key": "bible.66.1.1", "offset": 0},
        {"ref_key": "bible.66.1.18-66.1.21", "offset": 3794},
        {"ref_key": "bible.66.1.20", "offset": 4283},
        {"ref_key": "bible.66.1.26-66.1.28", "offset": 4701},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    # Nearest section containing or preceding v24 is 1:18-21 (offset 3794)
    # — it doesn't contain v24, but 1:26-28 does and its start (v26) > v24
    # The 1:20 ref (offset 4283) precedes v24, so start = 4283
    # No ref after v32, so end = len(text)
    assert result == text[4283:].strip()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -k "slice_article" -v`
Expected: FAIL — `_slice_article_by_offsets` not defined

- [ ] **Step 3: Implement `_slice_article_by_offsets()`**

Add to `tools/study.py` after `_parse_verse_from_navref()`:

```python
def _slice_article_by_offsets(text, navindex_refs, book_num, chapter,
                               verse_start, verse_end):
    """Slice article text to target verse range using navindex offsets.

    Args:
        text: full article text
        navindex_refs: list of {"ref_key", "offset"} dicts, sorted by offset
        book_num: target book number
        chapter: target chapter number
        verse_start: first target verse
        verse_end: last target verse

    Returns:
        Sliced text covering the target verse range, or full text as fallback.
    """
    if not text or not navindex_refs:
        return text

    # Parse all refs into (verse_start, verse_end, offset) tuples
    parsed = []
    for r in navindex_refs:
        vrange = _parse_verse_from_navref(r["ref_key"], book_num, chapter)
        if vrange is not None:
            vs, ve = vrange
            parsed.append((vs, ve, r["offset"]))

    if not parsed:
        return text

    # Sort by offset (should already be sorted, but ensure)
    parsed.sort(key=lambda x: x[2])

    # ── Find start offset ──
    # Priority 1: narrowest finite section-range containing verse_start
    # Cross-chapter ranges (ve=None) are skipped here — they're caught by Priority 3
    best_section_offset = None
    best_section_span = float('inf')
    for vs, ve, offset in parsed:
        if ve is not None and vs != ve and vs <= verse_start and ve >= verse_start:
            # Section range that contains verse_start
            span = ve - vs
            if span < best_section_span:
                best_section_span = span
                best_section_offset = offset

    # Priority 2: exact verse match
    exact_offset = None
    for vs, ve, offset in parsed:
        if vs == verse_start and ve == verse_start:
            exact_offset = offset
            break

    # Priority 3: nearest preceding verse
    preceding_offset = None
    for vs, ve, offset in parsed:
        if vs is not None and vs <= verse_start:
            preceding_offset = offset

    # Pick best start
    if best_section_offset is not None:
        start_offset = best_section_offset
    elif exact_offset is not None:
        start_offset = exact_offset
    elif preceding_offset is not None:
        start_offset = preceding_offset
    else:
        return text  # No usable refs

    # ── Find end offset ──
    end_offset = len(text)
    for vs, ve, offset in parsed:
        if vs is not None and vs > verse_end:
            end_offset = offset
            break

    result = text[start_offset:end_offset].strip()

    # Fallback if slicing produced very little
    if len(result) < 100:
        return text

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -k "slice_article" -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/study.py tools/workbench/tests/test_study_bible_notes.py
git commit -m "feat: add _slice_article_by_offsets() for verse-targeted extraction"
```

---

### Task 4: Wire offset slicing into `_find_via_navindex()`

**Files:**
- Modify: `tools/study.py:1482-1484` (the article fetch + return block in `_find_via_navindex`)

- [ ] **Step 1: Write the failing integration test**

Add to `tools/workbench/tests/test_study_bible_notes.py`:

```python
def test_find_via_navindex_targets_verses():
    """_find_via_navindex should return content for target verses, not chapter start."""
    from study import _find_via_navindex, parse_reference
    ref = parse_reference("Romans 1:24-32")
    esvsb_path = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources/ESVSB.logos4"
    result = _find_via_navindex(esvsb_path, ref)
    assert result is not None
    # Should contain content about verses 24-32, not start with 1:1 content
    # The section header "1:18" or "Unrighteousness" should appear near the start
    first_500 = result[:500].lower()
    assert "1:1 " not in first_500 or "1:18" in first_500
    # Should mention verse 24 or later content
    assert "1:24" in result or "gave them up" in result.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py::test_find_via_navindex_targets_verses -v`
Expected: FAIL — result starts with 1:1 content

- [ ] **Step 3: Extract slicing into a helper and apply to BOTH return paths**

The function has TWO return paths that need slicing:
1. **Cache fast path** (lines 1392-1397) — fires on all subsequent lookups
2. **Cold path** (lines 1482-1484) — fires on first-time navindex build

First, add a helper at the top of the function body (after the cache/ref setup):

In `tools/study.py`, add a local helper inside `_find_via_navindex()`, after line ~1389:

```python
    def _apply_verse_slicing(text, article_num):
        """Apply offset-based slicing if we have verse-level targeting."""
        if not text or not verse_start or not cache:
            return text
        article_refs = cache.get_article_navindex_refs(resource_file, article_num)
        if article_refs:
            return _slice_article_by_offsets(
                text, article_refs, book_num, chapter,
                verse_start, verse_end
            )
        return text

    verse_end = ref.get("verse_end") or verse_start
```

Then replace the **cache fast path** at lines ~1392-1397:

```python
    # Check cache first
    if cache:
        result = cache.find_article_for_reference(resource_file, bible_ref)
        if result:
            article_num, offset = result
            text = read_article_text(resource_file, article_num, max_chars=30000)
            return text
```

With:

```python
    # Check cache first
    if cache:
        result = cache.find_article_for_reference(resource_file, bible_ref)
        if result:
            article_num, offset = result
            text = read_article_text(resource_file, article_num, max_chars=30000)
            return _apply_verse_slicing(text, article_num)
```

And replace the **cold path** at lines ~1482-1484:

```python
    if best_article is not None:
        text = read_article_text(resource_file, best_article, max_chars=30000)
        return text
```

With:

```python
    if best_article is not None:
        text = read_article_text(resource_file, best_article, max_chars=30000)
        return _apply_verse_slicing(text, best_article)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py::test_find_via_navindex_targets_verses -v`
Expected: PASS

- [ ] **Step 5: Run all existing tests to check for regressions**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add tools/study.py tools/workbench/tests/test_study_bible_notes.py
git commit -m "feat: wire offset slicing into _find_via_navindex for verse targeting"
```

---

### Task 5: Raise `max_chars` and add narrowing fallbacks

**Files:**
- Modify: `tools/study.py:384` (`find_study_bible_notes` max_chars default)
- Modify: `tools/study.py:1507-1520` (`find_commentary_section` cache and TOC paths)
- Test: `tools/workbench/tests/test_study_bible_notes.py`

- [ ] **Step 1: Update `find_study_bible_notes()` max_chars**

In `tools/study.py` line 384, change:

```python
def find_study_bible_notes(ref, max_chars=5000):
```

To:

```python
def find_study_bible_notes(ref, max_chars=20000):
```

- [ ] **Step 2: Add `_narrow_to_verses()` to cache and TOC paths**

In `tools/study.py`, replace lines ~1510-1515 (cache path):

```python
    if cache:
        cached_arts = cache.get_commentary_articles(resource_file, chapter, verse_start)
        if cached_arts:
            best = cached_arts[0]
            text = read_article_text(resource_file, best["article_num"], max_chars=30000)
            if text:
                return text
```

With:

```python
    if cache:
        cached_arts = cache.get_commentary_articles(resource_file, chapter, verse_start)
        if cached_arts:
            best = cached_arts[0]
            text = read_article_text(resource_file, best["article_num"], max_chars=30000)
            if text and verse_start:
                narrowed = _narrow_to_verses(text, verse_start, verse_end)
                if narrowed:
                    return narrowed
            if text:
                return text
```

Replace lines ~1517-1520 (TOC path):

```python
    # ── Try TOC-based navigation ──
    toc_text = find_commentary_section_via_toc(resource_file, ref)
    if toc_text:
        return toc_text
```

With:

```python
    # ── Try TOC-based navigation ──
    toc_text = find_commentary_section_via_toc(resource_file, ref)
    if toc_text and verse_start:
        narrowed = _narrow_to_verses(toc_text, verse_start, verse_end)
        if narrowed:
            return narrowed
    if toc_text:
        return toc_text
```

- [ ] **Step 3: Update the truncation test**

In `tools/workbench/tests/test_study_bible_notes.py`, update `test_find_study_bible_notes_truncates_long_text`:

```python
def test_find_study_bible_notes_truncates_long_text():
    """Should truncate study bible notes longer than max_chars."""
    from study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:1-7")
    results = find_study_bible_notes(ref, max_chars=200)
    for r in results:
        if r["text"]:
            assert len(r["text"]) <= 250  # 200 + allowance for truncation marker
```

(No change needed — this test already passes max_chars=200 explicitly.)

- [ ] **Step 4: Write integration test for the full flow**

Add to `tools/workbench/tests/test_study_bible_notes.py`:

```python
def test_find_study_bible_notes_targets_passage():
    """Full integration: notes for Romans 1:24-32 should be about those verses."""
    from study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:24-32")
    results = find_study_bible_notes(ref)
    assert len(results) > 0
    for r in results:
        # Should not start with 1:1 content
        first_200 = r["text"][:200]
        assert "1:1 " not in first_200 or "1:1" not in first_200[:20]
        # Should not be truncated (targeted content is well under 20000)
        assert "[... truncated ...]" not in r["text"]
```

- [ ] **Step 5: Run all tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add tools/study.py tools/workbench/tests/test_study_bible_notes.py
git commit -m "feat: raise max_chars to 20000, add verse narrowing to cache/TOC paths"
```

---

### Task 6: Manual verification with live data

**Files:** None (testing only)

- [ ] **Step 1: Test with Romans 1:24-32 via Python**

```bash
cd tools/workbench && python3 -c "
from study import find_study_bible_notes, parse_reference
ref = parse_reference('Romans 1:24-32')
results = find_study_bible_notes(ref)
for r in results:
    print(f'=== {r[\"abbrev\"]} ({len(r[\"text\"])} chars) ===')
    print(r['text'][:300])
    print()
"
```

Expected: Each study bible's output starts with content about verses 18-32 (section header) or 24+ (verse notes), NOT with verse 1:1. No `[... truncated ...]` markers.

- [ ] **Step 2: Test with a different passage (Galatians 5:16-26)**

```bash
cd tools/workbench && python3 -c "
from study import find_study_bible_notes, parse_reference
ref = parse_reference('Galatians 5:16-26')
results = find_study_bible_notes(ref)
for r in results:
    print(f'=== {r[\"abbrev\"]} ({len(r[\"text\"])} chars) ===')
    print(r['text'][:300])
    print()
"
```

Expected: Content targets Galatians 5:16-26 (fruit of the Spirit section), not 5:1.

- [ ] **Step 3: Test chapter-only request still works**

```bash
cd tools/workbench && python3 -c "
from study import find_study_bible_notes, parse_reference
ref = parse_reference('Romans 1')
results = find_study_bible_notes(ref)
for r in results:
    print(f'=== {r[\"abbrev\"]} ({len(r[\"text\"])} chars) ===')
    print(r['text'][:200])
    print()
"
```

Expected: Returns full chapter notes (no slicing applied when no verse specified).

- [ ] **Step 4: Run the full test suite**

Run: `cd tools/workbench && python3 -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "test: verify study bible verse targeting across multiple passages"
```
