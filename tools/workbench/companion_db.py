import sqlite3
import json
from datetime import datetime, timezone

PHASE_TIMERS = {
    'prayer': 900,
    'text_work': 7200,
    'digestion': 3600,
    'observation': 3600,
    'word_study': 1800,
    'context': 2700,
    'theological': 7200,
    'commentary': 1800,
    'exegetical_point': 1800,
    'fcf_homiletical': 1800,
    'sermon_construction': 10800,
    'edit_pray': 5400,
}

PHASES_ORDER = list(PHASE_TIMERS.keys())

class CompanionDB:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passage_ref TEXT NOT NULL,
                book INTEGER NOT NULL,
                chapter INTEGER NOT NULL,
                verse_start INTEGER,
                verse_end INTEGER,
                genre TEXT NOT NULL,
                current_phase TEXT NOT NULL DEFAULT 'prayer',
                current_question_id INTEGER,
                timer_remaining_seconds INTEGER NOT NULL DEFAULT 900,
                timer_paused INTEGER NOT NULL DEFAULT 0,
                total_elapsed_seconds INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS card_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                phase TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                saved_to_outline INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                phase TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_name TEXT,
                tool_input TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outline_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                parent_id INTEGER REFERENCES outline_nodes(id),
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                verse_ref TEXT,
                rank INTEGER NOT NULL DEFAULT 0,
                flags TEXT DEFAULT '{}',
                source_type TEXT,
                source_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase TEXT NOT NULL,
                question_text TEXT NOT NULL,
                guidance_text TEXT,
                genre_tags TEXT NOT NULL DEFAULT '[]',
                priority TEXT NOT NULL DEFAULT 'core',
                resource_type TEXT DEFAULT 'none',
                rank INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_card_responses_session ON card_responses(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_messages(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_outline_session ON outline_nodes(session_id);
            CREATE INDEX IF NOT EXISTS idx_outline_parent ON outline_nodes(parent_id);
            CREATE INDEX IF NOT EXISTS idx_questions_phase ON question_bank(phase, priority);
        """)
        conn.commit()
        conn.close()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def create_session(self, passage_ref, book, chapter, verse_start, verse_end, genre):
        conn = self._conn()
        now = self._now()
        cur = conn.execute("""
            INSERT INTO sessions (passage_ref, book, chapter, verse_start, verse_end, genre,
                                  current_phase, timer_remaining_seconds, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'prayer', ?, ?, ?)
        """, (passage_ref, book, chapter, verse_start, verse_end, genre,
              PHASE_TIMERS['prayer'], now, now))
        conn.commit()
        sid = cur.lastrowid
        conn.close()
        return sid

    def get_session(self, session_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_sessions(self, status=None):
        conn = self._conn()
        if status:
            rows = conn.execute("SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_phase(self, session_id, phase, timer_seconds=None):
        if timer_seconds is None:
            timer_seconds = PHASE_TIMERS.get(phase, 1800)
        conn = self._conn()
        conn.execute("""
            UPDATE sessions SET current_phase = ?, timer_remaining_seconds = ?,
                               timer_paused = 0, updated_at = ?
            WHERE id = ?
        """, (phase, timer_seconds, self._now(), session_id))
        conn.commit()
        conn.close()

    def save_card_response(self, session_id, phase, question_id, content):
        conn = self._conn()
        cur = conn.execute("""
            INSERT INTO card_responses (session_id, phase, question_id, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, phase, question_id, content, self._now()))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def get_card_responses(self, session_id, phase=None):
        conn = self._conn()
        if phase:
            rows = conn.execute("SELECT * FROM card_responses WHERE session_id = ? AND phase = ? ORDER BY created_at", (session_id, phase)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM card_responses WHERE session_id = ? ORDER BY created_at", (session_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_message(self, session_id, phase, role, content, tool_name=None, tool_input=None):
        conn = self._conn()
        cur = conn.execute("""
            INSERT INTO conversation_messages (session_id, phase, role, content, tool_name, tool_input, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, phase, role, content, tool_name, tool_input, self._now()))
        conn.commit()
        mid = cur.lastrowid
        conn.close()
        return mid

    def get_messages(self, session_id, phase=None, limit=50):
        conn = self._conn()
        if phase:
            rows = conn.execute("""
                SELECT * FROM conversation_messages
                WHERE session_id = ? AND phase = ?
                ORDER BY created_at DESC LIMIT ?
            """, (session_id, phase, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (session_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in reversed(rows)]

    def add_outline_node(self, session_id, node_type, content, parent_id=None,
                         verse_ref=None, rank=0, flags=None, source_type=None, source_id=None):
        conn = self._conn()
        now = self._now()
        if rank == 0 and parent_id is not None:
            row = conn.execute("SELECT MAX(rank) as max_rank FROM outline_nodes WHERE session_id = ? AND parent_id = ?",
                               (session_id, parent_id)).fetchone()
            rank = (row['max_rank'] or 0) + 1
        elif rank == 0 and parent_id is None:
            row = conn.execute("SELECT MAX(rank) as max_rank FROM outline_nodes WHERE session_id = ? AND parent_id IS NULL",
                               (session_id,)).fetchone()
            rank = (row['max_rank'] or 0) + 1
        cur = conn.execute("""
            INSERT INTO outline_nodes (session_id, parent_id, type, content, verse_ref, rank,
                                       flags, source_type, source_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, parent_id, node_type, content, verse_ref, rank,
              json.dumps(flags or {}), source_type, source_id, now, now))
        conn.commit()
        nid = cur.lastrowid
        conn.close()
        return nid

    def get_outline_tree(self, session_id):
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM outline_nodes WHERE session_id = ? ORDER BY rank
        """, (session_id,)).fetchall()
        conn.close()
        nodes = [dict(r) for r in rows]
        for n in nodes:
            n['flags'] = json.loads(n['flags']) if n['flags'] else {}
        return self._build_tree(nodes)

    def _build_tree(self, nodes):
        by_id = {n['id']: {**n, 'children': []} for n in nodes}
        roots = []
        for n in nodes:
            node = by_id[n['id']]
            if n['parent_id'] and n['parent_id'] in by_id:
                by_id[n['parent_id']]['children'].append(node)
            else:
                roots.append(node)
        return roots

    def update_outline_node(self, node_id, content=None, node_type=None, rank=None, flags=None):
        conn = self._conn()
        updates = []
        params = []
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if node_type is not None:
            updates.append("type = ?")
            params.append(node_type)
        if rank is not None:
            updates.append("rank = ?")
            params.append(rank)
        if flags is not None:
            updates.append("flags = ?")
            params.append(json.dumps(flags))
        updates.append("updated_at = ?")
        params.append(self._now())
        params.append(node_id)
        conn.execute(f"UPDATE outline_nodes SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def delete_outline_node(self, node_id):
        conn = self._conn()
        conn.execute("DELETE FROM outline_nodes WHERE parent_id = ?", (node_id,))
        conn.execute("DELETE FROM outline_nodes WHERE id = ?", (node_id,))
        conn.commit()
        conn.close()

    def get_questions(self, phase, genre=None, priority=None):
        conn = self._conn()
        query = "SELECT * FROM question_bank WHERE phase = ?"
        params = [phase]
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY rank"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        questions = [dict(r) for r in rows]
        if genre:
            questions = [q for q in questions
                         if genre in json.loads(q['genre_tags']) or not json.loads(q['genre_tags'])]
        return questions

    def get_question(self, question_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM question_bank WHERE id = ?", (question_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_timer(self, session_id, remaining_seconds, paused=None, elapsed_delta=0):
        conn = self._conn()
        if paused is not None:
            conn.execute("""
                UPDATE sessions SET timer_remaining_seconds = ?, timer_paused = ?,
                       total_elapsed_seconds = total_elapsed_seconds + ?, updated_at = ?
                WHERE id = ?
            """, (remaining_seconds, int(paused), elapsed_delta, self._now(), session_id))
        else:
            conn.execute("""
                UPDATE sessions SET timer_remaining_seconds = ?,
                       total_elapsed_seconds = total_elapsed_seconds + ?, updated_at = ?
                WHERE id = ?
            """, (remaining_seconds, elapsed_delta, self._now(), session_id))
        conn.commit()
        conn.close()

    def complete_session(self, session_id):
        conn = self._conn()
        conn.execute("UPDATE sessions SET status = 'completed', updated_at = ? WHERE id = ?",
                     (self._now(), session_id))
        conn.commit()
        conn.close()
