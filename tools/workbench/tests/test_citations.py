"""Tests for tools/citations.py (WS0c — dual-citation builder + verifier).

These tests require the Logos native library and at least the following
resources to be present in ``study.RESOURCES_DIR``:

- ``RFRMDSYSTH04.logos4`` (Beeke & Smalley RST 4, has embedded milestone DB)
- ``PCLYPTCMGNTNPLT.logos4`` (Collins, Apocalyptic Imagination)
- ``OTL27DA.logos4`` (Newsom & Breed, OTL Daniel)
- ``HRMNEIA27DA.lbxlls`` (Collins, Hermeneia Daniel; no milestone DB)
"""

import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import citations  # noqa: E402
from citations import (  # noqa: E402
    SUPPORT_STATUS_VALUES,
    _resource_id_to_file,
    build_citation,
    sha256_of,
    verify_citation,
)


# Override the session-scoped Flask `base_url` fixture from conftest.py.
# The pytest-base-url plugin auto-injects `base_url` into every test's
# fixture graph; without this override these pure-tool tests would
# pull in the conftest fixture and abort with a port-5111 conflict.
@pytest.fixture(scope="session")
def base_url():  # noqa: D401  (intentionally short)
    return None


# ── sha256 ──────────────────────────────────────────────────────────────────


def test_sha256_of_matches_hashlib():
    text = "The Son of Man came with the clouds of heaven."
    assert sha256_of(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_sha256_of_is_lowercase_hex_64_chars():
    digest = sha256_of("anything")
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


# ── build_citation ──────────────────────────────────────────────────────────


def test_build_citation_rst4_r48_2_has_pages():
    """RFRMDSYSTH04 article 4718 = §R48.2, spans pp. 1497-1498."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="A Failed Expectation",
        author="Beeke & Smalley",
        short_title="RST 4",
        full_title="Reformed Systematic Theology, Vol. 4: Church and Last Things",
    )

    assert c["backend"]["resourceId"] == "LLS:RFRMDSYSTH04"
    assert c["backend"]["logosArticleNum"] == 4718
    assert c["backend"]["nativeSectionId"] == "R48.2"

    assert c["frontend"]["author"] == "Beeke & Smalley"
    assert c["frontend"]["section"] == "§R48.2 — A Failed Expectation"
    assert c["frontend"]["page"] == 1497
    assert c["frontend"]["pageEnd"] == 1498
    assert "RST 4" in c["frontend"]["citationString"]
    assert "R48.2" in c["frontend"]["citationString"]
    assert "1497" in c["frontend"]["citationString"]
    assert "1498" in c["frontend"]["citationString"]

    assert c["quote"]["text"] == "A Failed Expectation"
    assert c["quote"]["sha256"] == sha256_of("A Failed Expectation")


def test_build_citation_hermeneia_no_pages():
    """HRMNEIA27DA.lbxlls has no milestone index; page fields must be null."""
    c = build_citation(
        resource_file="HRMNEIA27DA.lbxlls",
        article_num=1,
        quote_text=None,  # paraphrase, no direct quote
        author="Collins",
        short_title="Hermeneia Daniel",
    )

    assert c["backend"]["resourceId"] == "LLS:HRMNEIA27DA"
    assert c["backend"]["nativeSectionId"]  # some ID present
    assert c["frontend"]["page"] is None
    assert c["frontend"]["pageEnd"] is None
    assert c["quote"] is None
    # citationString must not claim a page when none exists
    assert "p." not in c["frontend"]["citationString"]


def test_build_citation_multi_page_range_renders_pp():
    """Articles spanning multiple printed pages get pageStart != pageEnd and
    a 'pp. N–M' rendering in citationString. RFRMDSYSTH04 article 4718
    spans pp. 1497–1498."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text=None,
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    assert c["frontend"]["page"] == 1497
    assert c["frontend"]["pageEnd"] == 1498
    assert "pp. 1497–1498" in c["frontend"]["citationString"]


# ── verify_citation ─────────────────────────────────────────────────────────


def test_verify_citation_happy_path_collins_apocalyptic():
    """Known-good: Collins Apocalyptic Imagination art 1323 contains the quote."""
    quote = (
        "the second-century date for the visions of Daniel (chaps. 7–12) "
        "is accepted as beyond reasonable doubt by critical scholarship."
    )
    c = build_citation(
        resource_file="PCLYPTCMGNTNPLT.logos4",
        article_num=1323,
        quote_text=quote,
        author="Collins",
        short_title="Apocalyptic Imagination",
    )
    v = verify_citation(c)
    assert v["status"] == "verified", v


def test_verify_citation_long_article_no_truncation():
    """Newsom art. 488 is 46K chars; the target quote appears past the 20K
    default truncation. Verifier must read the full article."""
    quote = (
        "reinterpret this figure with increasing specificity, "
        "as prince of the host (8:11) and as Michael"
    )
    c = build_citation(
        resource_file="OTL27DA.logos4",
        article_num=488,
        quote_text=quote,
        author="Newsom",
        short_title="OTL Daniel",
    )
    v = verify_citation(c)
    assert v["status"] == "verified", v


def test_verify_citation_quote_not_found():
    """A deliberately fabricated quote returns quote-not-found."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="The authors categorically deny any form of eschatology whatsoever.",
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    v = verify_citation(c)
    assert v["status"] == "quote-not-found", v


def test_verify_citation_whitespace_normalization():
    """Verifier normalizes whitespace — a quote with extra spaces still matches."""
    quote = "A     Failed     Expectation"
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text=quote,
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    v = verify_citation(c)
    assert v["status"] == "verified", v


def test_verify_citation_paraphrase_only_ok():
    """A citation without a quote (pure paraphrase anchor) verifies if the
    article exists and is readable."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text=None,
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    v = verify_citation(c)
    assert v["status"] == "verified", v
    assert v.get("notes", "").startswith("paraphrase") or v.get("paraphrase") is True


def test_support_status_default_directly_quoted_when_quote_present():
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="A Failed Expectation",
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    assert c["supportStatus"] == "directly-quoted"


def test_support_status_default_uncited_gap_when_no_quote():
    c = build_citation(
        resource_file="HRMNEIA27DA.lbxlls",
        article_num=1,
        quote_text=None,
        author="Collins",
        short_title="Hermeneia Daniel",
    )
    assert c["supportStatus"] == "uncited-gap"


def test_support_status_explicit_paraphrase_anchored():
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text=None,
        author="Beeke & Smalley",
        short_title="RST 4",
        support_status="paraphrase-anchored",
    )
    assert c["supportStatus"] == "paraphrase-anchored"
    assert c["quote"] is None


def test_support_status_directly_quoted_without_quote_raises():
    with pytest.raises(ValueError, match="directly-quoted"):
        build_citation(
            resource_file="RFRMDSYSTH04.logos4",
            article_num=4718,
            quote_text=None,
            author="Beeke & Smalley",
            short_title="RST 4",
            support_status="directly-quoted",
        )


def test_support_status_invalid_value_raises():
    with pytest.raises(ValueError, match="support_status"):
        build_citation(
            resource_file="RFRMDSYSTH04.logos4",
            article_num=4718,
            quote_text="A Failed Expectation",
            author="Beeke & Smalley",
            short_title="RST 4",
            support_status="totally-made-up",
        )


def test_verify_citation_json_roundtrip():
    """A built citation must survive JSON round-trip without field loss."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="A Failed Expectation",
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    raw = json.dumps(c)
    round = json.loads(raw)
    v = verify_citation(round)
    assert v["status"] == "verified"


# ── _resource_id_to_file (resolution-order regression) ─────────────────────


def test_resource_id_to_file_dotted_catalog_id_resolves_via_resourcemanager():
    """LLS:6.60.2 → NPNF02.logos4 (dotted catalog ID; filename ≠ stem).

    Regression: prior implementation only did basename-LIKE match against the
    stem and could not resolve dotted catalog IDs whose filename was decoupled
    (e.g. LLS:6.60.2 lives at .../Resources/NPNF02.logos4 per RM.Resources).
    The fix routes through get_resource_file() which queries
    Resources.ResourceId directly.
    """
    assert _resource_id_to_file("LLS:6.60.2") == "NPNF02.logos4"


def test_resource_id_to_file_alphabetic_stem_still_works():
    """LLS:GS_WALV_DANIEL → GS_WALV_DANIEL.lbxlls (filename equals stem).

    Existing alphabetic-stem behavior must continue to work whether
    get_resource_file() resolves it directly or it falls through to
    _resolve_bare_stem.
    """
    assert _resource_id_to_file("LLS:GS_WALV_DANIEL") == "GS_WALV_DANIEL.lbxlls"


def test_resource_id_to_file_unknown_stem_raises():
    """Unknown stems must raise FileNotFoundError, not silently fabricate.

    Both the catalog and the filesystem fallback must miss before raising.
    """
    with pytest.raises(FileNotFoundError):
        _resource_id_to_file("LLS:NONEXISTENT_STEM_XYZ_2026")


# ── external-sefaria backend (WS0c-expansion) ──────────────────────────────


_RASHI_DAN_7_13_URL = "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13"
_IBN_EZRA_DAN_7_13_URL = "https://www.sefaria.org/api/texts/Ibn_Ezra_on_Daniel.7.13"

# Representative shape from the Sefaria text API. Hebrew + English arrays,
# inline <b> tags around lemmata, NFC-mixed Hebrew. Real fixture content for
# Rashi on Daniel 7:13 (verified against the live API 2026-04-28).
_RASHI_DAN_7_13_FIXTURE = {
    "ref": "Rashi on Daniel 7:13",
    "heRef": "רש\"י על דניאל ז׳:י״ג",
    "book": "Rashi on Daniel",
    "sections": [7, 13],
    "text": [
        "<b>one like a man was coming</b> That is the King Messiah.",
        "<b>and… up to the Ancient of Days</b> Who was sitting in judgment.",
    ],
    "he": [
        "<b>כְּבַר אֱנָשׁ אָתֵה.</b> הוּא מֶלֶךְ הַמָּשִׁיחַ:",
        "<b>וְעַד עַתִּיק יוֹמַיָּא.</b> שֶׁהָיָה יוֹשֵׁב בַּדִּין:",
    ],
    "commentator": "Rashi",
}

_IBN_EZRA_HE_FIXTURE = (
    "חזה - רואה הייתי במראות הלילה והנה עם ענני השמים "
    "כבן אנוש היה בא, ועד קדמון ימים הגיע ולפניו הקריבוהו."
)
_IBN_EZRA_FIXTURE = {
    "ref": "Ibn Ezra on Daniel 7:13",
    "book": "Ibn Ezra on Daniel",
    "sections": [7, 13],
    "text": [],  # Sefaria has no English for Ibn Ezra
    "he": [_IBN_EZRA_HE_FIXTURE],
    "commentator": "Ibn Ezra",
}


@pytest.fixture
def isolated_sefaria_cache(tmp_path, monkeypatch):
    """Point the Sefaria cache dir at a tmp dir so tests don't pollute the
    repo's external-resources/ tree, and don't see leftover state from prior
    runs."""
    monkeypatch.setattr(citations, "SEFARIA_CACHE_DIR", tmp_path / "sefaria-cache")
    return tmp_path / "sefaria-cache"


def _build_sefaria_citation(
    *,
    url=_RASHI_DAN_7_13_URL,
    language="en",
    quote_text="That is the King Messiah.",
    verse_ref="Daniel 7:13",
    commentator="Rashi",
):
    """Hand-build an external-sefaria citation. ``build_citation`` is for
    Logos backends; sefaria citations are constructed directly per schema."""
    citation = {
        "backend": {
            "kind": "external-sefaria",
            "resourceUrl": url,
            "language": language,
            "verseRef": verse_ref,
            "commentator": commentator,
        },
        "frontend": {
            "author": commentator,
            "title": f"{commentator} on Daniel",
            "section": verse_ref,
            "page": None,
            "pageEnd": None,
            "citationString": f"{commentator}, {verse_ref}",
        },
        "quote": (
            None
            if quote_text is None
            else {"text": quote_text, "sha256": sha256_of(quote_text)}
        ),
        "supportStatus": "directly-quoted" if quote_text else "paraphrase-anchored",
    }
    return citation


def test_sefaria_round_trip_rashi_daniel_7_13_english(
    isolated_sefaria_cache, monkeypatch
):
    calls = {"n": 0}

    def fake_fetch(url):
        calls["n"] += 1
        assert url == _RASHI_DAN_7_13_URL
        return _RASHI_DAN_7_13_FIXTURE

    monkeypatch.setattr(citations, "_fetch_sefaria_uncached", fake_fetch)

    citation = _build_sefaria_citation(
        language="en", quote_text="That is the King Messiah."
    )
    v = verify_citation(citation)
    assert v["status"] == "verified", v
    assert calls["n"] == 1


def test_sefaria_round_trip_rashi_daniel_7_13_hebrew(
    isolated_sefaria_cache, monkeypatch
):
    monkeypatch.setattr(
        citations, "_fetch_sefaria_uncached", lambda url: _RASHI_DAN_7_13_FIXTURE
    )

    citation = _build_sefaria_citation(
        language="he", quote_text="הוּא מֶלֶךְ הַמָּשִׁיחַ"
    )
    v = verify_citation(citation)
    assert v["status"] == "verified", v


def test_sefaria_quote_not_found(isolated_sefaria_cache, monkeypatch):
    """A fabricated quote that isn't in Sefaria's text returns quote-not-found."""
    monkeypatch.setattr(
        citations, "_fetch_sefaria_uncached", lambda url: _RASHI_DAN_7_13_FIXTURE
    )

    citation = _build_sefaria_citation(
        language="en",
        quote_text="Rashi categorically denies any messianic reading whatsoever.",
    )
    v = verify_citation(citation)
    assert v["status"] == "quote-not-found", v


def test_sefaria_html_tags_stripped(isolated_sefaria_cache, monkeypatch):
    """Citation quote is the plain text; Sefaria response wraps lemmata in <b>.
    Verifier must strip tags so the quote matches the cleaned text."""
    monkeypatch.setattr(
        citations, "_fetch_sefaria_uncached", lambda url: _RASHI_DAN_7_13_FIXTURE
    )

    citation = _build_sefaria_citation(
        language="en", quote_text="one like a man was coming"
    )
    v = verify_citation(citation)
    assert v["status"] == "verified", v


def test_sefaria_nfc_normalization_round_trip(isolated_sefaria_cache, monkeypatch):
    """Hebrew differs between NFC (composed) and NFD (decomposed) — both must
    verify against the same source. Force the response into NFD and the
    citation into NFC; verifier should still match."""
    import unicodedata

    nfd_fixture = dict(_IBN_EZRA_FIXTURE)
    nfd_fixture["he"] = [unicodedata.normalize("NFD", _IBN_EZRA_HE_FIXTURE)]
    monkeypatch.setattr(
        citations, "_fetch_sefaria_uncached", lambda url: nfd_fixture
    )

    nfc_quote = unicodedata.normalize(
        "NFC",
        "רואה הייתי במראות הלילה",
    )
    citation = _build_sefaria_citation(
        url=_IBN_EZRA_DAN_7_13_URL,
        language="he",
        quote_text=nfc_quote,
        commentator="Ibn Ezra",
    )
    v = verify_citation(citation)
    assert v["status"] == "verified", v


def test_sefaria_cache_hit_skips_network(isolated_sefaria_cache, monkeypatch):
    """Second verify on the same URL must not re-fetch — the disk cache
    short-circuits the network call."""
    calls = {"n": 0}

    def fake_fetch(url):
        calls["n"] += 1
        return _RASHI_DAN_7_13_FIXTURE

    monkeypatch.setattr(citations, "_fetch_sefaria_uncached", fake_fetch)

    citation = _build_sefaria_citation(
        language="en", quote_text="That is the King Messiah."
    )
    v1 = verify_citation(citation)
    v2 = verify_citation(citation)
    assert v1["status"] == "verified"
    assert v2["status"] == "verified"
    assert calls["n"] == 1, "second verify should hit cache, not network"
    # Cache file should exist on disk
    assert (
        isolated_sefaria_cache / "Rashi_on_Daniel.7.13.json"
    ).exists()


def test_sefaria_empty_text_for_requested_language(
    isolated_sefaria_cache, monkeypatch
):
    """Ibn Ezra has no English on Sefaria. Citing it as English must surface
    the empty-text condition rather than silently verifying against Hebrew."""
    monkeypatch.setattr(
        citations, "_fetch_sefaria_uncached", lambda url: _IBN_EZRA_FIXTURE
    )

    citation = _build_sefaria_citation(
        url=_IBN_EZRA_DAN_7_13_URL,
        language="en",
        quote_text="anything",
        commentator="Ibn Ezra",
    )
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v
    assert "no text" in v["notes"].lower() or "empty" in v["notes"].lower()


def test_sefaria_rejects_non_sefaria_url(isolated_sefaria_cache):
    citation = _build_sefaria_citation(
        url="https://example.com/api/texts/Rashi_on_Daniel.7.13",
        language="en",
        quote_text="anything",
    )
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v


def test_sefaria_rejects_non_https_url(isolated_sefaria_cache):
    citation = _build_sefaria_citation(
        url="http://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13",
        language="en",
        quote_text="anything",
    )
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v


def test_sefaria_rejects_path_traversal(isolated_sefaria_cache):
    citation = _build_sefaria_citation(
        url="https://www.sefaria.org/api/texts/../etc/passwd",
        language="en",
        quote_text="anything",
    )
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v


def test_sefaria_invalid_language_rejected(isolated_sefaria_cache):
    citation = _build_sefaria_citation(language="fr", quote_text="anything")
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v
    assert "language" in v["notes"]


def test_sefaria_missing_resource_url(isolated_sefaria_cache):
    citation = _build_sefaria_citation(quote_text="anything")
    del citation["backend"]["resourceUrl"]
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v


# ── URL hardening: cache-key safety + validator/runtime parity (Session C-2) ──
#
# Two failure modes the original validation missed:
#   1. Cache-key poisoning. The on-disk cache is keyed by the URL's path
#      component, so query/fragment/params would silently collide with the
#      bare-path entry while fetching a different payload.
#   2. Validator/runtime drift. validate_scholar.py used to do startswith()
#      while the runtime did urlparse() — bad URLs landed in the corpus and
#      only failed at sweep time.
#
# These tests cover both: the runtime rejects each bad URL, the validator
# rejects the same bad URL, and the parametrized test pins the two paths
# in lockstep.

_MALFORMED_SEFARIA_URLS = [
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13?commentary=0",
        "query string",
        id="query-string",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13#section-1",
        "fragment",
        id="fragment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13;param=val",
        "path params",
        id="rfc3986-params",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/../etc/passwd",
        "single path segment",
        id="path-traversal",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts//extra",
        "single path segment",
        id="empty-segment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13/extra",
        "single path segment",
        id="trailing-extra",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/..",
        "reserved",
        id="bare-double-dot",
    ),
    # C-3 hardening: userinfo, explicit ports, percent-encoding, whitespace.
    pytest.param(
        "https://user:pass@www.sefaria.org/api/texts/Rashi_on_Daniel.7.13",
        "userinfo",
        id="userinfo",
    ),
    pytest.param(
        "https://www.sefaria.org:443/api/texts/Rashi_on_Daniel.7.13",
        "explicit port",
        id="port-canonical-443",
    ),
    pytest.param(
        "https://www.sefaria.org:999/api/texts/Rashi_on_Daniel.7.13",
        "explicit port",
        id="port-non-canonical",
    ),
    pytest.param(
        "https://www.sefaria.org:abc/api/texts/Rashi_on_Daniel.7.13",
        "explicit port",
        id="port-non-integer",
    ),
    pytest.param(
        "https://www.sefaria.org:/api/texts/Rashi_on_Daniel.7.13",
        "explicit port",
        id="port-empty",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13%2Fextra",
        "percent-encoded",
        id="percent-encoded-slash",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/%2E%2E",
        "percent-encoded",
        id="percent-encoded-dotdot",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13%252Fextra",
        "percent-encoded",
        id="double-encoded-slash",
    ),
    pytest.param(
        "\nhttps://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13",
        "whitespace",
        id="leading-newline",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13\t",
        "whitespace",
        id="trailing-tab",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13 ",
        "whitespace",
        id="trailing-space",
    ),
    # C-4 hardening: ref-segment positive allowlist + empty-userinfo regression.
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13\\extra",
        "disallowed",
        id="backslash-in-segment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi on Daniel.7.13",
        "disallowed",
        id="space-in-segment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13‍",
        "disallowed",
        id="zwj-in-segment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13‮",
        "disallowed",
        id="rlo-in-segment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13 inner",
        "disallowed",
        id="nbsp-in-segment",
    ),
    pytest.param(
        "https://www.sefaria.org/api/texts/Rashí_on_Daniel.7.13",
        "disallowed",
        id="non-ascii-letter-in-segment",
    ),
    pytest.param(
        "https://@www.sefaria.org/api/texts/Rashi_on_Daniel.7.13",
        "userinfo",
        id="empty-userinfo",
    ),
]


@pytest.mark.parametrize("bad_url, expected_phrase", _MALFORMED_SEFARIA_URLS)
def test_runtime_rejects_malformed_sefaria_url(
    isolated_sefaria_cache, monkeypatch, bad_url, expected_phrase
):
    """Each bad URL aborts the runtime BEFORE any network fetch happens."""
    fetched: list[str] = []

    def trip(url):  # pragma: no cover — must never run for these inputs
        fetched.append(url)
        raise AssertionError(f"runtime fetched a malformed URL: {url!r}")

    monkeypatch.setattr(citations, "_fetch_sefaria_uncached", trip)

    citation = _build_sefaria_citation(url=bad_url, quote_text="anything")
    v = verify_citation(citation)

    assert v["status"] == "resource-unreadable", v
    assert expected_phrase in v["notes"], v
    assert fetched == [], "URL validation must run before the network call"


@pytest.mark.parametrize("bad_url, expected_phrase", _MALFORMED_SEFARIA_URLS)
def test_validator_rejects_malformed_sefaria_url(bad_url, expected_phrase):
    """validate_scholar.py rejects the SAME URLs the runtime rejects.

    Pre-hardening, the validator did startswith(...) and accepted these,
    leaving runtime as the only line of defense.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
    from validate_scholar import ValidationError, validate_scholar

    doc = {
        "scholarId": "rashi-daniel",
        "authorDisplay": "Rashi",
        "workDisplay": "Rashi on Daniel",
        "resourceId": "sefaria:Rashi_on_Daniel",
        "resourceFile": "Rashi_on_Daniel.sefaria",
        "traditionTag": "medieval-jewish",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "Son of Man",
                "position": "Messianic",
                "commitment": "strong",
                "rationale": "x",
                "citations": [
                    {
                        "backend": {
                            "kind": "external-sefaria",
                            "resourceUrl": bad_url,
                            "language": "en",
                            "verseRef": "Daniel 7:13",
                        },
                        "frontend": {
                            "author": "Rashi",
                            "title": "Rashi on Daniel",
                            "section": "Daniel 7:13",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Rashi, Daniel 7:13",
                        },
                        "quote": {
                            "text": "x",
                            "sha256": sha256_of("x"),
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_scholar(doc)
    # The validator wraps the inner ValueError as
    # "<path>.backend.resourceUrl: <inner-message>". The inner message must
    # carry the specific reason — pin it here so a regression to a generic
    # "resourceUrl invalid" gets caught.
    msg = str(exc_info.value)
    assert "resourceUrl" in msg, msg
    assert expected_phrase in msg, msg


def test_query_string_would_have_poisoned_the_cache(isolated_sefaria_cache):
    """Direct unit check: the cache path strips query/fragment, so without
    URL validation two distinct fetches would map to the same cache file.
    This pins the cache key behavior that motivates the URL rejection."""
    bare = "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13"
    poisoned = bare + "?commentary=0"
    # Sanity: same on-disk path = collision risk (the very thing validation prevents).
    assert citations._sefaria_cache_path(bare) == citations._sefaria_cache_path(poisoned)
    # ...and the validator now refuses to let a poisoned URL be cached at all.
    with pytest.raises(ValueError, match="query string"):
        citations.validate_sefaria_url(poisoned)


def test_validate_sefaria_url_accepts_canonical_urls():
    """Regression guard: hardening must not break the canonical URLs the
    Wave 6 surveys actually use."""
    for good in (
        "https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13",
        "https://sefaria.org/api/texts/Ibn_Ezra_on_Daniel.7.13",
        "https://www.sefaria.org/api/texts/Daniel.7.13",
    ):
        citations.validate_sefaria_url(good)  # raises if rejected


# ── validator integration ───────────────────────────────────────────────────


def test_validator_accepts_external_sefaria_citation():
    """A well-formed external-sefaria citation must pass the validator."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
    from validate_scholar import validate_scholar

    doc = {
        "scholarId": "rashi-daniel",
        "authorDisplay": "Rashi",
        "workDisplay": "Rashi on Daniel",
        "resourceId": "sefaria:Rashi_on_Daniel",
        "resourceFile": "Rashi_on_Daniel.sefaria",
        "traditionTag": "medieval-jewish",
        "commitmentProfile": {"strong": ["messianic-reading"], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "Son of Man",
                "position": "Messianic identification",
                "commitment": "strong",
                "rationale": "Rashi identifies the figure as King Messiah.",
                "citations": [
                    {
                        "backend": {
                            "kind": "external-sefaria",
                            "resourceUrl": _RASHI_DAN_7_13_URL,
                            "language": "en",
                            "verseRef": "Daniel 7:13",
                            "commentator": "Rashi",
                        },
                        "frontend": {
                            "author": "Rashi",
                            "title": "Rashi on Daniel",
                            "section": "Daniel 7:13",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Rashi, Daniel 7:13",
                        },
                        "quote": {
                            "text": "That is the King Messiah.",
                            "sha256": sha256_of("That is the King Messiah."),
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }
    validate_scholar(doc)  # raises if invalid


def test_validator_rejects_logos_fields_on_sefaria_backend():
    """resourceId/logosArticleNum on an external-sefaria backend is forbidden."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
    from validate_scholar import ValidationError, validate_scholar

    doc = {
        "scholarId": "rashi-daniel",
        "authorDisplay": "Rashi",
        "workDisplay": "Rashi on Daniel",
        "resourceId": "sefaria:Rashi_on_Daniel",
        "resourceFile": "Rashi_on_Daniel.sefaria",
        "traditionTag": "medieval-jewish",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "Son of Man",
                "position": "Messianic",
                "commitment": "strong",
                "rationale": "x",
                "citations": [
                    {
                        "backend": {
                            "kind": "external-sefaria",
                            "resourceUrl": _RASHI_DAN_7_13_URL,
                            "language": "en",
                            "verseRef": "Daniel 7:13",
                            "resourceId": "LLS:SHOULD_NOT_BE_HERE",  # forbidden
                        },
                        "frontend": {
                            "author": "Rashi",
                            "title": "Rashi on Daniel",
                            "section": "Daniel 7:13",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Rashi, Daniel 7:13",
                        },
                        "quote": {
                            "text": "That is the King Messiah.",
                            "sha256": sha256_of("That is the King Messiah."),
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="not allowed"):
        validate_scholar(doc)


def test_validator_rejects_filename_on_sefaria_backend():
    """filename is for file-backed external kinds; not allowed on sefaria."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
    from validate_scholar import ValidationError, validate_scholar

    doc = {
        "scholarId": "rashi-daniel",
        "authorDisplay": "Rashi",
        "workDisplay": "Rashi on Daniel",
        "resourceId": "sefaria:Rashi_on_Daniel",
        "resourceFile": "Rashi_on_Daniel.sefaria",
        "traditionTag": "medieval-jewish",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "Son of Man",
                "position": "Messianic",
                "commitment": "strong",
                "rationale": "x",
                "citations": [
                    {
                        "backend": {
                            "kind": "external-sefaria",
                            "resourceUrl": _RASHI_DAN_7_13_URL,
                            "language": "en",
                            "verseRef": "Daniel 7:13",
                            "filename": "epubs/should-not-be-here.epub",  # forbidden
                        },
                        "frontend": {
                            "author": "Rashi",
                            "title": "Rashi on Daniel",
                            "section": "Daniel 7:13",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Rashi, Daniel 7:13",
                        },
                        "quote": {
                            "text": "That is the King Messiah.",
                            "sha256": sha256_of("That is the King Messiah."),
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="not allowed"):
        validate_scholar(doc)


def test_validator_requires_language_and_verse_ref_on_sefaria():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
    from validate_scholar import ValidationError, validate_scholar

    base_doc = {
        "scholarId": "rashi-daniel",
        "authorDisplay": "Rashi",
        "workDisplay": "Rashi on Daniel",
        "resourceId": "sefaria:Rashi_on_Daniel",
        "resourceFile": "Rashi_on_Daniel.sefaria",
        "traditionTag": "medieval-jewish",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "Son of Man",
                "position": "Messianic",
                "commitment": "strong",
                "rationale": "x",
                "citations": [
                    {
                        "backend": {
                            "kind": "external-sefaria",
                            "resourceUrl": _RASHI_DAN_7_13_URL,
                            # missing language + verseRef
                        },
                        "frontend": {
                            "author": "Rashi",
                            "title": "Rashi on Daniel",
                            "section": "Daniel 7:13",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Rashi, Daniel 7:13",
                        },
                        "quote": {
                            "text": "That is the King Messiah.",
                            "sha256": sha256_of("That is the King Messiah."),
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="language|verseRef"):
        validate_scholar(base_doc)


def test_validator_rejects_invalid_sefaria_url():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
    from validate_scholar import ValidationError, validate_scholar

    doc = {
        "scholarId": "rashi-daniel",
        "authorDisplay": "Rashi",
        "workDisplay": "Rashi on Daniel",
        "resourceId": "sefaria:Rashi_on_Daniel",
        "resourceFile": "Rashi_on_Daniel.sefaria",
        "traditionTag": "medieval-jewish",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "Son of Man",
                "position": "Messianic",
                "commitment": "strong",
                "rationale": "x",
                "citations": [
                    {
                        "backend": {
                            "kind": "external-sefaria",
                            "resourceUrl": "https://example.com/Rashi_on_Daniel.7.13",
                            "language": "en",
                            "verseRef": "Daniel 7:13",
                        },
                        "frontend": {
                            "author": "Rashi",
                            "title": "Rashi on Daniel",
                            "section": "Daniel 7:13",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Rashi, Daniel 7:13",
                        },
                        "quote": {
                            "text": "That is the King Messiah.",
                            "sha256": sha256_of("That is the King Messiah."),
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="sefaria"):
        validate_scholar(doc)


# ── external-ocr backend (D-2: multilingual generalization) ─────────────────


def _build_external_ocr_citation(
    *,
    filename,
    quote_text,
    language,
    translations=None,
):
    """Compose a hand-built external-ocr citation. ``build_citation`` is for
    Logos backends; OCR-text citations are constructed directly per schema."""
    quote = {
        "text": quote_text,
        "sha256": sha256_of(quote_text),
        "language": language,
    }
    citation = {
        "backend": {
            "kind": "external-ocr",
            "filename": filename,
        },
        "frontend": {
            "author": "Test Fixture Author",
            "title": "Test Fixture Work",
            "section": "test",
            "page": None,
            "pageEnd": None,
            "citationString": "Test Fixture",
        },
        "quote": quote,
        "supportStatus": "directly-quoted",
    }
    if translations is not None:
        citation["translations"] = translations
    return citation


def test_external_ocr_greek_round_trip_theodoret():
    """Real Theodoret OCR text — quote known to be present in greek/dan7.txt."""
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        # An anchor known to verify in the Theodoret JSON
        quote_text="θηρίον τὴν Ῥωμαϊχὴν χαλεῖ βασιλείαν",
        language="grc",
    )
    v = verify_citation(citation)
    assert v["status"] == "verified", v


def test_external_ocr_latin_round_trip_fixture():
    """Latin fixture under external-resources/latin/ verifies via the
    same backend with quote.language='la'."""
    citation = _build_external_ocr_citation(
        filename="latin/test-fixture-jerome-dan7.txt",
        quote_text=(
            "in fine mundi, quando regnum destruendum est Romanorum"
        ),
        language="la",
    )
    v = verify_citation(citation)
    assert v["status"] == "verified", v


def test_external_ocr_quote_not_found():
    """Fabricated quote against the real Theodoret OCR returns quote-not-found."""
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="this exact phrase is not in the Theodoret OCR text",
        language="grc",
    )
    v = verify_citation(citation)
    assert v["status"] == "quote-not-found", v


def test_external_ocr_filename_must_match_language():
    """quote.language='la' with filename starting greek/ → resource-unreadable."""
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",  # but language is la
        quote_text="anything",
        language="la",
    )
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v
    assert "latin/" in v["notes"], v


def test_external_ocr_unsupported_language():
    """An ISO code outside the OCR-accepted set returns resource-unreadable."""
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="es",  # Spanish — not in OCR_LANGUAGE_DIRS
    )
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v


def test_external_ocr_missing_language_field():
    """external-ocr citation with no quote.language is unreadable at runtime."""
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
    )
    del citation["quote"]["language"]
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v
    assert "language" in v["notes"], v


# ── schema enforcement: validator-level checks for external-ocr + translations


def test_validator_requires_quote_language_for_external_ocr():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
    )
    del citation["quote"]["language"]
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    with pytest.raises(ValidationError, match="quote.language"):
        validate_scholar(doc)


def test_validator_translations_full_fields_pass():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="θηρίον τὴν Ῥωμαϊχὴν χαλεῖ βασιλείαν",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "[the prophet] calls the Roman empire a beast",
                "translator": "anthropic:claude-opus-4-7",
                "translatedAt": "2026-04-29",
                "method": "llm",
                "register": "modern-faithful",
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    validate_scholar(doc)  # raises on failure


def test_validator_translations_missing_translator_fails_for_llm():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "translation here",
                # missing translator entirely
                "translatedAt": "2026-04-29",
                "method": "llm",
                "register": "modern-faithful",
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    with pytest.raises(ValidationError, match="translator"):
        validate_scholar(doc)


def test_validator_translations_llm_translator_must_have_provider_prefix():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "translation here",
                "translator": "claude-opus-4-7",  # no provider:model prefix
                "translatedAt": "2026-04-29",
                "method": "llm",
                "register": "modern-faithful",
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    with pytest.raises(ValidationError, match="provider"):
        validate_scholar(doc)


def test_validator_translations_human_published_no_colon_required():
    """method='human-published' translator does NOT need a colon."""
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="θηρίον τὴν Ῥωμαϊχὴν χαλεῖ βασιλείαν",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "translation here",
                "translator": "Salmond, ANF 5",
                "translatedAt": "1885-01-01",
                "method": "human-published",
                "register": "wooden-literal",
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    validate_scholar(doc)  # raises if invalid


def test_validator_translations_invalid_method_fails():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "x",
                "translator": "x",
                "translatedAt": "2026-04-29",
                "method": "ai",  # not in accepted set
                "register": "modern-faithful",
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    with pytest.raises(ValidationError, match="method"):
        validate_scholar(doc)


def test_validator_translations_invalid_register_fails():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "x",
                "translator": "anthropic:claude-opus-4-7",
                "translatedAt": "2026-04-29",
                "method": "llm",
                "register": "neo-paraphrase",  # not in accepted set
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    with pytest.raises(ValidationError, match="register"):
        validate_scholar(doc)


def test_validator_translations_invalid_date_fails():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "x",
                "translator": "anthropic:claude-opus-4-7",
                "translatedAt": "April 29, 2026",  # not YYYY-MM-DD
                "method": "llm",
                "register": "modern-faithful",
            }
        ],
    )
    doc = {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }
    with pytest.raises(ValidationError, match="translatedAt"):
        validate_scholar(doc)


def test_build_citation_accepts_language_and_translations_kwargs():
    """build_citation round-trips the new D-2 kwargs: language + translations."""
    translations = [
        {
            "language": "en",
            "text": "a faithful expectation",
            "translator": "anthropic:claude-opus-4-7",
            "translatedAt": "2026-04-29",
            "method": "llm",
            "register": "modern-faithful",
        }
    ]
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="A Failed Expectation",
        author="Beeke & Smalley",
        short_title="RST 4",
        language="en",
        translations=translations,
    )
    assert c["quote"]["language"] == "en"
    assert c["translations"] == translations


def test_build_citation_default_language_en_when_quote_present():
    """Without explicit language=, build_citation defaults quote.language to 'en'."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="A Failed Expectation",
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    assert c["quote"]["language"] == "en"


def test_build_citation_no_translations_field_when_omitted():
    """Omitting translations should NOT add a translations key (cleaner JSON)."""
    c = build_citation(
        resource_file="RFRMDSYSTH04.logos4",
        article_num=4718,
        quote_text="A Failed Expectation",
        author="Beeke & Smalley",
        short_title="RST 4",
    )
    assert "translations" not in c


# ── _load_ocr_text type defenses (D-2.5) ────────────────────────────────────


def test_load_ocr_text_rejects_non_string_language():
    """quote.language passed as a list/dict returns resource-unreadable, not TypeError."""
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
    )
    citation["quote"]["language"] = ["grc"]  # list, not string
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v
    assert "string" in v["notes"], v


def test_load_ocr_text_rejects_dict_language():
    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
    )
    citation["quote"]["language"] = {"code": "grc"}
    v = verify_citation(citation)
    assert v["status"] == "resource-unreadable", v
    assert "string" in v["notes"], v


# ── codex-flagged validator-coverage gaps (D-2.5) ──────────────────────────


def _wrap_doc(citation: dict) -> dict:
    """Wrap a single citation in a minimal scholar doc for the validator."""
    return {
        "scholarId": "ocr-test",
        "authorDisplay": "Test",
        "workDisplay": "Test",
        "resourceId": "external/test",
        "resourceFile": "greek/theodoret-pg81-dan7.txt",
        "traditionTag": "patristic",
        "commitmentProfile": {"strong": [], "moderate": [], "tentative": []},
        "positions": [
            {
                "axis": "A",
                "axisName": "x",
                "position": "x",
                "commitment": "strong",
                "rationale": "x",
                "citations": [citation],
            }
        ],
    }


def test_validator_external_ocr_requires_non_null_quote():
    """external-ocr citations MUST have a non-null quote (per schema doc)."""
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "x",
                "translator": "anthropic:claude-opus-4-7",
                "translatedAt": "2026-04-29",
                "method": "llm",
                "register": "modern-faithful",
            }
        ],
    )
    citation["quote"] = None
    citation["supportStatus"] = "paraphrase-anchored"
    with pytest.raises(ValidationError, match="external-ocr"):
        validate_scholar(_wrap_doc(citation))


def test_validator_external_ocr_explicit_null_language_rejected():
    """quote.language=null on external-ocr → rejected (the kind requires a language)."""
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="grc",
    )
    citation["quote"]["language"] = None
    with pytest.raises(ValidationError, match="quote.language"):
        validate_scholar(_wrap_doc(citation))


def test_validator_external_ocr_english_language_rejected():
    """language='en' on external-ocr is rejected — no english/ subdir, OCR is for non-English."""
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="greek/theodoret-pg81-dan7.txt",
        quote_text="anything",
        language="en",
    )
    with pytest.raises(ValidationError, match="quote.language"):
        validate_scholar(_wrap_doc(citation))


def test_validator_external_ocr_filename_language_dir_mismatch_rejected():
    """filename starts with latin/ but language is grc → rejected."""
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")
    )
    from validate_scholar import ValidationError, validate_scholar

    citation = _build_external_ocr_citation(
        filename="latin/something.txt",  # but language is grc
        quote_text="anything",
        language="grc",
        translations=[
            {
                "language": "en",
                "text": "x",
                "translator": "anthropic:claude-opus-4-7",
                "translatedAt": "2026-04-29",
                "method": "llm",
                "register": "modern-faithful",
            }
        ],
    )
    with pytest.raises(ValidationError, match="must start with"):
        validate_scholar(_wrap_doc(citation))
