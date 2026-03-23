"""Session Analytics — behavioral tracking for sermon study sessions.

Tracks phase time, message patterns, stall detection, outline velocity,
silence gaps, and cross-session patterns. All data stored in SQLite,
silent to the user during active study.
"""

import json
import sqlite3
from datetime import datetime, timezone


class SessionAnalytics:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def init_db(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS phase_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                phase TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS message_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                phase TEXT,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                node_type TEXT,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_phase_events_session
                ON phase_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_message_events_session
                ON message_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_outline_events_session
                ON outline_events(session_id);
        """)
        conn.commit()
        conn.close()

    # ── Phase tracking ──────────────────────────────────────────────────

    def record_phase_enter(self, session_id, phase):
        conn = self._conn()
        conn.execute(
            "INSERT INTO phase_events (session_id, phase, event_type, timestamp) VALUES (?, ?, 'enter', ?)",
            (session_id, phase, self._now()))
        conn.commit()
        conn.close()

    def record_phase_exit(self, session_id, phase):
        conn = self._conn()
        conn.execute(
            "INSERT INTO phase_events (session_id, phase, event_type, timestamp) VALUES (?, ?, 'exit', ?)",
            (session_id, phase, self._now()))
        conn.commit()
        conn.close()

    def get_phase_time_seconds(self, session_id, phase):
        """Calculate total seconds spent in a phase from enter/exit pairs."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT event_type, timestamp FROM phase_events WHERE session_id = ? AND phase = ? ORDER BY timestamp",
            (session_id, phase)).fetchall()
        conn.close()

        total = 0.0
        enter_time = None
        for row in rows:
            ts = datetime.fromisoformat(row['timestamp'])
            if row['event_type'] == 'enter':
                enter_time = ts
            elif row['event_type'] == 'exit' and enter_time is not None:
                total += (ts - enter_time).total_seconds()
                enter_time = None
        return total

    def get_phase_distribution(self, session_id):
        """Return {phase: seconds} for all phases in a session."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT DISTINCT phase FROM phase_events WHERE session_id = ?",
            (session_id,)).fetchall()
        conn.close()
        return {row['phase']: self.get_phase_time_seconds(session_id, row['phase'])
                for row in rows}

    # ── Message tracking ────────────────────────────────────────────────

    def record_message(self, session_id, role, char_count, phase=None):
        conn = self._conn()
        conn.execute(
            "INSERT INTO message_events (session_id, role, char_count, phase, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, char_count, phase, self._now()))
        conn.commit()
        conn.close()

    def get_message_count(self, session_id, role=None):
        conn = self._conn()
        if role:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM message_events WHERE session_id = ? AND role = ?",
                (session_id, role)).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM message_events WHERE session_id = ?",
                (session_id,)).fetchone()
        conn.close()
        return row['cnt']

    def get_average_message_length(self, session_id, role=None):
        conn = self._conn()
        if role:
            row = conn.execute(
                "SELECT AVG(char_count) as avg_len FROM message_events WHERE session_id = ? AND role = ?",
                (session_id, role)).fetchone()
        else:
            row = conn.execute(
                "SELECT AVG(char_count) as avg_len FROM message_events WHERE session_id = ?",
                (session_id,)).fetchone()
        conn.close()
        return row['avg_len'] or 0.0

    # ── Silence / gap detection ─────────────────────────────────────────

    def get_silence_gaps(self, session_id, min_gap_seconds=300):
        """Find gaps between consecutive messages longer than min_gap_seconds."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT timestamp FROM message_events WHERE session_id = ? ORDER BY timestamp",
            (session_id,)).fetchall()
        conn.close()

        gaps = []
        for i in range(1, len(rows)):
            t1 = datetime.fromisoformat(rows[i - 1]['timestamp'])
            t2 = datetime.fromisoformat(rows[i]['timestamp'])
            gap = (t2 - t1).total_seconds()
            if gap >= min_gap_seconds:
                gaps.append({'start': rows[i - 1]['timestamp'],
                             'end': rows[i]['timestamp'],
                             'seconds': gap})
        return gaps

    # ── Outline velocity ────────────────────────────────────────────────

    def record_outline_event(self, session_id, action, node_type=None):
        conn = self._conn()
        conn.execute(
            "INSERT INTO outline_events (session_id, action, node_type, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, action, node_type, self._now()))
        conn.commit()
        conn.close()

    def get_outline_velocity(self, session_id):
        """Return outline adds per hour for this session."""
        conn = self._conn()
        adds = conn.execute(
            "SELECT COUNT(*) as cnt FROM outline_events WHERE session_id = ? AND action = 'add'",
            (session_id,)).fetchone()['cnt']
        timestamps = conn.execute(
            "SELECT MIN(timestamp) as first_t, MAX(timestamp) as last_t FROM outline_events WHERE session_id = ?",
            (session_id,)).fetchone()
        conn.close()

        if not timestamps['first_t'] or not timestamps['last_t'] or adds == 0:
            return 0.0

        first = datetime.fromisoformat(timestamps['first_t'])
        last = datetime.fromisoformat(timestamps['last_t'])
        hours = (last - first).total_seconds() / 3600
        if hours < 0.01:  # less than ~36 seconds
            return float(adds)  # treat as burst
        return adds / hours

    def get_last_outline_event_age(self, session_id):
        """Seconds since the last outline event. Returns None if no events."""
        conn = self._conn()
        row = conn.execute(
            "SELECT MAX(timestamp) as last_t FROM outline_events WHERE session_id = ?",
            (session_id,)).fetchone()
        conn.close()
        if not row['last_t']:
            return None
        last = datetime.fromisoformat(row['last_t'])
        now = datetime.now(timezone.utc)
        return (now - last).total_seconds()

    # ── Stall detection ─────────────────────────────────────────────────

    def detect_stall(self, session_id, outline_stall_minutes=45, message_stall_minutes=10):
        """Check if the session appears stalled.

        Returns dict with 'stalled' bool and 'reason' if stalled.
        """
        outline_age = self.get_last_outline_event_age(session_id)
        if outline_age is not None and outline_age > outline_stall_minutes * 60:
            return {'stalled': True, 'reason': 'outline_stall',
                    'minutes': outline_age / 60}

        conn = self._conn()
        last_msg = conn.execute(
            "SELECT MAX(timestamp) as last_t FROM message_events WHERE session_id = ?",
            (session_id,)).fetchone()
        conn.close()

        if last_msg and last_msg['last_t']:
            last = datetime.fromisoformat(last_msg['last_t'])
            now = datetime.now(timezone.utc)
            gap = (now - last).total_seconds()
            if gap > message_stall_minutes * 60:
                return {'stalled': True, 'reason': 'message_stall',
                        'minutes': gap / 60}

        return {'stalled': False}

    # ── Cross-session patterns ──────────────────────────────────────────

    def get_session_summary(self, session_id):
        """Aggregate summary for a single session."""
        return {
            'session_id': session_id,
            'phase_distribution': self.get_phase_distribution(session_id),
            'message_count': self.get_message_count(session_id),
            'user_messages': self.get_message_count(session_id, role='user'),
            'assistant_messages': self.get_message_count(session_id, role='assistant'),
            'avg_user_msg_length': self.get_average_message_length(session_id, role='user'),
            'outline_velocity': self.get_outline_velocity(session_id),
            'silence_gaps': self.get_silence_gaps(session_id),
        }

    def get_cross_session_phase_averages(self, session_ids):
        """Average phase time across multiple sessions."""
        if not session_ids:
            return {}
        phase_totals = {}
        phase_counts = {}
        for sid in session_ids:
            dist = self.get_phase_distribution(sid)
            for phase, seconds in dist.items():
                phase_totals[phase] = phase_totals.get(phase, 0) + seconds
                phase_counts[phase] = phase_counts.get(phase, 0) + 1
        return {phase: phase_totals[phase] / phase_counts[phase]
                for phase in phase_totals}
