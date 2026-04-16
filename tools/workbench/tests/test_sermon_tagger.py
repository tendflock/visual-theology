"""Tests for sermon_tagger constants and parse_tagger_output."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sermon_tagger import (
    CONFIDENCE_FLOOR,
    DIMENSION_KEYS,
    HOMILETIC_MOVES,
    MAX_MOMENTS_PER_SERMON,
    SECTION_ROLES,
    TAGGER_PROMPT_VERSION,
    parse_tagger_output,
)


# Override pytest-base-url's autouse _verify_url fixture so these pure-unit
# tests don't trigger conftest.py's Flask-server fixture.
@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


# ── Helpers ─────────────────────────────────────────────────────────

def _valid_moment(**overrides) -> dict:
    """Return a fully valid moment dict, with optional field overrides."""
    base = {
        'dimension_key': 'burden_clarity',
        'valence': 'positive',
        'section_role': 'exposition',
        'impact': 'major',
        'confidence': 0.90,
        'excerpt_text': 'The burden of the text is clear.',
        'rationale': 'The preacher stated the main idea explicitly.',
        'start_segment_index': 5,
        'end_segment_index': 8,
        'homiletic_move': 'big_idea_statement',
    }
    base.update(overrides)
    return base


# ── Constant sanity checks ─────────────────────────────────────────

def test_constants_are_frozen_sets():
    assert isinstance(DIMENSION_KEYS, frozenset)
    assert isinstance(SECTION_ROLES, frozenset)
    assert isinstance(HOMILETIC_MOVES, frozenset)


def test_constants_sizes():
    assert len(DIMENSION_KEYS) == 7
    assert len(SECTION_ROLES) == 11
    assert len(HOMILETIC_MOVES) == 16


def test_prompt_version_is_semver_string():
    parts = TAGGER_PROMPT_VERSION.split('.')
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


# ── parse_tagger_output: acceptance ────────────────────────────────

def test_parse_valid_moment():
    result = parse_tagger_output({'moments': [_valid_moment()]})
    assert len(result) == 1
    m = result[0]
    assert m['dimension_key'] == 'burden_clarity'
    assert m['confidence'] == 0.90
    assert m['homiletic_move'] == 'big_idea_statement'


# ── parse_tagger_output: drop rules ────────────────────────────────

def test_parse_rejects_invalid_dimension():
    result = parse_tagger_output({
        'moments': [_valid_moment(dimension_key='made_up_key')]
    })
    assert result == []


def test_parse_rejects_invalid_valence():
    result = parse_tagger_output({
        'moments': [_valid_moment(valence='neutral')]
    })
    assert result == []


def test_parse_rejects_invalid_section_role():
    result = parse_tagger_output({
        'moments': [_valid_moment(section_role='freestyle')]
    })
    assert result == []


def test_parse_rejects_invalid_impact():
    result = parse_tagger_output({
        'moments': [_valid_moment(impact='huge')]
    })
    assert result == []


def test_parse_suppresses_low_confidence():
    result = parse_tagger_output({
        'moments': [_valid_moment(confidence=0.50)]
    })
    assert result == []


def test_parse_rejects_empty_excerpt():
    result = parse_tagger_output({
        'moments': [_valid_moment(excerpt_text='')]
    })
    assert result == []


def test_parse_rejects_missing_segment_indices():
    # Missing start_segment_index
    m1 = _valid_moment()
    del m1['start_segment_index']
    # Missing end_segment_index
    m2 = _valid_moment()
    del m2['end_segment_index']
    result = parse_tagger_output({'moments': [m1, m2]})
    assert result == []


# ── parse_tagger_output: fixup rules ───────────────────────────────

def test_parse_fixes_invalid_homiletic_move():
    result = parse_tagger_output({
        'moments': [_valid_moment(homiletic_move='invented_move')]
    })
    assert len(result) == 1
    assert result[0]['homiletic_move'] is None


def test_parse_clamps_confidence():
    result = parse_tagger_output({
        'moments': [_valid_moment(confidence=1.5)]
    })
    assert len(result) == 1
    assert result[0]['confidence'] == 1.0


# ── parse_tagger_output: ordering and capping ──────────────────────

def test_parse_sorts_by_confidence():
    moments = [
        _valid_moment(confidence=0.70, excerpt_text='low'),
        _valid_moment(confidence=0.95, excerpt_text='high'),
        _valid_moment(confidence=0.80, excerpt_text='mid'),
    ]
    result = parse_tagger_output({'moments': moments})
    confs = [m['confidence'] for m in result]
    assert confs == [0.95, 0.80, 0.70]


def test_parse_caps_at_max():
    moments = [
        _valid_moment(confidence=round(0.65 + i * 0.01, 2), excerpt_text=f'm{i}')
        for i in range(25)
    ]
    result = parse_tagger_output({'moments': moments})
    assert len(result) == MAX_MOMENTS_PER_SERMON


# ── parse_tagger_output: edge cases ────────────────────────────────

def test_parse_empty_moments():
    assert parse_tagger_output({'moments': []}) == []


def test_parse_missing_moments_key():
    assert parse_tagger_output({}) == []
