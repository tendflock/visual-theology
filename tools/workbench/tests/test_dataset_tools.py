import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dataset_tools import (
    query_curated_cross_refs, query_theology_xrefs,
    query_preaching_themes, query_biblical_places,
    query_biblical_people, query_dataset_tables,
)


def test_query_dataset_tables():
    """Should list tables in a dataset."""
    tables = query_dataset_tables("FIGURATIVE-LANGUAGE.lbssd", "SupplementalData.db")
    assert len(tables) > 0
    assert "DataTypeReferences" in tables


def test_curated_cross_refs_genesis():
    """Should return cross-references for Genesis 1."""
    results = query_curated_cross_refs(book=1, chapter=1)
    assert len(results) > 0, "Expected cross-references for Genesis 1"
    # Should have score and reference fields
    assert "Score" in results[0]
    assert "Target" in results[0]


def test_curated_cross_refs_romans():
    """Should return cross-references for Romans 1."""
    results = query_curated_cross_refs(book=45, chapter=1)
    assert len(results) > 0, "Expected cross-references for Romans 1"


def test_theology_xrefs_romans():
    """Should return theology cross-references for Romans 1."""
    results = query_theology_xrefs(book=45, chapter=1, xref_type="systematic")
    assert len(results) > 0, "Expected theology xrefs for Romans 1"
    assert "ResourceId" in results[0]
    assert "Tradition" in results[0]


def test_preaching_themes_romans():
    """Should return preaching themes for Romans 1."""
    results = query_preaching_themes(book=45, chapter=1)
    assert len(results) > 0, "Expected preaching themes for Romans 1"
    assert "Theme" in results[0]


def test_biblical_places_acts():
    """Should return places for Acts 1 (mentions Jerusalem, etc.)."""
    results = query_biblical_places(book=44, chapter=1)
    assert len(results) > 0, "Expected places for Acts 1"
    titles = [r.get("Title", "").lower() for r in results]
    assert any("jerusal" in t for t in titles), f"Expected Jerusalem, got {titles}"


def test_biblical_people_genesis():
    """Should return people for Genesis 1."""
    results = query_biblical_people(book=1, chapter=1)
    # Genesis 1 might not have many named people
    assert isinstance(results, list)
