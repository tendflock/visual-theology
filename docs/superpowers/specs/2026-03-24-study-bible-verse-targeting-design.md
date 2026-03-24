# Study Bible Verse Targeting — Design Spec

**Date**: 2026-03-24
**Status**: Approved

## Problem

When studying Romans 1:24-32, the study bible card shows notes starting from Romans 1:1 and truncates at 5000 characters — never reaching the target passage. The navindex already contains per-verse character offsets into the article text, but `_find_via_navindex()` ignores them and returns the full article from position 0.

## Solution: Offset-based slicing

Use the navindex character offsets to extract only the content relevant to the target verse range.

## Algorithm

In `_find_via_navindex()`, after finding the target article:

1. **Collect chapter refs**: Query `navindex_cache` for all refs in the same article that belong to the target book+chapter. Parse each ref to extract verse start/end numbers.

2. **Find start offset**: Walk the collected refs to find the best starting point:
   - First preference: a section-range ref that contains the target start verse (e.g., `1:18-32` contains verse 24) — provides the section heading for context.
   - Second preference: the exact verse ref (e.g., `1:24`).
   - Third preference: the nearest preceding verse ref.

3. **Find end offset**: The offset of the first ref whose start verse is strictly greater than `verse_end`. If none exists (target is at end of chapter), use end of article.

4. **Slice**: Return `text[start_offset:end_offset].strip()`.

### Example: Romans 1:24-32 in ESV SB (article 1603)

| Ref | Offset | Role |
|-----|--------|------|
| `1:18-32` | 8918 | **Start** (section header containing range) |
| `1:18` | 9176 | (within range, skipped) |
| `1:24` | 11259 | (verse-level, covered by section start) |
| `1:25` | 11636 | |
| `1:26-27` | 11832 | |
| `1:28-31` | 13147 | |
| `1:32` | 13304 | Last verse in range |
| (end of article) | ~13800 | **End** |

Result: ~4900 chars of precisely targeted content starting with "The Unrighteousness of the Gentiles" section header.

## Changes

### 1. `tools/logos_cache.py` — New query method

Add `get_chapter_navindex_refs(resource_file, book_num, chapter)`:
- Returns all navindex refs for the given article's book+chapter
- Columns: `ref_key`, `article_num`, `offset`
- Sorted by offset ascending

### 2. `tools/study.py` — `_find_via_navindex()`

After finding `best_article` (line ~1482):
- Call `cache.get_chapter_navindex_refs()` to get all refs for this article+chapter
- Parse verse numbers from each ref (handle `bible+esv.66.1.24`, `bible.66.1.24-66.1.32`, etc.)
- Apply the start/end offset algorithm above
- Slice the article text
- If slicing produces < 100 chars (edge case), fall back to returning the full article

New helper: `_parse_verse_from_navref(ref_key, book_num, chapter)` — extracts (verse_start, verse_end) from a navindex ref key. Returns None for refs in other chapters/books.

### 3. `tools/study.py` — `find_study_bible_notes()`

- Change `max_chars` default from 5000 to 20000 (safety ceiling only; offset slicing controls scope)

### 4. `tools/study.py` — `find_commentary_section()`

- Apply `_narrow_to_verses()` to the cache path (line ~1514) and TOC path (line ~1519) as a fallback for non-navindex lookups

## Files Changed

| File | Change |
|------|--------|
| `tools/logos_cache.py` | Add `get_chapter_navindex_refs()` method |
| `tools/study.py` | Offset slicing in `_find_via_navindex()`, raise max_chars, add narrowing to cache/TOC paths |

No template, CSS, JS, or DB schema changes.

## Edge Cases

- **Verse range at end of chapter** (e.g., 1:24-32 where 32 is the last verse): End offset = end of article. Works naturally.
- **Study bibles with section-level only** (Ancient Faith has `1:18-21`, `1:26-28` but not `1:24`): Algorithm picks nearest section covering the verse. May include a few extra verses of context — acceptable.
- **No navindex data**: Falls through to existing cache/TOC/heuristic paths. Adding `_narrow_to_verses()` to those paths improves them too.
- **Offset slicing returns very little text**: If < 100 chars, fall back to full article (something is off with the offsets).
