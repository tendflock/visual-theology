import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermon_coach_tools import (
    get_sermon_review, get_sermon_flags, get_transcript_full,
    get_prep_session_full, pull_historical_sermons, get_sermon_patterns,
)


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


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
    db, sermon_id = stocked_db
    text = get_transcript_full(db, sermon_id, start_sec=0, end_sec=100)
    assert text is not None


def test_get_prep_session_full_returns_none_when_no_link(stocked_db):
    db, sermon_id = stocked_db
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
