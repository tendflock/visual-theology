import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermonaudio_sync import run_sync_with_client


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


class MockSAClient:
    """In-memory SermonAudio client for tests."""
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
    assert result['sermons_new'] == 2
    conn = fresh_db._conn()
    sermon_count = conn.execute("SELECT COUNT(*) FROM sermons WHERE classified_as = 'sermon'").fetchone()[0]
    skipped_count = conn.execute("SELECT COUNT(*) FROM sermons WHERE classified_as = 'skipped'").fetchone()[0]
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
