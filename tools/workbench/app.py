#!/usr/bin/env python3
"""
Sermon Research Workbench — Flask application.

Run:
    cd /Volumes/External/Logos4/tools/workbench
    python3 app.py
    # Open http://localhost:5111
"""

import atexit
import json
import os
import sys
from pathlib import Path

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file if present (simple key=value parsing)
_env_file = TOOLS_DIR / "workbench" / ".env"
if not _env_file.exists():
    _env_file = TOOLS_DIR.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k.strip(), v)

import bcrypt
import sqlite3
from functools import wraps
from flask import Flask, Response, render_template, request, jsonify, redirect, url_for, session, make_response, Blueprint, abort

import workbench_db as db
from workbench_agent import stream_agent_response, PHASES
from study import (
    init_batch_reader, shutdown_batch_reader, parse_reference,
    find_bibles, find_commentaries_for_ref, find_lexicons,
    read_bible_chapter, extract_verses, clean_bible_text, read_annotations,
    get_interlinear_for_chapter, run_reader, read_article_text,
    resolve_bible_files, find_study_bible_notes, CATALOG_DB, RESOURCE_MGR_DB,
)
from companion_db import CompanionDB, PHASES_ORDER, PHASE_TIMERS
from companion_agent import stream_companion_response, PHASE_DESCRIPTIONS
from companion_agent import build_study_prompt, stream_study_response
from session_analytics import SessionAnalytics
from genre_map import get_genre
from seed_questions import seed_question_bank
from app_secrets import sermonaudio_api_key, sermonaudio_broadcaster_id, anthropic_api_key

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    _APSCHEDULER_AVAILABLE = True
except ImportError:
    _APSCHEDULER_AVAILABLE = False

_scheduler = None


def _scheduled_sermon_sync():
    """The 4h cron body. Sync → match → analyze."""
    try:
        from sermonaudio_sync import run_sync
        from sermon_matcher import dispatch_matching
        from sermon_analyzer import dispatch_pending_analyses
        from llm_client import AnthropicClient
        db = get_db()
        run_sync(db, client=_make_sermonaudio_client(),
                 broadcaster_id=_broadcaster_id(), trigger='cron')
        dispatch_matching(db)
        client = AnthropicClient(api_key=anthropic_api_key())
        dispatch_pending_analyses(db, llm_client=client)
    except Exception as e:
        app.logger.error(f'Scheduled sermon sync failed: {e}')


def get_scheduler():
    """Return the singleton background scheduler. Lazy-initializes on first call.

    NOTE: Calling this starts a daemon thread. Production code should call this
    from the __main__ block. Tests can call it to inspect job registration.
    """
    global _scheduler
    if not _APSCHEDULER_AVAILABLE:
        raise RuntimeError('apscheduler not installed')
    if _scheduler is None:
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _scheduled_sermon_sync,
            IntervalTrigger(hours=4),
            id='sermon_sync_cron',
            replace_existing=True,
        )
        _scheduler.start()
    return _scheduler


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32).hex())

# ── Auth (shared with MightyOaks LMS admin) ──────────────────────────────

LMS_DB_PATH = "/Volumes/NetworkStorage/hybrid/data/lms.db"

def verify_admin(username, password):
    """Check credentials against MightyOaks LMS admins table."""
    try:
        conn = sqlite3.connect(LMS_DB_PATH)
        row = conn.execute(
            "SELECT password_hash FROM admins WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if row and bcrypt.checkpw(password.encode(), row[0].encode()):
            return True
    except Exception:
        pass
    return False

LOGIN_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sermon Tool — Login</title>
<style>
  body{font-family:system-ui,sans-serif;display:flex;justify-content:center;align-items:center;
       min-height:100vh;margin:0;background:#1a1a2e;color:#e0e0e0}
  form{background:#16213e;padding:2rem;border-radius:12px;width:320px;box-shadow:0 4px 24px rgba(0,0,0,.4)}
  h2{margin:0 0 1.5rem;text-align:center;color:#a8d8ea}
  input{width:100%;padding:.75rem;margin:.5rem 0;border:1px solid #333;border-radius:6px;
        background:#0f3460;color:#e0e0e0;box-sizing:border-box;font-size:1rem}
  button{width:100%;padding:.75rem;margin-top:1rem;border:none;border-radius:6px;
         background:#e94560;color:#fff;font-size:1rem;cursor:pointer;font-weight:600}
  button:hover{background:#c73e54}
  .err{color:#e94560;text-align:center;margin-top:.5rem;font-size:.9rem}
</style></head><body>
<form method="POST" action="/login">
  <h2>Sermon Tool</h2>
  <input name="username" placeholder="Username" required autofocus>
  <input name="password" type="password" placeholder="Password" required>
  <button type="submit">Log In</button>
  {error}
</form></body></html>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return LOGIN_PAGE.replace("{error}", "")
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if verify_admin(username, password):
        session["authenticated"] = True
        return redirect("/")
    return LOGIN_PAGE.replace("{error}", '<p class="err">Invalid credentials</p>')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.before_request
def require_auth():
    if request.path == "/login" or request.path.startswith("/static/"):
        return
    if not session.get("authenticated"):
        return redirect("/login")
    # Redirect root to the study tool
    if request.path == "/":
        return redirect("/study/")


# ── Jinja Filters ────────────────────────────────────────────────────────

@app.template_filter('safe_assistant')
def safe_assistant_filter(content):
    """Render assistant message content, which may be JSON with tool_use blocks."""
    from markupsafe import escape, Markup
    try:
        blocks = json.loads(content)
        if isinstance(blocks, list):
            parts = []
            for block in blocks:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(str(escape(block.get("text", ""))))
                    elif block.get("type") == "tool_use":
                        name = escape(block.get("name", ""))
                        parts.append(f'<span class="ri-type">{name}</span>')
            return Markup("<br>".join(parts)) if parts else escape(content)
    except (json.JSONDecodeError, TypeError):
        pass
    return escape(content)


# ── Lifecycle ─────────────────────────────────────────────────────────────

companion_db = None
study_analytics = None

# Module-level cache for get_db() — tests reset this via `_db_instance = None`
# to force re-creation after monkeypatching COMPANION_DB_PATH.
_db_instance = None

def get_db():
    """Return a cached CompanionDB instance, honoring COMPANION_DB_PATH.

    This is the entrypoint used by the sermons blueprint (and tests).
    It lazily instantiates a CompanionDB the first time it's called (or
    after `_db_instance` is reset to None). Existing routes continue to
    use the module-level `companion_db` global initialized by startup().
    """
    global _db_instance
    if _db_instance is None:
        db_path = os.environ.get(
            "COMPANION_DB_PATH",
            str(TOOLS_DIR / "workbench" / "companion.db"),
        )
        _db_instance = CompanionDB(db_path)
    return _db_instance


def startup():
    db.init_db()
    init_batch_reader()
    # Initialize companion DB
    global companion_db, study_analytics
    db_path = os.environ.get("COMPANION_DB_PATH", str(TOOLS_DIR / "workbench" / "companion.db"))
    companion_db = CompanionDB(db_path)
    companion_db.init_db()
    # Initialize analytics DB
    study_analytics = SessionAnalytics(db_path)
    study_analytics.init_db()
    # Seed question bank if empty
    if not companion_db.get_questions('prayer'):
        seed_question_bank(companion_db)

def shutdown():
    shutdown_batch_reader()

atexit.register(shutdown)

# ── Template Helpers ─────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    return {"phases": PHASES}

# ── Page Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    projects = db.list_projects()
    return render_template("projects_list.html", projects=projects)


@app.route("/project/<project_id>")
def project_view(project_id):
    project = db.get_project(project_id)
    if not project:
        return redirect(url_for("index"))
    conversation = db.get_conversation(project_id)
    research_items = db.get_research_items(project_id)
    notes = db.get_notes(project_id)
    return render_template(
        "project.html",
        project=project,
        conversation=conversation,
        research_items=research_items,
        notes=notes,
        phases=PHASES,
    )


@app.route("/library")
def library_view():
    return render_template("library.html")


# ── API: Projects ────────────────────────────────────────────────────────

@app.route("/api/projects", methods=["POST"])
def api_create_project():
    passage = request.form.get("passage", "").strip()
    theme = request.form.get("theme", "").strip() or None
    if not passage:
        return redirect(url_for("index"))

    try:
        parsed = parse_reference(passage)
    except Exception:
        parsed = None

    project = db.create_project(passage, theme, parsed)
    return redirect(url_for("project_view", project_id=project["id"]))


@app.route("/api/projects/<project_id>/phase", methods=["POST"])
def api_update_phase(project_id):
    phase = request.form.get("phase") or request.json.get("phase")
    if phase:
        db.update_project_phase(project_id, phase)
    return jsonify({"ok": True})


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    db.delete_project(project_id)
    return jsonify({"ok": True})


# ── API: Chat ────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    project_id = data.get("project_id")
    message = data.get("message", "").strip()
    model = data.get("model", "claude-haiku-4-5-20251001")

    if not project_id or not message:
        return jsonify({"error": "project_id and message required"}), 400

    return Response(
        stream_agent_response(project_id, message, model=model),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── API: Passage ─────────────────────────────────────────────────────────

@app.route("/api/passage")
def api_passage():
    """Get passage text in multiple translations."""
    ref_str = request.args.get("ref", "")
    versions = request.args.get("versions", "ESV,NASB95,KJV").split(",")

    if not ref_str:
        return jsonify({"error": "ref required"}), 400

    ref = parse_reference(ref_str)
    bible_files = resolve_bible_files(versions)

    results = []
    for bf in bible_files:
        chapter_text, metadata = read_bible_chapter(bf, ref["book"], ref["chapter"])
        if chapter_text:
            if ref["verse_start"]:
                text = extract_verses(chapter_text, ref["verse_start"], ref["verse_end"])
            else:
                text = chapter_text
            text = clean_bible_text(text)
            results.append({
                "version": bf.replace(".logos4", "").replace(".lbxlls", ""),
                "text": text,
            })

    return render_template("partials/passage_display.html",
                           reference=ref_str, translations=results)


@app.route("/api/interlinear")
def api_interlinear():
    """Get interlinear data for a passage."""
    ref_str = request.args.get("ref", "")
    if not ref_str:
        return jsonify({"error": "ref required"}), 400

    ref = parse_reference(ref_str)
    bible_files = resolve_bible_files(["ESV"])
    if not bible_files:
        return "<p>No Bible available for interlinear</p>"

    data = get_interlinear_for_chapter(bible_files[0], ref["book"], ref["chapter"])
    return render_template("partials/interlinear_display.html",
                           reference=ref_str, words=data)


# ── API: Notes ───────────────────────────────────────────────────────────

@app.route("/api/projects/<project_id>/notes", methods=["GET"])
def api_get_notes(project_id):
    section = request.args.get("section")
    notes = db.get_notes(project_id, section)
    return render_template("partials/notes_editor.html",
                           project_id=project_id, notes=notes)


@app.route("/api/projects/<project_id>/notes", methods=["POST"])
def api_save_notes(project_id):
    data = request.get_json() or request.form
    section = data.get("section", "general")
    content = data.get("content", "")
    db.save_note(project_id, content, section)
    return jsonify({"ok": True})


# ── API: Research Items ──────────────────────────────────────────────────

@app.route("/api/projects/<project_id>/research")
def api_get_research(project_id):
    item_type = request.args.get("type")
    items = db.get_research_items(project_id, item_type)
    return render_template("partials/research_panel.html",
                           project_id=project_id, items=items)


# ── API: Resource Browser ─────────────────────────────────────────────────

@app.route("/api/resource/<filename>/toc")
def api_resource_toc(filename):
    """Get a resource's table of contents."""
    from study import get_toc_cached
    toc_entries = get_toc_cached(filename)
    return render_template("partials/resource_detail.html",
                           filename=filename, toc=toc_entries,
                           title=request.args.get("title", filename),
                           abbrev=request.args.get("abbrev", ""),
                           rtype=request.args.get("type", ""))


@app.route("/api/resource/<filename>/article/<int:article_num>")
def api_resource_article(filename, article_num):
    """Read a specific article from a resource."""
    text = read_article_text(filename, article_num, max_chars=30000)
    if not text:
        text = "(Could not read this article)"
    return f'<div class="article-text">{_escape(text)}</div>'


def _escape(text):
    """HTML-escape text for safe rendering."""
    from markupsafe import escape
    return escape(text)


# ── API: Library ─────────────────────────────────────────────────────────

@app.route("/api/library/search")
def api_library_search():
    import sqlite3
    import os

    query = request.args.get("q", "").strip()
    rtype = request.args.get("type", "all")
    limit = int(request.args.get("limit", "50"))

    if not query and rtype == "all":
        return render_template("partials/library_results.html", results=[], query="")

    type_filter = ""
    if rtype != "all":
        type_map = {
            "bible": "text.monograph.bible",
            "commentary": "text.monograph.commentary%",
            "lexicon": "%lexicon%",
            "theology": "%systematic-theology%",
            "confession": "%confession%",
            "ancient": "%ancient%",
            "sermons": "%sermons%",
        }
        if rtype in type_map:
            type_filter = f"AND c.Type LIKE '{type_map[rtype]}'"

    conn = sqlite3.connect(CATALOG_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(f"ATTACH '{RESOURCE_MGR_DB}' AS rm")

    if query:
        rows = conn.execute(f"""
            SELECT c.ResourceId, c.AbbreviatedTitle, c.Title, c.Type,
                   rm.Resources.Location
            FROM Records c
            INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
            WHERE c.Availability = 2
            AND (c.Title LIKE ? OR c.AbbreviatedTitle LIKE ?)
            {type_filter}
            ORDER BY c.AbbreviatedTitle
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit)).fetchall()
    else:
        rows = conn.execute(f"""
            SELECT c.ResourceId, c.AbbreviatedTitle, c.Title, c.Type,
                   rm.Resources.Location
            FROM Records c
            INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
            WHERE c.Availability = 2
            {type_filter}
            ORDER BY c.AbbreviatedTitle
            LIMIT ?
        """, (limit,)).fetchall()
    conn.close()

    results = []
    for r in rows:
        loc = r["Location"] or ""
        results.append({
            "resource_id": r["ResourceId"],
            "abbrev": r["AbbreviatedTitle"] or "",
            "title": r["Title"],
            "type": r["Type"],
            "filename": os.path.basename(loc) if loc else "",
        })

    return render_template("partials/library_results.html",
                           results=results, query=query)


# ── Companion Routes ─────────────────────────────────────────────────────

@app.route("/companion/")
def companion_index():
    """Start page — enter a passage or continue an active session."""
    sessions = companion_db.list_sessions(status='active')
    error = request.args.get('error')
    return render_template("start.html", sessions=sessions, error=error)


@app.route("/companion/session/new", methods=["POST"])
def companion_new_session():
    """Create a new study session from a passage reference."""
    passage = request.form.get("passage", "").strip()
    if not passage:
        return redirect(url_for("companion_index", error="Please enter a passage"))

    try:
        ref = parse_reference(passage)
    except ValueError as e:
        return redirect(url_for("companion_index", error=str(e)))

    genre = get_genre(ref["book"])
    session_id = companion_db.create_session(
        passage_ref=passage,
        book=ref["book"],
        chapter=ref["chapter"],
        verse_start=ref["verse_start"],
        verse_end=ref["verse_end"],
        genre=genre,
    )
    return redirect(url_for("companion_session", session_id=session_id))


@app.route("/companion/session/<int:session_id>")
def companion_session(session_id):
    """Main session view."""
    session = companion_db.get_session(session_id)
    if not session:
        return redirect(url_for("companion_index"))

    phase = session['current_phase']
    phase_info = PHASE_DESCRIPTIONS.get(phase, {'name': phase.replace('_', ' ').title()})

    return render_template("session.html",
                           session=session,
                           phase_info=phase_info)


@app.route("/companion/session/<int:session_id>/card")
def companion_card(session_id):
    """Return the current card partial."""
    session = companion_db.get_session(session_id)
    if not session:
        return "<p>Session not found</p>", 404

    phase = session['current_phase']
    genre = session['genre']

    # Get questions for this phase + genre
    questions = companion_db.get_questions(phase, genre=genre)

    # Get responses already given in this phase
    responses = companion_db.get_card_responses(session_id, phase=phase)
    answered_ids = {r['question_id'] for r in responses}

    # Find next unanswered question
    current_question = None
    for q in questions:
        if q['id'] not in answered_ids:
            current_question = q
            break

    if current_question:
        # Load resource if applicable
        resource_text = None
        resource_label = None
        res_type = current_question.get('resource_type', 'none')

        if res_type == 'original_lang':
            # Original language text: THGNT for NT (books 61-87), BHS for OT (books 1-39)
            try:
                if session['book'] >= 61:
                    orig_versions = ["THGNT"]
                else:
                    orig_versions = ["BHS OT"]
                bible_files = resolve_bible_files(orig_versions)
                if bible_files:
                    chapter_text, _ = read_bible_chapter(
                        bible_files[0], session['book'], session['chapter'])
                    if chapter_text and session['verse_start']:
                        resource_text = extract_verses(chapter_text, session['verse_start'], session['verse_end'])
                    elif chapter_text:
                        resource_text = chapter_text
                    # Don't run clean_bible_text on original language — markers are different
                    if resource_text:
                        resource_text = resource_text.replace('\ufeff', '').replace('\xa0', ' ')
                    resource_label = orig_versions[0]
            except Exception:
                pass

        elif res_type == 'bible':
            try:
                bible_files = resolve_bible_files(["ESV"])
                if bible_files:
                    chapter_text, _ = read_bible_chapter(
                        bible_files[0], session['book'], session['chapter'])
                    if chapter_text and session['verse_start']:
                        resource_text = clean_bible_text(
                            extract_verses(chapter_text, session['verse_start'], session['verse_end']))
                    elif chapter_text:
                        resource_text = clean_bible_text(chapter_text)
                    resource_label = "ESV"
            except Exception:
                pass

        return render_template("partials/card.html",
                               session_id=session_id,
                               question=current_question,
                               resource_text=resource_text,
                               resource_label=resource_label,
                               total_questions=len(questions),
                               answered_count=len(answered_ids),
                               can_go_back=len(answered_ids) > 0,
                               phase_complete=False,
                               phase_name=None)
    else:
        # All questions answered — show phase completion
        phase_name = PHASE_DESCRIPTIONS.get(phase, {}).get('name', phase)
        return render_template("partials/card.html",
                               session_id=session_id,
                               question=None,
                               resource_text=None,
                               resource_label=None,
                               total_questions=len(questions),
                               answered_count=len(answered_ids),
                               can_go_back=False,
                               phase_complete=True,
                               phase_name=phase_name)


@app.route("/companion/session/<int:session_id>/card/respond", methods=["POST"])
def companion_card_respond(session_id):
    """Save a card response and return the next card."""
    session = companion_db.get_session(session_id)
    if not session:
        return "<p>Session not found</p>", 404

    question_id = request.form.get("question_id", type=int)
    response_text = request.form.get("response", "").strip()

    if question_id:
        # Check if this question was already answered (editing via Back)
        existing = [r for r in companion_db.get_card_responses(session_id, phase=session['current_phase'])
                    if r['question_id'] == question_id]
        if existing:
            # Update existing response
            conn = companion_db._conn()
            conn.execute("UPDATE card_responses SET content = ? WHERE id = ?",
                         (response_text or "(skipped)", existing[-1]['id']))
            conn.commit()
            conn.close()
        elif response_text:
            companion_db.save_card_response(session_id, session['current_phase'], question_id, response_text)
        else:
            companion_db.save_card_response(session_id, session['current_phase'], question_id, "(skipped)")

    # Return next card
    return companion_card(session_id)


@app.route("/companion/session/<int:session_id>/card/back", methods=["POST"])
def companion_card_back(session_id):
    """Go back to previous question, showing the saved response for editing."""
    session = companion_db.get_session(session_id)
    if not session:
        return "<p>Session not found</p>", 404

    phase = session['current_phase']
    genre = session['genre']
    questions = companion_db.get_questions(phase, genre=genre)
    responses = companion_db.get_card_responses(session_id, phase=phase)

    if not responses:
        return companion_card(session_id)

    # Show the last answered question with its response pre-filled
    last_response = responses[-1]
    prev_question = companion_db.get_question(last_response['question_id'])
    if not prev_question:
        return companion_card(session_id)

    # Load resource if applicable
    resource_text = None
    resource_label = None
    if prev_question.get('resource_type') == 'bible':
        try:
            bible_files = resolve_bible_files(["ESV"])
            if bible_files:
                chapter_text, _ = read_bible_chapter(
                    bible_files[0], session['book'], session['chapter'])
                if chapter_text and session['verse_start']:
                    resource_text = clean_bible_text(
                        extract_verses(chapter_text, session['verse_start'], session['verse_end']))
                elif chapter_text:
                    resource_text = clean_bible_text(chapter_text)
                resource_label = "ESV"
        except Exception:
            pass

    answered_ids = {r['question_id'] for r in responses}
    return render_template("partials/card.html",
                           session_id=session_id,
                           question=prev_question,
                           resource_text=resource_text,
                           resource_label=resource_label,
                           total_questions=len(questions),
                           answered_count=len(answered_ids) - 1,
                           can_go_back=len(answered_ids) > 1,
                           phase_complete=False,
                           phase_name=None,
                           prefilled_response=last_response['content'])


@app.route("/companion/session/<int:session_id>/phase/next", methods=["POST"])
def companion_phase_next(session_id):
    """Advance to the next phase."""
    session = companion_db.get_session(session_id)
    if not session:
        return "<p>Session not found</p>", 404

    current_phase = session['current_phase']
    try:
        idx = PHASES_ORDER.index(current_phase)
        if idx + 1 < len(PHASES_ORDER):
            next_phase = PHASES_ORDER[idx + 1]
            companion_db.update_phase(session_id, next_phase)
        else:
            companion_db.complete_session(session_id)
            return '<div class="phase-complete"><h3>Study Complete!</h3><p><a href="/companion/">Return home</a> | <a href="/companion/session/' + str(session_id) + '/export" target="_blank">Export Outline</a></p></div>'
    except ValueError:
        pass

    # Return new card + trigger progress dots refresh
    response_html = companion_card(session_id)
    return response_html


@app.route("/companion/session/<int:session_id>/discuss", methods=["POST"])
def companion_discuss(session_id):
    """Stream a discussion response via SSE."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "message required"}), 400

    return Response(
        stream_companion_response(session_id, message, companion_db),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/companion/session/<int:session_id>/outline")
def companion_outline(session_id):
    """Return outline drawer partial."""
    tree = companion_db.get_outline_tree(session_id)
    return render_template("partials/outline_drawer.html",
                           session_id=session_id, tree=tree)


@app.route("/companion/session/<int:session_id>/outline/add", methods=["POST"])
def companion_outline_add(session_id):
    """Add a node to the outline."""
    content = request.form.get("content", "").strip()
    node_type = request.form.get("node_type", "note")
    parent_id = request.form.get("parent_id", type=int)
    verse_ref = request.form.get("verse_ref", "").strip() or None

    if content:
        companion_db.add_outline_node(
            session_id=session_id,
            node_type=node_type,
            content=content,
            parent_id=parent_id,
            verse_ref=verse_ref,
        )

    return companion_outline(session_id)


@app.route("/companion/session/<int:session_id>/outline/<int:node_id>", methods=["PATCH"])
def companion_outline_update(session_id, node_id):
    """Update an outline node."""
    data = request.get_json() or {}
    companion_db.update_outline_node(
        node_id=node_id,
        content=data.get("content"),
        node_type=data.get("node_type"),
        rank=data.get("rank"),
    )
    return companion_outline(session_id)


@app.route("/companion/session/<int:session_id>/outline/<int:node_id>", methods=["DELETE"])
def companion_outline_delete(session_id, node_id):
    """Delete an outline node and its children."""
    companion_db.delete_outline_node(node_id)
    return companion_outline(session_id)


@app.route("/companion/session/<int:session_id>/export")
def companion_export(session_id):
    """Render printable outline."""
    session = companion_db.get_session(session_id)
    if not session:
        return redirect(url_for("companion_index"))
    tree = companion_db.get_outline_tree(session_id)
    return render_template("export.html", session=session, tree=tree)


@app.route("/companion/session/<int:session_id>/timer", methods=["PATCH"])
def companion_timer_update(session_id):
    """Update timer state from client."""
    data = request.get_json() or {}
    remaining = data.get("remaining")
    paused = data.get("paused")
    elapsed_delta = data.get("elapsed_delta", 0)

    if remaining is not None:
        companion_db.update_timer(session_id, remaining, paused=paused, elapsed_delta=elapsed_delta)

    return jsonify({"ok": True})


@app.route("/companion/session/<int:session_id>/progress")
def companion_progress(session_id):
    """Return progress dots partial."""
    session = companion_db.get_session(session_id)
    if not session:
        return ""

    current_phase = session['current_phase']
    try:
        current_idx = PHASES_ORDER.index(current_phase)
    except ValueError:
        current_idx = 0

    completed_phases = set(PHASES_ORDER[:current_idx])

    return render_template("partials/progress_dots.html",
                           phases_order=PHASES_ORDER,
                           current_phase=current_phase,
                           completed_phases=completed_phases)


# ── Card Phases (Study phases 1-5 use cards, 6+ use conversation) ──────

CARD_PHASES = [
    {"key": "prayer", "label": "Prayer", "prompt": "Pray for your study of this passage.",
     "guidance": "Ask the Spirit to open your eyes to see wonderful things in His word. Pray for your congregation.",
     "has_textarea": True, "auto_resource": None, "layout": "single"},
    {"key": "read_translate", "label": "Read & Translate", "prompt": "Read the original text and write your working translation.",
     "guidance": "Work from the Greek/Hebrew. Don't reach for a published translation — wrestle with the words yourself.",
     "has_textarea": True, "auto_resource": "original_language", "layout": "side_by_side"},
    {"key": "digestion", "label": "Digestion", "prompt": "Pray through the text phrase by phrase.",
     "guidance": "Take each phrase and turn it into prayer. What is God saying? What stirs in you?",
     "has_textarea": True, "auto_resource": None, "layout": "single"},
    {"key": "study_bibles", "label": "Study Bible Consultation", "prompt": "Review notes from your study bibles.",
     "guidance": "Star passages that catch your eye. Use the notepad to capture your thinking. These feed into the conversation.",
     "has_textarea": False, "auto_resource": "study_bibles", "layout": "single"},
]


def _get_original_language_text(session):
    """Get THGNT (NT) or BHS (OT) text for the session's passage."""
    try:
        ref = parse_reference(session["passage_ref"])
        if not ref:
            return None
        version = "THGNTCROSSWAY" if ref["book"] >= 40 else "BHS"
        files = resolve_bible_files([version])
        if not files:
            return None
        text, _ = read_bible_chapter(files[0], ref["book"], ref["chapter"])
        if text and ref.get("verse_start"):
            text = extract_verses(text, ref["verse_start"], ref.get("verse_end"))
        return text
    except Exception:
        return None


def _get_study_bible_notes(session):
    """Get study bible notes for the session's passage."""
    try:
        ref = parse_reference(session["passage_ref"])
        if not ref:
            return []
        return find_study_bible_notes(ref, max_chars=5000)
    except Exception:
        return []


def _save_card_summary_for_ai(session_id):
    """Save a system message summarizing Bryan's card work for the AI."""
    responses = companion_db.get_card_responses(session_id)
    annotations = companion_db.get_card_annotations(session_id)
    notepad_text = companion_db.get_card_notepad(session_id, "study_bibles")
    parts = []
    for resp in responses:
        if resp.get("content"):
            parts.append(f"[{resp['phase']}] {resp['content']}")
    if annotations:
        parts.append("\n[Study Bible Stars]")
        for a in annotations:
            line = f"  \u2605 {a['source']}: \"{a['starred_text']}\""
            if a.get("note"):
                line += f" \u2192 {a['note']}"
            parts.append(line)
    if notepad_text:
        parts.append(f"\n[Study Bible Notepad]\n{notepad_text}")
    if parts:
        summary = "Bryan's card-phase work:\n" + "\n".join(parts)
        companion_db.save_message(session_id, "context", "system", summary)


# ── Study Routes (Conversation-First UI) ────────────────────────────────

@app.route("/study/")
def study_index():
    """Start page — enter a passage or continue a session."""
    sessions = companion_db.list_sessions(status='active')
    error = request.args.get('error')
    return render_template("study_start.html", sessions=sessions, error=error)


@app.route("/study/session/<int:session_id>/delete", methods=["POST"])
def study_delete_session(session_id):
    """Delete a study session and all its data."""
    companion_db.delete_session(session_id)
    return redirect(url_for("study_index"))


@app.route("/study/session/new", methods=["POST"])
def study_new_session():
    """Create a new study session."""
    passage = request.form.get("passage", "").strip()
    if not passage:
        return redirect(url_for("study_index", error="Please enter a passage"))

    try:
        ref = parse_reference(passage)
    except ValueError as e:
        return redirect(url_for("study_index", error=str(e)))

    genre = get_genre(ref["book"])
    session_id = companion_db.create_session(
        passage_ref=passage,
        book=ref["book"],
        chapter=ref["chapter"],
        verse_start=ref["verse_start"],
        verse_end=ref["verse_end"],
        genre=genre,
    )
    # Record initial phase entry
    if study_analytics:
        study_analytics.record_phase_enter(session_id, 'prayer')
    return redirect(url_for("study_session_view", session_id=session_id))


@app.route("/study/session/<int:session_id>")
def study_session_view(session_id):
    """Main session view — card UI for phases 1-5, conversation for 6+."""
    session = companion_db.get_session(session_id)
    if not session:
        return redirect(url_for("study_index"))

    # Sermon-coach integration: is there a linked sermon for this session?
    linked_sermon = None
    review = None
    candidates = []
    conn = companion_db._conn()
    try:
        link_row = conn.execute("""
            SELECT s.*
            FROM sermons s
            JOIN sermon_links sl ON sl.sermon_id = s.id
            WHERE sl.session_id = ? AND sl.link_status = 'active'
            LIMIT 1
        """, (session_id,)).fetchone()
        if link_row:
            linked_sermon = dict(link_row)
            from sermon_coach_tools import get_sermon_review as _get_review_parsed
            review = _get_review_parsed(companion_db, linked_sermon['id'])
        candidate_rows = conn.execute("""
            SELECT sl.id, sl.sermon_id, sl.match_reason, s.title, s.bible_text_raw
            FROM sermon_links sl
            JOIN sermons s ON s.id = sl.sermon_id
            WHERE sl.link_status = 'candidate'
              AND s.id IN (
                  SELECT sl2.sermon_id FROM sermon_links sl2 WHERE sl2.session_id = ?
              )
        """, (session_id,)).fetchall()
        candidates = [dict(c) for c in candidate_rows]
    finally:
        conn.close()

    phase = session.get("current_phase", "prayer")
    card_phase_keys = [p["key"] for p in CARD_PHASES]

    if phase in card_phase_keys:
        # Card mode (phases 1-5)
        phase_index = card_phase_keys.index(phase)
        card_def = CARD_PHASES[phase_index]
        resource_text = None
        study_bible_notes = None
        if card_def["auto_resource"] == "original_language":
            resource_text = _get_original_language_text(session)
        elif card_def["auto_resource"] == "study_bibles":
            study_bible_notes = _get_study_bible_notes(session)
        responses = companion_db.get_card_responses(session_id, phase)
        # Check auto-saved draft first, then last submitted response
        prefilled = companion_db.get_card_notepad(session_id, f"card_{phase}")
        if not prefilled:
            prefilled = responses[-1]["content"] if responses else ""
        annotations = companion_db.get_card_annotations(session_id, phase) if phase == "study_bibles" else []
        notepad = companion_db.get_card_notepad(session_id, phase) if phase == "study_bibles" else ""
        return render_template("study_session.html",
                               session=session, mode="card",
                               card=card_def, phase_index=phase_index,
                               total_phases=len(CARD_PHASES),
                               resource_text=resource_text,
                               study_bible_notes=study_bible_notes,
                               prefilled=prefilled,
                               annotations=annotations,
                               notepad=notepad,
                               messages=[],
                               outline=companion_db.get_outline_tree(session_id),
                               linked_sermon=linked_sermon,
                               review=review,
                               candidates=candidates)
    else:
        # Conversation mode (phase 6+)
        messages = companion_db.get_messages(session_id, limit=200)
        return render_template("study_session.html",
                               session=session, mode="conversation",
                               card=None, phase_index=5,
                               total_phases=len(CARD_PHASES),
                               resource_text=None,
                               study_bible_notes=None,
                               prefilled="",
                               annotations=[],
                               notepad="",
                               messages=messages,
                               outline=companion_db.get_outline_tree(session_id),
                               linked_sermon=linked_sermon,
                               review=review,
                               candidates=candidates)


@app.route("/study/session/<int:session_id>/discuss", methods=["POST"])
def study_discuss(session_id):
    """Stream a study response via SSE."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "message required"}), 400

    # Record message analytics
    if study_analytics:
        study_analytics.record_message(session_id, 'user', len(message))

    return Response(
        stream_study_response(session_id, message, companion_db, study_analytics),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/study/session/<int:session_id>/card/next", methods=["POST"])
def study_card_next(session_id):
    """Advance to the next card phase, saving any response."""
    session = companion_db.get_session(session_id)
    if not session:
        return "Session not found", 404
    phase = session.get("current_phase", "prayer")
    response_text = request.form.get("response", "").strip()
    if response_text:
        companion_db.save_card_response(session_id, phase, question_id=0, content=response_text)
    card_phase_keys = [p["key"] for p in CARD_PHASES]
    if phase in card_phase_keys:
        idx = card_phase_keys.index(phase)
        if idx < len(card_phase_keys) - 1:
            next_phase = card_phase_keys[idx + 1]
            companion_db.update_phase(session_id, next_phase)
        else:
            companion_db.update_phase(session_id, "context")
            _save_card_summary_for_ai(session_id)
    return redirect(url_for("study_session_view", session_id=session_id))


@app.route("/study/session/<int:session_id>/card/back", methods=["POST"])
def study_card_back(session_id):
    """Go back to the previous card phase."""
    session = companion_db.get_session(session_id)
    if not session:
        return "Session not found", 404
    phase = session.get("current_phase", "prayer")
    card_phase_keys = [p["key"] for p in CARD_PHASES]
    if phase in card_phase_keys:
        idx = card_phase_keys.index(phase)
        if idx > 0:
            companion_db.update_phase(session_id, card_phase_keys[idx - 1])
    return redirect(url_for("study_session_view", session_id=session_id))


@app.route("/study/session/<int:session_id>/study-bibles")
def study_bible_notes_route(session_id):
    """Return study bible notes for the session's passage as JSON."""
    session = companion_db.get_session(session_id)
    if not session:
        return jsonify({"error": "not found"}), 404
    notes = _get_study_bible_notes(session)
    return jsonify(notes)


@app.route("/study/session/<int:session_id>/card/autosave", methods=["POST"])
def study_card_autosave(session_id):
    """Auto-save card textarea content without advancing phase."""
    data = request.get_json() or {}
    content = data.get("content", "")
    session = companion_db.get_session(session_id)
    if not session:
        return jsonify({"error": "not found"}), 404
    phase = session.get("current_phase", "prayer")
    # Use notepad table for auto-save (upsert by session+phase)
    companion_db.save_card_notepad(session_id, phase=f"card_{phase}", content=content)
    return jsonify({"ok": True})


_TRANSCRIBE_MAX_BYTES = 25 * 1024 * 1024


@app.route("/study/session/<int:session_id>/transcribe", methods=["POST"])
def study_transcribe(session_id):
    """Run voice-to-text on an uploaded audio blob and return the transcript."""
    session = companion_db.get_session(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    audio_file = request.files.get("audio")
    if audio_file is None:
        return jsonify({"error": "missing 'audio' field"}), 400

    audio_bytes = audio_file.read()
    if not audio_bytes:
        return jsonify({"error": "empty audio"}), 400
    if len(audio_bytes) > _TRANSCRIBE_MAX_BYTES:
        return jsonify({"error": "audio exceeds 25 MB limit"}), 413

    content_type = audio_file.mimetype or "audio/webm"

    try:
        import whisper_service
        result = whisper_service.transcribe_audio(audio_bytes, content_type=content_type)
    except Exception as e:
        app.logger.exception("transcription failed")
        return jsonify({"error": f"transcription failed: {e}"}), 500

    return jsonify(result)


def _lookup_lexicon_gloss(lemma, is_nt=True):
    """Look up a short English gloss from BDAG (NT) or BDB/HALOT (OT).

    Tries the lemma as-is, then with middle→active form for Greek deponents.
    Caches the result in the MorphGNT glosses table for future lookups.
    Returns the gloss string or None.
    """
    from resource_index import ResourceIndex
    from morphgnt_cache import _extract_gloss_from_bdag, _normalize_greek

    idx_path = os.path.join(os.path.dirname(__file__), '..', 'resource_index.db')
    idx = ResourceIndex(idx_path)
    lemma_nfc = _normalize_greek(lemma)

    if is_nt:
        resources = [("BDAG.logos4", _extract_gloss_from_bdag)]
    else:
        resources = [
            ("BDB.logos4", _extract_gloss_from_bdag),
            ("HAL.logos4", _extract_gloss_from_bdag),
        ]

    for res_file, extractor in resources:
        # Try exact lemma
        results = idx.lookup(lemma_nfc, res_file, limit=1)

        # For Greek: try active form if middle/passive lemma didn't match
        if not results and lemma_nfc.endswith("ομαι"):
            results = idx.lookup(lemma_nfc[:-4] + "ω", res_file, limit=1)
        if not results and lemma_nfc.endswith("μαι"):
            results = idx.lookup(lemma_nfc[:-3] + "μι", res_file, limit=1)

        if not results or results[0].get("score", 0) < 80:
            continue

        text = read_article_text(res_file, results[0]["article_num"], max_chars=800)
        gloss = extractor(text)
        if gloss:
            # Cache for next time
            try:
                from morphgnt_cache import get_cache, _normalize_greek as _nfcg
                import sqlite3
                cache = get_cache()
                conn = cache._get_conn()
                if conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO glosses VALUES (?,?,?)",
                        (_nfcg(lemma), gloss, "bdag-live"),
                    )
                    conn.commit()
            except Exception:
                pass
            return gloss

    return None


@app.route("/study/session/<int:session_id>/word-info", methods=["POST"])
def study_word_info(session_id):
    """Get parsing info for a Greek/Hebrew word.

    Uses MorphGNT cache for NT words (authoritative parsing).
    Looks up BDAG/BDB/HALOT from the library for glosses.
    Falls back to Claude Haiku only as last resort.
    """
    data = request.get_json() or {}
    word = data.get("word", "").strip()
    if not word:
        return jsonify({"error": "word required"}), 400

    session = companion_db.get_session(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    book = session.get("book", 66)
    is_nt = book >= 40

    morphgnt_result = None

    # Try MorphGNT cache first for NT words (authoritative parsing)
    if is_nt:
        from morphgnt_cache import get_cache
        cache = get_cache()
        morphgnt_result = cache.lookup_word(
            word,
            book=book,
            chapter=session.get("chapter"),
            verse=session.get("verse_start"),
        )
        if not morphgnt_result:
            morphgnt_result = cache.lookup_word(word, book=book)
        if not morphgnt_result:
            morphgnt_result = cache.lookup_word(word)

    if morphgnt_result:
        gloss = morphgnt_result.get("gloss", "")
        lemma = morphgnt_result["lemma"]

        # If no cached gloss, look it up live from BDAG
        if not gloss:
            gloss = _lookup_lexicon_gloss(lemma, is_nt=True) or ""

        return jsonify({
            "lemma": lemma,
            "gloss": gloss,
            "parsing": morphgnt_result["parsing_human"],
            "root": lemma,
            "source": "morphgnt",
        })

    # Fall back to Haiku for OT words or MorphGNT misses
    lang = "Greek" if is_nt else "Hebrew"
    try:
        import anthropic
        api_key = anthropic_api_key()
        if not api_key:
            return jsonify({"error": "API key not set"}), 500
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": f"Parse this {lang} word from the Bible: {word}\n\nReturn ONLY a JSON object with these fields:\n- \"lemma\": the dictionary form\n- \"gloss\": brief English meaning (2-4 words)\n- \"parsing\": full morphological parsing (e.g. \"Verb, Aorist Active Indicative, 3rd Person Singular\")\n- \"root\": the root/stem if different from lemma, otherwise same as lemma\n\nJSON only, no explanation."}],
        )
        import re
        text = resp.content[0].text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            info = json.loads(match.group())
            info["source"] = "haiku"
            return jsonify(info)
        return jsonify({"error": "parse failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/study/session/<int:session_id>/annotate", methods=["POST"])
def study_annotate(session_id):
    """Save a star annotation from the study bible card."""
    data = request.get_json()
    aid = companion_db.save_card_annotation(
        session_id, phase="study_bibles",
        source=data.get("source", ""),
        starred_text=data.get("starred_text", ""),
        note=data.get("note", ""))
    return jsonify({"id": aid})


@app.route("/study/session/<int:session_id>/notepad", methods=["POST"])
def study_notepad(session_id):
    """Save notepad content for the current phase."""
    data = request.get_json()
    companion_db.save_card_notepad(session_id, phase=data.get("phase", "study_bibles"),
                                   content=data.get("content", ""))
    return jsonify({"ok": True})


@app.route("/study/session/<int:session_id>/outline")
def study_outline(session_id):
    """Return outline tree as JSON."""
    tree = companion_db.get_outline_tree(session_id)
    return jsonify(tree)


@app.route("/study/session/<int:session_id>/outline/add", methods=["POST"])
def study_outline_add(session_id):
    """Add a node to the outline."""
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    node_type = data.get("node_type", "note")

    if content:
        node_id = companion_db.add_outline_node(
            session_id=session_id,
            node_type=node_type,
            content=content,
        )
        if study_analytics:
            study_analytics.record_outline_event(session_id, 'add', node_type)
        return jsonify({"ok": True, "id": node_id})

    return jsonify({"ok": False}), 400


@app.route("/study/session/<int:session_id>/outline/<int:node_id>", methods=["PATCH"])
def study_outline_update(session_id, node_id):
    """Update an outline node."""
    data = request.get_json() or {}
    companion_db.update_outline_node(
        node_id=node_id,
        content=data.get("content"),
        node_type=data.get("node_type"),
        rank=data.get("rank"),
    )
    return jsonify({"ok": True})


@app.route("/study/session/<int:session_id>/outline/<int:node_id>", methods=["DELETE"])
def study_outline_delete(session_id, node_id):
    """Delete an outline node."""
    companion_db.delete_outline_node(node_id)
    return jsonify({"ok": True})


@app.route("/study/session/<int:session_id>/clock", methods=["PATCH"])
def study_clock_update(session_id):
    """Update elapsed time from client (absolute, not delta)."""
    data = request.get_json() or {}
    elapsed = data.get("elapsed", 0)
    if elapsed:
        # Client sends total elapsed — set it directly, don't add as delta
        conn = companion_db._conn()
        conn.execute(
            "UPDATE sessions SET total_elapsed_seconds = ?, updated_at = ? WHERE id = ?",
            (elapsed, companion_db._now(), session_id))
        conn.commit()
        conn.close()
    return jsonify({"ok": True})


# ── Sermons Blueprint ────────────────────────────────────────────────────

sermons_bp = Blueprint('sermons', __name__, url_prefix='/sermons')


@sermons_bp.route('/', methods=['GET'])
def sermons_list():
    db = get_db()
    conn = db._conn()
    rows = conn.execute("""
        SELECT id, title, preach_date, duration_seconds, sync_status, match_status,
               ui_last_seen_version, source_version
        FROM sermons
        WHERE classified_as = 'sermon' AND is_remote_deleted = 0
        ORDER BY preach_date DESC
        LIMIT 100
    """).fetchall()
    sermons = [dict(
        id=r[0], title=r[1], preach_date=r[2], duration_seconds=r[3],
        sync_status=r[4], match_status=r[5],
        badge=(r[6] < r[7]),
    ) for r in rows]
    conn.close()
    return render_template('sermons/list.html', sermons=sermons)


@sermons_bp.route('/<int:sermon_id>', methods=['GET'])
def sermon_detail(sermon_id):
    db = get_db()
    conn = db._conn()
    sermon_row = conn.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,)).fetchone()
    if not sermon_row:
        conn.close()
        abort(404)
    sermon = dict(sermon_row)

    from sermon_coach_tools import get_sermon_review as _get_review_parsed
    review = _get_review_parsed(db, sermon_id)

    flags_rows = conn.execute("""
        SELECT id, flag_type, severity, transcript_start_sec, transcript_end_sec,
               section_label, excerpt, rationale
        FROM sermon_flags WHERE sermon_id = ?
        ORDER BY transcript_start_sec
    """, (sermon_id,)).fetchall()
    flags = [dict(r) for r in flags_rows]

    candidates_rows = conn.execute("""
        SELECT sl.id, sl.sermon_id, sl.session_id, sl.match_reason, s.passage_ref
        FROM sermon_links sl
        JOIN sessions s ON s.id = sl.session_id
        WHERE sl.sermon_id = ? AND sl.link_status = 'candidate'
    """, (sermon_id,)).fetchall()
    candidates = [dict(r) for r in candidates_rows]

    # Compare-and-set: only bump ui_last_seen_version if it's behind source_version
    conn.execute("""
        UPDATE sermons SET ui_last_seen_version = source_version
        WHERE id = ? AND ui_last_seen_version < source_version
    """, (sermon_id,))
    conn.commit()
    conn.close()

    return render_template(
        'sermons/detail.html',
        sermon=sermon, review=review, flags=flags, candidates=candidates,
    )


@sermons_bp.route('/<int:sermon_id>/status', methods=['GET'])
def sermon_status(sermon_id):
    db = get_db()
    conn = db._conn()
    row = conn.execute("""
        SELECT sync_status, match_status, source_version, ui_last_seen_version
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    return jsonify(dict(
        sync_status=row[0], match_status=row[1],
        source_version=row[2], ui_last_seen_version=row[3],
    ))


def _make_sermonaudio_client():
    """Factory for the real API client. Tests monkeypatch this."""
    from sermonaudio_sync import SermonAudioAPIClient
    return SermonAudioAPIClient(sermonaudio_api_key())


def _broadcaster_id() -> str:
    return sermonaudio_broadcaster_id()


@sermons_bp.route('/sync', methods=['POST'])
def sermon_sync():
    from sermonaudio_sync import run_sync
    from sermon_matcher import dispatch_matching
    from sermon_analyzer import dispatch_pending_analyses
    from llm_client import AnthropicClient
    db = get_db()
    result = run_sync(db, client=_make_sermonaudio_client(),
                      broadcaster_id=_broadcaster_id(), trigger='manual')
    if result is None:
        return jsonify({'error': 'sync already running'}), 409
    result['sermons_matched'] = dispatch_matching(db)
    client = AnthropicClient(api_key=anthropic_api_key())
    analyzed = dispatch_pending_analyses(db, llm_client=client)
    result['sermons_analyzed'] = analyzed
    return jsonify(result), 202


@sermons_bp.route('/backfill', methods=['POST'])
def sermon_backfill():
    from sermonaudio_sync import run_sync
    from sermon_matcher import dispatch_matching
    from sermon_analyzer import dispatch_pending_analyses
    from llm_client import AnthropicClient
    limit = int(request.args.get('limit', 24))
    db = get_db()
    result = run_sync(db, client=_make_sermonaudio_client(),
                      broadcaster_id=_broadcaster_id(), trigger='backfill', limit=limit)
    if result is None:
        return jsonify({'error': 'sync already running'}), 409
    result['sermons_matched'] = dispatch_matching(db)
    client = AnthropicClient(api_key=anthropic_api_key())
    analyzed = dispatch_pending_analyses(db, llm_client=client)
    result['sermons_analyzed'] = analyzed
    return jsonify(result), 202


@sermons_bp.route('/backfill-srt', methods=['POST'])
def sermon_backfill_srt():
    """Re-fetch SRT for all sermons and populate transcript_segments."""
    import json as _json
    from srt_parser import parse_srt_segments, validate_segments, build_canonical_transcript
    from sermonaudio_sync import _fetch_srt_raw
    db = get_db()
    conn = db._conn()
    rows = conn.execute("""
        SELECT id, sermonaudio_id, duration_seconds FROM sermons
        WHERE classified_as = 'sermon' AND transcript_segments IS NULL
    """).fetchall()

    results = {'total': len(rows), 'updated': 0, 'failed': 0, 'no_srt': 0}
    for row in rows:
        sermon_id, sa_id, duration = row[0], row[1], row[2] or 0
        try:
            from sermonaudio.node.requests import Node
            detail = Node.get_sermon(sa_id)
            caption = detail.media.caption[0] if detail.media and detail.media.caption else None
            if not caption or not caption.download_url:
                results['no_srt'] += 1
                continue
            srt_raw = _fetch_srt_raw(caption.download_url)
            if not srt_raw:
                results['no_srt'] += 1
                continue
            segments = parse_srt_segments(srt_raw)
            if not segments:
                results['failed'] += 1
                continue
            quality = validate_segments(segments, duration)
            canonical = build_canonical_transcript(segments)
            conn.execute("""
                UPDATE sermons SET transcript_segments = ?, transcript_quality = ?,
                    transcript_text = ? WHERE id = ?
            """, (_json.dumps(segments), quality, canonical, sermon_id))
            conn.commit()
            results['updated'] += 1
        except Exception as e:
            results['failed'] += 1
    conn.close()
    return jsonify(results)


@sermons_bp.route('/<int:sermon_id>/reanalyze', methods=['POST'])
def sermon_reanalyze(sermon_id):
    from sermon_analyzer import analyze_sermon
    from llm_client import AnthropicClient
    db = get_db()
    api_key = anthropic_api_key()
    client = AnthropicClient(api_key=api_key)
    conn = db._conn()
    updated = conn.execute(
        "UPDATE sermons SET sync_status = 'analysis_pending', last_state_change_at = datetime('now') "
        "WHERE id = ? AND sync_status NOT IN ('analysis_pending', 'analysis_running')",
        (sermon_id,),
    ).rowcount
    conn.commit()
    conn.close()
    if not updated:
        return jsonify({'error': 'analysis already pending or running'}), 409
    result = analyze_sermon(db, sermon_id, llm_client=client)
    return jsonify(result)


@sermons_bp.route('/<int:sermon_id>/link/<int:session_id>', methods=['POST'])
def sermon_link(sermon_id, session_id):
    db = get_db()
    conn = db._conn()
    conn.execute(
        "UPDATE sermon_links SET link_status = 'rejected' WHERE sermon_id = ? AND link_status = 'active'",
        (sermon_id,),
    )
    conn.execute("""
        INSERT INTO sermon_links
            (sermon_id, session_id, link_status, link_source, match_reason, created_at)
        VALUES (?, ?, 'active', 'manual', 'user_linked', datetime('now'))
    """, (sermon_id, session_id))
    conn.execute(
        "UPDATE sermons SET match_status = 'matched', last_match_attempt_at = datetime('now') WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'link_status': 'active', 'link_source': 'manual'})


@sermons_bp.route('/<int:sermon_id>/unlink', methods=['POST'])
def sermon_unlink(sermon_id):
    db = get_db()
    conn = db._conn()
    conn.execute("""
        UPDATE sermon_links SET link_status = 'rejected'
        WHERE sermon_id = ? AND link_status = 'active'
    """, (sermon_id,))
    conn.execute(
        "UPDATE sermons SET match_status = 'rejected_all' WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@sermons_bp.route('/<int:sermon_id>/approve-candidate/<int:link_id>', methods=['POST'])
def sermon_approve_candidate(sermon_id, link_id):
    db = get_db()
    conn = db._conn()
    conn.execute(
        "DELETE FROM sermon_links WHERE sermon_id = ? AND link_status = 'active'",
        (sermon_id,),
    )
    conn.execute("""
        UPDATE sermon_links SET link_status = 'active'
        WHERE id = ? AND sermon_id = ?
    """, (link_id, sermon_id))
    conn.execute(
        "UPDATE sermons SET match_status = 'matched' WHERE id = ?",
        (sermon_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@sermons_bp.route('/patterns', methods=['GET'])
def sermon_patterns():
    from sermon_coach_tools import get_sermon_patterns
    from meta_coach_tools import get_active_commitment
    db = get_db()
    data = get_sermon_patterns(db)
    commitment = get_active_commitment(db)
    return render_template('sermons/patterns.html', patterns=data, commitment=commitment)


@sermons_bp.route('/sync-log', methods=['GET'])
def sermon_sync_log_page():
    db = get_db()
    conn = db._conn()
    runs = conn.execute("""
        SELECT run_id, trigger, started_at, ended_at, sermons_new, sermons_updated,
               sermons_failed, status, error_summary
        FROM sermon_sync_log
        ORDER BY started_at DESC LIMIT 20
    """).fetchall()
    cost_total = conn.execute(
        "SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM sermon_analysis_cost_log WHERE called_at >= date('now','-30 days')"
    ).fetchone()[0]
    conn.close()
    return render_template('sermons/sync_log.html',
                             runs=[dict(r) for r in runs], cost_30d=cost_total)


@sermons_bp.route('/patterns/coach/message', methods=['POST'])
def meta_coach_message():
    import json as _json
    from meta_coach_agent import stream_meta_coach_response
    from llm_client import AnthropicClient
    user_message = request.json.get('message') if request.is_json else request.form.get('message', '')
    try:
        conversation_id = int(request.json.get('conversation_id', 0)) if request.is_json else 0
    except (ValueError, TypeError):
        conversation_id = 0
    db = get_db()
    api_key = anthropic_api_key()
    client = AnthropicClient(api_key=api_key)

    def generate():
        for event in stream_meta_coach_response(
            db=db, conversation_id=conversation_id,
            user_message=user_message, llm_client=client,
        ):
            yield f"data: {_json.dumps(event)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@sermons_bp.route('/patterns/coach/commitment', methods=['GET'])
def get_commitment():
    from meta_coach_tools import get_active_commitment
    db = get_db()
    commitment = get_active_commitment(db)
    return jsonify(commitment or {})


@sermons_bp.route('/patterns/coach/commitment', methods=['POST'])
def create_commitment():
    data = request.json or {}
    dimension_key = data.get('dimension_key', '')
    experiment = data.get('practice_experiment', '')
    if not dimension_key or not experiment:
        return jsonify({'error': 'dimension_key and practice_experiment required'}), 400
    try:
        target = int(data.get('target_sermons', 2))
    except (ValueError, TypeError):
        return jsonify({'error': 'target_sermons must be an integer'}), 400
    db = get_db()
    conn = db._conn()
    try:
        baseline = conn.execute(
            "SELECT id FROM sermons WHERE classified_as='sermon' ORDER BY preach_date DESC LIMIT 1"
        ).fetchone()
        baseline_id = baseline[0] if baseline else None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE coaching_commitments SET status='superseded' WHERE status='active'")
        conn.execute("""
            INSERT INTO coaching_commitments (dimension_key, practice_experiment, target_sermons,
                baseline_sermon_id, status, created_at)
            VALUES (?, ?, ?, ?, 'active', ?)
        """, (dimension_key, experiment, target, baseline_id, now))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return jsonify({'id': new_id, 'status': 'active'})
    finally:
        conn.close()


@sermons_bp.route('/<int:sermon_id>/coach/history', methods=['GET'])
def sermon_coach_history(sermon_id):
    db = get_db()
    try:
        conversation_id = int(request.args.get('conversation_id', 1))
    except (ValueError, TypeError):
        conversation_id = 1
    conn = db._conn()
    rows = conn.execute("""
        SELECT role, content FROM sermon_coach_messages
        WHERE sermon_id = ? AND conversation_id = ? AND role IN ('user', 'assistant')
        ORDER BY id
    """, (sermon_id, conversation_id)).fetchall()
    conn.close()
    return jsonify([{'role': r[0], 'content': r[1]} for r in rows if r[1]])


@sermons_bp.route('/<int:sermon_id>/coach/message', methods=['POST'])
def sermon_coach_message(sermon_id):
    import json as _json
    from sermon_coach_agent import stream_coach_response
    from llm_client import AnthropicClient
    user_message = request.json.get('message') if request.is_json else request.form.get('message', '')
    try:
        conversation_id = int(request.json.get('conversation_id', 1)) if request.is_json else 1
    except (ValueError, TypeError):
        conversation_id = 1
    db = get_db()
    api_key = anthropic_api_key()
    client = AnthropicClient(api_key=api_key)

    def generate():
        for event in stream_coach_response(
            db=db, sermon_id=sermon_id, conversation_id=conversation_id,
            user_message=user_message, llm_client=client,
        ):
            yield f"data: {_json.dumps(event)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@sermons_bp.route('/coaching-insight', methods=['POST'])
def create_coaching_insight():
    import json as _json
    data = request.get_json()
    if not data or not isinstance(data, dict) or not data.get('summary', '').strip():
        return jsonify({'error': 'summary is required'}), 400
    db = get_db()
    conn = db._conn()
    try:
        conn.execute("""
            INSERT INTO coaching_insights
                (dimension_key, summary, applies_when, avoid_when,
                 source_sermon_id, source_conversation_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            data.get('dimension_key'),
            data['summary'].strip(),
            _json.dumps(list(data.get('applies_when', []))),
            _json.dumps(list(data.get('avoid_when', []))),
            data.get('source_sermon_id'),
            data.get('source_conversation_id'),
        ))
        insight_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return jsonify({'id': insight_id, 'status': 'saved'}), 201
    finally:
        conn.close()


app.register_blueprint(sermons_bp)


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    startup()
    if _APSCHEDULER_AVAILABLE:
        get_scheduler()
    port = int(os.environ.get("FLASK_PORT", "5111"))
    print(f"Sermon Research Workbench starting on http://localhost:{port}", file=sys.stderr)
    print(f"  Companion at http://localhost:{port}/companion/", file=sys.stderr)
    print(f"  Study at http://localhost:{port}/study/", file=sys.stderr)
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
