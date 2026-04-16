#!/usr/bin/env python3
"""Backtest sermon_matcher.py over the real database and print a CSV of decisions.

Usage:
    python3 scripts/backtest_matcher.py > backtest.csv

Reads from tools/workbench/companion.db (or COMPANION_DB_PATH if set).
"""
import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'workbench'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from companion_db import CompanionDB
from sermon_matcher import (
    match_sermon_to_sessions, SermonInfo, SessionInfo, SermonLink,
    MatcherSettings,
)


def main():
    db_path = os.environ.get('COMPANION_DB_PATH',
                              os.path.join(os.path.dirname(__file__), '..',
                                            'tools', 'workbench', 'companion.db'))
    db = CompanionDB(db_path)
    conn = db._conn()
    sermons = conn.execute("""
        SELECT id, book, chapter, verse_start, verse_end, preach_date, sermon_type,
               bible_text_raw
        FROM sermons
        WHERE classified_as = 'sermon' AND is_remote_deleted = 0
        ORDER BY preach_date DESC
    """).fetchall()

    writer = csv.writer(sys.stdout)
    writer.writerow(['sermon_id', 'preach_date', 'passage', 'decision', 'tier',
                      'reason', 'linked_session_id'])

    settings = MatcherSettings()
    for s_row in sermons:
        sessions_rows = conn.execute("""
            SELECT id, book, chapter, verse_start, verse_end, created_at,
                   last_homiletical_activity_at
            FROM sessions WHERE book = ? AND chapter = ?
        """, (s_row[1], s_row[2])).fetchall()
        sessions = tuple(SessionInfo(
            id=r[0], book=r[1], chapter=r[2], verse_start=r[3], verse_end=r[4],
            created_at=r[5], last_homiletical_activity_at=r[6],
        ) for r in sessions_rows)
        passage_rows = conn.execute(
            "SELECT book, chapter_start, verse_start, chapter_end, verse_end "
            "FROM sermon_passages WHERE sermon_id = ? ORDER BY rank",
            (s_row[0],)
        ).fetchall()
        passages = [dict(book=r[0], chapter_start=r[1], verse_start=r[2],
                          chapter_end=r[3], verse_end=r[4])
                     for r in passage_rows]
        sermon = SermonInfo(
            id=s_row[0], book=s_row[1], chapter=s_row[2],
            verse_start=s_row[3], verse_end=s_row[4],
            preach_date=s_row[5], sermon_type=s_row[6],
            passages=passages,
        )
        decision = match_sermon_to_sessions(
            sermon, sessions, existing_links=(), rejected_session_ids=frozenset(),
            settings=settings,
        )
        linked_id = (decision.auto_link_target.session_id
                      if decision.auto_link_target else '')
        tier = (decision.auto_link_target.tier
                 if decision.auto_link_target
                 else (decision.candidates[0].tier if decision.candidates else 0))
        writer.writerow([
            s_row[0], s_row[5], s_row[7],
            decision.action, tier, decision.reason_summary, linked_id,
        ])

    conn.close()


if __name__ == '__main__':
    main()
