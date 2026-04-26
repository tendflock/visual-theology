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

from citations import (  # noqa: E402
    SUPPORT_STATUS_VALUES,
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
