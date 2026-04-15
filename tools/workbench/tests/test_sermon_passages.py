import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from study import parse_reference_multi


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def test_single_passage_returns_single_row():
    result = parse_reference_multi("Romans 8:1-11")
    assert len(result) == 1
    row = result[0]
    assert row['book'] >= 40  # NT Logos numbering
    assert row['chapter_start'] == 8
    assert row['chapter_end'] == 8
    assert row['verse_start'] == 1
    assert row['verse_end'] == 11


def test_multi_range_returns_two_rows_ordered():
    result = parse_reference_multi("Romans 8:1-11; Romans 9:1-5")
    assert len(result) == 2
    assert result[0]['chapter_start'] == 8
    assert result[0]['verse_start'] == 1
    assert result[0]['verse_end'] == 11
    assert result[1]['chapter_start'] == 9
    assert result[1]['verse_start'] == 1
    assert result[1]['verse_end'] == 5


def test_chapter_span_returns_single_row_spanning_chapters():
    result = parse_reference_multi("Psalm 1-2")
    assert len(result) == 1
    row = result[0]
    assert row['chapter_start'] == 1
    assert row['chapter_end'] == 2
    assert row['verse_start'] is None
    assert row['verse_end'] is None


def test_whole_chapter_returns_single_row():
    result = parse_reference_multi("Romans 8")
    assert len(result) == 1
    row = result[0]
    assert row['chapter_start'] == 8
    assert row['chapter_end'] == 8
    assert row['verse_start'] is None
    assert row['verse_end'] is None


def test_unparseable_returns_empty_list():
    assert parse_reference_multi("The Ten Commandments") == []
    assert parse_reference_multi("") == []
    assert parse_reference_multi(None) == []


def test_raw_text_preserved_per_row():
    result = parse_reference_multi("Romans 8:1-11; Romans 9:1-5")
    assert "Romans 8:1-11" in result[0]['raw_text']
    assert "Romans 9:1-5" in result[1]['raw_text']


def test_comma_verse_extra_after_range():
    result = parse_reference_multi("Romans 8:1-11,16")
    assert len(result) == 2
    assert result[0]['verse_start'] == 1
    assert result[0]['verse_end'] == 11
    assert result[1]['verse_start'] == 16
    assert result[1]['verse_end'] == 16


def test_comma_verse_single_then_range():
    result = parse_reference_multi("Romans 8:1,3-5")
    assert len(result) == 2
    assert result[0]['verse_start'] == 1
    assert result[0]['verse_end'] == 1
    assert result[1]['verse_start'] == 3
    assert result[1]['verse_end'] == 5


def test_comma_verse_three_singles():
    result = parse_reference_multi("Romans 8:1,3,5")
    assert len(result) == 3
    assert [r['verse_start'] for r in result] == [1, 3, 5]
    assert [r['verse_end'] for r in result] == [1, 3, 5]
