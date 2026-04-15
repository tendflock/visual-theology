import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermonaudio_sync import upsert_sermon
from sermon_matcher import apply_match_decision_for_sermon


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
    sid = fresh_db.create_session('Romans 8:1-11', 66, 8, 1, 11, 'epistle')
    fresh_db.save_card_response(sid, 'prayer', 1, 'praying')
    conn = fresh_db._conn()
    row1 = conn.execute("SELECT last_homiletical_activity_at FROM sessions WHERE id=?", (sid,)).fetchone()
    assert row1[0] is None
    fresh_db.save_card_response(sid, 'exegetical_point', 2, 'the big idea')
    row2 = conn.execute("SELECT last_homiletical_activity_at FROM sessions WHERE id=?", (sid,)).fetchone()
    conn.close()
    assert row2[0] is not None


def test_save_message_homiletical_phase_bumps_timestamp(fresh_db):
    sid = fresh_db.create_session('Romans 8:1-11', 66, 8, 1, 11, 'epistle')
    fresh_db.save_message(sid, 'sermon_construction', 'assistant', 'here is the outline')
    conn = fresh_db._conn()
    row = conn.execute("SELECT last_homiletical_activity_at FROM sessions WHERE id=?", (sid,)).fetchone()
    conn.close()
    assert row[0] is not None


def test_auto_match_creates_active_link_after_homiletical_activity(fresh_db):
    sid = fresh_db.create_session('Romans 8:1-11', 66, 8, 1, 11, 'epistle')
    conn = fresh_db._conn()
    conn.execute("UPDATE sessions SET created_at = '2026-04-06 09:00:00', updated_at = '2026-04-09 12:00:00' WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    fresh_db.save_card_response(sid, 'exegetical_point', 1, 'the big idea')
    conn = fresh_db._conn()
    conn.execute("UPDATE sessions SET last_homiletical_activity_at = '2026-04-09 12:00:00' WHERE id = ?", (sid,))
    conn.commit()
    upsert_sermon(conn, _remote(sid='sa-rematch-1'))
    conn.commit()
    sermon_id = conn.execute("SELECT id FROM sermons WHERE sermonaudio_id='sa-rematch-1'").fetchone()[0]
    conn.close()
    decision = apply_match_decision_for_sermon(fresh_db, sermon_id)
    assert decision.action == 'auto_link'
    conn = fresh_db._conn()
    link = conn.execute(
        "SELECT link_status, link_source, session_id FROM sermon_links WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    conn.close()
    # link may be a sqlite3.Row — compare via tuple conversion
    assert tuple(link) == ('active', 'auto', sid)
