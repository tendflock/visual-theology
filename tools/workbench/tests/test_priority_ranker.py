"""Tests for priority_ranker.compute_priority_ranking."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from priority_ranker import compute_priority_ranking


# Override pytest-base-url's autouse _verify_url fixture so these pure-unit
# tests don't trigger conftest.py's Flask-server fixture.
@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


# ── Tests ──────────────────────────────────────────────────────────


def test_ranking_returns_all_dimensions():
    ranking = compute_priority_ranking(moments=[], n_sermons=10)
    assert len(ranking) == 7  # 7 dimension keys
    assert all('overall_rank' in r for r in ranking)


def test_ranking_with_no_moments_all_zero_impact():
    ranking = compute_priority_ranking(moments=[], n_sermons=10)
    assert all(r['impact_priority_score'] == 0 for r in ranking)


def test_ranking_orders_by_negative_rate():
    moments = [
        {'sermon_id': 1, 'dimension_key': 'burden_clarity', 'valence': 'negative', 'confidence': 0.9, 'impact': 'major'},
        {'sermon_id': 2, 'dimension_key': 'burden_clarity', 'valence': 'negative', 'confidence': 0.85, 'impact': 'major'},
        {'sermon_id': 1, 'dimension_key': 'ethos_rating', 'valence': 'negative', 'confidence': 0.7, 'impact': 'minor'},
    ]
    ranking = compute_priority_ranking(moments, n_sermons=5)
    assert ranking[0]['dimension_key'] == 'burden_clarity'
    assert ranking[0]['overall_rank'] == 1


def test_positive_moments_ignored_for_impact():
    moments = [
        {'sermon_id': 1, 'dimension_key': 'burden_clarity', 'valence': 'positive', 'confidence': 0.95, 'impact': 'major'},
    ]
    ranking = compute_priority_ranking(moments, n_sermons=5)
    bc = [r for r in ranking if r['dimension_key'] == 'burden_clarity'][0]
    assert bc['impact_priority_score'] == 0  # positive moments don't count


def test_confidence_in_ranking_measures_gap():
    moments = [
        {'sermon_id': 1, 'dimension_key': 'burden_clarity', 'valence': 'negative', 'confidence': 0.9, 'impact': 'major'},
    ]
    ranking = compute_priority_ranking(moments, n_sermons=5)
    assert ranking[0]['confidence_in_ranking'] == ranking[0]['overall_score'] - ranking[1]['overall_score']


def test_actionability_scores_correct():
    ranking = compute_priority_ranking(moments=[], n_sermons=10)
    scores = {r['dimension_key']: r['actionability_score'] for r in ranking}
    assert scores['application_specificity'] == 1.0
    assert scores['burden_clarity'] == 1.0
    assert scores['movement_clarity'] == 0.7
    assert scores['christ_thread_score'] == 0.4
