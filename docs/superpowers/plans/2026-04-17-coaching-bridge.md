# Coaching Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect sermon coaching insights, patterns, and commitments into the study companion so it can reference Bryan's historical patterns during sermon prep — without nagging, and only when relevant.

**Architecture:** Three layers. Layer 1: active coaching commitment loaded into the study prompt. Layer 2: five coach-aware tools added to the companion with a retrieval policy and escalation ladder. Layer 3: session-level coaching exposure tracking for anti-nagging enforcement. Plus: coaching insights capture from coach conversations and linked_session_id fix for the per-sermon coach.

**Tech Stack:** Python (Flask), SQLite, existing `meta_coach_tools.py` / `sermon_coach_tools.py` query functions, `companion_agent.py` prompt builder, `companion_tools.py` tool definitions.

**Spec:** `docs/superpowers/specs/2026-04-17-coaching-bridge-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `tools/workbench/companion_db.py` | Modify | Add `coaching_insights` + `session_coaching_exposure` tables to `init_db()` |
| `tools/workbench/coaching_bridge.py` | Create | Bridge helper functions: load commitment, load insights, track/check exposure |
| `tools/workbench/companion_tools.py` | Modify | Add 5 coaching tool definitions to `TOOL_DEFINITIONS` |
| `tools/workbench/companion_agent.py` | Modify | Add coaching context to `build_study_prompt()`, add coaching tool dispatch to `execute_tool()` in study streaming, add retrieval policy + escalation ladder to prompt |
| `tools/workbench/app.py` | Modify | Wire coaching context into `study_discuss` route, add coaching insight REST endpoints |
| `tools/workbench/sermon_coach_agent.py` | Modify | Wire `linked_session_id` into `stream_coach_response()`, add insight proposal to coach prompt |
| `tools/workbench/meta_coach_agent.py` | Modify | Add insight proposal to meta-coach prompt |
| `tools/workbench/tests/test_coaching_bridge.py` | Create | Unit tests for bridge helpers |
| `tools/workbench/tests/test_coaching_bridge_tools.py` | Create | Tests for coaching tools in companion |
| `tools/workbench/tests/test_coaching_bridge_integration.py` | Create | End-to-end bridge flow test |

---

### Task 1: Schema — `coaching_insights` + `session_coaching_exposure` tables

**Files:**
- Modify: `tools/workbench/companion_db.py:380-400`
- Test: `tools/workbench/tests/test_coaching_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tools/workbench/tests/test_coaching_bridge.py
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = CompanionDB(path)
    d.init_db()
    yield d
    os.unlink(path)


def test_coaching_insights_table_exists(db):
    conn = db._conn()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    assert 'coaching_insights' in tables


def test_session_coaching_exposure_table_exists(db):
    conn = db._conn()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    assert 'session_coaching_exposure' in tables


def test_coaching_insights_insert_and_query(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES ('application_specificity',
                'Slow down at application moments',
                '["outline construction", "application development"]',
                '["textual observation"]',
                datetime('now'))
    """)
    conn.commit()
    row = conn.execute("SELECT summary FROM coaching_insights").fetchone()
    conn.close()
    assert row[0] == 'Slow down at application moments'


def test_session_coaching_exposure_unique_per_dimension(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('Romans 8:1-11', 66, 8, 1, 11, 'epistle', 'prayer', 900,
                datetime('now'), datetime('now'))
    """)
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO session_coaching_exposure
            (session_id, dimension_key, escalation_level, response, created_at)
        VALUES (?, 'burden_clarity', 2, 'pending', datetime('now'))
    """, (sid,))
    conn.commit()
    # Second insert for same dimension should fail
    with pytest.raises(Exception):
        conn.execute("""
            INSERT INTO session_coaching_exposure
                (session_id, dimension_key, escalation_level, response, created_at)
            VALUES (?, 'burden_clarity', 3, 'pending', datetime('now'))
        """, (sid,))
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url`
Expected: FAIL — tables don't exist yet

- [ ] **Step 3: Add tables to `init_db()`**

In `companion_db.py`, add after the `coaching_commitments` block (after line ~398, before `conn.commit()`):

```python
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS coaching_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dimension_key TEXT,
                summary TEXT NOT NULL,
                applies_when TEXT NOT NULL,
                avoid_when TEXT NOT NULL,
                source_sermon_id INTEGER REFERENCES sermons(id),
                source_conversation_id INTEGER,
                superseded_by INTEGER REFERENCES coaching_insights(id),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS session_coaching_exposure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                dimension_key TEXT NOT NULL,
                escalation_level INTEGER NOT NULL,
                response TEXT CHECK (response IN ('accepted', 'declined', 'deferred', 'pending')),
                created_at TEXT NOT NULL,
                UNIQUE(session_id, dimension_key)
            );
        """)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_db.py tools/workbench/tests/test_coaching_bridge.py
git commit -m "feat: add coaching_insights + session_coaching_exposure tables"
```

---

### Task 2: Bridge helper functions — `coaching_bridge.py`

**Files:**
- Create: `tools/workbench/coaching_bridge.py`
- Test: `tools/workbench/tests/test_coaching_bridge.py` (append)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_coaching_bridge.py`:

```python
from coaching_bridge import (
    load_active_commitment,
    load_coaching_insights,
    record_coaching_exposure,
    check_coaching_exposure,
    build_coaching_prompt_section,
)


def test_load_active_commitment_returns_none_when_empty(db):
    result = load_active_commitment(db)
    assert result is None


def test_load_active_commitment_returns_dict_when_present(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO coaching_commitments
            (dimension_key, practice_experiment, target_sermons, status, created_at)
        VALUES ('application_specificity', 'Pause at application moments', 2,
                'active', datetime('now'))
    """)
    conn.commit()
    conn.close()
    result = load_active_commitment(db)
    assert result is not None
    assert result['dimension_key'] == 'application_specificity'
    assert result['practice_experiment'] == 'Pause at application moments'


def test_load_coaching_insights_returns_non_superseded(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO coaching_insights
            (id, dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES (1, 'burden_clarity', 'State burden early', '["outline"]', '["observation"]',
                datetime('now'))
    """)
    conn.execute("""
        INSERT INTO coaching_insights
            (id, dimension_key, summary, applies_when, avoid_when, superseded_by, created_at)
        VALUES (2, 'burden_clarity', 'Old insight', '["outline"]', '["observation"]', 1,
                datetime('now'))
    """)
    conn.commit()
    conn.close()
    insights = load_coaching_insights(db)
    assert len(insights) == 1
    assert insights[0]['summary'] == 'State burden early'


def test_record_and_check_exposure(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('Romans 3:1-8', 66, 3, 1, 8, 'epistle', 'prayer', 900,
                datetime('now'), datetime('now'))
    """)
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    assert check_coaching_exposure(db, sid, 'burden_clarity') is None
    record_coaching_exposure(db, sid, 'burden_clarity', escalation_level=2, response='pending')
    exp = check_coaching_exposure(db, sid, 'burden_clarity')
    assert exp is not None
    assert exp['escalation_level'] == 2
    assert exp['response'] == 'pending'


def test_build_coaching_prompt_section_with_commitment(db):
    section = build_coaching_prompt_section(
        commitment={'dimension_key': 'application_specificity',
                    'practice_experiment': 'Pause at application moments',
                    'target_sermons': 2},
        insights=[],
    )
    assert 'application_specificity' in section
    assert 'Pause at application moments' in section
    assert 'RETRIEVAL' in section or 'ESCALATION' in section


def test_build_coaching_prompt_section_empty_when_no_data():
    section = build_coaching_prompt_section(commitment=None, insights=[])
    assert section == ''
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url -k "load_ or record_ or check_ or build_coaching"`
Expected: FAIL — `coaching_bridge` module doesn't exist

- [ ] **Step 3: Implement `coaching_bridge.py`**

```python
# tools/workbench/coaching_bridge.py
"""Bridge helpers: load coaching data for the study companion."""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional


def load_active_commitment(db) -> Optional[dict]:
    """Load the active coaching commitment, if any."""
    conn = db._conn()
    row = conn.execute("""
        SELECT dimension_key, practice_experiment, target_sermons, created_at
        FROM coaching_commitments WHERE status = 'active'
    """).fetchone()
    conn.close()
    if not row:
        return None
    return {
        'dimension_key': row[0],
        'practice_experiment': row[1],
        'target_sermons': row[2],
        'created_at': row[3],
    }


def load_coaching_insights(db, limit: int = 5) -> list[dict]:
    """Load recent non-superseded coaching insights."""
    conn = db._conn()
    rows = conn.execute("""
        SELECT id, dimension_key, summary, applies_when, avoid_when,
               source_sermon_id, created_at
        FROM coaching_insights
        WHERE superseded_by IS NULL
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {
            'id': r[0],
            'dimension_key': r[1],
            'summary': r[2],
            'applies_when': json.loads(r[3]) if r[3] else [],
            'avoid_when': json.loads(r[4]) if r[4] else [],
            'source_sermon_id': r[5],
            'created_at': r[6],
        }
        for r in rows
    ]


def record_coaching_exposure(db, session_id: int, dimension_key: str,
                             escalation_level: int, response: str = 'pending'):
    """Record that a coaching dimension was surfaced in this session."""
    conn = db._conn()
    conn.execute("""
        INSERT OR REPLACE INTO session_coaching_exposure
            (session_id, dimension_key, escalation_level, response, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, dimension_key, escalation_level, response,
          datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def check_coaching_exposure(db, session_id: int, dimension_key: str) -> Optional[dict]:
    """Check if a coaching dimension has been surfaced this session."""
    conn = db._conn()
    row = conn.execute("""
        SELECT escalation_level, response FROM session_coaching_exposure
        WHERE session_id = ? AND dimension_key = ?
    """, (session_id, dimension_key)).fetchone()
    conn.close()
    if not row:
        return None
    return {'escalation_level': row[0], 'response': row[1]}


def build_coaching_prompt_section(commitment: Optional[dict],
                                  insights: list[dict]) -> str:
    """Build the coaching context section for the study prompt.

    Returns empty string if no coaching data available.
    """
    if not commitment and not insights:
        return ''

    parts = ['## Coaching Memory\n']

    if commitment:
        parts.append(f"""### Active Coaching Commitment (background — do not recite verbatim)

Dimension: {commitment['dimension_key']}
Practice: {commitment['practice_experiment']}
Target: {commitment.get('target_sermons', 2)} sermons

Use this as a lens that shapes your guidance. When Bryan reaches sermon-shaping
work related to this dimension, naturally guide toward the practice — don't
announce the commitment. Active commitment is a bias, not a straitjacket: if
today's text demands something different, follow the text.
""")

    if insights:
        parts.append('### Coaching Insights from Past Conversations\n')
        for ins in insights[:3]:
            applies = ', '.join(ins.get('applies_when', []))
            avoid = ', '.join(ins.get('avoid_when', []))
            parts.append(f"- **{ins.get('dimension_key', 'general')}**: {ins['summary']}")
            if applies:
                parts.append(f"  Applies during: {applies}")
            if avoid:
                parts.append(f"  Avoid during: {avoid}")
            parts.append('')

    parts.append("""### Retrieval Policy

WHEN TO CONSULT COACHING TOOLS:
- During textual work (observation, word study, context, commentaries): Do NOT
  consult coaching tools. Your job here is discovery. Exception: Bryan asks.
- Transition gate: When the conversation shows ambiguous signals (exegesis winding
  down, outline language emerging), ask ONE TIME: "Are we still exploring the text,
  or are we shaping the sermon now?" Once answered, remember the mode.
- During sermon construction: Check get_active_commitment. Consult other tools when
  you detect sprawling outline, deferred application, unclear burden, or Bryan asks.

ESCALATION LADDER (never skip levels):
1. SILENT SHAPING — guide toward clarity, no coaching reference
2. DIAGNOSTIC CHECK — ask a targeted question testing if the issue is present
   ("What's the one burden you want them to carry out?")
3. PATTERN REFERENCE — only if diagnostic confirms drift
4. SPECIFIC EXAMPLE — only if Bryan asks, disputes, or is stuck
5. CONCRETE INTERVENTION — one action, not more analysis

ANTI-NAGGING:
- Max one explicit coaching callback per dimension per session
- If Bryan declines or redirects, back off — do not resurface that dimension
- Frame as allyship: "To help this land more clearly..." not "Because you usually..."
- No sermon titles/dates unprompted unless Bryan asks for evidence
- If current prep doesn't exhibit a known pattern, stay silent about it

TOOL PRECEDENCE (when data conflicts):
1. Active commitment  2. Pattern aggregates  3. Counterexamples
4. Coaching insights  5. Representative moments
""")

    return '\n'.join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url`
Expected: ALL PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/coaching_bridge.py tools/workbench/tests/test_coaching_bridge.py
git commit -m "feat: coaching_bridge.py helpers — load commitment, insights, exposure tracking"
```

---

### Task 3: Add coaching tools to companion TOOL_DEFINITIONS

**Files:**
- Modify: `tools/workbench/companion_tools.py:298`
- Test: `tools/workbench/tests/test_coaching_bridge_tools.py`

- [ ] **Step 1: Write failing test**

```python
# tools/workbench/tests/test_coaching_bridge_tools.py
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_tools import TOOL_DEFINITIONS


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


COACHING_TOOL_NAMES = {
    'get_active_commitment',
    'get_sermon_patterns',
    'get_representative_moments',
    'get_counterexamples',
    'get_coaching_insights',
}


def test_coaching_tools_present_in_definitions():
    tool_names = {t['name'] for t in TOOL_DEFINITIONS}
    for name in COACHING_TOOL_NAMES:
        assert name in tool_names, f"Missing coaching tool: {name}"


def test_coaching_tools_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        if tool['name'] in COACHING_TOOL_NAMES:
            assert 'description' in tool
            assert 'input_schema' in tool
            assert tool['input_schema'].get('type') == 'object'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge_tools.py -v -p no:base_url`
Expected: FAIL — coaching tools not in TOOL_DEFINITIONS

- [ ] **Step 3: Add 5 coaching tool definitions to `companion_tools.py`**

Append after the last tool definition (after line ~298, before `get_tool_names()`):

```python
    # ── Coaching Bridge Tools ─────────────────────────────────────────────
    {
        'name': 'get_active_commitment',
        'description': 'Get Bryan\'s current coaching commitment and progress. Returns the one practice he\'s working on, or null if none active.',
        'input_schema': {
            'type': 'object',
            'properties': {},
            'required': [],
        },
    },
    {
        'name': 'get_sermon_patterns',
        'description': 'Get aggregate sermon analysis patterns over a rolling window: burden clarity rate, application timing, movement, ethos, density, duration delta. Use during sermon construction to inform guidance.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'window_days': {'type': 'integer', 'description': 'Rolling window in days (default 90)'},
            },
            'required': [],
        },
    },
    {
        'name': 'get_representative_moments',
        'description': 'Get specific timestamped moments from past sermons for a given dimension. Use to find concrete examples of what Bryan does well or struggles with.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'dimension': {'type': 'string', 'description': 'One of: burden_clarity, movement_clarity, application_specificity, ethos_rating, concreteness_score, christ_thread_score, exegetical_grounding'},
                'valence': {'type': 'string', 'enum': ['positive', 'negative'], 'description': 'Whether to find strong or weak examples'},
            },
            'required': ['dimension', 'valence'],
        },
    },
    {
        'name': 'get_counterexamples',
        'description': 'Find sermons where a typically weak dimension was unusually strong — what did Bryan do differently? Use when Bryan is stuck on a dimension and needs to see what works.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'dimension': {'type': 'string', 'description': 'The dimension to find counterexamples for'},
            },
            'required': ['dimension'],
        },
    },
    {
        'name': 'get_coaching_insights',
        'description': 'Get structured insights from recent coaching conversations. These are Bryan-confirmed notes about his preaching patterns and growth edges. Use during sermon construction when a coaching dimension is relevant.',
        'input_schema': {
            'type': 'object',
            'properties': {},
            'required': [],
        },
    },
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge_tools.py -v -p no:base_url`
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_tools.py tools/workbench/tests/test_coaching_bridge_tools.py
git commit -m "feat: add 5 coaching bridge tools to companion TOOL_DEFINITIONS"
```

---

### Task 4: Modify `build_study_prompt()` to include coaching context

**Files:**
- Modify: `tools/workbench/companion_agent.py:459`
- Test: `tools/workbench/tests/test_coaching_bridge.py` (append)

- [ ] **Step 1: Write failing test**

Append to `tests/test_coaching_bridge.py`:

```python
from companion_agent import build_study_prompt


def test_build_study_prompt_includes_coaching_section():
    prompt = build_study_prompt(
        passage='Romans 8:1-11', genre='epistle',
        session_elapsed_seconds=3600,
        coaching_context='## Coaching Memory\n\nDimension: application_specificity',
    )
    assert 'Coaching Memory' in prompt
    assert 'application_specificity' in prompt


def test_build_study_prompt_omits_coaching_when_empty():
    prompt = build_study_prompt(
        passage='Romans 8:1-11', genre='epistle',
        session_elapsed_seconds=3600,
        coaching_context='',
    )
    assert 'Coaching Memory' not in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py::test_build_study_prompt_includes_coaching_section -v -p no:base_url`
Expected: FAIL — `build_study_prompt()` doesn't accept `coaching_context`

- [ ] **Step 3: Add `coaching_context` parameter to `build_study_prompt()`**

In `companion_agent.py`, modify the function signature at line 459:

```python
def build_study_prompt(passage, genre, session_elapsed_seconds,
                       outline_summary='', conversation_history_summary='',
                       card_work_summary='', coaching_context=''):
```

Then, inside the function's f-string, add `{coaching_context}` after the tools section and before the behavioral constraints section. Find the section that starts with `## Behavioral Constraints` and insert before it:

```python
{coaching_context}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url`
Expected: ALL PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_agent.py tools/workbench/tests/test_coaching_bridge.py
git commit -m "feat: add coaching_context parameter to build_study_prompt()"
```

---

### Task 5: Wire coaching context into `stream_study_response()` and add tool dispatch

**Files:**
- Modify: `tools/workbench/companion_agent.py:642-730`
- Modify: `tools/workbench/app.py:1079` (study_discuss route)

- [ ] **Step 1: Modify `stream_study_response()` to load and pass coaching context**

In `companion_agent.py`, inside `stream_study_response()` (around line 692-698 where the prompt is built), add coaching context loading:

```python
    # Load coaching context for the study prompt
    from coaching_bridge import load_active_commitment, load_coaching_insights, build_coaching_prompt_section
    commitment = load_active_commitment(db)
    insights = load_coaching_insights(db)
    coaching_context = build_coaching_prompt_section(commitment, insights)
```

Then pass it to `build_study_prompt()`:

```python
    system_prompt = build_study_prompt(
        passage=session['passage_ref'],
        genre=session['genre'],
        session_elapsed_seconds=elapsed,
        outline_summary=outline_summary,
        card_work_summary=card_work_summary,
        coaching_context=coaching_context,
    )
```

- [ ] **Step 2: Add coaching tool dispatch to `execute_tool()` in study streaming**

In `companion_agent.py`, find the `execute_tool()` function used by `stream_study_response()` (imported from `companion_tools.py`). The coaching tools need to be dispatched. In `companion_tools.py`, add to the `execute_tool()` function:

```python
    if tool_name == 'get_active_commitment':
        from coaching_bridge import load_active_commitment
        return load_active_commitment(session_context['db']) or {'active': False}
    if tool_name == 'get_sermon_patterns':
        from sermon_coach_tools import get_sermon_patterns
        return get_sermon_patterns(session_context['db'],
                                   window_days=tool_input.get('window_days', 90))
    if tool_name == 'get_representative_moments':
        from meta_coach_tools import get_representative_moments
        return {'moments': get_representative_moments(
            session_context['db'],
            dimension=tool_input['dimension'],
            valence=tool_input['valence'],
        )}
    if tool_name == 'get_counterexamples':
        from meta_coach_tools import get_counterexamples
        return {'counterexamples': get_counterexamples(
            session_context['db'],
            dimension=tool_input['dimension'],
        )}
    if tool_name == 'get_coaching_insights':
        from coaching_bridge import load_coaching_insights
        return {'insights': load_coaching_insights(session_context['db'])}
```

- [ ] **Step 3: Run the full test suite to verify nothing broke**

Run: `cd tools/workbench && python3 -m pytest tests/ -v -p no:base_url -k "companion or coaching" --no-header`
Expected: ALL PASSED

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/companion_agent.py tools/workbench/companion_tools.py
git commit -m "feat: wire coaching context + tool dispatch into study companion"
```

---

### Task 6: Wire `linked_session_id` into per-sermon coach

**Files:**
- Modify: `tools/workbench/sermon_coach_agent.py:191-220`
- Test: `tools/workbench/tests/test_coaching_bridge.py` (append)

- [ ] **Step 1: Write failing test**

Append to `tests/test_coaching_bridge.py`:

```python
def test_coach_loads_linked_session_id(db):
    conn = db._conn()
    # Create a sermon
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, preach_date, duration_seconds, bible_text_raw,
                              transcript_text, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-link', 'bcast', 'Test Sermon', 'sermon', 'review_ready',
                '2026-04-12', 2322, 'Romans 8:1-11', 'transcript text here',
                datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Create a session
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('Romans 8:1-11', 66, 8, 1, 11, 'epistle', 'prayer', 900,
                datetime('now'), datetime('now'))
    """)
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Link them
    conn.execute("""
        INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at)
        VALUES (?, ?, 'active', 'auto', 'tier1', datetime('now'))
    """, (sermon_id, session_id))
    conn.commit()
    conn.close()

    # The coach should find the linked session
    from sermon_coach_agent import _load_sermon_context
    ctx = _load_sermon_context(db, sermon_id)
    assert ctx.get('linked_session_id') == session_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py::test_coach_loads_linked_session_id -v -p no:base_url`
Expected: FAIL — `_load_sermon_context` doesn't exist or doesn't return `linked_session_id`

- [ ] **Step 3: Extract `_load_sermon_context()` and wire `linked_session_id`**

In `sermon_coach_agent.py`, extract the sermon context loading from `stream_coach_response()` (lines 195-220) into a helper:

```python
def _load_sermon_context(db, sermon_id: int) -> dict:
    """Load sermon metadata + linked session for the coach system prompt."""
    conn = db._conn()
    sermon_row = conn.execute("""
        SELECT id, bible_text_raw, preach_date, duration_seconds, transcript_text
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    if not sermon_row:
        conn.close()
        return {}

    ctx = {
        'passage': sermon_row[1],
        'preach_date': sermon_row[2],
        'duration_sec': sermon_row[3] or 0,
        'transcript': sermon_row[4] or '',
    }

    # Find linked prep session
    link_row = conn.execute("""
        SELECT sl.session_id FROM sermon_links sl
        WHERE sl.sermon_id = ? AND sl.link_status = 'active'
        ORDER BY sl.created_at DESC LIMIT 1
    """, (sermon_id,)).fetchone()
    if link_row:
        ctx['linked_session_id'] = link_row[0]

    conn.close()
    return ctx
```

Then update `stream_coach_response()` to use it instead of inline queries.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url`
Expected: ALL PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/sermon_coach_agent.py tools/workbench/tests/test_coaching_bridge.py
git commit -m "fix: wire linked_session_id into sermon coach context"
```

---

### Task 7: Add coaching insight capture to both coaches

**Files:**
- Modify: `tools/workbench/sermon_coach_agent.py` (system prompt)
- Modify: `tools/workbench/meta_coach_agent.py` (system prompt)
- Modify: `tools/workbench/app.py` (REST endpoint)
- Test: `tools/workbench/tests/test_coaching_bridge.py` (append)

- [ ] **Step 1: Write failing test for the REST endpoint**

Append to `tests/test_coaching_bridge.py`:

```python
from app import app


def test_create_coaching_insight_route(db, monkeypatch):
    import tempfile, os
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    monkeypatch.setenv('COMPANION_DB_PATH', db_path)
    import app as app_mod
    app_mod._db_instance = None
    app.config['TESTING'] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['authenticated'] = True
        from companion_db import CompanionDB
        test_db = CompanionDB(db_path)
        test_db.init_db()

        resp = c.post('/sermons/coaching-insight', json={
            'dimension_key': 'application_specificity',
            'summary': 'Slow down at application moments',
            'applies_when': ['outline construction'],
            'avoid_when': ['textual observation'],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'id' in data

        conn = test_db._conn()
        row = conn.execute("SELECT summary FROM coaching_insights WHERE id = ?",
                           (data['id'],)).fetchone()
        conn.close()
        assert row[0] == 'Slow down at application moments'
    os.unlink(db_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py::test_create_coaching_insight_route -v -p no:base_url`
Expected: FAIL — route doesn't exist

- [ ] **Step 3: Add REST endpoint for coaching insight creation**

In `app.py`, add to the `sermons_bp` blueprint:

```python
@sermons_bp.route('/coaching-insight', methods=['POST'])
def create_coaching_insight():
    import json as _json
    db = get_db()
    data = request.get_json()
    conn = db._conn()
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when,
             source_sermon_id, source_conversation_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        data.get('dimension_key'),
        data['summary'],
        _json.dumps(data.get('applies_when', [])),
        _json.dumps(data.get('avoid_when', [])),
        data.get('source_sermon_id'),
        data.get('source_conversation_id'),
    ))
    insight_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({'id': insight_id, 'status': 'saved'}), 201
```

- [ ] **Step 4: Add insight proposal instruction to both coach system prompts**

In `sermon_coach_agent.py`, add to the behavioral constraints section of `build_system_prompt()`:

```python
- When a conversation produces a refined coaching insight that would help future
  sermon prep, propose: "Should I save this as a coaching note for your future
  prep?" If Bryan confirms, the frontend will call the save endpoint. Frame the
  insight as: what dimension it relates to, a 1-2 sentence summary, and when it
  applies vs when to avoid it.
```

In `meta_coach_agent.py`, add the same instruction to the behavioral constraints in `build_meta_system_prompt()`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge.py -v -p no:base_url`
Expected: ALL PASSED

- [ ] **Step 6: Commit**

```bash
git add tools/workbench/app.py tools/workbench/sermon_coach_agent.py tools/workbench/meta_coach_agent.py tools/workbench/tests/test_coaching_bridge.py
git commit -m "feat: coaching insight capture — REST endpoint + coach prompt instructions"
```

---

### Task 8: Integration test — full bridge flow

**Files:**
- Create: `tools/workbench/tests/test_coaching_bridge_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tools/workbench/tests/test_coaching_bridge_integration.py
"""End-to-end test: coaching data flows from coach side into study companion prompt."""
import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from coaching_bridge import (
    load_active_commitment, load_coaching_insights,
    build_coaching_prompt_section, record_coaching_exposure,
    check_coaching_exposure,
)
from companion_agent import build_study_prompt


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = CompanionDB(path)
    d.init_db()
    yield d
    os.unlink(path)


def test_full_bridge_flow(db):
    conn = db._conn()
    # 1. Create an active commitment (simulates meta-coach output)
    conn.execute("""
        INSERT INTO coaching_commitments
            (dimension_key, practice_experiment, target_sermons, status, created_at)
        VALUES ('application_specificity', 'Pause 15-20 seconds at application moments',
                2, 'active', datetime('now'))
    """)
    # 2. Create a coaching insight (simulates per-sermon coach output)
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES ('application_specificity',
                'Application is present but diffuse — slow down at moments where text touches listener life',
                '["outline construction", "application development"]',
                '["textual observation", "word study"]',
                datetime('now'))
    """)
    # 3. Create a study session
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('Romans 3:1-8', 66, 3, 1, 8, 'epistle', 'sermon_construction', 900,
                datetime('now'), datetime('now'))
    """)
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    # 4. Load coaching data (as stream_study_response would)
    commitment = load_active_commitment(db)
    insights = load_coaching_insights(db)
    coaching_section = build_coaching_prompt_section(commitment, insights)

    # 5. Build the study prompt with coaching context
    prompt = build_study_prompt(
        passage='Romans 3:1-8', genre='epistle',
        session_elapsed_seconds=5400,
        coaching_context=coaching_section,
    )

    # Verify coaching data is in the prompt
    assert 'application_specificity' in prompt
    assert 'Pause 15-20 seconds' in prompt
    assert 'diffuse' in prompt
    assert 'ESCALATION LADDER' in prompt
    assert 'ANTI-NAGGING' in prompt

    # 6. Test exposure tracking
    assert check_coaching_exposure(db, session_id, 'application_specificity') is None
    record_coaching_exposure(db, session_id, 'application_specificity',
                             escalation_level=2, response='accepted')
    exp = check_coaching_exposure(db, session_id, 'application_specificity')
    assert exp['escalation_level'] == 2
    assert exp['response'] == 'accepted'


def test_bridge_degrades_gracefully_with_no_coaching_data(db):
    """When no coaching data exists, the prompt should have no coaching section."""
    prompt = build_study_prompt(
        passage='Genesis 1:1-5', genre='narrative',
        session_elapsed_seconds=1800,
        coaching_context='',
    )
    assert 'Coaching Memory' not in prompt
    assert 'ESCALATION' not in prompt
```

- [ ] **Step 2: Run integration tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_coaching_bridge_integration.py -v -p no:base_url`
Expected: 2 PASSED

- [ ] **Step 3: Run full test suite for regression**

Run: `cd tools/workbench && python3 -m pytest tests/ -v -p no:base_url -k "coaching or companion_agent or companion_db or companion_tools" --no-header`
Expected: ALL PASSED

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/tests/test_coaching_bridge_integration.py
git commit -m "test: coaching bridge integration — full flow + graceful degradation"
```

---

## Self-Review

**Spec coverage:**
- Layer 1 (active commitment in prompt): Task 2 (`build_coaching_prompt_section`) + Task 4 (wired into `build_study_prompt`)
- Layer 2 (tools + retrieval policy): Task 3 (tool definitions) + Task 5 (dispatch + wiring) + Task 2 (retrieval policy in prompt section)
- Layer 3 (session memory + anti-nagging): Task 1 (schema) + Task 2 (exposure tracking functions) + Task 2 (anti-nagging rules in prompt)
- Coaching insights capture: Task 1 (schema) + Task 7 (REST endpoint + coach prompt instructions)
- linked_session_id fix: Task 6
- Transition question: Task 2 (in retrieval policy text)
- Escalation ladder: Task 2 (in prompt section)
- Graceful degradation: Task 2 (`build_coaching_prompt_section` returns empty string) + Task 8 (tested)

**Placeholder scan:** No TBD/TODO found. All code blocks complete.

**Type consistency:** `load_active_commitment` returns `Optional[dict]` consistently. `load_coaching_insights` returns `list[dict]` consistently. `build_coaching_prompt_section` accepts both and returns `str`. Tool dispatch uses same function signatures across Task 3 (definitions) and Task 5 (dispatch).
