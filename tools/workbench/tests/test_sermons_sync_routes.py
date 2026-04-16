import os
import sys
import tempfile
import json
from types import SimpleNamespace
import datetime as dt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, get_db


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


@pytest.fixture
def client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    monkeypatch.setenv('COMPANION_DB_PATH', db_path)
    import app as app_mod
    app_mod._db_instance = None
    app.config['TESTING'] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['authenticated'] = True
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

    import app as app_mod
    monkeypatch.setattr(app_mod, '_make_sermonaudio_client', lambda: MockClient())
    resp = c.post('/sermons/sync')
    assert resp.status_code == 202
    data = resp.get_json()
    assert 'run_id' in data
    conn = db._conn()
    count = conn.execute("SELECT COUNT(*) FROM sermons").fetchone()[0]
    conn.close()
    assert count == 1


def test_manual_link_creates_active_row(client):
    c, db = client
    conn = db._conn()
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
    assert tuple(row) == ('active', 'manual')


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
