import os
import sqlite3
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB


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
    # Two distinct sessions
    conn.execute("INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre, current_phase, timer_remaining_seconds, created_at, updated_at) VALUES ('Romans 8:1-11', 45, 8, 1, 11, 'epistle', 'prayer', 900, datetime('now'), datetime('now'))")
    session_a = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre, current_phase, timer_remaining_seconds, created_at, updated_at) VALUES ('Romans 8:1-11', 45, 8, 1, 11, 'epistle', 'prayer', 900, datetime('now'), datetime('now'))")
    session_b = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    assert session_a != session_b
    # One sermon
    conn.execute("INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as, sync_status, last_state_change_at, first_synced_at, last_synced_at, created_at, updated_at) VALUES ('rcf001', 'bcast', 'Test', 'sermon', 'review_ready', datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))")
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # First active link to session_a — should succeed
    conn.execute("INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at) VALUES (?, ?, 'active', 'auto', 'tier1', datetime('now'))", (sermon_id, session_a))
    conn.commit()
    # Second active link to session_b — should fail due to partial unique index
    # (fires at INSERT time, not commit time — no conn.commit() needed)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO sermon_links (sermon_id, session_id, link_status, link_source, match_reason, created_at) VALUES (?, ?, 'active', 'auto', 'tier1-other-session', datetime('now'))", (sermon_id, session_b))
    conn.close()


def test_init_db_is_idempotent(fresh_db):
    """Calling init_db() a second time on an already-initialized DB must not crash
    and must not duplicate the sessions.last_homiletical_activity_at column."""
    fresh_db.init_db()  # Second call — should be a no-op due to IF NOT EXISTS + PRAGMA guard
    cols = _columns(fresh_db, 'sessions')
    assert 'last_homiletical_activity_at' in cols
    # Ensure we only have ONE last_homiletical_activity_at column
    conn = fresh_db._conn()
    rows = conn.execute("PRAGMA table_info(sessions)").fetchall()
    count = sum(1 for r in rows if r[1] == 'last_homiletical_activity_at')
    conn.close()
    assert count == 1
