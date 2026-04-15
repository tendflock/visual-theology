"""Tools the sermon coach agent uses for depth reads.

All read-only. Override / reanalyze are deferred to Phase 2 per the MVP spec.
"""

from __future__ import annotations
import json
from typing import Optional
from homiletics_core import corpus_gate_status


def _dict(row, cursor_desc):
    if row is None:
        return None
    return {cursor_desc[i][0]: row[i] for i in range(len(cursor_desc))}


def get_sermon_review(db, sermon_id: int) -> Optional[dict]:
    """Fetch the full sermon_reviews row for a sermon."""
    conn = db._conn()
    cur = conn.execute("SELECT * FROM sermon_reviews WHERE sermon_id = ?", (sermon_id,))
    row = cur.fetchone()
    desc = cur.description
    conn.close()
    if row is None:
        return None
    review = _dict(row, desc)
    for field in ('application_excerpts', 'ethos_markers', 'narrative_moments',
                   'christ_thread_excerpts', 'section_timings', 'density_hotspots',
                   'outline_additions', 'outline_omissions',
                   'top_impact_helpers', 'top_impact_hurters'):
        if review.get(field):
            try:
                review[field] = json.loads(review[field])
            except (TypeError, ValueError):
                pass
    return review


def get_sermon_flags(db, sermon_id: int) -> list:
    """Fetch all flags for a sermon, ordered by transcript position."""
    conn = db._conn()
    cur = conn.execute("""
        SELECT id, flag_type, severity, transcript_start_sec, transcript_end_sec,
               section_label, excerpt, rationale, created_at
        FROM sermon_flags WHERE sermon_id = ?
        ORDER BY transcript_start_sec
    """, (sermon_id,))
    rows = cur.fetchall()
    desc = cur.description
    conn.close()
    return [_dict(r, desc) for r in rows]


def get_transcript_full(db, sermon_id: int,
                        start_sec: Optional[int] = None,
                        end_sec: Optional[int] = None) -> Optional[str]:
    """Return the raw transcript text. MVP: slicing approximated linearly from
    text length; returns the whole text if start/end are None.
    """
    conn = db._conn()
    row = conn.execute(
        "SELECT transcript_text, duration_seconds FROM sermons WHERE id = ?",
        (sermon_id,)
    ).fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    text, duration = row[0], row[1] or 0
    if start_sec is None and end_sec is None:
        return text
    if duration <= 0:
        return text
    start_idx = int(len(text) * (start_sec / duration)) if start_sec else 0
    end_idx = int(len(text) * (end_sec / duration)) if end_sec else len(text)
    return text[start_idx:end_idx]


def get_prep_session_full(db, sermon_id: int) -> Optional[dict]:
    """Fetch the linked prep session: outline + card responses + homiletical messages.

    Returns None if the sermon has no active link.
    """
    conn = db._conn()
    link = conn.execute(
        "SELECT session_id FROM sermon_links WHERE sermon_id = ? AND link_status = 'active'",
        (sermon_id,)
    ).fetchone()
    if not link:
        conn.close()
        return None
    session_id = link[0]
    session_row = conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    outline = conn.execute(
        "SELECT id, type, content, rank FROM outline_nodes WHERE session_id = ? ORDER BY rank",
        (session_id,)
    ).fetchall()
    cards = conn.execute(
        "SELECT phase, question_id, content, created_at FROM card_responses WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    ).fetchall()
    homiletical_msgs = conn.execute("""
        SELECT phase, role, content, created_at FROM conversation_messages
        WHERE session_id = ? AND phase IN ('exegetical_point','fcf_homiletical','sermon_construction','edit_pray')
        ORDER BY created_at
    """, (session_id,)).fetchall()
    conn.close()
    return {
        'session': dict(session_row) if session_row else None,
        'outline': [{'id': r[0], 'type': r[1], 'content': r[2], 'rank': r[3]} for r in outline],
        'card_responses': [{'phase': r[0], 'question_id': r[1], 'content': r[2], 'created_at': r[3]} for r in cards],
        'homiletical_messages': [{'phase': r[0], 'role': r[1], 'content': r[2], 'created_at': r[3]} for r in homiletical_msgs],
    }


def pull_historical_sermons(db, n: int = 5, filter_expr: Optional[str] = None) -> list:
    """Return the N most recent classified-sermon rows with their review."""
    conn = db._conn()
    rows = conn.execute("""
        SELECT s.id, s.title, s.preach_date, s.duration_seconds,
               sr.burden_clarity, sr.application_specificity, sr.ethos_rating,
               sr.christ_thread_score, sr.duration_delta_seconds, sr.one_change_for_next_sunday
        FROM sermons s
        LEFT JOIN sermon_reviews sr ON sr.sermon_id = s.id
        WHERE s.classified_as = 'sermon' AND s.is_remote_deleted = 0
        ORDER BY s.preach_date DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [
        {
            'id': r[0], 'title': r[1], 'preach_date': r[2], 'duration_seconds': r[3],
            'burden_clarity': r[4], 'application_specificity': r[5],
            'ethos_rating': r[6], 'christ_thread_score': r[7],
            'duration_delta_seconds': r[8], 'one_change_for_next_sunday': r[9],
        }
        for r in rows
    ]


def get_sermon_patterns(db, window_days: int = 90) -> dict:
    """Compute rolling aggregates over sermons in the window.

    Returns a dict including corpus_gate_status so the coach knows what
    longitudinal voice it is allowed to use.
    """
    conn = db._conn()
    row = conn.execute(f"""
        SELECT
            COUNT(*),
            AVG(sr.duration_delta_seconds),
            1.0 * SUM(CASE WHEN sr.burden_clarity IN ('crisp','clear') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.movement_clarity IN ('river','mostly_river') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.application_specificity IN ('localized','concrete') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.ethos_rating IN ('seized','engaged') THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            AVG(sr.concreteness_score),
            1.0 * SUM(CASE WHEN sr.christ_thread_score = 'explicit' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            1.0 * SUM(CASE WHEN sr.exegetical_grounding = 'grounded' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0),
            AVG(sr.outline_coverage_pct)
        FROM sermon_reviews sr
        JOIN sermons s ON s.id = sr.sermon_id
        WHERE s.preach_date >= date('now', '-{window_days} days')
          AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
    """).fetchone()
    conn.close()

    n = row[0] or 0
    return {
        'n_sermons': n,
        'corpus_gate_status': corpus_gate_status(n),
        'avg_duration_delta_sec': row[1],
        'burden_clear_rate': row[2],
        'movement_clear_rate': row[3],
        'application_concrete_rate': row[4],
        'ethos_engaged_rate': row[5],
        'avg_concreteness': row[6],
        'christ_explicit_rate': row[7],
        'exegetical_grounded_rate': row[8],
        'avg_outline_coverage': row[9],
        'window_days': window_days,
    }
