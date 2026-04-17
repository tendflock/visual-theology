import json
import os
import sqlite3
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from coaching_bridge import (
    load_active_commitment,
    load_coaching_insights,
    record_coaching_exposure,
    check_coaching_exposure,
    build_coaching_prompt_section,
)


# Override pytest-base-url's autouse _verify_url fixture so these DB-only
# tests don't trigger conftest.py's Flask-server `base_url` fixture (which
# hard-exits if port 5111 is in use).
@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


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


def test_coaching_insights_table_exists(fresh_db):
    tables = _tables(fresh_db)
    assert 'coaching_insights' in tables


def test_session_coaching_exposure_table_exists(fresh_db):
    tables = _tables(fresh_db)
    assert 'session_coaching_exposure' in tables


def test_coaching_insights_insert_and_query(fresh_db):
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, ('illustration_density', 'Use more concrete illustrations',
          'When audience attention dips', 'When making tight exegetical arguments',
          '2026-04-15T00:00:00+00:00'))
    conn.commit()
    row = conn.execute(
        "SELECT dimension_key, summary, applies_when, avoid_when FROM coaching_insights WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 'illustration_density'
    assert row[1] == 'Use more concrete illustrations'
    assert row[2] == 'When audience attention dips'
    assert row[3] == 'When making tight exegetical arguments'


def test_session_coaching_exposure_unique_per_dimension(fresh_db):
    # Create a session to satisfy the FK
    session_id = fresh_db.create_session('John 3:16', 'John', 3, 16, 16, 'gospel')
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO session_coaching_exposure
            (session_id, dimension_key, escalation_level, response, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, 'illustration_density', 1, 'pending', '2026-04-15T00:00:00+00:00'))
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("""
            INSERT INTO session_coaching_exposure
                (session_id, dimension_key, escalation_level, response, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, 'illustration_density', 2, 'pending', '2026-04-15T00:00:01+00:00'))
    conn.close()


# ── Bridge helper tests ──────────────────────────────────────────────

def test_load_active_commitment_returns_none_when_empty(fresh_db):
    result = load_active_commitment(fresh_db)
    assert result is None


def test_load_active_commitment_returns_dict_when_present(fresh_db):
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO coaching_commitments
            (dimension_key, practice_experiment, target_sermons, status, created_at)
        VALUES (?, ?, ?, 'active', ?)
    """, ('application_specificity',
          'Identify two moments where the text touches the listener.',
          2, '2026-04-15T00:00:00+00:00'))
    conn.commit()
    conn.close()

    result = load_active_commitment(fresh_db)
    assert result is not None
    assert result['dimension_key'] == 'application_specificity'
    assert 'two moments' in result['practice_experiment']
    assert result['target_sermons'] == 2
    assert result['created_at'] == '2026-04-15T00:00:00+00:00'


def test_load_coaching_insights_returns_non_superseded(fresh_db):
    conn = fresh_db._conn()
    # Insert first insight
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, ('application_specificity',
          'Old insight about application.',
          '["outline construction"]',
          '["textual observation"]',
          '2026-04-14T00:00:00+00:00'))
    # Insert second insight that supersedes the first
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, ('application_specificity',
          'Updated insight about application.',
          '["outline construction", "application development"]',
          '["textual observation"]',
          '2026-04-15T00:00:00+00:00'))
    # Mark first as superseded by second (id=2 supersedes id=1)
    conn.execute("UPDATE coaching_insights SET superseded_by = 2 WHERE id = 1")
    conn.commit()
    conn.close()

    results = load_coaching_insights(fresh_db)
    assert len(results) == 1
    assert results[0]['summary'] == 'Updated insight about application.'
    assert results[0]['applies_when'] == ['outline construction', 'application development']
    assert results[0]['avoid_when'] == ['textual observation']
    assert results[0]['id'] == 2


def test_record_and_check_exposure(fresh_db):
    session_id = fresh_db.create_session('Romans 8:1-4', 66, 8, 1, 4, 'epistle')

    # Initially no exposure
    result = check_coaching_exposure(fresh_db, session_id, 'burden_clarity')
    assert result is None

    # Record exposure
    record_coaching_exposure(fresh_db, session_id, 'burden_clarity', 2, 'pending')

    # Now it should be present
    result = check_coaching_exposure(fresh_db, session_id, 'burden_clarity')
    assert result is not None
    assert result['escalation_level'] == 2
    assert result['response'] == 'pending'


def test_build_coaching_prompt_section_with_commitment(fresh_db):
    commitment = {
        'dimension_key': 'application_specificity',
        'practice_experiment': 'Identify two moments where the text touches the listener.',
        'target_sermons': 2,
        'created_at': '2026-04-15T00:00:00+00:00',
    }
    insights = [
        {
            'id': 1,
            'dimension_key': 'application_specificity',
            'summary': 'Application is present but diffuse.',
            'applies_when': ['outline construction', 'application development'],
            'avoid_when': ['textual observation'],
            'source_sermon_id': None,
            'created_at': '2026-04-15T00:00:00+00:00',
        }
    ]

    section = build_coaching_prompt_section(commitment, insights)

    # Contains commitment info
    assert 'application_specificity' in section
    assert 'two moments' in section
    # Contains retrieval policy keywords
    assert 'Retrieval Policy' in section or 'WHEN TO CONSULT' in section
    # Contains escalation ladder
    assert 'SILENT SHAPING' in section
    assert 'DIAGNOSTIC CHECK' in section
    assert 'ESCALATION LADDER' in section or 'escalation' in section.lower()
    # Contains anti-nagging rules
    assert 'RELEVANCE GATE' in section or 'ANTI-NAGGING' in section
    # Contains insight info
    assert 'diffuse' in section


def test_build_coaching_prompt_section_empty_when_no_data(fresh_db):
    section = build_coaching_prompt_section(None, [])
    assert section == ''


# ── build_study_prompt coaching_context tests ────────────────────────

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


# ── REST endpoint tests ──────────────────────────────────────────────

def test_create_coaching_insight_route():
    import tempfile, os
    from app import app, get_db
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    os.environ['COMPANION_DB_PATH'] = db_path
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


# ── _load_sermon_context tests ──────────────────────────────────────

def test_coach_loads_linked_session_id(fresh_db):
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, preach_date, duration_seconds, bible_text_raw,
                              transcript_text, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-link-test', 'bcast', 'Test Linked', 'sermon', 'review_ready',
                '2026-04-12', 2322, 'Romans 8:1-11', 'transcript here',
                datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('Romans 8:1-11', 66, 8, 1, 11, 'epistle', 'prayer', 900,
                datetime('now'), datetime('now'))
    """)
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at)
        VALUES (?, ?, 'active', 'auto', 'tier1', datetime('now'))
    """, (sermon_id, session_id))
    conn.commit()
    conn.close()
    from sermon_coach_agent import _load_sermon_context
    ctx = _load_sermon_context(fresh_db, sermon_id)
    assert ctx.get('linked_session_id') == session_id


def test_coach_context_omits_linked_session_when_no_link(fresh_db):
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, preach_date, duration_seconds, bible_text_raw,
                              transcript_text, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-nolink-test', 'bcast', 'Test No Link', 'sermon', 'review_ready',
                '2026-04-12', 1800, 'John 3:16', 'some transcript',
                datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    from sermon_coach_agent import _load_sermon_context
    ctx = _load_sermon_context(fresh_db, sermon_id)
    assert ctx is not None
    assert 'linked_session_id' not in ctx
    assert ctx['passage'] == 'John 3:16'
    assert ctx['duration_sec'] == 1800
