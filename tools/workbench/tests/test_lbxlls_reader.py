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


# Override the session-scoped Flask `base_url` fixture from conftest.py.
# pytest-base-url plugin auto-injects `base_url` into every test's fixture
# graph; without this override these pure-tool tests would pull in the
# conftest fixture and abort with a port-5111 conflict whenever the dev
# server is running.
@pytest.fixture(scope="session")
def base_url():
    return None


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from study import (
    RESOURCES_DIR,
    _resolve_bare_stem,
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


@pytest.mark.parametrize("stem,expected_articles", [
    ("HRMNEIA27DA", 9431),
    ("GS_WALV_DANIEL", 988),
    ("PROGDISPNM", 290),
])
def test_bare_stem_resolves_lbxlls(stem, expected_articles):
    """Bare-stem ``.lbxlls`` resources must resolve via ResourceManager and
    open through the native reader (Fix 12). Case-insensitive lookup matters
    for Walvoord's `LLS:gs_walv_daniel` → `GS_WALV_DANIEL.lbxlls`."""
    resolved = resolve_bible_files([stem])
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) == expected_articles, \
        f"Expected {expected_articles} articles for {stem}, got {len(articles)}"


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


# ── Category 6: Fix 12 cleanup — hardened _resolve_bare_stem ───────────────


def test_find_commentaries_for_daniel_7_excludes_romans_and_leviticus():
    """Broadened LIKE admits rows where 27 appears as a verse number
    (e.g. Romans 66.1.1-66.16.27). ref_covers_passage must filter them out."""
    ref = parse_reference("Daniel 7:1")
    ids = {r["resource_id"] for r in find_commentaries_for_ref(ref, limit=100)}
    for wrong in ("LLS:NICNT66RO", "LLS:EBTC66RO", "LLS:LANGE66RO"):
        assert wrong not in ids, (
            f"{wrong} is not a Daniel commentary but surfaced for Daniel 7:1. "
            f"ref_covers_passage failed to filter the broadened-LIKE over-match."
        )


def test_resolve_bare_stem_empty_raises():
    """Empty stem must raise ValueError, not silently produce '.logos4'."""
    with pytest.raises(ValueError, match="empty stem"):
        _resolve_bare_stem("")


def test_resolve_bare_stem_underscore_is_literal():
    """LIKE ESCAPE must neutralize the underscore in 'GS_WALV_DANIEL'
    so it matches literally, not as a single-character wildcard."""
    assert _resolve_bare_stem("GS_WALV_DANIEL") == "GS_WALV_DANIEL.lbxlls"


def test_resolve_bare_stem_is_case_insensitive():
    """Docstring promises case-insensitive basename match: lowercase stem
    resolves to the on-disk (uppercase) filename."""
    assert _resolve_bare_stem("hrmneia27da") == "HRMNEIA27DA.lbxlls"
    assert _resolve_bare_stem("gs_walv_daniel") == "GS_WALV_DANIEL.lbxlls"


def test_resolve_bare_stem_nonexistent_raises():
    """After F2: an unknown stem must raise FileNotFoundError rather than
    silently fabricating 'stem + ".logos4"'. The caller (resolve_bible_files)
    catches this and falls back, but the helper itself must not hide the failure."""
    with pytest.raises(FileNotFoundError, match="no resource matches stem"):
        _resolve_bare_stem("DEFINITELY_NOT_A_REAL_RESOURCE_ZZZ_9999")
