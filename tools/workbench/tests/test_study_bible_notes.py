"""Tests for study bible notes lookup."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch, MagicMock


def test_find_study_bible_notes_returns_dict_per_bible():
    """Should return a list of dicts with title, abbrev, and text keys."""
    from study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:1-7")
    results = find_study_bible_notes(ref)
    assert isinstance(results, list)
    for r in results:
        assert "title" in r
        assert "abbrev" in r
        assert "text" in r
        assert isinstance(r["text"], str)


def test_find_study_bible_notes_handles_missing_files():
    """Should skip study bibles whose files don't exist."""
    from study import find_study_bible_notes
    ref = {"book": 66, "book_name": "Romans", "chapter": 1,
           "verse_start": 1, "verse_end": 7, "ref_str": "Romans 1:1-7"}
    results = find_study_bible_notes(ref)
    assert isinstance(results, list)


def test_find_study_bible_notes_truncates_long_text():
    """Should truncate study bible notes longer than max_chars."""
    from study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:1-7")
    results = find_study_bible_notes(ref, max_chars=200)
    for r in results:
        if r["text"]:
            assert len(r["text"]) <= 250  # 200 + allowance for truncation marker
