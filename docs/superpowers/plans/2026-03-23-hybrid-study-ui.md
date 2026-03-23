# Hybrid Card→Conversation Study UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the conversation-first `/study/` UI with a hybrid workflow: structured cards for phases 1-5 (Bryan drives, AI silent) with auto-loaded THGNT/BHS and study bible notes, then seamless transition to AI conversation for phases 6-16 following Bryan's 16-step sermon prep methodology.

**Architecture:** The existing `/study/` routes, templates, JS, and CSS are replaced. Card phases use HTMX to swap card content without page reloads. Phase 6+ reuses the existing SSE streaming conversation engine (`stream_study_response`). A new `find_study_bible_notes()` function in `study.py` queries all 7 study bibles via navindex. The system prompt is rebuilt to encode Bryan's full 16-step workflow with phase-aware coaching intensity.

**Tech Stack:** Python/Flask, HTMX, SSE streaming, SQLite, Anthropic Claude API, LogosReader (C# P/Invoke), Jinja2 templates

**Key prerequisite already done:** LogosReader driver version updated from `2019-05-26` to `2025-05-27`, unlocking all 7 study bibles + BDAG.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `tools/study.py` | Modify | Add `find_study_bible_notes(ref)` function |
| `tools/workbench/app.py` | Modify | Replace `/study/` routes with card+conversation hybrid |
| `tools/workbench/companion_db.py` | Modify | Add `save_card_annotations()`, `get_card_annotations()` methods |
| `tools/workbench/companion_agent.py` | Modify | Rewrite `build_study_prompt()` for 16-step workflow |
| `tools/workbench/templates/study_session.html` | Rewrite | Hybrid layout: top bar + card/conversation area + outline sidebar |
| `tools/workbench/templates/partials/study_card.html` | Create | Card partial for phases 1-5 (HTMX-swappable) |
| `tools/workbench/static/study.js` | Rewrite | Card navigation, star annotations, tab switching, transition to conversation |
| `tools/workbench/static/study.css` | Rewrite | Card styles, tabs, stars, annotations notepad, conversation styles |
| `tools/workbench/tests/test_study_bible_notes.py` | Create | Tests for study bible lookup function |
| `tools/workbench/tests/test_study_routes.py` | Modify | Update/add tests for new card+conversation routes |

---

## Task 1: Add `find_study_bible_notes()` to study.py

**Files:**
- Modify: `tools/study.py` (add function after `find_commentaries_for_ref` at ~line 368)
- Create: `tools/workbench/tests/test_study_bible_notes.py`

This function queries all 7 study bibles for a passage using the existing `find_commentary_section()` which already handles the `bible+version` navindex format (fixed earlier this session).

- [ ] **Step 1: Write the failing test**

```python
# tools/workbench/tests/test_study_bible_notes.py
"""Tests for study bible notes lookup."""
import pytest
from unittest.mock import patch, MagicMock


def test_find_study_bible_notes_returns_dict_per_bible():
    """Should return a list of dicts with title, abbrev, and text keys."""
    from tools.study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:1-7")
    results = find_study_bible_notes(ref)
    assert isinstance(results, list)
    # Should attempt all 7 study bibles
    for r in results:
        assert "title" in r
        assert "abbrev" in r
        assert "text" in r
        assert isinstance(r["text"], str)


def test_find_study_bible_notes_handles_missing_files():
    """Should skip study bibles whose files don't exist."""
    from tools.study import find_study_bible_notes
    ref = {"book": 66, "book_name": "Romans", "chapter": 1,
           "verse_start": 1, "verse_end": 7, "ref_str": "Romans 1:1-7"}
    # Should not raise even if some files are missing
    results = find_study_bible_notes(ref)
    assert isinstance(results, list)


def test_find_study_bible_notes_truncates_long_text():
    """Should truncate study bible notes longer than max_chars."""
    from tools.study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:1-7")
    results = find_study_bible_notes(ref, max_chars=200)
    for r in results:
        if r["text"]:
            assert len(r["text"]) <= 250  # 200 + allowance for truncation marker
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -v`
Expected: FAIL with `ImportError: cannot import name 'find_study_bible_notes'`

- [ ] **Step 3: Write the implementation**

Add to `tools/study.py` after `find_commentaries_for_ref()` (~line 368):

```python
# ── Study Bible Resources ────────────────────────────────────────────────

STUDY_BIBLES = [
    {"resource_id": "LLS:ESVSB", "abbrev": "ESV SB", "title": "ESV Study Bible", "file": "ESVSB.logos4"},
    {"resource_id": "LLS:CSBANCIENTFAITHSB", "abbrev": "Ancient Faith", "title": "Ancient Faith Study Bible: Notes", "file": "CSBANCIENTFAITHSB.logos4"},
    {"resource_id": "LLS:ESVREFSTBBL", "abbrev": "Reformation SB", "title": "The Reformation Study Bible", "file": "ESVREFSTBBL.logos4"},
    {"resource_id": "LLS:FSB", "abbrev": "FSB", "title": "Faithlife Study Bible", "file": "FSB.logos4"},
    {"resource_id": "LLS:GENEVABBL1560NOTE", "abbrev": "Geneva Notes", "title": "Geneva Bible: Notes", "file": "GENEVABBL1560NOTE.logos4"},
    {"resource_id": "LLS:NVCLTRLBCBBLNTS", "abbrev": "NIV Cultural BG", "title": "NIV Cultural Backgrounds Study Bible", "file": "NVCLTRLBCBBLNTS.logos4"},
    {"resource_id": "LLS:NIVZNDRVNSTBBL", "abbrev": "NIVBT SB", "title": "NIV Biblical Theology Study Bible", "file": "NIVZNDRVNSTBBL.logos4"},
]


def find_study_bible_notes(ref, max_chars=5000):
    """Look up notes for a passage across all 7 study bibles.

    Returns list of dicts: [{"title", "abbrev", "text"}, ...]
    Only includes study bibles that returned content.
    """
    results = []
    for sb in STUDY_BIBLES:
        fpath = os.path.join(RESOURCES_DIR, sb["file"])
        if not os.path.isfile(fpath):
            continue
        try:
            text = find_commentary_section(fpath, ref)
            if text:
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n\n[... truncated ...]"
                results.append({
                    "title": sb["title"],
                    "abbrev": sb["abbrev"],
                    "text": text,
                })
        except Exception:
            continue
    return results
```

Also ensure `RESOURCES_DIR` is defined near the top of `study.py`. Check for an existing constant — it should be something like:
```python
RESOURCES_DIR = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_study_bible_notes.py -v`
Expected: 3 PASS (note: tests that read actual files will only pass if the Logos library is accessible; mock tests should always pass)

- [ ] **Step 5: Run full test suite**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/ -v --tb=short -q`
Expected: 105+ passed (existing tests must not break)

- [ ] **Step 6: Commit**

```bash
git add tools/study.py tools/workbench/tests/test_study_bible_notes.py
git commit -m "feat: add find_study_bible_notes() for 7 study bible lookup"
```

---

## Task 2: Add card annotations to companion_db.py

**Files:**
- Modify: `tools/workbench/companion_db.py`
- Modify: `tools/workbench/tests/test_companion_db.py`

Add a `card_annotations` table for storing starred study bible passages + freeform notepad content from step 5.

- [ ] **Step 1: Write the failing test**

Add to `tools/workbench/tests/test_companion_db.py`:

```python
def test_save_and_get_card_annotations(tmp_path):
    """Card annotations (stars + notepad) should round-trip."""
    db = CompanionDB(str(tmp_path / "test.db"))
    db.init_db()
    sid = db.create_session("Romans 1:1-7", 66, 1, 1, 7, "epistle")

    # Save a star annotation
    aid = db.save_card_annotation(sid, phase="study_bibles", source="ESV SB",
                                   starred_text="δοῦλος carries OT connotations",
                                   note="Moses parallel for intro")
    assert aid is not None

    # Save notepad content
    db.save_card_notepad(sid, phase="study_bibles",
                         content="Key theme: covenant service language")

    # Retrieve
    annotations = db.get_card_annotations(sid, phase="study_bibles")
    assert len(annotations) == 1
    assert annotations[0]["starred_text"] == "δοῦλος carries OT connotations"
    assert annotations[0]["note"] == "Moses parallel for intro"

    notepad = db.get_card_notepad(sid, phase="study_bibles")
    assert notepad == "Key theme: covenant service language"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_companion_db.py::test_save_and_get_card_annotations -v`
Expected: FAIL — method doesn't exist

- [ ] **Step 3: Add schema + methods to companion_db.py**

Add to `init_db()` method's CREATE TABLE block:

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS card_annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES sessions(id),
        phase TEXT NOT NULL,
        source TEXT,
        starred_text TEXT,
        note TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS card_notepads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES sessions(id),
        phase TEXT NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(session_id, phase)
    )
""")
```

Add methods:

```python
def save_card_annotation(self, session_id, phase, source, starred_text, note=""):
    cursor = self.conn.execute(
        "INSERT INTO card_annotations (session_id, phase, source, starred_text, note) VALUES (?, ?, ?, ?, ?)",
        (session_id, phase, source, starred_text, note))
    self.conn.commit()
    return cursor.lastrowid

def get_card_annotations(self, session_id, phase=None):
    if phase:
        rows = self.conn.execute(
            "SELECT id, source, starred_text, note, created_at FROM card_annotations WHERE session_id = ? AND phase = ? ORDER BY created_at",
            (session_id, phase)).fetchall()
    else:
        rows = self.conn.execute(
            "SELECT id, source, starred_text, note, created_at FROM card_annotations WHERE session_id = ? ORDER BY created_at",
            (session_id,)).fetchall()
    return [{"id": r[0], "source": r[1], "starred_text": r[2], "note": r[3], "created_at": r[4]} for r in rows]

def save_card_notepad(self, session_id, phase, content):
    self.conn.execute(
        "INSERT INTO card_notepads (session_id, phase, content) VALUES (?, ?, ?) ON CONFLICT(session_id, phase) DO UPDATE SET content = ?, updated_at = datetime('now')",
        (session_id, phase, content, content))
    self.conn.commit()

def get_card_notepad(self, session_id, phase):
    row = self.conn.execute(
        "SELECT content FROM card_notepads WHERE session_id = ? AND phase = ?",
        (session_id, phase)).fetchone()
    return row[0] if row else ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_companion_db.py -v`
Expected: All tests pass including new one

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_db.py tools/workbench/tests/test_companion_db.py
git commit -m "feat: add card_annotations and card_notepads tables for study bible star+notepad"
```

---

## Task 3: Add card routes to app.py

**Files:**
- Modify: `tools/workbench/app.py` (study routes section, ~lines 732-862)
- Modify: `tools/workbench/tests/test_study_routes.py`

Replace the existing conversation-only `/study/session/<id>` with card-aware routes.

- [ ] **Step 1: Write failing tests for new card routes**

Add to `tools/workbench/tests/test_study_routes.py`:

```python
def _make_study_session(client):
    """Helper to create a study session and return its ID."""
    resp = client.post("/study/session/new", data={"passage": "Romans 1:1-7"},
                       follow_redirects=True)
    # Extract session ID from the redirect URL or page
    import re
    match = re.search(r'/study/session/(\d+)', resp.request.path if hasattr(resp, 'request') else str(resp.data))
    if match:
        return int(match.group(1))
    # Fallback: get from DB
    from tools.workbench.companion_db import CompanionDB
    db = CompanionDB()
    sessions = db.list_sessions()
    return sessions[-1]["id"] if sessions else None


def test_study_session_shows_card_phase(client):
    """GET /study/session/<id> should show card UI for phases 1-5."""
    sid = _make_study_session(client)
    resp = client.get(f"/study/session/{sid}")
    assert resp.status_code == 200
    assert b"study-card" in resp.data  # card container present


def test_study_card_next(client):
    """POST /study/session/<id>/card/next should redirect to next phase."""
    sid = _make_study_session(client)
    resp = client.post(f"/study/session/{sid}/card/next",
                       data={"response": "My prayer for this study"},
                       follow_redirects=True)
    assert resp.status_code == 200


def test_study_card_back(client):
    """POST /study/session/<id>/card/back should go to previous phase."""
    sid = _make_study_session(client)
    # First advance past prayer
    client.post(f"/study/session/{sid}/card/next",
                data={"response": "prayer"}, follow_redirects=True)
    resp = client.post(f"/study/session/{sid}/card/back", follow_redirects=True)
    assert resp.status_code == 200


def test_study_session_transition_to_conversation(client):
    """After completing phase 5, session should show conversation UI."""
    sid = _make_study_session(client)
    # Advance through all 5 card phases
    for i in range(5):
        client.post(f"/study/session/{sid}/card/next",
                    data={"response": f"response {i}"}, follow_redirects=True)
    resp = client.get(f"/study/session/{sid}")
    assert resp.status_code == 200
    assert b"conversation-column" in resp.data  # conversation UI present


def test_study_bible_notes_route(client):
    """GET /study/session/<id>/study-bibles should return study bible notes."""
    sid = _make_study_session(client)
    resp = client.get(f"/study/session/{sid}/study-bibles")
    assert resp.status_code == 200


def test_study_annotation_save(client):
    """POST /study/session/<id>/annotate should save a star annotation."""
    sid = _make_study_session(client)
    resp = client.post(f"/study/session/{sid}/annotate",
                       json={"source": "ESV SB",
                             "starred_text": "test quote",
                             "note": "important"})
    assert resp.status_code == 200


def test_study_notepad_save(client):
    """POST /study/session/<id>/notepad should save notepad content."""
    sid = _make_study_session(client)
    resp = client.post(f"/study/session/{sid}/notepad",
                       json={"phase": "study_bibles",
                             "content": "My observations"})
    assert resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_study_routes.py -v -k "card or transition or bible_notes or annotation or notepad"`
Expected: FAIL

- [ ] **Step 3: Define the 5 card phases**

Add a constant near the study routes in `app.py`:

```python
CARD_PHASES = [
    {"key": "prayer", "label": "Prayer", "prompt": "Pray for your study of this passage.",
     "guidance": "Ask the Spirit to open your eyes to see wonderful things in His word. Pray for your congregation.",
     "has_textarea": True, "auto_resource": None},
    {"key": "read_text", "label": "Read the Text", "prompt": "Read the passage in the original language.",
     "guidance": "Read it slowly. Read it again. Let the words sit.",
     "has_textarea": False, "auto_resource": "original_language"},
    {"key": "translation", "label": "Working Translation", "prompt": "Write your own translation of the passage.",
     "guidance": "Work from the Greek/Hebrew text above. Don't reach for a published translation — wrestle with the words yourself.",
     "has_textarea": True, "auto_resource": "original_language"},
    {"key": "digestion", "label": "Digestion", "prompt": "Pray through the text phrase by phrase.",
     "guidance": "Take each phrase and turn it into prayer. What is God saying? What stirs in you?",
     "has_textarea": True, "auto_resource": None},
    {"key": "study_bibles", "label": "Study Bible Consultation", "prompt": "Review notes from your study bibles.",
     "guidance": "Star passages that catch your eye. Use the notepad to capture your thinking. These feed into the conversation.",
     "has_textarea": False, "auto_resource": "study_bibles"},
]
```

- [ ] **Step 4: Implement card routes**

Replace/augment the study routes in `app.py`:

```python
@app.route("/study/session/<session_id>")
def study_session(session_id):
    session = db.get_session(session_id)
    if not session:
        return redirect(url_for("study_start"))

    phase = session.get("current_phase", "prayer")

    # Determine if we're in card mode or conversation mode
    card_phase_keys = [p["key"] for p in CARD_PHASES]
    if phase in card_phase_keys:
        phase_index = card_phase_keys.index(phase)
        card_def = CARD_PHASES[phase_index]
        # Get auto-resource content
        resource_text = None
        study_bible_notes = None
        if card_def["auto_resource"] == "original_language":
            resource_text = _get_original_language_text(session)
        elif card_def["auto_resource"] == "study_bibles":
            study_bible_notes = _get_study_bible_notes(session)
        # Get existing response for this phase
        responses = db.get_card_responses(session_id, phase)
        prefilled = responses[-1]["content"] if responses else ""
        # Get annotations for study_bibles phase
        annotations = db.get_card_annotations(session_id, phase) if phase == "study_bibles" else []
        notepad = db.get_card_notepad(session_id, phase) if phase == "study_bibles" else ""
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
                               outline=db.get_outline_tree(session_id))
    else:
        # Conversation mode — phase 6+
        messages = db.get_messages(session_id, limit=100)
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
                               outline=db.get_outline_tree(session_id))


@app.route("/study/session/<session_id>/card/next", methods=["POST"])
def study_card_next(session_id):
    """Advance to next card phase, saving current response."""
    session = db.get_session(session_id)
    if not session:
        return "Session not found", 404

    phase = session.get("current_phase", "prayer")
    response_text = request.form.get("response", "").strip()

    # Save card response if provided
    # Note: question_id=0 is used as sentinel for card-phase responses (no associated question)
    # The card_responses.question_id column has a NOT NULL constraint
    if response_text:
        db.save_card_response(session_id, phase, question_id=0, content=response_text)

    # Advance phase
    card_phase_keys = [p["key"] for p in CARD_PHASES]
    if phase in card_phase_keys:
        idx = card_phase_keys.index(phase)
        if idx < len(card_phase_keys) - 1:
            next_phase = card_phase_keys[idx + 1]
            db.update_phase(session_id, next_phase)
        else:
            # Done with cards — transition to conversation
            db.update_phase(session_id, "context")
            # Save an opening context message summarizing card work
            _save_card_summary_for_ai(session_id, db)

    # Return the updated card via HTMX or redirect
    return redirect(url_for("study_session_view", session_id=session_id))


@app.route("/study/session/<session_id>/card/back", methods=["POST"])
def study_card_back(session_id):
    """Go back to previous card phase."""
    session = db.get_session(session_id)
    if not session:
        return "Session not found", 404

    phase = session.get("current_phase", "prayer")
    card_phase_keys = [p["key"] for p in CARD_PHASES]
    if phase in card_phase_keys:
        idx = card_phase_keys.index(phase)
        if idx > 0:
            db.update_phase(session_id, card_phase_keys[idx - 1])

    return redirect(url_for("study_session_view", session_id=session_id))


@app.route("/study/session/<session_id>/study-bibles")
def study_bible_notes_route(session_id):
    """Return study bible notes as JSON."""
    session = db.get_session(session_id)
    if not session:
        return jsonify({"error": "not found"}), 404
    notes = _get_study_bible_notes(session)
    return jsonify(notes)


@app.route("/study/session/<session_id>/annotate", methods=["POST"])
def study_annotate(session_id):
    """Save a star annotation."""
    data = request.get_json()
    aid = db.save_card_annotation(
        session_id, phase="study_bibles",
        source=data.get("source", ""),
        starred_text=data.get("starred_text", ""),
        note=data.get("note", ""))
    return jsonify({"id": aid})


@app.route("/study/session/<session_id>/notepad", methods=["POST"])
def study_notepad(session_id):
    """Save notepad content."""
    data = request.get_json()
    db.save_card_notepad(session_id, phase=data.get("phase", "study_bibles"),
                         content=data.get("content", ""))
    return jsonify({"ok": True})
```

Also add helper functions:

```python
def _get_original_language_text(session):
    """Get THGNT (NT) or BHS (OT) text for the session's passage."""
    from tools.study import parse_reference, resolve_bible_files, read_bible_chapter, extract_verses
    ref = parse_reference(session["passage_ref"])
    if not ref:
        return None
    # NT = books 40-66 (Matthew onwards), OT = 1-39
    version = "THGNTCROSSWAY" if ref["book"] >= 40 else "BHS"
    files = resolve_bible_files([version])
    if not files:
        return None
    text, _ = read_bible_chapter(files[0], ref["book"], ref["chapter"])
    if text and ref.get("verse_start"):
        text = extract_verses(text, ref["verse_start"], ref.get("verse_end"))
    return text


def _get_study_bible_notes(session):
    """Get study bible notes for the session's passage."""
    from tools.study import parse_reference, find_study_bible_notes
    ref = parse_reference(session["passage_ref"])
    if not ref:
        return []
    return find_study_bible_notes(ref, max_chars=5000)


def _save_card_summary_for_ai(session_id, db):
    """Save a system message summarizing Bryan's card work for the AI."""
    responses = db.get_card_responses(session_id)
    annotations = db.get_card_annotations(session_id)
    notepad_text = db.get_card_notepad(session_id, "study_bibles")

    parts = []
    for resp in responses:
        if resp.get("content"):
            parts.append(f"[{resp['phase']}] {resp['content']}")
    if annotations:
        parts.append("\n[Study Bible Stars]")
        for a in annotations:
            line = f"  ★ {a['source']}: \"{a['starred_text']}\""
            if a.get("note"):
                line += f" → {a['note']}"
            parts.append(line)
    if notepad_text:
        parts.append(f"\n[Study Bible Notepad]\n{notepad_text}")

    if parts:
        summary = "Bryan's card-phase work:\n" + "\n".join(parts)
        db.save_message(session_id, "context", "system", summary)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_study_routes.py -v`
Expected: All tests pass (existing + new)

- [ ] **Step 5: Run full test suite**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/ -v --tb=short -q`
Expected: 105+ passed

- [ ] **Step 6: Commit**

```bash
git add tools/workbench/app.py tools/workbench/tests/test_study_routes.py
git commit -m "feat: add card phase routes for hybrid study UI (phases 1-5)"
```

---

## Task 4: Build the study_session.html template

**Files:**
- Rewrite: `tools/workbench/templates/study_session.html`
- Create: `tools/workbench/templates/partials/study_card.html`

The template renders either card mode (phases 1-5) or conversation mode (phase 6+) based on the `mode` variable.

- [ ] **Step 1: Write study_session.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ session.passage_ref }} — Study</title>
    <link rel="stylesheet" href="/static/study.css?v=2">
</head>
<body>
<div id="study-app">
    <!-- Top Bar -->
    <div id="study-topbar">
        <div class="topbar-passage">{{ session.passage_ref }}</div>
        <div class="topbar-dots">
            {% for i in range(total_phases) %}
            <span class="phase-dot {% if i < phase_index %}done{% elif i == phase_index %}current{% endif %}"
                  title="{{ ['Prayer','Read','Translate','Digest','Study Bibles'][i] if i < 5 else 'Conversation' }}"></span>
            {% endfor %}
            <span class="phase-divider"></span>
            <span class="phase-dot {% if mode == 'conversation' %}current{% endif %}" title="Conversation"></span>
        </div>
        <div id="session-clock" class="topbar-clock">0:00</div>
    </div>

    <!-- Main Area -->
    <div id="study-main">
        {% if mode == "card" %}
        <!-- Card Phase -->
        <div id="card-area">
            {% include "partials/study_card.html" %}
        </div>
        {% else %}
        <!-- Conversation Phase -->
        <div id="conversation-column">
            <div id="conversation-thread">
                {% for msg in messages %}
                {% if msg.role != "system" %}
                <div class="conv-message {{ msg.role }}">
                    <div class="msg-content">{{ msg.content }}</div>
                </div>
                {% endif %}
                {% endfor %}
            </div>
            <div id="input-area">
                <textarea id="study-input" placeholder="Talk with your study partner..." rows="2"></textarea>
                <button id="btn-study-send">Send</button>
            </div>
        </div>
        {% endif %}

        <!-- Outline Sidebar -->
        <div id="outline-sidebar">
            <div class="sidebar-header">
                <input id="outline-title" placeholder="Sermon title...">
            </div>
            <div id="outline-tree-container"></div>
            <div class="sidebar-footer">
                <input id="outline-add-input" placeholder="+ add note">
                <select id="outline-add-type">
                    <option value="note">Note</option>
                    <option value="main_point">Main pt</option>
                    <option value="sub_point">Sub pt</option>
                    <option value="cross_ref">Ref</option>
                </select>
            </div>
        </div>
    </div>
</div>

<script src="/static/study.js?v=2"></script>
<script>
    window.studySessionId = "{{ session.id }}";
    window.studyMode = "{{ mode }}";
    studyClock.start({{ session.total_elapsed_seconds or 0 }});
</script>
</body>
</html>
```

- [ ] **Step 2: Write study_card.html partial**

```html
<div class="study-card">
    <div class="card-phase-label">{{ card.label }}</div>
    <h3 class="card-prompt">{{ card.prompt }}</h3>
    {% if card.guidance %}
    <p class="card-guidance">{{ card.guidance }}</p>
    {% endif %}

    {% if resource_text %}
    <div class="card-resource">
        <div class="card-resource-label">
            {% if session.book >= 40 %}THGNT{% else %}BHS{% endif %}
        </div>
        <div class="card-resource-text {% if session.book < 40 %}rtl{% endif %}">{{ resource_text }}</div>
    </div>
    {% endif %}

    {% if study_bible_notes %}
    <div class="study-bible-container">
        <div class="sb-tabs">
            {% for note in study_bible_notes %}
            <button class="sb-tab {% if loop.first %}active{% endif %}"
                    data-tab="{{ loop.index0 }}"
                    onclick="switchStudyBibleTab(this, {{ loop.index0 }})">{{ note.abbrev }}</button>
            {% endfor %}
        </div>
        <div class="sb-content-area">
            {% for note in study_bible_notes %}
            <div class="sb-content {% if loop.first %}active{% endif %}" data-tab="{{ loop.index0 }}">
                <div class="sb-text" data-source="{{ note.abbrev }}">{{ note.text }}</div>
            </div>
            {% endfor %}
        </div>
        <div class="sb-annotations">
            <div class="sb-notepad-label">My Notes</div>
            <textarea class="sb-notepad" placeholder="Capture your thinking..."
                      oninput="debouncedSaveNotepad(this.value)">{{ notepad }}</textarea>
            {% if annotations %}
            <div class="sb-stars">
                {% for a in annotations %}
                <div class="sb-star-item">
                    <span class="star-icon">★</span>
                    <span class="star-source">{{ a.source }}:</span>
                    <span class="star-text">"{{ a.starred_text }}"</span>
                    {% if a.note %}<span class="star-note">→ {{ a.note }}</span>{% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
    </div>
    {% endif %}

    {% if card.has_textarea %}
    <textarea class="card-textarea" name="response" placeholder="Your response..." rows="5">{{ prefilled }}</textarea>
    {% endif %}

    <div class="card-actions">
        {% if phase_index > 0 %}
        <form method="POST" action="/study/session/{{ session.id }}/card/back">
            <button type="submit" class="btn btn-secondary">← Back</button>
        </form>
        {% else %}
        <div></div>
        {% endif %}
        <form method="POST" action="/study/session/{{ session.id }}/card/next" id="card-next-form">
            <textarea name="response" style="display:none;" id="hidden-response"></textarea>
            <button type="submit" class="btn btn-primary" onclick="copyCardResponse()">
                {% if phase_index == total_phases - 1 %}Begin Conversation →{% else %}Next →{% endif %}
            </button>
        </form>
    </div>
</div>
```

- [ ] **Step 3: Verify template renders**

Run the app and visit `/study/`, create a new session, verify:
1. Card UI shows for prayer phase
2. "Next" advances to read_text phase with THGNT/BHS auto-loaded
3. All 5 phases work
4. After phase 5, conversation UI appears

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/templates/study_session.html tools/workbench/templates/partials/study_card.html
git commit -m "feat: hybrid study_session template with card phases 1-5 and conversation 6+"
```

---

## Task 5: Build study.css

**Files:**
- Rewrite: `tools/workbench/static/study.css`

- [ ] **Step 1: Write the CSS**

Key sections to include (full CSS should be written — dark ADHD-friendly theme matching existing companion.css design tokens):

- Design tokens (dark theme: `--bg: #1a1a2e`, `--text: #e0e0e0`, `--blue: #5b8dd9`, `--green: #4a7c59`, `--gold: #d4a55a`)
- `#study-app` — flex column, full height
- `#study-topbar` — passage, phase dots, clock
- `.phase-dot` — 8px circles, `.done` = green, `.current` = blue, `.phase-divider` = vertical line
- `#study-main` — flex row, card-area + outline-sidebar
- `.study-card` — card container, max-width 800px centered
- `.card-phase-label` — uppercase, small, blue
- `.card-resource` — original language display with left border
- `.rtl` — direction: rtl for Hebrew
- `.study-bible-container` — tabs + content + annotations
- `.sb-tabs` / `.sb-tab` — horizontal tab bar, overflow-x auto
- `.sb-content` — tab content panel, hidden unless `.active`
- `.sb-text` — readable font, line-height 1.7
- `.sb-annotations` — right-side notepad area
- `.sb-notepad` — textarea, gold accent
- `.sb-stars` / `.sb-star-item` — starred items with gold star icon
- `.card-textarea` — response textarea
- `.card-actions` — flex row, space-between
- `#conversation-column` — flex column, conversation thread + input area (reuse existing conversation styles)
- `#outline-sidebar` — 300px, collapsible
- No animations or transitions (ADHD-friendly)

- [ ] **Step 2: Verify visual appearance**

Visit the app, check:
1. Dark theme with calm colors
2. Card fits comfortably in viewport
3. Study bible tabs work visually
4. Notepad is visible alongside study bible content
5. Phase dots show correct state

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/static/study.css
git commit -m "feat: dark ADHD-friendly CSS for hybrid study UI"
```

---

## Task 6: Build study.js

**Files:**
- Rewrite: `tools/workbench/static/study.js`

- [ ] **Step 1: Write the JavaScript**

Key functions:

```javascript
// ── Session Clock (reuse existing pattern) ──
const studyClock = { /* ... same as existing ... */ };

// ── Card Phase Functions ──
function switchStudyBibleTab(btn, index) { /* show/hide tab content */ }
function copyCardResponse() { /* copy visible textarea to hidden form field */ }

// ── Star Annotations (study bibles phase) ──
function starSelectedText(source) {
    const selection = window.getSelection();
    if (!selection.rangeCount || selection.isCollapsed) return;
    const text = selection.toString().trim();
    if (!text) return;
    const note = prompt("Why is this important? (optional)") || "";
    fetch(`/study/session/${window.studySessionId}/annotate`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source, starred_text: text, note})
    }).then(() => location.reload());
}

// ── Notepad Auto-save ──
let notepadTimer = null;
function debouncedSaveNotepad(content) {
    clearTimeout(notepadTimer);
    notepadTimer = setTimeout(() => {
        fetch(`/study/session/${window.studySessionId}/notepad`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({phase: "study_bibles", content})
        });
    }, 1000);
}

// ── Conversation Functions (reuse existing SSE pattern) ──
async function sendStudyMessage(sessionId, message) { /* existing SSE streaming */ }
function appendConvMessage(role, text) { /* existing */ }
function handleSSEEvent(data, assistantEl) { /* existing */ }

// ── Outline Functions (reuse existing) ──
function refreshOutline() { /* existing */ }
function renderOutlineTree(tree) { /* existing */ }

// ── Star button on study bible text ──
// Add mouseup listener to .sb-text elements to show star button on text selection
document.addEventListener("DOMContentLoaded", () => {
    if (window.studyMode === "card") {
        document.querySelectorAll(".sb-text").forEach(el => {
            el.addEventListener("mouseup", () => {
                const sel = window.getSelection();
                if (sel && !sel.isCollapsed) {
                    // Show floating star button near selection
                    showStarButton(el.dataset.source);
                }
            });
        });
    } else {
        // Conversation mode — wire up send button and input
        // ... existing conversation wiring ...
    }
    refreshOutline();
});
```

- [ ] **Step 2: Test in browser**

1. Card phase: navigate through phases 1-5
2. Study bibles: switch tabs, select text, star it
3. Notepad: type content, verify auto-save
4. Transition: after phase 5, conversation UI appears
5. Conversation: send a message, verify SSE streaming works

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/static/study.js
git commit -m "feat: study.js with card navigation, star annotations, and conversation streaming"
```

---

## Task 7: Rewrite `build_study_prompt()` for 16-step workflow

**Files:**
- Modify: `tools/workbench/companion_agent.py`
- Modify: `tools/workbench/tests/test_companion_agent.py`

The system prompt must encode Bryan's full 16-step workflow so the AI knows which step Bryan is on and adjusts its coaching intensity accordingly.

- [ ] **Step 1: Write failing test**

Add to `tools/workbench/tests/test_companion_agent.py`:

```python
def test_build_study_prompt_includes_16_steps():
    """System prompt should reference the 16-step workflow phases."""
    from tools.workbench.companion_agent import build_study_prompt
    prompt = build_study_prompt("Romans 1:1-7", "epistle", 1800)
    # Should mention key homiletical concepts
    assert "FCF" in prompt or "Fallen Condition" in prompt
    assert "EP" in prompt or "Exegetical Point" in prompt
    assert "HP" in prompt or "Homiletical Point" in prompt
    assert "THT" in prompt or "Take Home Truth" in prompt


def test_build_study_prompt_includes_card_summary():
    """System prompt should incorporate Bryan's card-phase work."""
    from tools.workbench.companion_agent import build_study_prompt
    card_summary = "[prayer] Lord, open my eyes\n[translation] Paul, slave of Christ Jesus..."
    prompt = build_study_prompt("Romans 1:1-7", "epistle", 3600,
                                card_work_summary=card_summary)
    assert "slave of Christ Jesus" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_companion_agent.py -v -k "16_steps or card_summary"`
Expected: FAIL

- [ ] **Step 3: Rewrite build_study_prompt()**

Update the function signature to accept `card_work_summary=""` and rewrite the prompt body. The prompt should include:

1. **Identity**: "You are Bryan's graduate research assistant and homiletical coach"
2. **Bryan's workflow context**: Summarize the 16-step structure, note where Bryan is (past cards, now in conversation)
3. **Card-phase work**: Include his prayer, translation, digestion notes, starred study bible passages, notepad
4. **Phase-specific coaching intensity**:
   - Steps 6-8: Help Bryan think, offer options, pull library resources
   - Steps 9-10, 12: **Triage the volume** — surface what's relevant, prevent rabbit holes, enforce time
   - Step 11: Proactively surface Westminster/confessional material
   - Steps 13-14: **Push hardest** — force Bryan to state EP, FCF, HP/THT in single sentences; challenge weak formulations; enforce illustration discipline (one per point)
   - Steps 15-16: Final review questions, push to edit ruthlessly
5. **Homiletical guardrails**: Include the specific sub-steps from Bryan's methodology (13.1-13.8, 14.1-14.4)
6. **ADHD awareness**: One thing at a time, no step counts visible, don't let Bryan linger in comfort zone of exegesis when he should be doing homiletics
7. **Illustration discipline**: "Bryan tends to stack 3-4 illustrations per point. Push him to pick his best one and move on. Quote his own guide: 'Do NOT let the sermon be nothing but illustrations.'"
8. **Sermon length**: "Target 25-30 minutes. If the outline grows beyond 3 main points, push back."
9. **Available tools**: All 10 companion tools
10. **Step 8 — 7 Christ-identification lenses**: redemptive-historical, promise-fulfillment, typology, analogy, longitudinal themes, contrast, NT reference
11. **Step 14.2 — 12 Application Prods**: Why It Matters, Dissecting the Message, Clarifying, Analyzing Reaction, Addressing Struggle, Challenging Frameworks, Shaping Loyalties, Envisioning Realization, Ministering Truth, In Real Life, Pursuing Growth, Reaching Unbelievers
12. **Step 14.3 — 10 intro types**: Front Porch, Challenge/White Glove, Mystery, Examination, Paradox, Occasion, Quote, Question, Short Story, Ramrod
13. **Step 15 — 14 finishing questions**: faithful to text, prayed for age groups, head+heart balance, lecture vs sermon, missional reading, tangible application, bound the wounded, freedom to captives, good news to poor, FCF intro, landed the sermon
14. **Conversation phase tracking**: The AI manages step progression internally through conversation context (no DB phase tracking for steps 6-16). The system prompt instructs the AI to guide Bryan through the steps and announce transitions naturally.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/test_companion_agent.py -v`
Expected: All pass

- [ ] **Step 5: Run full test suite**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/ -v --tb=short -q`
Expected: 105+ passed

- [ ] **Step 6: Commit**

```bash
git add tools/workbench/companion_agent.py tools/workbench/tests/test_companion_agent.py
git commit -m "feat: rewrite study prompt for 16-step workflow with homiletical coaching"
```

---

## Task 8: Wire conversation transition and update stream_study_response

**Files:**
- Modify: `tools/workbench/companion_agent.py` (stream_study_response)
- Modify: `tools/workbench/app.py` (discuss route)

The conversation streaming must pass card-phase work into the system prompt, and the AI's first message should acknowledge Bryan's card work and open with a contextual question.

- [ ] **Step 1: Update stream_study_response to include card work**

In `stream_study_response()`, after loading session data, add:

```python
# Load Bryan's card-phase work
card_responses = db.get_card_responses(session_id)
card_annotations = db.get_card_annotations(session_id)
card_notepad = db.get_card_notepad(session_id, "study_bibles")

# Build card work summary
card_parts = []
for resp in card_responses:
    if resp.get("content"):
        card_parts.append(f"[{resp['phase']}] {resp['content']}")
if card_annotations:
    card_parts.append("\n[Study Bible Stars]")
    for a in card_annotations:
        line = f"  ★ {a['source']}: \"{a['starred_text']}\""
        if a.get("note"):
            line += f" → {a['note']}"
        card_parts.append(line)
if card_notepad:
    card_parts.append(f"\n[Study Bible Notepad]\n{card_notepad}")
card_work_summary = "\n".join(card_parts) if card_parts else ""
```

Pass `card_work_summary` to `build_study_prompt()`.

- [ ] **Step 2: Update the discuss route to handle first conversation message**

The `/study/session/<id>/discuss` route should detect if this is the first conversation message (no prior messages) and if so, prepend context about the card-to-conversation transition.

- [ ] **Step 3: Test the full flow**

1. Create a new study session
2. Complete all 5 card phases (prayer, read, translate, digest, study bibles with stars)
3. Transition to conversation
4. Send first message
5. Verify the AI acknowledges Bryan's card work and asks a contextual question
6. Verify tools work (lexicon, commentary, etc.)

- [ ] **Step 4: Run full test suite**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/ -v --tb=short -q`
Expected: 105+ passed

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/companion_agent.py tools/workbench/app.py
git commit -m "feat: wire card work into conversation phase with 16-step coaching"
```

---

## Task 9: Final integration testing and cleanup

**Files:**
- All modified files
- `tools/workbench/tests/test_study_routes.py`

- [ ] **Step 1: Run full test suite**

Run: `cd /Volumes/External/Logos4/tools/workbench && python3 -m pytest tests/ -v`
Expected: 105+ passed (all original tests + new tests)

- [ ] **Step 2: Test the complete flow manually**

```bash
cd /Volumes/External/Logos4/tools/workbench && python3 app.py
```

Visit `http://localhost:5111/study/` and test:
1. Enter a passage (e.g., "Romans 1:18-23")
2. Phase 1 (Prayer): Write a prayer, click Next
3. Phase 2 (Read): THGNT auto-loads, read it, click Next
4. Phase 3 (Translation): Write translation with THGNT visible, click Next
5. Phase 4 (Digestion): Write digestion notes, click Next
6. Phase 5 (Study Bibles): Tabs show 7 study bibles, star passages, write in notepad, click "Begin Conversation"
7. Conversation opens with AI acknowledging your card work
8. Walk through steps 6-14 with AI coaching
9. Verify outline sidebar works throughout

- [ ] **Step 3: Verify existing companion routes still work**

Visit `http://localhost:5111/companion/` and verify the old card system still functions.

- [ ] **Step 4: Restart PM2**

```bash
pm2 restart sermon-study
```

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: hybrid card→conversation study UI with 16-step sermon prep coaching"
```

---

## Summary

| Task | Description | New Tests |
|------|-------------|-----------|
| 1 | `find_study_bible_notes()` in study.py | 3 |
| 2 | Card annotations DB tables + methods | 1 |
| 3 | Card routes in app.py | 7 |
| 4 | study_session.html + study_card.html templates | — |
| 5 | study.css (dark ADHD-friendly theme) | — |
| 6 | study.js (cards, stars, tabs, conversation) | — |
| 7 | Rewrite `build_study_prompt()` for 16-step workflow | 2 |
| 8 | Wire conversation transition | — |
| 9 | Integration testing + cleanup | — |
| **Total** | | **13 new tests** |

Existing 105 tests must continue passing throughout.
