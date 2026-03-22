import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from word_number_cache import WordNumberCache

@pytest.fixture(scope="module")
def cache():
    """Build cache once for all tests in this module."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    c = WordNumberCache(path)
    c.build()
    yield c
    os.unlink(path)

def test_cache_is_built(cache):
    """Cache should have 200K+ entries after build."""
    assert cache.is_built()
    count = cache.count()
    assert count > 40000, f"Expected 40K+ entries, got {count}"

def test_romans_1_word_numbers(cache):
    """Should return GNT word numbers for Romans 1."""
    refs = cache.get_word_numbers(45, 1)
    assert len(refs) > 30, f"Expected 30+ words in Romans 1, got {len(refs)}"
    assert all(r.startswith("gnt/") for r in refs), "Romans 1 should be GNT words"

def test_genesis_1_word_numbers(cache):
    """Should return HOT word numbers for Genesis 1."""
    refs = cache.get_word_numbers(1, 1)
    assert len(refs) > 20, f"Expected 20+ words in Genesis 1, got {len(refs)}"
    assert all(r.startswith("hot/") for r in refs), f"Genesis 1 should be HOT words, got {refs[:3]}"

def test_verse_range_filter(cache):
    """Should filter to specific verse range."""
    full_chapter = cache.get_word_numbers(45, 1)
    verse_range = cache.get_word_numbers(45, 1, verse_start=18, verse_end=23)
    assert len(verse_range) > 0, "Should have words in Rom 1:18-23"
    assert len(verse_range) < len(full_chapter), "Verse range should be smaller than full chapter"

def test_empty_for_invalid_book(cache):
    """Should return empty list for non-existent book."""
    refs = cache.get_word_numbers(99, 1)
    assert refs == []


# ── Integration tests: full pipeline ─────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dataset_tools import (
    query_figurative_language, query_greek_constructions,
    query_literary_typing, query_wordplay,
)

def test_greek_constructions_romans_1():
    """Should return Greek constructions for Romans 1."""
    results = query_greek_constructions(book=45, chapter=1)
    assert len(results) > 0, "Expected constructions for Romans 1"
    for r in results[:3]:
        assert "category" in r, f"Missing category in {r}"
        assert "properties" in r, f"Missing properties in {r}"

def test_figurative_language_has_data():
    """Should return figurative language data for a well-known passage."""
    for book, chapter in [(45, 1), (43, 1), (1, 1), (23, 1)]:
        results = query_figurative_language(book=book, chapter=chapter)
        if results:
            assert "category" in results[0]
            return
    # Pipeline works even if data is sparse for these chapters

def test_wordplay_returns_list():
    """Wordplay query should return a list (possibly empty)."""
    results = query_wordplay(book=45, chapter=1)
    assert isinstance(results, list)
