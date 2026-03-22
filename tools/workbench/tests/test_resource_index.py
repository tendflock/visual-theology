import os
import sys
import sqlite3
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from resource_index import ResourceIndex

EDNT_FILE = "EXGDCTNT.logos4"

@pytest.fixture
def index_db():
    """Create a temp DB for the index."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)

def test_build_lexicon_index(index_db):
    """Building an index for EDNT should produce entries with Greek headwords."""
    idx = ResourceIndex(index_db)
    count = idx.build_index_for_resource(EDNT_FILE, resource_type="lexicon")
    assert count > 1000, f"Expected 1000+ entries, got {count}"

    results = idx.lookup("μαται", EDNT_FILE)
    assert len(results) > 0, "Should find entries matching μαται"
    art_ids = [r["article_id"] for r in results]
    assert any("MATAI" in aid.upper() or "MATI" in aid.upper() for aid in art_ids), \
        f"Expected MATAI* article, got {art_ids}"

def test_build_grammar_index(index_db):
    """Building an index for Wallace should map chapter topics to article ranges."""
    idx = ResourceIndex(index_db)
    count = idx.build_index_for_resource("GRKGRAMBBWALLACE.logos4", resource_type="grammar")
    assert count > 20, f"Expected 20+ chapter entries, got {count}"

    results = idx.lookup("voice", "GRKGRAMBBWALLACE.logos4")
    assert len(results) > 0, "Should find voice-related entries"

def test_lookup_nonexistent(index_db):
    """Lookup in empty index returns empty list."""
    idx = ResourceIndex(index_db)
    results = idx.lookup("ματαιόω", "nonexistent.logos4")
    assert results == []

def test_lookup_transliterated(index_db):
    """Should find entries by transliterated form too."""
    idx = ResourceIndex(index_db)
    idx.build_index_for_resource(EDNT_FILE, resource_type="lexicon")
    results = idx.lookup("mataio", EDNT_FILE)
    assert len(results) > 0, "Should find entries by transliterated search"
