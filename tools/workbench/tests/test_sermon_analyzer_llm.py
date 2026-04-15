import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import pytest
from llm_client import CannedLLMClient
from sermon_analyzer import (
    AnalyzerInput, run_pure_stages, build_rubric_prompt,
    run_llm_rubric, REVIEW_SCHEMA,
)


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def _canned_review():
    return {
        'output': {
            'tier1_impact': {
                'burden_clarity': 'clear',
                'burden_statement_excerpt': 'There is no condemnation for those in Christ',
                'burden_first_stated_at_sec': 180,
                'movement_clarity': 'mostly_river',
                'movement_rationale': 'Flowed well.',
                'application_specificity': 'concrete',
                'application_first_arrived_at_sec': 1860,
                'application_excerpts': [{'start_sec': 1860, 'excerpt': 'trust the verdict'}],
                'ethos_rating': 'engaged',
                'ethos_markers': ['direct 2nd person at 12:40'],
                'concreteness_score': 3,
                'imagery_density_per_10min': 4.2,
                'narrative_moments': [],
            },
            'tier2_faithfulness': {
                'christ_thread_score': 'gestured',
                'christ_thread_excerpts': [{'start_sec': 2400, 'excerpt': 'pointing to Christ'}],
                'exegetical_grounding': 'grounded',
                'exegetical_grounding_notes': 'Text is the sermon center.',
            },
            'tier3_diagnostic': {
                'length_delta_commentary': 'Length hurts because application came late.',
                'density_hotspots': [{'start_sec': 820, 'end_sec': 1060, 'note': 'genitive hold'}],
                'late_application_note': 'Application arrived at 31:00.',
                'outline_drift_note': None,
            },
            'coach_summary': {
                'top_impact_helpers': ['Burden stated early', 'Personal confession at 24:15', 'Narrative at 7:40'],
                'top_impact_hurters': ['Late application', 'Abstract app', 'Density spike §2'],
                'faithfulness_note': 'Christ thread gestured, not explicit mid-body.',
                'one_change_for_next_sunday': 'Start application at 22:00 mark.',
            },
            'flags': [
                {'flag_type': 'late_application', 'severity': 'concern',
                 'start_sec': 0, 'end_sec': 1860, 'section_label': 'intro+body',
                 'excerpt': 'exegetical heat', 'rationale': 'Application at 31:00 of 38:42'},
                {'flag_type': 'density_spike', 'severity': 'warn',
                 'start_sec': 820, 'end_sec': 1060, 'section_label': 'body',
                 'excerpt': 'genitive hold', 'rationale': '4 minute Greek hold'},
            ],
        },
        'input_tokens': 5000, 'output_tokens': 800, 'model': 'claude-opus-4-6',
    }


def test_build_rubric_prompt_includes_transcript_and_metadata():
    inp = AnalyzerInput(
        sermon_id=1, transcript_text='hello world', duration_sec=600,
        planned_duration_sec=600, outline_points=[], bible_text_raw='Romans 8:1-11',
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    assert 'Romans 8:1-11' in prompt
    assert 'hello world' in prompt
    assert '600' in prompt


def test_review_schema_has_three_tiers_and_summary():
    schema = REVIEW_SCHEMA
    top_props = set(schema['properties'].keys())
    assert 'tier1_impact' in top_props
    assert 'tier2_faithfulness' in top_props
    assert 'tier3_diagnostic' in top_props
    assert 'coach_summary' in top_props
    assert 'flags' in top_props


def test_run_llm_rubric_with_canned_client():
    inp = AnalyzerInput(
        sermon_id=1, transcript_text='x' * 5000, duration_sec=2322,
        planned_duration_sec=1680, outline_points=[], bible_text_raw='Romans 8:1-11',
    )
    pure = run_pure_stages(inp)
    prompt = build_rubric_prompt(inp, pure)
    import hashlib
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    client = CannedLLMClient({key: _canned_review()})
    result = run_llm_rubric(client, inp, pure)
    assert result['model'] == 'claude-opus-4-6'
    assert 'output' in result
    assert result['output']['tier1_impact']['burden_clarity'] == 'clear'
    assert result['output']['coach_summary']['one_change_for_next_sunday'] == 'Start application at 22:00 mark.'
