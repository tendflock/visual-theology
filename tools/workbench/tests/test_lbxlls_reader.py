"""Regression tests for Fix 12: bare-stem resolution for .lbxlls resources.

Five categories, all passing:

  1. Regression: bare-stem `.logos4` resolution still works.
  2. Bare-stem `.lbxlls` resolution (now fixed via ResourceManager lookup).
  3. Baseline: full `.lbxlls` paths work through the native loader.
  4. Broadened commentary superset matching — surfaces resources whose
     ``ReferenceSupersets`` uses a qualified ``bible+bhs.``/``bible+lxx.``
     prefix instead of the bare ``bible.`` one (Fix 12 Task 3).
  5. End-to-end: article text flows through the reader, and
     ``find_commentary_section`` returns a section for Daniel 7:7 in both
     blocked Daniel commentaries (Fix 12 Task 4).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from study import (
    RESOURCES_DIR,
    find_commentaries_for_ref,
    find_commentary_section,
    get_resource_articles,
    parse_reference,
    read_article_text,
    resolve_bible_files,
)


# ── Category 1: regression guard ───────────────────────────────────────────

def test_bare_stem_resolves_logos4_eec27da():
    """EEC27DA (bare stem) must still resolve and open via the current code."""
    resolved = resolve_bible_files(["EEC27DA"])
    assert resolved == ["EEC27DA.logos4"], \
        f"Expected ['EEC27DA.logos4'], got {resolved}"
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) > 0, \
        f"Expected non-empty article list for EEC27DA, got {len(articles)}"


# ── Category 2: bare-stem .lbxlls resolution (Fix 12) ──────────────────────


def test_bare_stem_resolves_lbxlls_hermeneia():
    """HRMNEIA27DA (bare stem) should resolve and open the .lbxlls file."""
    resolved = resolve_bible_files(["HRMNEIA27DA"])
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) == 9431, \
        f"Expected 9431 articles for HRMNEIA27DA, got {len(articles)}"


def test_bare_stem_resolves_lbxlls_walvoord():
    """GS_WALV_DANIEL (bare stem) should resolve and open the .lbxlls file."""
    resolved = resolve_bible_files(["GS_WALV_DANIEL"])
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) == 988, \
        f"Expected 988 articles for GS_WALV_DANIEL, got {len(articles)}"


def test_bare_stem_resolves_lbxlls_progdispnm():
    """PROGDISPNM (bare stem) should resolve and open the .lbxlls file."""
    resolved = resolve_bible_files(["PROGDISPNM"])
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) == 290, \
        f"Expected 290 articles for PROGDISPNM, got {len(articles)}"


# ── Category 3: full .lbxlls path works (native loader baseline) ───────────

@pytest.mark.parametrize("stem,expected_articles", [
    ("HRMNEIA27DA", 9431),
    ("GS_WALV_DANIEL", 988),
    ("PROGDISPNM", 290),
])
def test_full_lbxlls_path_opens(stem, expected_articles):
    """Full `.lbxlls` paths already open correctly via get_resource_articles."""
    path = f"{RESOURCES_DIR}/{stem}.lbxlls"
    assert os.path.exists(path), f"Fixture missing: {path}"
    articles = get_resource_articles(path, timeout=120)
    assert len(articles) == expected_articles, \
        f"Expected {expected_articles} articles for {stem}, got {len(articles)}"


# ── Category 4: broadened commentary superset matching (Fix 12 Task 3) ─────


def test_find_commentaries_for_daniel_7_surfaces_hermeneia():
    """Collins Hermeneia Daniel stores ``bible+bhs.27``; the old ``bible.27%``
    LIKE pattern missed it. The broadened ``bible%.27%`` pattern must surface
    it for Daniel 7:1."""
    ref = parse_reference("Daniel 7:1")
    results = find_commentaries_for_ref(ref, limit=50)
    ids = [r["resource_id"] for r in results]
    assert "LLS:HRMNEIA27DA" in ids, (
        "Collins Hermeneia Daniel (LLS:HRMNEIA27DA, supersets=bible+bhs.27) "
        f"must appear in commentary-discovery results for Daniel 7:1; got {ids}"
    )


def test_find_commentaries_for_daniel_7_regression_eec_and_nac():
    """``.logos4`` Daniel commentaries that matched under the old pattern must
    still match: EEC Da (LLS:EEC27DA, supersets=bible.27.1.1-27.12.13) and
    NAC Da (LLS:29.32.3)."""
    ref = parse_reference("Daniel 7:1")
    results = find_commentaries_for_ref(ref, limit=50)
    ids = [r["resource_id"] for r in results]
    for expected in ("LLS:EEC27DA", "LLS:29.32.3"):
        assert expected in ids, (
            f"Regression: expected {expected} in Daniel 7:1 commentary "
            f"results, got {ids}"
        )


def test_find_commentaries_for_romans_3_regression():
    """Regression guard for NT commentary discovery. NICNT Romans
    (LLS:NICNT66RO, supersets=bible.66.1.1-66.16.27) and EBTC Ro
    (LLS:EBTC66RO) must still surface for Romans 3:10 under the broadened
    LIKE pattern — these are the kinds of ``bible.{book}`` resources the
    fix must not break."""
    ref = parse_reference("Romans 3:10")
    results = find_commentaries_for_ref(ref, limit=100)
    ids = [r["resource_id"] for r in results]
    for expected in ("LLS:NICNT66RO", "LLS:EBTC66RO", "LLS:HODGECM66RO"):
        assert expected in ids, (
            f"Regression: expected {expected} in Romans 3:10 commentary "
            f"results, got {ids}"
        )


# ── Category 5: end-to-end text flow (Fix 12 Task 4) ───────────────────────


# Article 0 across the three resources is short prose content
# (Hermeneia: ~459 chars intro paragraph; Walvoord: ~50-char footnote;
# PROGDISPNM: ~322 chars intro). A 20-char floor proves real text flows
# through the native reader without over-fitting to any one resource.
_MIN_ARTICLE_TEXT = 20


@pytest.mark.parametrize("stem", ["HRMNEIA27DA", "GS_WALV_DANIEL", "PROGDISPNM"])
def test_read_article_text_returns_content(stem):
    """Article 0 of each ``.lbxlls`` resource must return non-empty text.

    This proves the full stack — Python caller → persistent reader subprocess
    → ``libSinaiInterop`` → ``.lbxlls`` container — extracts article text,
    not just article metadata.
    """
    path = resolve_bible_files([stem])[0]
    text = read_article_text(path, 0, max_chars=20000)
    assert text, f"Expected non-empty text for {stem} article 0, got {text!r}"
    assert len(text) >= _MIN_ARTICLE_TEXT, (
        f"Expected ≥{_MIN_ARTICLE_TEXT} chars for {stem} article 0, "
        f"got {len(text)}: {text!r}"
    )


@pytest.mark.parametrize("stem", ["HRMNEIA27DA", "GS_WALV_DANIEL"])
def test_find_commentary_section_daniel_7_7(stem):
    """Collins Hermeneia and Walvoord must locate a Daniel 7:7 section.

    Both are ``text.monograph.commentary.bible`` resources on Daniel. Once
    the ``.lbxlls`` file opens, ``find_commentary_section`` should locate
    and return content covering Daniel 7:7 through one of its lookup paths
    (navindex → verse-index cache → TOC → heuristic scan).
    """
    path = resolve_bible_files([stem])[0]
    ref = parse_reference("Daniel 7:7")
    section = find_commentary_section(path, ref)
    assert section, (
        f"Expected non-empty Daniel 7:7 commentary section for {stem}, "
        f"got {section!r}"
    )


# PROGDISPNM (Blaising & Bock, Progressive Dispensationalism) is
# ``text.monograph`` — a topical monograph, not a commentary. It has no
# per-verse "Daniel 7:7" section to locate. ``find_commentary_section``
# falls back to its heuristic article scan and may surface an unrelated
# prose snippet; that is not a meaningful assertion either way. This case
# is intentionally omitted — it is out of scope for Fix 12 per the plan
# at ``docs/superpowers/plans/2026-04-24-lbxlls-reader.md``.
