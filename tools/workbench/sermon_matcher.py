"""Sermon -> session matching.

Pure function match_sermon_to_sessions returns a MatchDecision. The orchestrator
apply_match_decision_for_sermon (Task 10) wraps the pure function in a BEGIN
IMMEDIATE transaction and writes sermon_links rows.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class SermonInfo:
    id: int
    book: Optional[int]
    chapter: Optional[int]
    verse_start: Optional[int]
    verse_end: Optional[int]
    preach_date: Optional[str]
    sermon_type: str  # 'expository' | 'topical'
    passages: list = field(default_factory=list)


@dataclass(frozen=True)
class SessionInfo:
    id: int
    book: Optional[int]
    chapter: Optional[int]
    verse_start: Optional[int]
    verse_end: Optional[int]
    created_at: str
    last_homiletical_activity_at: Optional[str]


@dataclass(frozen=True)
class SermonLink:
    sermon_id: int
    session_id: int
    link_status: str
    link_source: str


@dataclass(frozen=True)
class SessionMatch:
    session_id: int
    tier: int
    reason: str


@dataclass(frozen=True)
class MatchDecision:
    sermon_id: int
    action: str  # 'auto_link' | 'surface_candidates' | 'no_match'
    auto_link_target: Optional[SessionMatch] = None
    candidates: tuple = ()
    reason_summary: str = ''


@dataclass(frozen=True)
class MatcherSettings:
    tier1_days: int = 7
    tier2_days: int = 14
    cutoff_days: int = 30


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.split('+')[0].split('Z')[0].split('.')[0])
    except Exception:
        return None


def _passage_match(sermon: SermonInfo, session: SessionInfo) -> str:
    """Return 'exact', 'overlap', or 'none'."""
    if sermon.book is None or session.book is None:
        return 'none'
    if sermon.book != session.book:
        return 'none'
    if (sermon.chapter == session.chapter
        and sermon.verse_start == session.verse_start
        and sermon.verse_end == session.verse_end):
        return 'exact'
    if sermon.chapter == session.chapter:
        return 'overlap'
    for p in sermon.passages or []:
        if p.get('book') == session.book and p.get('chapter_start') == session.chapter:
            if (p.get('verse_start') == session.verse_start
                and p.get('verse_end') == session.verse_end):
                return 'exact'
            return 'overlap'
    return 'none'


def _days_before(date_a: Optional[datetime], date_b: Optional[datetime]) -> Optional[int]:
    """Days that date_a is before date_b (positive if before, negative if after)."""
    if date_a is None or date_b is None:
        return None
    delta = (date_b - date_a).days
    return delta


def match_sermon_to_sessions(
    sermon: SermonInfo,
    sessions: tuple,
    existing_links: tuple,
    rejected_session_ids: frozenset,
    settings: MatcherSettings,
) -> MatchDecision:
    """Pure function. Returns a MatchDecision based on tier rules."""
    if sermon.sermon_type == 'topical':
        return MatchDecision(sermon_id=sermon.id, action='no_match',
                             reason_summary='topical_excluded')

    preach_dt = _parse_date(sermon.preach_date)
    if preach_dt is None:
        return MatchDecision(sermon_id=sermon.id, action='no_match',
                             reason_summary='unparseable_preach_date')

    tier1, tier2 = [], []
    for s in sessions:
        if s.id in rejected_session_ids:
            continue
        created_dt = _parse_date(s.created_at)
        if created_dt is None or created_dt > preach_dt:
            continue
        pmatch = _passage_match(sermon, s)
        if pmatch == 'none':
            continue
        activity_dt = _parse_date(s.last_homiletical_activity_at)
        if activity_dt is None:
            days_before = None
        else:
            days_before = _days_before(activity_dt, preach_dt)

        if days_before is not None and days_before > settings.cutoff_days:
            continue
        if days_before is not None and days_before < 0:
            continue

        if (pmatch == 'exact' and days_before is not None
            and 0 <= days_before <= settings.tier1_days):
            tier1.append(SessionMatch(session_id=s.id, tier=1,
                                       reason=f'tier1:exact+{days_before}d'))
        else:
            if pmatch == 'overlap':
                reason = f'tier2:overlap+{days_before}d' if days_before is not None else 'tier2:overlap+no_hom'
            elif days_before is None:
                reason = 'tier2:exact+no_hom_activity'
            elif days_before > settings.tier1_days and days_before <= settings.cutoff_days:
                reason = f'tier2:exact+{days_before}d'
            else:
                reason = f'tier2:misc+{days_before}d'
            tier2.append(SessionMatch(session_id=s.id, tier=2, reason=reason))

    if len(tier1) == 1:
        return MatchDecision(
            sermon_id=sermon.id, action='auto_link',
            auto_link_target=tier1[0],
            candidates=tuple(tier2),
            reason_summary=tier1[0].reason,
        )
    if len(tier1) > 1:
        demoted = tuple(SessionMatch(session_id=m.session_id, tier=2,
                                      reason='tier2:ambiguous_tier1')
                         for m in tier1)
        return MatchDecision(
            sermon_id=sermon.id, action='surface_candidates',
            candidates=demoted + tuple(tier2),
            reason_summary='tier1_ambiguous',
        )
    if tier2:
        return MatchDecision(
            sermon_id=sermon.id, action='surface_candidates',
            candidates=tuple(tier2),
            reason_summary='tier2_only',
        )
    return MatchDecision(sermon_id=sermon.id, action='no_match',
                         reason_summary='no_sessions_qualified')
