"""Tests for MorphGNT cache — authoritative Greek NT morphology."""

import os
import sys
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from morphgnt_cache import (
    build_db, MorphGNTCache, human_readable_parsing,
    MORPHGNT_DATA_DIR, LOGOS_OFFSET,
)


@pytest.fixture
def cache_db():
    """Build a MorphGNT cache from real data into a temp DB."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.unlink(path)  # build_db creates it fresh
    count = build_db(db_path=path, data_dir=MORPHGNT_DATA_DIR)
    assert count > 100000, f"Expected 100k+ words, got {count}"
    yield path, count
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def cache(cache_db):
    """MorphGNTCache instance on the temp DB."""
    path, _ = cache_db
    c = MorphGNTCache(path)
    yield c
    c.close()


# ── Build / load tests ─────────────────────────────────────────────────

def test_build_loads_all_words(cache_db):
    """Should load ~137k words from 27 NT books."""
    _, count = cache_db
    assert 130000 < count < 150000


def test_db_has_correct_schema(cache_db):
    path, _ = cache_db
    conn = sqlite3.connect(path)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(morphgnt)").fetchall()]
    conn.close()
    assert "book" in cols
    assert "lemma" in cols
    assert "parsing" in cols
    assert "word_num" in cols


def test_books_stored_as_logos_numbers(cache_db):
    """Book numbers should use Logos convention (40-66), not MorphGNT (1-27)."""
    path, _ = cache_db
    conn = sqlite3.connect(path)
    min_book = conn.execute("SELECT MIN(book) FROM morphgnt").fetchone()[0]
    max_book = conn.execute("SELECT MAX(book) FROM morphgnt").fetchone()[0]
    conn.close()
    assert min_book == 40, f"Min book should be 40 (Matthew), got {min_book}"
    assert max_book == 66, f"Max book should be 66 (Revelation), got {max_book}"


# ── Verse lookup ────────────────────────────────────────────────────────

def test_lookup_verse_matthew_1_1(cache):
    """Matthew 1:1 should have 8 words starting with Βίβλος."""
    words = cache.lookup_verse(40, 1, 1)
    assert len(words) == 8
    assert words[0]["lemma"] == "βίβλος"
    assert words[0]["word_num"] == 1
    assert words[2]["lemma"] == "Ἰησοῦς"


def test_lookup_verse_john_3_16(cache):
    """John 3:16 — ἠγάπησεν should parse as Aorist Active Indicative."""
    words = cache.lookup_verse(43, 3, 16)
    assert len(words) > 20
    agapesen = [w for w in words if w["lemma"] == "ἀγαπάω"]
    assert len(agapesen) == 1
    assert "Aorist" in agapesen[0]["parsing_human"]
    assert "Active" in agapesen[0]["parsing_human"]
    assert "Indicative" in agapesen[0]["parsing_human"]


def test_lookup_verse_revelation_last(cache):
    """Revelation 22:21 should exist and have words."""
    words = cache.lookup_verse(66, 22, 21)
    assert len(words) > 0
    lemmas = [w["lemma"] for w in words]
    assert "Ἰησοῦς" in lemmas


def test_lookup_verse_nonexistent(cache):
    """Non-existent verse returns empty list."""
    assert cache.lookup_verse(40, 99, 99) == []


def test_lookup_verse_ot_returns_empty(cache):
    """OT book (Genesis = book 1) returns empty — MorphGNT is NT only."""
    assert cache.lookup_verse(1, 1, 1) == []


# ── Word lookup ─────────────────────────────────────────────────────────

def test_lookup_word_by_surface(cache):
    """Look up ἠγάπησεν in John 3."""
    result = cache.lookup_word("ἠγάπησεν", book=43, chapter=3, verse=16)
    assert result is not None
    assert result["lemma"] == "ἀγαπάω"
    assert "Verb" in result["parsing_human"]


def test_lookup_word_broad_search(cache):
    """Search without book/chapter/verse finds the word anywhere."""
    result = cache.lookup_word("Βίβλος")
    assert result is not None
    assert result["lemma"] == "βίβλος"


def test_lookup_word_strips_punctuation(cache):
    """Words with trailing punctuation should still match."""
    result = cache.lookup_word("Ἀβραάμ.", book=40, chapter=1, verse=1)
    assert result is not None
    assert result["lemma"] == "Ἀβραάμ"


def test_lookup_word_not_found(cache):
    """Non-existent word returns None."""
    assert cache.lookup_word("zzzzzzz") is None


# ── Lemma search ────────────────────────────────────────────────────────

def test_search_lemma_agapao(cache):
    """ἀγαπάω should appear many times across NT."""
    hits = cache.search_lemma("ἀγαπάω")
    assert len(hits) >= 25
    books = set(h["book"] for h in hits)
    assert len(books) > 3, "Should appear in multiple books"


def test_search_lemma_not_found(cache):
    """Non-existent lemma returns empty list."""
    assert cache.search_lemma("zzzzzzz") == []


# ── Human-readable parsing ─────────────────────────────────────────────

def test_parsing_verb():
    result = human_readable_parsing("V-", "3AAI-S--")
    assert "Verb" in result
    assert "Aorist" in result
    assert "Active" in result
    assert "Indicative" in result
    assert "3rd Person" in result
    assert "Singular" in result


def test_parsing_noun():
    result = human_readable_parsing("N-", "----NSF-")
    assert "Noun" in result
    assert "Nominative" in result
    assert "Singular" in result
    assert "Feminine" in result


def test_parsing_article():
    result = human_readable_parsing("RA", "----ASM-")
    assert "Article" in result
    assert "Accusative" in result
    assert "Singular" in result
    assert "Masculine" in result


def test_parsing_participle():
    result = human_readable_parsing("V-", "-PAPNSM-")
    assert "Verb" in result
    assert "Present" in result
    assert "Active" in result
    assert "Participle" in result
    assert "Nominative" in result


def test_parsing_conjunction():
    result = human_readable_parsing("C-", "--------")
    assert result == "Conjunction"


# ── is_nt_book ──────────────────────────────────────────────────────────

def test_is_nt_book(cache):
    assert cache.is_nt_book(40) is True   # Matthew
    assert cache.is_nt_book(66) is True   # Revelation
    assert cache.is_nt_book(39) is False  # Malachi
    assert cache.is_nt_book(1) is False   # Genesis


# ── Word-info endpoint integration ─────────────────────────────────────

def test_word_info_endpoint_nt(cache_db):
    """POST /word-info for an NT session should use MorphGNT."""
    import app as app_module
    from companion_db import CompanionDB
    from seed_questions import seed_question_bank

    db_path, _ = cache_db

    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    cdb = CompanionDB(tmp.name)
    cdb.init_db()
    seed_question_bank(cdb)

    app_module.companion_db = cdb
    app_module.app.config['TESTING'] = True

    # Patch morphgnt_cache to use our temp DB
    import morphgnt_cache
    old_path = morphgnt_cache.MORPHGNT_DB_PATH
    morphgnt_cache.MORPHGNT_DB_PATH = db_path
    morphgnt_cache._cache_instance = None  # reset singleton

    try:
        with app_module.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['authenticated'] = True
            # Create a Romans session (book 45 = NT)
            r = client.post('/study/session/new', data={'passage': 'Romans 1:18'})
            location = r.headers.get('Location', '')
            session_id = int(location.rstrip('/').split('/')[-1])

            # Look up a Greek word
            r = client.post(
                f'/study/session/{session_id}/word-info',
                json={'word': 'ὀργὴ'},
                content_type='application/json',
            )
            assert r.status_code == 200
            data = r.get_json()
            assert data.get("source") == "morphgnt"
            assert data.get("lemma") != ""
            assert data.get("parsing") != ""
    finally:
        morphgnt_cache.MORPHGNT_DB_PATH = old_path
        morphgnt_cache._cache_instance = None
        os.unlink(tmp.name)
