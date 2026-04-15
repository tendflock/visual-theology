import os
import sys
import tempfile
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
    app.config['TESTING'] = True
    import app as app_mod
    app_mod._db_instance = None
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['authenticated'] = True
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
