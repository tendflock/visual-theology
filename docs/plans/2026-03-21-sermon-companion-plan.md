# Sermon Study Companion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ADHD-friendly sermon study companion that walks Bryan through a 12-phase prep workflow one question at a time, with an engaged AI study partner and homiletical coaching.

**Architecture:** Flask web app with HTMX + vanilla JS frontend. Card-based UI shows one question at a time; discussion mode opens a streaming conversation with Claude. Outline builds incrementally. Backend reads from Logos 4 library via existing LogosReader/study.py layer. SQLite for all persistence.

**Tech Stack:** Python 3 (Flask, anthropic SDK), HTMX, vanilla JS/CSS, SQLite, LogosReader (C# .NET 8)

**Spec:** `docs/specs/2026-03-21-sermon-companion-design.md`
**Methodology/Question Bank Source:** `docs/research/exegetical-methodology.md`

---

## File Structure

### New Files
```
tools/workbench/
├── companion_db.py          — new database layer (sessions, cards, outline, questions)
├── companion_agent.py        — new agent loop (12 phases, coaching, streaming)
├── companion_tools.py        — focused tool implementations (commentary paragraph, word study, cross-ref)
├── genre_map.py              — book → genre static mapping
├── seed_questions.py         — questions embedded as Python data, populates question_bank table
├── static/
│   └── companion.css         — all styles for the companion UI
│   └── companion.js          — client-side state (timer, mode toggle, drawer, SSE)
├── templates/
│   ├── companion_base.html   — minimal shell (no navbar clutter)
│   ├── start.html            — "What are you preaching?" entry screen
│   ├── session.html          — main session view (card + discussion + outline drawer)
│   ├── partials/
│   │   ├── card.html         — the card component (question + resource + response area)
│   │   ├── discussion.html   — conversation thread partial
│   │   ├── outline_drawer.html — outline tree partial
│   │   └── progress_dots.html — phase progress dots
│   └── export.html           — printable outline (standalone, no app chrome)
```

### Modified Files
```
tools/study.py                — fix clean_bible_text(), add get_genre_for_book()
tools/workbench/app.py        — add new routes alongside existing ones (don't break old routes yet)
```

### Untouched Files
```
tools/LogosReader/*           — don't touch
tools/logos_batch.py           — don't touch
tools/logos_cache.py           — don't touch
tools/resource_types.py        — don't touch
tools/sermon_agent.py          — keep existing, companion_tools.py replaces its role
tools/workbench/workbench_agent.py  — keep existing, companion_agent.py replaces its role
tools/workbench/workbench_db.py     — keep existing, companion_db.py replaces its role
```

**Strategy:** Build new files alongside existing ones. The old workbench still works at `/`. The new companion lives at `/companion`. Once stable, the old routes can be removed.

---

## Task 1: Database Layer

**Files:**
- Create: `tools/workbench/companion_db.py`
- Test: `tools/workbench/tests/test_companion_db.py`

- [ ] **Step 1: Create test directory and test file**

```bash
mkdir -p tools/workbench/tests
touch tools/workbench/tests/__init__.py
```

- [ ] **Step 2: Write failing tests for session CRUD**

```python
# tools/workbench/tests/test_companion_db.py
import os, sys, pytest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB

@pytest.fixture
def db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    d = CompanionDB(tmp.name)
    d.init_db()
    yield d
    os.unlink(tmp.name)

def test_create_session(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    s = db.get_session(sid)
    assert s['passage_ref'] == 'Romans 1:18-23'
    assert s['genre'] == 'epistle'
    assert s['current_phase'] == 'prayer'
    assert s['status'] == 'active'
    assert s['timer_remaining_seconds'] == 900  # 15 min for prayer

def test_list_active_sessions(db):
    db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    db.create_session('1 Samuel 25:1-13', 9, 25, 1, 13, 'narrative')
    sessions = db.list_sessions(status='active')
    assert len(sessions) == 2

def test_update_phase(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    db.update_phase(sid, 'text_work', 7200)  # 2 hrs
    s = db.get_session(sid)
    assert s['current_phase'] == 'text_work'
    assert s['timer_remaining_seconds'] == 7200
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_db.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'companion_db'`

- [ ] **Step 4: Implement companion_db.py with session CRUD**

```python
# tools/workbench/companion_db.py
import sqlite3
import json
from datetime import datetime, timezone

PHASE_TIMERS = {
    'prayer': 900,          # 15 min
    'text_work': 7200,      # 2 hrs
    'digestion': 3600,      # 1 hr
    'observation': 3600,    # 1 hr
    'word_study': 1800,     # 30 min
    'context': 2700,        # 45 min
    'theological': 7200,    # 2 hrs
    'commentary': 1800,     # 30 min
    'exegetical_point': 1800, # 30 min
    'fcf_homiletical': 1800,  # 30 min
    'sermon_construction': 10800, # 3 hrs
    'edit_pray': 5400,      # 1.5 hrs
}

PHASES_ORDER = list(PHASE_TIMERS.keys())

class CompanionDB:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passage_ref TEXT NOT NULL,
                book INTEGER NOT NULL,
                chapter INTEGER NOT NULL,
                verse_start INTEGER,
                verse_end INTEGER,
                genre TEXT NOT NULL,
                current_phase TEXT NOT NULL DEFAULT 'prayer',
                current_question_id INTEGER,
                timer_remaining_seconds INTEGER NOT NULL DEFAULT 900,
                timer_paused INTEGER NOT NULL DEFAULT 0,
                total_elapsed_seconds INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS card_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                phase TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                saved_to_outline INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                phase TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_name TEXT,
                tool_input TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outline_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                parent_id INTEGER REFERENCES outline_nodes(id),
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                verse_ref TEXT,
                rank INTEGER NOT NULL DEFAULT 0,
                flags TEXT DEFAULT '{}',
                source_type TEXT,
                source_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase TEXT NOT NULL,
                question_text TEXT NOT NULL,
                guidance_text TEXT,
                genre_tags TEXT NOT NULL DEFAULT '[]',
                priority TEXT NOT NULL DEFAULT 'core',
                resource_type TEXT DEFAULT 'none',
                rank INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_card_responses_session ON card_responses(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_messages(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_outline_session ON outline_nodes(session_id);
            CREATE INDEX IF NOT EXISTS idx_outline_parent ON outline_nodes(parent_id);
            CREATE INDEX IF NOT EXISTS idx_questions_phase ON question_bank(phase, priority);
        """)
        conn.commit()
        conn.close()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def create_session(self, passage_ref, book, chapter, verse_start, verse_end, genre):
        conn = self._conn()
        now = self._now()
        cur = conn.execute("""
            INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                                  current_phase, timer_remaining_seconds, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'prayer', ?, ?, ?)
        """, (passage_ref, book, chapter, verse_start, verse_end, genre,
              PHASE_TIMERS['prayer'], now, now))
        conn.commit()
        sid = cur.lastrowid
        conn.close()
        return sid

    def get_session(self, session_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_sessions(self, status=None):
        conn = self._conn()
        if status:
            rows = conn.execute("SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_phase(self, session_id, phase, timer_seconds=None):
        if timer_seconds is None:
            timer_seconds = PHASE_TIMERS.get(phase, 1800)
        conn = self._conn()
        conn.execute("""
            UPDATE sessions SET current_phase = ?, timer_remaining_seconds = ?,
                               timer_paused = 0, updated_at = ?
            WHERE id = ?
        """, (phase, timer_seconds, self._now(), session_id))
        conn.commit()
        conn.close()

    # --- Card Responses ---
    def save_card_response(self, session_id, phase, question_id, content):
        conn = self._conn()
        cur = conn.execute("""
            INSERT INTO card_responses (session_id, phase, question_id, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, phase, question_id, content, self._now()))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def get_card_responses(self, session_id, phase=None):
        conn = self._conn()
        if phase:
            rows = conn.execute("SELECT * FROM card_responses WHERE session_id = ? AND phase = ? ORDER BY created_at", (session_id, phase)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM card_responses WHERE session_id = ? ORDER BY created_at", (session_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Conversation Messages ---
    def save_message(self, session_id, phase, role, content, tool_name=None, tool_input=None):
        conn = self._conn()
        cur = conn.execute("""
            INSERT INTO conversation_messages (session_id, phase, role, content, tool_name, tool_input, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, phase, role, content, tool_name, tool_input, self._now()))
        conn.commit()
        mid = cur.lastrowid
        conn.close()
        return mid

    def get_messages(self, session_id, phase=None, limit=50):
        conn = self._conn()
        if phase:
            rows = conn.execute("""
                SELECT * FROM conversation_messages
                WHERE session_id = ? AND phase = ?
                ORDER BY created_at DESC LIMIT ?
            """, (session_id, phase, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (session_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in reversed(rows)]

    # --- Outline Nodes ---
    def add_outline_node(self, session_id, node_type, content, parent_id=None,
                         verse_ref=None, rank=0, flags=None, source_type=None, source_id=None):
        conn = self._conn()
        now = self._now()
        if rank == 0 and parent_id is not None:
            row = conn.execute("SELECT MAX(rank) as max_rank FROM outline_nodes WHERE session_id = ? AND parent_id = ?",
                               (session_id, parent_id)).fetchone()
            rank = (row['max_rank'] or 0) + 1
        elif rank == 0 and parent_id is None:
            row = conn.execute("SELECT MAX(rank) as max_rank FROM outline_nodes WHERE session_id = ? AND parent_id IS NULL",
                               (session_id,)).fetchone()
            rank = (row['max_rank'] or 0) + 1
        cur = conn.execute("""
            INSERT INTO outline_nodes (session_id, parent_id, type, content, verse_ref, rank,
                                       flags, source_type, source_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, parent_id, node_type, content, verse_ref, rank,
              json.dumps(flags or {}), source_type, source_id, now, now))
        conn.commit()
        nid = cur.lastrowid
        conn.close()
        return nid

    def get_outline_tree(self, session_id):
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM outline_nodes WHERE session_id = ? ORDER BY rank
        """, (session_id,)).fetchall()
        conn.close()
        nodes = [dict(r) for r in rows]
        for n in nodes:
            n['flags'] = json.loads(n['flags']) if n['flags'] else {}
        return self._build_tree(nodes)

    def _build_tree(self, nodes):
        by_id = {n['id']: {**n, 'children': []} for n in nodes}
        roots = []
        for n in nodes:
            node = by_id[n['id']]
            if n['parent_id'] and n['parent_id'] in by_id:
                by_id[n['parent_id']]['children'].append(node)
            else:
                roots.append(node)
        return roots

    def update_outline_node(self, node_id, content=None, node_type=None, rank=None, flags=None):
        conn = self._conn()
        updates = []
        params = []
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if node_type is not None:
            updates.append("type = ?")
            params.append(node_type)
        if rank is not None:
            updates.append("rank = ?")
            params.append(rank)
        if flags is not None:
            updates.append("flags = ?")
            params.append(json.dumps(flags))
        updates.append("updated_at = ?")
        params.append(self._now())
        params.append(node_id)
        conn.execute(f"UPDATE outline_nodes SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def delete_outline_node(self, node_id):
        conn = self._conn()
        conn.execute("DELETE FROM outline_nodes WHERE parent_id = ?", (node_id,))
        conn.execute("DELETE FROM outline_nodes WHERE id = ?", (node_id,))
        conn.commit()
        conn.close()

    # --- Question Bank ---
    def get_questions(self, phase, genre=None, priority=None):
        conn = self._conn()
        query = "SELECT * FROM question_bank WHERE phase = ?"
        params = [phase]
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY rank"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        questions = [dict(r) for r in rows]
        if genre:
            questions = [q for q in questions
                         if genre in json.loads(q['genre_tags']) or not json.loads(q['genre_tags'])]
        return questions

    def get_question(self, question_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM question_bank WHERE id = ?", (question_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    # --- Timer ---
    def update_timer(self, session_id, remaining_seconds, paused=None, elapsed_delta=0):
        conn = self._conn()
        if paused is not None:
            conn.execute("""
                UPDATE sessions SET timer_remaining_seconds = ?, timer_paused = ?,
                       total_elapsed_seconds = total_elapsed_seconds + ?, updated_at = ?
                WHERE id = ?
            """, (remaining_seconds, int(paused), elapsed_delta, self._now(), session_id))
        else:
            conn.execute("""
                UPDATE sessions SET timer_remaining_seconds = ?,
                       total_elapsed_seconds = total_elapsed_seconds + ?, updated_at = ?
                WHERE id = ?
            """, (remaining_seconds, elapsed_delta, self._now(), session_id))
        conn.commit()
        conn.close()

    def complete_session(self, session_id):
        conn = self._conn()
        conn.execute("UPDATE sessions SET status = 'completed', updated_at = ? WHERE id = ?",
                     (self._now(), session_id))
        conn.commit()
        conn.close()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_db.py -v
```

- [ ] **Step 6: Write tests for card responses, outline, and questions**

```python
# Append to tools/workbench/tests/test_companion_db.py

def test_save_and_get_card_response(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    rid = db.save_card_response(sid, 'text_work', 1, 'The main verb is apokaluptetai')
    responses = db.get_card_responses(sid, 'text_work')
    assert len(responses) == 1
    assert responses[0]['content'] == 'The main verb is apokaluptetai'

def test_outline_tree(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    root = db.add_outline_node(sid, 'title', 'The Wrath of God Revealed')
    mp1 = db.add_outline_node(sid, 'main_point', 'I. God Reveals His Wrath (v.18)', parent_id=root, verse_ref='Rom 1:18')
    sp1 = db.add_outline_node(sid, 'sub_point', 'Present tense — happening now', parent_id=mp1)
    tree = db.get_outline_tree(sid)
    assert len(tree) == 1
    assert tree[0]['content'] == 'The Wrath of God Revealed'
    assert len(tree[0]['children']) == 1
    assert len(tree[0]['children'][0]['children']) == 1

def test_question_bank(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO question_bank (phase, question_text, guidance_text, genre_tags, priority, rank)
        VALUES ('text_work', 'What is the main verb?', 'Identify tense, voice, mood', '["epistle","narrative"]', 'core', 1)
    """)
    conn.execute("""
        INSERT INTO question_bank (phase, question_text, guidance_text, genre_tags, priority, rank)
        VALUES ('text_work', 'What figurative language is present?', 'Metaphor, simile, etc.', '["poetry"]', 'supplemental', 2)
    """)
    conn.commit()
    conn.close()

    qs = db.get_questions('text_work', genre='epistle')
    assert len(qs) == 1
    assert qs[0]['question_text'] == 'What is the main verb?'

    all_qs = db.get_questions('text_work')
    assert len(all_qs) == 2

def test_delete_outline_node_cascades(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    root = db.add_outline_node(sid, 'title', 'Title')
    child = db.add_outline_node(sid, 'main_point', 'Point', parent_id=root)
    db.delete_outline_node(root)
    tree = db.get_outline_tree(sid)
    assert len(tree) == 0
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_db.py -v
```

- [ ] **Step 8: Commit**

```bash
git add tools/workbench/companion_db.py tools/workbench/tests/
git commit -m "feat: add companion database layer with sessions, cards, outline, questions"
```

---

## Task 2: Genre Map + study.py Fixes

**Files:**
- Create: `tools/workbench/genre_map.py`
- Modify: `tools/study.py` (clean_bible_text function, ~line 645)
- Test: `tools/workbench/tests/test_genre_map.py`, `tools/workbench/tests/test_clean_text.py`

- [ ] **Step 1: Write genre map test**

```python
# tools/workbench/tests/test_genre_map.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genre_map import get_genre

def test_epistle():
    assert get_genre(66) == 'epistle'   # Romans
    assert get_genre(70) == 'epistle'   # Ephesians

def test_narrative():
    assert get_genre(1) == 'narrative'   # Genesis
    assert get_genre(9) == 'narrative'   # 1 Samuel
    assert get_genre(63) == 'narrative'  # Luke
    assert get_genre(64) == 'narrative'  # John (Gospel)

def test_poetry():
    assert get_genre(19) == 'poetry'     # Psalms
    assert get_genre(22) == 'poetry'     # Song of Solomon

def test_prophecy():
    assert get_genre(23) == 'prophecy'   # Isaiah

def test_apocalyptic():
    assert get_genre(27) == 'apocalyptic' # Revelation

def test_law():
    assert get_genre(3) == 'law'         # Leviticus

def test_wisdom():
    assert get_genre(20) == 'wisdom'     # Proverbs
    assert get_genre(21) == 'wisdom'     # Ecclesiastes
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd tools/workbench && python3 -m pytest tests/test_genre_map.py -v
```

- [ ] **Step 3: Implement genre_map.py**

```python
# tools/workbench/genre_map.py
"""Static mapping of Bible book numbers to genre tags for question filtering."""

# Book numbers follow Logos convention (1=Gen, 64=John, 66=Romans, etc.)
GENRE_MAP = {
    # Law / Torah
    1: 'narrative',    # Genesis (narrative with law elements)
    2: 'narrative',    # Exodus
    3: 'law',          # Leviticus
    4: 'narrative',    # Numbers
    5: 'law',          # Deuteronomy
    # Historical Narrative
    6: 'narrative',    # Joshua
    7: 'narrative',    # Judges
    8: 'narrative',    # Ruth
    9: 'narrative',    # 1 Samuel
    10: 'narrative',   # 2 Samuel
    11: 'narrative',   # 1 Kings
    12: 'narrative',   # 2 Kings
    13: 'narrative',   # 1 Chronicles
    14: 'narrative',   # 2 Chronicles
    15: 'narrative',   # Ezra
    16: 'narrative',   # Nehemiah
    17: 'narrative',   # Esther
    # Poetry / Wisdom
    18: 'poetry',      # Job
    19: 'poetry',      # Psalms
    20: 'wisdom',      # Proverbs
    21: 'wisdom',      # Ecclesiastes
    22: 'poetry',      # Song of Solomon
    # Major Prophets
    23: 'prophecy',    # Isaiah
    24: 'prophecy',    # Jeremiah
    25: 'poetry',      # Lamentations
    26: 'prophecy',    # Ezekiel
    27: 'apocalyptic', # Daniel
    # Minor Prophets
    28: 'prophecy',    # Hosea
    29: 'prophecy',    # Joel
    30: 'prophecy',    # Amos
    31: 'prophecy',    # Obadiah
    32: 'narrative',   # Jonah (prophetic narrative)
    33: 'prophecy',    # Micah
    34: 'prophecy',    # Nahum
    35: 'prophecy',    # Habakkuk
    36: 'prophecy',    # Zephaniah
    37: 'prophecy',    # Haggai
    38: 'prophecy',    # Zechariah
    39: 'prophecy',    # Malachi
    # Gospels + Acts
    61: 'narrative',   # Matthew
    62: 'narrative',   # Mark
    63: 'narrative',   # Luke
    64: 'narrative',   # John
    65: 'narrative',   # Acts
    # Pauline Epistles
    66: 'epistle',     # Romans
    67: 'epistle',     # 1 Corinthians
    68: 'epistle',     # 2 Corinthians
    69: 'epistle',     # Galatians
    70: 'epistle',     # Ephesians
    71: 'epistle',     # Philippians
    72: 'epistle',     # Colossians
    73: 'epistle',     # 1 Thessalonians
    74: 'epistle',     # 2 Thessalonians
    75: 'epistle',     # 1 Timothy
    76: 'epistle',     # 2 Timothy
    77: 'epistle',     # Titus
    78: 'epistle',     # Philemon
    # General Epistles
    79: 'epistle',     # Hebrews
    80: 'epistle',     # James
    81: 'epistle',     # 1 Peter
    82: 'epistle',     # 2 Peter
    83: 'epistle',     # 1 John
    84: 'epistle',     # 2 John
    85: 'epistle',     # 3 John
    86: 'epistle',     # Jude
    # Apocalyptic
    87: 'apocalyptic', # Revelation
}

def get_genre(book_num):
    """Return genre tag for a book number. Defaults to 'narrative' if unknown."""
    return GENRE_MAP.get(book_num, 'narrative')
```

- [ ] **Step 4: Run genre tests**

```bash
cd tools/workbench && python3 -m pytest tests/test_genre_map.py -v
```

- [ ] **Step 5: Write test for clean_bible_text fix**

```python
# tools/workbench/tests/test_clean_text.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from study import clean_bible_text

def test_strips_crossref_markers():
    text = "For \ufeffhGod so loved \ufeffithe world"
    result = clean_bible_text(text)
    assert '[h]' not in result
    assert '\ufeff' not in result
    assert 'God so loved' in result
    assert 'the world' in result

def test_strips_footnote_markers():
    text = "gave his only Son\ufeff9"
    result = clean_bible_text(text)
    assert '[fn9]' not in result
    assert '\ufeff' not in result
    assert 'gave his only Son' in result

def test_preserves_verse_numbers():
    text = "16 For God so loved the world"
    result = clean_bible_text(text)
    assert '16' in result

def test_clean_text_no_markers():
    text = "The Lord is my shepherd"
    result = clean_bible_text(text)
    assert result == "The Lord is my shepherd"
```

- [ ] **Step 6: Run test to verify current behavior fails** (it currently converts markers rather than stripping)

```bash
cd tools/workbench && python3 -m pytest tests/test_clean_text.py -v
```

- [ ] **Step 7: Fix clean_bible_text() in study.py**

Find the `clean_bible_text()` function (~line 645 of `tools/study.py`) and modify it to strip markers entirely instead of converting them to `[h]` format. The function should:
- Remove all `\ufeff` characters and the letter/number immediately adjacent
- Remove `\xa0` (non-breaking space) artifacts
- Preserve verse numbers and actual text content
- Keep the raw annotated text available via a separate function or parameter for when cross-ref data is needed

- [ ] **Step 7b: Fix parse_reference() to not call sys.exit()**

The existing `parse_reference()` in study.py calls `sys.exit(1)` on invalid input, which would kill the Flask server. Modify it to raise `ValueError` instead. Find the `sys.exit(1)` call (~line 226) and replace with `raise ValueError(f"Could not parse reference: {ref_str}")`. The Flask route in Task 8 will catch this and show a helpful error message.

- [ ] **Step 8: Run clean text tests**

```bash
cd tools/workbench && python3 -m pytest tests/test_clean_text.py -v
```

- [ ] **Step 9: Commit**

```bash
git add tools/workbench/genre_map.py tools/workbench/tests/test_genre_map.py tools/workbench/tests/test_clean_text.py tools/study.py
git commit -m "feat: add genre map and fix clean_bible_text to strip markers entirely"
```

---

## Task 3: Question Bank Seeder

**Files:**
- Create: `tools/workbench/seed_questions.py`
- Test: `tools/workbench/tests/test_question_bank.py`

The question bank is populated from the 113 questions in `docs/research/exegetical-methodology.md`. This is a one-time seed script. Each question gets: phase, question_text, guidance_text, genre_tags (JSON array), priority (core/supplemental), resource_type, rank.

- [ ] **Step 1: Write test for question bank seeding**

```python
# tools/workbench/tests/test_question_bank.py
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_db import CompanionDB
from seed_questions import seed_question_bank

def test_seed_populates_all_phases():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)

    conn = db._conn()
    phases = conn.execute("SELECT DISTINCT phase FROM question_bank").fetchall()
    conn.close()
    phase_names = {r['phase'] for r in phases}
    assert 'prayer' in phase_names
    assert 'text_work' in phase_names
    assert 'observation' in phase_names
    assert 'word_study' in phase_names
    assert 'context' in phase_names
    assert 'theological' in phase_names
    assert 'commentary' in phase_names
    assert 'exegetical_point' in phase_names
    assert 'fcf_homiletical' in phase_names
    assert 'sermon_construction' in phase_names
    assert 'edit_pray' in phase_names
    os.unlink(tmp.name)

def test_seed_has_core_questions():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)

    core = db.get_questions('text_work', priority='core')
    assert len(core) >= 3  # at minimum: translation, odd words, repetition
    os.unlink(tmp.name)

def test_seed_has_genre_tags():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)

    import json
    qs = db.get_questions('observation')
    tagged = [q for q in qs if json.loads(q['genre_tags'])]
    assert len(tagged) > 0  # at least some questions have genre tags
    os.unlink(tmp.name)

def test_seed_is_idempotent():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)
    count1 = len(db.get_questions('text_work'))
    seed_question_bank(db)  # run again
    count2 = len(db.get_questions('text_work'))
    assert count1 == count2
    os.unlink(tmp.name)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tools/workbench && python3 -m pytest tests/test_question_bank.py -v
```

- [ ] **Step 3: Implement seed_questions.py**

Create `tools/workbench/seed_questions.py` with all 113 questions **embedded as a Python list of dicts** — do NOT parse the methodology markdown file (it's a corrupted single-line format). Each question is a dict with: phase, question_text, guidance_text, genre_tags, priority, resource_type, rank.

The questions come from `docs/research/exegetical-methodology.md` but must be **manually mapped** to the spec's 12 phase names (the methodology doc uses different phase numbering — see mapping below). Mark core vs. supplemental (core = Bryan's original workflow questions that always appear; supplemental = methodology additions that appear when time allows).

**Phase mapping from methodology → plan:**
- Methodology "Preacher Prep" → plan phases `prayer` (prayer questions) + `digestion` (devotional questions)
- Methodology "Text Establishment" → plan phase `text_work`
- Methodology "Observation" → plan phase `observation`
- Methodology "Word Study" → plan phase `word_study`
- Methodology "Context" → plan phase `context`
- Methodology "Theological Analysis" (6A-6C) → plan phase `theological`
- Methodology "Theological Analysis" (6D Commentary) → plan phase `commentary`
- Methodology "Subject/Complement/EP" → plan phase `exegetical_point`
- Methodology "FCF" + "HP/THT" + "Purpose & Application" → plan phase `fcf_homiletical`
- Methodology "Sermon Construction" → plan phase `sermon_construction`
- Methodology "Self-Examination & Editing" → plan phase `edit_pray`

**Genre tags:** Use 7 genres: `epistle`, `narrative`, `poetry`, `wisdom`, `prophecy`, `law`, `apocalyptic`. (The spec lists 6; `wisdom` is added for Proverbs/Ecclesiastes which are distinct from poetry.) Empty genre_tags `[]` means the question applies to all genres.

The seed function should clear existing questions before inserting (idempotent).

- [ ] **Step 4: Run tests**

```bash
cd tools/workbench && python3 -m pytest tests/test_question_bank.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/seed_questions.py tools/workbench/tests/test_question_bank.py
git commit -m "feat: add question bank seeder with 113 questions across 12 phases"
```

---

## Task 4: Companion Tools (Commentary Paragraph Finder + Word Study + Cross-Ref)

**Files:**
- Create: `tools/workbench/companion_tools.py`
- Test: `tools/workbench/tests/test_companion_tools.py`

These are the focused tools the companion calls, replacing the generic sermon_agent.py tools. They wrap study.py functions and add AI-powered paragraph selection for commentaries.

- [ ] **Step 1: Write tests for tool definitions and basic execution**

```python
# tools/workbench/tests/test_companion_tools.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_tools import TOOL_DEFINITIONS, get_tool_names

def test_tool_definitions_exist():
    names = get_tool_names()
    assert 'read_bible_passage' in names
    assert 'find_commentary_paragraph' in names
    assert 'word_study_lookup' in names
    assert 'expand_cross_references' in names

def test_tool_definitions_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert 'name' in tool
        assert 'description' in tool
        assert 'input_schema' in tool
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_tools.py -v
```

- [ ] **Step 3: Implement companion_tools.py**

Create `tools/workbench/companion_tools.py` with:
- `TOOL_DEFINITIONS` — list of Claude tool schemas for: `read_bible_passage`, `find_commentary_paragraph`, `word_study_lookup`, `expand_cross_references`, `save_to_outline`
- `execute_tool(tool_name, tool_input, session_context)` — dispatcher
- Each tool implementation wraps study.py functions
- `find_commentary_paragraph` uses Haiku to identify relevant paragraphs from a full section, caches results
- `word_study_lookup` uses interlinear data (lemma, morphology, Strong's) — no lexicon reading for MVP
- `expand_cross_references` reads annotation articles and fetches actual verse text for each ref
- `save_to_outline` adds a node to the outline tree via companion_db

Key design: each tool returns a dict with structured data, not just a string dump. The companion agent formats it for display.

- [ ] **Step 4: Run tests**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_tools.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_tools.py tools/workbench/tests/test_companion_tools.py
git commit -m "feat: add focused companion tools for commentary, word study, cross-refs"
```

---

## Task 5: Companion Agent (System Prompt + Streaming Loop)

**Files:**
- Create: `tools/workbench/companion_agent.py`
- Test: `tools/workbench/tests/test_companion_agent.py`

This is the brain — the streaming Claude agent loop with the new system prompt structure, phase awareness, and homiletical coaching.

- [ ] **Step 1: Write test for system prompt assembly**

```python
# tools/workbench/tests/test_companion_agent.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_agent import build_system_prompt

def test_system_prompt_includes_identity():
    prompt = build_system_prompt(
        phase='text_work', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=3600, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert 'Reformed' in prompt
    assert 'study partner' in prompt.lower() or 'companion' in prompt.lower()

def test_system_prompt_includes_phase():
    prompt = build_system_prompt(
        phase='text_work', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=3600, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert 'text' in prompt.lower() or 'translation' in prompt.lower()

def test_system_prompt_includes_homiletical_guardrails():
    prompt = build_system_prompt(
        phase='sermon_construction', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=3600, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert 'so what' in prompt.lower() or 'So What' in prompt
    assert 'Christ' in prompt
    assert 'wife' in prompt.lower() or 'congregation' in prompt.lower()

def test_system_prompt_includes_timer():
    prompt = build_system_prompt(
        phase='text_work', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=1200, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert '20 minutes' in prompt or '1200' in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_agent.py -v
```

- [ ] **Step 3: Implement companion_agent.py**

Create `tools/workbench/companion_agent.py` with:

- `build_system_prompt(phase, passage, genre, timer_remaining, card_responses, outline_summary, conversation_summary)` — assembles the 7-section system prompt per spec
- `stream_companion_response(session_id, user_message, db, model='claude-sonnet-4-20250514')` — generator yielding SSE events
  - Uses `client.messages.stream()` (actual streaming, not sync-then-SSE)
  - Handles tool_use blocks — calls `companion_tools.execute_tool()`
  - Yields events: `text_delta`, `tool_start`, `tool_result`, `done`, `error`
  - Saves all messages to conversation_messages table
- Phase-specific instructions for each of the 12 phases
- Homiletical guardrails always present in system prompt (phases 9-12 get extra emphasis)

The system prompt structure (per spec):
1. Identity & voice
2. Current phase context (phase name, time remaining, what's been done)
3. Passage context (text, genre)
4. Homiletical guardrails (So What gate, Christ thread, time estimator)
5. Research summary (card responses so far, condensed)
6. Available tools
7. Behavioral constraints (no walls of text, no step counts, mention time naturally)

- [ ] **Step 4: Run tests**

```bash
cd tools/workbench && python3 -m pytest tests/test_companion_agent.py -v
```

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_agent.py tools/workbench/tests/test_companion_agent.py
git commit -m "feat: add companion agent with 12-phase system prompt and streaming loop"
```

---

## Task 6: Frontend — CSS + JS Foundation

**Files:**
- Create: `tools/workbench/static/companion.css`
- Create: `tools/workbench/static/companion.js`

- [ ] **Step 1: Create static directory**

```bash
mkdir -p tools/workbench/static
```

- [ ] **Step 2: Write companion.css**

ADHD-first design: dark theme (easier on eyes for long sessions), generous whitespace, clear hierarchy, one thing at a time. Key elements: card component, discussion thread, outline drawer, timer, progress dots. No animation distractions. Calm, focused.

Match the visual style from the brainstorming mockup: dark background (#1a1a2e), green for completed (#7fdb98), blue for current (#5b8def), yellow for timer (#f0c674), subtle borders.

- [ ] **Step 3: Write companion.js**

Client-side state management:
- `Timer` class: countdown, auto-pause on inactivity, sync to server
- `CardMode` / `DiscussionMode` toggle (CSS class swap)
- `OutlineDrawer` open/close
- `SSEConnection` class: connect, auto-reconnect, event parsing
- `InactivityMonitor`: track last interaction, trigger nudge after 10 min, pause after 30 min
- HTMX event listeners for card submission, discussion messages

- [ ] **Step 4: Verify static files are served**

```bash
cd tools/workbench && python3 -c "
from flask import Flask
app = Flask(__name__, static_folder='static')
with app.test_client() as c:
    r = c.get('/static/companion.css')
    print('CSS:', r.status_code)
    r = c.get('/static/companion.js')
    print('JS:', r.status_code)
"
```

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/static/
git commit -m "feat: add companion CSS (ADHD-first dark theme) and JS (timer, SSE, mode toggle)"
```

---

## Task 7: Frontend — Templates

**Files:**
- Create: `tools/workbench/templates/companion_base.html`
- Create: `tools/workbench/templates/start.html`
- Create: `tools/workbench/templates/session.html`
- Create: `tools/workbench/templates/partials/card.html`
- Create: `tools/workbench/templates/partials/discussion.html`
- Create: `tools/workbench/templates/partials/outline_drawer.html`
- Create: `tools/workbench/templates/partials/progress_dots.html`
- Create: `tools/workbench/templates/export.html`

- [ ] **Step 1: Create companion_base.html**

Minimal shell: dark theme, loads companion.css + companion.js + htmx.js, no navbar clutter. Just a content block. HTMX loaded via CDN.

- [ ] **Step 2: Create start.html**

"What are you preaching?" — single input field, centered. List of active sessions below (if any). Clean, no clutter. Form POSTs to `/companion/session/new`.

- [ ] **Step 3: Create session.html**

Main session view. Structure:
- Top bar: passage ref, phase badge, timer, progress dots
- Center: card partial (swapped by HTMX)
- Bottom: discuss button / discussion thread (toggled by JS)
- Right edge: outline drawer toggle button
- Outline drawer: slide-out panel

All dynamic content loaded via HTMX partials.

- [ ] **Step 4: Create card.html partial**

The card component. Shows:
- No question counter (spec forbids showing step counts). Use progress dots within the phase: filled for answered, outlined for remaining. Bryan sees progress without a number.
- Question text (h3)
- Guidance text (subtitle)
- Pre-loaded resource (if applicable — Bible text, previous translation, etc.)
- Textarea for response
- Three buttons: Back, Discuss, Next

HTMX: form submits POST to `/companion/session/<id>/card/respond`, returns next card partial via hx-swap.

- [ ] **Step 5: Create discussion.html partial**

Conversation thread. Messages styled as chat bubbles (user right, companion left). Tool results in collapsible details. Commentary displays with summary + highlighted paragraph.

New messages arrive via SSE and are appended. Input area at bottom with send button.

- [ ] **Step 6: Create outline_drawer.html partial**

Nested list showing outline tree. Each node shows type icon + content. Edit/delete buttons on hover. "Save to outline" button visible in discussion mode. Export button at bottom.

Loaded via HTMX GET to `/companion/session/<id>/outline`.

- [ ] **Step 7: Create progress_dots.html partial**

Small row of dots representing phases. Completed = filled green, current = filled blue, future = dim outline. No labels, no numbers. Loaded via HTMX.

- [ ] **Step 8: Commit**

```bash
git add tools/workbench/templates/companion_base.html tools/workbench/templates/start.html tools/workbench/templates/session.html tools/workbench/templates/partials/ tools/workbench/templates/export.html
git commit -m "feat: add companion templates — card, discussion, outline, export"
```

---

## Task 8: Flask Routes

**Files:**
- Modify: `tools/workbench/app.py`

Add new routes under `/companion/` prefix. Keep existing routes intact so the old workbench still works during development.

- [ ] **Step 1: Add companion routes to app.py**

New routes:
- `GET /companion/` — render start.html (session list + new session form)
- `POST /companion/session/new` — create session, redirect to session view
- `GET /companion/session/<id>` — render session.html with current card
- `GET /companion/session/<id>/card` — return card.html partial for current question
- `POST /companion/session/<id>/card/respond` — save response, return next card partial
- `POST /companion/session/<id>/card/skip` — skip current question, return next card
- `POST /companion/session/<id>/phase/next` — advance to next phase
- `POST /companion/session/<id>/discuss` — accepts user message, returns SSE stream. Note: browser `EventSource` only supports GET; use `fetch()` with `ReadableStream` on the client side to handle POST→SSE.
- `GET /companion/session/<id>/outline` — return outline_drawer.html partial
- `POST /companion/session/<id>/outline/add` — add outline node
- `PATCH /companion/session/<id>/outline/<node_id>` — update node
- `DELETE /companion/session/<id>/outline/<node_id>` — delete node
- `GET /companion/session/<id>/export` — render export.html
- `PATCH /companion/session/<id>/timer` — update timer state
- `GET /companion/session/<id>/progress` — return progress_dots.html partial

Key implementation details:
- Session creation: parse reference via `study.py:parse_reference()`, detect genre via `genre_map.py`, create session in DB, seed first phase
- Card flow: get current question from question_bank, load relevant resource (Bible text, previous responses), render card partial
- Discussion: SSE stream via `companion_agent.stream_companion_response()`
- Initialize CompanionDB at app startup, seed question bank if empty

- [ ] **Step 2: Test routes manually**

```bash
cd tools/workbench && python3 app.py &
sleep 2
curl -s http://localhost:5111/companion/ | head -20
curl -X POST http://localhost:5111/companion/session/new -d "passage=Romans+1:18-23" -L | head -20
kill %1
```

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/app.py
git commit -m "feat: add companion Flask routes for card flow, discussion, outline, export"
```

---

## Task 9: Wire Up Streaming Discussion

**Files:**
- Modify: `tools/workbench/app.py` (discussion SSE endpoint)
- Modify: `tools/workbench/companion_agent.py` (ensure streaming works end-to-end)
- Modify: `tools/workbench/static/companion.js` (SSE client)

- [ ] **Step 1: Implement the SSE discussion endpoint**

The `/companion/session/<id>/discuss` POST route:
1. Receives user message from request body
2. Saves user message to conversation_messages
3. Builds context (session, phase, timer, card responses, outline summary)
4. Calls `companion_agent.stream_companion_response()` as SSE generator
5. Returns `Response(stream, mimetype='text/event-stream')`

- [ ] **Step 2: Ensure companion_agent uses actual streaming**

```python
# In companion_agent.py, stream_companion_response must use the streaming API.
# Tool use with streaming requires accumulating input_json_delta events,
# then executing the tool, then making a follow-up call with the tool result.

def stream_companion_response(session_id, user_message, db, model='claude-opus-4-20250514'):
    # ... build system prompt, messages, etc. ...

    while True:  # loop handles multi-turn tool use
        tool_use_blocks = []
        current_tool = None

        with client.messages.stream(
            model=model, max_tokens=4096,
            system=system_prompt, messages=messages, tools=tool_definitions,
        ) as stream:
            for event in stream:
                if event.type == 'content_block_start':
                    if hasattr(event.content_block, 'type') and event.content_block.type == 'tool_use':
                        current_tool = {'id': event.content_block.id, 'name': event.content_block.name, 'input_json': ''}
                        yield sse_event('tool_start', {'name': event.content_block.name})
                elif event.type == 'content_block_delta':
                    if hasattr(event.delta, 'text'):
                        yield sse_event('text_delta', {'text': event.delta.text})
                    elif hasattr(event.delta, 'partial_json'):
                        if current_tool:
                            current_tool['input_json'] += event.delta.partial_json
                elif event.type == 'content_block_stop':
                    if current_tool:
                        tool_input = json.loads(current_tool['input_json'])
                        result = execute_tool(current_tool['name'], tool_input, session_context)
                        tool_use_blocks.append((current_tool, result))
                        yield sse_event('tool_result', {'name': current_tool['name'], 'result': result})
                        current_tool = None

            response = stream.get_final_message()

        if response.stop_reason == 'tool_use':
            # Append assistant message + tool results, then loop for follow-up
            messages.append({'role': 'assistant', 'content': response.content})
            tool_results = []
            for tool, result in tool_use_blocks:
                tool_results.append({
                    'type': 'tool_result', 'tool_use_id': tool['id'],
                    'content': json.dumps(result) if isinstance(result, dict) else str(result)
                })
            messages.append({'role': 'user', 'content': tool_results})
        else:
            break  # stop_reason == 'end_turn', done

    yield sse_event('done', {})
```

**Note:** Use `claude-haiku-4-5-20251001` for commentary paragraph selection calls in `companion_tools.py`. Use `claude-opus-4-20250514` for interactive conversation — the study partner needs seminary-level theological depth.

- [ ] **Step 3: Wire up JS SSE client**

In companion.js, the `sendDiscussionMessage()` function:
1. POSTs to the discuss endpoint
2. Opens EventSource on the response
3. Appends text deltas to the discussion thread in real-time
4. Handles tool_start/tool_result events (show collapsible tool usage)
5. On 'done' event, re-enable input

- [ ] **Step 4: Test end-to-end**

```bash
cd tools/workbench && ANTHROPIC_API_KEY=<key> python3 app.py
# Open http://localhost:5111/companion/
# Create session for "Romans 1:18-23"
# Click Discuss, type "What does Hodge say about the wrath of God in v18?"
# Verify streaming response appears
```

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/app.py tools/workbench/companion_agent.py tools/workbench/static/companion.js
git commit -m "feat: wire up streaming discussion with SSE + companion agent"
```

---

## Task 10: Timer + Inactivity Logic

**Files:**
- Modify: `tools/workbench/static/companion.js` (Timer class)
- Modify: `tools/workbench/app.py` (timer PATCH endpoint)

- [ ] **Step 1: Implement Timer class in JS**

```javascript
class Timer {
    constructor(sessionId, initialSeconds) {
        this.sessionId = sessionId;
        this.remaining = initialSeconds;
        this.paused = false;
        this.interval = null;
        this.lastInteraction = Date.now();
        this.inactivityWarned = false;
    }
    start() { /* setInterval, decrement, update display, check inactivity */ }
    pause() { /* clear interval, POST to /timer */ }
    resume() { /* restart interval, POST to /timer */ }
    sync() { /* POST remaining to server every 30 seconds */ }
    checkInactivity() {
        const idle = (Date.now() - this.lastInteraction) / 1000;
        if (idle > 300 && !this.paused) { /* 5 min: auto-pause timer per spec */ }
        if (idle > 600 && !this.inactivityWarned) { /* 10 min: trigger companion nudge */ }
    }
    onInteraction() { this.lastInteraction = Date.now(); this.inactivityWarned = false; }
}
```

- [ ] **Step 2: Wire timer display to top bar**

The timer element in session.html updates every second via the Timer class. Format: MM:SS for under 1 hour, H:MM:SS for over. Yellow color when under 5 minutes.

- [ ] **Step 3: Implement server-side timer endpoint**

PATCH `/companion/session/<id>/timer` accepts `{remaining: seconds, paused: bool}`, updates DB.

- [ ] **Step 4: Implement inactivity nudge**

When 10 minutes pass without interaction, the JS sends a special "nudge" request to the discussion endpoint. The companion responds with a re-engagement message based on current context.

- [ ] **Step 5: Test timer persistence**

Start a session, advance time, close browser, reopen — timer should show remaining time, not restart.

- [ ] **Step 6: Commit**

```bash
git add tools/workbench/static/companion.js tools/workbench/app.py
git commit -m "feat: add timer with auto-pause, inactivity detection, and server sync"
```

---

## Task 11: Outline Export

**Files:**
- Modify: `tools/workbench/app.py` (export route)
- Create: `tools/workbench/templates/export.html`

- [ ] **Step 1: Implement export route**

GET `/companion/session/<id>/export` renders the outline tree as a styled HTML page with no app chrome. The template walks the tree depth-first, rendering each node type with appropriate formatting:
- `title` → `<h1>`
- `theme` → `<h2 class="theme">`
- `main_point` → `<h2>` with Roman numeral
- `sub_point` → `<h3>` with verse ref
- `bullet` → `<li>` in a `<ul>`
- `cross_ref` → styled margin note
- `note` → italic text

- [ ] **Step 2: Style export.html for printing**

CSS `@media print` rules: hide browser chrome, clean fonts (serif for body, sans-serif for headings), proper margins, page breaks before main points. Match Bryan's Ecclesiastes 11 typed outline style.

- [ ] **Step 3: Test export**

Create a session, add outline nodes manually via DB, open export page, print to PDF, verify format matches Bryan's actual outline style.

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/app.py tools/workbench/templates/export.html
git commit -m "feat: add outline export as printable HTML matching Bryan's pulpit format"
```

---

## Task 12: Integration Testing + Polish

**Files:**
- All files from previous tasks

- [ ] **Step 1: End-to-end smoke test**

```bash
cd tools/workbench && ANTHROPIC_API_KEY=<key> python3 app.py
```

1. Open http://localhost:5111/companion/
2. Enter "Romans 1:18-23" → session created, prayer card appears
3. Answer prayer card → next question appears
4. Click "Discuss" → conversation mode opens
5. Ask "What does Hodge say about v18?" → streaming response with commentary paragraph
6. Save insight to outline → outline drawer updates
7. Advance through phases → timer counts down
8. Open outline drawer → tree shows accumulated content
9. Click Export → printable outline renders
10. Close browser, reopen → session resumes where left off

- [ ] **Step 2: Fix any issues found in smoke test**

- [ ] **Step 3: Test error cases**

1. Start session without ANTHROPIC_API_KEY → card flow works, discussion shows "can't connect" message
2. Enter invalid reference → helpful error message
3. Lose network during discussion → SSE reconnects
4. Let timer expire → companion nudges but doesn't block

- [ ] **Step 4: Test the homiletical coaching**

In phase 11 (sermon construction), with an outline that has 4+ main points:
1. Verify companion asks "So what?" when adding an exegetical sub-point
2. Verify companion checks for Christ in each main point
3. Verify time estimator flags outlines over 30 minutes

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: sermon study companion — complete implementation with card flow, discussion, outline, and homiletical coaching"
```

---

## Dependency Graph

```
Task 1 (DB) ──┬── Task 3 (Questions) ──┐
              │                         │
Task 2 (Genre + Clean Text)             │
              │                         ├── Task 8 (Routes) ── Task 9 (Streaming) ── Task 12 (Integration)
Task 4 (Tools) ──── Task 5 (Agent) ─────┤
                                        │
Task 6 (CSS/JS) ── Task 7 (Templates) ──┤
                                        │
                              Task 10 (Timer) ── Task 11 (Export)
```

Tasks 1, 2, 4, 6 can run in parallel. Task 3 depends on Task 1. Tasks 5, 7 depend on their predecessors. Task 8 integrates everything. Tasks 9-11 build on 8. Task 12 is final integration.
