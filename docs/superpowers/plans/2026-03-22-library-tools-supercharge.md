# Library Tools Supercharge — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the sermon companion's library access actually work — fix broken lexicon/grammar search, unlock encrypted dataset files, and wire up 30+ tools so the companion can be a real graduate assistant.

**Architecture:** Three phases that build on each other. Phase 1 fixes the search index so existing tools work. Phase 2 adds EncryptedVolume P/Invoke to LogosReader so we can query encrypted SQLite databases inside .lbs* files. Phase 3 wires up companion tools for each workflow step. Each phase is independently testable and committable.

**Tech Stack:** C# .NET 8 (LogosReader P/Invoke), Python 3 (companion tools), SQLite (index cache + encrypted volume queries), libSinaiInterop.dylib + libsqlite3-logos.dylib (native libraries)

**Key Reference Docs:**
- Encrypted Volume API research: `docs/plans/2026-03-10-encrypted-volume-api.md`
- Companion design spec: `docs/specs/2026-03-21-sermon-companion-design.md`
- Existing companion tools: `tools/workbench/companion_tools.py`
- LogosReader: `tools/LogosReader/Program.cs`
- Study orchestrator: `tools/study.py`
- Batch reader: `tools/logos_batch.py`

**Environment Setup (required for all tasks):**
```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

---

## File Structure

### New files:
```
tools/
├── resource_index.py           — One-time index builder: Greek lemma → article#, grammar topic → article range
├── workbench/
│   ├── dataset_tools.py        — EncryptedVolume dataset tool implementations (figurative language, constructions, etc.)
│   └── tests/
│       ├── test_resource_index.py
│       └── test_dataset_tools.py
```

### Modified files:
```
tools/
├── LogosReader/Program.cs      — Add EncryptedVolume P/Invoke + query-db + volume-info batch commands
├── logos_batch.py              — Add query_dataset() and volume_info() methods
├── study.py                    — Add lookup_in_index(), build_resource_index() functions
├── workbench/
│   ├── companion_tools.py      — Rewrite _search_lexicon() to use index; add dataset tool dispatching
│   └── companion_agent.py      — Update system prompt with new tool descriptions
```

---

## Phase 1: Fix Lexicon & Grammar Search

**Problem:** `_search_lexicon()` in `companion_tools.py` searches article IDs for Greek text, but article IDs are transliterated Latin with inconsistencies (e.g., `MATIOVW` for ματαιόω, `G16W22` for Wallace chapter 16). The content search fallback samples 200/12,000 articles — a 1.6% hit rate.

**Solution:** Build a one-time index that reads the first line of every article (which contains the Greek/Hebrew headword for lexicons and the section title for grammars), extracts the headword, and maps it to the article number. Store in SQLite. Subsequent lookups are sub-millisecond.

### Task 1: Build Resource Index

**Files:**
- Create: `tools/resource_index.py`
- Create: `tools/workbench/tests/test_resource_index.py`

- [ ] **Step 1: Write the failing test for lemma index building**

```python
# tools/workbench/tests/test_resource_index.py
import os
import sys
import sqlite3
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from resource_index import ResourceIndex

# Integration test — requires LogosReader and actual resource files
# Skip if not available
EDNT_FILE = "EXGDCTNT.logos4"

@pytest.fixture
def index_db():
    """Create a temp DB for the index."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)

def test_build_lexicon_index(index_db):
    """Building an index for EDNT should produce entries with Greek headwords."""
    idx = ResourceIndex(index_db)
    count = idx.build_index_for_resource(EDNT_FILE, resource_type="lexicon")
    assert count > 1000, f"Expected 1000+ entries, got {count}"

    # Should find ματαιόω (article #7428, ID = MATIOVW)
    results = idx.lookup("μαται", EDNT_FILE)
    assert len(results) > 0, "Should find entries matching μαται"
    # Check that we got the right article
    art_ids = [r["article_id"] for r in results]
    assert any("MATAI" in aid.upper() or "MATI" in aid.upper() for aid in art_ids), \
        f"Expected MATAI* article, got {art_ids}"

def test_build_grammar_index(index_db):
    """Building an index for Wallace should map chapter topics to article ranges."""
    idx = ResourceIndex(index_db)
    count = idx.build_index_for_resource("GRKGRAMBBWALLACE.logos4", resource_type="grammar")
    assert count > 20, f"Expected 20+ chapter entries, got {count}"

    # Should find voice-related content via chapter 16
    results = idx.lookup("voice", "GRKGRAMBBWALLACE.logos4")
    assert len(results) > 0, "Should find voice-related entries"

def test_lookup_nonexistent(index_db):
    """Lookup in empty index returns empty list."""
    idx = ResourceIndex(index_db)
    results = idx.lookup("ματαιόω", "nonexistent.logos4")
    assert results == []

def test_lookup_transliterated(index_db):
    """Should find entries by transliterated form too."""
    idx = ResourceIndex(index_db)
    idx.build_index_for_resource(EDNT_FILE, resource_type="lexicon")
    results = idx.lookup("mataio", EDNT_FILE)
    assert len(results) > 0, "Should find entries by transliterated search"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_resource_index.py -v 2>&1 | head -30
```
Expected: FAIL with "No module named 'resource_index'"

- [ ] **Step 3: Write resource_index.py**

```python
# tools/resource_index.py
"""One-time index builder for lexicon and grammar resources.

Reads article headwords (first line of each article) and builds a SQLite
index mapping searchable terms → article numbers. This replaces the broken
content-sampling search in companion_tools.py.

Usage:
    idx = ResourceIndex("path/to/index.db")
    idx.build_index_for_resource("EXGDCTNT.logos4", resource_type="lexicon")
    results = idx.lookup("ματαιόω", "EXGDCTNT.logos4")
"""
import os
import re
import sqlite3
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
from logos_batch import LogosBatchReader

# Wallace chapter structure: chapter prefix → topic
# Derived from manual inspection of article ID patterns and content

# NOTE: These chapter mappings are APPROXIMATE — derived from content inspection
# of G## article prefixes, NOT from Wallace's printed chapter numbers.
# The Logos .logos4 file uses its own article grouping prefixes.
# Task 1 Step 3 includes a verification substep to confirm/correct these.
WALLACE_CHAPTERS = {
    "G01": "Introduction to Syntax",
    "G02": "The Cases: Overview",
    "G03": "Nominative Case",
    "G04": "Vocative Case",
    "G05": "Genitive Case",
    "G06": "Dative Case",
    "G07": "Accusative Case",
    "G08": "The Article: Overview",
    "G09": "The Article: Special Uses and Non-Uses",
    "G10": "Adjectives",
    "G11": "Pronouns",
    "G12": "Prepositions",
    "G13": "Person and Number",
    "G14": "Voice: Active, Middle, Passive",
    "G15": "Mood: Overview, Indicative, Subjunctive, Optative, Imperative",
    "G16": "The Tenses: Overview, Present, Imperfect",
    "G17": "Aorist, Future, Perfect, Pluperfect",
    "G18A": "Infinitive",
    "G18B": "Infinitive continued",
    "G18C": "Participle: Adverbial",
    "G18D": "Participle: Adjectival",
    "G18E": "Participle: Substantival, Independent, Genitive Absolute",
    "G18F": "Participle: Periphrastic, Redundant",
    "G19": "Clauses: Relative, Conditional, Causal, Temporal, Result, Purpose",
    "G20": "Word Order, Sentences",
    "G21A": "Discourse Analysis: Cohesion",
    "G21B": "Discourse Analysis: Prominence",
    "G21C": "Discourse Analysis continued",
    "G21D": "Discourse Analysis continued",
}

# Topics to add as searchable keywords for each Wallace chapter
WALLACE_TOPICS = {
    "G03": ["nominative", "subject", "predicate nominative", "nominative absolute"],
    "G05": ["genitive", "possessive", "subjective genitive", "objective genitive",
             "partitive", "genitive absolute", "ablative"],
    "G06": ["dative", "indirect object", "instrumental", "locative", "dative of advantage"],
    "G07": ["accusative", "direct object", "double accusative"],
    "G08": ["article", "definite article", "anarthrous"],
    "G14": ["voice", "active voice", "middle voice", "passive voice", "deponent",
             "middle passive", "reflexive", "causative"],
    "G15": ["mood", "indicative", "subjunctive", "optative", "imperative",
             "prohibition", "hortatory", "deliberative"],
    "G16": ["tense", "present tense", "imperfect", "progressive", "iterative",
             "gnomic", "historical present", "conative", "customary"],
    "G17": ["aorist", "future", "perfect", "pluperfect", "constative",
             "ingressive", "consummative", "gnomic aorist", "epistolary aorist",
             "proleptic", "intensive perfect", "dramatic aorist"],
    "G18A": ["infinitive", "purpose", "result", "complementary", "substantival infinitive"],
    "G18C": ["participle", "adverbial participle", "temporal", "causal", "conditional",
              "concessive", "purpose participle", "result participle", "attendant circumstance"],
    "G18D": ["adjectival participle", "attributive", "predicate"],
    "G18E": ["substantival participle", "genitive absolute", "independent participle",
              "periphrastic"],
    "G19": ["clause", "relative clause", "conditional", "first class condition",
             "second class condition", "third class condition", "fourth class condition",
             "causal clause", "temporal clause", "result clause", "purpose clause",
             "concessive clause"],
}


class ResourceIndex:
    """SQLite-backed index for fast lexicon/grammar lookups."""

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
            CREATE TABLE IF NOT EXISTS resource_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_file TEXT NOT NULL,
                article_num INTEGER NOT NULL,
                article_id TEXT NOT NULL,
                headword TEXT,          -- Greek/Hebrew headword (original script)
                headword_translit TEXT,  -- Transliterated/normalized form
                gloss TEXT,             -- English gloss if available
                entry_type TEXT,        -- 'lemma', 'topic', 'chapter'
                UNIQUE(resource_file, article_num)
            );
            CREATE INDEX IF NOT EXISTS idx_headword ON resource_entries(headword);
            CREATE INDEX IF NOT EXISTS idx_translit ON resource_entries(headword_translit);
            CREATE INDEX IF NOT EXISTS idx_gloss ON resource_entries(gloss);
            CREATE INDEX IF NOT EXISTS idx_resource ON resource_entries(resource_file);
        """)
        conn.commit()
        conn.close()

    def build_index_for_resource(self, resource_file, resource_type="lexicon"):
        """Build the index for a resource by reading article headwords.

        For lexicons: reads first line of each article, extracts Greek/Hebrew headword.
        For grammars: uses chapter structure + topic keywords.

        Returns count of entries indexed.
        """
        if resource_type == "grammar":
            return self._build_grammar_index(resource_file)
        else:
            return self._build_lexicon_index(resource_file)

    def _build_lexicon_index(self, resource_file):
        """Read first line of every article and extract headword."""
        reader = LogosBatchReader()
        try:
            articles = reader.list_articles(resource_file)
            if not articles:
                return 0

            conn = self._conn()
            # Clear existing entries for this resource
            conn.execute("DELETE FROM resource_entries WHERE resource_file = ?",
                         (resource_file,))

            count = 0
            batch = []
            for art_num, art_id in articles:
                # Skip abbreviation entries and footnotes
                if art_id.startswith("ABBR") or art_id.startswith("FTN"):
                    continue

                # Read first 300 chars to get headword line
                text = reader.read_article(resource_file, art_num, max_chars=300)
                if not text or len(text.strip()) < 3:
                    continue

                headword, translit, gloss = self._extract_headword(text)
                if not headword and not translit:
                    # Use article ID as fallback transliteration
                    translit = art_id.lower()

                batch.append((
                    resource_file, art_num, art_id,
                    headword, translit, gloss, "lemma"
                ))
                count += 1

                # Insert in batches of 500
                if len(batch) >= 500:
                    conn.executemany(
                        """INSERT OR REPLACE INTO resource_entries
                           (resource_file, article_num, article_id, headword,
                            headword_translit, gloss, entry_type)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        batch
                    )
                    conn.commit()
                    batch = []

            if batch:
                conn.executemany(
                    """INSERT OR REPLACE INTO resource_entries
                       (resource_file, article_num, article_id, headword,
                        headword_translit, gloss, entry_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    batch
                )
                conn.commit()

            conn.close()
            return count
        finally:
            reader.close()

    def _extract_headword(self, text):
        """Extract Greek/Hebrew headword, transliteration, and gloss from article first line.

        EDNT format: "ματαιότης, ητος, ἡ   mataiotēs   vanity, nothingness﻿*﻿"
        BDB format:  "כָּבוֹד   kāḇôḏ   glory, honour"
        Louw-Nida:   "88.150 ματαιόω" or prose description
        """
        first_line = text.split('\n')[0].strip()

        # Extract Greek headword (first Greek word cluster)
        # Allow single-character headwords (e.g., preposition ἐν)
        greek_match = re.search(r'([\u0370-\u03FF\u1F00-\u1FFF][\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F,\s]*)', first_line)
        hebrew_match = re.search(r'([\u0590-\u05FF][\u0590-\u05FF\u0300-\u036F\s]*)', first_line)

        headword = None
        if greek_match:
            headword = greek_match.group(1).split(',')[0].split()[0].strip()
        elif hebrew_match:
            headword = hebrew_match.group(1).split()[0].strip()

        # Extract transliteration (Latin chars between the original script and gloss)
        translit = None
        # Common pattern: Greek   transliteration   English gloss
        parts = re.split(r'\s{2,}', first_line)
        if len(parts) >= 2:
            for part in parts[1:]:
                part = part.strip().rstrip('*\ufeff')
                # Transliteration: mostly lowercase Latin with macrons/accents
                if part and re.match(r'^[a-zA-Zāēīōūàèìòùáéíóúâêîôûäëïöü\-ʾʿ]+$', part):
                    translit = part.lower()
                    break

        # Extract English gloss
        gloss = None
        if len(parts) >= 3:
            # Last meaningful part is usually the gloss
            for part in reversed(parts):
                part = part.strip().rstrip('*\ufeff')
                if part and re.match(r'^[a-zA-Z]', part) and not re.match(r'^[a-zA-Zāēīōūàèìòùáéíóúâêîôûäëïöü\-ʾʿ]+$', part):
                    gloss = part.lower()
                    break

        # Normalize headword for searching
        if headword:
            # Strip accents for normalized form
            nfkd = unicodedata.normalize('NFKD', headword)
            translit_from_greek = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()
            if not translit:
                translit = translit_from_greek

        return headword, translit, gloss

    def _build_grammar_index(self, resource_file):
        """Build index for grammar using chapter structure + topic keywords."""
        reader = LogosBatchReader()
        try:
            articles = reader.list_articles(resource_file)
            if not articles:
                return 0

            conn = self._conn()
            conn.execute("DELETE FROM resource_entries WHERE resource_file = ?",
                         (resource_file,))

            count = 0
            # Determine chapter prefix → article range
            chapter_ranges = {}
            for art_num, art_id in articles:
                # Extract chapter prefix (e.g., G16 from G16W22)
                match = re.match(r'(G\d+[A-F]?|CH\d+|PT\d+|SSC|IDX|SYN)', art_id)
                if match:
                    prefix = match.group(1)
                    if prefix not in chapter_ranges:
                        chapter_ranges[prefix] = {"start": art_num, "end": art_num, "art_id_start": art_id}
                    chapter_ranges[prefix]["end"] = art_num

            # Index chapters with their topics
            for prefix, info in chapter_ranges.items():
                topic = WALLACE_CHAPTERS.get(prefix, prefix)
                keywords = WALLACE_TOPICS.get(prefix, [])

                # Insert the chapter entry
                conn.execute(
                    """INSERT OR REPLACE INTO resource_entries
                       (resource_file, article_num, article_id, headword,
                        headword_translit, gloss, entry_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (resource_file, info["start"], info["art_id_start"],
                     topic, prefix.lower(), topic.lower(), "chapter")
                )
                count += 1

                # Insert keyword entries pointing to the same chapter
                for kw in keywords:
                    conn.execute(
                        """INSERT INTO resource_entries
                           (resource_file, article_num, article_id, headword,
                            headword_translit, gloss, entry_type)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (resource_file, info["start"], info["art_id_start"],
                         kw, kw.lower(), topic.lower(), "topic")
                    )
                    count += 1

            conn.commit()
            conn.close()
            return count
        finally:
            reader.close()

    def lookup(self, query, resource_file, limit=5):
        """Look up a word or topic in the index.

        Searches headword (Greek/Hebrew), transliterated form, gloss, and article ID.
        Returns list of {article_num, article_id, headword, gloss, entry_type, score}.
        """
        conn = self._conn()
        query_lower = query.lower().strip()

        # Strip accents from query for normalized matching
        query_norm = unicodedata.normalize('NFKD', query_lower)
        query_norm = ''.join(c for c in query_norm if not unicodedata.combining(c))

        results = []

        # 1. Exact headword match (Greek/Hebrew)
        rows = conn.execute(
            """SELECT article_num, article_id, headword, gloss, entry_type
               FROM resource_entries
               WHERE resource_file = ? AND headword = ?
               LIMIT ?""",
            (resource_file, query.strip(), limit)
        ).fetchall()
        for r in rows:
            results.append({**dict(r), "score": 100})

        # 2. Headword prefix match
        if len(results) < limit:
            rows = conn.execute(
                """SELECT article_num, article_id, headword, gloss, entry_type
                   FROM resource_entries
                   WHERE resource_file = ? AND headword LIKE ? AND headword != ?
                   LIMIT ?""",
                (resource_file, query.strip() + '%', query.strip(), limit - len(results))
            ).fetchall()
            for r in rows:
                results.append({**dict(r), "score": 80})

        # 3. Transliterated/normalized match
        if len(results) < limit:
            rows = conn.execute(
                """SELECT article_num, article_id, headword, gloss, entry_type
                   FROM resource_entries
                   WHERE resource_file = ? AND headword_translit LIKE ?
                   LIMIT ?""",
                (resource_file, '%' + query_norm + '%', limit - len(results))
            ).fetchall()
            for r in rows:
                if not any(existing["article_num"] == r["article_num"] for existing in results):
                    results.append({**dict(r), "score": 60})

        # 4. Gloss match
        if len(results) < limit:
            rows = conn.execute(
                """SELECT article_num, article_id, headword, gloss, entry_type
                   FROM resource_entries
                   WHERE resource_file = ? AND gloss LIKE ?
                   LIMIT ?""",
                (resource_file, '%' + query_lower + '%', limit - len(results))
            ).fetchall()
            for r in rows:
                if not any(existing["article_num"] == r["article_num"] for existing in results):
                    results.append({**dict(r), "score": 40})

        # 5. Article ID match (fallback)
        if len(results) < limit:
            rows = conn.execute(
                """SELECT article_num, article_id, headword, gloss, entry_type
                   FROM resource_entries
                   WHERE resource_file = ? AND article_id LIKE ?
                   LIMIT ?""",
                (resource_file, '%' + query_lower.upper() + '%', limit - len(results))
            ).fetchall()
            for r in rows:
                if not any(existing["article_num"] == r["article_num"] for existing in results):
                    results.append({**dict(r), "score": 20})

        conn.close()
        return sorted(results, key=lambda x: -x["score"])[:limit]

    def is_indexed(self, resource_file):
        """Check if a resource has been indexed."""
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM resource_entries WHERE resource_file = ?",
            (resource_file,)
        ).fetchone()
        conn.close()
        return row["cnt"] > 0
```

- [ ] **Step 3b: Verify Wallace chapter mapping**

Before running tests, verify the G## → topic mapping by reading the first substantial article in each prefix. The mapping was derived from content inspection but article groupings may differ from Wallace's printed chapter numbers.

```bash
cd /Volumes/External/Logos4/tools && python3 -c "
from logos_batch import LogosBatchReader
reader = LogosBatchReader()
# Check content of first article in each key chapter
for prefix, start in [('G14', 1079), ('G15', 1054), ('G16', 1079)]:
    text = reader.read_article('GRKGRAMBBWALLACE.logos4', start, max_chars=200)
    print(f'{prefix} #{start}: {text[:150] if text else \"EMPTY\"}')
    print()
reader.close()
"
```

If the content doesn't match the expected topic, correct the `WALLACE_CHAPTERS` mapping. Known confirmed: G16 articles (1095-1102) contain voice/middle/passive discussion.

- [ ] **Step 4: Run tests**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_resource_index.py -v 2>&1
```
Expected: Tests pass. `test_build_lexicon_index` should find μαται entries. `test_build_grammar_index` should find voice entries.

Note: These are integration tests that require the LogosReader subprocess and actual `.logos4` files. They will be slow (~30-60 seconds) on first run because they index thousands of articles.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/resource_index.py tools/workbench/tests/test_resource_index.py
git commit -m "feat: add resource index for fast lexicon/grammar lookups

Replaces broken content-sampling search with a one-time index that reads
article headwords and maps Greek/Hebrew lemmas to article numbers.
Includes Wallace chapter-topic mapping for grammar navigation."
```

---

### Task 2: Rewrite companion_tools Search to Use Index

**Files:**
- Modify: `tools/workbench/companion_tools.py` (rewrite `_search_lexicon`, `_lookup_lexicon`, `_lookup_grammar`)

- [ ] **Step 1: Write failing test for index-based lookup**

```python
# Add to tools/workbench/tests/test_companion_tools.py (or create if missing)
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from companion_tools import _lookup_lexicon, _lookup_grammar

@pytest.fixture
def session_ctx():
    return {"book": 66, "chapter": 1, "verse_start": 21, "verse_end": 21, "genre": "epistle"}

def test_lookup_lexicon_finds_greek_word(session_ctx):
    """lookup_lexicon should find ματαιόω in EDNT."""
    result = _lookup_lexicon({"word": "ματαιό"}, session_ctx)
    assert len(result["entries"]) > 0, f"Expected entries, got {result}"
    # Check that at least one entry has real content (not just ABBR.*)
    has_real = any(len(e.get("text", "")) > 50 for e in result["entries"])
    assert has_real, "Expected real article content, not abbreviation stubs"

def test_lookup_grammar_finds_voice(session_ctx):
    """lookup_grammar should find Wallace's discussion of middle/passive voice."""
    result = _lookup_grammar({"query": "middle voice"}, session_ctx)
    assert len(result["entries"]) > 0, f"Expected entries, got {result}"
    # Should be substantial content about voice, not ABBR.MID
    has_real = any(len(e.get("text", "")) > 200 for e in result["entries"])
    assert has_real, "Expected real grammar content about voice"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_companion_tools.py::test_lookup_lexicon_finds_greek_word -v 2>&1
```
Expected: FAIL or returns ABBR.* stubs (broken search)

- [ ] **Step 3: Rewrite _search_lexicon and related functions in companion_tools.py**

Replace the `_search_lexicon` function and update `_lookup_lexicon` and `_lookup_grammar` to use the resource index. Key changes:

1. Add a module-level `ResourceIndex` singleton (lazy-initialized)
2. On first call, check if the resource is indexed; if not, build the index
3. Use `idx.lookup()` to find article numbers, then `read_article_text()` to get content
4. Fall back to old content search if index returns nothing

```python
# At top of companion_tools.py, add:
from resource_index import ResourceIndex

# Module-level index singleton
_resource_index = None
_INDEX_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'resource_index.db')

def _get_index():
    global _resource_index
    if _resource_index is None:
        _resource_index = ResourceIndex(_INDEX_DB_PATH)
    return _resource_index

def _ensure_indexed(resource_file, resource_type="lexicon"):
    """Ensure a resource is indexed. Build index on first use."""
    idx = _get_index()
    if not idx.is_indexed(resource_file):
        idx.build_index_for_resource(resource_file, resource_type=resource_type)
    return idx
```

Replace `_search_lexicon`:

```python
def _search_lexicon(resource_file, abbrev, word, resource_type="lexicon"):
    """Search a lexicon/grammar using the pre-built index."""
    try:
        idx = _ensure_indexed(resource_file, resource_type=resource_type)
        results = idx.lookup(word, resource_file, limit=3)

        if not results:
            return None

        # Read the best match article
        best = results[0]
        text = read_article_text(resource_file, best["article_num"], max_chars=8000)
        if not text:
            return None

        return {
            "lexicon": abbrev,
            "article_id": best["article_id"],
            "headword": best.get("headword", ""),
            "text": text[:6000] if len(text) > 6000 else text,
        }
    except Exception:
        return None
```

Update `_lookup_grammar` to pass `resource_type="grammar"`:

```python
def _lookup_grammar(tool_input, session_context):
    query = tool_input["query"]
    requested_grammars = tool_input.get("grammars")
    testament = tool_input.get("testament", "nt")

    if requested_grammars:
        grammars = [g for g in ALL_GRAMMARS if g["abbrev"] in requested_grammars]
        if not grammars:
            grammars = NT_GRAMMARS[:2] if testament == "nt" else OT_GRAMMARS[:1]
    else:
        grammars = NT_GRAMMARS[:3] if testament == "nt" else OT_GRAMMARS

    results = []
    for gram in grammars:
        entry = _search_lexicon(gram["file"], gram["abbrev"], query, resource_type="grammar")
        if entry:
            results.append(entry)
        if len(results) >= 2:
            break

    return {
        "query": query,
        "testament": testament,
        "entries": results,
        "searched": [g["abbrev"] for g in grammars],
    }
```

- [ ] **Step 4: Run tests**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_companion_tools.py -v 2>&1
```
Expected: Both new tests pass. `test_lookup_lexicon_finds_greek_word` finds real EDNT content. `test_lookup_grammar_finds_voice` finds Wallace voice discussion.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/workbench/companion_tools.py
git commit -m "fix: rewrite lexicon/grammar search to use pre-built index

Replaces broken content-sampling search (200/12000 articles = 1.6% hit rate)
with index-based lookup. First call builds the index by reading article
headwords; subsequent lookups are sub-millisecond."
```

---

## Phase 2: Unlock Encrypted Volume API

**Problem:** 150+ `.lbs*` files contain pre-indexed study tool databases (figurative language, grammatical constructions, biblical places, cross-references, etc.). These are encrypted SQLite databases that require the EncryptedVolume API to open. The API exists in libSinaiInterop.dylib but isn't implemented in LogosReader.

**Solution:** Add P/Invoke declarations for EncryptedVolume_* and sqlite3_* functions to LogosReader. Add a `query-db` batch command that opens an encrypted volume, opens its embedded SQLite database, runs a SQL query, and returns TSV results. Wrap in Python via logos_batch.py.

### Task 3: Add EncryptedVolume P/Invoke to LogosReader

**Files:**
- Modify: `tools/LogosReader/Program.cs`

- [ ] **Step 1: Add EncryptedVolume P/Invoke declarations**

Add after the existing interlinear P/Invoke declarations (around line 200 in Program.cs):

```csharp
// ── EncryptedVolume API ──────────────────────────────────────────────
// Opens encrypted dataset files (.lbssd, .lbsxrf, .lbsplc, .lbsthg, etc.)
// These contain embedded SQLite databases with structured study tool data.

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern IntPtr EncryptedVolume_New();

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.U1)]
static extern bool EncryptedVolume_Open(
    IntPtr ptr,
    IntPtr pLicenseManager,
    [MarshalAs(UnmanagedType.LPWStr)] string filePath);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern IntPtr EncryptedVolume_OpenDatabase(
    IntPtr ptr,
    [MarshalAs(UnmanagedType.LPWStr)] string strFileName);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern IntPtr EncryptedVolume_OpenFile(
    IntPtr ptr,
    [MarshalAs(UnmanagedType.LPWStr)] string strFileName);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetResourceId(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetResourceDriverName(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern void EncryptedVolume_Delete(IntPtr ptr);

// ── SQLite C API (from libsqlite3-logos.dylib bundled with Logos) ────
// Used to query the raw sqlite3* handle returned by EncryptedVolume_OpenDatabase.

const string SqliteLib = "/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/Resources/lib/libsqlite3-logos.dylib";

[DllImport(SqliteLib, EntryPoint = "sqlite3_prepare_v2")]
static extern int sqlite3_prepare_v2(IntPtr db, byte[] sql, int nByte, out IntPtr stmt, out IntPtr tail);

[DllImport(SqliteLib, EntryPoint = "sqlite3_step")]
static extern int sqlite3_step(IntPtr stmt);

[DllImport(SqliteLib, EntryPoint = "sqlite3_column_count")]
static extern int sqlite3_column_count(IntPtr stmt);

[DllImport(SqliteLib, EntryPoint = "sqlite3_column_name")]
static extern IntPtr sqlite3_column_name(IntPtr stmt, int col);

[DllImport(SqliteLib, EntryPoint = "sqlite3_column_text")]
static extern IntPtr sqlite3_column_text(IntPtr stmt, int col);

[DllImport(SqliteLib, EntryPoint = "sqlite3_column_type")]
static extern int sqlite3_column_type(IntPtr stmt, int col);

[DllImport(SqliteLib, EntryPoint = "sqlite3_finalize")]
static extern int sqlite3_finalize(IntPtr stmt);

[DllImport(SqliteLib, EntryPoint = "sqlite3_errmsg")]
static extern IntPtr sqlite3_errmsg(IntPtr db);

// SQLite constants
const int SQLITE_ROW = 100;
const int SQLITE_DONE = 101;
const int SQLITE_OK = 0;
const int SQLITE_NULL = 5;
```

- [ ] **Step 2: Add EncryptedVolume handle caching**

Add static dictionaries near the existing `resourceCache` dictionary in the batch mode method (around line 1030 in the `RunBatchMode` method):

```csharp
// Add alongside existing: var resourceCache = new Dictionary<string, IntPtr>();
var volumeCache = new Dictionary<string, IntPtr>();
var volumeDbCache = new Dictionary<string, IntPtr>();
```

- [ ] **Step 3: Add `query-db` and `volume-info` as special-case batch commands**

**CRITICAL INTEGRATION NOTE:** The existing batch loop structure is:
1. Parse command → switch on cmd → set `mode` and `resourceFile`
2. Resolve resource path (line 1162)
3. Open resource via `OpenResource()` → `SinaiInterop_LoadTitleWithoutDataTypeOptions` (line 1168)
4. Call `ExecuteOperation(title, mode, ...)` (line 1178)
5. Print `---END---` (line 1185)

`query-db` and `volume-info` commands CANNOT go through steps 2-4 because `OpenResource()` uses CTitle loading which fails for `.lbs*` files. These must be handled as **early-exit cases in the switch** that do their own work, print their own output (but NOT `---END---` — the outer loop handles that at line 1185), and then `break` out of the switch with a special `mode` that skips the CTitle path.

Add these cases to the switch (before the `default:` case, around line 1155):

```csharp
                        case "query-db":
                        {
                            if (tokens.Count < 4)
                            {
                                Console.Error.WriteLine("[!] query-db requires: query-db <file> <db-name> <sql>");
                                // Don't print ---END--- here; the outer loop does it
                                mode = "__skip__";
                                resourceFile = "";
                                break;
                            }
                            string volFile = tokens[1];
                            string dbName = tokens[2];
                            // SQL is the 4th token (should be double-quoted in the command)
                            string sql = tokens[3];

                            // Resolve path (same inline logic as line 1162)
                            if (!volFile.Contains("/"))
                                volFile = $"{resourcesBase}/{volFile}";

                            string cacheKey = volFile + "|" + dbName;
                            IntPtr dbHandle;
                            if (!volumeDbCache.TryGetValue(cacheKey, out dbHandle))
                            {
                                IntPtr volHandle;
                                if (!volumeCache.TryGetValue(volFile, out volHandle))
                                {
                                    volHandle = EncryptedVolume_New();
                                    bool opened = EncryptedVolume_Open(volHandle, licMgr, volFile);
                                    if (!opened)
                                    {
                                        Console.Error.WriteLine($"[!] Failed to open volume: {volFile}");
                                        mode = "__skip__";
                                        resourceFile = "";
                                        break;
                                    }
                                    volumeCache[volFile] = volHandle;
                                }
                                dbHandle = EncryptedVolume_OpenDatabase(volHandle, dbName);
                                if (dbHandle == IntPtr.Zero)
                                {
                                    Console.Error.WriteLine($"[!] Failed to open DB {dbName} in {volFile}");
                                    mode = "__skip__";
                                    resourceFile = "";
                                    break;
                                }
                                volumeDbCache[cacheKey] = dbHandle;
                            }

                            // Execute SQL via raw sqlite3 C API
                            byte[] sqlBytes = System.Text.Encoding.UTF8.GetBytes(sql + "\0");
                            int rc = sqlite3_prepare_v2(dbHandle, sqlBytes, -1, out IntPtr stmt, out IntPtr tail);
                            if (rc != SQLITE_OK)
                            {
                                IntPtr errMsg = sqlite3_errmsg(dbHandle);
                                string err = Marshal.PtrToStringUTF8(errMsg) ?? "unknown error";
                                Console.Error.WriteLine($"[!] SQL error: {err}");
                                mode = "__skip__";
                                resourceFile = "";
                                break;
                            }

                            // Print column headers
                            int colCount = sqlite3_column_count(stmt);
                            var colNames = new string[colCount];
                            for (int ci = 0; ci < colCount; ci++)
                            {
                                IntPtr namePtr = sqlite3_column_name(stmt, ci);
                                colNames[ci] = Marshal.PtrToStringUTF8(namePtr) ?? $"col{ci}";
                            }
                            Console.WriteLine(string.Join("\t", colNames));

                            // Print rows (UTF-8 for Greek/Hebrew data)
                            int rowCount = 0;
                            while (sqlite3_step(stmt) == SQLITE_ROW && rowCount < 1000)
                            {
                                var vals = new string[colCount];
                                for (int ci = 0; ci < colCount; ci++)
                                {
                                    if (sqlite3_column_type(stmt, ci) == SQLITE_NULL)
                                        vals[ci] = "";
                                    else
                                    {
                                        IntPtr textPtr = sqlite3_column_text(stmt, ci);
                                        vals[ci] = Marshal.PtrToStringUTF8(textPtr) ?? "";
                                    }
                                }
                                Console.WriteLine(string.Join("\t", vals));
                                rowCount++;
                            }
                            sqlite3_finalize(stmt);

                            mode = "__skip__";
                            resourceFile = "";
                            break;
                        }

                        case "volume-info":
                        {
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] volume-info requires: volume-info <file>");
                                mode = "__skip__";
                                resourceFile = "";
                                break;
                            }
                            string volFile = tokens[1];
                            if (!volFile.Contains("/"))
                                volFile = $"{resourcesBase}/{volFile}";

                            IntPtr volHandle;
                            if (!volumeCache.TryGetValue(volFile, out volHandle))
                            {
                                volHandle = EncryptedVolume_New();
                                bool opened = EncryptedVolume_Open(volHandle, licMgr, volFile);
                                if (!opened)
                                {
                                    Console.Error.WriteLine($"[!] Failed to open volume: {volFile}");
                                    mode = "__skip__";
                                    resourceFile = "";
                                    break;
                                }
                                volumeCache[volFile] = volHandle;
                            }

                            string resId = EncryptedVolume_GetResourceId(volHandle) ?? "unknown";
                            string driverName = EncryptedVolume_GetResourceDriverName(volHandle) ?? "unknown";
                            Console.WriteLine($"ResourceId: {resId}");
                            Console.WriteLine($"DriverName: {driverName}");

                            mode = "__skip__";
                            resourceFile = "";
                            break;
                        }
```

Then, after the switch statement and BEFORE the resource path resolution at line 1162, add:

```csharp
                    // Skip CTitle path for EncryptedVolume commands
                    if (mode == "__skip__")
                    {
                        // Output already written; outer loop prints ---END---
                        continue;  // This continue goes to the outer while loop,
                                   // which prints ---END--- at line 1185
                    }
```

**Wait — `continue` inside the switch doesn't continue the outer loop.** The `continue` needs to be AFTER the switch closes. Add this check between the switch closing brace (line 1159) and the resource path resolution (line 1162):

```csharp
                    } // end switch

                    // Skip CTitle path for EncryptedVolume commands
                    if (mode == "__skip__")
                        continue; // → prints ---END--- at line 1185

                    // Resolve resource path (existing line 1162)
                    if (!resourceFile.Contains("/"))
```

**IMPORTANT:** The `continue` here jumps to the top of the `while` loop. But `---END---` is printed at the BOTTOM of the loop (line 1185), AFTER the `catch` block. We need to verify the loop structure. Looking at the code: the `---END---` print at line 1185 is OUTSIDE the try-catch, so `continue` would skip it. To fix this, use `goto endMarker;` instead:

```csharp
                    if (mode == "__skip__")
                        goto printEnd;

                    // ... rest of CTitle path ...

                } // end try
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[!] Command error: ...");
                }

                printEnd:
                Console.WriteLine("---END---");
                Console.Out.Flush();
```

Actually, looking more carefully at lines 1179-1186, the `---END---` IS inside the try block's scope but after `ExecuteOperation`. Let me re-examine... No — lines 1185-1186 are at the same indentation as the `try` block, meaning they execute after the try-catch regardless. So `continue` WOULD skip `---END---`. The `goto` approach is correct.

- [ ] **Step 5: Verify libsqlite3-logos.dylib exists**

```bash
ls -la "/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/Resources/lib/libsqlite3-logos.dylib"
```
Expected: File exists (~824KB). If not found, fall back to system `/usr/lib/libsqlite3.dylib`.

- [ ] **Step 6: Build and verify compilation**

```bash
cd /Volumes/External/Logos4/tools && dotnet build LogosReader/ 2>&1
```
Expected: Build succeeded. May have warnings but no errors.

- [ ] **Step 7: Test query-db with a real encrypted volume**

```bash
cd /Volumes/External/Logos4/tools && echo 'volume-info FIGURATIVE-LANGUAGE.lbssd' | dotnet run --project LogosReader -- --batch 2>&1
```
Expected: Should print ResourceId and DriverName, then `---END---`.

```bash
echo 'query-db FIGURATIVE-LANGUAGE.lbssd SupplementalData.db "SELECT name FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1
```
Expected: Should print table names from the embedded database.

- [ ] **Step 8: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/LogosReader/Program.cs
git commit -m "feat: add EncryptedVolume API + query-db command to LogosReader

P/Invoke declarations for EncryptedVolume_New/Open/OpenDatabase/Delete
and sqlite3 C API (prepare_v2, step, column_text, finalize) via
libsqlite3-logos.dylib. New batch commands: query-db and volume-info.
Unlocks 150+ encrypted dataset files (.lbssd, .lbsxrf, .lbsplc, etc.)"
```

---

### Task 4: Add Python Wrappers for Encrypted Volume Queries

**Files:**
- Modify: `tools/logos_batch.py`

- [ ] **Step 1: Add query_dataset and volume_info to LogosBatchReader**

Add these methods to the `LogosBatchReader` class in `logos_batch.py`:

```python
def query_dataset(self, resource_file, db_name, sql, max_rows=500):
    """Query an encrypted volume's embedded SQLite database.

    Args:
        resource_file: e.g. "FIGURATIVE-LANGUAGE.lbssd"
        db_name: e.g. "SupplementalData.db"
        sql: SQL query string

    Returns:
        List of dicts (column_name → value), or empty list on failure.
    """
    # SQL must be double-quoted so ParseCommandLine treats it as one token.
    # Replace internal double-quotes with single-quotes (safe for SQLite).
    sql_safe = sql.replace('"', "'")
    result = self._send_command(f'query-db {resource_file} {db_name} "{sql_safe}"')
    if not result:
        return []

    lines = result.strip().split('\n')
    if len(lines) < 1:
        return []

    # First line is tab-separated column headers
    headers = lines[0].split('\t')
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        vals = line.split('\t')
        row = {}
        for i, h in enumerate(headers):
            row[h] = vals[i] if i < len(vals) else ""
        rows.append(row)
        if len(rows) >= max_rows:
            break

    return rows

def volume_info(self, resource_file):
    """Get metadata for an encrypted volume.

    Returns:
        Dict with ResourceId and DriverName, or None on failure.
    """
    result = self._send_command(f'volume-info {resource_file}')
    if not result:
        return None

    info = {}
    for line in result.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            info[key.strip()] = val.strip()
    return info
```

- [ ] **Step 2: Write test for query_dataset**

```python
# tools/workbench/tests/test_dataset_query.py
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logos_batch import LogosBatchReader

def test_volume_info():
    """Should return metadata for an encrypted volume."""
    reader = LogosBatchReader()
    try:
        info = reader.volume_info("FIGURATIVE-LANGUAGE.lbssd")
        assert info is not None, "volume_info returned None"
        assert "ResourceId" in info or "DriverName" in info
    finally:
        reader.close()

def test_query_dataset_tables():
    """Should list tables in an encrypted volume's database."""
    reader = LogosBatchReader()
    try:
        rows = reader.query_dataset(
            "FIGURATIVE-LANGUAGE.lbssd",
            "SupplementalData.db",
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        assert len(rows) > 0, "Expected at least one table"
        table_names = [r.get("name", "") for r in rows]
        assert any("Reference" in t or "Attachment" in t or "Resource" in t for t in table_names), \
            f"Expected study data tables, got {table_names}"
    finally:
        reader.close()

def test_query_dataset_content():
    """Should return actual data from a supplemental data query."""
    reader = LogosBatchReader()
    try:
        # First, discover the schema
        rows = reader.query_dataset(
            "FIGURATIVE-LANGUAGE.lbssd",
            "SupplementalData.db",
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        assert len(rows) > 0
        # Then query the first table for a few rows
        first_table = rows[0]["name"]
        data = reader.query_dataset(
            "FIGURATIVE-LANGUAGE.lbssd",
            "SupplementalData.db",
            f"SELECT * FROM [{first_table}] LIMIT 5"
        )
        assert len(data) > 0, f"Expected data from {first_table}"
    finally:
        reader.close()
```

- [ ] **Step 3: Run tests**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_dataset_query.py -v 2>&1
```
Expected: All pass. This confirms the full pipeline works: Python → batch reader → LogosReader → EncryptedVolume API → sqlite3 query → TSV results → Python dicts.

- [ ] **Step 4: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/logos_batch.py tools/workbench/tests/test_dataset_query.py
git commit -m "feat: add query_dataset() Python wrapper for encrypted volumes

Sends query-db commands to LogosReader batch mode and parses TSV results
into Python dicts. Full pipeline test confirms end-to-end data access."
```

---

### Task 5: Explore Dataset Schemas

**Important:** Before building tools, we need to understand the actual table schemas inside these encrypted databases. This task is pure research — no code changes.

- [ ] **Step 1: Discover schemas for all workflow-critical datasets**

Run these queries to map out the table structures. Record the output — it will inform every tool in Phase 3.

```bash
cd /Volumes/External/Logos4/tools

# Figurative Language
echo 'query-db FIGURATIVE-LANGUAGE.lbssd SupplementalData.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Greek Constructions
echo 'query-db GREEK-CONSTRUCTIONS.lbssd SupplementalData.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Biblical Cross-References
echo 'query-db BIBLEXREFS.lbslcr bxrefs.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Thematic Outlines
echo 'query-db ThematicOutlines.lbstod thematicoutlines.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Theology Cross-Refs
echo 'query-db THEOLOGY-XREFS.lbsxrf CrossReferences.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Biblical Places
echo 'query-db BiblicalPlaces.lbsplc biblicalplaces.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Preaching Themes
echo 'query-db PreachingThemes.lbsptd preachingthemes.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1

# Important Words
echo 'query-db IMPORTANTWORDS.lbsiw importantwords.db "SELECT sql FROM sqlite_master WHERE type='"'"'table'"'"'"' | dotnet run --project LogosReader -- --batch 2>&1
```

- [ ] **Step 2: Sample data from each to understand reference format**

The datasets use Bible reference "sort keys" for range intersection queries. We need to understand the format:

```bash
# Sample a few rows from figurative language to see reference format
echo 'query-db FIGURATIVE-LANGUAGE.lbssd SupplementalData.db "SELECT * FROM ReferenceAttachments LIMIT 5"' | dotnet run --project LogosReader -- --batch 2>&1

# Sample cross-references
echo 'query-db BIBLEXREFS.lbslcr bxrefs.db "SELECT * FROM CrossReferences LIMIT 5"' | dotnet run --project LogosReader -- --batch 2>&1
```

- [ ] **Step 3: Document the schemas**

Save the discovered schemas to `docs/research/encrypted-volume-schemas.md` for reference when building tools. Include:
- Table names and columns for each dataset
- The reference format used (sort keys, ranges, etc.)
- Sample data showing what the output looks like
- Any encoding/format notes

- [ ] **Step 4: Commit**

```bash
cd /Volumes/External/Logos4
git add docs/research/encrypted-volume-schemas.md
git commit -m "docs: document encrypted volume database schemas

Tables and reference formats for figurative language, Greek constructions,
cross-references, thematic outlines, theology xrefs, places, preaching
themes, and important words datasets."
```

---

## Phase 3: Wire Up Dataset Tools

**Approach:** Each dataset tool follows the same pattern: receive a Bible reference, convert to the dataset's reference format, query the encrypted volume, and return structured results. We build a base query function in `dataset_tools.py` and one tool per dataset type.

### Task 6: Create Dataset Tools Module

**Files:**
- Create: `tools/workbench/dataset_tools.py`
- Create: `tools/workbench/tests/test_dataset_tools.py`

**Note:** The exact SQL queries in this task depend on the schemas discovered in Task 5. The code below uses placeholder queries that MUST be updated based on actual schema discovery. The patterns are correct but column names may differ.

- [ ] **Step 1: Write failing test**

```python
# tools/workbench/tests/test_dataset_tools.py
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dataset_tools import query_figurative_language, query_dataset_tables

def test_query_dataset_tables():
    """Should list tables in a dataset."""
    tables = query_dataset_tables("FIGURATIVE-LANGUAGE.lbssd", "SupplementalData.db")
    assert len(tables) > 0

def test_figurative_language_returns_data():
    """Should return figurative language data for a known passage."""
    # Romans 1 should have entries — it's rich in figurative language
    results = query_figurative_language(book=66, chapter=1)
    # Even if empty for this chapter, function should not crash
    assert isinstance(results, list)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_dataset_tools.py -v 2>&1
```
Expected: FAIL with "No module named 'dataset_tools'"

- [ ] **Step 3: Write dataset_tools.py**

```python
# tools/workbench/dataset_tools.py
"""Encrypted volume dataset tools for the sermon study companion.

Each function queries a specific encrypted dataset file via LogosBatchReader.
The batch reader sends query-db commands to LogosReader which uses the
EncryptedVolume API to open encrypted SQLite databases.

IMPORTANT: The SQL queries in this file depend on the actual database schemas
discovered in Task 5. Update column/table names based on the schema research
document at docs/research/encrypted-volume-schemas.md.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Reuse the batch reader singleton from study.py to avoid spawning
# a second LogosReader process (which doubles memory and may conflict
# with native library initialization).
from study import init_batch_reader, _batch_reader

def _get_reader():
    """Get the shared batch reader singleton."""
    global _batch_reader
    if _batch_reader is None:
        init_batch_reader()
    from study import _batch_reader
    return _batch_reader


def query_dataset_tables(resource_file, db_name):
    """List tables in an encrypted volume's database."""
    reader = _get_reader()
    rows = reader.query_dataset(
        resource_file, db_name,
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    return [r.get("name", "") for r in rows]


# ── Bible reference helpers ──────────────────────────────────────────
# The datasets store references using Logos-internal sort keys.
# The exact format will be determined in Task 5 schema discovery.
# These helpers convert book/chapter/verse to the dataset reference format.

def _make_ref_prefix(book, chapter):
    """Create a reference prefix for querying datasets.

    NOTE: This is a placeholder. The actual reference format used by
    SupplementalData tables needs to be determined from schema discovery.
    Common formats: "bible.66.1" or sort-key integers.
    """
    return f"bible.{book}.{chapter}"


# ── Dataset query functions ──────────────────────────────────────────
# Each function follows the pattern:
# 1. Convert reference to dataset format
# 2. Query the encrypted volume
# 3. Return structured results

def query_figurative_language(book, chapter, verse_start=None, verse_end=None):
    """Query figurative language tagged for a passage.

    Returns list of dicts with figure type, description, and reference.
    Source: FIGURATIVE-LANGUAGE.lbssd → SupplementalData.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)

    # NOTE: Actual query depends on schema from Task 5.
    # This is a best-guess based on the SupplementalData driver pattern.
    rows = reader.query_dataset(
        "FIGURATIVE-LANGUAGE.lbssd",
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_greek_constructions(book, chapter, verse_start=None, verse_end=None):
    """Query Greek grammatical constructions for a passage.

    Source: GREEK-CONSTRUCTIONS.lbssd → SupplementalData.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "GREEK-CONSTRUCTIONS.lbssd",
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_hebrew_constructions(book, chapter, verse_start=None, verse_end=None):
    """Query Hebrew grammatical constructions for a passage.

    Source: HEBREW-CONSTRUCTIONS.lbssd → SupplementalData.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "HEBREW-CONSTRUCTIONS.lbssd",
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_literary_typing(book, chapter):
    """Query literary type classification for a passage.

    Source: LITERARYTYPING.lbssd → SupplementalData.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "LITERARYTYPING.lbssd",
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 20"
    )
    return rows


def query_curated_cross_refs(book, chapter, verse_start=None, verse_end=None):
    """Query curated Bible cross-references for a passage.

    Source: BIBLEXREFS.lbslcr → bxrefs.db
    This is much richer than inline ESV annotations.
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "BIBLEXREFS.lbslcr",
        "bxrefs.db",
        f"SELECT * FROM CrossReferences WHERE SourceReference LIKE '{ref_prefix}%' LIMIT 100"
    )
    return rows


def query_thematic_outlines(book, chapter):
    """Query thematic outlines for a passage.

    Source: ThematicOutlines.lbstod → thematicoutlines.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "ThematicOutlines.lbstod",
        "thematicoutlines.db",
        f"SELECT * FROM PointReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_theology_xrefs(book, chapter, xref_type="systematic"):
    """Query theology cross-references for a passage.

    xref_type: "systematic" → THEOLOGY-XREFS.lbsxrf
               "biblical" → BIBLICAL-THEOLOGY-XREFS.lbsxrf
               "confessional" → CREEDS-COUNCILS-XREFS.lbsxrf
               "grammar" → GRAMMAR-XREFS.lbsxrf
    """
    file_map = {
        "systematic": "THEOLOGY-XREFS.lbsxrf",
        "biblical": "BIBLICAL-THEOLOGY-XREFS.lbsxrf",
        "confessional": "CREEDS-COUNCILS-XREFS.lbsxrf",
        "grammar": "GRAMMAR-XREFS.lbsxrf",
    }
    resource_file = file_map.get(xref_type, "THEOLOGY-XREFS.lbsxrf")
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        resource_file,
        "CrossReferences.db",
        f"SELECT * FROM CrossReferences WHERE SourceReference LIKE '{ref_prefix}%' LIMIT 100"
    )
    return rows


def query_biblical_places(book, chapter):
    """Query biblical places mentioned in a passage.

    Source: BiblicalPlaces.lbsplc → biblicalplaces.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "BiblicalPlaces.lbsplc",
        "biblicalplaces.db",
        f"SELECT * FROM EntityReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_biblical_people(book, chapter):
    """Query biblical people mentioned in a passage.

    Source: BiblicalPeople.lbsbpd → biblicalpeople.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "BiblicalPeople.lbsbpd",
        "biblicalpeople.db",
        f"SELECT * FROM EntityReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_biblical_things(book, chapter):
    """Query biblical things/objects mentioned in a passage.

    Source: BiblicalThings.lbsthg → biblicalthings.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "BiblicalThings.lbsthg",
        "biblicalthings.db",
        f"SELECT * FROM EntityReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_preaching_themes(book, chapter):
    """Query preaching themes for a passage.

    Source: PreachingThemes.lbsptd → preachingthemes.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "PreachingThemes.lbsptd",
        "preachingthemes.db",
        f"SELECT * FROM ThemeReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_important_words(book, chapter):
    """Query important words tagged for a passage.

    Source: IMPORTANTWORDS.lbsiw → importantwords.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "IMPORTANTWORDS.lbsiw",
        "importantwords.db",
        f"SELECT * FROM WordReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_ancient_literature(book, chapter):
    """Query ancient literature cross-references for a passage.

    Source: AncientLiterature.lbsanc → ancientliterature.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "AncientLiterature.lbsanc",
        "ancientliterature.db",
        f"SELECT * FROM CrossReferences WHERE SourceReference LIKE '{ref_prefix}%' LIMIT 100"
    )
    return rows


def query_propositional_outline(book, chapter, testament="nt"):
    """Query propositional outline for a passage.

    Source: PROPOSITIONAL-OUTLINES.lbssd (NT) or PROPOSITIONAL-OUTLINES-OT.lbssd (OT)
    """
    resource_file = "PROPOSITIONAL-OUTLINES.lbssd" if testament == "nt" else "PROPOSITIONAL-OUTLINES-OT.lbssd"
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        resource_file,
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_nt_use_of_ot(book, chapter):
    """Query NT use of OT passages.

    Source: NT-USE-OF-OT.lbssd → SupplementalData.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "NT-USE-OF-OT.lbssd",
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_wordplay(book, chapter):
    """Query wordplay instances in a passage.

    Source: WORDPLAY.lbssd → SupplementalData.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "WORDPLAY.lbssd",
        "SupplementalData.db",
        f"SELECT * FROM ReferenceAttachments WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows


def query_cultural_concepts(book, chapter):
    """Query Lexham Cultural Ontology for a passage.

    Source: LCO.lbslco → lco.db
    """
    reader = _get_reader()
    ref_prefix = _make_ref_prefix(book, chapter)
    rows = reader.query_dataset(
        "LCO.lbslco",
        "lco.db",
        f"SELECT * FROM SenseReferences WHERE Reference LIKE '{ref_prefix}%' LIMIT 50"
    )
    return rows
```

- [ ] **Step 4: Run tests**

```bash
cd /Volumes/External/Logos4/tools && python3 -m pytest workbench/tests/test_dataset_tools.py -v 2>&1
```
Expected: Tests pass (at least `test_query_dataset_tables`). The content tests may need query adjustments after schema discovery in Task 5.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/workbench/dataset_tools.py tools/workbench/tests/test_dataset_tools.py
git commit -m "feat: add dataset query functions for all encrypted volumes

16 query functions covering figurative language, constructions, cross-refs,
places, people, things, theology xrefs, preaching themes, important words,
propositional outlines, ancient literature, cultural concepts, and more.
SQL queries are placeholders pending schema discovery in Task 5."
```

---

### Task 7: Wire Dataset Tools into Companion Agent

**Files:**
- Modify: `tools/workbench/companion_tools.py` (add tool definitions + dispatcher)
- Modify: `tools/workbench/companion_agent.py` (update system prompt)

- [ ] **Step 1: Add dataset tool definitions to TOOL_DEFINITIONS**

Add these after the existing `save_to_outline` tool definition in `companion_tools.py`:

```python
    # ── Encrypted Volume Dataset Tools ──────────────────────────────────
    {
        "name": "get_passage_data",
        "description": "Get structured study data for a passage from Logos's pre-indexed datasets. Returns figurative language, grammatical constructions, literary typing, wordplay, propositional outlines, important words, preaching themes, and more. Use this proactively when Bryan enters a new passage or phase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference, e.g. 'Romans 1:18-23'"
                },
                "datasets": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["figurative_language", "greek_constructions", "hebrew_constructions",
                                 "literary_typing", "wordplay", "propositional_outline",
                                 "important_words", "preaching_themes", "nt_use_of_ot",
                                 "cultural_concepts"]
                    },
                    "description": "Which datasets to query. If omitted, queries the most relevant ones for the current phase."
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "get_cross_reference_network",
        "description": "Get curated cross-references from Logos's cross-reference databases. Much richer than inline Bible annotations. Can also query theology, biblical theology, confessional, and grammar cross-references.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference"
                },
                "xref_type": {
                    "type": "string",
                    "enum": ["curated", "systematic", "biblical", "confessional", "grammar"],
                    "description": "Type of cross-references. 'curated' = Bible cross-refs, 'systematic' = systematic theology sections, etc."
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "get_passage_context",
        "description": "Get contextual data for a passage: biblical places, people, things, events, ancient literature references, and timeline data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference"
                },
                "context_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["places", "people", "things", "ancient_literature"]
                    },
                    "description": "Which context data to retrieve. If omitted, returns all available."
                }
            },
            "required": ["reference"]
        }
    },
```

- [ ] **Step 2: Add dispatcher cases in execute_tool**

```python
        elif tool_name == "get_passage_data":
            return _get_passage_data(tool_input, session_context)
        elif tool_name == "get_cross_reference_network":
            return _get_cross_reference_network(tool_input, session_context)
        elif tool_name == "get_passage_context":
            return _get_passage_context(tool_input, session_context)
```

- [ ] **Step 3: Add implementation functions**

```python
def _get_passage_data(tool_input, session_context):
    """Query pre-indexed passage datasets."""
    from dataset_tools import (
        query_figurative_language, query_greek_constructions,
        query_hebrew_constructions, query_literary_typing,
        query_wordplay, query_propositional_outline,
        query_important_words, query_preaching_themes,
        query_nt_use_of_ot, query_cultural_concepts
    )

    ref = parse_reference(tool_input["reference"])
    book, chapter = ref["book"], ref["chapter"]
    testament = "ot" if book <= 39 else "nt"

    requested = tool_input.get("datasets")
    if not requested:
        # Default: most relevant datasets
        requested = ["figurative_language", "important_words", "preaching_themes"]
        if testament == "nt":
            requested.append("greek_constructions")
        else:
            requested.append("hebrew_constructions")

    dispatch = {
        "figurative_language": lambda: query_figurative_language(book, chapter),
        "greek_constructions": lambda: query_greek_constructions(book, chapter),
        "hebrew_constructions": lambda: query_hebrew_constructions(book, chapter),
        "literary_typing": lambda: query_literary_typing(book, chapter),
        "wordplay": lambda: query_wordplay(book, chapter),
        "propositional_outline": lambda: query_propositional_outline(book, chapter, testament),
        "important_words": lambda: query_important_words(book, chapter),
        "preaching_themes": lambda: query_preaching_themes(book, chapter),
        "nt_use_of_ot": lambda: query_nt_use_of_ot(book, chapter),
        "cultural_concepts": lambda: query_cultural_concepts(book, chapter),
    }

    results = {}
    for ds in requested:
        if ds in dispatch:
            data = dispatch[ds]()
            results[ds] = data if data else []

    return {"reference": tool_input["reference"], "datasets": results}


def _get_cross_reference_network(tool_input, session_context):
    """Query cross-reference databases."""
    from dataset_tools import query_curated_cross_refs, query_theology_xrefs

    ref = parse_reference(tool_input["reference"])
    xref_type = tool_input.get("xref_type", "curated")

    if xref_type == "curated":
        rows = query_curated_cross_refs(ref["book"], ref["chapter"])
    else:
        rows = query_theology_xrefs(ref["book"], ref["chapter"], xref_type=xref_type)

    return {
        "reference": tool_input["reference"],
        "xref_type": xref_type,
        "cross_references": rows[:50]  # Cap at 50
    }


def _get_passage_context(tool_input, session_context):
    """Query contextual data for a passage."""
    from dataset_tools import (
        query_biblical_places, query_biblical_people,
        query_biblical_things, query_ancient_literature
    )

    ref = parse_reference(tool_input["reference"])
    book, chapter = ref["book"], ref["chapter"]

    requested = tool_input.get("context_types")
    if not requested:
        requested = ["places", "people", "things"]

    dispatch = {
        "places": lambda: query_biblical_places(book, chapter),
        "people": lambda: query_biblical_people(book, chapter),
        "things": lambda: query_biblical_things(book, chapter),
        "ancient_literature": lambda: query_ancient_literature(book, chapter),
    }

    results = {}
    for ct in requested:
        if ct in dispatch:
            data = dispatch[ct]()
            results[ct] = data if data else []

    return {"reference": tool_input["reference"], "context": results}
```

- [ ] **Step 4: Update companion_agent.py system prompt**

In the tools section of the system prompt (companion_agent.py), add after the existing tool descriptions:

```python
# Add to the tools_section string:
"""
- **get_passage_data**: Query Logos's pre-indexed passage datasets. Returns figurative language, grammatical constructions, literary typing, wordplay, propositional outlines, important words, preaching themes, NT use of OT, and cultural concepts. Use this proactively when Bryan starts a new passage or moves to a new phase.
- **get_cross_reference_network**: Query curated cross-reference databases — much richer than inline Bible annotations. Can also get systematic theology, biblical theology, confessional, and grammar cross-references that point to sections in Bryan's theology books.
- **get_passage_context**: Get contextual data: biblical places, people, things mentioned in the passage, plus ancient literature cross-references (church fathers, Josephus, Philo, etc.).

**Proactive data surfacing**: When Bryan enters a passage, call get_passage_data early to discover what Logos has tagged for this text. If figurative language or constructions are tagged, mention them naturally: "Logos tags a metonymy in v.21 — do you see it?" Don't dump raw data; use it to guide the conversation."""
```

- [ ] **Step 5: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/workbench/companion_tools.py tools/workbench/companion_agent.py
git commit -m "feat: wire encrypted volume dataset tools into companion

Three new tools: get_passage_data (figurative language, constructions,
outlines, themes), get_cross_reference_network (curated xrefs, theology
xrefs, confessional xrefs), get_passage_context (places, people, things,
ancient literature). System prompt updated for proactive data surfacing."
```

---

## Dependency Graph

```
Task 1 (Resource Index)
  └→ Task 2 (Rewrite Search) ← independent of Phase 2

Task 3 (EncryptedVolume P/Invoke)
  └→ Task 4 (Python Wrappers)
       └→ Task 5 (Schema Discovery)
            └→ Task 6 (Dataset Tools)
                 └→ Task 7 (Wire into Agent)
```

**Tasks 1-2 and Tasks 3-4 can run in parallel** — they modify different files and have no dependencies on each other. Task 5 depends on Task 4. Tasks 6-7 depend on Task 5.

## Post-Implementation Verification

After all tasks are complete:

1. Start the companion: `cd tools/workbench && python3 app.py`
2. Open http://localhost:5111/companion/
3. Enter "Romans 1:18-23"
4. Ask "Is ἐματαιώθησαν a middle passive?" — should pull from Wallace chapter on voice AND EDNT entry for ματαιόω
5. Ask "What figurative language does Logos tag in this passage?" — should query FIGURATIVE-LANGUAGE.lbssd and return tagged data
6. Ask "What do the systematic theologies say about this passage?" — should query THEOLOGY-XREFS.lbsxrf and identify relevant sections
7. Check that each tool result has substantial content (not abbreviation stubs or empty arrays)
