# Word Number Mapping Cache — Design Spec

**Date:** 2026-03-22
**Goal:** Unlock the 8 stubbed SupplementalData tools (figurative language, Greek/Hebrew constructions, literary typing, propositional outlines, wordplay, important words, cultural concepts, ancient literature) by building a word-number-to-verse mapping cache.

## Problem

SupplementalData encrypted databases (`.lbssd` files) index their data by GNT/BHS word numbers (e.g., `gnt/83662`) rather than Bible verse references. To query "what figurative language is in Romans 1:18-23?", we need to know which word numbers correspond to that passage.

The mapping exists in `WordSenses.lbswsd` — a separate encrypted database that links word numbers to Bible verse references through an Occurrences join chain:

```
WordNumbers.Reference (gnt/83662)
  → OccurrenceWordNumbers.WordNumberId
  → Occurrences.BibleReferenceId
  → BibleReferences.Reference (binary: 60 42 01 1B = Rom 1:27)
```

## Solution

### New file: `tools/word_number_cache.py`

A one-time build script that extracts all 264K word-number-to-verse mappings from WordSenses.lbswsd into a local SQLite cache.

**Schema:**
```sql
CREATE TABLE word_verse_map (
    word_ref TEXT PRIMARY KEY,   -- e.g. "gnt/83662" or "hot/8246"
    logos_book INTEGER NOT NULL, -- Logos canonical book number (1-39 OT, 61-87 NT)
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL
);
CREATE INDEX idx_book_chapter ON word_verse_map(logos_book, chapter);
CREATE INDEX idx_book_chapter_verse ON word_verse_map(logos_book, chapter, verse);
```

**Build process:**
1. Query WordSenses.lbswsd in batches (1000 rows at a time)
2. Decode binary Bible references to (logos_book, chapter, verse)
3. Insert into local SQLite at `tools/word_number_cache.db`
4. ~264K rows, ~5 minutes build time, ~10MB cache file

**Public API:**
```python
class WordNumberCache:
    def __init__(self, cache_db_path):
        """Open or create the cache database."""

    def is_built(self) -> bool:
        """Check if the cache has been populated."""

    def build(self):
        """One-time build: extract all mappings from WordSenses.lbswsd."""

    def get_word_numbers(self, protestant_book, chapter,
                         verse_start=None, verse_end=None) -> list[str]:
        """Get word number references for a passage.

        Returns list of strings like ["gnt/83219", "gnt/83220", ...].
        Converts Protestant book number to Logos canonical internally.
        """

    def get_word_number_ids(self, resource_file, db_name,
                            word_refs: list[str]) -> list[int]:
        """Find WordNumberIds in a SupplementalData database
        that match the given word references.

        Returns list of WordNumberId integers from the target database.
        """
```

### Changes to `dataset_tools.py`

Replace the 8 `return []` stubs with real implementations. Each follows the same pattern:

```python
def query_greek_constructions(book, chapter, verse_start=None, verse_end=None):
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter, verse_start, verse_end)
    if not word_refs:
        return []

    reader = _get_reader()
    # Find matching WordNumberIds in the SupplementalData database
    word_ids = _find_word_ids(reader, "GREEK-CONSTRUCTIONS.lbssd",
                              "SupplementalData.db", word_refs)
    if not word_ids:
        return []

    # Join: WordNumberSets → WordNumberSetAttachments → DataTypeReferences
    # Decode the label Reference blob into structured properties
    return _query_supplemental_by_word_ids(
        reader, "GREEK-CONSTRUCTIONS.lbssd", "SupplementalData.db", word_ids)
```

### Label decoding

The DataTypeReferences.Reference blob for "label" entries contains URL-encoded category data:
```
~Prepositional%20Phrase|Object%20Case=$Genitive|Object%20Lemma=#lemma.lbs.el.υἱός
```

Parsing rules:
- `~` prefix = label marker, strip it
- Split on `|` for key=value pairs
- First segment (before first `|`) = category name
- `$` prefix on value = enum value
- `#` prefix on value = reference (lemma, concept, etc.)
- URL-decode `%20` → space, etc.

Result format:
```python
{
    "category": "Prepositional Phrase",
    "properties": {
        "Object Case": "Genitive",
        "Object Lemma": "υἱός"
    },
    "word_refs": ["gnt/83270"]
}
```

### SupplementalData query helper

Shared function used by all 8 tools:

```python
def _query_supplemental_by_word_ids(reader, resource_file, db_name, word_ids):
    """Query SupplementalData for entries matching word IDs.

    Joins: WordNumberSets → WordNumberSetAttachments → DataTypeReferences
    Filters for DataType='label' entries and decodes the Reference blob.
    """
```

This runs a single SQL query per tool call:
```sql
SELECT DISTINCT dtr.ReferenceId, hex(dtr.Reference) as ref, hex(dtr.DataType) as dt
FROM WordNumberSets wns
JOIN WordNumberSetAttachments wnsa ON wns.WordNumberSetAttachmentId = wnsa.WordNumberSetAttachmentId
JOIN DataTypeReferences dtr ON wnsa.DataTypeReferenceId = dtr.ReferenceId
WHERE wns.WordNumberId IN ({word_id_list})
AND hex(dtr.DataType) = '6C6162656C'  -- 'label' in hex
```

### Word ID lookup optimization

Rather than hex-matching 240 word references one by one (slow), we batch-query:

1. Build a temporary mapping by querying the target database's WordNumbers table for all GNT words in the numeric range
2. Match against our word_refs list in Python
3. Return the WordNumberId integers for the SQL IN clause

```python
def _find_word_ids(reader, resource_file, db_name, word_refs):
    """Find WordNumberIds matching word references in a SupplementalData db."""
    # Get numeric range from word_refs
    nums = [int(w.split('/')[1].split('.')[0]) for w in word_refs if '/' in w]
    if not nums:
        return []
    mn, mx = min(nums), max(nums)

    # Query all word numbers in range from the target database
    # Use hex comparison on the numeric part
    prefix = word_refs[0].split('/')[0]  # "gnt" or "hot"
    rows = reader.query_dataset(resource_file, db_name,
        f"SELECT WordNumberId, hex(Reference) as ref FROM WordNumbers")

    # Filter in Python: decode each ref and check if in our set
    word_ref_set = set(word_refs)
    matching_ids = []
    for r in rows:
        ref_bytes = bytes.fromhex(r['ref'])
        ref_text = ref_bytes[1:].decode('utf-8', errors='replace')
        if ref_text in word_ref_set:
            matching_ids.append(int(r['WordNumberId']))

    return matching_ids
```

Note: For databases with 200K+ word numbers, this full-table scan is expensive (~2-3 seconds). Optimization for v2: pre-build a word_ref → WordNumberId index per database.

## Which tools get which databases

| Tool function | Resource file | Word type |
|---|---|---|
| `query_figurative_language` | FIGURATIVE-LANGUAGE.lbssd | gnt + hot |
| `query_greek_constructions` | GREEK-CONSTRUCTIONS.lbssd | gnt + lxx |
| `query_hebrew_constructions` | HEBREW-CONSTRUCTIONS.lbssd | hot |
| `query_literary_typing` | LITERARYTYPING.lbssd | gnt + hot |
| `query_wordplay` | WORDPLAY.lbssd | gnt + hot |
| `query_propositional_outline` | PROPOSITIONAL-OUTLINES.lbssd (NT) / PROPOSITIONAL-OUTLINES-OT.lbssd (OT) | gnt / hot |
| `query_nt_use_of_ot` | NT-USE-OF-OT.lbssd | gnt |
| `query_important_words` | IMPORTANTWORDS.lbsiw | different schema — see below |

### ImportantWords special case

`IMPORTANTWORDS.lbsiw` uses a different schema (Pericopes, Lemmas, Words, PericopeWordRelationships) rather than the standard SupplementalData pattern. It needs a separate query approach using its Pericopes table with Bible reference blobs (same binary format as PreachingThemes).

### Cultural Concepts and Ancient Literature

`LCO.lbslco` and `AncientLiterature.lbsanc` may use different schemas. These should be investigated during implementation and either use the word-number approach or the binary-reference approach depending on their schema.

## Files changed

| File | Change |
|---|---|
| `tools/word_number_cache.py` | NEW — cache builder and lookup |
| `tools/workbench/dataset_tools.py` | Replace 8 stubs with real implementations |
| `tools/workbench/tests/test_word_cache.py` | NEW — tests for cache and query pipeline |

## Testing

1. Build the cache, verify 264K entries
2. Query word numbers for Romans 1, verify range ~83219-83760
3. Query Greek constructions for Romans 1, verify structured results
4. Query figurative language for a passage known to have figures
5. End-to-end: companion tool `get_passage_data` returns real data for all requested datasets
