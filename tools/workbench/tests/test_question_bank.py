import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_db import CompanionDB
from seed_questions import seed_question_bank

def test_seed_populates_all_phases():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)
    conn = db._conn()
    phases = conn.execute("SELECT DISTINCT phase FROM question_bank").fetchall()
    conn.close()
    phase_names = {r['phase'] for r in phases}
    assert 'prayer' in phase_names
    assert 'text_work' in phase_names
    assert 'observation' in phase_names
    assert 'word_study' in phase_names
    assert 'context' in phase_names
    assert 'theological' in phase_names
    assert 'commentary' in phase_names
    assert 'exegetical_point' in phase_names
    assert 'fcf_homiletical' in phase_names
    assert 'sermon_construction' in phase_names
    assert 'edit_pray' in phase_names
    os.unlink(tmp.name)

def test_seed_has_core_questions():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)
    core = db.get_questions('text_work', priority='core')
    assert len(core) >= 3
    os.unlink(tmp.name)

def test_seed_has_genre_tags():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)
    import json
    qs = db.get_questions('observation')
    tagged = [q for q in qs if json.loads(q['genre_tags'])]
    assert len(tagged) > 0
    os.unlink(tmp.name)

def test_seed_is_idempotent():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = CompanionDB(tmp.name)
    db.init_db()
    seed_question_bank(db)
    count1 = len(db.get_questions('text_work'))
    seed_question_bank(db)  # run again
    count2 = len(db.get_questions('text_work'))
    assert count1 == count2
    os.unlink(tmp.name)
