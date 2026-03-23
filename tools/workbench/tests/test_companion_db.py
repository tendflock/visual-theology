import os, sys, pytest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB

@pytest.fixture
def db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    d = CompanionDB(tmp.name)
    d.init_db()
    yield d
    os.unlink(tmp.name)

def test_create_session(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    s = db.get_session(sid)
    assert s['passage_ref'] == 'Romans 1:18-23'
    assert s['genre'] == 'epistle'
    assert s['current_phase'] == 'prayer'
    assert s['status'] == 'active'
    assert s['timer_remaining_seconds'] == 900

def test_list_active_sessions(db):
    db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    db.create_session('1 Samuel 25:1-13', 9, 25, 1, 13, 'narrative')
    sessions = db.list_sessions(status='active')
    assert len(sessions) == 2

def test_update_phase(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    db.update_phase(sid, 'text_work', 7200)
    s = db.get_session(sid)
    assert s['current_phase'] == 'text_work'
    assert s['timer_remaining_seconds'] == 7200

def test_save_and_get_card_response(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    rid = db.save_card_response(sid, 'text_work', 1, 'The main verb is apokaluptetai')
    responses = db.get_card_responses(sid, 'text_work')
    assert len(responses) == 1
    assert responses[0]['content'] == 'The main verb is apokaluptetai'

def test_outline_tree(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    root = db.add_outline_node(sid, 'title', 'The Wrath of God Revealed')
    mp1 = db.add_outline_node(sid, 'main_point', 'I. God Reveals His Wrath (v.18)', parent_id=root, verse_ref='Rom 1:18')
    sp1 = db.add_outline_node(sid, 'sub_point', 'Present tense — happening now', parent_id=mp1)
    tree = db.get_outline_tree(sid)
    assert len(tree) == 1
    assert tree[0]['content'] == 'The Wrath of God Revealed'
    assert len(tree[0]['children']) == 1
    assert len(tree[0]['children'][0]['children']) == 1

def test_question_bank(db):
    conn = db._conn()
    conn.execute("""
        INSERT INTO question_bank (phase, question_text, guidance_text, genre_tags, priority, rank)
        VALUES ('text_work', 'What is the main verb?', 'Identify tense, voice, mood', '["epistle","narrative"]', 'core', 1)
    """)
    conn.execute("""
        INSERT INTO question_bank (phase, question_text, guidance_text, genre_tags, priority, rank)
        VALUES ('text_work', 'What figurative language is present?', 'Metaphor, simile, etc.', '["poetry"]', 'supplemental', 2)
    """)
    conn.commit()
    conn.close()
    qs = db.get_questions('text_work', genre='epistle')
    assert len(qs) == 1
    assert qs[0]['question_text'] == 'What is the main verb?'
    all_qs = db.get_questions('text_work')
    assert len(all_qs) == 2

def test_delete_outline_node_cascades(db):
    sid = db.create_session('Romans 1:18-23', 66, 1, 18, 23, 'epistle')
    root = db.add_outline_node(sid, 'title', 'Title')
    child = db.add_outline_node(sid, 'main_point', 'Point', parent_id=root)
    db.delete_outline_node(root)
    tree = db.get_outline_tree(sid)
    assert len(tree) == 0

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
