# Study Bible Verse Targeting — Design Spec

**Date**: 2026-03-24
**Status**: Approved

## Problem

When studying Romans 1:24-32, the study bible card shows notes starting from Romans 1:1 and truncates at 5000 characters — never reaching the target passage. The navindex already contains per-verse character offsets into the article text, but `_find_via_navindex()` ignores them and returns the full article from position 0.

## Solution: Offset-based slicing

Use the navindex character offsets to extract only the content relevant to the target verse range.

## Algorithm

In `_find_via_navindex()`, after finding the target article:

1. **Read the full article text** first (using existing `read_article_text(resource_file, article_num, max_chars=30000)`). We need the full text to slice from, and `len(text)` serves as the default end offset.

2. **Collect article refs**: Query `navindex_cache` for all refs with the same `resource_file` and `article_num`. Filter in Python by book+chapter using `_parse_verse_from_navref()` (handles all prefix formats). Sort by offset ascending.

3. **Find start offset**: Walk the collected refs to find the best starting point:
   - First preference: the **narrowest** section-range ref whose range contains `verse_start` (e.g., `1:18-32` over `1:18-3:20` — prefer the range with fewer verses). This provides the section heading for context.
   - Second preference: the exact verse ref (e.g., `1:24`).
   - Third preference: the nearest preceding verse ref.

4. **Find end offset**: The offset of the first ref whose start verse is strictly greater than `verse_end`. If none exists (target is at end of chapter), use `len(text)`.

5. **Slice**: Return `text[start_offset:end_offset].strip()`. If result < 100 chars, fall back to full article text.

### Ref key format handling

The `_parse_verse_from_navref(ref_key, book_num, chapter)` helper must handle:

| Format | Example | Strategy |
|--------|---------|----------|
| `bible.{book}.{ch}.{vs}` | `bible.66.1.24` | Direct parse |
| `bible+{ver}.{book}.{ch}.{vs}` | `bible+esv.66.1.24` | Strip version: `"bible" + ref[ref.index("."):]` then parse |
| Verse range (same chapter) | `bible+esv.66.1.26-66.1.27` | Parse start and end verses |
| Cross-chapter range | `bible+esv.66.1.18-66.3.20` | For start offset: treat as starting at 1:18. For end detection: skip (doesn't help determine end of a within-chapter range) |
| Non-bible refs | `page.2157`, `topic.xxx` | Return None (skip) |

### Example: Romans 1:24-32 in ESV SB (article 1603)

Relevant navindex entries (sorted by offset):

| Ref | Offset | Role |
|-----|--------|------|
| `1:18-3:20` | 8677 | Broad section header (skipped — wider than `1:18-32`) |
| `1:18-32` | 8918 | **Start** (narrowest section containing verse 24) |
| `1:18` | 9176 | |
| `1:19-20` | 9478 | |
| `1:21` | 10165 | |
| `1:22` | 10513 | |
| `1:23` | 10669 | |
| `1:24` | 11259 | First target verse |
| `1:25` | 11636 | |
| `1:26-27` | 11832 | |
| `1:28-31` | 13147 | |
| `1:32` | 13304 | Last target verse |
| `len(text)` | ~13800 | **End** (no ref with start verse > 32 in chapter 1) |

Result: ~4900 chars of precisely targeted content starting with "The Unrighteousness of the Gentiles" section header.

## Changes

### 1. `tools/logos_cache.py` — New query method

Add `get_article_navindex_refs(resource_file, article_num)`:
- SQL: `SELECT ref_key, article_num, offset FROM navindex_cache WHERE resource_file = ? AND article_num = ? ORDER BY offset`
- Returns list of dicts: `[{"ref_key", "article_num", "offset"}, ...]`
- Filtering by book+chapter happens in Python via `_parse_verse_from_navref()` (handles all prefix formats without fragile SQL LIKE patterns)

### 2. `tools/study.py` — `_find_via_navindex()`

After finding `best_article` (line ~1482):
- Read full article: `text = read_article_text(resource_file, best_article, max_chars=30000)`
- If `verse_start` is None (chapter-level request), return text as-is (no slicing needed)
- Call `cache.get_article_navindex_refs(resource_file, best_article)` to get all refs
- Parse each with `_parse_verse_from_navref()`, filter to target chapter, sort by offset
- Apply start/end offset algorithm
- Slice: `text[start_offset:end_offset].strip()`
- If sliced result < 100 chars, return full text (offset data may be stale/wrong)

New helper: `_parse_verse_from_navref(ref_key, book_num, chapter)` — normalizes prefix, extracts `(verse_start, verse_end, offset)` or returns None for non-matching refs.

### 3. `tools/study.py` — `find_study_bible_notes()`

- Change `max_chars` default from 5000 to 20000 (safety ceiling only; offset slicing controls scope)

### 4. `tools/study.py` — `find_commentary_section()`

Apply `_narrow_to_verses()` as fallback in non-navindex paths:

```python
# Cache path (line ~1514):
text = read_article_text(resource_file, best["article_num"], max_chars=30000)
if text and verse_start:
    narrowed = _narrow_to_verses(text, verse_start, verse_end)
    if narrowed:
        return narrowed
if text:
    return text

# TOC path (line ~1519):
toc_text = find_commentary_section_via_toc(resource_file, ref)
if toc_text and verse_start:
    narrowed = _narrow_to_verses(toc_text, verse_start, verse_end)
    if narrowed:
        return narrowed
if toc_text:
    return toc_text
```

`verse_start` and `verse_end` are already computed at lines 1504-1505.

## Files Changed

| File | Change |
|------|--------|
| `tools/logos_cache.py` | Add `get_article_navindex_refs()` method, add index on `(resource_file, article_num)` |
| `tools/study.py` | Offset slicing in `_find_via_navindex()`, new `_parse_verse_from_navref()` helper, raise max_chars, add narrowing to cache/TOC paths |

No template, CSS, JS, or DB schema changes.

## Edge Cases

- **Verse range at end of chapter** (e.g., 1:24-32 where 32 is the last verse): No ref with start verse > 32, so end offset = `len(text)`. Works naturally.
- **Cross-chapter section headers** (e.g., `1:18-3:20`): Parsed as starting at verse 18 of chapter 1 with `verse_end=None`. When selecting the narrowest containing section, treat `None` end as infinitely wide — so `1:18-32` (14 verse span) always beats `1:18-3:20` (infinite span).
- **Study bibles with section-level only** (Ancient Faith has `1:18-21`, `1:26-28` but not `1:24`): Algorithm picks nearest section covering the verse. May include a few extra verses of context — acceptable.
- **No navindex data**: Falls through to existing cache/TOC/heuristic paths. Adding `_narrow_to_verses()` to those paths improves them too.
- **Offset slicing returns very little text**: If < 100 chars, fall back to full article.
- **`max_chars` on `read_article_text`**: Already 30000 in `_find_via_navindex`. All known study bible articles for single chapters are well under this. The end offset is clamped to `len(text)` so even if the article were somehow truncated, slicing is safe.

## Tests

Unit tests for the new helper and algorithm:

| Test | Input | Expected |
|------|-------|----------|
| Parse `bible+esv.66.1.24` | book=66, ch=1 | (24, 24) |
| Parse `bible.66.1.24-66.1.32` | book=66, ch=1 | (24, 32) |
| Parse `bible+esv.66.1.18-66.3.20` | book=66, ch=1 | (18, None) — cross-chapter, end indeterminate |
| Parse `page.2157` | book=66, ch=1 | None (skip) |
| Parse `bible+esv.66.2.1` | book=66, ch=1 | None (wrong chapter) |
| Offset slicing: Romans 1:24-32 | ESV SB navindex data | Starts at offset 8918, ends at len(text) |
| Offset slicing: sparse SB | Ancient Faith data | Picks nearest section |
| Offset slicing: < 100 chars result | Fabricated bad offsets | Falls back to full article |

Integration test: `find_study_bible_notes(parse_reference("Romans 1:24-32"))` returns notes that contain "1:24" or "1:25" content (not "1:1" content).
