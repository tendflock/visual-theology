import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermon_coach_agent import (
    build_system_prompt, TOOL_DEFINITIONS, execute_tool,
)


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


@pytest.fixture
def stocked_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    yield db
    os.unlink(path)


def test_system_prompt_includes_voice_constants():
    prompt = build_system_prompt(
        sermon_context={'passage': 'Romans 8:1-11', 'duration_sec': 2322},
        review_json={},
        corpus_gate_status='pre_gate',
    )
    assert 'Reformed Presbyterian' in prompt
    assert 'Chapell' in prompt
    assert 'study partner' in prompt.lower() or 'partner' in prompt.lower()


def test_system_prompt_includes_corpus_gate_rule_verbatim():
    prompt = build_system_prompt(
        sermon_context={}, review_json={}, corpus_gate_status='pre_gate',
    )
    assert 'pre_gate' in prompt
    assert 'pattern' in prompt.lower()
    assert 'persistent' in prompt.lower()


def test_system_prompt_forbids_pattern_words_in_pre_gate():
    prompt = build_system_prompt(
        sermon_context={}, review_json={}, corpus_gate_status='pre_gate',
    )
    for word in ['pattern', 'persistent', 'always', 'every time']:
        assert word in prompt


def test_system_prompt_includes_three_tier_framing():
    prompt = build_system_prompt(
        sermon_context={}, review_json={'burden_clarity': 'clear'},
        corpus_gate_status='stable',
    )
    assert 'Impact' in prompt
    assert 'Faithfulness' in prompt
    assert 'Diagnostic' in prompt


def test_tool_definitions_list_all_read_tools():
    names = {t['name'] for t in TOOL_DEFINITIONS}
    assert 'get_sermon_review' in names
    assert 'get_sermon_flags' in names
    assert 'get_transcript_excerpt' in names
    assert 'get_prep_session_full' in names
    assert 'pull_historical_sermons' in names
    assert 'get_sermon_patterns' in names


def test_execute_tool_dispatches_get_sermon_review(stocked_db):
    conn = stocked_db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-a', 'bcast', 'T', 'sermon', 'review_ready', datetime('now'),
                datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_reviews (sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis, actual_duration_seconds,
            burden_clarity, top_impact_helpers, top_impact_hurters, one_change_for_next_sunday,
            computed_at)
        VALUES (?, '1.0.0', '1.0.0', 'claude-opus-4-6', 'h', 1, 100,
                'clear', '["a"]', '["b"]', 'change', datetime('now'))
    """, (sermon_id,))
    conn.commit()
    conn.close()

    result = execute_tool(
        'get_sermon_review',
        {'sermon_id': sermon_id},
        session_context={'db': stocked_db, 'sermon_id': sermon_id},
    )
    assert result['burden_clarity'] == 'clear'
