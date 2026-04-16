import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from sermon_analyzer import (
    run_pure_stages, AnalyzerInput, PureStageOutput,
)


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def test_pure_stages_returns_expected_shape():
    transcript = (
        "Welcome to Romans 8. Today we explore no condemnation.\n\n"
        "Let me begin with an observation about the participle.\n\n"
        "Note the genitive absolute and the aorist indicative here.\n\n"
        "So what does this mean for your life this Monday morning?"
    )
    inp = AnalyzerInput(
        sermon_id=1,
        transcript_text=transcript,
        duration_sec=600,
        planned_duration_sec=480,
        outline_points=[],
        bible_text_raw='Romans 8:1-11',
    )
    out = run_pure_stages(inp)
    assert isinstance(out, PureStageOutput)
    assert len(out.segments) >= 3
    assert out.section_timings['intro'] + out.section_timings['body'] + \
           out.section_timings['application'] + out.section_timings['close'] == 600
    assert out.duration_delta_sec == 120
    assert isinstance(out.density_hotspots, list)


def test_pure_stages_handles_empty_outline():
    inp = AnalyzerInput(
        sermon_id=2,
        transcript_text="A short sermon with two paragraphs.\n\nSecond paragraph here.",
        duration_sec=120,
        planned_duration_sec=None,
        outline_points=[],
        bible_text_raw='Romans 8:1-11',
    )
    out = run_pure_stages(inp)
    assert out.duration_delta_sec is None
    assert out.outline_coverage_pct is None


def test_pure_stages_writes_outline_coverage_when_linked():
    transcript = (
        "First point: the participle is significant.\n\n"
        "Second point: the genitive absolute emphasizes.\n\n"
        "Third point: apply this by remembering the gospel daily."
    )
    outline_points = [
        {'id': 1, 'content': 'The participle is significant'},
        {'id': 2, 'content': 'The genitive absolute emphasizes'},
        {'id': 3, 'content': 'Application: remember the gospel daily'},
    ]
    inp = AnalyzerInput(
        sermon_id=3,
        transcript_text=transcript,
        duration_sec=600,
        planned_duration_sec=600,
        outline_points=outline_points,
        bible_text_raw='Romans 8:1-11',
    )
    out = run_pure_stages(inp)
    assert out.outline_coverage_pct is not None
    assert 0 <= out.outline_coverage_pct <= 1.0
