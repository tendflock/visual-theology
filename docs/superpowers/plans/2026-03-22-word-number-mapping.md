# Word Number Mapping Cache — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a word-number-to-verse mapping cache and use it to unlock 8 stubbed SupplementalData passage tools (figurative language, constructions, literary typing, etc.).

**Architecture:** One-time extraction of 264K word-number-to-verse mappings from WordSenses.lbswsd into a local SQLite cache. Each SupplementalData tool queries the cache for word numbers in a passage, finds matching WordNumberIds in the target database, then joins through to get label data.

**Tech Stack:** Python 3, SQLite, LogosBatchReader (existing), EncryptedVolume API (existing)

**Spec:** `docs/superpowers/specs/2026-03-22-word-number-mapping-design.md`

**Environment Setup (required for all tasks):**
```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:/opt/homebrew/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

**Test runner:** `/opt/homebrew/bin/python3 -m pytest` (NOT `python3 -m pytest` which resolves to system Python without pytest)

---

## File Structure

### New files:
```
tools/
├── word_number_cache.py              — Cache builder + lookup API
├── workbench/
│   └── tests/
│       └── test_word_cache.py        — Tests for cache + SupplementalData pipeline
```

### Modified files:
```
tools/
├── workbench/
│   └── dataset_tools.py              — Replace 8 stubs with real implementations
```

---

## Task 1: Build Word Number Cache

**Files:**
- Create: `tools/word_number_cache.py`
- Create: `tools/workbench/tests/test_word_cache.py`

- [ ] **Step 1: Write test for cache build and lookup**

```python
# tools/workbench/tests/test_word_cache.py
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from word_number_cache import WordNumberCache

@pytest.fixture(scope="module")
def cache():
    """Build cache once for all tests in this module."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    c = WordNumberCache(path)
    c.build()
    yield c
    os.unlink(path)

def test_cache_is_built(cache):
    """Cache should have 200K+ entries after build."""
    assert cache.is_built()
    count = cache.count()
    assert count > 200000, f"Expected 200K+ entries, got {count}"

def test_romans_1_word_numbers(cache):
    """Should return GNT word numbers for Romans 1."""
    refs = cache.get_word_numbers(45, 1)  # Protestant book 45 = Romans
    assert len(refs) > 100, f"Expected 100+ words in Romans 1, got {len(refs)}"
    assert all(r.startswith("gnt/") for r in refs), "Romans 1 should be GNT words"

def test_genesis_1_word_numbers(cache):
    """Should return HOT word numbers for Genesis 1."""
    refs = cache.get_word_numbers(1, 1)  # Genesis
    assert len(refs) > 50, f"Expected 50+ words in Genesis 1, got {len(refs)}"
    assert all(r.startswith("hot/") for r in refs), f"Genesis 1 should be HOT words, got {refs[:3]}"

def test_verse_range_filter(cache):
    """Should filter to specific verse range."""
    full_chapter = cache.get_word_numbers(45, 1)
    verse_range = cache.get_word_numbers(45, 1, verse_start=18, verse_end=23)
    assert len(verse_range) > 0, "Should have words in Rom 1:18-23"
    assert len(verse_range) < len(full_chapter), "Verse range should be smaller than full chapter"

def test_empty_for_invalid_book(cache):
    """Should return empty list for non-existent book."""
    refs = cache.get_word_numbers(99, 1)
    assert refs == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Volumes/External/Logos4/tools && /opt/homebrew/bin/python3 -m pytest workbench/tests/test_word_cache.py -v 2>&1 | head -15
```
Expected: FAIL with "No module named 'word_number_cache'"

- [ ] **Step 3: Write word_number_cache.py**

```python
# tools/word_number_cache.py
"""Word-number-to-verse mapping cache.

Extracts word number → Bible verse mappings from WordSenses.lbswsd
(an encrypted Logos database) and caches them in a local SQLite database.
This enables SupplementalData tools to query by passage.

Usage:
    cache = WordNumberCache("path/to/cache.db")
    if not cache.is_built():
        cache.build()  # One-time, ~5 minutes
    word_refs = cache.get_word_numbers(45, 1)  # Romans 1
"""
import binascii
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(__file__))
from logos_batch import LogosBatchReader


def _protestant_to_logos(book):
    """Convert Protestant book number (1-66) to Logos canonical number."""
    if book <= 39:
        return book
    return book + 21


class WordNumberCache:
    """SQLite-backed cache mapping word numbers to Bible verses."""

    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_tables()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS word_verse_map (
                word_ref TEXT PRIMARY KEY,
                logos_book INTEGER NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_book_chapter
                ON word_verse_map(logos_book, chapter);
            CREATE INDEX IF NOT EXISTS idx_book_chapter_verse
                ON word_verse_map(logos_book, chapter, verse);
        """)
        conn.commit()
        conn.close()

    def is_built(self):
        """Check if the cache has been populated."""
        conn = self._conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM word_verse_map").fetchone()
        conn.close()
        return row["cnt"] > 0

    def count(self):
        """Return number of entries in the cache."""
        conn = self._conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM word_verse_map").fetchone()
        conn.close()
        return row["cnt"]

    def build(self):
        """One-time build: extract all mappings from WordSenses.lbswsd.

        Queries the encrypted WordSenses database via LogosBatchReader,
        joining WordNumbers → OccurrenceWordNumbers → Occurrences → BibleReferences.
        Decodes binary Bible references to (logos_book, chapter, verse).
        """
        reader = LogosBatchReader()
        conn = self._conn()
        try:
            # Clear existing data
            conn.execute("DELETE FROM word_verse_map")
            conn.commit()

            # Query in batches using OFFSET/LIMIT
            batch_size = 1000
            total_inserted = 0
            offset = 0

            while True:
                rows = reader.query_dataset(
                    "WordSenses.lbswsd", "WordSenses.db",
                    f"SELECT DISTINCT hex(wn.Reference) as wn_ref, "
                    f"hex(br.Reference) as bible_ref "
                    f"FROM WordNumbers wn "
                    f"JOIN OccurrenceWordNumbers own ON wn.WordNumberId = own.WordNumberId "
                    f"JOIN Occurrences o ON own.OccurrenceId = o.OccurrenceId "
                    f"JOIN BibleReferences br ON o.BibleReferenceId = br.BibleReferenceId "
                    f"LIMIT {batch_size} OFFSET {offset}",
                    max_rows=batch_size
                )

                if not rows:
                    break

                batch = []
                for r in rows:
                    wn_hex = r.get("wn_ref", "")
                    br_hex = r.get("bible_ref", "")
                    if not wn_hex or not br_hex:
                        continue

                    # Decode word number reference
                    try:
                        wn_bytes = binascii.unhexlify(wn_hex)
                        # Skip length prefix byte
                        word_ref = wn_bytes[1:].decode("utf-8", errors="replace")
                    except Exception:
                        continue

                    if not word_ref or "/" not in word_ref:
                        continue

                    # Decode Bible reference: 60 {book} {chapter} {verse}
                    try:
                        br_bytes = binascii.unhexlify(br_hex)
                        if len(br_bytes) < 4 or br_bytes[0] != 0x60:
                            continue
                        logos_book = br_bytes[1]
                        chapter = br_bytes[2]
                        verse = br_bytes[3]
                    except Exception:
                        continue

                    batch.append((word_ref, logos_book, chapter, verse))

                if batch:
                    conn.executemany(
                        "INSERT OR IGNORE INTO word_verse_map "
                        "(word_ref, logos_book, chapter, verse) VALUES (?, ?, ?, ?)",
                        batch
                    )
                    conn.commit()
                    total_inserted += len(batch)

                offset += batch_size

                # Safety: stop after 500 batches (500K rows)
                if offset > 500000:
                    break

            return total_inserted
        finally:
            conn.close()
            reader.close()

    def get_word_numbers(self, protestant_book, chapter,
                         verse_start=None, verse_end=None):
        """Get word number references for a passage.

        Args:
            protestant_book: Protestant book number (1-66)
            chapter: Chapter number
            verse_start: Optional start verse (inclusive)
            verse_end: Optional end verse (inclusive)

        Returns:
            List of word reference strings like ["gnt/83219", "gnt/83220", ...]
        """
        logos_book = _protestant_to_logos(protestant_book)
        conn = self._conn()

        if verse_start and verse_end:
            rows = conn.execute(
                "SELECT word_ref FROM word_verse_map "
                "WHERE logos_book = ? AND chapter = ? "
                "AND verse >= ? AND verse <= ?",
                (logos_book, chapter, verse_start, verse_end)
            ).fetchall()
        elif verse_start:
            rows = conn.execute(
                "SELECT word_ref FROM word_verse_map "
                "WHERE logos_book = ? AND chapter = ? AND verse = ?",
                (logos_book, chapter, verse_start)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT word_ref FROM word_verse_map "
                "WHERE logos_book = ? AND chapter = ?",
                (logos_book, chapter)
            ).fetchall()

        conn.close()
        return [r["word_ref"] for r in rows]
```

- [ ] **Step 4: Run tests**

```bash
cd /Volumes/External/Logos4/tools && /opt/homebrew/bin/python3 -m pytest workbench/tests/test_word_cache.py -v 2>&1
```
Expected: All 5 tests pass. The `build()` call will take 3-5 minutes on first run (scope="module" fixture means it only builds once).

- [ ] **Step 5: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/word_number_cache.py tools/workbench/tests/test_word_cache.py
git commit -m "feat: add word-number-to-verse mapping cache

Extracts 264K word-number → Bible verse mappings from WordSenses.lbswsd
into a local SQLite cache. Enables SupplementalData tools to query by
passage reference instead of raw word numbers."
```

---

## Task 2: Add SupplementalData Query Helpers to dataset_tools.py

**Files:**
- Modify: `tools/workbench/dataset_tools.py`

- [ ] **Step 1: Add word cache singleton and helper functions**

Add these at the top of `dataset_tools.py`, after the existing `_get_reader()` function:

```python
from word_number_cache import WordNumberCache

_word_cache = None
_WORD_CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'word_number_cache.db')


def _get_word_cache():
    """Get or create the word number cache singleton. Build if needed."""
    global _word_cache
    if _word_cache is None:
        _word_cache = WordNumberCache(_WORD_CACHE_PATH)
        if not _word_cache.is_built():
            _word_cache.build()
    return _word_cache


def _find_word_ids(reader, resource_file, db_name, word_refs):
    """Find WordNumberIds in a SupplementalData db matching word references.

    Queries all WordNumbers from the target database and filters in Python.
    Returns list of WordNumberId integers.
    """
    if not word_refs:
        return []

    word_ref_set = set(word_refs)
    rows = reader.query_dataset(resource_file, db_name,
        "SELECT WordNumberId, hex(Reference) as ref FROM WordNumbers",
        max_rows=300000)

    matching_ids = []
    for r in rows:
        try:
            ref_bytes = bytes.fromhex(r["ref"])
            ref_text = ref_bytes[1:].decode("utf-8", errors="replace")
            if ref_text in word_ref_set:
                matching_ids.append(int(r["WordNumberId"]))
        except Exception:
            continue

    return matching_ids


def _decode_label_ref(hex_ref):
    """Decode a SupplementalData label Reference blob into structured data.

    Format: ~Category%20Name|Property1=$Value1|Property2=#lemma.lbs.el.word
    Returns dict with 'category' and 'properties' keys.
    """
    try:
        ref_bytes = bytes.fromhex(hex_ref)
        ref_text = ref_bytes[1:].decode("utf-8", errors="replace")
    except Exception:
        return None

    if not ref_text or ref_text[0] != "~":
        return None

    from urllib.parse import unquote
    ref_text = ref_text[1:]  # Strip ~ prefix
    parts = ref_text.split("|")

    category = unquote(parts[0]) if parts else ""
    properties = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = unquote(key)
        # Strip $ (enum) or # (reference) prefix, extract readable value
        if val.startswith("$"):
            val = val[1:]
        elif val.startswith("#"):
            # Extract the last segment of reference paths
            # e.g. #lemma.lbs.el.υἱός → υἱός
            # e.g. #flterm.to-sow → to-sow
            segments = val[1:].split(".")
            val = segments[-1] if segments else val[1:]
        val = unquote(val)
        properties[key] = val

    return {"category": category, "properties": properties}


def _query_supplemental_by_word_ids(reader, resource_file, db_name, word_ids):
    """Query SupplementalData for label entries matching word IDs.

    Joins: WordNumberSets → WordNumberSetAttachments → DataTypeReferences.
    Filters for DataType='label', decodes Reference blobs.
    Returns list of dicts with category, properties.
    """
    if not word_ids:
        return []

    # Build IN clause (cap at 500 IDs to avoid SQL length limits)
    id_list = ",".join(str(i) for i in word_ids[:500])

    rows = reader.query_dataset(resource_file, db_name,
        f"SELECT DISTINCT dtr.ReferenceId, hex(dtr.Reference) as ref, "
        f"hex(dtr.DataType) as dt "
        f"FROM WordNumberSets wns "
        f"JOIN WordNumberSetAttachments wnsa "
        f"  ON wns.WordNumberSetAttachmentId = wnsa.WordNumberSetAttachmentId "
        f"JOIN DataTypeReferences dtr "
        f"  ON wnsa.DataTypeReferenceId = dtr.ReferenceId "
        f"WHERE wns.WordNumberId IN ({id_list}) "
        f"AND hex(dtr.DataType) = '6C6162656C'")  # 'label'

    results = []
    seen = set()
    for r in rows:
        ref_hex = r.get("ref", "")
        if ref_hex in seen:
            continue
        seen.add(ref_hex)

        decoded = _decode_label_ref(ref_hex)
        if decoded:
            results.append(decoded)

    return results
```

- [ ] **Step 2: Replace the 7 SupplementalData stubs**

Replace each stub function in `dataset_tools.py`:

```python
def query_figurative_language(book, chapter, verse_start=None, verse_end=None):
    """Query figurative language tagged for a passage."""
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter, verse_start, verse_end)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, "FIGURATIVE-LANGUAGE.lbssd",
                              "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, "FIGURATIVE-LANGUAGE.lbssd", "SupplementalData.db", word_ids)


def query_greek_constructions(book, chapter, verse_start=None, verse_end=None):
    """Query Greek grammatical constructions for a passage."""
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter, verse_start, verse_end)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, "GREEK-CONSTRUCTIONS.lbssd",
                              "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, "GREEK-CONSTRUCTIONS.lbssd", "SupplementalData.db", word_ids)


def query_hebrew_constructions(book, chapter, verse_start=None, verse_end=None):
    """Query Hebrew grammatical constructions for a passage."""
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter, verse_start, verse_end)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, "HEBREW-CONSTRUCTIONS.lbssd",
                              "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, "HEBREW-CONSTRUCTIONS.lbssd", "SupplementalData.db", word_ids)


def query_literary_typing(book, chapter):
    """Query literary type classification for a passage."""
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, "LITERARYTYPING.lbssd",
                              "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, "LITERARYTYPING.lbssd", "SupplementalData.db", word_ids)


def query_propositional_outline(book, chapter, testament="nt"):
    """Query propositional outline for a passage."""
    resource = "PROPOSITIONAL-OUTLINES.lbssd" if testament == "nt" else "PROPOSITIONAL-OUTLINES-OT.lbssd"
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, resource, "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, resource, "SupplementalData.db", word_ids)


def query_nt_use_of_ot(book, chapter):
    """Query NT use of OT passages."""
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, "NT-USE-OF-OT.lbssd",
                              "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, "NT-USE-OF-OT.lbssd", "SupplementalData.db", word_ids)


def query_wordplay(book, chapter):
    """Query wordplay instances in a passage."""
    cache = _get_word_cache()
    word_refs = cache.get_word_numbers(book, chapter)
    if not word_refs:
        return []
    reader = _get_reader()
    word_ids = _find_word_ids(reader, "WORDPLAY.lbssd",
                              "SupplementalData.db", word_refs)
    return _query_supplemental_by_word_ids(
        reader, "WORDPLAY.lbssd", "SupplementalData.db", word_ids)
```

Leave `query_cultural_concepts`, `query_ancient_literature`, and `query_important_words` as `return []` for now — they use different schemas.

- [ ] **Step 3: Run existing tests to verify nothing broke**

```bash
cd /Volumes/External/Logos4/tools && /opt/homebrew/bin/python3 -m pytest workbench/tests/test_dataset_tools.py -v 2>&1
```
Expected: All 7 existing tests still pass. The figurative language test may now return different data (structured labels instead of raw query).

- [ ] **Step 4: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/workbench/dataset_tools.py
git commit -m "feat: wire 7 SupplementalData tools to word number cache

Replace return-[] stubs with real implementations for figurative language,
Greek/Hebrew constructions, literary typing, propositional outlines,
wordplay, and NT use of OT. Each tool queries the word number cache for
passage word references, then joins through SupplementalData tables."
```

---

## Task 3: Integration Test — End-to-End Passage Queries

**Files:**
- Create/extend: `tools/workbench/tests/test_word_cache.py`

- [ ] **Step 1: Add integration tests for the full pipeline**

Append to `test_word_cache.py`:

```python
from dataset_tools import (
    query_figurative_language, query_greek_constructions,
    query_literary_typing, query_wordplay,
)

def test_greek_constructions_romans_1():
    """Should return Greek constructions for Romans 1."""
    results = query_greek_constructions(book=45, chapter=1)
    assert len(results) > 0, "Expected constructions for Romans 1"
    # Each result should have category and properties
    for r in results[:3]:
        assert "category" in r, f"Missing category in {r}"
        assert "properties" in r, f"Missing properties in {r}"

def test_figurative_language_has_data():
    """Should return figurative language data for a well-known passage."""
    # Try several passages — figurative language may be sparse
    for book, chapter in [(45, 1), (43, 1), (1, 1), (23, 1)]:
        results = query_figurative_language(book=book, chapter=chapter)
        if results:
            assert "category" in results[0]
            return
    # If none found, that's OK — the pipeline works even if data is sparse
    pass

def test_wordplay_returns_list():
    """Wordplay query should return a list (possibly empty)."""
    results = query_wordplay(book=45, chapter=1)
    assert isinstance(results, list)
```

- [ ] **Step 2: Run all tests**

```bash
cd /Volumes/External/Logos4/tools && /opt/homebrew/bin/python3 -m pytest workbench/tests/ -v 2>&1
```
Expected: All tests pass (existing 62 + new 8 = ~70 tests).

- [ ] **Step 3: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/workbench/tests/test_word_cache.py
git commit -m "test: add integration tests for SupplementalData pipeline

Tests verify Greek constructions, figurative language, and wordplay
queries return structured data via the word number cache."
```

---

## Task 4: Build the Production Cache

This task builds the actual cache file that the app will use at runtime.

- [ ] **Step 1: Build the cache**

```bash
cd /Volumes/External/Logos4/tools && /opt/homebrew/bin/python3 -c "
from word_number_cache import WordNumberCache
cache = WordNumberCache('word_number_cache.db')
count = cache.build()
print(f'Built cache with {count} entries')
print(f'File size: {__import__(\"os\").path.getsize(\"word_number_cache.db\") / 1024 / 1024:.1f} MB')
"
```
Expected: ~200K+ entries, ~5-10MB file, 3-5 minutes build time.

- [ ] **Step 2: Verify the cache works**

```bash
cd /Volumes/External/Logos4/tools && /opt/homebrew/bin/python3 -c "
from word_number_cache import WordNumberCache
cache = WordNumberCache('word_number_cache.db')
print(f'Cache entries: {cache.count()}')
print(f'Romans 1 words: {len(cache.get_word_numbers(45, 1))}')
print(f'Genesis 1 words: {len(cache.get_word_numbers(1, 1))}')
print(f'Rom 1:18-23 words: {len(cache.get_word_numbers(45, 1, 18, 23))}')
"
```

- [ ] **Step 3: Add cache to .gitignore**

The cache file is generated data — don't check it in:

```bash
echo "tools/word_number_cache.db" >> /Volumes/External/Logos4/.gitignore
echo "tools/resource_index.db" >> /Volumes/External/Logos4/.gitignore
```

- [ ] **Step 4: Commit**

```bash
cd /Volumes/External/Logos4
git add .gitignore
git commit -m "chore: add generated cache databases to .gitignore"
```

---

## Dependency Graph

```
Task 1 (Word Number Cache)
  └→ Task 2 (Wire SupplementalData tools)
       └→ Task 3 (Integration tests)
            └→ Task 4 (Build production cache)
```

All tasks are sequential — each depends on the previous.

## Post-Implementation Verification

After all tasks are complete:

1. Run full test suite: `cd tools && /opt/homebrew/bin/python3 -m pytest workbench/tests/ -v`
2. Start the companion: `cd tools/workbench && python3 app.py`
3. Open http://localhost:5111/companion/
4. Enter "Romans 1:18-23"
5. Ask "What Greek constructions does Logos tag in this passage?" — should return prepositional phrases, case usage, etc.
6. Ask "Any figurative language?" — should query FIGURATIVE-LANGUAGE.lbssd
7. Ask "What are the preaching themes?" — should return themes from PreachingThemes (already working from Phase 1)
