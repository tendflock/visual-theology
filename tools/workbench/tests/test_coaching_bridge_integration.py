"""End-to-end test: coaching data flows from coach side into study companion prompt."""
import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from coaching_bridge import (
    load_active_commitment, load_coaching_insights,
    build_coaching_prompt_section, record_coaching_exposure,
    check_coaching_exposure,
)
from companion_agent import build_study_prompt


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = CompanionDB(path)
    d.init_db()
    yield d
    os.unlink(path)


def test_full_bridge_flow(db):
    conn = db._conn()
    # 1. Create an active commitment (simulates meta-coach output)
    conn.execute("""
        INSERT INTO coaching_commitments
            (dimension_key, practice_experiment, target_sermons, status, created_at)
        VALUES ('application_specificity', 'Pause 15-20 seconds at application moments',
                2, 'active', datetime('now'))
    """)
    # 2. Create a coaching insight (simulates per-sermon coach output)
    conn.execute("""
        INSERT INTO coaching_insights
            (dimension_key, summary, applies_when, avoid_when, created_at)
        VALUES ('application_specificity',
                'Application is present but diffuse — slow down at moments where text touches listener life',
                '["outline construction", "application development"]',
                '["textual observation", "word study"]',
                datetime('now'))
    """)
    # 3. Create a study session
    conn.execute("""
        INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                              current_phase, timer_remaining_seconds, created_at, updated_at)
        VALUES ('Romans 3:1-8', 66, 3, 1, 8, 'epistle', 'sermon_construction', 900,
                datetime('now'), datetime('now'))
    """)
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    # 4. Load coaching data (as stream_study_response would)
    commitment = load_active_commitment(db)
    insights = load_coaching_insights(db)
    coaching_section = build_coaching_prompt_section(commitment, insights)

    # 5. Build the study prompt with coaching context
    prompt = build_study_prompt(
        passage='Romans 3:1-8', genre='epistle',
        session_elapsed_seconds=5400,
        coaching_context=coaching_section,
    )

    # Verify coaching data is in the prompt
    assert 'application_specificity' in prompt
    assert 'Pause 15-20 seconds' in prompt
    assert 'diffuse' in prompt
    assert 'ESCALATION LADDER' in prompt
    assert 'ANTI-NAGGING' in prompt

    # 6. Test exposure tracking
    assert check_coaching_exposure(db, session_id, 'application_specificity') is None
    record_coaching_exposure(db, session_id, 'application_specificity',
                             escalation_level=2, response='accepted')
    exp = check_coaching_exposure(db, session_id, 'application_specificity')
    assert exp['escalation_level'] == 2
    assert exp['response'] == 'accepted'

    # 7. Verify anti-nagging: recording again with 'pending' doesn't overwrite 'accepted'
    record_coaching_exposure(db, session_id, 'application_specificity',
                             escalation_level=1, response='pending')
    exp2 = check_coaching_exposure(db, session_id, 'application_specificity')
    assert exp2['response'] == 'accepted'  # not overwritten


def test_bridge_degrades_gracefully_with_no_coaching_data(db):
    prompt = build_study_prompt(
        passage='Genesis 1:1-5', genre='narrative',
        session_elapsed_seconds=1800,
        coaching_context='',
    )
    assert 'Coaching Memory' not in prompt
    assert 'ESCALATION' not in prompt
