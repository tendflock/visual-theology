"""Source change flow test.

Verifies that source changes (transcript update) bump source_version and push
state back to analysis_pending, and that unchanged source is a noop.
"""

import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermonaudio_sync import upsert_sermon


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
    upsert_sermon(conn, _remote(transcript='first version'))
    conn.commit()
    conn.execute("UPDATE sermons SET sync_status = 'review_ready' WHERE sermonaudio_id='sa-1'")
    conn.commit()
    upsert_sermon(conn, _remote(transcript='second version'))
    conn.commit()
    row = conn.execute("SELECT source_version, sync_status FROM sermons WHERE sermonaudio_id='sa-1'").fetchone()
    conn.close()
    assert row[0] == 2
    assert row[1] in ('analysis_pending', 'transcript_ready')


def test_unchanged_source_is_noop(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote(transcript='same'))
    upsert_sermon(conn, _remote(transcript='same'))
    row = conn.execute("SELECT source_version FROM sermons").fetchone()
    conn.close()
    assert row[0] == 1
