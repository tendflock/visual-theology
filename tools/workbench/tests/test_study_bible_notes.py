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


def test_get_article_navindex_refs():
    """Cache should return all navindex refs for a given article."""
    from logos_cache import LogosCache
    cache = LogosCache()
    # ESV SB article 1603 = Romans chapter 1 notes
    refs = cache.get_article_navindex_refs(
        "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources/ESVSB.logos4",
        1603
    )
    assert isinstance(refs, list)
    assert len(refs) > 10  # ESV SB has ~40 refs for Romans 1
    # Should be sorted by offset
    offsets = [r["offset"] for r in refs]
    assert offsets == sorted(offsets)
    # Each entry should have ref_key, article_num, offset
    for r in refs:
        assert "ref_key" in r
        assert "article_num" in r
        assert "offset" in r
        assert r["article_num"] == 1603


def test_parse_verse_from_navref_direct():
    """Parse bible.66.1.24 format."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible.66.1.24", 66, 1)
    assert result == (24, 24)


def test_parse_verse_from_navref_versioned():
    """Parse bible+esv.66.1.24 format (strip version prefix)."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.1.24", 66, 1)
    assert result == (24, 24)


def test_parse_verse_from_navref_range_same_chapter():
    """Parse verse range within same chapter."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.1.26-66.1.27", 66, 1)
    assert result == (26, 27)


def test_parse_verse_from_navref_range_no_version_prefix():
    """Parse bible.66.1.24-66.1.32 (no version prefix, range)."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible.66.1.24-66.1.32", 66, 1)
    assert result == (24, 32)


def test_parse_verse_from_navref_range_cross_chapter():
    """Cross-chapter range: verse_end is None (indeterminate)."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.1.18-66.3.20", 66, 1)
    assert result == (18, None)


def test_parse_verse_from_navref_wrong_chapter():
    """Ref in different chapter returns None."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible+esv.66.2.1", 66, 1)
    assert result is None


def test_parse_verse_from_navref_non_bible():
    """Non-bible refs (page, topic) return None."""
    from study import _parse_verse_from_navref
    assert _parse_verse_from_navref("page.2157", 66, 1) is None
    assert _parse_verse_from_navref("topic.salvation", 66, 1) is None


def test_parse_verse_from_navref_chapter_only():
    """Chapter-only ref like bible.66.1 returns None — no verse info."""
    from study import _parse_verse_from_navref
    result = _parse_verse_from_navref("bible.66.1", 66, 1)
    assert result is None


def test_slice_article_picks_narrowest_section():
    """Should prefer 1:18-32 (narrow) over 1:18-3:20 (broad) as start."""
    from study import _slice_article_by_offsets
    text = "A" * 15000
    refs = [
        {"ref_key": "bible.66.1.1", "offset": 0},
        {"ref_key": "bible.66.1.18-66.3.20", "offset": 8677},
        {"ref_key": "bible.66.1.18-66.1.32", "offset": 8918},
        {"ref_key": "bible.66.1.24", "offset": 11259},
        {"ref_key": "bible.66.1.32", "offset": 13304},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    assert result == text[8918:]


def test_slice_article_end_offset():
    """End offset should be the first ref after verse_end."""
    from study import _slice_article_by_offsets
    text = "A" * 20000
    refs = [
        {"ref_key": "bible.66.1.1", "offset": 0},
        {"ref_key": "bible.66.1.16", "offset": 6000},
        {"ref_key": "bible.66.1.18", "offset": 8000},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 1, 7)
    assert result == text[0:6000].strip()


def test_slice_article_fallback_on_short_result():
    """Should return full text if slicing produces < 100 chars."""
    from study import _slice_article_by_offsets
    text = "Short text but real content here."
    refs = [
        {"ref_key": "bible.66.1.24", "offset": 30},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    assert result == text


def test_slice_article_no_matching_refs():
    """Should return full text if no refs match target chapter."""
    from study import _slice_article_by_offsets
    text = "Full article text here."
    refs = [
        {"ref_key": "page.123", "offset": 0},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    assert result == text


def test_slice_article_sparse_sections():
    """Ancient Faith style: section-level refs only, no exact verse match."""
    from study import _slice_article_by_offsets
    text = "A" * 6000
    refs = [
        {"ref_key": "bible.66.1.1", "offset": 0},
        {"ref_key": "bible.66.1.18-66.1.21", "offset": 3794},
        {"ref_key": "bible.66.1.20", "offset": 4283},
        {"ref_key": "bible.66.1.26-66.1.28", "offset": 4701},
    ]
    result = _slice_article_by_offsets(text, refs, 66, 1, 24, 32)
    assert result == text[4283:].strip()


def test_find_via_navindex_targets_verses():
    """_find_via_navindex should return content for target verses, not chapter start."""
    from study import _find_via_navindex, parse_reference
    ref = parse_reference("Romans 1:24-32")
    esvsb_path = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources/ESVSB.logos4"
    result = _find_via_navindex(esvsb_path, ref)
    assert result is not None
    # Must NOT start with 1:1–17 content (the old bug — full chapter from v1)
    assert not result.startswith("1:1–17"), f"Result starts with chapter beginning: {result[:100]}"
    assert not result.startswith("1:1 "), f"Result starts with verse 1:1: {result[:100]}"
    # Should start with the section header containing our range (1:18)
    assert "1:18" in result[:100], f"Expected section header near start: {result[:100]}"
    # Should be significantly shorter than the full article (~13K chars)
    assert len(result) < 8000, f"Result too long ({len(result)} chars), likely not sliced"
    # Should contain verse 24 content
    assert "1:24" in result, f"Result missing 1:24 content: {result[:200]}"


def test_find_study_bible_notes_targets_passage():
    """Full integration: notes for Romans 1:24-32 should be about those verses."""
    from study import find_study_bible_notes, parse_reference
    ref = parse_reference("Romans 1:24-32")
    results = find_study_bible_notes(ref)
    assert len(results) > 0
    for r in results:
        # Should not start with 1:1 chapter-beginning content
        assert not r["text"].startswith("1:1–17"), \
            f"{r['abbrev']} starts with chapter beginning: {r['text'][:100]}"
        assert not r["text"].startswith("1:1 "), \
            f"{r['abbrev']} starts with verse 1:1: {r['text'][:100]}"
        # Should not be truncated (targeted content is well under 20000)
        assert "[... truncated ...]" not in r["text"], \
            f"{r['abbrev']} was truncated ({len(r['text'])} chars)"
