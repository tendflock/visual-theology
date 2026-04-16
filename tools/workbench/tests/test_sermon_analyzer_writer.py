import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace
import json
import hashlib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from llm_client import CannedLLMClient
from sermonaudio_sync import upsert_sermon
from sermon_analyzer import analyze_sermon, dispatch_pending_analyses


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


@pytest.fixture
def db_with_sermon():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    conn = db._conn()
    upsert_sermon(conn, SimpleNamespace(
        sermon_id='sa-1', broadcaster_id='bcast', title='Romans 8',
        speaker_name='Bryan Schneider', event_type='Sunday Service', series='Romans',
        preach_date=dt.date(2026, 4, 12), publish_date=dt.date(2026, 4, 12),
        duration=2322, bible_text='Romans 8:1-11',
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome to Romans 8.\n\nThe aorist here is significant.\n\n' * 120,
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    ))
    conn.commit()
    conn.close()
    yield db
    os.unlink(path)


def _canned_for(db_with_sermon):
    from sermon_analyzer import (
        AnalyzerInput, run_pure_stages, build_rubric_prompt,
        DEFAULT_PLANNED_DURATION_SEC,
    )
    conn = db_with_sermon._conn()
    row = conn.execute("SELECT id, transcript_text, duration_seconds, bible_text_raw FROM sermons").fetchone()
    conn.close()
    inp = AnalyzerInput(
        sermon_id=row[0], transcript_text=row[1], duration_sec=row[2],
        planned_duration_sec=DEFAULT_PLANNED_DURATION_SEC,
        outline_points=[], bible_text_raw=row[3],
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    return {key: {
        'output': {
            'tier1_impact': {
                'burden_clarity': 'clear',
                'burden_statement_excerpt': 'No condemnation in Christ',
                'burden_first_stated_at_sec': 180,
                'movement_clarity': 'mostly_river',
                'movement_rationale': 'Tracked well.',
                'application_specificity': 'abstract',
                'application_first_arrived_at_sec': 1860,
                'application_excerpts': [],
                'ethos_rating': 'engaged',
                'ethos_markers': [],
                'concreteness_score': 3,
                'imagery_density_per_10min': 2.1,
                'narrative_moments': [],
            },
            'tier2_faithfulness': {
                'christ_thread_score': 'gestured',
                'christ_thread_excerpts': [],
                'exegetical_grounding': 'grounded',
                'exegetical_grounding_notes': 'Well grounded.',
            },
            'tier3_diagnostic': {
                'length_delta_commentary': 'Acceptable.',
                'density_hotspots': [],
                'late_application_note': 'Late.',
                'outline_drift_note': None,
            },
            'coach_summary': {
                'top_impact_helpers': ['Clear burden', 'Engaged delivery', 'Grounded exegesis'],
                'top_impact_hurters': ['Late application', 'Abstract app', 'Weak imagery'],
                'faithfulness_note': 'Christ thread gestured.',
                'one_change_for_next_sunday': 'Start application 6 minutes earlier.',
            },
            'flags': [
                {'flag_type': 'late_application', 'severity': 'warn',
                 'start_sec': 0, 'end_sec': 1860, 'section_label': 'intro+body',
                 'excerpt': '...', 'rationale': 'App arrived at 31:00'},
            ],
        },
        'input_tokens': 4200, 'output_tokens': 700, 'model': 'claude-opus-4-6',
    }}


def test_analyze_sermon_writes_review_row(db_with_sermon):
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    conn = db_with_sermon._conn()
    sermon_id = conn.execute("SELECT id FROM sermons").fetchone()[0]
    conn.close()

    result = analyze_sermon(db_with_sermon, sermon_id, llm_client=client)
    assert result['status'] == 'review_ready'

    conn = db_with_sermon._conn()
    review = conn.execute(
        "SELECT burden_clarity, one_change_for_next_sunday FROM sermon_reviews WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    sermon_status = conn.execute(
        "SELECT sync_status FROM sermons WHERE id=?", (sermon_id,)
    ).fetchone()[0]
    flag_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_flags WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    cost_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_analysis_cost_log WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    conn.close()

    assert review[0] == 'clear'
    assert review[1] == 'Start application 6 minutes earlier.'
    assert sermon_status == 'review_ready'
    assert flag_count == 1
    assert cost_count == 1


def test_reanalyze_overwrites_review_and_replaces_flags(db_with_sermon):
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    conn = db_with_sermon._conn()
    sermon_id = conn.execute("SELECT id FROM sermons").fetchone()[0]
    conn.close()

    analyze_sermon(db_with_sermon, sermon_id, llm_client=client)
    analyze_sermon(db_with_sermon, sermon_id, llm_client=client)

    conn = db_with_sermon._conn()
    flag_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_flags WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    review_count = conn.execute(
        "SELECT COUNT(*) FROM sermon_reviews WHERE sermon_id=?", (sermon_id,)
    ).fetchone()[0]
    conn.close()

    assert flag_count == 1
    assert review_count == 1


def test_dispatch_picks_up_transcript_ready_sermons(db_with_sermon):
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    processed = dispatch_pending_analyses(db_with_sermon, llm_client=client, limit=10)
    assert processed == 1


def test_analyze_sermon_populates_duration_delta_with_default(db_with_sermon):
    """Regression: planned_duration_sec defaults to 28 min so length delta is computed."""
    canned = _canned_for(db_with_sermon)
    client = CannedLLMClient(canned)
    conn = db_with_sermon._conn()
    sermon_id = conn.execute("SELECT id FROM sermons").fetchone()[0]
    conn.close()

    analyze_sermon(db_with_sermon, sermon_id, llm_client=client)

    conn = db_with_sermon._conn()
    review = conn.execute(
        "SELECT actual_duration_seconds, planned_duration_seconds, duration_delta_seconds "
        "FROM sermon_reviews WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    conn.close()
    assert review[0] == 2322  # actual from fixture
    assert review[1] == 1680  # default planned
    assert review[2] == 642   # delta = actual - planned (2322 - 1680)
