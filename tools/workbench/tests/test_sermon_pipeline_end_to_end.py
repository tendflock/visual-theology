"""End-to-end sermon coach pipeline test.

Drives the full pipeline (sync -> match -> analyze) against a fresh DB with a
mocked SermonAudio client and canned LLM, asserts every layer works end-to-end.
"""

import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace
import hashlib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermonaudio_sync import run_sync_with_client
from sermon_matcher import apply_match_decision_for_sermon
from sermon_analyzer import (
    analyze_sermon, AnalyzerInput, run_pure_stages, build_rubric_prompt,
    DEFAULT_PLANNED_DURATION_SEC,
)
from llm_client import CannedLLMClient


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


class MockSAClient:
    def __init__(self, items): self.items = items
    def list_sermons_updated_since(self, broadcaster_id, since=None, limit=100):
        return self.items
    def get_sermon_detail(self, sermon_id):
        for i in self.items:
            if i.sermon_id == sermon_id: return i
        return None


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def _canned_review(prompt):
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    return {key: {
        'output': {
            'tier1_impact': {
                'burden_clarity': 'clear',
                'burden_statement_excerpt': 'No condemnation',
                'burden_first_stated_at_sec': 120,
                'movement_clarity': 'river',
                'movement_rationale': 'Coherent arc.',
                'application_specificity': 'concrete',
                'application_first_arrived_at_sec': 1500,
                'application_excerpts': [],
                'ethos_rating': 'engaged',
                'ethos_markers': [],
                'concreteness_score': 4,
                'imagery_density_per_10min': 3.8,
                'narrative_moments': [],
            },
            'tier2_faithfulness': {
                'christ_thread_score': 'explicit',
                'christ_thread_excerpts': [],
                'exegetical_grounding': 'grounded',
                'exegetical_grounding_notes': 'Strong text focus.',
            },
            'tier3_diagnostic': {
                'length_delta_commentary': 'On time.',
                'density_hotspots': [],
                'late_application_note': None,
                'outline_drift_note': None,
            },
            'coach_summary': {
                'top_impact_helpers': ['Clear burden', 'Strong application', 'Engaged delivery'],
                'top_impact_hurters': ['-', '-', '-'],
                'faithfulness_note': 'Christ thread explicit.',
                'one_change_for_next_sunday': 'Keep doing exactly this.',
            },
            'flags': [],
        },
        'input_tokens': 4000, 'output_tokens': 600, 'model': 'claude-opus-4-6',
    }}


def test_full_pipeline_sync_match_analyze(fresh_db):
    # Seed a session with Logos book numbering (66 for Romans, NOT 45)
    sid = fresh_db.create_session('Romans 8:1-11', 66, 8, 1, 11, 'epistle')
    conn = fresh_db._conn()
    conn.execute("UPDATE sessions SET created_at = '2026-04-06 09:00:00', "
                 "last_homiletical_activity_at = '2026-04-09 12:00:00' WHERE id = ?", (sid,))
    conn.commit()
    conn.close()

    # Sync a sermon
    remote = SimpleNamespace(
        sermon_id='sa-e2e', broadcaster_id='bcast', title='Romans 8',
        speaker_name='Bryan Schneider', event_type='Sunday Service', series='Romans',
        preach_date=dt.date(2026, 4, 12), publish_date=dt.date(2026, 4, 12),
        duration=2322, bible_text='Romans 8:1-11',
        audio_url='https://sa.example/x.mp3',
        transcript='Welcome to Romans 8.\n\n' * 400,  # well over 1000 words
        update_date=dt.datetime(2026, 4, 12, 18, 0, 0),
    )
    client = MockSAClient([remote])
    sync_result = run_sync_with_client(fresh_db, client, broadcaster_id='bcast', trigger='manual')
    assert sync_result['sermons_new'] == 1

    # Match
    conn = fresh_db._conn()
    sermon_id = conn.execute("SELECT id FROM sermons WHERE sermonaudio_id='sa-e2e'").fetchone()[0]
    conn.close()
    match_decision = apply_match_decision_for_sermon(fresh_db, sermon_id)
    assert match_decision.action == 'auto_link'

    # Build the analyzer input THE SAME WAY production does
    # (planned_duration_sec = DEFAULT_PLANNED_DURATION_SEC since Task 24)
    inp = AnalyzerInput(
        sermon_id=sermon_id, transcript_text=remote.transcript,
        duration_sec=2322, planned_duration_sec=DEFAULT_PLANNED_DURATION_SEC,
        outline_points=[], bible_text_raw='Romans 8:1-11',
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    llm = CannedLLMClient(_canned_review(prompt))

    analysis = analyze_sermon(fresh_db, sermon_id, llm_client=llm)
    assert analysis['status'] == 'review_ready'

    # Final: verify review row exists and contains expected data
    conn = fresh_db._conn()
    review = conn.execute(
        "SELECT burden_clarity, one_change_for_next_sunday FROM sermon_reviews WHERE sermon_id=?",
        (sermon_id,)
    ).fetchone()
    status = conn.execute("SELECT sync_status FROM sermons WHERE id=?", (sermon_id,)).fetchone()[0]
    link = conn.execute(
        "SELECT link_status FROM sermon_links WHERE sermon_id=?", (sermon_id,)
    ).fetchone()
    conn.close()
    # rows may be sqlite3.Row - use tuple()
    assert tuple(review) == ('clear', 'Keep doing exactly this.')
    assert status == 'review_ready'
    assert tuple(link) == ('active',)
