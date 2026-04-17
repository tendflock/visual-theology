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


def apply_match_decision_for_sermon(db, sermon_id: int) -> MatchDecision:
    """Orchestrator: fetch state, compute decision, write sermon_links. BEGIN IMMEDIATE."""
    conn = db._conn()
    conn.execute("BEGIN IMMEDIATE")
    try:
        s_row = conn.execute("""
            SELECT id, book, chapter, verse_start, verse_end, preach_date, sermon_type
            FROM sermons WHERE id = ?
        """, (sermon_id,)).fetchone()
        if not s_row:
            conn.execute("ROLLBACK")
            conn.close()
            return MatchDecision(sermon_id=sermon_id, action='no_match',
                                  reason_summary='sermon_not_found')

        passages = [dict(book=r[0], chapter_start=r[1], verse_start=r[2],
                          chapter_end=r[3], verse_end=r[4])
                    for r in conn.execute(
                        "SELECT book, chapter_start, verse_start, chapter_end, verse_end "
                        "FROM sermon_passages WHERE sermon_id = ? ORDER BY rank",
                        (sermon_id,)
                    ).fetchall()]
        sermon = SermonInfo(
            id=s_row[0], book=s_row[1], chapter=s_row[2],
            verse_start=s_row[3], verse_end=s_row[4],
            preach_date=s_row[5], sermon_type=s_row[6],
            passages=passages,
        )

        session_rows = conn.execute("""
            SELECT id, book, chapter, verse_start, verse_end,
                   created_at, last_homiletical_activity_at
            FROM sessions
            WHERE book = ? AND chapter = ?
        """, (s_row[1], s_row[2])).fetchall()
        sessions = tuple(SessionInfo(
            id=r[0], book=r[1], chapter=r[2], verse_start=r[3], verse_end=r[4],
            created_at=r[5], last_homiletical_activity_at=r[6],
        ) for r in session_rows)

        link_rows = conn.execute("""
            SELECT sermon_id, session_id, link_status, link_source
            FROM sermon_links WHERE sermon_id = ?
        """, (sermon_id,)).fetchall()
        existing_links = tuple(SermonLink(sermon_id=r[0], session_id=r[1],
                                            link_status=r[2], link_source=r[3])
                                for r in link_rows)
        rejected = frozenset(l.session_id for l in existing_links
                              if l.link_status == 'rejected')

        settings = MatcherSettings()
        decision = match_sermon_to_sessions(
            sermon, sessions, existing_links, rejected, settings,
        )

        now = datetime.now().isoformat()
        if decision.action == 'auto_link' and decision.auto_link_target:
            target = decision.auto_link_target.session_id
            existing_auto_active = [l for l in existing_links
                                     if l.link_status == 'active' and l.link_source == 'auto'
                                     and l.session_id != target]
            for l in existing_auto_active:
                conn.execute(
                    "DELETE FROM sermon_links WHERE sermon_id = ? AND session_id = ? AND link_source = 'auto'",
                    (sermon_id, l.session_id),
                )
            has_manual_active = any(
                l.link_status == 'active' and l.link_source == 'manual'
                for l in existing_links
            )
            if not has_manual_active:
                conn.execute("""
                    INSERT OR REPLACE INTO sermon_links
                        (sermon_id, session_id, link_status, link_source, match_reason, created_at)
                    VALUES (?, ?, 'active', 'auto', ?, ?)
                """, (sermon_id, target, decision.auto_link_target.reason, now))
                conn.execute("UPDATE sermons SET match_status = 'matched', last_match_attempt_at = ? WHERE id = ?",
                             (now, sermon_id))
        elif decision.action == 'surface_candidates':
            for c in decision.candidates:
                conn.execute("""
                    INSERT OR IGNORE INTO sermon_links
                        (sermon_id, session_id, link_status, link_source, match_reason, created_at)
                    VALUES (?, ?, 'candidate', 'auto', ?, ?)
                """, (sermon_id, c.session_id, c.reason, now))
            conn.execute("UPDATE sermons SET match_status = 'awaiting_candidates', last_match_attempt_at = ? WHERE id = ?",
                         (now, sermon_id))
        else:
            conn.execute("UPDATE sermons SET last_match_attempt_at = ? WHERE id = ?",
                         (now, sermon_id))

        conn.execute("COMMIT")
        return decision
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def dispatch_matching(db, limit: int = 50) -> int:
    """Match all unmatched sermons to prep sessions. Returns count matched."""
    conn = db._conn()
    rows = conn.execute("""
        SELECT id FROM sermons
        WHERE classified_as = 'sermon'
          AND match_status = 'unmatched'
        ORDER BY preach_date DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    matched = 0
    for (sid,) in rows:
        decision = apply_match_decision_for_sermon(db, sid)
        if decision.action in ('auto_link', 'surface_candidates'):
            matched += 1
    return matched
