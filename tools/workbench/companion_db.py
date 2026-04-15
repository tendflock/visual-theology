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
            CREATE TABLE IF NOT EXISTS card_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                phase TEXT NOT NULL,
                source TEXT,
                starred_text TEXT,
                note TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS card_notepads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                phase TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(session_id, phase)
            );
            CREATE INDEX IF NOT EXISTS idx_card_responses_session ON card_responses(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_messages(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_outline_session ON outline_nodes(session_id);
            CREATE INDEX IF NOT EXISTS idx_outline_parent ON outline_nodes(parent_id);
            CREATE INDEX IF NOT EXISTS idx_questions_phase ON question_bank(phase, priority);
            CREATE INDEX IF NOT EXISTS idx_card_annotations_session ON card_annotations(session_id, phase);
            CREATE INDEX IF NOT EXISTS idx_card_notepads_session ON card_notepads(session_id, phase);
        """)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sermons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermonaudio_id TEXT UNIQUE NOT NULL,
                broadcaster_id TEXT NOT NULL,
                title TEXT NOT NULL,
                speaker_name TEXT,
                event_type TEXT,
                series TEXT,
                preach_date TEXT,
                publish_date TEXT,
                duration_seconds INTEGER,
                bible_text_raw TEXT,
                book INTEGER,
                chapter INTEGER,
                verse_start INTEGER,
                verse_end INTEGER,
                audio_url TEXT,
                transcript_text TEXT,
                transcript_source TEXT DEFAULT 'sermonaudio',
                sermon_type TEXT NOT NULL DEFAULT 'expository' CHECK (sermon_type IN ('expository','topical')),
                classified_as TEXT NOT NULL CHECK (classified_as IN ('sermon','skipped')),
                classification_reason TEXT,
                metadata_hash TEXT,
                transcript_hash TEXT,
                source_version INTEGER NOT NULL DEFAULT 1,
                remote_updated_at TEXT,
                sync_status TEXT NOT NULL DEFAULT 'pending_sync' CHECK (sync_status IN (
                    'pending_sync','synced_metadata','transcript_ready',
                    'analysis_pending','analysis_running','review_ready',
                    'sync_failed','analysis_failed','analysis_skipped','permanent_failure'
                )),
                sync_error TEXT,
                failure_count INTEGER NOT NULL DEFAULT 0 CHECK (failure_count >= 0),
                last_failure_at TEXT,
                last_state_change_at TEXT NOT NULL,
                last_match_attempt_at TEXT,
                match_status TEXT NOT NULL DEFAULT 'unmatched' CHECK (match_status IN (
                    'unmatched','matched','awaiting_candidates',
                    'unparseable_passage','topical_no_match','rejected_all'
                )),
                is_remote_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_remote_deleted IN (0, 1)),
                deleted_at TEXT,
                ui_last_seen_version INTEGER NOT NULL DEFAULT 0,
                first_synced_at TEXT NOT NULL,
                last_synced_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sermons_sermonaudio_id ON sermons(sermonaudio_id);
            CREATE INDEX IF NOT EXISTS idx_sermons_preach_date ON sermons(preach_date DESC);
            CREATE INDEX IF NOT EXISTS idx_sermons_sync_status ON sermons(sync_status);
            CREATE INDEX IF NOT EXISTS idx_sermons_classified ON sermons(classified_as);
            CREATE INDEX IF NOT EXISTS idx_sermons_match_status ON sermons(match_status);
            CREATE INDEX IF NOT EXISTS idx_sermons_book_chapter ON sermons(book, chapter);

            CREATE TABLE IF NOT EXISTS sermon_passages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
                rank INTEGER NOT NULL,
                book INTEGER NOT NULL,
                chapter_start INTEGER NOT NULL,
                verse_start INTEGER,
                chapter_end INTEGER NOT NULL,
                verse_end INTEGER,
                raw_text TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(sermon_id, rank)
            );
            CREATE INDEX IF NOT EXISTS idx_sermon_passages_sermon ON sermon_passages(sermon_id);
            CREATE INDEX IF NOT EXISTS idx_sermon_passages_lookup ON sermon_passages(book, chapter_start);

            CREATE TABLE IF NOT EXISTS sermon_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                link_status TEXT NOT NULL CHECK (link_status IN ('active','candidate','rejected')),
                link_source TEXT NOT NULL CHECK (link_source IN ('auto','manual')),
                match_reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(sermon_id, session_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_sermon_links_one_active
                ON sermon_links(sermon_id) WHERE link_status = 'active';
            CREATE INDEX IF NOT EXISTS idx_sermon_links_sermon ON sermon_links(sermon_id);
            CREATE INDEX IF NOT EXISTS idx_sermon_links_session ON sermon_links(session_id);

            CREATE TABLE IF NOT EXISTS sermon_reviews (
                sermon_id INTEGER PRIMARY KEY REFERENCES sermons(id) ON DELETE CASCADE,
                analyzer_version TEXT NOT NULL,
                homiletics_core_version TEXT NOT NULL,
                model_version TEXT,
                analyzed_transcript_hash TEXT NOT NULL,
                source_version_at_analysis INTEGER NOT NULL,
                burden_clarity TEXT CHECK (burden_clarity IN ('crisp','clear','implied','muddled','absent')),
                burden_statement_excerpt TEXT,
                burden_first_stated_at_sec INTEGER,
                movement_clarity TEXT CHECK (movement_clarity IN ('river','mostly_river','uneven','lake')),
                movement_rationale TEXT,
                application_specificity TEXT CHECK (application_specificity IN ('localized','concrete','abstract','absent')),
                application_first_arrived_at_sec INTEGER,
                application_excerpts TEXT,
                ethos_rating TEXT CHECK (ethos_rating IN ('seized','engaged','professional','detached')),
                ethos_markers TEXT,
                concreteness_score INTEGER CHECK (concreteness_score BETWEEN 1 AND 5),
                imagery_density_per_10min REAL,
                narrative_moments TEXT,
                christ_thread_score TEXT CHECK (christ_thread_score IN ('explicit','gestured','absent')),
                christ_thread_excerpts TEXT,
                exegetical_grounding TEXT CHECK (exegetical_grounding IN ('grounded','partial','pretext')),
                exegetical_grounding_notes TEXT,
                actual_duration_seconds INTEGER NOT NULL,
                planned_duration_seconds INTEGER,
                duration_delta_seconds INTEGER,
                section_timings TEXT,
                length_delta_commentary TEXT,
                density_hotspots TEXT,
                late_application_note TEXT,
                outline_coverage_pct REAL,
                outline_additions TEXT,
                outline_omissions TEXT,
                outline_drift_note TEXT,
                top_impact_helpers TEXT NOT NULL,
                top_impact_hurters TEXT NOT NULL,
                faithfulness_note TEXT,
                one_change_for_next_sunday TEXT NOT NULL,
                computed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sermon_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
                flag_type TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('info','note','warn','concern')),
                transcript_start_sec INTEGER,
                transcript_end_sec INTEGER,
                section_label TEXT,
                excerpt TEXT,
                rationale TEXT NOT NULL,
                analyzer_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sermon_flags_sermon ON sermon_flags(sermon_id);
            CREATE INDEX IF NOT EXISTS idx_sermon_flags_type ON sermon_flags(flag_type);

            CREATE TABLE IF NOT EXISTS sermon_coach_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermon_id INTEGER REFERENCES sermons(id) ON DELETE CASCADE,
                session_id INTEGER REFERENCES sessions(id),
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user','assistant','tool','tool_result')),
                content TEXT,
                tool_name TEXT,
                tool_input TEXT,
                tool_result TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_coach_messages_sermon ON sermon_coach_messages(sermon_id);
            CREATE INDEX IF NOT EXISTS idx_coach_messages_session ON sermon_coach_messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_coach_messages_conv ON sermon_coach_messages(conversation_id);

            CREATE TABLE IF NOT EXISTS sermon_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                trigger TEXT NOT NULL CHECK (trigger IN ('cron','manual','backfill')),
                started_at TEXT NOT NULL,
                ended_at TEXT,
                sermons_fetched INTEGER DEFAULT 0,
                sermons_new INTEGER DEFAULT 0,
                sermons_updated INTEGER DEFAULT 0,
                sermons_noop INTEGER DEFAULT 0,
                sermons_skipped INTEGER DEFAULT 0,
                sermons_failed INTEGER DEFAULT 0,
                error_summary TEXT,
                status TEXT NOT NULL CHECK (status IN ('running','completed','failed'))
            );

            CREATE TABLE IF NOT EXISTS sermon_analysis_cost_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                estimated_cost_usd REAL NOT NULL,
                called_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cost_log_sermon ON sermon_analysis_cost_log(sermon_id);
            CREATE INDEX IF NOT EXISTS idx_cost_log_called ON sermon_analysis_cost_log(called_at DESC);
        """)
        existing_session_cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        if 'last_homiletical_activity_at' not in existing_session_cols:
            conn.execute("ALTER TABLE sessions ADD COLUMN last_homiletical_activity_at TEXT")
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
        now = self._now()
        cur = conn.execute("""
            INSERT INTO card_responses (session_id, phase, question_id, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, phase, question_id, content, now))
        if phase in ('exegetical_point', 'fcf_homiletical', 'sermon_construction', 'edit_pray'):
            conn.execute(
                "UPDATE sessions SET last_homiletical_activity_at = ?, updated_at = ? WHERE id = ?",
                (now, now, session_id),
            )
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
        now = self._now()
        cur = conn.execute("""
            INSERT INTO conversation_messages (session_id, phase, role, content, tool_name, tool_input, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, phase, role, content, tool_name, tool_input, now))
        if phase in ('exegetical_point', 'fcf_homiletical', 'sermon_construction', 'edit_pray'):
            conn.execute(
                "UPDATE sessions SET last_homiletical_activity_at = ?, updated_at = ? WHERE id = ?",
                (now, now, session_id),
            )
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

    def save_card_annotation(self, session_id, phase, source, starred_text, note=""):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO card_annotations (session_id, phase, source, starred_text, note) VALUES (?, ?, ?, ?, ?)",
            (session_id, phase, source, starred_text, note))
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return aid

    def get_card_annotations(self, session_id, phase=None):
        conn = self._conn()
        if phase:
            rows = conn.execute(
                "SELECT id, source, starred_text, note, created_at FROM card_annotations WHERE session_id = ? AND phase = ? ORDER BY created_at",
                (session_id, phase)).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, source, starred_text, note, created_at FROM card_annotations WHERE session_id = ? ORDER BY created_at",
                (session_id,)).fetchall()
        conn.close()
        return [{"id": r[0], "source": r[1], "starred_text": r[2], "note": r[3], "created_at": r[4]} for r in rows]

    def save_card_notepad(self, session_id, phase, content):
        conn = self._conn()
        conn.execute(
            "INSERT INTO card_notepads (session_id, phase, content) VALUES (?, ?, ?) ON CONFLICT(session_id, phase) DO UPDATE SET content = ?, updated_at = datetime('now')",
            (session_id, phase, content, content))
        conn.commit()
        conn.close()

    def get_card_notepad(self, session_id, phase):
        conn = self._conn()
        row = conn.execute(
            "SELECT content FROM card_notepads WHERE session_id = ? AND phase = ?",
            (session_id, phase)).fetchone()
        conn.close()
        return row[0] if row else ""
