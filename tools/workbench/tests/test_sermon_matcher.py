import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

from sermon_matcher import (
    match_sermon_to_sessions, SermonInfo, SessionInfo, MatchDecision,
    MatcherSettings,
)


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def _sermon(book=45, chapter=8, vs=1, ve=11, preach='2026-04-12',
            sermon_type='expository'):
    return SermonInfo(
        id=1, book=book, chapter=chapter, verse_start=vs, verse_end=ve,
        preach_date=preach, sermon_type=sermon_type,
        passages=[{'book': book, 'chapter_start': chapter, 'verse_start': vs,
                    'chapter_end': chapter, 'verse_end': ve}],
    )


def _session(sid=10, book=45, chapter=8, vs=1, ve=11,
             last_hom='2026-04-09 12:00:00', created='2026-04-06 09:00:00'):
    return SessionInfo(
        id=sid, book=book, chapter=chapter, verse_start=vs, verse_end=ve,
        created_at=created, last_homiletical_activity_at=last_hom,
    )


def _settings():
    return MatcherSettings(tier1_days=7, tier2_days=14, cutoff_days=30)


def test_tier1_exact_match_within_7_days_auto_links():
    decision = match_sermon_to_sessions(
        _sermon(), (_session(),), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'auto_link'
    assert decision.auto_link_target.tier == 1
    assert decision.auto_link_target.session_id == 10


def test_multiple_tier1_candidates_demoted_to_candidates():
    sermon = _sermon()
    sessions = (
        _session(sid=10),
        _session(sid=20, created='2026-04-07 10:00:00', last_hom='2026-04-10 15:00:00'),
    )
    decision = match_sermon_to_sessions(
        sermon, sessions, existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert len(decision.candidates) >= 2


def test_session_created_after_sermon_never_matches():
    sermon = _sermon()
    s = _session(created='2026-04-13 10:00:00')
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_timing_7_to_14_days_becomes_candidate():
    sermon = _sermon(preach='2026-04-12')
    s = _session(last_hom='2026-04-01 10:00:00', created='2026-03-30 08:00:00')
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert decision.candidates[0].tier == 2


def test_topical_sermon_never_auto_links():
    sermon = _sermon(sermon_type='topical')
    decision = match_sermon_to_sessions(
        sermon, (_session(),), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_rejected_session_is_excluded():
    decision = match_sermon_to_sessions(
        _sermon(), (_session(sid=10),), existing_links=(),
        rejected_session_ids=frozenset({10}), settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_no_match_when_passage_mismatch():
    sermon = _sermon(book=45, chapter=8)
    s = _session(book=45, chapter=12)
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_cutoff_30_days_excludes_old_sessions():
    sermon = _sermon(preach='2026-04-12')
    s = _session(last_hom='2026-02-20 10:00:00', created='2026-02-18 08:00:00')
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'no_match'


def test_partial_passage_overlap_is_tier2():
    sermon = _sermon(book=45, chapter=8, vs=1, ve=17)
    s = _session(book=45, chapter=8, vs=1, ve=11)
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert decision.candidates[0].tier == 2


def test_session_with_no_homiletical_activity_is_candidate():
    sermon = _sermon()
    s = _session(last_hom=None)
    decision = match_sermon_to_sessions(
        sermon, (s,), existing_links=(), rejected_session_ids=frozenset(),
        settings=_settings(),
    )
    assert decision.action == 'surface_candidates'
    assert decision.candidates[0].tier == 2
