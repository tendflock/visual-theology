"""
SQLite data layer for the Sermon Research Workbench.

Manages sermon projects, conversation history, research items,
user notes, and generated documents.
"""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "workbench.db"


def _connect(db_path=None):
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path=None):
    """Create all tables if they don't exist."""
    conn = _connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            passage TEXT NOT NULL,
            book_num INTEGER,
            chapter INTEGER,
            verse_start INTEGER,
            verse_end INTEGER,
            theme TEXT,
            current_phase TEXT DEFAULT 'exegesis',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_name TEXT,
            tool_input TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS research_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            item_type TEXT NOT NULL,
            title TEXT,
            source TEXT,
            content TEXT NOT NULL,
            reference TEXT,
            phase TEXT,
            pinned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS project_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            section TEXT DEFAULT 'general',
            content TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            doc_type TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_conv_project
            ON conversations(project_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_research_project
            ON research_items(project_id, item_type);
        CREATE INDEX IF NOT EXISTS idx_notes_project
            ON project_notes(project_id, section);
        CREATE INDEX IF NOT EXISTS idx_docs_project
            ON documents(project_id, doc_type);
    """)
    conn.commit()
    conn.close()


# ── Projects ──────────────────────────────────────────────────────────────

def create_project(passage, theme=None, parsed_ref=None):
    """Create a new sermon project. Returns the project dict."""
    pid = uuid.uuid4().hex[:12]
    conn = _connect()
    book_num = parsed_ref["book"] if parsed_ref else None
    chapter = parsed_ref["chapter"] if parsed_ref else None
    vs = parsed_ref["verse_start"] if parsed_ref else None
    ve = parsed_ref["verse_end"] if parsed_ref else None
    conn.execute(
        """INSERT INTO projects (id, passage, book_num, chapter, verse_start, verse_end, theme)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (pid, passage, book_num, chapter, vs, ve, theme),
    )
    conn.commit()
    project = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone())
    conn.close()
    return project


def get_project(project_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_projects():
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM projects ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_project_phase(project_id, phase):
    conn = _connect()
    conn.execute(
        "UPDATE projects SET current_phase = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (phase, project_id),
    )
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = _connect()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


# ── Conversations ─────────────────────────────────────────────────────────

def add_message(project_id, role, content, tool_name=None, tool_input=None):
    """Add a message to the conversation. Returns the message id."""
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO conversations (project_id, role, content, tool_name, tool_input)
           VALUES (?, ?, ?, ?, ?)""",
        (project_id, role, content, tool_name,
         json.dumps(tool_input) if tool_input else None),
    )
    conn.execute(
        "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (project_id,),
    )
    conn.commit()
    msg_id = cur.lastrowid
    conn.close()
    return msg_id


def get_conversation(project_id, limit=100):
    """Get conversation history for a project."""
    conn = _connect()
    rows = conn.execute(
        """SELECT * FROM conversations
           WHERE project_id = ?
           ORDER BY created_at ASC
           LIMIT ?""",
        (project_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_messages_for_api(project_id, limit=50):
    """Build Claude API messages array from conversation history.

    Groups tool_call and tool_result messages into proper Claude format.
    Validates that every tool_use block has a matching tool_result.
    """
    rows = get_conversation(project_id, limit)
    messages = []
    i = 0
    while i < len(rows):
        row = rows[i]
        role = row["role"]

        if role == "user":
            messages.append({"role": "user", "content": row["content"]})
        elif role == "assistant":
            content_blocks = []
            try:
                parsed = json.loads(row["content"])
                if isinstance(parsed, list):
                    content_blocks = parsed
                else:
                    content_blocks = [{"type": "text", "text": row["content"]}]
            except (json.JSONDecodeError, TypeError):
                content_blocks = [{"type": "text", "text": row["content"]}]
            messages.append({"role": "assistant", "content": content_blocks})
        elif role == "tool_result":
            # Group consecutive tool_results into one user message
            tool_results = []
            while i < len(rows) and rows[i]["role"] == "tool_result":
                r = rows[i]
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": r.get("tool_name", "unknown"),
                    "content": r["content"],
                })
                i += 1
            messages.append({"role": "user", "content": tool_results})
            continue  # skip the i += 1 at the bottom

        i += 1

    # Validate tool_use / tool_result pairing in both directions.
    # Pass 1: For each assistant msg with tool_use, check next msg has results.
    #          For each user msg with tool_results, check prev msg has tool_use.
    validated = []
    for idx, msg in enumerate(messages):
        if msg["role"] == "assistant":
            blocks = msg["content"] if isinstance(msg["content"], list) else []
            tool_use_ids = [
                b["id"] for b in blocks
                if isinstance(b, dict) and b.get("type") == "tool_use"
            ]
            if tool_use_ids:
                # Check if the next message has matching tool_results
                next_msg = messages[idx + 1] if idx + 1 < len(messages) else None
                has_results = False
                if next_msg and next_msg["role"] == "user" and isinstance(next_msg["content"], list):
                    result_ids = {
                        b.get("tool_use_id") for b in next_msg["content"]
                        if isinstance(b, dict) and b.get("type") == "tool_result"
                    }
                    has_results = all(tid in result_ids for tid in tool_use_ids)
                if not has_results:
                    # Strip tool_use blocks, keep only text
                    text_blocks = [b for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
                    if text_blocks:
                        validated.append({"role": "assistant", "content": text_blocks})
                    continue
            validated.append(msg)
        elif msg["role"] == "user" and isinstance(msg["content"], list):
            # User message with tool_results — verify preceding assistant has matching tool_use
            tool_result_ids = {
                b.get("tool_use_id") for b in msg["content"]
                if isinstance(b, dict) and b.get("type") == "tool_result"
            }
            if tool_result_ids:
                # Find the preceding assistant message in validated
                prev_assistant = validated[-1] if validated and validated[-1]["role"] == "assistant" else None
                if prev_assistant and isinstance(prev_assistant["content"], list):
                    prev_tool_ids = {
                        b["id"] for b in prev_assistant["content"]
                        if isinstance(b, dict) and b.get("type") == "tool_use"
                    }
                    # Only keep tool_results that match
                    kept = [
                        b for b in msg["content"]
                        if not (isinstance(b, dict) and b.get("type") == "tool_result")
                        or b.get("tool_use_id") in prev_tool_ids
                    ]
                    if kept:
                        validated.append({"role": "user", "content": kept})
                    # else: drop orphaned tool_results entirely
                else:
                    # No preceding assistant with tool_use — drop this message
                    pass
            else:
                validated.append(msg)
        else:
            validated.append(msg)

    # Ensure messages alternate user/assistant properly and start with user
    final = []
    for msg in validated:
        if not final:
            if msg["role"] == "user":
                final.append(msg)
        elif msg["role"] == final[-1]["role"]:
            # Merge consecutive same-role messages
            if msg["role"] == "user":
                final[-1] = msg
            else:
                if isinstance(final[-1]["content"], list) and isinstance(msg["content"], list):
                    final[-1]["content"].extend(msg["content"])
                else:
                    final[-1] = msg
        else:
            final.append(msg)

    # Final safety: ensure it ends with user (Claude requires this for new response)
    # This is already handled by the caller appending the new user message.
    return final


# ── Research Items ────────────────────────────────────────────────────────

def add_research_item(project_id, item_type, content, title=None,
                      source=None, reference=None, phase=None):
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO research_items
           (project_id, item_type, title, source, content, reference, phase)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (project_id, item_type, title, source, content, reference, phase),
    )
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return item_id


def get_research_items(project_id, item_type=None):
    conn = _connect()
    if item_type:
        rows = conn.execute(
            """SELECT * FROM research_items
               WHERE project_id = ? AND item_type = ?
               ORDER BY created_at ASC""",
            (project_id, item_type),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM research_items
               WHERE project_id = ?
               ORDER BY created_at ASC""",
            (project_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def pin_research_item(item_id, pinned=True):
    conn = _connect()
    conn.execute(
        "UPDATE research_items SET pinned = ? WHERE id = ?",
        (1 if pinned else 0, item_id),
    )
    conn.commit()
    conn.close()


# ── Notes ─────────────────────────────────────────────────────────────────

def save_note(project_id, content, section="general"):
    """Upsert a note for a project section."""
    conn = _connect()
    existing = conn.execute(
        "SELECT id FROM project_notes WHERE project_id = ? AND section = ?",
        (project_id, section),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE project_notes
               SET content = ?, updated_at = CURRENT_TIMESTAMP
               WHERE project_id = ? AND section = ?""",
            (content, project_id, section),
        )
    else:
        conn.execute(
            """INSERT INTO project_notes (project_id, section, content)
               VALUES (?, ?, ?)""",
            (project_id, section, content),
        )
    conn.commit()
    conn.close()


def get_notes(project_id, section=None):
    conn = _connect()
    if section:
        rows = conn.execute(
            "SELECT * FROM project_notes WHERE project_id = ? AND section = ?",
            (project_id, section),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM project_notes WHERE project_id = ? ORDER BY section",
            (project_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Documents ─────────────────────────────────────────────────────────────

def save_document(project_id, doc_type, content):
    """Save a new version of a document."""
    conn = _connect()
    # Get current max version
    row = conn.execute(
        "SELECT MAX(version) FROM documents WHERE project_id = ? AND doc_type = ?",
        (project_id, doc_type),
    ).fetchone()
    version = (row[0] or 0) + 1
    conn.execute(
        """INSERT INTO documents (project_id, doc_type, content, version)
           VALUES (?, ?, ?, ?)""",
        (project_id, doc_type, content, version),
    )
    conn.commit()
    conn.close()
    return version


def get_document(project_id, doc_type, version=None):
    conn = _connect()
    if version:
        row = conn.execute(
            """SELECT * FROM documents
               WHERE project_id = ? AND doc_type = ? AND version = ?""",
            (project_id, doc_type, version),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT * FROM documents
               WHERE project_id = ? AND doc_type = ?
               ORDER BY version DESC LIMIT 1""",
            (project_id, doc_type),
        ).fetchone()
    conn.close()
    return dict(row) if row else None
