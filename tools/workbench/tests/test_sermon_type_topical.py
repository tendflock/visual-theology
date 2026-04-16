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


def _remote(bible_text, **overrides):
    base = dict(
        sermon_id='sa-x',
        broadcaster_id='bcast',
        title='Test',
        speaker_name='Bryan Schneider',
        event_type='Sunday Service',
        series='Test',
        preach_date=dt.date(2026, 4, 12),
        publish_date=dt.date(2026, 4, 12),
        duration=2400,
        bible_text=bible_text,
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome. ' * 200,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_single_passage_writes_one_passage_row(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('Romans 8:1-11', sermon_id='sa-1'))
    conn.commit()
    rows = conn.execute(
        "SELECT rank, chapter_start, chapter_end, verse_start, verse_end "
        "FROM sermon_passages WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-1')"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert tuple(rows[0]) == (1, 8, 8, 1, 11)


def test_multi_range_writes_two_passage_rows(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('Romans 8:1-11; Romans 9:1-5', sermon_id='sa-2'))
    conn.commit()
    rows = conn.execute(
        "SELECT rank, chapter_start, verse_start, verse_end FROM sermon_passages "
        "WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-2') "
        "ORDER BY rank"
    ).fetchall()
    conn.close()
    assert len(rows) == 2
    assert tuple(rows[0]) == (1, 8, 1, 11)
    assert tuple(rows[1]) == (2, 9, 1, 5)


def test_unparseable_passage_marks_topical_and_writes_no_rows(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('The Ten Commandments', sermon_id='sa-3'))
    conn.commit()
    sermon = conn.execute(
        "SELECT sermon_type, match_status FROM sermons WHERE sermonaudio_id='sa-3'"
    ).fetchone()
    passage_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_passages WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-3')"
    ).fetchone()[0]
    conn.close()
    assert sermon[0] == 'topical'
    assert sermon[1] == 'topical_no_match'
    assert passage_count == 0


def test_update_deletes_old_passages_and_writes_new(fresh_db):
    conn = fresh_db._conn()
    upsert_sermon(conn, _remote('Romans 8:1-11', sermon_id='sa-4'))
    conn.commit()
    upsert_sermon(conn, _remote('Romans 9:1-5', sermon_id='sa-4', title='Updated'))
    conn.commit()
    rows = conn.execute(
        "SELECT chapter_start, verse_start FROM sermon_passages "
        "WHERE sermon_id = (SELECT id FROM sermons WHERE sermonaudio_id='sa-4')"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert tuple(rows[0]) == (9, 1)
