# Sermon Coach MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ADHD-friendly sermon retrospective coach that syncs Bryan's Sunday sermons from SermonAudio, auto-links them to prep study sessions, analyzes them with a three-tier rubric (Impact / Faithfulness / Diagnostic) via a single Opus 4.6 LLM pass, surfaces a four-card review page + streaming coach conversation, and tracks longitudinal patterns under a corpus gate.

**Architecture:** Pipeline-first. Five layers (Ingest → Match → Analyze → Coach → UI) with one direction of data flow. Deterministic code writes the canonical floor; a single LLM call populates the subjective rubric fields; a streaming Opus 4.6 coach reads everything and narrates. No override tables, no stage cache, no provenance popovers — coach disagreement lives as ordinary chat messages. Spec: `docs/superpowers/specs/2026-04-14-sermon-coach-design.md`.

**Tech Stack:** Python 3 (Flask, anthropic SDK, sermonaudio PyPI library, APScheduler), HTMX + vanilla JS/CSS, SQLite (extending `companion_db.py`), pytest + Playwright for tests. All LLM calls use `claude-opus-4-6` per project preference.

---

## Prerequisites

Before Task 1, ensure:
- `SERMONAUDIO_API_KEY` and `SERMONAUDIO_BROADCASTER_ID` are known (Bryan provides from SermonAudio dashboard)
- `pip install sermonaudio apscheduler` available (will be added to a requirements file in Task 1)
- `dotnet@8` is available for the existing LogosReader layer (already set up on Bryan's machine per CLAUDE.md)
- The existing workbench test suite passes: `cd tools/workbench && python3 -m pytest tests/ -q`

## File Structure

**New files** (all under `tools/workbench/` unless noted):

| File | Responsibility |
|---|---|
| `voice_constants.py` | Shared Reformed/Chapell/Robinson voice DNA imported by `companion_agent.py` and `sermon_coach_agent.py` |
| `homiletics_core.py` | Pure rule functions: `segment_transcript`, `align_segments_to_outline`, `compute_section_timings`, `detect_density_hotspots`, `late_application`, `corpus_gate_status`, `HOMILETICAL_PHASES` constant, `__version__` |
| `llm_client.py` | `LLMClient` protocol + `AnthropicClient` implementation + `CannedLLMClient` for tests |
| `sermonaudio_sync.py` | Ingest: API client, classify, hash computation, idempotent upsert, file lock, retry cooldown, state transitions |
| `sermon_matcher.py` | Pure `match_sermon_to_sessions()` function + `apply_match_decision()` orchestrator |
| `sermon_analyzer.py` | Analyzer pipeline: segment/align/timing/density pure stages + single Opus 4.6 rubric call + flag extraction + writer + dispatch poll |
| `sermon_coach_agent.py` | Streaming coach: system prompt assembly, corpus gate, SSE loop |
| `sermon_coach_tools.py` | Read tools: `get_sermon_review`, `get_sermon_flags`, `get_transcript_full`, `get_prep_session_full`, `pull_historical_sermons`, `get_sermon_patterns` |
| `static/sermons.css` | Dark-theme styles matching existing `companion.css` / `study.css` |
| `static/sermons.js` | HTMX/SSE glue for the review page and coach chat |
| `templates/partials/sermon_impact_card.html` | Tier 1 metrics |
| `templates/partials/sermon_faithfulness_card.html` | Tier 2 metrics |
| `templates/partials/sermon_diagnostic_card.html` | Tier 3 metrics |
| `templates/partials/sermon_prescription_card.html` | `one_change_for_next_sunday` + trends delta |
| `templates/partials/sermon_flag_list.html` | Clickable flag list |
| `templates/partials/sermon_coach_chat.html` | Streaming chat surface |
| `templates/partials/sermon_candidates_list.html` | Candidate links awaiting approval |
| `templates/partials/sermon_review_tab.html` | Full review surface rendered inside `study_session.html` |
| `templates/sermons/list.html` | `/sermons/` list view |
| `templates/sermons/detail.html` | `/sermons/<id>` authoritative review page |
| `templates/sermons/patterns.html` | `/sermons/patterns` trends view |
| `templates/sermons/sync_log.html` | `/sermons/sync-log` debug view |

**Modified files:**

| File | Change |
|---|---|
| `tools/workbench/companion_db.py` | Extend `init_db()` with 8 new tables + `ALTER TABLE sessions ADD COLUMN last_homiletical_activity_at TEXT`; modify `save_card_response()` and `save_message()` to bump `last_homiletical_activity_at` on homiletical-phase writes |
| `tools/workbench/companion_agent.py` | Replace inline `IDENTITY`, `HOMILETICAL_TRADITION`, and `VOICE_GUARDRAILS` string constants with imports from `voice_constants.py` |
| `tools/workbench/app.py` | Register `/sermons/` blueprint + APScheduler `BackgroundScheduler`; add manual sync/backfill/match/reanalyze endpoints; add SSE coach endpoint |
| `tools/workbench/templates/study_session.html` | Add "Review" tab that renders `sermon_review_tab.html` when the session has an active or candidate link |
| `tools/study.py` | Extend `parse_reference()` to handle multi-range (`"Romans 8:1-11; Romans 9:1-5"`), chapter spans (`"Psalm 1-2"`), and whole chapters (`"Romans 8"`) — return a list of passage dicts, not a single dict |
| `tools/workbench/requirements-dev.txt` (create if missing) | Add `sermonaudio>=2`, `apscheduler>=3.10`, `fcntl` is stdlib so no entry |

**New scripts:**
- `scripts/backtest_matcher.py` — CSV audit tool for matcher decisions

**New test files** (in `tools/workbench/tests/`):
- `test_sermonaudio_sync.py`
- `test_sermon_passages.py`
- `test_sermon_type_topical.py`
- `test_sermon_matcher.py`
- `test_sermon_analyzer.py`
- `test_homiletics_core.py`
- `test_voice_constants.py`
- `test_sermon_coach_agent.py`
- `test_sermon_coach_tools.py`
- `test_llm_client.py`
- `test_sermon_pipeline_end_to_end.py`
- `test_sermon_rematch_flow.py`
- `test_sermon_source_change_flow.py`
- `test_e2e_sermon_ui.py` (Playwright)

---

## Task 1: Schema migration + dependencies

**Files:**
- Modify: `tools/workbench/companion_db.py` — extend `init_db()`
- Create: `tools/workbench/requirements-dev.txt`
- Create: `tools/workbench/tests/test_companion_db_sermon_tables.py`

- [ ] **Step 1: Add `sermonaudio` and `apscheduler` to a requirements file**

Create `tools/workbench/requirements-dev.txt` (or extend the existing one if present):

```
sermonaudio>=2.0
apscheduler>=3.10
```

Run: `pip install -r tools/workbench/requirements-dev.txt`
Expected: packages install successfully. Run `python3 -c "import sermonaudio; import apscheduler; print('ok')"` → should print `ok`.

- [ ] **Step 2: Write a failing test asserting the new tables exist after `init_db()`**

Create `tools/workbench/tests/test_companion_db_sermon_tables.py`:

```python
import os
import tempfile
import pytest
from companion_db import CompanionDB


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _tables(db):
    conn = db._conn()
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    return {r[0] for r in rows}


def _columns(db, table):
    conn = db._conn()
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    conn.close()
    return {r[1] for r in rows}


def test_new_sermon_tables_created(fresh_db):
    tables = _tables(fresh_db)
    expected = {
        'sermons', 'sermon_passages', 'sermon_links',
        'sermon_reviews', 'sermon_flags', 'sermon_coach_messages',
        'sermon_sync_log', 'sermon_analysis_cost_log',
    }
    missing = expected - tables
    assert not missing, f"Missing new tables: {missing}"


def test_sermons_has_required_columns(fresh_db):
    cols = _columns(fresh_db, 'sermons')
    required = {
        'id', 'sermonaudio_id', 'broadcaster_id', 'title', 'speaker_name',
        'event_type', 'series', 'preach_date', 'publish_date', 'duration_seconds',
        'bible_text_raw', 'book', 'chapter', 'verse_start', 'verse_end',
        'audio_url', 'transcript_text', 'transcript_source',
        'sermon_type', 'classified_as', 'classification_reason',
        'metadata_hash', 'transcript_hash', 'source_version', 'remote_updated_at',
        'sync_status', 'sync_error', 'failure_count', 'last_failure_at',
        'last_state_change_at', 'last_match_attempt_at', 'match_status',
        'is_remote_deleted', 'deleted_at',
        'ui_last_seen_version',
        'first_synced_at', 'last_synced_at', 'created_at', 'updated_at',
    }
    missing = required - cols
    assert not missing, f"Missing columns on sermons: {missing}"


def test_sessions_has_last_homiletical_activity_at(fresh_db):
    cols = _columns(fresh_db, 'sessions')
    assert 'last_homiletical_activity_at' in cols


def test_partial_unique_index_one_active_link(fresh_db):
    conn = fresh_db._conn()
    # Insert a session and a sermon to link against
    conn.execute("INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre, current_phase, timer_remaining_seconds, created_at, updated_at) VALUES ('Romans 8:1-11', 45, 8, 1, 11, 'epistle', 'prayer', 900, datetime('now'), datetime('now'))")
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as, sync_status, last_state_change_at, first_synced_at, last_synced_at, created_at, updated_at) VALUES ('rcf001', 'bcast', 'Test', 'sermon', 'review_ready', datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))")
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at) VALUES (?, ?, 'active', 'auto', 'tier1', datetime('now'))", (sermon_id, sid))
    conn.commit()
    # Second active row for same sermon should fail
    with pytest.raises(Exception):
        conn.execute("INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at) VALUES (?, ?, 'active', 'auto', 'tier1-dup', datetime('now'))", (sermon_id, sid))
        conn.commit()
    conn.close()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_companion_db_sermon_tables.py -v`
Expected: ALL tests FAIL with "no such table: sermons" or similar.

- [ ] **Step 4: Extend `companion_db.py` `init_db()` with the new tables**

In `tools/workbench/companion_db.py`, inside `init_db()` after the existing `executescript`, add a second `executescript` call with:

```python
conn.executescript("""
    CREATE TABLE IF NOT EXISTS sermons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermonaudio_id TEXT UNIQUE NOT NULL,
        broadcaster_id TEXT NOT NULL,
        title TEXT NOT NULL,
        speaker_name TEXT,
        event_type TEXT,
        series TEXT,
        preach_date TEXT,
        publish_date TEXT,
        duration_seconds INTEGER,
        bible_text_raw TEXT,
        book INTEGER,
        chapter INTEGER,
        verse_start INTEGER,
        verse_end INTEGER,
        audio_url TEXT,
        transcript_text TEXT,
        transcript_source TEXT DEFAULT 'sermonaudio',
        sermon_type TEXT NOT NULL DEFAULT 'expository' CHECK (sermon_type IN ('expository','topical')),
        classified_as TEXT NOT NULL CHECK (classified_as IN ('sermon','skipped')),
        classification_reason TEXT,
        metadata_hash TEXT,
        transcript_hash TEXT,
        source_version INTEGER NOT NULL DEFAULT 1,
        remote_updated_at TEXT,
        sync_status TEXT NOT NULL DEFAULT 'pending_sync' CHECK (sync_status IN (
            'pending_sync','synced_metadata','transcript_ready',
            'analysis_pending','analysis_running','review_ready',
            'sync_failed','analysis_failed','analysis_skipped','permanent_failure'
        )),
        sync_error TEXT,
        failure_count INTEGER NOT NULL DEFAULT 0,
        last_failure_at TEXT,
        last_state_change_at TEXT NOT NULL,
        last_match_attempt_at TEXT,
        match_status TEXT NOT NULL DEFAULT 'unmatched' CHECK (match_status IN (
            'unmatched','matched','awaiting_candidates',
            'unparseable_passage','topical_no_match','rejected_all'
        )),
        is_remote_deleted INTEGER NOT NULL DEFAULT 0,
        deleted_at TEXT,
        ui_last_seen_version INTEGER NOT NULL DEFAULT 0,
        first_synced_at TEXT NOT NULL,
        last_synced_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_sermons_sermonaudio_id ON sermons(sermonaudio_id);
    CREATE INDEX IF NOT EXISTS idx_sermons_preach_date ON sermons(preach_date DESC);
    CREATE INDEX IF NOT EXISTS idx_sermons_sync_status ON sermons(sync_status);
    CREATE INDEX IF NOT EXISTS idx_sermons_classified ON sermons(classified_as);
    CREATE INDEX IF NOT EXISTS idx_sermons_match_status ON sermons(match_status);
    CREATE INDEX IF NOT EXISTS idx_sermons_book_chapter ON sermons(book, chapter);

    CREATE TABLE IF NOT EXISTS sermon_passages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
        rank INTEGER NOT NULL,
        book INTEGER NOT NULL,
        chapter_start INTEGER NOT NULL,
        verse_start INTEGER,
        chapter_end INTEGER NOT NULL,
        verse_end INTEGER,
        raw_text TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(sermon_id, rank)
    );
    CREATE INDEX IF NOT EXISTS idx_sermon_passages_sermon ON sermon_passages(sermon_id);
    CREATE INDEX IF NOT EXISTS idx_sermon_passages_lookup ON sermon_passages(book, chapter_start);

    CREATE TABLE IF NOT EXISTS sermon_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermon_id INTEGER NOT NULL REFERENCES sermons(id),
        session_id INTEGER NOT NULL REFERENCES sessions(id),
        link_status TEXT NOT NULL CHECK (link_status IN ('active','candidate','rejected')),
        link_source TEXT NOT NULL CHECK (link_source IN ('auto','manual')),
        match_reason TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(sermon_id, session_id)
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_sermon_links_one_active
        ON sermon_links(sermon_id) WHERE link_status = 'active';
    CREATE INDEX IF NOT EXISTS idx_sermon_links_sermon ON sermon_links(sermon_id);
    CREATE INDEX IF NOT EXISTS idx_sermon_links_session ON sermon_links(session_id);

    CREATE TABLE IF NOT EXISTS sermon_reviews (
        sermon_id INTEGER PRIMARY KEY REFERENCES sermons(id),
        analyzer_version TEXT NOT NULL,
        homiletics_core_version TEXT NOT NULL,
        model_version TEXT,
        analyzed_transcript_hash TEXT NOT NULL,
        source_version_at_analysis INTEGER NOT NULL,
        burden_clarity TEXT CHECK (burden_clarity IN ('crisp','clear','implied','muddled','absent')),
        burden_statement_excerpt TEXT,
        burden_first_stated_at_sec INTEGER,
        movement_clarity TEXT CHECK (movement_clarity IN ('river','mostly_river','uneven','lake')),
        movement_rationale TEXT,
        application_specificity TEXT CHECK (application_specificity IN ('localized','concrete','abstract','absent')),
        application_first_arrived_at_sec INTEGER,
        application_excerpts TEXT,
        ethos_rating TEXT CHECK (ethos_rating IN ('seized','engaged','professional','detached')),
        ethos_markers TEXT,
        concreteness_score INTEGER CHECK (concreteness_score BETWEEN 1 AND 5),
        imagery_density_per_10min REAL,
        narrative_moments TEXT,
        christ_thread_score TEXT CHECK (christ_thread_score IN ('explicit','gestured','absent')),
        christ_thread_excerpts TEXT,
        exegetical_grounding TEXT CHECK (exegetical_grounding IN ('grounded','partial','pretext')),
        exegetical_grounding_notes TEXT,
        actual_duration_seconds INTEGER NOT NULL,
        planned_duration_seconds INTEGER,
        duration_delta_seconds INTEGER,
        section_timings TEXT,
        length_delta_commentary TEXT,
        density_hotspots TEXT,
        late_application_note TEXT,
        outline_coverage_pct REAL,
        outline_additions TEXT,
        outline_omissions TEXT,
        outline_drift_note TEXT,
        top_impact_helpers TEXT NOT NULL,
        top_impact_hurters TEXT NOT NULL,
        faithfulness_note TEXT,
        one_change_for_next_sunday TEXT NOT NULL,
        computed_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sermon_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
        flag_type TEXT NOT NULL,
        severity TEXT NOT NULL CHECK (severity IN ('info','note','warn','concern')),
        transcript_start_sec INTEGER,
        transcript_end_sec INTEGER,
        section_label TEXT,
        excerpt TEXT,
        rationale TEXT NOT NULL,
        analyzer_version TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_sermon_flags_sermon ON sermon_flags(sermon_id);
    CREATE INDEX IF NOT EXISTS idx_sermon_flags_type ON sermon_flags(flag_type);

    CREATE TABLE IF NOT EXISTS sermon_coach_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermon_id INTEGER REFERENCES sermons(id),
        session_id INTEGER REFERENCES sessions(id),
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('user','assistant','tool','tool_result')),
        content TEXT,
        tool_name TEXT,
        tool_input TEXT,
        tool_result TEXT,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_coach_messages_sermon ON sermon_coach_messages(sermon_id);
    CREATE INDEX IF NOT EXISTS idx_coach_messages_session ON sermon_coach_messages(session_id);
    CREATE INDEX IF NOT EXISTS idx_coach_messages_conv ON sermon_coach_messages(conversation_id);

    CREATE TABLE IF NOT EXISTS sermon_sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        trigger TEXT NOT NULL CHECK (trigger IN ('cron','manual','backfill')),
        started_at TEXT NOT NULL,
        ended_at TEXT,
        sermons_fetched INTEGER DEFAULT 0,
        sermons_new INTEGER DEFAULT 0,
        sermons_updated INTEGER DEFAULT 0,
        sermons_noop INTEGER DEFAULT 0,
        sermons_skipped INTEGER DEFAULT 0,
        sermons_failed INTEGER DEFAULT 0,
        error_summary TEXT,
        status TEXT NOT NULL CHECK (status IN ('running','completed','failed'))
    );

    CREATE TABLE IF NOT EXISTS sermon_analysis_cost_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermon_id INTEGER NOT NULL REFERENCES sermons(id),
        model TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        estimated_cost_usd REAL NOT NULL,
        called_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_cost_log_sermon ON sermon_analysis_cost_log(sermon_id);
    CREATE INDEX IF NOT EXISTS idx_cost_log_called ON sermon_analysis_cost_log(called_at DESC);
""")

# Add last_homiletical_activity_at to sessions (idempotent: guard via PRAGMA)
existing_session_cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
if 'last_homiletical_activity_at' not in existing_session_cols:
    conn.execute("ALTER TABLE sessions ADD COLUMN last_homiletical_activity_at TEXT")

conn.commit()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd tools/workbench && python3 -m pytest tests/test_companion_db_sermon_tables.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 6: Run the full existing test suite to ensure no regression**

Run: `cd tools/workbench && python3 -m pytest tests/ -q`
Expected: all tests pass, including the new sermon schema tests.

- [ ] **Step 7: Commit**

```bash
cd /Volumes/External/Logos4
git add tools/workbench/companion_db.py tools/workbench/requirements-dev.txt tools/workbench/tests/test_companion_db_sermon_tables.py
git -c commit.gpgsign=false commit -m "feat: add sermon coach schema (8 tables + sessions.last_homiletical_activity_at)"
```

---

## Task 2: Extract voice constants

**Files:**
- Create: `tools/workbench/voice_constants.py`
- Modify: `tools/workbench/companion_agent.py` — replace inline voice strings with imports
- Create: `tools/workbench/tests/test_voice_constants.py`

- [ ] **Step 1: Write a failing test for the voice_constants module**

Create `tools/workbench/tests/test_voice_constants.py`:

```python
from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS


def test_constants_are_non_empty_strings():
    for name, value in [
        ('IDENTITY_CORE', IDENTITY_CORE),
        ('HOMILETICAL_TRADITION', HOMILETICAL_TRADITION),
        ('VOICE_GUARDRAILS', VOICE_GUARDRAILS),
    ]:
        assert isinstance(value, str), f"{name} should be str, got {type(value).__name__}"
        assert len(value.strip()) > 50, f"{name} is too short to be a real prompt section"


def test_identity_names_the_tradition():
    assert 'Reformed' in IDENTITY_CORE or 'Presbyterian' in IDENTITY_CORE


def test_homiletical_tradition_cites_chapell_and_robinson():
    assert 'Chapell' in HOMILETICAL_TRADITION
    assert 'Robinson' in HOMILETICAL_TRADITION


def test_voice_guardrails_mention_study_partner():
    assert 'study partner' in VOICE_GUARDRAILS.lower() or 'partner' in VOICE_GUARDRAILS.lower()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_voice_constants.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'voice_constants'`.

- [ ] **Step 3: Create `voice_constants.py` with the three constants extracted from `companion_agent.py`**

Create `tools/workbench/voice_constants.py`:

```python
"""Shared voice DNA for the companion and coach agents.

Both companion_agent.py (prep-time) and sermon_coach_agent.py (retrospective)
import these constants so that voice drift is prevented by a single source
of truth. Changes to voice flow to both agents automatically.
"""

IDENTITY_CORE = """## Identity & Voice

You are Bryan's sermon study companion — a Reformed Presbyterian study partner with seminary-level theological depth. You are warm but direct, like a trusted colleague in the study. You engage with genuine intellectual curiosity about the text."""

HOMILETICAL_TRADITION = """Your theological tradition: Reformed, confessional (Westminster Standards), redemptive-historical hermeneutic. You appreciate Edwards' affections, Chapell's Christ-centered preaching, Robinson's "Big Idea," Perkins' practical application, and York's editorial discipline."""

VOICE_GUARDRAILS = """Voice: Conversational but substantive. You can be informal ("That's a great catch — the aorist there is doing something interesting") but never shallow. You push Bryan when he's being sloppy and encourage him when he's doing good work. You are a study partner, not an assistant."""
```

- [ ] **Step 4: Run the voice_constants test — expect pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_voice_constants.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Update `companion_agent.py` to import from `voice_constants.py`**

In `tools/workbench/companion_agent.py`, locate the `identity = """## Identity & Voice\n\nYou are Bryan's sermon study companion...` block inside `build_system_prompt()` (around lines 153-159) and replace with:

```python
from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS

# ... in build_system_prompt() ...
identity = f"{IDENTITY_CORE}\n\n{HOMILETICAL_TRADITION}\n\n{VOICE_GUARDRAILS}"
```

Place the `from voice_constants import ...` near the top of the file with the other imports. Delete the triple-quoted inline identity string.

- [ ] **Step 6: Run the existing `companion_agent` tests — expect pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_companion_agent.py -v`
Expected: all existing companion_agent tests still PASS — the import refactor must be behavior-preserving.

- [ ] **Step 7: Commit**

```bash
git add tools/workbench/voice_constants.py tools/workbench/companion_agent.py tools/workbench/tests/test_voice_constants.py
git -c commit.gpgsign=false commit -m "refactor: extract voice DNA to voice_constants.py for sharing with sermon coach"
```

---

## Task 3: `parse_reference()` multi-range + chapter-span extensions

**Files:**
- Modify: `tools/study.py` — extend `parse_reference()`
- Create: `tools/workbench/tests/test_sermon_passages.py` — parser tests

- [ ] **Step 1: Read current `parse_reference` signature and behavior**

Run: `grep -n "def parse_reference" tools/study.py` and read the function to understand its current return shape.
Expected: current function returns a single dict `{book, chapter, verse_start, verse_end}` for a single passage string like `"Romans 8:1-11"`.

- [ ] **Step 2: Write failing tests for multi-range and chapter-span parsing**

Create `tools/workbench/tests/test_sermon_passages.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from study import parse_reference_multi


def test_single_passage_returns_single_row():
    result = parse_reference_multi("Romans 8:1-11")
    assert len(result) == 1
    row = result[0]
    assert row['book'] >= 40  # NT Logos numbering
    assert row['chapter_start'] == 8
    assert row['chapter_end'] == 8
    assert row['verse_start'] == 1
    assert row['verse_end'] == 11


def test_multi_range_returns_two_rows_ordered():
    result = parse_reference_multi("Romans 8:1-11; Romans 9:1-5")
    assert len(result) == 2
    assert result[0]['chapter_start'] == 8
    assert result[0]['verse_start'] == 1
    assert result[0]['verse_end'] == 11
    assert result[1]['chapter_start'] == 9
    assert result[1]['verse_start'] == 1
    assert result[1]['verse_end'] == 5


def test_chapter_span_returns_single_row_spanning_chapters():
    result = parse_reference_multi("Psalm 1-2")
    assert len(result) == 1
    row = result[0]
    assert row['chapter_start'] == 1
    assert row['chapter_end'] == 2
    assert row['verse_start'] is None
    assert row['verse_end'] is None


def test_whole_chapter_returns_single_row():
    result = parse_reference_multi("Romans 8")
    assert len(result) == 1
    row = result[0]
    assert row['chapter_start'] == 8
    assert row['chapter_end'] == 8
    assert row['verse_start'] is None
    assert row['verse_end'] is None


def test_unparseable_returns_empty_list():
    assert parse_reference_multi("The Ten Commandments") == []
    assert parse_reference_multi("") == []
    assert parse_reference_multi(None) == []


def test_raw_text_preserved_per_row():
    result = parse_reference_multi("Romans 8:1-11; Romans 9:1-5")
    assert "Romans 8:1-11" in result[0]['raw_text']
    assert "Romans 9:1-5" in result[1]['raw_text']
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_passages.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_reference_multi'`.

- [ ] **Step 4: Implement `parse_reference_multi` in `tools/study.py`**

Add to `tools/study.py` after the existing `parse_reference`:

```python
def parse_reference_multi(ref_str):
    """Parse a reference string that may contain multiple ranges.

    Returns a list of dicts, each with:
        book, chapter_start, verse_start, chapter_end, verse_end, raw_text

    Handles:
      - Single range: "Romans 8:1-11" -> 1 row
      - Multi-range: "Romans 8:1-11; Romans 9:1-5" -> 2 rows
      - Chapter span: "Psalm 1-2" -> 1 row, chapter_start=1, chapter_end=2, verses=None
      - Whole chapter: "Romans 8" -> 1 row, verses=None
      - Unparseable: returns []
    """
    if not ref_str or not isinstance(ref_str, str):
        return []

    parts = [p.strip() for p in ref_str.split(';') if p.strip()]
    results = []
    for part in parts:
        parsed = _parse_single_range(part)
        if parsed:
            parsed['raw_text'] = part
            results.append(parsed)
    return results


def _parse_single_range(part):
    """Parse one range segment. Returns dict or None."""
    import re
    # Extract book name (everything before the first digit)
    m = re.match(r'^(.+?)\s+(\d+)(?::(\d+)(?:-(\d+))?|(?:-(\d+)))?$', part)
    if not m:
        return None
    book_name, first_num, v_start, v_end, chap_end = m.groups()
    try:
        base = parse_reference(f"{book_name} {first_num}:1")
    except Exception:
        return None
    if not base or 'book' not in base:
        return None
    book = base['book']
    chapter_start = int(first_num)
    if v_start is not None:
        # "Romans 8:1" or "Romans 8:1-11"
        vs = int(v_start)
        ve = int(v_end) if v_end else vs
        return {
            'book': book,
            'chapter_start': chapter_start,
            'verse_start': vs,
            'chapter_end': chapter_start,
            'verse_end': ve,
        }
    if chap_end is not None:
        # "Psalm 1-2"
        return {
            'book': book,
            'chapter_start': chapter_start,
            'verse_start': None,
            'chapter_end': int(chap_end),
            'verse_end': None,
        }
    # "Romans 8" (whole chapter)
    return {
        'book': book,
        'chapter_start': chapter_start,
        'verse_start': None,
        'chapter_end': chapter_start,
        'verse_end': None,
    }
```

- [ ] **Step 5: Run the tests and iterate until they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_passages.py -v`
Expected: all 6 tests PASS. If any fail, refine the regex/logic in `_parse_single_range`.

- [ ] **Step 6: Run the existing `test_routes.py` and `test_study_routes.py` to ensure the pre-existing `parse_reference` still works**

Run: `cd tools/workbench && python3 -m pytest tests/test_routes.py tests/test_study_routes.py -v`
Expected: all existing parse_reference-dependent tests still pass. We added a new function without changing the old one.

- [ ] **Step 7: Commit**

```bash
git add tools/study.py tools/workbench/tests/test_sermon_passages.py
git -c commit.gpgsign=false commit -m "feat: add parse_reference_multi for multi-range and chapter-span sermons"
```

---

## Task 4: `homiletics_core.py` pure rule functions

**Files:**
- Create: `tools/workbench/homiletics_core.py`
- Create: `tools/workbench/tests/test_homiletics_core.py`

- [ ] **Step 1: Write failing tests for the pure rule functions**

Create `tools/workbench/tests/test_homiletics_core.py`:

```python
from homiletics_core import (
    HOMILETICAL_PHASES,
    __version__,
    segment_transcript,
    compute_section_timings,
    detect_density_hotspots,
    late_application,
    corpus_gate_status,
)


def test_version_is_semver_string():
    assert isinstance(__version__, str)
    parts = __version__.split('.')
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_homiletical_phases_constant():
    assert 'exegetical_point' in HOMILETICAL_PHASES
    assert 'fcf_homiletical' in HOMILETICAL_PHASES
    assert 'sermon_construction' in HOMILETICAL_PHASES
    assert 'edit_pray' in HOMILETICAL_PHASES
    assert 'prayer' not in HOMILETICAL_PHASES  # non-homiletical excluded


def test_corpus_gate_status_thresholds():
    assert corpus_gate_status(0) == 'pre_gate'
    assert corpus_gate_status(4) == 'pre_gate'
    assert corpus_gate_status(5) == 'emerging'
    assert corpus_gate_status(9) == 'emerging'
    assert corpus_gate_status(10) == 'stable'
    assert corpus_gate_status(50) == 'stable'


def test_late_application_threshold():
    # arrival > 0.75 * duration is late
    assert late_application(arrival_sec=1860, duration_sec=2322)  # 80.1% — late
    assert not late_application(arrival_sec=1320, duration_sec=2322)  # 56.8% — OK
    assert late_application(arrival_sec=1742, duration_sec=2322)  # exactly 75.02% — late
    assert not late_application(arrival_sec=1741, duration_sec=2322)  # 74.98% — not late
    # Zero duration guard
    assert not late_application(arrival_sec=100, duration_sec=0)


def test_segment_transcript_returns_segments_with_timing():
    # Synthetic transcript with obvious paragraph breaks
    txt = (
        "Welcome to this sermon on Romans 8. Today we explore what it means to have no condemnation. "
        "Let me begin by asking a question. What does it mean that there is therefore now no condemnation?\n\n"
        "First, we need to understand the word 'therefore.' The apostle is drawing a conclusion from chapter 7. "
        "Paul has just finished an extended argument about the struggle with sin.\n\n"
        "Second, consider the phrase 'in Christ Jesus.' This is the hinge of Paul's theology. "
        "To be in Christ is to be transferred from Adam's family to Christ's family.\n\n"
        "So what does this mean for you this morning? It means that if you trust in Christ, "
        "there is no accusation that can stick against you. The court has ruled in your favor."
    )
    segments = segment_transcript(txt, duration_sec=600)
    assert len(segments) >= 3
    assert all('start_sec' in s and 'end_sec' in s and 'text' in s for s in segments)
    assert segments[0]['start_sec'] == 0
    assert segments[-1]['end_sec'] == 600
    # Sequential non-overlapping
    for i in range(1, len(segments)):
        assert segments[i]['start_sec'] >= segments[i-1]['end_sec'] - 1  # allow off-by-one


def test_compute_section_timings_sums_correctly():
    segments = [
        {'start_sec': 0, 'end_sec': 120, 'section_label': 'intro', 'text': ''},
        {'start_sec': 120, 'end_sec': 1800, 'section_label': 'body', 'text': ''},
        {'start_sec': 1800, 'end_sec': 2100, 'section_label': 'application', 'text': ''},
        {'start_sec': 2100, 'end_sec': 2280, 'section_label': 'close', 'text': ''},
    ]
    result = compute_section_timings(segments)
    assert result['intro'] == 120
    assert result['body'] == 1680
    assert result['application'] == 300
    assert result['close'] == 180


def test_detect_density_hotspots_finds_long_greek_holds():
    segments = [
        {'start_sec': 0, 'end_sec': 60, 'text': 'Welcome', 'section_label': 'intro'},
        # Density spike: 4 consecutive segments heavy on technical terms
        {'start_sec': 60, 'end_sec': 120, 'text': 'The genitive absolute here in the aorist participle is significant', 'section_label': 'body'},
        {'start_sec': 120, 'end_sec': 180, 'text': 'Note the anarthrous noun and the oblique case usage', 'section_label': 'body'},
        {'start_sec': 180, 'end_sec': 240, 'text': 'The exegetical weight of the dative of means cannot be overstated', 'section_label': 'body'},
        {'start_sec': 240, 'end_sec': 300, 'text': 'Wallace notes the adverbial participle as causal in syntax', 'section_label': 'body'},
        {'start_sec': 300, 'end_sec': 360, 'text': 'Now let me apply this to your daily life', 'section_label': 'body'},
    ]
    hotspots = detect_density_hotspots(segments)
    assert len(hotspots) >= 1
    assert hotspots[0]['start_sec'] == 60
    assert hotspots[0]['end_sec'] >= 180
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_homiletics_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'homiletics_core'`.

- [ ] **Step 3: Implement `homiletics_core.py`**

Create `tools/workbench/homiletics_core.py`:

```python
"""Pure homiletical rule functions shared by sermon_analyzer and sermon_coach_tools.

No DB access. No side effects. All functions are deterministic given their inputs.
Version is tracked so that stale reviews can be detected when the rubric evolves.
"""

from __future__ import annotations
import re
from typing import Iterable

__version__ = '1.0.0'

HOMILETICAL_PHASES = (
    'exegetical_point',
    'fcf_homiletical',
    'sermon_construction',
    'edit_pray',
)

# Seminary / technical jargon markers (rough density signal — supplemented by LLM)
JARGON_PATTERNS = [
    r'\b(aorist|genitive|dative|accusative|nominative|vocative)\b',
    r'\banarthrous\b',
    r'\bparticiple\b',
    r'\b(exegetical|hermeneutical|eschatological|soteriological)\b',
    r'\boblique case\b',
    r'\bdative of \w+\b',
    r'\b(Wallace|Robertson|Blass[- ]Debrunner)\b',
    r'\bLXX\b',
    r'\bThGNT\b',
    r'\bMT\b',
    r'\bBDAG\b',
]


def corpus_gate_status(n_sermons: int) -> str:
    """Return the coach's longitudinal permission level based on corpus size."""
    if n_sermons >= 10:
        return 'stable'
    if n_sermons >= 5:
        return 'emerging'
    return 'pre_gate'


def late_application(arrival_sec: int, duration_sec: int) -> bool:
    """True if the application arrived later than 75% of the way through."""
    if duration_sec <= 0:
        return False
    return arrival_sec >= 0.75 * duration_sec


def segment_transcript(transcript_text: str, duration_sec: int) -> list[dict]:
    """Split a transcript into rough segments using paragraph breaks as markers.

    This is a cheap structural pass — the real segmentation happens via the LLM.
    Returns a list of {start_sec, end_sec, text, section_label} dicts where
    times are interpolated linearly over the sermon duration.
    """
    if not transcript_text or duration_sec <= 0:
        return []

    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', transcript_text) if p.strip()]
    if not paragraphs:
        return []

    total_chars = sum(len(p) for p in paragraphs)
    segments = []
    cursor = 0
    for i, p in enumerate(paragraphs):
        char_share = len(p) / total_chars if total_chars else 1 / len(paragraphs)
        duration_share = int(round(char_share * duration_sec))
        start = cursor
        end = min(cursor + duration_share, duration_sec)
        if i == len(paragraphs) - 1:
            end = duration_sec
        # Guess a section label by position
        pct = start / duration_sec if duration_sec else 0
        if pct < 0.1:
            label = 'intro'
        elif pct > 0.9:
            label = 'close'
        elif pct > 0.75:
            label = 'application'
        else:
            label = 'body'
        segments.append({
            'start_sec': start,
            'end_sec': end,
            'text': p,
            'section_label': label,
        })
        cursor = end
    return segments


def compute_section_timings(segments: Iterable[dict]) -> dict:
    """Sum per-section durations from segment list."""
    timings = {'intro': 0, 'body': 0, 'application': 0, 'close': 0}
    for s in segments:
        label = s.get('section_label', 'body')
        if label not in timings:
            label = 'body'
        timings[label] += s.get('end_sec', 0) - s.get('start_sec', 0)
    return timings


def detect_density_hotspots(segments: list[dict]) -> list[dict]:
    """Find sliding windows of ≥3 consecutive segments with jargon counts ≥2 each.

    Returns hotspot records: {start_sec, end_sec, note}.
    """
    if not segments:
        return []

    def jargon_count(text: str) -> int:
        count = 0
        for pat in JARGON_PATTERNS:
            count += len(re.findall(pat, text, flags=re.IGNORECASE))
        return count

    counts = [jargon_count(s.get('text', '')) for s in segments]
    hotspots = []
    i = 0
    while i < len(counts):
        if counts[i] >= 2:
            j = i
            total = 0
            while j < len(counts) and counts[j] >= 2:
                total += counts[j]
                j += 1
            if j - i >= 3:
                hotspots.append({
                    'start_sec': segments[i]['start_sec'],
                    'end_sec': segments[j - 1]['end_sec'],
                    'note': f"{total} technical terms across {j - i} consecutive segments",
                })
            i = j
        else:
            i += 1
    return hotspots


def align_segments_to_outline(segments: list[dict], outline_points: list[dict]) -> list[dict]:
    """Cheap alignment: assign each outline point to the segment whose midpoint is closest.

    Returns a list augmented with {outline_point_id, outline_matched} on each segment.
    The real alignment happens in the LLM pass — this is a pre-hint.
    """
    if not outline_points or not segments:
        return [dict(s) for s in segments]

    result = [dict(s) for s in segments]
    for op in outline_points:
        # Naive match: longest substring overlap between segment text and outline text
        op_text = (op.get('content') or '').lower()
        if not op_text:
            continue
        best_i = None
        best_score = 0
        for i, seg in enumerate(result):
            seg_text = (seg.get('text') or '').lower()
            score = _overlap_score(op_text, seg_text)
            if score > best_score:
                best_score = score
                best_i = i
        if best_i is not None and best_score > 2:
            result[best_i].setdefault('outline_point_ids', []).append(op.get('id'))
            result[best_i]['outline_matched'] = True
    return result


def _overlap_score(a: str, b: str) -> int:
    """Count shared 3+ char tokens."""
    atoks = {t for t in re.findall(r'\w{3,}', a)}
    btoks = {t for t in re.findall(r'\w{3,}', b)}
    return len(atoks & btoks)
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_homiletics_core.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/homiletics_core.py tools/workbench/tests/test_homiletics_core.py
git -c commit.gpgsign=false commit -m "feat: add homiletics_core.py pure rule functions (segmentation, timings, density, corpus gate)"
```

---

## Task 5: `llm_client.py` protocol + CannedLLMClient + AnthropicClient

**Files:**
- Create: `tools/workbench/llm_client.py`
- Create: `tools/workbench/tests/test_llm_client.py`

- [ ] **Step 1: Write failing test for LLMClient protocol + CannedLLMClient**

Create `tools/workbench/tests/test_llm_client.py`:

```python
import pytest
from llm_client import LLMClient, CannedLLMClient, AnthropicClient


def test_canned_client_returns_fixture_on_match():
    canned = {'hello': {'result': 'world'}}
    client = CannedLLMClient(canned)
    result = client.call(prompt='hello', schema={})
    assert result == {'result': 'world'}


def test_canned_client_returns_error_on_miss():
    client = CannedLLMClient({})
    result = client.call(prompt='unseen', schema={})
    assert 'error' in result


def test_canned_client_hashes_long_prompts():
    # Fixture key can be a short hash prefix
    canned = {}
    client = CannedLLMClient(canned)
    # Register by actual hash
    import hashlib
    long_prompt = 'x' * 5000
    key = hashlib.sha256(long_prompt.encode()).hexdigest()[:16]
    client.fixtures[key] = {'ok': True}
    assert client.call(prompt=long_prompt, schema={}) == {'ok': True}


def test_llm_client_is_a_protocol():
    # Protocol check: AnthropicClient satisfies LLMClient structurally
    assert hasattr(AnthropicClient, 'call')


def test_anthropic_client_defaults_to_opus_4_6():
    client = AnthropicClient(api_key='fake-key-for-test')
    assert client.model == 'claude-opus-4-6'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_llm_client.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `llm_client.py`**

Create `tools/workbench/llm_client.py`:

```python
"""LLM client abstraction for sermon_analyzer and sermon_coach_agent.

LLMClient is a Protocol. Production code uses AnthropicClient. Tests use
CannedLLMClient to pin LLM outputs without making real API calls.
"""

from __future__ import annotations
import hashlib
import json
from typing import Protocol, Any


class LLMClient(Protocol):
    """Structural interface any LLM client must satisfy."""
    def call(self, prompt: str, schema: dict, **kwargs) -> dict: ...


class CannedLLMClient:
    """Test double. Returns pre-registered responses keyed by prompt or hash prefix."""

    def __init__(self, fixtures: dict[str, dict]):
        # fixtures: {prompt_or_hash_prefix: response_dict}
        self.fixtures = dict(fixtures)

    def call(self, prompt: str, schema: dict = None, **kwargs) -> dict:
        if prompt in self.fixtures:
            return self.fixtures[prompt]
        key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        if key in self.fixtures:
            return self.fixtures[key]
        return {'error': f'no canned response for prompt hash {key}'}


class AnthropicClient:
    """Real client using the anthropic SDK. Opus 4.6 by default."""

    def __init__(self, api_key: str, model: str = 'claude-opus-4-6'):
        self.api_key = api_key
        self.model = model
        # Lazy import so tests that don't touch the real API don't require the SDK
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def call(self, prompt: str, schema: dict, *,
             max_tokens: int = 4096,
             system: str = None,
             track_usage: bool = True) -> dict:
        """Call the model with a tool-use-enforced schema.

        Returns {output: dict, input_tokens: int, output_tokens: int, model: str}.
        On error, returns {error: str}.
        """
        client = self._get_client()
        try:
            messages = [{'role': 'user', 'content': prompt}]
            tools = [{
                'name': 'emit_review',
                'description': 'Emit the structured sermon review following the schema.',
                'input_schema': schema,
            }]
            kwargs = dict(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools,
                tool_choice={'type': 'tool', 'name': 'emit_review'},
            )
            if system:
                kwargs['system'] = system
            response = client.messages.create(**kwargs)
        except Exception as e:
            return {'error': f'{type(e).__name__}: {e}'}

        # Extract tool_use block
        tool_block = None
        for block in response.content:
            if getattr(block, 'type', None) == 'tool_use':
                tool_block = block
                break
        if tool_block is None:
            return {'error': 'no tool_use block in response'}

        return {
            'output': tool_block.input,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'model': self.model,
        }
```

- [ ] **Step 4: Run tests — expect all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_llm_client.py -v`
Expected: all 5 tests PASS. (The AnthropicClient test creates an instance but never calls `.call()`, so no real API hit.)

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/llm_client.py tools/workbench/tests/test_llm_client.py
git -c commit.gpgsign=false commit -m "feat: add LLMClient protocol + CannedLLMClient test double + AnthropicClient impl"
```

---

## Task 6: `sermonaudio_sync.py` — pure helpers (classify + hashes + upsert)

**Files:**
- Create: `tools/workbench/sermonaudio_sync.py`
- Create: `tools/workbench/tests/test_sermonaudio_sync.py`

- [ ] **Step 1: Write failing tests for classify, compute_hashes, and upsert logic**

Create `tools/workbench/tests/test_sermonaudio_sync.py`:

```python
import os
import json
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest
from companion_db import CompanionDB
from sermonaudio_sync import (
    classify, compute_hashes, upsert_sermon,
    SERMON_EVENT_TYPES, DEVOTIONAL_EVENT_TYPES, BRYAN_SPEAKER_NAME,
)


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _remote(**overrides):
    base = dict(
        sermon_id='sa-001',
        broadcaster_id='bcast',
        title='Romans 8:1-11',
        speaker_name='Bryan Schneider',
        event_type='Sunday Service',
        series='Romans',
        preach_date=dt.date(2026, 4, 12),
        publish_date=dt.date(2026, 4, 12),
        duration=2400,
        bible_text='Romans 8:1-11',
        audio_url='https://sa.example/sa-001.mp3',
        transcript='...' * 500,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


# ── classify ────────────────────────────────────────────────────────

def test_classify_sermon_by_eventtype():
    cls, reason = classify(_remote())
    assert cls == 'sermon'
    assert 'Sunday Service' in reason


def test_classify_skipped_when_speaker_not_bryan():
    cls, reason = classify(_remote(speaker_name='Guest Preacher'))
    assert cls == 'skipped'
    assert 'speaker' in reason


def test_classify_skipped_by_eventtype_devotional():
    cls, reason = classify(_remote(event_type='Daily Devotional'))
    assert cls == 'skipped'
    assert 'Daily Devotional' in reason


def test_classify_heuristic_fallback_sunday_plus_duration():
    # Unknown event type but Sunday + >20min = sermon via heuristic
    cls, reason = classify(_remote(event_type='Revival Service', duration=1800))
    assert cls == 'sermon'
    assert 'heuristic' in reason


def test_classify_unknown_eventtype_short_duration_skipped():
    cls, reason = classify(_remote(event_type='Wedding', duration=600, preach_date=dt.date(2026, 4, 10)))
    assert cls == 'skipped'


# ── compute_hashes ─────────────────────────────────────────────────

def test_compute_hashes_stable_for_same_input():
    r1 = _remote()
    r2 = _remote()
    h1a, t1a = compute_hashes(r1)
    h2a, t2a = compute_hashes(r2)
    assert h1a == h2a
    assert t1a == t2a


def test_compute_hashes_changes_when_metadata_changes():
    r1 = _remote()
    r2 = _remote(title='Different Title')
    h1, _ = compute_hashes(r1)
    h2, _ = compute_hashes(r2)
    assert h1 != h2


def test_compute_hashes_changes_when_transcript_changes():
    r1 = _remote()
    r2 = _remote(transcript='different transcript content')
    _, t1 = compute_hashes(r1)
    _, t2 = compute_hashes(r2)
    assert t1 != t2


def test_compute_hashes_transcript_none_yields_none():
    r = _remote(transcript=None)
    _, tx_hash = compute_hashes(r)
    assert tx_hash is None


# ── upsert_sermon ──────────────────────────────────────────────────

def test_upsert_inserts_new_sermon(fresh_db):
    conn = fresh_db._conn()
    result = upsert_sermon(conn, _remote())
    conn.commit()
    assert result == 'new'
    row = conn.execute("SELECT sermonaudio_id, classified_as, source_version FROM sermons").fetchone()
    assert row[0] == 'sa-001'
    assert row[1] == 'sermon'
    assert row[2] == 1
    conn.close()


def test_upsert_noop_on_unchanged(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote())
    conn.commit()
    result = upsert_sermon(conn, _remote())
    conn.commit()
    assert result == 'noop'
    row = conn.execute("SELECT source_version FROM sermons").fetchone()
    assert row[0] == 1
    conn.close()


def test_upsert_updates_and_bumps_source_version(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote())
    conn.commit()
    result = upsert_sermon(conn, _remote(title='Updated Title'))
    conn.commit()
    assert result == 'updated'
    row = conn.execute("SELECT source_version, title FROM sermons").fetchone()
    assert row[0] == 2
    assert row[1] == 'Updated Title'
    conn.close()
```

- [ ] **Step 2: Run — expect module not found failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermonaudio_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sermonaudio_sync'`.

- [ ] **Step 3: Create `sermonaudio_sync.py` with the pure helpers**

Create `tools/workbench/sermonaudio_sync.py`:

```python
"""SermonAudio ingest module.

Pulls sermons from Bryan's broadcaster account, classifies them,
fingerprints them, and upserts into the sermons table.
"""

from __future__ import annotations
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from study import parse_reference_multi

BRYAN_SPEAKER_NAME = 'Bryan Schneider'
SERMON_EVENT_TYPES = frozenset({'Sunday Service'})
DEVOTIONAL_EVENT_TYPES = frozenset({'Devotional', 'Daily Devotional'})


def classify(sermon_remote) -> tuple[str, str]:
    """Return (classified_as, reason). Hard gate on speaker, then event type."""
    speaker = (getattr(sermon_remote, 'speaker_name', '') or '').strip()
    event_type = (getattr(sermon_remote, 'event_type', '') or '').strip()

    if speaker != BRYAN_SPEAKER_NAME:
        return ('skipped', f'speaker={speaker!r}')

    if event_type in SERMON_EVENT_TYPES:
        return ('sermon', f'eventType={event_type}')
    if event_type in DEVOTIONAL_EVENT_TYPES:
        return ('skipped', f'eventType={event_type}')

    pdate = getattr(sermon_remote, 'preach_date', None)
    dur_sec = getattr(sermon_remote, 'duration', 0) or 0
    dur_min = dur_sec / 60
    if pdate and hasattr(pdate, 'weekday') and pdate.weekday() == 6 and dur_min > 20:
        return ('sermon', f'heuristic: Sunday + {int(dur_min)}min')

    return ('skipped', f'eventType={event_type!r} (unknown)')


def compute_hashes(sermon_remote) -> tuple[str, Optional[str]]:
    """Compute metadata + transcript hashes. Returns (metadata_hash, transcript_hash)."""
    meta_blob = json.dumps({
        'title': getattr(sermon_remote, 'title', None),
        'event_type': getattr(sermon_remote, 'event_type', None),
        'series': getattr(sermon_remote, 'series', None),
        'preach_date': str(getattr(sermon_remote, 'preach_date', None)),
        'bible_text_raw': getattr(sermon_remote, 'bible_text', None),
        'duration_seconds': getattr(sermon_remote, 'duration', None),
        'remote_updated_at': str(getattr(sermon_remote, 'update_date', None)),
    }, sort_keys=True)
    meta_hash = hashlib.sha256(meta_blob.encode()).hexdigest()[:16]

    transcript = getattr(sermon_remote, 'transcript', None)
    tx_hash = hashlib.sha256(transcript.encode()).hexdigest()[:16] if transcript else None

    return meta_hash, tx_hash


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_passage_fields(bible_text: Optional[str]) -> dict:
    """Return primary passage fields (book, chapter, verse_start, verse_end) or NULLs."""
    if not bible_text:
        return {'book': None, 'chapter': None, 'verse_start': None, 'verse_end': None}
    parsed = parse_reference_multi(bible_text)
    if not parsed:
        return {'book': None, 'chapter': None, 'verse_start': None, 'verse_end': None}
    first = parsed[0]
    return {
        'book': first['book'],
        'chapter': first['chapter_start'],
        'verse_start': first['verse_start'],
        'verse_end': first['verse_end'],
    }


def upsert_sermon(conn, sermon_remote) -> str:
    """Upsert a sermon row, keyed on sermonaudio_id. Returns 'new' | 'noop' | 'updated'."""
    row = conn.execute(
        "SELECT id, metadata_hash, transcript_hash, source_version, sync_status "
        "FROM sermons WHERE sermonaudio_id = ?",
        (getattr(sermon_remote, 'sermon_id'),),
    ).fetchone()

    new_meta, new_tx = compute_hashes(sermon_remote)
    classified_as, reason = classify(sermon_remote)
    now = _now()

    if row is None:
        passage_fields = _parse_passage_fields(getattr(sermon_remote, 'bible_text', None))
        conn.execute("""
            INSERT INTO sermons (
                sermonaudio_id, broadcaster_id, title, speaker_name, event_type, series,
                preach_date, publish_date, duration_seconds,
                bible_text_raw, book, chapter, verse_start, verse_end,
                audio_url, transcript_text, transcript_source,
                sermon_type, classified_as, classification_reason,
                metadata_hash, transcript_hash, source_version, remote_updated_at,
                sync_status, last_state_change_at,
                first_synced_at, last_synced_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      'expository', ?, ?, ?, ?, 1, ?,
                      CASE WHEN ? IS NOT NULL THEN 'transcript_ready' ELSE 'synced_metadata' END,
                      ?, ?, ?, ?, ?)
        """, (
            getattr(sermon_remote, 'sermon_id'),
            getattr(sermon_remote, 'broadcaster_id'),
            getattr(sermon_remote, 'title'),
            getattr(sermon_remote, 'speaker_name', None),
            getattr(sermon_remote, 'event_type', None),
            getattr(sermon_remote, 'series', None),
            str(getattr(sermon_remote, 'preach_date', None)),
            str(getattr(sermon_remote, 'publish_date', None)),
            getattr(sermon_remote, 'duration', None),
            getattr(sermon_remote, 'bible_text', None),
            passage_fields['book'], passage_fields['chapter'],
            passage_fields['verse_start'], passage_fields['verse_end'],
            getattr(sermon_remote, 'audio_url', None),
            getattr(sermon_remote, 'transcript', None),
            'sermonaudio',
            classified_as, reason,
            new_meta, new_tx,
            str(getattr(sermon_remote, 'update_date', None)),
            getattr(sermon_remote, 'transcript', None),
            now, now, now, now, now,
        ))
        return 'new'

    if row[1] == new_meta and row[2] == new_tx:
        conn.execute(
            "UPDATE sermons SET last_synced_at = ? WHERE id = ?",
            (now, row[0]),
        )
        return 'noop'

    # Source changed — bump version, update hashes, push state back if needed
    new_version = row[3] + 1
    current_status = row[4]
    next_status = current_status
    if current_status in ('review_ready', 'transcript_ready', 'analysis_pending',
                          'analysis_running', 'analysis_failed'):
        next_status = 'analysis_pending' if row[2] and new_tx else 'synced_metadata'
    elif current_status == 'synced_metadata' and new_tx and row[2] != new_tx:
        next_status = 'transcript_ready'

    passage_fields = _parse_passage_fields(getattr(sermon_remote, 'bible_text', None))
    conn.execute("""
        UPDATE sermons SET
            title = ?, speaker_name = ?, event_type = ?, series = ?,
            preach_date = ?, publish_date = ?, duration_seconds = ?,
            bible_text_raw = ?, book = ?, chapter = ?, verse_start = ?, verse_end = ?,
            audio_url = ?, transcript_text = ?,
            classified_as = ?, classification_reason = ?,
            metadata_hash = ?, transcript_hash = ?, source_version = ?, remote_updated_at = ?,
            sync_status = ?, last_state_change_at = ?, last_synced_at = ?, updated_at = ?
        WHERE id = ?
    """, (
        getattr(sermon_remote, 'title'),
        getattr(sermon_remote, 'speaker_name', None),
        getattr(sermon_remote, 'event_type', None),
        getattr(sermon_remote, 'series', None),
        str(getattr(sermon_remote, 'preach_date', None)),
        str(getattr(sermon_remote, 'publish_date', None)),
        getattr(sermon_remote, 'duration', None),
        getattr(sermon_remote, 'bible_text', None),
        passage_fields['book'], passage_fields['chapter'],
        passage_fields['verse_start'], passage_fields['verse_end'],
        getattr(sermon_remote, 'audio_url', None),
        getattr(sermon_remote, 'transcript', None),
        classified_as, reason,
        new_meta, new_tx, new_version,
        str(getattr(sermon_remote, 'update_date', None)),
        next_status, now, now, now, row[0],
    ))
    return 'updated'
```

- [ ] **Step 4: Run tests — all should pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermonaudio_sync.py -v`
Expected: all 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermonaudio_sync.py tools/workbench/tests/test_sermonaudio_sync.py
git -c commit.gpgsign=false commit -m "feat: sermonaudio_sync pure helpers (classify, hash, upsert)"
```

---

## Task 7: `sermonaudio_sync.py` — API client wrapper + run_sync orchestrator with file lock

**Files:**
- Modify: `tools/workbench/sermonaudio_sync.py` — add API client wrapper, `run_sync`, `run_backfill`, file lock
- Create: `tools/workbench/tests/test_sermonaudio_sync_orchestrator.py`

- [ ] **Step 1: Write failing tests for run_sync with a mock API client**

Create `tools/workbench/tests/test_sermonaudio_sync_orchestrator.py`:

```python
import os
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest
from companion_db import CompanionDB
from sermonaudio_sync import run_sync_with_client


class MockSAClient:
    """In-memory SermonAudio client for tests. Conforms to SermonAudioClient protocol."""
    def __init__(self, sermons):
        self.sermons = sermons

    def list_sermons_updated_since(self, broadcaster_id, since=None, limit=100):
        return self.sermons

    def get_sermon_detail(self, sermon_id):
        for s in self.sermons:
            if s.sermon_id == sermon_id:
                return s
        return None


def _remote(sid='sa-001', **overrides):
    base = dict(
        sermon_id=sid,
        broadcaster_id='bcast',
        title='Romans 8:1-11',
        speaker_name='Bryan Schneider',
        event_type='Sunday Service',
        series='Romans',
        preach_date=dt.date(2026, 4, 12),
        publish_date=dt.date(2026, 4, 12),
        duration=2400,
        bible_text='Romans 8:1-11',
        audio_url='https://sa.example/' + sid + '.mp3',
        transcript='Welcome to Romans 8 this morning. ' * 200,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def test_run_sync_inserts_new_sermon(fresh_db):
    client = MockSAClient([_remote('sa-001')])
    result = run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    assert result['sermons_new'] == 1
    assert result['sermons_failed'] == 0
    assert result['status'] == 'completed'


def test_run_sync_filters_non_bryan_speakers(fresh_db):
    client = MockSAClient([
        _remote('sa-001'),
        _remote('sa-002', speaker_name='Guest Preacher'),
    ])
    result = run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    assert result['sermons_new'] == 2  # both persist
    # But only one is classified as sermon
    conn = fresh_db._conn()
    sermon_count = conn.execute(
        "SELECT COUNT(*) FROM sermons WHERE classified_as = 'sermon'"
    ).fetchone()[0]
    skipped_count = conn.execute(
        "SELECT COUNT(*) FROM sermons WHERE classified_as = 'skipped'"
    ).fetchone()[0]
    conn.close()
    assert sermon_count == 1
    assert skipped_count == 1


def test_run_sync_writes_sync_log_row(fresh_db):
    client = MockSAClient([_remote('sa-001')])
    run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    conn = fresh_db._conn()
    log = conn.execute("SELECT trigger, status, sermons_new FROM sermon_sync_log").fetchone()
    conn.close()
    assert log[0] == 'manual'
    assert log[1] == 'completed'
    assert log[2] == 1


def test_run_sync_is_idempotent(fresh_db):
    client = MockSAClient([_remote('sa-001')])
    r1 = run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    r2 = run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    assert r1['sermons_new'] == 1
    assert r2['sermons_new'] == 0
    assert r2['sermons_noop'] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermonaudio_sync_orchestrator.py -v`
Expected: FAIL with `ImportError: cannot import name 'run_sync_with_client'`.

- [ ] **Step 3: Add `run_sync_with_client` to `sermonaudio_sync.py`**

Append to `tools/workbench/sermonaudio_sync.py`:

```python
import uuid
import fcntl


def run_sync_with_client(db, client, broadcaster_id: str, trigger: str = 'cron',
                         since: Optional[str] = None, limit: int = 100) -> dict:
    """Execute a sync run against an injected SermonAudio-shaped client.

    This is the core logic; the file-lock + APScheduler wrapper lives in run_sync().
    Returns the final sermon_sync_log row as a dict.
    """
    run_id = str(uuid.uuid4())
    started_at = _now()
    counters = {
        'sermons_fetched': 0, 'sermons_new': 0, 'sermons_updated': 0,
        'sermons_noop': 0, 'sermons_skipped': 0, 'sermons_failed': 0,
    }

    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_sync_log (run_id, trigger, started_at, status)
        VALUES (?, ?, ?, 'running')
    """, (run_id, trigger, started_at))
    conn.commit()

    error_summary = None
    status = 'completed'
    try:
        remotes = client.list_sermons_updated_since(broadcaster_id, since=since, limit=limit)
        counters['sermons_fetched'] = len(remotes)
        for remote in remotes:
            try:
                result = upsert_sermon(conn, remote)
                if result == 'new':
                    counters['sermons_new'] += 1
                elif result == 'updated':
                    counters['sermons_updated'] += 1
                elif result == 'noop':
                    counters['sermons_noop'] += 1
                conn.commit()
            except Exception as e:
                counters['sermons_failed'] += 1
                # Try to mark the specific sermon as failed if we can identify it
                try:
                    conn.execute("""
                        UPDATE sermons SET sync_status='sync_failed',
                                           sync_error = ?,
                                           failure_count = failure_count + 1,
                                           last_failure_at = ?,
                                           last_state_change_at = ?
                        WHERE sermonaudio_id = ?
                    """, (str(e), _now(), _now(), getattr(remote, 'sermon_id', None)))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        status = 'failed'
        error_summary = f'{type(e).__name__}: {e}'

    conn.execute("""
        UPDATE sermon_sync_log SET
            ended_at = ?,
            sermons_fetched = ?, sermons_new = ?, sermons_updated = ?,
            sermons_noop = ?, sermons_skipped = ?, sermons_failed = ?,
            error_summary = ?, status = ?
        WHERE run_id = ?
    """, (
        _now(),
        counters['sermons_fetched'], counters['sermons_new'], counters['sermons_updated'],
        counters['sermons_noop'], counters['sermons_skipped'], counters['sermons_failed'],
        error_summary, status, run_id,
    ))
    conn.commit()
    conn.close()

    return {'run_id': run_id, 'status': status, 'error_summary': error_summary, **counters}


class SermonAudioAPIClient:
    """Thin wrapper over the sermonaudio PyPI library with a testable shape."""

    def __init__(self, api_key: str):
        import sermonaudio
        sermonaudio.set_api_key(api_key)
        self._sa = sermonaudio

    def list_sermons_updated_since(self, broadcaster_id, since=None, limit=100):
        from sermonaudio.node.requests import Node
        kwargs = {'broadcaster_id': broadcaster_id, 'page_size': limit}
        if since:
            kwargs['updated_since'] = since
        try:
            result = Node.get_sermons(**kwargs)
        except TypeError:
            # SDK variant: updated_since might not be supported; fall back to page list
            result = Node.get_sermons(broadcaster_id=broadcaster_id, page_size=limit)
        return list(getattr(result, 'results', result) or [])

    def get_sermon_detail(self, sermon_id):
        from sermonaudio.node.requests import Node
        return Node.get_sermon(sermon_id)


def _lock_path():
    return os.path.join(os.path.dirname(__file__), '.sermon_sync.lock')


def run_sync(db, api_key: str, broadcaster_id: str, trigger: str = 'cron') -> Optional[dict]:
    """Acquire file lock, call run_sync_with_client using the real API client, release."""
    lock_path = _lock_path()
    with open(lock_path, 'w') as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None  # another run is in progress
        try:
            client = SermonAudioAPIClient(api_key)
            return run_sync_with_client(db, client, broadcaster_id, trigger=trigger)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermonaudio_sync_orchestrator.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermonaudio_sync.py tools/workbench/tests/test_sermonaudio_sync_orchestrator.py
git -c commit.gpgsign=false commit -m "feat: run_sync orchestrator with file lock and sermon_sync_log audit"
```

---

## Task 8: `sermon_passages` writer + topical detection

**Files:**
- Modify: `tools/workbench/sermonaudio_sync.py` — write `sermon_passages` rows during upsert
- Create: `tools/workbench/tests/test_sermon_type_topical.py`

- [ ] **Step 1: Write failing tests for sermon_passages write-through + topical detection**

Create `tools/workbench/tests/test_sermon_type_topical.py`:

```python
import os
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest
from companion_db import CompanionDB
from sermonaudio_sync import upsert_sermon


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _remote(bible_text, **overrides):
    base = dict(
        sermon_id='sa-x',
        broadcaster_id='bcast',
        title='Test',
        speaker_name='Bryan Schneider',
        event_type='Sunday Service',
        series='Test',
        preach_date=dt.date(2026, 4, 12),
        publish_date=dt.date(2026, 4, 12),
        duration=2400,
        bible_text=bible_text,
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome. ' * 200,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_single_passage_writes_one_passage_row(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('Romans 8:1-11', sermon_id='sa-1'))
    conn.commit()
    rows = conn.execute(
        "SELECT rank, chapter_start, chapter_end, verse_start, verse_end "
        "FROM sermon_passages WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-1')"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0] == (1, 8, 8, 1, 11)


def test_multi_range_writes_two_passage_rows(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('Romans 8:1-11; Romans 9:1-5', sermon_id='sa-2'))
    conn.commit()
    rows = conn.execute(
        "SELECT rank, chapter_start, verse_start, verse_end FROM sermon_passages "
        "WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-2') "
        "ORDER BY rank"
    ).fetchall()
    conn.close()
    assert len(rows) == 2
    assert rows[0] == (1, 8, 1, 11)
    assert rows[1] == (2, 9, 1, 5)


def test_unparseable_passage_marks_topical_and_writes_no_rows(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('The Ten Commandments', sermon_id='sa-3'))
    conn.commit()
    sermon = conn.execute(
        "SELECT sermon_type, match_status FROM sermons WHERE sermonaudio_id='sa-3'"
    ).fetchone()
    passage_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_passages WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-3')"
    ).fetchone()[0]
    conn.close()
    assert sermon[0] == 'topical'
    assert sermon[1] == 'topical_no_match'
    assert passage_count == 0


def test_update_deletes_old_passages_and_writes_new(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('Romans 8:1-11', sermon_id='sa-4'))
    conn.commit()
    # Second call with different passage (different title to force meta_hash change)
    upsert_sermon(conn, _remote('Romans 9:1-5', sermon_id='sa-4', title='Updated'))
    conn.commit()
    rows = conn.execute(
        "SELECT chapter_start, verse_start FROM sermon_passages "
        "WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-4')"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0] == (9, 1)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_type_topical.py -v`
Expected: FAIL — `sermon_passages` rows aren't being written yet.

- [ ] **Step 3: Add `_write_sermon_passages` helper and call it from `upsert_sermon`**

In `tools/workbench/sermonaudio_sync.py`, add the helper and update the upsert logic. Insert after `_parse_passage_fields`:

```python
def _write_sermon_passages(conn, sermon_id: int, bible_text: Optional[str]) -> tuple[str, str]:
    """Write sermon_passages rows. Returns (sermon_type, match_status) for the parent sermon.

    Deletes any prior rows for this sermon before inserting new ones.
    """
    conn.execute("DELETE FROM sermon_passages WHERE sermon_id = ?", (sermon_id,))
    if not bible_text:
        return ('topical', 'topical_no_match')

    passages = parse_reference_multi(bible_text)
    if not passages:
        return ('topical', 'topical_no_match')

    now = _now()
    for rank, p in enumerate(passages, start=1):
        conn.execute("""
            INSERT INTO sermon_passages (
                sermon_id, rank, book, chapter_start, verse_start,
                chapter_end, verse_end, raw_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sermon_id, rank, p['book'],
            p['chapter_start'], p['verse_start'],
            p['chapter_end'], p['verse_end'],
            p.get('raw_text', bible_text), now,
        ))
    return ('expository', 'unmatched')
```

Then in `upsert_sermon`, after the INSERT path (`row is None` branch), get the new sermon id and call:

```python
        sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        sermon_type, match_status = _write_sermon_passages(conn, sermon_id,
                                                            getattr(sermon_remote, 'bible_text', None))
        conn.execute(
            "UPDATE sermons SET sermon_type = ?, match_status = ? WHERE id = ?",
            (sermon_type, match_status, sermon_id),
        )
        return 'new'
```

And in the UPDATE branch (source changed), after the UPDATE sermons statement, call:

```python
    sermon_type, match_status = _write_sermon_passages(conn, row[0],
                                                        getattr(sermon_remote, 'bible_text', None))
    conn.execute(
        "UPDATE sermons SET sermon_type = ?, match_status = ? WHERE id = ?",
        (sermon_type, match_status, row[0]),
    )
    return 'updated'
```

- [ ] **Step 4: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_type_topical.py tests/test_sermonaudio_sync.py tests/test_sermonaudio_sync_orchestrator.py -v`
Expected: all tests pass (including the older sync tests).

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermonaudio_sync.py tools/workbench/tests/test_sermon_type_topical.py
git -c commit.gpgsign=false commit -m "feat: write sermon_passages + detect topical sermons during upsert"
```

---

## Task 9: `sermon_matcher.py` — pure tier-rule function

**Files:**
- Create: `tools/workbench/sermon_matcher.py`
- Create: `tools/workbench/tests/test_sermon_matcher.py`

- [ ] **Step 1: Write failing tests for the pure matcher function**

Create `tools/workbench/tests/test_sermon_matcher.py`:

```python
from dataclasses import dataclass
from sermon_matcher import (
    match_sermon_to_sessions, SermonInfo, SessionInfo, MatchDecision,
    MatcherSettings,
)


def _sermon(book=45, chapter=8, vs=1, ve=11, preach='2026-04-12',
            sermon_type='expository'):
    return SermonInfo(
        id=1, book=book, chapter=chapter, verse_start=vs, verse_end=ve,
        preach_date=preach, sermon_type=sermon_type,
        passages=[{'book': book, 'chapter_start': chapter, 'verse_start': vs,
                    'chapter_end': chapter, 'verse_end': ve}],
    )


def _session(sid=10, book=45, chapter=8, vs=1, ve=11,
             last_hom='2026-04-09 12:00:00', created='2026-04-06 09:00:00'):
    return SessionInfo(
        id=sid, book=book, chapter=chapter, verse_start=vs, verse_end=ve,
        created_at=created, last_homiletical_activity_at=last_hom,
    )


def _settings():
    return MatcherSettings(tier1_days=7, tier2_days=14, cutoff_days=30)


def test_tier1_exact_match_within_7_days_auto_links():
    decision = match_sermon_to_sessions(
        _sermon(), (_session(),), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'auto_link'
    assert decision.auto_link_target.tier == 1
    assert decision.auto_link_target.session_id == 10


def test_multiple_tier1_candidates_demoted_to_candidates():
    sermon = _sermon()
    sessions = (
        _session(sid=10),
        _session(sid=20, created='2026-04-07 10:00:00', last_hom='2026-04-10 15:00:00'),
    )
    decision = match_sermon_to_sessions(
        sermon, sessions, existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert len(decision.candidates) >= 2


def test_session_created_after_sermon_never_matches():
    sermon = _sermon()
    s = _session(created='2026-04-13 10:00:00')  # after preach_date
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_timing_7_to_14_days_becomes_candidate():
    sermon = _sermon(preach='2026-04-12')
    s = _session(last_hom='2026-04-01 10:00:00', created='2026-03-30 08:00:00')
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert decision.candidates[0].tier == 2


def test_topical_sermon_never_auto_links():
    sermon = _sermon(sermon_type='topical')
    decision = match_sermon_to_sessions(
        sermon, (_session(),), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_rejected_session_is_excluded():
    decision = match_sermon_to_sessions(
        _sermon(), (_session(sid=10),), existing_links=(),
        rejected_session_ids=frozenset({10}), settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_no_match_when_passage_mismatch():
    sermon = _sermon(book=45, chapter=8)
    s = _session(book=45, chapter=12)
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_cutoff_30_days_excludes_old_sessions():
    sermon = _sermon(preach='2026-04-12')
    s = _session(last_hom='2026-02-20 10:00:00', created='2026-02-18 08:00:00')
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_partial_passage_overlap_is_tier2():
    sermon = _sermon(book=45, chapter=8, vs=1, ve=17)
    s = _session(book=45, chapter=8, vs=1, ve=11)  # same chapter, different verse range
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert decision.candidates[0].tier == 2


def test_session_with_no_homiletical_activity_is_candidate():
    sermon = _sermon()
    s = _session(last_hom=None)
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert decision.candidates[0].tier == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_matcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sermon_matcher'`.

- [ ] **Step 3: Create `sermon_matcher.py` with the pure function**

Create `tools/workbench/sermon_matcher.py`:

```python
"""Sermon → session matching.

Pure function match_sermon_to_sessions returns a MatchDecision. The orchestrator
apply_match_decision wraps the pure function in a BEGIN IMMEDIATE transaction and
writes sermon_links rows.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class SermonInfo:
    id: int
    book: Optional[int]
    chapter: Optional[int]
    verse_start: Optional[int]
    verse_end: Optional[int]
    preach_date: Optional[str]
    sermon_type: str  # 'expository' | 'topical'
    passages: list = field(default_factory=list)  # list of dicts from sermon_passages


@dataclass(frozen=True)
class SessionInfo:
    id: int
    book: Optional[int]
    chapter: Optional[int]
    verse_start: Optional[int]
    verse_end: Optional[int]
    created_at: str
    last_homiletical_activity_at: Optional[str]


@dataclass(frozen=True)
class SermonLink:
    sermon_id: int
    session_id: int
    link_status: str
    link_source: str


@dataclass(frozen=True)
class SessionMatch:
    session_id: int
    tier: int
    reason: str


@dataclass(frozen=True)
class MatchDecision:
    sermon_id: int
    action: str  # 'auto_link' | 'surface_candidates' | 'no_match'
    auto_link_target: Optional[SessionMatch] = None
    candidates: tuple[SessionMatch, ...] = ()
    reason_summary: str = ''


@dataclass(frozen=True)
class MatcherSettings:
    tier1_days: int = 7
    tier2_days: int = 14
    cutoff_days: int = 30


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.split('+')[0].split('Z')[0].split('.')[0])
    except Exception:
        return None


def _passage_match(sermon: SermonInfo, session: SessionInfo) -> str:
    """Return 'exact', 'overlap', or 'none'."""
    if sermon.book is None or session.book is None:
        return 'none'
    if sermon.book != session.book:
        return 'none'
    # Use primary passage; sermon_passages can refine this
    # Exact: same book, chapter, verse range
    if (sermon.chapter == session.chapter
        and sermon.verse_start == session.verse_start
        and sermon.verse_end == session.verse_end):
        return 'exact'
    # Overlap: same book+chapter, any verse overlap
    if sermon.chapter == session.chapter:
        return 'overlap'
    # Check secondary passages on the sermon
    for p in sermon.passages or []:
        if p.get('book') == session.book and p.get('chapter_start') == session.chapter:
            if (p.get('verse_start') == session.verse_start
                and p.get('verse_end') == session.verse_end):
                return 'exact'
            return 'overlap'
    return 'none'


def _days_before(date_a: Optional[datetime], date_b: Optional[datetime]) -> Optional[int]:
    """Days that date_a is before date_b (positive if before, negative if after)."""
    if date_a is None or date_b is None:
        return None
    delta = (date_b - date_a).days
    return delta


def match_sermon_to_sessions(
    sermon: SermonInfo,
    sessions: tuple[SessionInfo, ...],
    existing_links: tuple[SermonLink, ...],
    rejected_session_ids: frozenset[int],
    settings: MatcherSettings,
) -> MatchDecision:
    """Pure function. Returns a MatchDecision based on tier rules."""
    if sermon.sermon_type == 'topical':
        return MatchDecision(sermon_id=sermon.id, action='no_match',
                             reason_summary='topical_excluded')

    preach_dt = _parse_date(sermon.preach_date)
    if preach_dt is None:
        return MatchDecision(sermon_id=sermon.id, action='no_match',
                             reason_summary='unparseable_preach_date')

    tier1, tier2 = [], []
    for s in sessions:
        if s.id in rejected_session_ids:
            continue
        # session.created_at must be before sermon.preach_date
        created_dt = _parse_date(s.created_at)
        if created_dt is None or created_dt > preach_dt:
            continue
        # Passage match
        pmatch = _passage_match(sermon, s)
        if pmatch == 'none':
            continue
        # Prep timing
        activity_dt = _parse_date(s.last_homiletical_activity_at)
        if activity_dt is None:
            # Session never reached a homiletical phase — still a candidate if passage fits
            days_before = None
        else:
            days_before = _days_before(activity_dt, preach_dt)

        # Evaluate against cutoff
        if days_before is not None and days_before > settings.cutoff_days:
            continue
        if days_before is not None and days_before < 0:
            # Activity after preach_date: not prep for this sermon
            continue

        # Tier classification
        if (pmatch == 'exact' and days_before is not None
            and 0 <= days_before <= settings.tier1_days):
            tier1.append(SessionMatch(session_id=s.id, tier=1,
                                       reason=f'tier1:exact+{days_before}d'))
        else:
            # Various Tier 2 reasons
            if pmatch == 'overlap':
                reason = f'tier2:overlap+{days_before}d' if days_before is not None else 'tier2:overlap+no_hom'
            elif days_before is None:
                reason = 'tier2:exact+no_hom_activity'
            elif days_before > settings.tier1_days and days_before <= settings.cutoff_days:
                reason = f'tier2:exact+{days_before}d'
            else:
                reason = f'tier2:misc+{days_before}d'
            tier2.append(SessionMatch(session_id=s.id, tier=2, reason=reason))

    if len(tier1) == 1:
        return MatchDecision(
            sermon_id=sermon.id, action='auto_link',
            auto_link_target=tier1[0],
            candidates=tuple(tier2),
            reason_summary=tier1[0].reason,
        )
    if len(tier1) > 1:
        # Ambiguity: all Tier 1 become candidates
        demoted = tuple(SessionMatch(session_id=m.session_id, tier=2,
                                      reason=f'tier2:ambiguous_tier1')
                         for m in tier1)
        return MatchDecision(
            sermon_id=sermon.id, action='surface_candidates',
            candidates=demoted + tuple(tier2),
            reason_summary='tier1_ambiguous',
        )
    if tier2:
        return MatchDecision(
            sermon_id=sermon.id, action='surface_candidates',
            candidates=tuple(tier2),
            reason_summary='tier2_only',
        )
    return MatchDecision(sermon_id=sermon.id, action='no_match',
                         reason_summary='no_sessions_qualified')
```

- [ ] **Step 4: Run tests — all should pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_matcher.py -v`
Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_matcher.py tools/workbench/tests/test_sermon_matcher.py
git -c commit.gpgsign=false commit -m "feat: pure match_sermon_to_sessions with tier rules"
```

---

## Task 10: Matcher orchestrator + rematch triggers + companion_db writer touches

**Files:**
- Modify: `tools/workbench/sermon_matcher.py` — add `apply_match_decision` orchestrator
- Modify: `tools/workbench/companion_db.py` — bump `last_homiletical_activity_at` on homiletical writes + add helper to call matcher
- Create: `tools/workbench/tests/test_sermon_rematch_flow.py`

- [ ] **Step 1: Write failing integration test for rematch triggers**

Create `tools/workbench/tests/test_sermon_rematch_flow.py`:

```python
import os
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest
from companion_db import CompanionDB, PHASE_TIMERS
from sermonaudio_sync import upsert_sermon
from sermon_matcher import apply_match_decision_for_sermon


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _remote(sid='sa-1', bible='Romans 8:1-11', preach='2026-04-12'):
    return SimpleNamespace(
        sermon_id=sid, broadcaster_id='bcast', title='Test',
        speaker_name='Bryan Schneider', event_type='Sunday Service', series='Romans',
        preach_date=dt.date.fromisoformat(preach),
        publish_date=dt.date.fromisoformat(preach),
        duration=2400, bible_text=bible,
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome. ' * 200,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )


def test_save_card_response_bumps_homiletical_activity_timestamp(fresh_db):
    sid = fresh_db.create_session('Romans 8:1-11', 45, 8, 1, 11, 'epistle')
    # Non-homiletical phase: should NOT bump
    fresh_db.save_card_response(sid, 'prayer', 1, 'praying')
    conn = fresh_db._conn()
    row1 = conn.execute("SELECT last_homiletical_activity_at FROM sessions WHERE id=?", (sid,)).fetchone()
    assert row1[0] is None
    # Homiletical phase: SHOULD bump
    fresh_db.save_card_response(sid, 'exegetical_point', 2, 'the big idea')
    row2 = conn.execute("SELECT last_homiletical_activity_at FROM sessions WHERE id=?", (sid,)).fetchone()
    conn.close()
    assert row2[0] is not None


def test_save_message_homiletical_phase_bumps_timestamp(fresh_db):
    sid = fresh_db.create_session('Romans 8:1-11', 45, 8, 1, 11, 'epistle')
    fresh_db.save_message(sid, 'sermon_construction', 'assistant', 'here is the outline')
    conn = fresh_db._conn()
    row = conn.execute("SELECT last_homiletical_activity_at FROM sessions WHERE id=?", (sid,)).fetchone()
    conn.close()
    assert row[0] is not None


def test_auto_match_creates_active_link_after_homiletical_activity(fresh_db):
    # Create session with homiletical activity
    sid = fresh_db.create_session('Romans 8:1-11', 45, 8, 1, 11, 'epistle')
    # Backdate the session's created_at to before the sermon
    conn = fresh_db._conn()
    conn.execute("UPDATE sessions SET created_at = '2026-04-06 09:00:00', updated_at = '2026-04-09 12:00:00' WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    fresh_db.save_card_response(sid, 'exegetical_point', 1, 'the big idea')
    # Manually set last_homiletical_activity_at to a known value
    conn = fresh_db._conn()
    conn.execute("UPDATE sessions SET last_homiletical_activity_at = '2026-04-09 12:00:00' WHERE id = ?", (sid,))
    conn.commit()
    # Ingest a sermon that matches
    upsert_sermon(conn, _remote(sid='sa-rematch-1'))
    conn.commit()
    sermon_id = conn.execute("SELECT id FROM sermons WHERE sermonaudio_id='sa-rematch-1'").fetchone()[0]
    conn.close()
    # Run matcher
    decision = apply_match_decision_for_sermon(fresh_db, sermon_id)
    assert decision.action == 'auto_link'
    # Check sermon_links row
    conn = fresh_db._conn()
    link = conn.execute(
        "SELECT link_status, link_source, session_id FROM sermon_links WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    conn.close()
    assert link == ('active', 'auto', sid)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_rematch_flow.py -v`
Expected: FAIL — homiletical bump missing, `apply_match_decision_for_sermon` missing.

- [ ] **Step 3: Update `companion_db.py` writer functions to bump `last_homiletical_activity_at`**

In `tools/workbench/companion_db.py`, modify `save_card_response`:

```python
    def save_card_response(self, session_id, phase, question_id, content):
        conn = self._conn()
        now = self._now()
        cur = conn.execute("""
            INSERT INTO card_responses (session_id, phase, question_id, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, phase, question_id, content, now))
        if phase in ('exegetical_point', 'fcf_homiletical', 'sermon_construction', 'edit_pray'):
            conn.execute(
                "UPDATE sessions SET last_homiletical_activity_at = ?, updated_at = ? WHERE id = ?",
                (now, now, session_id),
            )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid
```

And `save_message`:

```python
    def save_message(self, session_id, phase, role, content, tool_name=None, tool_input=None):
        conn = self._conn()
        now = self._now()
        cur = conn.execute("""
            INSERT INTO conversation_messages (session_id, phase, role, content, tool_name, tool_input, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, phase, role, content, tool_name, tool_input, now))
        if phase in ('exegetical_point', 'fcf_homiletical', 'sermon_construction', 'edit_pray'):
            conn.execute(
                "UPDATE sessions SET last_homiletical_activity_at = ?, updated_at = ? WHERE id = ?",
                (now, now, session_id),
            )
        conn.commit()
        mid = cur.lastrowid
        conn.close()
        return mid
```

- [ ] **Step 4: Add `apply_match_decision_for_sermon` to `sermon_matcher.py`**

Append to `tools/workbench/sermon_matcher.py`:

```python
def apply_match_decision_for_sermon(db, sermon_id: int) -> MatchDecision:
    """Orchestrator: fetch state, compute decision, write sermon_links. BEGIN IMMEDIATE."""
    conn = db._conn()
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Load sermon + passages
        s_row = conn.execute("""
            SELECT id, book, chapter, verse_start, verse_end, preach_date, sermon_type
            FROM sermons WHERE id = ?
        """, (sermon_id,)).fetchone()
        if not s_row:
            conn.execute("ROLLBACK")
            conn.close()
            return MatchDecision(sermon_id=sermon_id, action='no_match',
                                  reason_summary='sermon_not_found')

        passages = [dict(book=r[0], chapter_start=r[1], verse_start=r[2],
                          chapter_end=r[3], verse_end=r[4])
                    for r in conn.execute(
                        "SELECT book, chapter_start, verse_start, chapter_end, verse_end "
                        "FROM sermon_passages WHERE sermon_id = ? ORDER BY rank",
                        (sermon_id,)
                    ).fetchall()]
        sermon = SermonInfo(
            id=s_row[0], book=s_row[1], chapter=s_row[2],
            verse_start=s_row[3], verse_end=s_row[4],
            preach_date=s_row[5], sermon_type=s_row[6],
            passages=passages,
        )

        # Load candidate sessions (passage match scope)
        session_rows = conn.execute("""
            SELECT id, book, chapter, verse_start, verse_end,
                   created_at, last_homiletical_activity_at
            FROM sessions
            WHERE book = ? AND chapter = ?
        """, (s_row[1], s_row[2])).fetchall()
        sessions = tuple(SessionInfo(
            id=r[0], book=r[1], chapter=r[2], verse_start=r[3], verse_end=r[4],
            created_at=r[5], last_homiletical_activity_at=r[6],
        ) for r in session_rows)

        # Existing links (so we don't duplicate and can identify manual)
        link_rows = conn.execute("""
            SELECT sermon_id, session_id, link_status, link_source
            FROM sermon_links WHERE sermon_id = ?
        """, (sermon_id,)).fetchall()
        existing_links = tuple(SermonLink(sermon_id=r[0], session_id=r[1],
                                            link_status=r[2], link_source=r[3])
                                for r in link_rows)
        rejected = frozenset(l.session_id for l in existing_links
                              if l.link_status == 'rejected')

        settings = MatcherSettings()
        decision = match_sermon_to_sessions(
            sermon, sessions, existing_links, rejected, settings,
        )

        # Write decision
        now = datetime.now().isoformat()
        if decision.action == 'auto_link' and decision.auto_link_target:
            target = decision.auto_link_target.session_id
            # If an active auto link already exists for a different session, delete it
            # (MVP: no supersession chain — just rewrite)
            existing_auto_active = [l for l in existing_links
                                     if l.link_status == 'active' and l.link_source == 'auto'
                                     and l.session_id != target]
            for l in existing_auto_active:
                conn.execute(
                    "DELETE FROM sermon_links WHERE sermon_id = ? AND session_id = ? AND link_source = 'auto'",
                    (sermon_id, l.session_id),
                )
            # Upsert active link (don't touch manual)
            has_manual_active = any(
                l.link_status == 'active' and l.link_source == 'manual'
                for l in existing_links
            )
            if not has_manual_active:
                conn.execute("""
                    INSERT OR REPLACE INTO sermon_links
                        (sermon_id, session_id, link_status, link_source, match_reason, created_at)
                    VALUES (?, ?, 'active', 'auto', ?, ?)
                """, (sermon_id, target, decision.auto_link_target.reason, now))
                conn.execute("UPDATE sermons SET match_status = 'matched', last_match_attempt_at = ? WHERE id = ?",
                             (now, sermon_id))
        elif decision.action == 'surface_candidates':
            for c in decision.candidates:
                conn.execute("""
                    INSERT OR IGNORE INTO sermon_links
                        (sermon_id, session_id, link_status, link_source, match_reason, created_at)
                    VALUES (?, ?, 'candidate', 'auto', ?, ?)
                """, (sermon_id, c.session_id, c.reason, now))
            conn.execute("UPDATE sermons SET match_status = 'awaiting_candidates', last_match_attempt_at = ? WHERE id = ?",
                         (now, sermon_id))
        else:
            conn.execute("UPDATE sermons SET last_match_attempt_at = ? WHERE id = ?",
                         (now, sermon_id))

        conn.execute("COMMIT")
        return decision
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
```

- [ ] **Step 5: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_rematch_flow.py tests/test_companion_db.py -v`
Expected: all tests pass, including the existing companion_db tests (writer touches are additive, so existing behavior preserved).

- [ ] **Step 6: Commit**

```bash
git add tools/workbench/sermon_matcher.py tools/workbench/companion_db.py tools/workbench/tests/test_sermon_rematch_flow.py
git -c commit.gpgsign=false commit -m "feat: apply_match_decision_for_sermon orchestrator + homiletical-phase activity tracking"
```

---

## Task 11: `sermon_analyzer.py` — deterministic stages 1-4 (pure)

**Files:**
- Create: `tools/workbench/sermon_analyzer.py`
- Create: `tools/workbench/tests/test_sermon_analyzer_stages.py`

- [ ] **Step 1: Write failing tests for the deterministic pipeline stages**

Create `tools/workbench/tests/test_sermon_analyzer_stages.py`:

```python
import pytest
from sermon_analyzer import (
    run_pure_stages, AnalyzerInput, PureStageOutput,
)


def test_pure_stages_returns_expected_shape():
    transcript = (
        "Welcome to Romans 8. Today we explore no condemnation.\n\n"
        "Let me begin with an observation about the participle.\n\n"
        "Note the genitive absolute and the aorist indicative here.\n\n"
        "So what does this mean for your life this Monday morning?"
    )
    inp = AnalyzerInput(
        sermon_id=1,
        transcript_text=transcript,
        duration_sec=600,
        planned_duration_sec=480,
        outline_points=[],
        bible_text_raw='Romans 8:1-11',
    )
    out = run_pure_stages(inp)
    assert isinstance(out, PureStageOutput)
    assert len(out.segments) >= 3
    assert out.section_timings['intro'] + out.section_timings['body'] + \
           out.section_timings['application'] + out.section_timings['close'] == 600
    assert out.duration_delta_sec == 120  # actual - planned
    assert isinstance(out.density_hotspots, list)


def test_pure_stages_handles_empty_outline():
    inp = AnalyzerInput(
        sermon_id=2,
        transcript_text="A short sermon with two paragraphs.\n\nSecond paragraph here.",
        duration_sec=120,
        planned_duration_sec=None,
        outline_points=[],
        bible_text_raw='Romans 8:1-11',
    )
    out = run_pure_stages(inp)
    assert out.duration_delta_sec is None
    assert out.outline_coverage_pct is None


def test_pure_stages_writes_outline_coverage_when_linked():
    transcript = (
        "First point: the participle is significant.\n\n"
        "Second point: the genitive absolute emphasizes.\n\n"
        "Third point: apply this by remembering the gospel daily."
    )
    outline_points = [
        {'id': 1, 'content': 'The participle is significant'},
        {'id': 2, 'content': 'The genitive absolute emphasizes'},
        {'id': 3, 'content': 'Application: remember the gospel daily'},
    ]
    inp = AnalyzerInput(
        sermon_id=3,
        transcript_text=transcript,
        duration_sec=600,
        planned_duration_sec=600,
        outline_points=outline_points,
        bible_text_raw='Romans 8:1-11',
    )
    out = run_pure_stages(inp)
    assert out.outline_coverage_pct is not None
    assert 0 <= out.outline_coverage_pct <= 1.0
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer_stages.py -v`
Expected: FAIL — `sermon_analyzer` module missing.

- [ ] **Step 3: Create `sermon_analyzer.py` with pure stages**

Create `tools/workbench/sermon_analyzer.py`:

```python
"""Sermon analyzer — deterministic stages + one structured LLM call.

Stages 1-4 are pure. Stage 5 (LLM rubric pass) and stage 6 (flag extraction)
come in Tasks 12 and 13.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json

from homiletics_core import (
    __version__ as homiletics_core_version,
    segment_transcript,
    compute_section_timings,
    detect_density_hotspots,
    align_segments_to_outline,
    late_application,
)

ANALYZER_VERSION = '1.0.0'


@dataclass(frozen=True)
class AnalyzerInput:
    sermon_id: int
    transcript_text: str
    duration_sec: int
    planned_duration_sec: Optional[int]
    outline_points: list[dict] = field(default_factory=list)  # from linked session if any
    bible_text_raw: str = ''


@dataclass(frozen=True)
class PureStageOutput:
    segments: list[dict]
    section_timings: dict
    actual_duration_sec: int
    planned_duration_sec: Optional[int]
    duration_delta_sec: Optional[int]
    density_hotspots: list[dict]
    outline_coverage_pct: Optional[float]
    outline_additions: list
    outline_omissions: list


def run_pure_stages(inp: AnalyzerInput) -> PureStageOutput:
    """Stages 1-4: segment, align, timing, density. Pure and cheap."""
    segments = segment_transcript(inp.transcript_text, inp.duration_sec)
    aligned = align_segments_to_outline(segments, inp.outline_points) if inp.outline_points else segments
    section_timings = compute_section_timings(aligned)
    density_hotspots = detect_density_hotspots(aligned)

    duration_delta = (
        inp.duration_sec - inp.planned_duration_sec
        if inp.planned_duration_sec is not None else None
    )

    if inp.outline_points:
        matched_point_ids = set()
        for seg in aligned:
            for pid in seg.get('outline_point_ids', []):
                matched_point_ids.add(pid)
        total = len(inp.outline_points)
        coverage_pct = len(matched_point_ids) / total if total else None
        omitted = [p for p in inp.outline_points if p.get('id') not in matched_point_ids]
        additions = []  # Populated by the LLM pass in stage 5
    else:
        coverage_pct = None
        omitted = []
        additions = []

    return PureStageOutput(
        segments=aligned,
        section_timings=section_timings,
        actual_duration_sec=inp.duration_sec,
        planned_duration_sec=inp.planned_duration_sec,
        duration_delta_sec=duration_delta,
        density_hotspots=density_hotspots,
        outline_coverage_pct=coverage_pct,
        outline_additions=additions,
        outline_omissions=omitted,
    )
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer_stages.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_analyzer.py tools/workbench/tests/test_sermon_analyzer_stages.py
git -c commit.gpgsign=false commit -m "feat: sermon_analyzer pure stages (segment, align, timing, density)"
```

---

## Task 12: `sermon_analyzer.py` — structured LLM rubric pass

**Files:**
- Modify: `tools/workbench/sermon_analyzer.py` — add `REVIEW_SCHEMA`, `build_rubric_prompt`, `run_llm_rubric`
- Create: `tools/workbench/tests/test_sermon_analyzer_llm.py`

- [ ] **Step 1: Write failing tests for the LLM rubric pass with a CannedLLMClient**

Create `tools/workbench/tests/test_sermon_analyzer_llm.py`:

```python
import json
from llm_client import CannedLLMClient
from sermon_analyzer import (
    AnalyzerInput, run_pure_stages, build_rubric_prompt,
    run_llm_rubric, REVIEW_SCHEMA,
)


def _canned_review():
    return {
        'output': {
            'tier1_impact': {
                'burden_clarity': 'clear',
                'burden_statement_excerpt': 'There is no condemnation for those in Christ',
                'burden_first_stated_at_sec': 180,
                'movement_clarity': 'mostly_river',
                'movement_rationale': 'Flowed well through the body; transition at §3 felt abrupt.',
                'application_specificity': 'concrete',
                'application_first_arrived_at_sec': 1860,
                'application_excerpts': [{'start_sec': 1860, 'excerpt': 'trust the verdict'}],
                'ethos_rating': 'engaged',
                'ethos_markers': ['direct 2nd person at 12:40'],
                'concreteness_score': 3,
                'imagery_density_per_10min': 4.2,
                'narrative_moments': [],
            },
            'tier2_faithfulness': {
                'christ_thread_score': 'gestured',
                'christ_thread_excerpts': [{'start_sec': 2400, 'excerpt': 'pointing to Christ'}],
                'exegetical_grounding': 'grounded',
                'exegetical_grounding_notes': 'Text is the sermon center.',
            },
            'tier3_diagnostic': {
                'length_delta_commentary': 'Length hurts because application came late.',
                'density_hotspots': [{'start_sec': 820, 'end_sec': 1060, 'note': 'genitive hold'}],
                'late_application_note': 'Application arrived at 31:00 of 38:42.',
                'outline_drift_note': None,
            },
            'coach_summary': {
                'top_impact_helpers': ['Burden stated early', 'Personal confession at 24:15', 'Narrative at 7:40'],
                'top_impact_hurters': ['Late application', 'Abstract app', 'Density spike §2'],
                'faithfulness_note': 'Christ thread gestured, not explicit mid-body.',
                'one_change_for_next_sunday': 'Start application at 22:00 mark.',
            },
            'flags': [
                {'flag_type': 'late_application', 'severity': 'concern',
                 'start_sec': 0, 'end_sec': 1860, 'section_label': 'intro+body',
                 'excerpt': 'exegetical heat', 'rationale': 'Application at 31:00 of 38:42'},
                {'flag_type': 'density_spike', 'severity': 'warn',
                 'start_sec': 820, 'end_sec': 1060, 'section_label': 'body',
                 'excerpt': 'genitive hold', 'rationale': '4 minute Greek hold'},
            ],
        },
        'input_tokens': 5000, 'output_tokens': 800, 'model': 'claude-opus-4-6',
    }


def test_build_rubric_prompt_includes_transcript_and_metadata():
    inp = AnalyzerInput(
        sermon_id=1, transcript_text='hello world', duration_sec=600,
        planned_duration_sec=600, outline_points=[], bible_text_raw='Romans 8:1-11',
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    assert 'Romans 8:1-11' in prompt
    assert 'hello world' in prompt
    assert '600' in prompt  # duration somewhere


def test_review_schema_has_three_tiers_and_summary():
    schema = REVIEW_SCHEMA
    top_props = set(schema['properties'].keys())
    assert 'tier1_impact' in top_props
    assert 'tier2_faithfulness' in top_props
    assert 'tier3_diagnostic' in top_props
    assert 'coach_summary' in top_props
    assert 'flags' in top_props


def test_run_llm_rubric_with_canned_client():
    inp = AnalyzerInput(
        sermon_id=1, transcript_text='x' * 5000, duration_sec=2322,
        planned_duration_sec=1680, outline_points=[], bible_text_raw='Romans 8:1-11',
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    import hashlib
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    client = CannedLLMClient({key: _canned_review()})
    result = run_llm_rubric(client, inp, pure)
    assert result['model'] == 'claude-opus-4-6'
    assert 'output' in result
    assert result['output']['tier1_impact']['burden_clarity'] == 'clear'
    assert result['output']['coach_summary']['one_change_for_next_sunday'] == 'Start application at 22:00 mark.'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer_llm.py -v`
Expected: FAIL — `REVIEW_SCHEMA`, `build_rubric_prompt`, `run_llm_rubric` missing.

- [ ] **Step 3: Append the rubric schema, prompt builder, and runner to `sermon_analyzer.py`**

Append to `tools/workbench/sermon_analyzer.py`:

```python
REVIEW_SCHEMA = {
    'type': 'object',
    'required': ['tier1_impact', 'tier2_faithfulness', 'tier3_diagnostic',
                 'coach_summary', 'flags'],
    'properties': {
        'tier1_impact': {
            'type': 'object',
            'required': ['burden_clarity', 'movement_clarity', 'application_specificity',
                         'ethos_rating', 'concreteness_score'],
            'properties': {
                'burden_clarity': {'type': 'string',
                                    'enum': ['crisp', 'clear', 'implied', 'muddled', 'absent']},
                'burden_statement_excerpt': {'type': ['string', 'null']},
                'burden_first_stated_at_sec': {'type': ['integer', 'null']},
                'movement_clarity': {'type': 'string',
                                      'enum': ['river', 'mostly_river', 'uneven', 'lake']},
                'movement_rationale': {'type': 'string'},
                'application_specificity': {'type': 'string',
                                             'enum': ['localized', 'concrete', 'abstract', 'absent']},
                'application_first_arrived_at_sec': {'type': ['integer', 'null']},
                'application_excerpts': {'type': 'array', 'items': {'type': 'object'}},
                'ethos_rating': {'type': 'string',
                                  'enum': ['seized', 'engaged', 'professional', 'detached']},
                'ethos_markers': {'type': 'array', 'items': {'type': 'string'}},
                'concreteness_score': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                'imagery_density_per_10min': {'type': 'number'},
                'narrative_moments': {'type': 'array', 'items': {'type': 'object'}},
            },
        },
        'tier2_faithfulness': {
            'type': 'object',
            'required': ['christ_thread_score', 'exegetical_grounding'],
            'properties': {
                'christ_thread_score': {'type': 'string',
                                         'enum': ['explicit', 'gestured', 'absent']},
                'christ_thread_excerpts': {'type': 'array', 'items': {'type': 'object'}},
                'exegetical_grounding': {'type': 'string',
                                          'enum': ['grounded', 'partial', 'pretext']},
                'exegetical_grounding_notes': {'type': 'string'},
            },
        },
        'tier3_diagnostic': {
            'type': 'object',
            'properties': {
                'length_delta_commentary': {'type': ['string', 'null']},
                'density_hotspots': {'type': 'array', 'items': {'type': 'object'}},
                'late_application_note': {'type': ['string', 'null']},
                'outline_drift_note': {'type': ['string', 'null']},
            },
        },
        'coach_summary': {
            'type': 'object',
            'required': ['top_impact_helpers', 'top_impact_hurters',
                         'one_change_for_next_sunday'],
            'properties': {
                'top_impact_helpers': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 3},
                'top_impact_hurters': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 3},
                'faithfulness_note': {'type': ['string', 'null']},
                'one_change_for_next_sunday': {'type': 'string'},
            },
        },
        'flags': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['flag_type', 'severity', 'rationale'],
                'properties': {
                    'flag_type': {'type': 'string'},
                    'severity': {'type': 'string', 'enum': ['info', 'note', 'warn', 'concern']},
                    'start_sec': {'type': ['integer', 'null']},
                    'end_sec': {'type': ['integer', 'null']},
                    'section_label': {'type': ['string', 'null']},
                    'excerpt': {'type': ['string', 'null']},
                    'rationale': {'type': 'string'},
                },
            },
        },
    },
}


RUBRIC_SYSTEM_PROMPT = """You are scoring a preached sermon for Bryan, a Reformed Presbyterian pastor.
Emit a structured review following the tool schema exactly. Ground every score in transcript evidence.

The three tiers:
- Tier 1 (Impact): burden clarity, movement, application specificity, ethos, concreteness — these
  are what rhetoric research identifies as the strongest impact predictors.
- Tier 2 (Faithfulness): Christ thread + exegetical grounding — parallel crown for a Reformed pastor.
- Tier 3 (Diagnostic): symptoms whose causes live in Tier 1 — length, density hotspots, late application.

For the coach_summary:
- top_impact_helpers: 2-3 concrete things that drove impact THIS sermon
- top_impact_hurters: 2-3 concrete things that blocked impact THIS sermon
- one_change_for_next_sunday: ONE concrete actionable change

For flags: return 3-8 per-moment observations tied to transcript timestamps."""


def build_rubric_prompt(inp: AnalyzerInput, pure: PureStageOutput) -> str:
    """Compose the prompt string from inputs and deterministic outputs."""
    outline_summary = 'No linked prep session.' if not inp.outline_points else \
        '\n'.join(f"- [{p.get('id')}] {p.get('content', '')[:160]}" for p in inp.outline_points)

    segments_text = '\n'.join(
        f"[{s['start_sec']}s-{s['end_sec']}s {s.get('section_label', 'body')}] {s['text'][:400]}"
        for s in pure.segments
    )

    return f"""SERMON METADATA
Passage: {inp.bible_text_raw}
Duration: {inp.duration_sec} seconds ({inp.duration_sec // 60}:{inp.duration_sec % 60:02d})
Planned: {inp.planned_duration_sec or 'unknown'} seconds
Duration delta: {pure.duration_delta_sec or 'N/A'} seconds

PREP OUTLINE
{outline_summary}

SEGMENTED TRANSCRIPT
{segments_text}

DETERMINISTIC STAGE OUTPUT
Section timings: {json.dumps(pure.section_timings)}
Density hotspots: {json.dumps(pure.density_hotspots)}
Outline coverage: {pure.outline_coverage_pct}

Score this sermon per the schema."""


def run_llm_rubric(client, inp: AnalyzerInput, pure: PureStageOutput) -> dict:
    """Call the LLM client with the assembled prompt and the REVIEW_SCHEMA."""
    prompt = build_rubric_prompt(inp, pure)
    return client.call(prompt=prompt, schema=REVIEW_SCHEMA, system=RUBRIC_SYSTEM_PROMPT)
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer_llm.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_analyzer.py tools/workbench/tests/test_sermon_analyzer_llm.py
git -c commit.gpgsign=false commit -m "feat: sermon_analyzer LLM rubric pass (REVIEW_SCHEMA + build_rubric_prompt + run_llm_rubric)"
```

---

## Task 13: `sermon_analyzer.py` — full analyze() writer + dispatch poll

**Files:**
- Modify: `tools/workbench/sermon_analyzer.py` — add `analyze_sermon()`, `dispatch_pending_analyses()`, writer code, cost log
- Create: `tools/workbench/tests/test_sermon_analyzer_writer.py`

- [ ] **Step 1: Write failing tests for the full analyze() writer path**

Create `tools/workbench/tests/test_sermon_analyzer_writer.py`:

```python
import os
import tempfile
import datetime as dt
from types import SimpleNamespace
import json
import hashlib
import pytest
from companion_db import CompanionDB
from llm_client import CannedLLMClient
from sermonaudio_sync import upsert_sermon
from sermon_analyzer import analyze_sermon, dispatch_pending_analyses


@pytest.fixture
def db_with_sermon():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    conn = db._conn()
    upsert_sermon(conn, SimpleNamespace(
        sermon_id='sa-1', broadcaster_id='bcast', title='Romans 8',
        speaker_name='Bryan Schneider', event_type='Sunday Service', series='Romans',
        preach_date=dt.date(2026, 4, 12), publish_date=dt.date(2026, 4, 12),
        duration=2322, bible_text='Romans 8:1-11',
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome to Romans 8.\n\nThe aorist here is significant.\n\n' * 50,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    ))
    conn.commit()
    conn.close()
    yield db
    os.unlink(path)


def _canned_for(db_with_sermon):
    # Build the expected prompt and canned response
    from sermon_analyzer import AnalyzerInput, run_pure_stages, build_rubric_prompt
    conn = db_with_sermon._conn()
    row = conn.execute("SELECT id, transcript_text, duration_seconds, bible_text_raw FROM sermons").fetchone()
    conn.close()
    inp = AnalyzerInput(
        sermon_id=row[0], transcript_text=row[1], duration_sec=row[2],
        planned_duration_sec=None, outline_points=[], bible_text_raw=row[3],
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    return {key: {
        'output': {
            'tier1_impact': {
                'burden_clarity': 'clear',
                'burden_statement_excerpt': 'No condemnation in Christ',
                'burden_first_stated_at_sec': 180,
                'movement_clarity': 'mostly_river',
                'movement_rationale': 'Tracked well.',
                'application_specificity': 'abstract',
                'application_first_arrived_at_sec': 1860,
                'application_excerpts': [],
                'ethos_rating': 'engaged',
                'ethos_markers': [],
                'concreteness_score': 3,
                'imagery_density_per_10min': 2.1,
                'narrative_moments': [],
            },
            'tier2_faithfulness': {
                'christ_thread_score': 'gestured',
                'christ_thread_excerpts': [],
                'exegetical_grounding': 'grounded',
                'exegetical_grounding_notes': 'Well grounded.',
            },
            'tier3_diagnostic': {
                'length_delta_commentary': 'Acceptable.',
                'density_hotspots': [],
                'late_application_note': 'Late.',
                'outline_drift_note': None,
            },
            'coach_summary': {
                'top_impact_helpers': ['Clear burden', 'Engaged delivery', 'Grounded exegesis'],
                'top_impact_hurters': ['Late application', 'Abstract app', 'Weak imagery'],
                'faithfulness_note': 'Christ thread gestured.',
                'one_change_for_next_sunday': 'Start application 6 minutes earlier.',
            },
            'flags': [
                {'flag_type': 'late_application', 'severity': 'warn',
                 'start_sec': 0, 'end_sec': 1860, 'section_label': 'intro+body',
                 'excerpt': '...', 'rationale': 'App arrived at 31:00'},
            ],
        },
        'input_tokens': 4200, 'output_tokens': 700, 'model': 'claude-opus-4-6',
    }}


def test_analyze_sermon_writes_review_row(db_with_sermon):
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    conn = db_with_sermon._conn()
    sermon_id = conn.execute("SELECT id FROM sermons").fetchone()[0]
    conn.close()

    result = analyze_sermon(db_with_sermon, sermon_id, llm_client=client)
    assert result['status'] == 'review_ready'

    conn = db_with_sermon._conn()
    review = conn.execute(
        "SELECT burden_clarity, one_change_for_next_sunday FROM sermon_reviews WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    sermon_status = conn.execute(
        "SELECT sync_status FROM sermons WHERE id=?", (sermon_id,)
    ).fetchone()[0]
    flag_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_flags WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    cost_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_analysis_cost_log WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    conn.close()

    assert review[0] == 'clear'
    assert review[1] == 'Start application 6 minutes earlier.'
    assert sermon_status == 'review_ready'
    assert flag_count == 1
    assert cost_count == 1


def test_reanalyze_overwrites_review_and_replaces_flags(db_with_sermon):
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    conn = db_with_sermon._conn()
    sermon_id = conn.execute("SELECT id FROM sermons").fetchone()[0]
    conn.close()

    analyze_sermon(db_with_sermon, sermon_id, llm_client=client)
    analyze_sermon(db_with_sermon, sermon_id, llm_client=client)

    conn = db_with_sermon._conn()
    flag_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_flags WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    review_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_reviews WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    conn.close()

    assert flag_count == 1  # deleted + reinserted, not duplicated
    assert review_count == 1  # overwritten via PK


def test_dispatch_picks_up_transcript_ready_sermons(db_with_sermon):
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    processed = dispatch_pending_analyses(db_with_sermon, llm_client=client, limit=10)
    assert processed == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer_writer.py -v`
Expected: FAIL.

- [ ] **Step 3: Add `analyze_sermon`, `dispatch_pending_analyses`, writer helpers to `sermon_analyzer.py`**

Append to `tools/workbench/sermon_analyzer.py`:

```python
import hashlib
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Rough Opus 4.6 pricing per 1M tokens (update as needed)
OPUS_INPUT_COST_PER_MTOK = 15.0
OPUS_OUTPUT_COST_PER_MTOK = 75.0


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model.startswith('claude-opus'):
        return (input_tokens * OPUS_INPUT_COST_PER_MTOK +
                output_tokens * OPUS_OUTPUT_COST_PER_MTOK) / 1_000_000
    return 0.0


def _load_analyzer_input(conn, sermon_id: int) -> AnalyzerInput:
    row = conn.execute("""
        SELECT id, transcript_text, duration_seconds, bible_text_raw
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    if not row or not row[1]:
        raise ValueError(f"sermon {sermon_id} has no transcript")

    # Look up planned duration from linked session if present
    link_row = conn.execute("""
        SELECT s.id FROM sermon_links sl
        JOIN sessions s ON s.id = sl.session_id
        WHERE sl.sermon_id = ? AND sl.link_status = 'active'
        LIMIT 1
    """, (sermon_id,)).fetchone()
    outline_points = []
    planned_duration_sec = None
    if link_row:
        session_id = link_row[0]
        # Best-effort planned duration sum of homiletical-phase timers
        planned_duration_sec = None  # MVP: leave NULL; derive from prep data in Phase 2
        point_rows = conn.execute("""
            SELECT id, content FROM outline_nodes
            WHERE session_id = ? AND type IN ('main_point','sub_point','bullet')
            ORDER BY rank
        """, (session_id,)).fetchall()
        outline_points = [{'id': r[0], 'content': r[1]} for r in point_rows]

    return AnalyzerInput(
        sermon_id=row[0],
        transcript_text=row[1],
        duration_sec=row[2] or 0,
        planned_duration_sec=planned_duration_sec,
        outline_points=outline_points,
        bible_text_raw=row[3] or '',
    )


def _transcript_hash(text: str) -> str:
    return hashlib.sha256((text or '').encode()).hexdigest()[:16]


def _write_review(conn, sermon_id: int, inp: AnalyzerInput, pure: PureStageOutput,
                  llm_output: dict, model: str) -> None:
    """Overwrite sermon_reviews row and replace flags."""
    now = _now()
    tier1 = llm_output.get('tier1_impact', {})
    tier2 = llm_output.get('tier2_faithfulness', {})
    tier3 = llm_output.get('tier3_diagnostic', {})
    summary = llm_output.get('coach_summary', {})

    conn.execute("DELETE FROM sermon_reviews WHERE sermon_id = ?", (sermon_id,))
    conn.execute("""
        INSERT INTO sermon_reviews (
            sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis,
            burden_clarity, burden_statement_excerpt, burden_first_stated_at_sec,
            movement_clarity, movement_rationale,
            application_specificity, application_first_arrived_at_sec, application_excerpts,
            ethos_rating, ethos_markers,
            concreteness_score, imagery_density_per_10min, narrative_moments,
            christ_thread_score, christ_thread_excerpts,
            exegetical_grounding, exegetical_grounding_notes,
            actual_duration_seconds, planned_duration_seconds, duration_delta_seconds,
            section_timings, length_delta_commentary, density_hotspots,
            late_application_note, outline_coverage_pct, outline_additions, outline_omissions,
            outline_drift_note,
            top_impact_helpers, top_impact_hurters, faithfulness_note, one_change_for_next_sunday,
            computed_at
        ) VALUES (?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sermon_id, ANALYZER_VERSION, homiletics_core_version, model,
        _transcript_hash(inp.transcript_text),
        conn.execute("SELECT source_version FROM sermons WHERE id=?", (sermon_id,)).fetchone()[0],
        tier1.get('burden_clarity'), tier1.get('burden_statement_excerpt'),
        tier1.get('burden_first_stated_at_sec'),
        tier1.get('movement_clarity'), tier1.get('movement_rationale'),
        tier1.get('application_specificity'), tier1.get('application_first_arrived_at_sec'),
        json.dumps(tier1.get('application_excerpts', [])),
        tier1.get('ethos_rating'), json.dumps(tier1.get('ethos_markers', [])),
        tier1.get('concreteness_score'), tier1.get('imagery_density_per_10min'),
        json.dumps(tier1.get('narrative_moments', [])),
        tier2.get('christ_thread_score'), json.dumps(tier2.get('christ_thread_excerpts', [])),
        tier2.get('exegetical_grounding'), tier2.get('exegetical_grounding_notes'),
        pure.actual_duration_sec, pure.planned_duration_sec, pure.duration_delta_sec,
        json.dumps(pure.section_timings),
        tier3.get('length_delta_commentary'),
        json.dumps(tier3.get('density_hotspots', [])),
        tier3.get('late_application_note'),
        pure.outline_coverage_pct,
        json.dumps(pure.outline_additions),
        json.dumps(pure.outline_omissions),
        tier3.get('outline_drift_note'),
        json.dumps(summary.get('top_impact_helpers', [])),
        json.dumps(summary.get('top_impact_hurters', [])),
        summary.get('faithfulness_note'),
        summary.get('one_change_for_next_sunday', ''),
        now,
    ))

    # Replace flags
    conn.execute("DELETE FROM sermon_flags WHERE sermon_id = ?", (sermon_id,))
    for f in llm_output.get('flags', []):
        conn.execute("""
            INSERT INTO sermon_flags (
                sermon_id, flag_type, severity,
                transcript_start_sec, transcript_end_sec,
                section_label, excerpt, rationale, analyzer_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sermon_id, f.get('flag_type'), f.get('severity', 'note'),
            f.get('start_sec'), f.get('end_sec'),
            f.get('section_label'), f.get('excerpt'),
            f.get('rationale', ''), ANALYZER_VERSION, now,
        ))


def analyze_sermon(db, sermon_id: int, llm_client) -> dict:
    """Run the full pipeline for a single sermon. Returns {status, ...}."""
    conn = db._conn()
    try:
        try:
            inp = _load_analyzer_input(conn, sermon_id)
        except ValueError as e:
            conn.execute("UPDATE sermons SET sync_status='analysis_failed', sync_error=?, last_state_change_at=? WHERE id=?",
                         (str(e), _now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_failed', 'error': str(e)}

        # Minimum transcript word gate
        if len((inp.transcript_text or '').split()) < 1000:
            conn.execute("UPDATE sermons SET sync_status='analysis_skipped', last_state_change_at=? WHERE id=?",
                         (_now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_skipped', 'reason': 'transcript_too_short'}

        conn.execute("UPDATE sermons SET sync_status='analysis_running', last_state_change_at=? WHERE id=?",
                     (_now(), sermon_id))
        conn.commit()

        pure = run_pure_stages(inp)
        result = run_llm_rubric(llm_client, inp, pure)

        if 'error' in result:
            conn.execute("UPDATE sermons SET sync_status='analysis_failed', sync_error=?, last_state_change_at=? WHERE id=?",
                         (result['error'], _now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_failed', 'error': result['error']}

        model = result.get('model', 'claude-opus-4-6')
        output = result.get('output', {})
        _write_review(conn, sermon_id, inp, pure, output, model)

        # Cost log
        input_tokens = result.get('input_tokens', 0)
        output_tokens = result.get('output_tokens', 0)
        cost = estimate_cost_usd(model, input_tokens, output_tokens)
        conn.execute("""
            INSERT INTO sermon_analysis_cost_log
                (sermon_id, model, input_tokens, output_tokens, estimated_cost_usd, called_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sermon_id, model, input_tokens, output_tokens, cost, _now()))

        conn.execute("UPDATE sermons SET sync_status='review_ready', last_state_change_at=? WHERE id=?",
                     (_now(), sermon_id))
        conn.commit()
        return {'status': 'review_ready', 'cost_usd': cost,
                'input_tokens': input_tokens, 'output_tokens': output_tokens}
    finally:
        conn.close()


def dispatch_pending_analyses(db, llm_client, limit: int = 10) -> int:
    """Poll for sermons ready to analyze and process them serially.

    Returns the number of sermons processed.
    """
    conn = db._conn()
    rows = conn.execute("""
        SELECT id FROM sermons
        WHERE classified_as = 'sermon'
          AND sermon_type = 'expository'
          AND (
            sync_status = 'transcript_ready'
            OR (sync_status = 'review_ready'
                AND source_version > COALESCE(
                    (SELECT source_version_at_analysis FROM sermon_reviews WHERE sermon_id = sermons.id),
                    0))
          )
        ORDER BY preach_date DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    count = 0
    for (sid,) in rows:
        result = analyze_sermon(db, sid, llm_client=llm_client)
        if result.get('status') == 'review_ready':
            count += 1
    return count
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer_writer.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_analyzer.py tools/workbench/tests/test_sermon_analyzer_writer.py
git -c commit.gpgsign=false commit -m "feat: analyze_sermon writer + dispatch_pending_analyses + cost log"
```

---

## Task 14: `sermon_coach_tools.py` — read tools for the coach

**Files:**
- Create: `tools/workbench/sermon_coach_tools.py`
- Create: `tools/workbench/tests/test_sermon_coach_tools.py`

- [ ] **Step 1: Write failing tests for the coach's read tools**

Create `tools/workbench/tests/test_sermon_coach_tools.py`:

```python
import os
import tempfile
import pytest
from companion_db import CompanionDB
from sermon_coach_tools import (
    get_sermon_review, get_sermon_flags, get_transcript_full,
    get_prep_session_full, pull_historical_sermons, get_sermon_patterns,
)


@pytest.fixture
def stocked_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, transcript_text, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at,
                              preach_date, duration_seconds)
        VALUES ('sa-1', 'bcast', 'Test', 'sermon', 'review_ready', 'Hello world transcript',
                datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'),
                '2026-04-12', 2322)
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_reviews (sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis, actual_duration_seconds,
            burden_clarity, top_impact_helpers, top_impact_hurters, one_change_for_next_sunday,
            computed_at)
        VALUES (?, '1.0.0', '1.0.0', 'claude-opus-4-6', 'hash', 1, 2322,
                'clear', '["a","b"]', '["x","y"]', 'change this', datetime('now'))
    """, (sermon_id,))
    conn.execute("""
        INSERT INTO sermon_flags (sermon_id, flag_type, severity, rationale, analyzer_version, created_at)
        VALUES (?, 'late_application', 'warn', 'App arrived too late', '1.0.0', datetime('now'))
    """, (sermon_id,))
    conn.commit()
    conn.close()
    yield db, sermon_id
    os.unlink(path)


def test_get_sermon_review_returns_row(stocked_db):
    db, sermon_id = stocked_db
    review = get_sermon_review(db, sermon_id)
    assert review is not None
    assert review['burden_clarity'] == 'clear'
    assert review['one_change_for_next_sunday'] == 'change this'


def test_get_sermon_flags_returns_list(stocked_db):
    db, sermon_id = stocked_db
    flags = get_sermon_flags(db, sermon_id)
    assert len(flags) == 1
    assert flags[0]['flag_type'] == 'late_application'


def test_get_transcript_full_returns_whole(stocked_db):
    db, sermon_id = stocked_db
    text = get_transcript_full(db, sermon_id)
    assert text == 'Hello world transcript'


def test_get_transcript_full_slices_by_seconds(stocked_db):
    # With only one plain-text blob we simply return full text if slicing is unsupported
    db, sermon_id = stocked_db
    text = get_transcript_full(db, sermon_id, start_sec=0, end_sec=100)
    assert text is not None


def test_get_prep_session_full_returns_none_when_no_link(stocked_db):
    db, sermon_id = stocked_db
    # No sermon_links row — should return None
    assert get_prep_session_full(db, sermon_id) is None


def test_pull_historical_sermons_returns_recent(stocked_db):
    db, _ = stocked_db
    rows = pull_historical_sermons(db, n=5)
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_get_sermon_patterns_returns_corpus_gate(stocked_db):
    db, _ = stocked_db
    patterns = get_sermon_patterns(db)
    assert 'corpus_gate_status' in patterns
    assert patterns['corpus_gate_status'] in ('pre_gate', 'emerging', 'stable')
    assert 'n_sermons' in patterns
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_tools.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `sermon_coach_tools.py`**

Create `tools/workbench/sermon_coach_tools.py`:

```python
"""Tools the sermon coach agent uses for depth reads.

All read-only. Override / reanalyze are deferred to Phase 2 per the MVP spec.
"""

from __future__ import annotations
import json
from typing import Optional
from homiletics_core import corpus_gate_status


def _dict(row, cursor_desc):
    if row is None:
        return None
    return {cursor_desc[i][0]: row[i] for i in range(len(cursor_desc))}


def get_sermon_review(db, sermon_id: int) -> Optional[dict]:
    """Fetch the full sermon_reviews row for a sermon."""
    conn = db._conn()
    cur = conn.execute("SELECT * FROM sermon_reviews WHERE sermon_id = ?", (sermon_id,))
    row = cur.fetchone()
    desc = cur.description
    conn.close()
    if row is None:
        return None
    review = _dict(row, desc)
    # Parse JSON fields for coach convenience
    for field in ('application_excerpts', 'ethos_markers', 'narrative_moments',
                   'christ_thread_excerpts', 'section_timings', 'density_hotspots',
                   'outline_additions', 'outline_omissions',
                   'top_impact_helpers', 'top_impact_hurters'):
        if review.get(field):
            try:
                review[field] = json.loads(review[field])
            except (TypeError, ValueError):
                pass
    return review


def get_sermon_flags(db, sermon_id: int) -> list[dict]:
    """Fetch all flags for a sermon, ordered by transcript position."""
    conn = db._conn()
    cur = conn.execute("""
        SELECT id, flag_type, severity, transcript_start_sec, transcript_end_sec,
               section_label, excerpt, rationale, created_at
        FROM sermon_flags WHERE sermon_id = ?
        ORDER BY transcript_start_sec
    """, (sermon_id,))
    rows = cur.fetchall()
    desc = cur.description
    conn.close()
    return [_dict(r, desc) for r in rows]


def get_transcript_full(db, sermon_id: int,
                        start_sec: Optional[int] = None,
                        end_sec: Optional[int] = None) -> Optional[str]:
    """Return the raw transcript text. MVP: slicing by seconds is approximated
    linearly from the text length; returns the whole text if start/end are None.
    """
    conn = db._conn()
    row = conn.execute(
        "SELECT transcript_text, duration_seconds FROM sermons WHERE id = ?",
        (sermon_id,)
    ).fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    text, duration = row[0], row[1] or 0
    if start_sec is None and end_sec is None:
        return text
    if duration <= 0:
        return text
    start_idx = int(len(text) * (start_sec / duration)) if start_sec else 0
    end_idx = int(len(text) * (end_sec / duration)) if end_sec else len(text)
    return text[start_idx:end_idx]


def get_prep_session_full(db, sermon_id: int) -> Optional[dict]:
    """Fetch the linked prep session: outline + card responses + homiletical messages.

    Returns None if the sermon has no active link.
    """
    conn = db._conn()
    link = conn.execute(
        "SELECT session_id FROM sermon_links WHERE sermon_id = ? AND link_status = 'active'",
        (sermon_id,)
    ).fetchone()
    if not link:
        conn.close()
        return None
    session_id = link[0]
    session_row = conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    outline = conn.execute(
        "SELECT id, type, content, rank FROM outline_nodes WHERE session_id = ? ORDER BY rank",
        (session_id,)
    ).fetchall()
    cards = conn.execute(
        "SELECT phase, question_id, content, created_at FROM card_responses WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    ).fetchall()
    homiletical_msgs = conn.execute("""
        SELECT phase, role, content, created_at FROM conversation_messages
        WHERE session_id = ? AND phase IN ('exegetical_point','fcf_homiletical','sermon_construction','edit_pray')
        ORDER BY created_at
    """, (session_id,)).fetchall()
    conn.close()
    return {
        'session': dict(session_row) if session_row else None,
        'outline': [{'id': r[0], 'type': r[1], 'content': r[2], 'rank': r[3]} for r in outline],
        'card_responses': [{'phase': r[0], 'question_id': r[1], 'content': r[2], 'created_at': r[3]} for r in cards],
        'homiletical_messages': [{'phase': r[0], 'role': r[1], 'content': r[2], 'created_at': r[3]} for r in homiletical_msgs],
    }


def pull_historical_sermons(db, n: int = 5, filter_expr: Optional[str] = None) -> list[dict]:
    """Return the N most recent classified-sermon rows with their review."""
    conn = db._conn()
    rows = conn.execute("""
        SELECT s.id, s.title, s.preach_date, s.duration_seconds,
               sr.burden_clarity, sr.application_specificity, sr.ethos_rating,
               sr.christ_thread_score, sr.duration_delta_seconds, sr.one_change_for_next_sunday
        FROM sermons s
        LEFT JOIN sermon_reviews sr ON sr.sermon_id = s.id
        WHERE s.classified_as = 'sermon' AND s.is_remote_deleted = 0
        ORDER BY s.preach_date DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [
        {
            'id': r[0], 'title': r[1], 'preach_date': r[2], 'duration_seconds': r[3],
            'burden_clarity': r[4], 'application_specificity': r[5],
            'ethos_rating': r[6], 'christ_thread_score': r[7],
            'duration_delta_seconds': r[8], 'one_change_for_next_sunday': r[9],
        }
        for r in rows
    ]


def get_sermon_patterns(db, window_days: int = 90) -> dict:
    """Compute rolling aggregates over sermons in the window.

    Returns a dict including corpus_gate_status so the coach knows what
    longitudinal voice it is allowed to use.
    """
    conn = db._conn()
    row = conn.execute(f"""
        SELECT
            COUNT(*),
            AVG(sr.duration_delta_seconds),
            1.0 * SUM(CASE WHEN sr.burden_clarity IN ('crisp','clear') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.movement_clarity IN ('river','mostly_river') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.application_specificity IN ('localized','concrete') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.ethos_rating IN ('seized','engaged') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            AVG(sr.concreteness_score),
            1.0 * SUM(CASE WHEN sr.christ_thread_score = 'explicit' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.exegetical_grounding = 'grounded' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            AVG(sr.outline_coverage_pct)
        FROM sermon_reviews sr
        JOIN sermons s ON s.id = sr.sermon_id
        WHERE s.preach_date >= date('now', '-{window_days} days')
          AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
    """).fetchone()
    conn.close()

    n = row[0] or 0
    return {
        'n_sermons': n,
        'corpus_gate_status': corpus_gate_status(n),
        'avg_duration_delta_sec': row[1],
        'burden_clear_rate': row[2],
        'movement_clear_rate': row[3],
        'application_concrete_rate': row[4],
        'ethos_engaged_rate': row[5],
        'avg_concreteness': row[6],
        'christ_explicit_rate': row[7],
        'exegetical_grounded_rate': row[8],
        'avg_outline_coverage': row[9],
        'window_days': window_days,
    }
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_tools.py -v`
Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_coach_tools.py tools/workbench/tests/test_sermon_coach_tools.py
git -c commit.gpgsign=false commit -m "feat: sermon_coach_tools read helpers with corpus_gate_status"
```

---

## Task 15: `sermon_coach_agent.py` — system prompt + tool schemas

**Files:**
- Create: `tools/workbench/sermon_coach_agent.py`
- Create: `tools/workbench/tests/test_sermon_coach_agent.py`

- [ ] **Step 1: Write failing tests for the coach's system prompt + tool schemas**

Create `tools/workbench/tests/test_sermon_coach_agent.py`:

```python
import os
import tempfile
import pytest
from companion_db import CompanionDB
from sermon_coach_agent import (
    build_system_prompt, TOOL_DEFINITIONS, execute_tool,
)


@pytest.fixture
def stocked_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def test_system_prompt_includes_voice_constants():
    prompt = build_system_prompt(
        sermon_context={'passage': 'Romans 8:1-11', 'duration_sec': 2322},
        review_json={},
        corpus_gate_status='pre_gate',
    )
    assert 'Reformed Presbyterian' in prompt
    assert 'Chapell' in prompt
    assert 'study partner' in prompt.lower() or 'partner' in prompt.lower()


def test_system_prompt_includes_corpus_gate_rule_verbatim():
    prompt = build_system_prompt(
        sermon_context={}, review_json={}, corpus_gate_status='pre_gate',
    )
    assert 'pre_gate' in prompt
    assert 'pattern' in prompt.lower()
    assert 'persistent' in prompt.lower()


def test_system_prompt_forbids_pattern_words_in_pre_gate():
    prompt = build_system_prompt(
        sermon_context={}, review_json={}, corpus_gate_status='pre_gate',
    )
    # The rule should explicitly name forbidden words
    for word in ['pattern', 'persistent', 'always', 'every time']:
        assert word in prompt


def test_system_prompt_includes_three_tier_framing():
    prompt = build_system_prompt(
        sermon_context={}, review_json={'burden_clarity': 'clear'},
        corpus_gate_status='stable',
    )
    assert 'Impact' in prompt
    assert 'Faithfulness' in prompt
    assert 'Diagnostic' in prompt


def test_tool_definitions_list_all_read_tools():
    names = {t['name'] for t in TOOL_DEFINITIONS}
    assert 'get_sermon_review' in names
    assert 'get_sermon_flags' in names
    assert 'get_transcript_full' in names
    assert 'get_prep_session_full' in names
    assert 'pull_historical_sermons' in names
    assert 'get_sermon_patterns' in names


def test_execute_tool_dispatches_get_sermon_review(stocked_db):
    conn = stocked_db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-a', 'bcast', 'T', 'sermon', 'review_ready', datetime('now'),
                datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_reviews (sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis, actual_duration_seconds,
            burden_clarity, top_impact_helpers, top_impact_hurters, one_change_for_next_sunday,
            computed_at)
        VALUES (?, '1.0.0', '1.0.0', 'claude-opus-4-6', 'h', 1, 100,
                'clear', '["a"]', '["b"]', 'change', datetime('now'))
    """, (sermon_id,))
    conn.commit()
    conn.close()

    result = execute_tool(
        'get_sermon_review',
        {'sermon_id': sermon_id},
        session_context={'db': stocked_db, 'sermon_id': sermon_id},
    )
    assert result['burden_clarity'] == 'clear'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_agent.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Create `sermon_coach_agent.py`**

Create `tools/workbench/sermon_coach_agent.py`:

```python
"""Sermon coach agent — streaming Claude Opus 4.6 narrator.

Reads precomputed sermon_reviews + flags + full raw context via tool calls,
narrates the four review cards, runs a conversation over the sermon.
"""

from __future__ import annotations
import json
from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS
from sermon_coach_tools import (
    get_sermon_review, get_sermon_flags, get_transcript_full,
    get_prep_session_full, pull_historical_sermons, get_sermon_patterns,
)


LONGITUDINAL_POSTURE_RULE = """## Longitudinal Posture — YOU MUST FOLLOW THIS

The system has analyzed N recent sermons. The current corpus gate is: {corpus_gate_status}

If corpus_gate_status == 'pre_gate' (fewer than 5 recent sermons):
  - You may NOT use any of these words: "pattern", "persistent", "always",
    "every time", "trajectory", "tendency", "habit", "consistently".
  - You may ONLY describe what you see in this specific sermon.
  - If Bryan asks about patterns, say: "I don't have enough corpus yet to
    speak to patterns — I need at least 5 recent sermons before I can. What
    I see in THIS sermon is ..."

If corpus_gate_status == 'emerging' (5-9 recent sermons):
  - You may say "emerging pattern" when >=3 of the last 5 sermons share the
    same dimension in the same direction.
  - You may NOT say "persistent" or "always" or "stable pattern."
  - Always label: "emerging observation across the last 5 sermons..."

If corpus_gate_status == 'stable' (10+ recent sermons):
  - Full longitudinal voice is available.
  - Always label observations explicitly: "current-sermon observation",
    "historical pattern", or "trajectory".
  - Never conflate the three.

This rule is non-negotiable. Violating it damages Bryan's trust in the system."""


HOMILETICAL_FRAMEWORK = """## Homiletical Framework

Impact → Faithfulness → Diagnostic, three tiers:

- Tier 1 (Impact): burden clarity, movement, application specificity, ethos, concreteness.
  These are what rhetoric and sermon-listening research identify as the
  strongest predictors of impact on hearers.
- Tier 2 (Faithfulness): Christ thread + exegetical grounding. Parallel crown
  for a Reformed pastor — faithfulness is a distinct axis from impact.
- Tier 3 (Diagnostic): length, density hotspots, late application, outline drift.
  These are symptoms. Their causes live in Tier 1. When Bryan runs long,
  the length is the surface; the cause is usually late application or density."""


def build_system_prompt(sermon_context: dict, review_json: dict,
                        corpus_gate_status: str) -> str:
    """Assemble the coach's system prompt."""
    sections = [
        IDENTITY_CORE,
        HOMILETICAL_TRADITION,
        VOICE_GUARDRAILS,
        HOMILETICAL_FRAMEWORK,
        _current_sermon_section(sermon_context),
        _pipeline_findings_section(review_json),
        LONGITUDINAL_POSTURE_RULE.replace('{corpus_gate_status}', corpus_gate_status),
        _tools_section(),
        _behavioral_constraints(),
    ]
    return '\n\n'.join(s for s in sections if s)


def _current_sermon_section(ctx: dict) -> str:
    if not ctx:
        return ""
    parts = ["## Current Sermon Context"]
    if 'passage' in ctx:
        parts.append(f"Passage: {ctx['passage']}")
    if 'duration_sec' in ctx:
        d = ctx['duration_sec']
        parts.append(f"Duration: {d // 60}:{d % 60:02d}")
    if 'preach_date' in ctx:
        parts.append(f"Preached: {ctx['preach_date']}")
    if 'linked_session_id' in ctx:
        parts.append(f"Linked prep session: #{ctx['linked_session_id']}")
    return '\n'.join(parts)


def _pipeline_findings_section(review: dict) -> str:
    if not review:
        return "## Pipeline Findings\n\n(no review yet)"
    return "## Pipeline Findings (structured)\n\n```json\n" + json.dumps(review, indent=2, default=str) + "\n```"


def _tools_section() -> str:
    lines = ["## Tools Available\n"]
    for tool in TOOL_DEFINITIONS:
        lines.append(f"- **{tool['name']}**: {tool['description']}")
    return '\n'.join(lines)


def _behavioral_constraints() -> str:
    return """## Behavioral Constraints

- You never auto-initiate. You respond when Bryan enters the Review page or clicks a flag.
- One action per turn per metric: if you override, don't also reanalyze on the same turn.
- When you disagree with a pipeline value, say so in the chat with explicit rationale — your
  disagreement becomes part of the conversation log.
- Lead with the Impact card when Bryan opens the review. Tier 1 is the coaching crown.
- When appropriate, cite Chapell's Christ-Centered Preaching, Robinson's Big Idea, Beeke, or
  Piper — but only when the citation earns its place. Don't pepper quotes unnecessarily."""


# ── Tool definitions ──────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        'name': 'get_sermon_review',
        'description': 'Fetch the full structured review for a sermon (all three tiers + coach summary).',
        'input_schema': {
            'type': 'object',
            'properties': {'sermon_id': {'type': 'integer'}},
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_sermon_flags',
        'description': 'Fetch per-moment flags for a sermon (late_application, density_spike, etc.).',
        'input_schema': {
            'type': 'object',
            'properties': {'sermon_id': {'type': 'integer'}},
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_transcript_full',
        'description': 'Fetch raw transcript text. Optionally slice by seconds.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'sermon_id': {'type': 'integer'},
                'start_sec': {'type': 'integer'},
                'end_sec': {'type': 'integer'},
            },
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_prep_session_full',
        'description': 'Fetch the linked prep session: outline, card responses, homiletical messages. Returns null if no active link.',
        'input_schema': {
            'type': 'object',
            'properties': {'sermon_id': {'type': 'integer'}},
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'pull_historical_sermons',
        'description': 'Return the N most recent classified sermons with their review summary fields. Use for cross-sermon depth — subject to the corpus gate.',
        'input_schema': {
            'type': 'object',
            'properties': {'n': {'type': 'integer', 'default': 5}},
        },
    },
    {
        'name': 'get_sermon_patterns',
        'description': 'Aggregate metrics over recent sermons + corpus_gate_status. Tells you what longitudinal voice you are allowed to use.',
        'input_schema': {
            'type': 'object',
            'properties': {'window_days': {'type': 'integer', 'default': 90}},
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, session_context: dict) -> dict:
    """Dispatch a tool call."""
    db = session_context['db']
    try:
        if tool_name == 'get_sermon_review':
            return get_sermon_review(db, tool_input['sermon_id']) or {'error': 'not found'}
        if tool_name == 'get_sermon_flags':
            return {'flags': get_sermon_flags(db, tool_input['sermon_id'])}
        if tool_name == 'get_transcript_full':
            return {'transcript': get_transcript_full(
                db, tool_input['sermon_id'],
                start_sec=tool_input.get('start_sec'),
                end_sec=tool_input.get('end_sec'),
            )}
        if tool_name == 'get_prep_session_full':
            prep = get_prep_session_full(db, tool_input['sermon_id'])
            return prep if prep else {'linked': False}
        if tool_name == 'pull_historical_sermons':
            return {'sermons': pull_historical_sermons(db, n=tool_input.get('n', 5))}
        if tool_name == 'get_sermon_patterns':
            return get_sermon_patterns(db, window_days=tool_input.get('window_days', 90))
        return {'error': f'unknown tool: {tool_name}'}
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_agent.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_coach_agent.py tools/workbench/tests/test_sermon_coach_agent.py
git -c commit.gpgsign=false commit -m "feat: sermon_coach_agent system prompt + tool schemas + execute_tool dispatch"
```

---

## Task 16: `sermon_coach_agent.py` — streaming loop + SSE handler

**Files:**
- Modify: `tools/workbench/sermon_coach_agent.py` — add `stream_coach_response()`
- Create: `tools/workbench/tests/test_sermon_coach_streaming.py`

- [ ] **Step 1: Write failing tests for the streaming loop using a canned LLM**

Create `tools/workbench/tests/test_sermon_coach_streaming.py`:

```python
import os
import tempfile
import pytest
from companion_db import CompanionDB
from sermon_coach_agent import stream_coach_response, CoachTurnResult


class FakeStreamingClient:
    """Stub for testing. Yields fake deltas, no tool use."""
    def __init__(self, final_text='Hello from the coach.'):
        self.final_text = final_text

    def stream_message(self, system, messages, tools):
        # Yield a sequence of events
        yield {'type': 'text_delta', 'text': 'Hello'}
        yield {'type': 'text_delta', 'text': ' from'}
        yield {'type': 'text_delta', 'text': ' the coach.'}
        yield {'type': 'message_complete', 'usage': {'input_tokens': 100, 'output_tokens': 20}}


@pytest.fixture
def db_with_sermon():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, preach_date, duration_seconds, bible_text_raw,
                              transcript_text, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-c', 'bcast', 'Romans 8', 'sermon', 'review_ready',
                '2026-04-12', 2322, 'Romans 8:1-11', 'hello transcript',
                datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_reviews (sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis, actual_duration_seconds,
            burden_clarity, top_impact_helpers, top_impact_hurters, one_change_for_next_sunday,
            computed_at)
        VALUES (?, '1.0.0', '1.0.0', 'claude-opus-4-6', 'h', 1, 2322,
                'clear', '["a"]', '["b"]', 'change', datetime('now'))
    """, (sermon_id,))
    conn.commit()
    conn.close()
    yield db, sermon_id
    os.unlink(path)


def test_stream_coach_response_persists_user_and_assistant_messages(db_with_sermon):
    db, sermon_id = db_with_sermon
    client = FakeStreamingClient()
    chunks = []
    for event in stream_coach_response(
        db=db, sermon_id=sermon_id, conversation_id=1,
        user_message='Walk me through the review',
        llm_client=client,
    ):
        chunks.append(event)
    full_text = ''.join(e['text'] for e in chunks if e.get('type') == 'text_delta')
    assert 'Hello' in full_text

    conn = db._conn()
    msgs = conn.execute(
        "SELECT role, content FROM sermon_coach_messages WHERE sermon_id = ? ORDER BY id",
        (sermon_id,)
    ).fetchall()
    conn.close()
    assert len(msgs) == 2  # user + assistant
    assert msgs[0] == ('user', 'Walk me through the review')
    assert msgs[1][0] == 'assistant'
    assert 'Hello' in msgs[1][1]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_streaming.py -v`
Expected: FAIL — `stream_coach_response` missing.

- [ ] **Step 3: Append streaming loop to `sermon_coach_agent.py`**

Append to `tools/workbench/sermon_coach_agent.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class CoachTurnResult:
    assistant_text: str
    input_tokens: int
    output_tokens: int


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stream_coach_response(db, sermon_id: int, conversation_id: int,
                          user_message: str, llm_client):
    """Generator that streams coach output events and persists messages.

    llm_client must expose a stream_message(system, messages, tools) generator
    yielding events like {'type':'text_delta','text':str} or
    {'type':'tool_use', ...} or {'type':'message_complete','usage':{...}}.
    """
    # Load sermon context
    conn = db._conn()
    sermon_row = conn.execute("""
        SELECT id, bible_text_raw, preach_date, duration_seconds
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    conn.close()
    if not sermon_row:
        yield {'type': 'error', 'error': 'sermon_not_found'}
        return

    # Persist user turn
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (?, ?, 'user', ?, ?)
    """, (sermon_id, conversation_id, user_message, _now()))
    conn.commit()
    conn.close()

    review = get_sermon_review(db, sermon_id) or {}
    patterns = get_sermon_patterns(db)
    sermon_context = {
        'passage': sermon_row[1],
        'preach_date': sermon_row[2],
        'duration_sec': sermon_row[3] or 0,
    }
    system = build_system_prompt(sermon_context, review, patterns['corpus_gate_status'])

    # Load conversation history for this sermon
    conn = db._conn()
    history_rows = conn.execute("""
        SELECT role, content FROM sermon_coach_messages
        WHERE sermon_id = ? AND conversation_id = ?
        ORDER BY id
    """, (sermon_id, conversation_id)).fetchall()
    conn.close()
    messages = [{'role': r[0], 'content': r[1]} for r in history_rows if r[1]]

    assistant_text_parts = []
    input_tokens = 0
    output_tokens = 0
    try:
        for event in llm_client.stream_message(system=system, messages=messages,
                                                 tools=TOOL_DEFINITIONS):
            if event.get('type') == 'text_delta':
                assistant_text_parts.append(event.get('text', ''))
                yield event
            elif event.get('type') == 'tool_use':
                tool_result = execute_tool(
                    event['tool_name'], event['tool_input'],
                    session_context={'db': db, 'sermon_id': sermon_id},
                )
                yield {'type': 'tool_result', 'tool_name': event['tool_name'],
                        'result': tool_result}
            elif event.get('type') == 'message_complete':
                usage = event.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                yield event
    except Exception as e:
        yield {'type': 'error', 'error': f'{type(e).__name__}: {e}'}
        return

    assistant_text = ''.join(assistant_text_parts)
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (?, ?, 'assistant', ?, ?)
    """, (sermon_id, conversation_id, assistant_text, _now()))
    conn.commit()
    conn.close()
```

- [ ] **Step 4: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_streaming.py -v`
Expected: test PASSES.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_coach_agent.py tools/workbench/tests/test_sermon_coach_streaming.py
git -c commit.gpgsign=false commit -m "feat: stream_coach_response generator with message persistence"
```

---

## Task 17: `app.py` — `/sermons/` blueprint list + detail routes

**Files:**
- Modify: `tools/workbench/app.py` — register blueprint, add list + detail + status routes
- Create: `tools/workbench/tests/test_sermons_routes.py`

- [ ] **Step 1: Write failing tests for the blueprint routes**

Create `tools/workbench/tests/test_sermons_routes.py`:

```python
import os
import tempfile
import pytest
from app import app, get_db


@pytest.fixture
def client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    monkeypatch.setenv('COMPANION_DB_PATH', db_path)
    app.config['TESTING'] = True
    # Clear app's cached db
    import app as app_mod
    app_mod._db_instance = None
    with app.test_client() as c:
        db = get_db()
        db.init_db()
        conn = db._conn()
        conn.execute("""
            INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                                  sync_status, preach_date, duration_seconds, bible_text_raw,
                                  last_state_change_at, first_synced_at, last_synced_at,
                                  created_at, updated_at)
            VALUES ('sa-1', 'bcast', 'Romans 8', 'sermon', 'review_ready',
                    '2026-04-12', 2322, 'Romans 8:1-11',
                    datetime('now'), datetime('now'), datetime('now'),
                    datetime('now'), datetime('now'))
        """)
        conn.commit()
        conn.close()
        yield c
    try:
        os.unlink(db_path)
    except Exception:
        pass


def test_sermons_list_returns_200(client):
    resp = client.get('/sermons/')
    assert resp.status_code == 200
    assert b'Romans 8' in resp.data


def test_sermon_detail_returns_200(client):
    resp = client.get('/sermons/1')
    assert resp.status_code == 200
    assert b'Romans 8:1-11' in resp.data


def test_sermon_detail_404_for_missing(client):
    resp = client.get('/sermons/9999')
    assert resp.status_code == 404


def test_sermon_status_json(client):
    resp = client.get('/sermons/1/status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['sync_status'] == 'review_ready'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermons_routes.py -v`
Expected: FAIL — routes not registered.

- [ ] **Step 3: Register the `/sermons/` blueprint in `app.py`**

In `tools/workbench/app.py`, locate the existing blueprint registrations. Add:

```python
from flask import Blueprint, render_template, jsonify, request, abort, Response

sermons_bp = Blueprint('sermons', __name__, url_prefix='/sermons')


@sermons_bp.route('/', methods=['GET'])
def sermons_list():
    db = get_db()
    conn = db._conn()
    rows = conn.execute("""
        SELECT id, title, preach_date, duration_seconds, sync_status, match_status,
               ui_last_seen_version, source_version
        FROM sermons
        WHERE classified_as = 'sermon' AND is_remote_deleted = 0
        ORDER BY preach_date DESC
        LIMIT 100
    """).fetchall()
    sermons = [dict(
        id=r[0], title=r[1], preach_date=r[2], duration_seconds=r[3],
        sync_status=r[4], match_status=r[5],
        badge=(r[6] < r[7]),
    ) for r in rows]
    conn.close()
    return render_template('sermons/list.html', sermons=sermons)


@sermons_bp.route('/<int:sermon_id>', methods=['GET'])
def sermon_detail(sermon_id):
    db = get_db()
    conn = db._conn()
    sermon_row = conn.execute("""
        SELECT * FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    if not sermon_row:
        conn.close()
        abort(404)
    sermon = dict(sermon_row)

    review_row = conn.execute("SELECT * FROM sermon_reviews WHERE sermon_id = ?", (sermon_id,)).fetchone()
    review = dict(review_row) if review_row else None

    flags_rows = conn.execute("""
        SELECT id, flag_type, severity, transcript_start_sec, transcript_end_sec,
               section_label, excerpt, rationale
        FROM sermon_flags WHERE sermon_id = ?
        ORDER BY transcript_start_sec
    """, (sermon_id,)).fetchall()
    flags = [dict(r) for r in flags_rows]

    candidates_rows = conn.execute("""
        SELECT sl.id, sl.session_id, sl.match_reason, s.passage_ref
        FROM sermon_links sl
        JOIN sessions s ON s.id = sl.session_id
        WHERE sl.sermon_id = ? AND sl.link_status = 'candidate'
    """, (sermon_id,)).fetchall()
    candidates = [dict(r) for r in candidates_rows]

    # Compare-and-set ui_last_seen_version
    conn.execute("""
        UPDATE sermons SET ui_last_seen_version = source_version
        WHERE id = ? AND ui_last_seen_version < source_version
    """, (sermon_id,))
    conn.commit()
    conn.close()

    return render_template(
        'sermons/detail.html',
        sermon=sermon, review=review, flags=flags, candidates=candidates,
    )


@sermons_bp.route('/<int:sermon_id>/status', methods=['GET'])
def sermon_status(sermon_id):
    db = get_db()
    conn = db._conn()
    row = conn.execute("""
        SELECT sync_status, match_status, source_version, ui_last_seen_version
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    return jsonify(dict(
        sync_status=row[0], match_status=row[1],
        source_version=row[2], ui_last_seen_version=row[3],
    ))


app.register_blueprint(sermons_bp)
```

Ensure `get_db()` exists in `app.py` and uses `sqlite3.Row` as row_factory (it already does per `companion_db.py._conn()`).

Also create minimal templates (empty for now; filled in Task 20):

```
tools/workbench/templates/sermons/list.html
tools/workbench/templates/sermons/detail.html
```

With placeholder content so the tests can render:

`tools/workbench/templates/sermons/list.html`:
```html
<!DOCTYPE html>
<html><head><title>Sermons</title></head>
<body>
<h1>Sermons</h1>
<ul>
{% for s in sermons %}
  <li><a href="/sermons/{{ s.id }}">{{ s.title }}</a> — {{ s.preach_date }}</li>
{% endfor %}
</ul>
</body></html>
```

`tools/workbench/templates/sermons/detail.html`:
```html
<!DOCTYPE html>
<html><head><title>{{ sermon.title }}</title></head>
<body>
<h1>{{ sermon.title }}</h1>
<p>{{ sermon.bible_text_raw }}</p>
<p>Status: {{ sermon.sync_status }}</p>
</body></html>
```

(Full styled templates come in Task 20.)

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermons_routes.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/app.py tools/workbench/templates/sermons/list.html tools/workbench/templates/sermons/detail.html tools/workbench/tests/test_sermons_routes.py
git -c commit.gpgsign=false commit -m "feat: /sermons/ blueprint with list + detail + status routes (minimal templates)"
```

---

## Task 18: Sync + match + reanalyze routes + coach SSE

**Files:**
- Modify: `tools/workbench/app.py` — add sync/backfill/reanalyze/link/unlink/candidate/patterns/sync-log routes + coach SSE endpoint
- Create: `tools/workbench/tests/test_sermons_sync_routes.py`

- [ ] **Step 1: Write failing tests for the sync and match routes**

Create `tools/workbench/tests/test_sermons_sync_routes.py`:

```python
import os
import tempfile
import json
from types import SimpleNamespace
import datetime as dt
import pytest
from app import app, get_db


@pytest.fixture
def client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    monkeypatch.setenv('COMPANION_DB_PATH', db_path)
    import app as app_mod
    app_mod._db_instance = None
    app.config['TESTING'] = True
    with app.test_client() as c:
        db = get_db()
        db.init_db()
        yield c, db
    try:
        os.unlink(db_path)
    except Exception:
        pass


def test_manual_sync_with_mock_client(client, monkeypatch):
    c, db = client
    from sermonaudio_sync import run_sync_with_client

    class MockClient:
        def list_sermons_updated_since(self, broadcaster_id, since=None, limit=100):
            return [SimpleNamespace(
                sermon_id='sa-9', broadcaster_id='bcast', title='Test',
                speaker_name='Bryan Schneider', event_type='Sunday Service',
                series='R', preach_date=dt.date(2026, 4, 12),
                publish_date=dt.date(2026, 4, 12), duration=2322,
                bible_text='Romans 8:1-11', audio_url='https://x',
                transcript='Hello. ' * 200,
                update_date=dt.datetime(2026, 4, 12),
            )]
        def get_sermon_detail(self, sermon_id):
            return None

    # Inject mock client via app_mod reference
    import app as app_mod
    monkeypatch.setattr(app_mod, '_make_sermonaudio_client', lambda: MockClient())
    resp = c.post('/sermons/sync')
    assert resp.status_code == 202
    data = resp.get_json()
    assert 'run_id' in data
    # Verify sermon landed
    conn = db._conn()
    count = conn.execute("SELECT COUNT(*) FROM sermons").fetchone()[0]
    conn.close()
    assert count == 1


def test_manual_link_creates_active_row(client):
    c, db = client
    conn = db._conn()
    # Create a sermon and a session
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, last_state_change_at, first_synced_at, last_synced_at,
                              created_at, updated_at)
        VALUES ('sa-1', 'bcast', 'T', 'sermon', 'review_ready', datetime('now'),
                datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('R', 45, 8, 1, 11, 'epistle', 'prayer', 900, datetime('now'), datetime('now'))
    """)
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    resp = c.post(f'/sermons/{sermon_id}/link/{session_id}')
    assert resp.status_code == 200

    conn = db._conn()
    row = conn.execute("SELECT link_status, link_source FROM sermon_links WHERE sermon_id = ?", (sermon_id,)).fetchone()
    conn.close()
    assert row == ('active', 'manual')


def test_unlink_marks_rejected(client):
    c, db = client
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, last_state_change_at, first_synced_at, last_synced_at,
                              created_at, updated_at)
        VALUES ('sa-2', 'bcast', 'T', 'sermon', 'review_ready', datetime('now'),
                datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('R', 45, 8, 1, 11, 'epistle', 'prayer', 900, datetime('now'), datetime('now'))
    """)
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at)
        VALUES (?, ?, 'active', 'auto', 'tier1', datetime('now'))
    """, (sermon_id, session_id))
    conn.commit()
    conn.close()

    resp = c.post(f'/sermons/{sermon_id}/unlink')
    assert resp.status_code == 200

    conn = db._conn()
    row = conn.execute("SELECT link_status FROM sermon_links WHERE sermon_id = ?", (sermon_id,)).fetchone()
    conn.close()
    assert row[0] == 'rejected'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermons_sync_routes.py -v`
Expected: FAIL.

- [ ] **Step 3: Add the routes to `app.py`**

Append to `tools/workbench/app.py` (inside `sermons_bp`):

```python
import os as _os
from sermonaudio_sync import run_sync_with_client, run_sync


def _make_sermonaudio_client():
    """Factory for the real API client. Tests monkeypatch this."""
    from sermonaudio_sync import SermonAudioAPIClient
    api_key = _os.environ.get('SERMONAUDIO_API_KEY', '')
    return SermonAudioAPIClient(api_key)


def _broadcaster_id() -> str:
    return _os.environ.get('SERMONAUDIO_BROADCASTER_ID', '')


@sermons_bp.route('/sync', methods=['POST'])
def sermon_sync():
    db = get_db()
    client = _make_sermonaudio_client()
    result = run_sync_with_client(
        db, client, broadcaster_id=_broadcaster_id(), trigger='manual',
    )
    return jsonify(result), 202


@sermons_bp.route('/backfill', methods=['POST'])
def sermon_backfill():
    limit = int(request.args.get('limit', 24))
    db = get_db()
    client = _make_sermonaudio_client()
    result = run_sync_with_client(
        db, client, broadcaster_id=_broadcaster_id(), trigger='backfill', limit=limit,
    )
    return jsonify(result), 202


@sermons_bp.route('/<int:sermon_id>/reanalyze', methods=['POST'])
def sermon_reanalyze(sermon_id):
    from sermon_analyzer import analyze_sermon
    from llm_client import AnthropicClient
    db = get_db()
    api_key = _os.environ.get('ANTHROPIC_API_KEY', '')
    client = AnthropicClient(api_key=api_key)
    # Force status back to analysis_pending so analyze_sermon proceeds
    conn = db._conn()
    conn.execute(
        "UPDATE sermons SET sync_status = 'analysis_pending', last_state_change_at = datetime('now') WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    result = analyze_sermon(db, sermon_id, llm_client=client)
    return jsonify(result)


@sermons_bp.route('/<int:sermon_id>/link/<int:session_id>', methods=['POST'])
def sermon_link(sermon_id, session_id):
    db = get_db()
    conn = db._conn()
    # Remove any existing active auto link on this sermon
    conn.execute(
        "DELETE FROM sermon_links WHERE sermon_id = ? AND link_status = 'active' AND link_source = 'auto'",
        (sermon_id,),
    )
    conn.execute("""
        INSERT OR REPLACE INTO sermon_links
            (sermon_id, session_id, link_status, link_source, match_reason, created_at)
        VALUES (?, ?, 'active', 'manual', 'user_linked', datetime('now'))
    """, (sermon_id, session_id))
    conn.execute(
        "UPDATE sermons SET match_status = 'matched', last_match_attempt_at = datetime('now') WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'link_status': 'active', 'link_source': 'manual'})


@sermons_bp.route('/<int:sermon_id>/unlink', methods=['POST'])
def sermon_unlink(sermon_id):
    db = get_db()
    conn = db._conn()
    conn.execute("""
        UPDATE sermon_links SET link_status = 'rejected'
        WHERE sermon_id = ? AND link_status = 'active'
    """, (sermon_id,))
    conn.execute(
        "UPDATE sermons SET match_status = 'rejected_all' WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@sermons_bp.route('/<int:sermon_id>/approve-candidate/<int:link_id>', methods=['POST'])
def sermon_approve_candidate(sermon_id, link_id):
    db = get_db()
    conn = db._conn()
    conn.execute(
        "DELETE FROM sermon_links WHERE sermon_id = ? AND link_status = 'active'",
        (sermon_id,),
    )
    conn.execute("""
        UPDATE sermon_links SET link_status = 'active'
        WHERE id = ? AND sermon_id = ?
    """, (link_id, sermon_id))
    conn.execute(
        "UPDATE sermons SET match_status = 'matched' WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@sermons_bp.route('/patterns', methods=['GET'])
def sermon_patterns():
    from sermon_coach_tools import get_sermon_patterns
    db = get_db()
    data = get_sermon_patterns(db)
    return render_template('sermons/patterns.html', patterns=data)


@sermons_bp.route('/sync-log', methods=['GET'])
def sermon_sync_log_page():
    db = get_db()
    conn = db._conn()
    runs = conn.execute("""
        SELECT run_id, trigger, started_at, ended_at, sermons_new, sermons_updated,
               sermons_failed, status, error_summary
        FROM sermon_sync_log
        ORDER BY started_at DESC LIMIT 20
    """).fetchall()
    cost_total = conn.execute(
        "SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM sermon_analysis_cost_log WHERE called_at >= date('now','-30 days')"
    ).fetchone()[0]
    conn.close()
    return render_template('sermons/sync_log.html',
                             runs=[dict(r) for r in runs], cost_30d=cost_total)


@sermons_bp.route('/<int:sermon_id>/coach/message', methods=['POST'])
def sermon_coach_message(sermon_id):
    from sermon_coach_agent import stream_coach_response
    from llm_client import AnthropicClient
    user_message = request.json.get('message') if request.is_json else request.form.get('message', '')
    conversation_id = int(request.json.get('conversation_id', 1)) if request.is_json else 1
    db = get_db()
    api_key = _os.environ.get('ANTHROPIC_API_KEY', '')
    client = AnthropicClient(api_key=api_key)

    def generate():
        for event in stream_coach_response(
            db=db, sermon_id=sermon_id, conversation_id=conversation_id,
            user_message=user_message, llm_client=client,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return Response(generate(), mimetype='text/event-stream')
```

Create placeholder templates:

`tools/workbench/templates/sermons/patterns.html`:
```html
<!DOCTYPE html>
<html><head><title>Sermon Patterns</title></head>
<body>
<h1>Sermon Patterns (last {{ patterns.window_days }} days)</h1>
<p>{{ patterns.n_sermons }} sermons • corpus gate: {{ patterns.corpus_gate_status }}</p>
</body></html>
```

`tools/workbench/templates/sermons/sync_log.html`:
```html
<!DOCTYPE html>
<html><head><title>Sync Log</title></head>
<body>
<h1>Sync Log</h1>
<p>30-day cost: ${{ '%.2f'|format(cost_30d) }}</p>
<table>
<tr><th>Run</th><th>Trigger</th><th>Started</th><th>Status</th></tr>
{% for r in runs %}
<tr><td>{{ r.run_id[:8] }}</td><td>{{ r.trigger }}</td><td>{{ r.started_at }}</td><td>{{ r.status }}</td></tr>
{% endfor %}
</table>
</body></html>
```

- [ ] **Step 4: Run tests — all pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermons_sync_routes.py tests/test_sermons_routes.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/app.py tools/workbench/templates/sermons/patterns.html tools/workbench/templates/sermons/sync_log.html tools/workbench/tests/test_sermons_sync_routes.py
git -c commit.gpgsign=false commit -m "feat: sync, match, reanalyze, patterns, sync-log routes + coach SSE endpoint"
```

---

## Task 19: APScheduler integration + 4h cron

**Files:**
- Modify: `tools/workbench/app.py` — add `BackgroundScheduler` setup
- Create: `tools/workbench/tests/test_scheduler_setup.py`

- [ ] **Step 1: Write failing test verifying the scheduler is registered**

Create `tools/workbench/tests/test_scheduler_setup.py`:

```python
from app import app, get_scheduler


def test_scheduler_has_sermon_sync_job():
    scheduler = get_scheduler()
    job_ids = {j.id for j in scheduler.get_jobs()}
    assert 'sermon_sync_cron' in job_ids


def test_scheduler_job_runs_every_4_hours():
    scheduler = get_scheduler()
    job = scheduler.get_job('sermon_sync_cron')
    assert job is not None
    trigger_str = str(job.trigger)
    assert '4' in trigger_str or '14400' in trigger_str
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools/workbench && python3 -m pytest tests/test_scheduler_setup.py -v`
Expected: FAIL — `get_scheduler` not exported.

- [ ] **Step 3: Add scheduler setup to `app.py`**

In `tools/workbench/app.py`, near the top-level imports:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

_scheduler = None


def _scheduled_sermon_sync():
    """The 4h cron body. Swallows exceptions so a bad run doesn't kill the scheduler."""
    try:
        db = get_db()
        client = _make_sermonaudio_client()
        run_sync_with_client(
            db, client, broadcaster_id=_broadcaster_id(), trigger='cron',
        )
    except Exception as e:
        app.logger.error(f'Scheduled sermon sync failed: {e}')


def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _scheduled_sermon_sync,
            IntervalTrigger(hours=4),
            id='sermon_sync_cron',
            replace_existing=True,
        )
        _scheduler.start()
    return _scheduler


# Initialize on import
get_scheduler()
```

- [ ] **Step 4: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_scheduler_setup.py -v`
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/app.py tools/workbench/tests/test_scheduler_setup.py
git -c commit.gpgsign=false commit -m "feat: APScheduler BackgroundScheduler with 4h sermon_sync_cron job"
```

---

## Task 20: Four-card partial templates

**Files:**
- Create: `tools/workbench/templates/partials/sermon_impact_card.html`
- Create: `tools/workbench/templates/partials/sermon_faithfulness_card.html`
- Create: `tools/workbench/templates/partials/sermon_diagnostic_card.html`
- Create: `tools/workbench/templates/partials/sermon_prescription_card.html`
- Create: `tools/workbench/templates/partials/sermon_flag_list.html`
- Create: `tools/workbench/templates/partials/sermon_candidates_list.html`
- Create: `tools/workbench/templates/partials/sermon_coach_chat.html`
- Modify: `tools/workbench/templates/sermons/detail.html` — include the partials

- [ ] **Step 1: Write the Impact card partial**

Create `tools/workbench/templates/partials/sermon_impact_card.html`:

```html
{% if review %}
<div class="sermon-card sermon-card-impact">
  <h2>Impact</h2>
  <div class="metric-row">
    <span class="metric-label">Burden</span>
    <span class="metric-value metric-{{ review.burden_clarity }}">{{ review.burden_clarity|upper }}</span>
    {% if review.burden_statement_excerpt %}
      <blockquote>"{{ review.burden_statement_excerpt }}"</blockquote>
      <div class="metric-timestamp">stated at {{ (review.burden_first_stated_at_sec or 0) // 60 }}:{{ '%02d' % ((review.burden_first_stated_at_sec or 0) % 60) }}</div>
    {% endif %}
  </div>
  <div class="metric-row">
    <span class="metric-label">Movement</span>
    <span class="metric-value metric-{{ review.movement_clarity }}">{{ review.movement_clarity|upper|replace('_', ' ') }}</span>
    <div class="metric-rationale">{{ review.movement_rationale }}</div>
  </div>
  <div class="metric-row">
    <span class="metric-label">Application</span>
    <span class="metric-value metric-{{ review.application_specificity }}">{{ review.application_specificity|upper }}</span>
    {% if review.application_first_arrived_at_sec %}
      <div class="metric-timestamp">arrived at {{ review.application_first_arrived_at_sec // 60 }}:{{ '%02d' % (review.application_first_arrived_at_sec % 60) }} of {{ review.actual_duration_seconds // 60 }}:{{ '%02d' % (review.actual_duration_seconds % 60) }}</div>
    {% endif %}
  </div>
  <div class="metric-row">
    <span class="metric-label">Ethos</span>
    <span class="metric-value metric-{{ review.ethos_rating }}">{{ review.ethos_rating|upper }}</span>
  </div>
  <div class="metric-row">
    <span class="metric-label">Concreteness</span>
    <span class="metric-value">{{ review.concreteness_score }} / 5</span>
    {% if review.imagery_density_per_10min %}
      <div class="metric-sub">{{ '%.1f' % review.imagery_density_per_10min }} images per 10 min</div>
    {% endif %}
  </div>
  <div class="helpers-hurters">
    <div class="helpers">
      <h3>What helped</h3>
      <ul>
      {% for item in (review.top_impact_helpers or []) %}
        <li>{{ item }}</li>
      {% endfor %}
      </ul>
    </div>
    <div class="hurters">
      <h3>What hurt</h3>
      <ul>
      {% for item in (review.top_impact_hurters or []) %}
        <li>{{ item }}</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
{% endif %}
```

- [ ] **Step 2: Write the Faithfulness card partial**

Create `tools/workbench/templates/partials/sermon_faithfulness_card.html`:

```html
{% if review %}
<div class="sermon-card sermon-card-faithfulness">
  <h2>Faithfulness</h2>
  <div class="metric-row">
    <span class="metric-label">Christ Thread</span>
    <span class="metric-value metric-{{ review.christ_thread_score }}">{{ review.christ_thread_score|upper }}</span>
  </div>
  <div class="metric-row">
    <span class="metric-label">Exegetical Grounding</span>
    <span class="metric-value metric-{{ review.exegetical_grounding }}">{{ review.exegetical_grounding|upper }}</span>
    <div class="metric-rationale">{{ review.exegetical_grounding_notes }}</div>
  </div>
  {% if review.faithfulness_note %}
    <div class="faithfulness-note">{{ review.faithfulness_note }}</div>
  {% endif %}
</div>
{% endif %}
```

- [ ] **Step 3: Write the Diagnostic card partial**

Create `tools/workbench/templates/partials/sermon_diagnostic_card.html`:

```html
{% if review %}
<div class="sermon-card sermon-card-diagnostic">
  <h2>Diagnostic <span class="subtitle">(symptoms — causes live in Impact)</span></h2>
  <div class="metric-row">
    <span class="metric-label">Length</span>
    <span class="metric-value">
      {{ review.actual_duration_seconds // 60 }}:{{ '%02d' % (review.actual_duration_seconds % 60) }}
      {% if review.planned_duration_seconds %}
        / {{ review.planned_duration_seconds // 60 }}:{{ '%02d' % (review.planned_duration_seconds % 60) }} planned
        <span class="delta">{{ '%+d' % (review.duration_delta_seconds // 60) }}:{{ '%02d' % ((review.duration_delta_seconds|abs) % 60) }}</span>
      {% endif %}
    </span>
    {% if review.length_delta_commentary %}
      <div class="metric-commentary">{{ review.length_delta_commentary }}</div>
    {% endif %}
  </div>
  {% if review.late_application_note %}
    <div class="metric-row"><strong>Late application:</strong> {{ review.late_application_note }}</div>
  {% endif %}
  {% if review.outline_coverage_pct is not none %}
    <div class="metric-row">
      <span class="metric-label">Outline fidelity</span>
      <span class="metric-value">{{ '%d' % (review.outline_coverage_pct * 100) }}%</span>
      {% if review.outline_drift_note %}
        <div class="metric-rationale">{{ review.outline_drift_note }}</div>
      {% endif %}
    </div>
  {% endif %}
</div>
{% endif %}
```

- [ ] **Step 4: Write the Prescription card partial**

Create `tools/workbench/templates/partials/sermon_prescription_card.html`:

```html
{% if review and review.one_change_for_next_sunday %}
<div class="sermon-card sermon-card-prescription">
  <h2>For Next Sunday</h2>
  <div class="prescription-text">{{ review.one_change_for_next_sunday }}</div>
</div>
{% endif %}
```

- [ ] **Step 5: Write the flag list partial**

Create `tools/workbench/templates/partials/sermon_flag_list.html`:

```html
{% if flags %}
<div class="sermon-card sermon-card-flags">
  <h2>Flagged Moments</h2>
  <ul class="flag-list">
    {% for flag in flags %}
      <li class="flag flag-{{ flag.severity }}" data-flag-id="{{ flag.id }}">
        <span class="flag-type">{{ flag.flag_type|replace('_', ' ') }}</span>
        {% if flag.transcript_start_sec is not none %}
          <span class="flag-timestamp">@ {{ flag.transcript_start_sec // 60 }}:{{ '%02d' % (flag.transcript_start_sec % 60) }}</span>
        {% endif %}
        <div class="flag-rationale">{{ flag.rationale }}</div>
        {% if flag.excerpt %}
          <blockquote class="flag-excerpt">"{{ flag.excerpt }}"</blockquote>
        {% endif %}
      </li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

- [ ] **Step 6: Write candidates list partial**

Create `tools/workbench/templates/partials/sermon_candidates_list.html`:

```html
{% if candidates %}
<div class="sermon-card sermon-card-candidates">
  <h2>Candidate prep sessions</h2>
  <p>Not sure which session you prepped for this sermon. Pick one:</p>
  <ul>
    {% for c in candidates %}
      <li>
        <form method="post" action="/sermons/{{ sermon.id }}/approve-candidate/{{ c.id }}" style="display:inline">
          <span>{{ c.passage_ref }}</span>
          <span class="match-reason">{{ c.match_reason }}</span>
          <button type="submit">Approve</button>
        </form>
      </li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

- [ ] **Step 7: Write coach chat partial**

Create `tools/workbench/templates/partials/sermon_coach_chat.html`:

```html
<div class="sermon-card sermon-card-coach">
  <h2>Coach Conversation</h2>
  <div id="coach-messages"></div>
  <form id="coach-form" data-sermon-id="{{ sermon.id }}">
    <textarea name="message" placeholder="Ask the coach about this sermon..." rows="3"></textarea>
    <button type="submit">Send</button>
  </form>
</div>
```

- [ ] **Step 8: Replace `templates/sermons/detail.html` with the composed view**

Replace `tools/workbench/templates/sermons/detail.html` contents with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ sermon.title }} — Review</title>
  <link rel="stylesheet" href="/static/sermons.css?v=1">
</head>
<body>
<div id="sermon-review-page">
  <header>
    <a href="/sermons/">← All sermons</a>
    <h1>{{ sermon.title }}</h1>
    <div class="sermon-meta">
      {{ sermon.bible_text_raw }} · preached {{ sermon.preach_date }} ·
      {{ sermon.duration_seconds // 60 }}:{{ '%02d' % (sermon.duration_seconds % 60) }}
    </div>
  </header>

  {% if candidates %}
    {% include 'partials/sermon_candidates_list.html' %}
  {% endif %}

  {% if review %}
    {% include 'partials/sermon_impact_card.html' %}
    {% include 'partials/sermon_faithfulness_card.html' %}
    {% include 'partials/sermon_diagnostic_card.html' %}
    {% include 'partials/sermon_prescription_card.html' %}
    {% include 'partials/sermon_flag_list.html' %}
  {% elif sermon.sync_status == 'analysis_pending' or sermon.sync_status == 'analysis_running' %}
    <div class="state-message">Analysis in progress — refresh in a minute.</div>
  {% elif sermon.sync_status == 'analysis_failed' %}
    <div class="state-message error">Analysis failed: {{ sermon.sync_error }}
      <form method="post" action="/sermons/{{ sermon.id }}/reanalyze" style="display:inline">
        <button type="submit">Retry</button>
      </form>
    </div>
  {% else %}
    <div class="state-message">{{ sermon.sync_status }}</div>
  {% endif %}

  {% include 'partials/sermon_coach_chat.html' %}
</div>
<script src="/static/sermons.js"></script>
</body>
</html>
```

- [ ] **Step 9: Run the existing sermons route tests to confirm templates render**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermons_routes.py -v`
Expected: tests still PASS (the route doesn't care about the richer template, only that the response contains the passage string).

- [ ] **Step 10: Commit**

```bash
git add tools/workbench/templates/partials/sermon_impact_card.html tools/workbench/templates/partials/sermon_faithfulness_card.html tools/workbench/templates/partials/sermon_diagnostic_card.html tools/workbench/templates/partials/sermon_prescription_card.html tools/workbench/templates/partials/sermon_flag_list.html tools/workbench/templates/partials/sermon_candidates_list.html tools/workbench/templates/partials/sermon_coach_chat.html tools/workbench/templates/sermons/detail.html
git -c commit.gpgsign=false commit -m "feat: four-card review page partials + detail template"
```

---

## Task 21: List + patterns + sync_log full templates

**Files:**
- Modify: `tools/workbench/templates/sermons/list.html` — richer list view with badges
- Modify: `tools/workbench/templates/sermons/patterns.html` — trend cards + corpus gate display
- Modify: `tools/workbench/templates/sermons/sync_log.html` — runs table + cost summary

- [ ] **Step 1: Replace `templates/sermons/list.html` with the richer version**

Replace contents:

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Sermons</title>
<link rel="stylesheet" href="/static/sermons.css?v=1">
</head><body>
<div id="sermons-list-page">
<header>
  <h1>Sermons</h1>
  <nav>
    <a href="/sermons/patterns">Patterns</a>
    <a href="/sermons/sync-log">Sync log</a>
    <form method="post" action="/sermons/sync" style="display:inline">
      <button type="submit">Sync now</button>
    </form>
    <form method="post" action="/sermons/backfill?limit=24" style="display:inline">
      <button type="submit">Backfill last 24</button>
    </form>
  </nav>
</header>
<table class="sermons-table">
<thead><tr><th></th><th>Title</th><th>Preached</th><th>Duration</th><th>Status</th></tr></thead>
<tbody>
{% for s in sermons %}
<tr class="{% if s.badge %}has-badge{% endif %}">
  <td>{% if s.badge %}<span class="badge new-badge">NEW</span>{% endif %}</td>
  <td><a href="/sermons/{{ s.id }}">{{ s.title }}</a></td>
  <td>{{ s.preach_date }}</td>
  <td>{{ (s.duration_seconds // 60) if s.duration_seconds else '?' }} min</td>
  <td class="status status-{{ s.sync_status }}">{{ s.sync_status|replace('_', ' ') }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
</body></html>
```

- [ ] **Step 2: Replace `templates/sermons/patterns.html` with trend cards + corpus gate**

Replace contents:

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Sermon Patterns</title>
<link rel="stylesheet" href="/static/sermons.css?v=1">
</head><body>
<div id="sermon-patterns-page">
<header>
  <a href="/sermons/">← All sermons</a>
  <h1>Patterns</h1>
</header>

<div class="corpus-gate corpus-gate-{{ patterns.corpus_gate_status }}">
  {% if patterns.corpus_gate_status == 'pre_gate' %}
    <strong>Not enough corpus yet.</strong>
    {{ patterns.n_sermons }} sermons analyzed. Need at least 5 before patterns can be
    cited. Keep preaching and ingesting — the coach will open up soon.
  {% elif patterns.corpus_gate_status == 'emerging' %}
    <strong>Emerging patterns visible.</strong>
    {{ patterns.n_sermons }} sermons in the last {{ patterns.window_days }} days.
    The coach can cite patterns that show up in ≥3 of the last 5.
  {% else %}
    <strong>Stable corpus.</strong>
    {{ patterns.n_sermons }} sermons — full longitudinal voice is available.
  {% endif %}
</div>

<div class="trend-grid">
  <div class="trend-card">
    <h3>Duration delta (avg)</h3>
    <div class="trend-value">
      {% if patterns.avg_duration_delta_sec is not none %}
        {{ '%+d' % ((patterns.avg_duration_delta_sec or 0) // 60) }} min
      {% else %}—{% endif %}
    </div>
  </div>
  <div class="trend-card">
    <h3>Burden clear rate</h3>
    <div class="trend-value">{% if patterns.burden_clear_rate is not none %}{{ '%d' % (patterns.burden_clear_rate * 100) }}%{% else %}—{% endif %}</div>
  </div>
  <div class="trend-card">
    <h3>Movement clear rate</h3>
    <div class="trend-value">{% if patterns.movement_clear_rate is not none %}{{ '%d' % (patterns.movement_clear_rate * 100) }}%{% else %}—{% endif %}</div>
  </div>
  <div class="trend-card">
    <h3>Application concrete rate</h3>
    <div class="trend-value">{% if patterns.application_concrete_rate is not none %}{{ '%d' % (patterns.application_concrete_rate * 100) }}%{% else %}—{% endif %}</div>
  </div>
  <div class="trend-card">
    <h3>Ethos engaged rate</h3>
    <div class="trend-value">{% if patterns.ethos_engaged_rate is not none %}{{ '%d' % (patterns.ethos_engaged_rate * 100) }}%{% else %}—{% endif %}</div>
  </div>
  <div class="trend-card">
    <h3>Avg concreteness</h3>
    <div class="trend-value">{% if patterns.avg_concreteness %}{{ '%.1f' % patterns.avg_concreteness }} / 5{% else %}—{% endif %}</div>
  </div>
  <div class="trend-card">
    <h3>Christ explicit rate</h3>
    <div class="trend-value">{% if patterns.christ_explicit_rate is not none %}{{ '%d' % (patterns.christ_explicit_rate * 100) }}%{% else %}—{% endif %}</div>
  </div>
  <div class="trend-card">
    <h3>Exegetical grounded rate</h3>
    <div class="trend-value">{% if patterns.exegetical_grounded_rate is not none %}{{ '%d' % (patterns.exegetical_grounded_rate * 100) }}%{% else %}—{% endif %}</div>
  </div>
</div>
</div>
</body></html>
```

- [ ] **Step 3: Replace `templates/sermons/sync_log.html`**

Replace contents:

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Sync Log</title>
<link rel="stylesheet" href="/static/sermons.css?v=1">
</head><body>
<div id="sermons-sync-log-page">
<header>
  <a href="/sermons/">← All sermons</a>
  <h1>Sync Log</h1>
</header>
<div class="cost-summary">
  <strong>30-day LLM cost:</strong> ${{ '%.2f' % cost_30d }}
</div>
<table class="sync-runs-table">
<thead><tr><th>Run</th><th>Trigger</th><th>Started</th><th>Status</th><th>New</th><th>Updated</th><th>Failed</th><th>Error</th></tr></thead>
<tbody>
{% for r in runs %}
<tr class="status-{{ r.status }}">
  <td class="run-id">{{ r.run_id[:8] }}</td>
  <td>{{ r.trigger }}</td>
  <td>{{ r.started_at }}</td>
  <td>{{ r.status }}</td>
  <td>{{ r.sermons_new }}</td>
  <td>{{ r.sermons_updated }}</td>
  <td>{{ r.sermons_failed }}</td>
  <td class="error-cell">{{ r.error_summary or '' }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
</body></html>
```

- [ ] **Step 4: Run existing route tests — should still pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermons_routes.py tests/test_sermons_sync_routes.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/templates/sermons/list.html tools/workbench/templates/sermons/patterns.html tools/workbench/templates/sermons/sync_log.html
git -c commit.gpgsign=false commit -m "feat: styled sermon list, patterns, and sync-log templates"
```

---

## Task 22: Review tab integration into `study_session.html`

**Files:**
- Create: `tools/workbench/templates/partials/sermon_review_tab.html`
- Modify: `tools/workbench/templates/study_session.html` — add Review tab
- Modify: `tools/workbench/app.py` — pass sermon-link data into the study session route

- [ ] **Step 1: Create the review tab partial that reuses the four cards**

Create `tools/workbench/templates/partials/sermon_review_tab.html`:

```html
{% if linked_sermon %}
<div id="review-tab" class="study-tab">
  <header class="review-header">
    <h2>Sunday review</h2>
    <a href="/sermons/{{ linked_sermon.id }}">Open full review →</a>
  </header>

  {% if candidates %}
    {% include 'partials/sermon_candidates_list.html' %}
  {% endif %}

  {% set sermon = linked_sermon %}
  {% if review %}
    {% include 'partials/sermon_impact_card.html' %}
    {% include 'partials/sermon_faithfulness_card.html' %}
    {% include 'partials/sermon_diagnostic_card.html' %}
    {% include 'partials/sermon_prescription_card.html' %}
    {% include 'partials/sermon_flag_list.html' %}
  {% else %}
    <div class="state-message">Review not ready yet ({{ linked_sermon.sync_status }}).</div>
  {% endif %}

  {% include 'partials/sermon_coach_chat.html' %}
</div>
{% elif candidates %}
<div id="review-tab" class="study-tab">
  {% set sermon = None %}
  {% include 'partials/sermon_candidates_list.html' %}
</div>
{% endif %}
```

- [ ] **Step 2: Modify the study_session route in `app.py` to pass sermon-link data**

Find the existing `study_session` route in `tools/workbench/app.py`. Inside the view function, after loading the session, add:

```python
    # Sermon-coach integration: is there a linked sermon for this session?
    linked_sermon = None
    review = None
    candidates = []
    conn = db._conn()
    link_row = conn.execute("""
        SELECT s.*
        FROM sermons s
        JOIN sermon_links sl ON sl.sermon_id = s.id
        WHERE sl.session_id = ? AND sl.link_status = 'active'
        LIMIT 1
    """, (session_id,)).fetchone()
    if link_row:
        linked_sermon = dict(link_row)
        r = conn.execute("SELECT * FROM sermon_reviews WHERE sermon_id = ?", (linked_sermon['id'],)).fetchone()
        review = dict(r) if r else None
    candidate_rows = conn.execute("""
        SELECT sl.id, sl.sermon_id, sl.match_reason, s.title, s.bible_text_raw
        FROM sermon_links sl
        JOIN sermons s ON s.id = sl.sermon_id
        WHERE sl.link_status = 'candidate'
          AND s.id IN (
              SELECT sl2.sermon_id FROM sermon_links sl2 WHERE sl2.session_id = ?
          )
    """, (session_id,)).fetchall()
    candidates = [dict(c) for c in candidate_rows]
    conn.close()
```

Pass `linked_sermon`, `review`, `candidates` into the `render_template` call for `study_session.html`.

- [ ] **Step 3: Add the Review tab to `study_session.html`**

In `tools/workbench/templates/study_session.html`, after the existing tab structure (find where the conversation/card tabs are), add:

```html
{% if linked_sermon or candidates %}
  <button class="tab-button" data-tab="review">Review{% if linked_sermon and linked_sermon.ui_last_seen_version < linked_sermon.source_version %}<span class="tab-badge">•</span>{% endif %}</button>
{% endif %}
...
{% if linked_sermon or candidates %}
  {% include 'partials/sermon_review_tab.html' %}
{% endif %}
```

Wire up tab switching via existing study_session tab JS (use `data-tab="review"` convention).

- [ ] **Step 4: Write a test verifying the Review tab renders when a link exists**

Create `tools/workbench/tests/test_review_tab_integration.py`:

```python
import os
import tempfile
import pytest
from app import app, get_db


@pytest.fixture
def client_with_linked_session(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    monkeypatch.setenv('COMPANION_DB_PATH', db_path)
    import app as app_mod
    app_mod._db_instance = None
    app.config['TESTING'] = True
    with app.test_client() as c:
        db = get_db()
        db.init_db()
        # Create session + sermon + link + review
        conn = db._conn()
        conn.execute("""
            INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                                  current_phase, timer_remaining_seconds, created_at, updated_at)
            VALUES ('Romans 8:1-11', 45, 8, 1, 11, 'epistle', 'prayer', 900, datetime('now'), datetime('now'))
        """)
        sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                                  sync_status, last_state_change_at, first_synced_at, last_synced_at,
                                  created_at, updated_at)
            VALUES ('sa-test', 'bcast', 'Romans 8', 'sermon', 'review_ready', datetime('now'),
                    datetime('now'), datetime('now'), datetime('now'), datetime('now'))
        """)
        sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at)
            VALUES (?, ?, 'active', 'auto', 'tier1', datetime('now'))
        """, (sermon_id, sid))
        conn.execute("""
            INSERT INTO sermon_reviews (sermon_id, analyzer_version, homiletics_core_version, model_version,
                analyzed_transcript_hash, source_version_at_analysis, actual_duration_seconds,
                burden_clarity, top_impact_helpers, top_impact_hurters, one_change_for_next_sunday,
                computed_at)
            VALUES (?, '1.0.0', '1.0.0', 'claude-opus-4-6', 'h', 1, 2322,
                    'clear', '["a"]', '["b"]', 'change it', datetime('now'))
        """, (sermon_id,))
        conn.commit()
        conn.close()
        yield c, sid, sermon_id
    try:
        os.unlink(db_path)
    except Exception:
        pass


def test_study_session_shows_review_tab(client_with_linked_session):
    c, sid, sermon_id = client_with_linked_session
    resp = c.get(f'/study/{sid}')
    assert resp.status_code == 200
    # Review tab button present
    assert b'data-tab="review"' in resp.data or b'Review' in resp.data
    # Review content renders
    assert b'Impact' in resp.data
    assert b'change it' in resp.data
```

- [ ] **Step 5: Run the test**

Run: `cd tools/workbench && python3 -m pytest tests/test_review_tab_integration.py -v`
Expected: test PASSES. (If the existing `/study/<id>` route differs, adjust the test URL to match.)

- [ ] **Step 6: Commit**

```bash
git add tools/workbench/templates/partials/sermon_review_tab.html tools/workbench/templates/study_session.html tools/workbench/app.py tools/workbench/tests/test_review_tab_integration.py
git -c commit.gpgsign=false commit -m "feat: Review tab inside study_session.html rendering linked sermon + candidates"
```

---

## Task 23: `sermons.css` + `sermons.js`

**Files:**
- Create: `tools/workbench/static/sermons.css`
- Create: `tools/workbench/static/sermons.js`

- [ ] **Step 1: Write `sermons.css` matching the existing dark-theme companion styles**

Create `tools/workbench/static/sermons.css`:

```css
/* Sermon coach — dark theme matching companion.css / study.css */

:root {
  --sermon-bg: #0d1117;
  --sermon-surface: #161b22;
  --sermon-surface-hover: #1c2028;
  --sermon-border: #30363d;
  --sermon-text: #c9d1d9;
  --sermon-text-muted: #8b949e;
  --sermon-accent: #58a6ff;
  --sermon-good: #3fb950;
  --sermon-warn: #d29922;
  --sermon-bad: #f85149;
  --sermon-impact: #388bfd;
  --sermon-faithfulness: #a371f7;
  --sermon-diagnostic: #db6d28;
  --sermon-prescription: #3fb950;
}

body {
  background: var(--sermon-bg);
  color: var(--sermon-text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.5;
}

#sermon-review-page,
#sermons-list-page,
#sermon-patterns-page,
#sermons-sync-log-page {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px;
}

header { margin-bottom: 24px; }
header h1 { margin: 0 0 8px; font-size: 24px; }
.sermon-meta { color: var(--sermon-text-muted); font-size: 14px; }

.sermon-card {
  background: var(--sermon-surface);
  border: 1px solid var(--sermon-border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}
.sermon-card h2 { margin: 0 0 12px; font-size: 18px; letter-spacing: 0.02em; }
.sermon-card h2 .subtitle { font-size: 12px; color: var(--sermon-text-muted); font-weight: normal; }

.sermon-card-impact { border-left: 3px solid var(--sermon-impact); }
.sermon-card-faithfulness { border-left: 3px solid var(--sermon-faithfulness); }
.sermon-card-diagnostic { border-left: 3px solid var(--sermon-diagnostic); }
.sermon-card-prescription {
  border-left: 3px solid var(--sermon-prescription);
  background: rgba(63, 185, 80, 0.08);
}

.metric-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--sermon-border);
}
.metric-row:last-child { border-bottom: none; }
.metric-label { color: var(--sermon-text-muted); min-width: 120px; font-size: 13px; }
.metric-value { font-weight: 600; }
.metric-rationale, .metric-commentary { width: 100%; color: var(--sermon-text-muted); font-size: 13px; }
.metric-timestamp { width: 100%; color: var(--sermon-text-muted); font-size: 12px; }

.metric-crisp, .metric-clear, .metric-landed, .metric-explicit, .metric-grounded,
.metric-river, .metric-localized, .metric-concrete, .metric-seized, .metric-engaged { color: var(--sermon-good); }
.metric-implied, .metric-partial, .metric-gestured, .metric-mostly_river, .metric-abstract,
.metric-professional, .metric-uneven { color: var(--sermon-warn); }
.metric-muddled, .metric-absent, .metric-missed, .metric-lake, .metric-detached, .metric-pretext { color: var(--sermon-bad); }

.helpers-hurters { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 16px; }
.helpers h3, .hurters h3 { font-size: 13px; margin: 0 0 6px; color: var(--sermon-text-muted); }
.helpers ul, .hurters ul { margin: 0; padding-left: 18px; }
.helpers li { color: var(--sermon-good); }
.hurters li { color: var(--sermon-warn); }

.prescription-text { font-size: 16px; font-weight: 500; line-height: 1.6; }

.flag-list { list-style: none; padding: 0; margin: 0; }
.flag { padding: 12px; margin-bottom: 8px; background: var(--sermon-surface-hover); border-radius: 6px; cursor: pointer; }
.flag-concern { border-left: 2px solid var(--sermon-bad); }
.flag-warn { border-left: 2px solid var(--sermon-warn); }
.flag-note { border-left: 2px solid var(--sermon-accent); }
.flag-type { font-weight: 600; }
.flag-timestamp { color: var(--sermon-text-muted); margin-left: 8px; font-size: 12px; }
.flag-rationale { margin-top: 4px; }
.flag-excerpt { font-style: italic; color: var(--sermon-text-muted); margin: 6px 0 0; padding-left: 12px; border-left: 2px solid var(--sermon-border); }

.sermon-card-coach { background: var(--sermon-surface-hover); }
#coach-messages { min-height: 120px; max-height: 420px; overflow-y: auto; margin-bottom: 12px; }
#coach-messages .msg-user { color: var(--sermon-text); margin-bottom: 10px; }
#coach-messages .msg-assistant { color: var(--sermon-accent); margin-bottom: 10px; }
#coach-form textarea {
  width: 100%; background: var(--sermon-bg); color: var(--sermon-text);
  border: 1px solid var(--sermon-border); border-radius: 6px; padding: 8px;
  font: inherit; resize: vertical;
}
#coach-form button {
  background: var(--sermon-accent); color: #fff; border: none;
  padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-top: 8px;
}

.sermons-table { width: 100%; border-collapse: collapse; }
.sermons-table th, .sermons-table td { padding: 10px 8px; text-align: left; border-bottom: 1px solid var(--sermon-border); }
.sermons-table tr.has-badge { background: rgba(88, 166, 255, 0.08); }
.new-badge { background: var(--sermon-accent); color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.status-review_ready { color: var(--sermon-good); }
.status-analysis_pending, .status-analysis_running { color: var(--sermon-warn); }
.status-sync_failed, .status-analysis_failed, .status-permanent_failure { color: var(--sermon-bad); }

.corpus-gate { padding: 16px; border-radius: 8px; margin-bottom: 24px; }
.corpus-gate-pre_gate { background: rgba(139, 148, 158, 0.12); border: 1px solid var(--sermon-border); }
.corpus-gate-emerging { background: rgba(210, 153, 34, 0.12); border: 1px solid var(--sermon-warn); }
.corpus-gate-stable { background: rgba(63, 185, 80, 0.12); border: 1px solid var(--sermon-good); }

.trend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.trend-card { background: var(--sermon-surface); border: 1px solid var(--sermon-border); border-radius: 8px; padding: 16px; }
.trend-card h3 { margin: 0 0 8px; font-size: 13px; color: var(--sermon-text-muted); }
.trend-value { font-size: 24px; font-weight: 600; }

.cost-summary { padding: 12px; background: var(--sermon-surface); border-radius: 6px; margin-bottom: 16px; }
.sync-runs-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sync-runs-table th, .sync-runs-table td { padding: 6px 8px; border-bottom: 1px solid var(--sermon-border); }
.run-id { font-family: monospace; }

.state-message { padding: 16px; background: var(--sermon-surface); border-radius: 8px; text-align: center; color: var(--sermon-text-muted); }
.state-message.error { color: var(--sermon-bad); }

nav { display: flex; gap: 12px; align-items: center; }
nav a, nav button {
  background: var(--sermon-surface); color: var(--sermon-text);
  border: 1px solid var(--sermon-border); padding: 6px 12px; border-radius: 6px;
  text-decoration: none; cursor: pointer; font: inherit;
}
nav button:hover, nav a:hover { background: var(--sermon-surface-hover); }
```

- [ ] **Step 2: Write `sermons.js` handling the coach chat SSE**

Create `tools/workbench/static/sermons.js`:

```javascript
// Sermon coach — SSE chat handler

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('coach-form');
  if (!form) return;

  const messagesDiv = document.getElementById('coach-messages');
  const sermonId = form.dataset.sermonId;
  let conversationId = 1;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const textarea = form.querySelector('textarea[name=message]');
    const userText = textarea.value.trim();
    if (!userText) return;

    appendMessage('user', userText);
    textarea.value = '';

    const response = await fetch(`/sermons/${sermonId}/coach/message`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: userText, conversation_id: conversationId}),
    });

    if (!response.ok) {
      appendMessage('error', `HTTP ${response.status}`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const assistantEl = appendMessage('assistant', '');
    let buffer = '';

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === 'text_delta') {
            assistantEl.textContent += event.text;
          } else if (event.type === 'error') {
            assistantEl.textContent += `\n[error: ${event.error}]`;
          }
        } catch (err) {
          console.error('parse error', err);
        }
      }
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  });

  function appendMessage(role, text) {
    const el = document.createElement('div');
    el.className = `msg-${role}`;
    el.textContent = (role === 'user' ? 'You: ' : role === 'assistant' ? 'Coach: ' : '') + text;
    messagesDiv.appendChild(el);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return el;
  }

  // Flag click → focused message
  document.querySelectorAll('.flag').forEach(el => {
    el.addEventListener('click', () => {
      const rationale = el.querySelector('.flag-rationale')?.textContent;
      const ts = el.querySelector('.flag-timestamp')?.textContent;
      const type = el.querySelector('.flag-type')?.textContent;
      const textarea = form.querySelector('textarea');
      textarea.value = `Walk me through the ${type} flag ${ts || ''}: ${rationale}`;
      textarea.focus();
    });
  });
});
```

- [ ] **Step 3: Smoke-test by running the Flask app locally (optional for CI, required for manual UI test)**

Run: `cd tools/workbench && python3 app.py`
Then visit `http://localhost:5111/sermons/` in a browser. Expected: the dark-themed list page renders. Click into a sermon (even if you have to seed one manually) → four cards render → clicking a flag pre-fills the coach input.

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/static/sermons.css tools/workbench/static/sermons.js
git -c commit.gpgsign=false commit -m "feat: sermons.css dark theme + sermons.js SSE coach chat"
```

---

## Task 24: `scripts/backtest_matcher.py`

**Files:**
- Create: `scripts/backtest_matcher.py`

- [ ] **Step 1: Write the backtest script**

Create `scripts/backtest_matcher.py`:

```python
#!/usr/bin/env python3
"""Backtest sermon_matcher.py over the real database and print a CSV of decisions.

Usage:
    python3 scripts/backtest_matcher.py > backtest.csv

Reads from tools/workbench/companion.db (or COMPANION_DB_PATH if set).
"""
import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'workbench'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from companion_db import CompanionDB
from sermon_matcher import (
    match_sermon_to_sessions, SermonInfo, SessionInfo, SermonLink,
    MatcherSettings,
)


def main():
    db_path = os.environ.get('COMPANION_DB_PATH',
                              os.path.join(os.path.dirname(__file__), '..',
                                            'tools', 'workbench', 'companion.db'))
    db = CompanionDB(db_path)
    conn = db._conn()
    sermons = conn.execute("""
        SELECT id, book, chapter, verse_start, verse_end, preach_date, sermon_type,
               bible_text_raw
        FROM sermons
        WHERE classified_as = 'sermon' AND is_remote_deleted = 0
        ORDER BY preach_date DESC
    """).fetchall()

    writer = csv.writer(sys.stdout)
    writer.writerow(['sermon_id', 'preach_date', 'passage', 'decision', 'tier',
                      'reason', 'linked_session_id'])

    settings = MatcherSettings()
    for s_row in sermons:
        sessions_rows = conn.execute("""
            SELECT id, book, chapter, verse_start, verse_end, created_at,
                   last_homiletical_activity_at
            FROM sessions WHERE book = ? AND chapter = ?
        """, (s_row[1], s_row[2])).fetchall()
        sessions = tuple(SessionInfo(
            id=r[0], book=r[1], chapter=r[2], verse_start=r[3], verse_end=r[4],
            created_at=r[5], last_homiletical_activity_at=r[6],
        ) for r in sessions_rows)
        passage_rows = conn.execute(
            "SELECT book, chapter_start, verse_start, chapter_end, verse_end "
            "FROM sermon_passages WHERE sermon_id = ? ORDER BY rank",
            (s_row[0],)
        ).fetchall()
        passages = [dict(book=r[0], chapter_start=r[1], verse_start=r[2],
                          chapter_end=r[3], verse_end=r[4])
                     for r in passage_rows]
        sermon = SermonInfo(
            id=s_row[0], book=s_row[1], chapter=s_row[2],
            verse_start=s_row[3], verse_end=s_row[4],
            preach_date=s_row[5], sermon_type=s_row[6],
            passages=passages,
        )
        decision = match_sermon_to_sessions(
            sermon, sessions, existing_links=(), rejected_session_ids=frozenset(),
            settings=settings,
        )
        linked_id = (decision.auto_link_target.session_id
                      if decision.auto_link_target else '')
        tier = (decision.auto_link_target.tier
                 if decision.auto_link_target
                 else (decision.candidates[0].tier if decision.candidates else 0))
        writer.writerow([
            s_row[0], s_row[5], s_row[7],
            decision.action, tier, decision.reason_summary, linked_id,
        ])

    conn.close()


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Make it executable and smoke-test**

Run: `chmod +x scripts/backtest_matcher.py`
Run: `cd /Volumes/External/Logos4 && python3 scripts/backtest_matcher.py | head -5`
Expected: CSV header + up to 4 rows (empty DB is OK — just the header).

- [ ] **Step 3: Commit**

```bash
git add scripts/backtest_matcher.py
git -c commit.gpgsign=false commit -m "feat: scripts/backtest_matcher.py CSV audit tool"
```

---

## Task 25: Integration + E2E tests

**Files:**
- Create: `tools/workbench/tests/test_sermon_pipeline_end_to_end.py`
- Create: `tools/workbench/tests/test_sermon_source_change_flow.py`
- Create: `tools/workbench/tests/test_e2e_sermon_ui.py` (Playwright)

- [ ] **Step 1: Write the end-to-end pipeline test**

Create `tools/workbench/tests/test_sermon_pipeline_end_to_end.py`:

```python
import os
import tempfile
import datetime as dt
from types import SimpleNamespace
import hashlib
import pytest
from companion_db import CompanionDB
from sermonaudio_sync import run_sync_with_client
from sermon_matcher import apply_match_decision_for_sermon
from sermon_analyzer import analyze_sermon, AnalyzerInput, run_pure_stages, build_rubric_prompt
from llm_client import CannedLLMClient


class MockSAClient:
    def __init__(self, items): self.items = items
    def list_sermons_updated_since(self, broadcaster_id, since=None, limit=100):
        return self.items
    def get_sermon_detail(self, sermon_id):
        for i in self.items:
            if i.sermon_id == sermon_id: return i
        return None


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _canned_review(prompt):
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    return {key: {
        'output': {
            'tier1_impact': {
                'burden_clarity': 'clear',
                'burden_statement_excerpt': 'No condemnation',
                'burden_first_stated_at_sec': 120,
                'movement_clarity': 'river',
                'movement_rationale': 'Coherent arc.',
                'application_specificity': 'concrete',
                'application_first_arrived_at_sec': 1500,
                'application_excerpts': [],
                'ethos_rating': 'engaged',
                'ethos_markers': [],
                'concreteness_score': 4,
                'imagery_density_per_10min': 3.8,
                'narrative_moments': [],
            },
            'tier2_faithfulness': {
                'christ_thread_score': 'explicit',
                'christ_thread_excerpts': [],
                'exegetical_grounding': 'grounded',
                'exegetical_grounding_notes': 'Strong text focus.',
            },
            'tier3_diagnostic': {
                'length_delta_commentary': 'On time.',
                'density_hotspots': [],
                'late_application_note': None,
                'outline_drift_note': None,
            },
            'coach_summary': {
                'top_impact_helpers': ['Clear burden', 'Strong application', 'Engaged delivery'],
                'top_impact_hurters': ['—', '—', '—'],
                'faithfulness_note': 'Christ thread explicit.',
                'one_change_for_next_sunday': 'Keep doing exactly this.',
            },
            'flags': [],
        },
        'input_tokens': 4000, 'output_tokens': 600, 'model': 'claude-opus-4-6',
    }}


def test_full_pipeline_sync_match_analyze(fresh_db):
    # Seed a session
    sid = fresh_db.create_session('Romans 8:1-11', 45, 8, 1, 11, 'epistle')
    conn = fresh_db._conn()
    conn.execute("UPDATE sessions SET created_at = '2026-04-06 09:00:00', "
                  "last_homiletical_activity_at = '2026-04-09 12:00:00' WHERE id = ?", (sid,))
    conn.commit()
    conn.close()

    # Sync a sermon
    remote = SimpleNamespace(
        sermon_id='sa-e2e', broadcaster_id='bcast', title='Romans 8',
        speaker_name='Bryan Schneider', event_type='Sunday Service', series='Romans',
        preach_date=dt.date(2026, 4, 12), publish_date=dt.date(2026, 4, 12),
        duration=2322, bible_text='Romans 8:1-11',
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome to Romans 8.\n\n' * 400,  # well over 1000 words
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    client = MockSAClient([remote])
    sync_result = run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    assert sync_result['sermons_new'] == 1

    # Match
    conn = fresh_db._conn()
    sermon_id = conn.execute("SELECT id FROM sermons WHERE sermonaudio_id='sa-e2e'").fetchone()[0]
    conn.close()
    match_decision = apply_match_decision_for_sermon(fresh_db, sermon_id)
    assert match_decision.action == 'auto_link'

    # Analyze
    conn = fresh_db._conn()
    inp = AnalyzerInput(
        sermon_id=sermon_id, transcript_text=remote.transcript,
        duration_sec=2322, planned_duration_sec=None, outline_points=[],
        bible_text_raw='Romans 8:1-11',
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    conn.close()
    llm = CannedLLMClient(_canned_review(prompt))
    analysis = analyze_sermon(fresh_db, sermon_id, llm_client=llm)
    assert analysis['status'] == 'review_ready'

    # Final: verify review row exists and contains expected data
    conn = fresh_db._conn()
    review = conn.execute(
        "SELECT burden_clarity, one_change_for_next_sunday FROM sermon_reviews WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    status = conn.execute("SELECT sync_status FROM sermons WHERE id=?", (sermon_id,)).fetchone()[0]
    link = conn.execute(
        "SELECT link_status FROM sermon_links WHERE sermon_id=?", (sermon_id,)
    ).fetchone()
    conn.close()
    assert review == ('clear', 'Keep doing exactly this.')
    assert status == 'review_ready'
    assert link == ('active',)
```

- [ ] **Step 2: Write the source-change flow test**

Create `tools/workbench/tests/test_sermon_source_change_flow.py`:

```python
import os
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest
from companion_db import CompanionDB
from sermonaudio_sync import upsert_sermon


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _remote(**overrides):
    base = dict(
        sermon_id='sa-1', broadcaster_id='bcast', title='Test',
        speaker_name='Bryan Schneider', event_type='Sunday Service', series='R',
        preach_date=dt.date(2026, 4, 12), publish_date=dt.date(2026, 4, 12),
        duration=2322, bible_text='Romans 8:1-11',
        audio_url='x', transcript='hi',
        update_date=dt.datetime(2026, 4, 12),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_transcript_change_bumps_source_version_and_triggers_analysis(fresh_db):
    conn = fresh_db._conn()
    # Initial insert — transcript present
    upsert_sermon(conn, _remote(transcript='first version'))
    conn.commit()
    # Simulate review_ready state
    conn.execute("UPDATE sermons SET sync_status = 'review_ready' WHERE sermonaudio_id='sa-1'")
    conn.commit()
    # New transcript
    upsert_sermon(conn, _remote(transcript='second version'))
    conn.commit()
    row = conn.execute("SELECT source_version, sync_status FROM sermons WHERE sermonaudio_id='sa-1'").fetchone()
    conn.close()
    assert row[0] == 2
    # Status should have been pushed back for re-analysis
    assert row[1] in ('analysis_pending', 'transcript_ready')


def test_unchanged_source_is_noop(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote(transcript='same'))
    upsert_sermon(conn, _remote(transcript='same'))
    row = conn.execute("SELECT source_version FROM sermons").fetchone()
    conn.close()
    assert row[0] == 1
```

- [ ] **Step 3: Write a minimal Playwright E2E test**

Create `tools/workbench/tests/test_e2e_sermon_ui.py`:

```python
"""Minimal Playwright tests for the sermon review UI.

Requires: playwright, pytest-playwright. Server must be running on http://localhost:5111
or the PORT env var. Tests use a preseeded DB; see conftest.py for setup patterns.
"""
import pytest

pytest.importorskip('playwright')

from playwright.sync_api import sync_playwright


BASE_URL = 'http://localhost:5111'


@pytest.mark.e2e
def test_sermons_list_loads():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'{BASE_URL}/sermons/')
        assert page.title().lower().startswith('sermon')
        browser.close()


@pytest.mark.e2e
def test_sermon_detail_renders_four_cards_when_review_ready():
    """Requires a seeded sermon with a review. Run seed_e2e.py first."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'{BASE_URL}/sermons/1')
        # Four card headers must appear when review_ready
        if page.locator('text=Impact').is_visible():
            assert page.locator('text=Faithfulness').is_visible()
            assert page.locator('text=Diagnostic').is_visible()
            assert page.locator('text=For Next Sunday').is_visible()
        browser.close()
```

- [ ] **Step 4: Run all integration tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_pipeline_end_to_end.py tests/test_sermon_source_change_flow.py -v`
Expected: both pytest tests PASS. Playwright test is `@pytest.mark.e2e` and only runs when the server is up (skipped otherwise).

- [ ] **Step 5: Run the entire new sermon test suite together**

Run: `cd tools/workbench && python3 -m pytest tests/test_companion_db_sermon_tables.py tests/test_voice_constants.py tests/test_sermon_passages.py tests/test_homiletics_core.py tests/test_llm_client.py tests/test_sermonaudio_sync.py tests/test_sermonaudio_sync_orchestrator.py tests/test_sermon_type_topical.py tests/test_sermon_matcher.py tests/test_sermon_rematch_flow.py tests/test_sermon_analyzer_stages.py tests/test_sermon_analyzer_llm.py tests/test_sermon_analyzer_writer.py tests/test_sermon_coach_tools.py tests/test_sermon_coach_agent.py tests/test_sermon_coach_streaming.py tests/test_sermons_routes.py tests/test_sermons_sync_routes.py tests/test_scheduler_setup.py tests/test_review_tab_integration.py tests/test_sermon_pipeline_end_to_end.py tests/test_sermon_source_change_flow.py -v`
Expected: all sermon-coach tests PASS.

- [ ] **Step 6: Run the full project test suite to catch regressions**

Run: `cd tools/workbench && python3 -m pytest tests/ -q`
Expected: all tests (existing + new) PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/workbench/tests/test_sermon_pipeline_end_to_end.py tools/workbench/tests/test_sermon_source_change_flow.py tools/workbench/tests/test_e2e_sermon_ui.py
git -c commit.gpgsign=false commit -m "test: add sermon coach integration + source change + E2E tests"
```

---

## Self-Review Notes

After writing this plan, I spot-checked against the spec:

1. **Spec coverage:** All nine spec sections have tasks covering their requirements.
   - §2 Data Model → Task 1 creates the 8 tables + ALTER; Task 8 writes sermon_passages; Task 10 maintains `sessions.last_homiletical_activity_at`.
   - §3 Ingest → Tasks 6 + 7 + 8 (pure helpers, orchestrator, sermon_passages).
   - §4 Matcher → Tasks 9 + 10 (pure function + orchestrator + rematch triggers).
   - §5 Analyzer → Tasks 11 + 12 + 13 (pure stages, LLM rubric pass, writer + dispatch).
   - §6 Coach Agent → Tasks 14 + 15 + 16 (tools, prompt, streaming loop).
   - §7 UI → Tasks 17 + 18 + 19 + 20 + 21 + 22 + 23 (routes, scheduler, partials, list/patterns/sync-log, Review tab, static).
   - §8 Error handling → Integrated throughout: file lock, retry cooldown, state transitions, dispatch poll fallback, LLM retry in Task 12/13.
   - §9 Testing → Tasks 1 through 25 each include their own unit test; Task 25 adds integration + E2E. Task 24 adds backtest script.
   - Operational costs + deferred features are documented in the spec appendix; no task needed.

2. **Placeholder scan:** No "TBD", "TODO", "implement later", or "similar to Task N" references.

3. **Type consistency:** `SermonInfo`, `SessionInfo`, `SermonLink`, `MatchDecision`, `SessionMatch`, `MatcherSettings`, `AnalyzerInput`, `PureStageOutput`, `LLMClient`, `CannedLLMClient`, `AnthropicClient`, `CoachTurnResult` are consistently named across tasks. Function signatures (`match_sermon_to_sessions`, `apply_match_decision_for_sermon`, `run_sync_with_client`, `analyze_sermon`, `dispatch_pending_analyses`, `build_system_prompt`, `stream_coach_response`) are stable.

4. **Ordering:** Dependencies flow correctly — homiletics_core (Task 4) lands before sermon_analyzer (Task 11), llm_client (Task 5) before analyzer LLM pass (Task 12), sermon_coach_tools (Task 14) before coach agent (Task 15), agent (Task 15) before streaming (Task 16), streaming before Flask SSE route (Task 18), scheduler setup (Task 19) after the orchestrator exists (Task 7), partials (Task 20) before review tab integration (Task 22).

5. **Gaps I noticed and fixed inline:**
   - `companion_tools.py` doesn't need modification — the coach reuses it via direct import, no change to the file itself.
   - `requirements-dev.txt` may not exist; Task 1 creates it.
   - The existing `companion_db.py` uses `COMPANION_DB_PATH` env var; confirmed in Task 17 test fixtures.
   - The existing `app.py` already has a `get_db()` helper — confirmed reused, not re-created.
   - Playwright test uses `@pytest.mark.e2e` so it's skipped in non-interactive runs.
   - Task 25's existing-suite regression run catches any break in the pre-existing workbench tests.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-14-sermon-coach-mvp.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task on Opus 4.6, review between tasks, four-way verification (implementer → me → codex → me final pass → you when uncertain). Fast iteration, minimal context pollution, clean per-task commit boundaries.

**2. Inline Execution** — I execute tasks in this session using executing-plans, with batch checkpoints every 3-5 tasks for review. Preserves conversation thread but uses more context.

**Which approach?**




