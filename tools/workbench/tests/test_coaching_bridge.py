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


def test_coaching_insights_table_exists(fresh_db):
    tables = _tables(fresh_db)
    assert 'coaching_insights' in tables


def test_session_coaching_exposure_table_exists(fresh_db):
    tables = _tables(fresh_db)
    assert 'session_coaching_exposure' in tables


def test_coaching_insights_insert_and_query(fresh_db):
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, ('illustration_density', 'Use more concrete illustrations',
          'When audience attention dips', 'When making tight exegetical arguments',
          '2026-04-15T00:00:00+00:00'))
    conn.commit()
    row = conn.execute(
        "SELECT dimension_key, summary, applies_when, avoid_when FROM coaching_insights WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 'illustration_density'
    assert row[1] == 'Use more concrete illustrations'
    assert row[2] == 'When audience attention dips'
    assert row[3] == 'When making tight exegetical arguments'


def test_session_coaching_exposure_unique_per_dimension(fresh_db):
    # Create a session to satisfy the FK
    session_id = fresh_db.create_session('John 3:16', 'John', 3, 16, 16, 'gospel')
    conn = fresh_db._conn()
    conn.execute("""
        INSERT INTO session_coaching_exposure
            (session_id, dimension_key, escalation_level, response, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, 'illustration_density', 1, 'pending', '2026-04-15T00:00:00+00:00'))
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("""
            INSERT INTO session_coaching_exposure
                (session_id, dimension_key, escalation_level, response, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, 'illustration_density', 2, 'pending', '2026-04-15T00:00:01+00:00'))
    conn.close()
