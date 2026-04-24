"""Baseline tests for Fix 12: bare-stem resolution for .lbxlls resources.

These tests capture current behavior before fixing resolve_bible_files so the
fix has a regression harness. Three categories:

  1. Regression: bare-stem `.logos4` resolution still works.
  2. xfail: bare-stem `.lbxlls` resolution is broken (force-appends `.logos4`).
  3. Baseline: full `.lbxlls` paths work through the native loader.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from study import get_resource_articles, resolve_bible_files

RESOURCES_DIR = (
    "/Users/family/Library/Application Support/Logos4/"
    "Data/e3txalek.5iq/ResourceManager/Resources"
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


# ── Category 2: xfail (bug reproduction) ───────────────────────────────────

_XFAIL_REASON = "Fix 12 not yet implemented: bare-stem lookup force-appends .logos4"


@pytest.mark.xfail(reason=_XFAIL_REASON, strict=True)
def test_bare_stem_resolves_lbxlls_hermeneia():
    """HRMNEIA27DA (bare stem) should resolve and open the .lbxlls file."""
    resolved = resolve_bible_files(["HRMNEIA27DA"])
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) == 9431, \
        f"Expected 9431 articles for HRMNEIA27DA, got {len(articles)}"


@pytest.mark.xfail(reason=_XFAIL_REASON, strict=True)
def test_bare_stem_resolves_lbxlls_walvoord():
    """GS_WALV_DANIEL (bare stem) should resolve and open the .lbxlls file."""
    resolved = resolve_bible_files(["GS_WALV_DANIEL"])
    articles = get_resource_articles(resolved[0], timeout=60)
    assert len(articles) == 988, \
        f"Expected 988 articles for GS_WALV_DANIEL, got {len(articles)}"


@pytest.mark.xfail(reason=_XFAIL_REASON, strict=True)
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
