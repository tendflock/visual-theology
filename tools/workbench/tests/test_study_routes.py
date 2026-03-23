"""
Integration tests for /study/ routes.

Uses Flask's test client — does NOT start the actual server.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from companion_db import CompanionDB
from session_analytics import SessionAnalytics
from seed_questions import seed_question_bank

import pytest


@pytest.fixture
def client():
    """Create Flask test client with temp DBs."""
    import app as app_module

    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    cdb = CompanionDB(tmp.name)
    cdb.init_db()
    seed_question_bank(cdb)

    sa = SessionAnalytics(tmp.name)
    sa.init_db()

    app_module.companion_db = cdb
    app_module.study_analytics = sa
    app_module.app.config['TESTING'] = True

    with app_module.app.test_client() as c:
        yield c

    os.unlink(tmp.name)


def _make_study_session(client, passage='Romans 1:18-23'):
    """Helper: POST /study/session/new and return (session_id, location)."""
    r = client.post('/study/session/new', data={'passage': passage})
    location = r.headers.get('Location', '')
    session_id = None
    if '/study/session/' in location:
        parts = location.rstrip('/').split('/')
        try:
            session_id = int(parts[-1])
        except ValueError:
            pass
    return session_id, location


# ── Index ────────────────────────────────────────────────────────────────

def test_study_index(client):
    r = client.get('/study/')
    assert r.status_code == 200
    assert b'Sermon Study' in r.data


# ── Session creation ─────────────────────────────────────────────────────

def test_create_study_session(client):
    r = client.post('/study/session/new', data={'passage': 'Romans 1:18-23'})
    assert r.status_code == 302
    assert '/study/session/' in r.headers['Location']


def test_create_study_session_valid_id(client):
    session_id, location = _make_study_session(client)
    assert session_id is not None


def test_create_study_session_empty_passage(client):
    r = client.post('/study/session/new', data={'passage': ''})
    assert r.status_code == 302
    assert 'error' in r.headers.get('Location', '')


def test_create_study_session_invalid_passage(client):
    r = client.post('/study/session/new', data={'passage': 'Not A Passage 999'})
    assert r.status_code == 302
    assert 'error' in r.headers.get('Location', '')


# ── Session view ─────────────────────────────────────────────────────────

def test_study_session_view(client):
    session_id, _ = _make_study_session(client)
    r = client.get(f'/study/session/{session_id}')
    assert r.status_code == 200
    assert b'Romans 1:18-23' in r.data


def test_study_session_not_found(client):
    r = client.get('/study/session/99999')
    assert r.status_code == 302
    assert '/study/' in r.headers['Location']


# ── Discuss ──────────────────────────────────────────────────────────────

def test_study_discuss_no_message(client):
    session_id, _ = _make_study_session(client)
    r = client.post(
        f'/study/session/{session_id}/discuss',
        json={},
        content_type='application/json',
    )
    assert r.status_code == 400


def test_study_discuss_returns_sse(client):
    session_id, _ = _make_study_session(client)
    r = client.post(
        f'/study/session/{session_id}/discuss',
        json={'message': 'What is the main verb?'},
        content_type='application/json',
    )
    assert r.status_code == 200
    assert r.content_type.startswith('text/event-stream')


# ── Outline ──────────────────────────────────────────────────────────────

def test_study_outline_empty(client):
    session_id, _ = _make_study_session(client)
    r = client.get(f'/study/session/{session_id}/outline')
    assert r.status_code == 200
    data = r.get_json()
    assert data == []


def test_study_outline_add(client):
    session_id, _ = _make_study_session(client)
    r = client.post(
        f'/study/session/{session_id}/outline/add',
        json={'content': 'God reveals wrath', 'node_type': 'main_point'},
        content_type='application/json',
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok'] is True
    assert 'id' in data


def test_study_outline_add_empty(client):
    session_id, _ = _make_study_session(client)
    r = client.post(
        f'/study/session/{session_id}/outline/add',
        json={'content': '', 'node_type': 'note'},
        content_type='application/json',
    )
    assert r.status_code == 400


def test_study_outline_update(client):
    session_id, _ = _make_study_session(client)
    # Add first
    r = client.post(
        f'/study/session/{session_id}/outline/add',
        json={'content': 'Original', 'node_type': 'note'},
        content_type='application/json',
    )
    node_id = r.get_json()['id']

    # Update
    r = client.patch(
        f'/study/session/{session_id}/outline/{node_id}',
        json={'content': 'Updated'},
        content_type='application/json',
    )
    assert r.status_code == 200


def test_study_outline_delete(client):
    session_id, _ = _make_study_session(client)
    r = client.post(
        f'/study/session/{session_id}/outline/add',
        json={'content': 'To delete', 'node_type': 'note'},
        content_type='application/json',
    )
    node_id = r.get_json()['id']

    r = client.delete(f'/study/session/{session_id}/outline/{node_id}')
    assert r.status_code == 200

    # Verify gone
    r = client.get(f'/study/session/{session_id}/outline')
    assert r.get_json() == []


# ── Clock ────────────────────────────────────────────────────────────────

def test_study_clock_update(client):
    session_id, _ = _make_study_session(client)
    r = client.patch(
        f'/study/session/{session_id}/clock',
        json={'elapsed': 3600},
        content_type='application/json',
    )
    assert r.status_code == 200
    assert r.get_json()['ok'] is True


# ── Companion routes still work ──────────────────────────────────────────

# ── Card Navigation ─────────────────────────────────────────────────────

def test_study_session_shows_card_phase(client):
    """GET /study/session/<id> should show card UI for phases 1-5."""
    sid, _ = _make_study_session(client)
    resp = client.get(f"/study/session/{sid}")
    assert resp.status_code == 200
    assert b"study-card" in resp.data or b"card" in resp.data


def test_study_card_next(client):
    """POST card/next should redirect back to session."""
    sid, _ = _make_study_session(client)
    resp = client.post(f"/study/session/{sid}/card/next",
                       data={"response": "My prayer for this study"},
                       follow_redirects=True)
    assert resp.status_code == 200


def test_study_card_back(client):
    """POST card/back should go to previous phase."""
    sid, _ = _make_study_session(client)
    client.post(f"/study/session/{sid}/card/next",
                data={"response": "prayer"}, follow_redirects=True)
    resp = client.post(f"/study/session/{sid}/card/back", follow_redirects=True)
    assert resp.status_code == 200


def test_study_session_transition_to_conversation(client):
    """After completing all 5 card phases, session should show conversation UI."""
    sid, _ = _make_study_session(client)
    for i in range(5):
        client.post(f"/study/session/{sid}/card/next",
                    data={"response": f"response {i}"}, follow_redirects=True)
    resp = client.get(f"/study/session/{sid}")
    assert resp.status_code == 200
    assert b"conversation" in resp.data


def test_study_bible_notes_route(client):
    """GET study-bibles should return JSON."""
    sid, _ = _make_study_session(client)
    resp = client.get(f"/study/session/{sid}/study-bibles")
    assert resp.status_code == 200


def test_study_annotation_save(client):
    """POST annotate should save a star annotation."""
    sid, _ = _make_study_session(client)
    resp = client.post(f"/study/session/{sid}/annotate",
                       json={"source": "ESV SB", "starred_text": "test", "note": "important"})
    assert resp.status_code == 200


def test_study_notepad_save(client):
    """POST notepad should save notepad content."""
    sid, _ = _make_study_session(client)
    resp = client.post(f"/study/session/{sid}/notepad",
                       json={"phase": "study_bibles", "content": "My observations"})
    assert resp.status_code == 200


# ── Companion routes still work ──────────────────────────────────────────

def test_companion_index_still_works(client):
    r = client.get('/companion/')
    assert r.status_code == 200
    assert b'Sermon Study Companion' in r.data


def test_companion_session_still_works(client):
    r = client.post('/companion/session/new', data={'passage': 'Romans 1:18-23'})
    assert r.status_code == 302
    assert '/companion/session/' in r.headers['Location']
