"""Tests for WS0a-A2: ``article-meta`` reader command + ``get_article_meta``
Python wrapper.

Fixed empirical anchors (verified 2026-04-24 via codex probes — see
``docs/research/2026-04-24-codex-logos-metadata-design.md``):

* RFRMDSYSTH04 article 4718 → nativeSectionId ``R48.2``,
  heading ``A Failed Expectation``, pageStart 1497, pageEnd 1498.
* RFRMDSYSTH04 article 4716 → heading starts with ``Chapter 27``,
  milestone index present, page range non-None.
* HRMNEIA27DA article 1 → no embedded milestone index, pages None.
* COMMREVDURHAM article 1 → no embedded milestone index even though
  it is a ``.logos4`` (page fields None).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from study import get_article_meta  # noqa: E402


# ── RFRMDSYSTH04 — the primary fixture (has milestone index) ───────────────

def test_article_meta_rfrmdsysth04_4718_fields():
    """Article 4718 of Reformed Systematic Theology vol 4:

    * ``nativeSectionId`` = ``R48.2``
    * ``heading`` = ``A Failed Expectation``
    * ``hasMilestoneIndex`` = True
    * ``pageStart`` = 1497, ``pageEnd`` = 1498
    * ``resourceId`` starts with ``LLS:``
    * article offsets are populated and ordered

    All values verified empirically 2026-04-24.
    """
    meta = get_article_meta("RFRMDSYSTH04.logos4", 4718)
    assert meta is not None, "get_article_meta returned None for a known-good input"

    assert meta["logosArticleNum"] == 4718
    assert meta["nativeSectionId"] == "R48.2"
    assert meta["heading"] == "A Failed Expectation"
    assert meta["hasMilestoneIndex"] is True
    assert meta["pageStart"] == 1497
    assert meta["pageEnd"] == 1498
    assert isinstance(meta["resourceId"], str) and meta["resourceId"].startswith("LLS:")
    assert isinstance(meta["articleStart"], int) and meta["articleStart"] > 0
    assert isinstance(meta["articleEnd"], int) and meta["articleEnd"] > meta["articleStart"]


def test_article_meta_rfrmdsysth04_4716_chapter_heading():
    """Article 4716 is the chapter-27 opener; heading should begin with
    ``Chapter 27``, milestone index present, page range populated (any ints)."""
    meta = get_article_meta("RFRMDSYSTH04.logos4", 4716)
    assert meta is not None
    assert meta["logosArticleNum"] == 4716
    assert meta["heading"] is not None
    assert meta["heading"].startswith("Chapter 27"), (
        f"Expected heading to start with 'Chapter 27', got {meta['heading']!r}"
    )
    assert meta["hasMilestoneIndex"] is True
    assert isinstance(meta["pageStart"], int)
    assert isinstance(meta["pageEnd"], int)
    assert meta["pageStart"] <= meta["pageEnd"]


# ── Resources WITHOUT an embedded milestone index — pages must be None ─────

@pytest.mark.parametrize(
    "resource_file,article_num",
    [
        ("HRMNEIA27DA.lbxlls", 1),
        ("COMMREVDURHAM.logos4", 1),
    ],
)
def test_article_meta_no_milestone_index(resource_file, article_num):
    """Both resources lack an embedded ``MilestoneIndexCerodDb.mstidx``
    (verified empirically). ``hasMilestoneIndex`` must be False and both
    page fields must be None. Core fields (resourceId, nativeSectionId)
    still populated."""
    meta = get_article_meta(resource_file, article_num)
    assert meta is not None, f"get_article_meta returned None for {resource_file}"
    assert meta["hasMilestoneIndex"] is False
    assert meta["pageStart"] is None
    assert meta["pageEnd"] is None
    # Still must return core identity fields even without milestone DB
    assert isinstance(meta["resourceId"], str) and meta["resourceId"].startswith("LLS:")
    assert meta["logosArticleNum"] == article_num
    # nativeSectionId should be non-empty for article 1 of both fixtures
    assert meta["nativeSectionId"] is not None and meta["nativeSectionId"] != ""


# ── Shape / contract checks ────────────────────────────────────────────────

def test_article_meta_shape_has_all_expected_keys():
    """The returned dict must have the full documented field set, in any order."""
    meta = get_article_meta("RFRMDSYSTH04.logos4", 4718)
    assert meta is not None
    expected = {
        "resourceId",
        "resourceVersion",
        "logosArticleNum",
        "nativeSectionId",
        "heading",
        "articleStart",
        "articleEnd",
        "hasMilestoneIndex",
        "pageStart",
        "pageEnd",
    }
    assert expected.issubset(set(meta.keys())), (
        f"Missing keys: {expected - set(meta.keys())}"
    )
