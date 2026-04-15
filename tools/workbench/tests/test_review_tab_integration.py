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
def client_with_linked_session(monkeypatch):
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
        # The existing study_session_view route uses the `companion_db` global,
        # not get_db(). Point the global at the same temp DB so the route sees
        # the test data we insert below.
        app_mod.companion_db = db
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
    resp = c.get(f'/study/session/{sid}')
    assert resp.status_code == 200
    # Review content must render
    assert b'Impact' in resp.data
    assert b'change it' in resp.data
