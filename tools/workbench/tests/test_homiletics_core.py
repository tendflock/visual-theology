import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

from homiletics_core import (
    HOMILETICAL_PHASES,
    __version__,
    segment_transcript,
    compute_section_timings,
    detect_density_hotspots,
    late_application,
    corpus_gate_status,
)


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def test_version_is_semver_string():
    assert isinstance(__version__, str)
    parts = __version__.split('.')
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_homiletical_phases_constant():
    assert 'exegetical_point' in HOMILETICAL_PHASES
    assert 'fcf_homiletical' in HOMILETICAL_PHASES
    assert 'sermon_construction' in HOMILETICAL_PHASES
    assert 'edit_pray' in HOMILETICAL_PHASES
    assert 'prayer' not in HOMILETICAL_PHASES  # non-homiletical excluded


def test_corpus_gate_status_thresholds():
    assert corpus_gate_status(0) == 'pre_gate'
    assert corpus_gate_status(4) == 'pre_gate'
    assert corpus_gate_status(5) == 'emerging'
    assert corpus_gate_status(9) == 'emerging'
    assert corpus_gate_status(10) == 'stable'
    assert corpus_gate_status(50) == 'stable'


def test_late_application_threshold():
    # arrival > 0.75 * duration is late
    assert late_application(arrival_sec=1860, duration_sec=2322)  # 80.1% — late
    assert not late_application(arrival_sec=1320, duration_sec=2322)  # 56.8% — OK
    assert late_application(arrival_sec=1742, duration_sec=2322)  # exactly 75.02% — late
    assert not late_application(arrival_sec=1741, duration_sec=2322)  # 74.98% — not late
    # Zero duration guard
    assert not late_application(arrival_sec=100, duration_sec=0)


def test_segment_transcript_returns_segments_with_timing():
    txt = (
        "Welcome to this sermon on Romans 8. Today we explore what it means to have no condemnation. "
        "Let me begin by asking a question. What does it mean that there is therefore now no condemnation?\n\n"
        "First, we need to understand the word 'therefore.' The apostle is drawing a conclusion from chapter 7. "
        "Paul has just finished an extended argument about the struggle with sin.\n\n"
        "Second, consider the phrase 'in Christ Jesus.' This is the hinge of Paul's theology. "
        "To be in Christ is to be transferred from Adam's family to Christ's family.\n\n"
        "So what does this mean for you this morning? It means that if you trust in Christ, "
        "there is no accusation that can stick against you. The court has ruled in your favor."
    )
    segments = segment_transcript(txt, duration_sec=600)
    assert len(segments) >= 3
    assert all('start_sec' in s and 'end_sec' in s and 'text' in s for s in segments)
    assert segments[0]['start_sec'] == 0
    assert segments[-1]['end_sec'] == 600
    for i in range(1, len(segments)):
        assert segments[i]['start_sec'] >= segments[i-1]['end_sec'] - 1


def test_compute_section_timings_sums_correctly():
    segments = [
        {'start_sec': 0, 'end_sec': 120, 'section_label': 'intro', 'text': ''},
        {'start_sec': 120, 'end_sec': 1800, 'section_label': 'body', 'text': ''},
        {'start_sec': 1800, 'end_sec': 2100, 'section_label': 'application', 'text': ''},
        {'start_sec': 2100, 'end_sec': 2280, 'section_label': 'close', 'text': ''},
    ]
    result = compute_section_timings(segments)
    assert result['intro'] == 120
    assert result['body'] == 1680
    assert result['application'] == 300
    assert result['close'] == 180


def test_detect_density_hotspots_finds_long_greek_holds():
    segments = [
        {'start_sec': 0, 'end_sec': 60, 'text': 'Welcome', 'section_label': 'intro'},
        {'start_sec': 60, 'end_sec': 120, 'text': 'The genitive absolute here in the aorist participle is significant', 'section_label': 'body'},
        {'start_sec': 120, 'end_sec': 180, 'text': 'Note the anarthrous noun and the oblique case usage', 'section_label': 'body'},
        {'start_sec': 180, 'end_sec': 240, 'text': 'The exegetical weight of the dative of means cannot be overstated', 'section_label': 'body'},
        {'start_sec': 240, 'end_sec': 300, 'text': 'Wallace notes the adverbial participle as causal in syntax', 'section_label': 'body'},
        {'start_sec': 300, 'end_sec': 360, 'text': 'Now let me apply this to your daily life', 'section_label': 'body'},
    ]
    hotspots = detect_density_hotspots(segments)
    assert len(hotspots) >= 1
    assert hotspots[0]['start_sec'] == 60
    assert hotspots[0]['end_sec'] >= 180

def test_late_application_exact_boundary():
    # arrival_sec == 0.75 * duration_sec must be NOT late (strict >)
    assert not late_application(arrival_sec=75, duration_sec=100)
    # Just above is late
    assert late_application(arrival_sec=76, duration_sec=100)

