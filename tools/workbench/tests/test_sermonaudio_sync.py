import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermonaudio_sync import (
    classify, compute_hashes, upsert_sermon,
    SERMON_EVENT_TYPES, DEVOTIONAL_EVENT_TYPES, BRYAN_SPEAKER_NAME,
)


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
        sermon_id='sa-001',
        broadcaster_id='bcast',
        title='Romans 8:1-11',
        speaker_name='Bryan Schneider',
        event_type='Sunday Service',
        series='Romans',
        preach_date=dt.date(2026, 4, 12),
        publish_date=dt.date(2026, 4, 12),
        duration=2400,
        bible_text='Romans 8:1-11',
        audio_url='https://sa.example/sa-001.mp3',
        transcript='...' * 500,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


# classify

def test_classify_sermon_by_eventtype():
    cls, reason = classify(_remote())
    assert cls == 'sermon'
    assert 'Sunday Service' in reason


def test_classify_skipped_when_speaker_not_bryan():
    cls, reason = classify(_remote(speaker_name='Guest Preacher'))
    assert cls == 'skipped'
    assert 'speaker' in reason


def test_classify_skipped_by_eventtype_devotional():
    cls, reason = classify(_remote(event_type='Daily Devotional'))
    assert cls == 'skipped'
    assert 'Daily Devotional' in reason


def test_classify_heuristic_fallback_sunday_plus_duration():
    cls, reason = classify(_remote(event_type='Revival Service', duration=1800))
    assert cls == 'sermon'
    assert 'heuristic' in reason


def test_classify_unknown_eventtype_short_duration_skipped():
    cls, reason = classify(_remote(event_type='Wedding', duration=600, preach_date=dt.date(2026, 4, 10)))
    assert cls == 'skipped'


# compute_hashes

def test_compute_hashes_stable_for_same_input():
    r1 = _remote()
    r2 = _remote()
    h1a, t1a = compute_hashes(r1)
    h2a, t2a = compute_hashes(r2)
    assert h1a == h2a
    assert t1a == t2a


def test_compute_hashes_changes_when_metadata_changes():
    r1 = _remote()
    r2 = _remote(title='Different Title')
    h1, _ = compute_hashes(r1)
    h2, _ = compute_hashes(r2)
    assert h1 != h2


def test_compute_hashes_changes_when_transcript_changes():
    r1 = _remote()
    r2 = _remote(transcript='different transcript content')
    _, t1 = compute_hashes(r1)
    _, t2 = compute_hashes(r2)
    assert t1 != t2


def test_compute_hashes_transcript_none_yields_none():
    r = _remote(transcript=None)
    _, tx_hash = compute_hashes(r)
    assert tx_hash is None


# upsert_sermon

def test_upsert_inserts_new_sermon(fresh_db):
    conn = fresh_db._conn()
    result = upsert_sermon(conn, _remote())
    conn.commit()
    assert result == 'new'
    row = conn.execute("SELECT sermonaudio_id, classified_as, source_version FROM sermons").fetchone()
    assert row[0] == 'sa-001'
    assert row[1] == 'sermon'
    assert row[2] == 1
    conn.close()


def test_upsert_noop_on_unchanged(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote())
    conn.commit()
    result = upsert_sermon(conn, _remote())
    conn.commit()
    assert result == 'noop'
    row = conn.execute("SELECT source_version FROM sermons").fetchone()
    assert row[0] == 1
    conn.close()


def test_upsert_updates_and_bumps_source_version(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote())
    conn.commit()
    result = upsert_sermon(conn, _remote(title='Updated Title'))
    conn.commit()
    assert result == 'updated'
    row = conn.execute("SELECT source_version, title FROM sermons").fetchone()
    assert row[0] == 2
    assert row[1] == 'Updated Title'
    conn.close()
