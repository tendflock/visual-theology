"""Tests for tools/validate_scholar.py."""

import copy
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from validate_scholar import (  # noqa: E402
    AXIS_LETTERS,
    COMMITMENT_VALUES,
    SUPPORT_STATUS_VALUES,
    ValidationError,
    validate_scholar,
)


# Override the session-scoped Flask `base_url` fixture from conftest.py.
# pytest-base-url plugin auto-injects `base_url`; without this override
# these pure-tool tests would pull in the conftest fixture and abort
# with a port-5111 conflict.
@pytest.fixture(scope="session")
def base_url():
    return None


ROOT = Path(__file__).resolve().parents[3]
SCHOLARS = ROOT / "docs" / "research" / "scholars"


def _minimal_scholar() -> dict:
    """A minimal passing scholar document."""
    return {
        "scholarId": "demo-scholar",
        "authorDisplay": "Demo",
        "workDisplay": "Demo Work",
        "resourceId": "LLS:DEMO",
        "resourceFile": "DEMO.logos4",
        "traditionTag": "demo-tradition",
        "commitmentProfile": {
            "strong": ["A: Sample — reason"],
            "moderate": [],
            "tentative": [],
        },
        "positions": [
            {
                "axis": "A",
                "axisName": "Dating",
                "position": "Sample position",
                "commitment": "strong",
                "rationale": "Sample rationale text",
                "compositional": None,
                "citations": [
                    {
                        "backend": {
                            "resourceId": "LLS:DEMO",
                            "logosArticleNum": 1,
                            "nativeSectionId": "S.1",
                        },
                        "frontend": {
                            "author": "Demo",
                            "title": "Demo Work",
                            "section": "§S.1",
                            "page": None,
                            "pageEnd": None,
                            "citationString": "Demo, Demo Work, §S.1",
                        },
                        "quote": {
                            "text": "A sample quotation",
                            "sha256": "0" * 64,
                        },
                        "supportStatus": "directly-quoted",
                    }
                ],
            }
        ],
    }


# ── happy path ──────────────────────────────────────────────────────────────


def test_minimal_scholar_validates():
    validate_scholar(_minimal_scholar())  # should not raise


def test_all_committed_scholar_files_validate_strict():
    """The four WS0b scholar files on disk validate in STRICT mode —
    every citation must carry a ``supportStatus`` from the fixed enum.

    This is the post-WS0.5-2 bar. If a new scholar file is added without
    supportStatus tags, this test fails.
    """
    for path in sorted(SCHOLARS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        with path.open(encoding="utf-8") as fh:
            doc = json.load(fh)
        try:
            validate_scholar(doc, require_support_status=True)
        except ValidationError as e:
            pytest.fail(
                f"{path.name} failed STRICT validation: {e}\n"
                "If this is a legacy file that predates WS0.5-2, either tag its "
                "citations with supportStatus or move it out of docs/research/scholars/."
            )


def test_all_committed_scholar_files_validate_lenient():
    """Backward-compat: files also validate in lenient mode (without
    requiring supportStatus). Used to catch pure-structural regressions
    separately from the tagging regression covered by the strict test."""
    for path in sorted(SCHOLARS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        with path.open(encoding="utf-8") as fh:
            doc = json.load(fh)
        try:
            validate_scholar(doc, require_support_status=False)
        except ValidationError as e:
            pytest.fail(f"{path.name} failed structural validation: {e}")


# ── required fields ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "missing_field",
    [
        "scholarId",
        "authorDisplay",
        "workDisplay",
        "resourceId",
        "resourceFile",
        "traditionTag",
        "commitmentProfile",
        "positions",
    ],
)
def test_missing_top_level_field_fails(missing_field):
    s = _minimal_scholar()
    del s[missing_field]
    with pytest.raises(ValidationError, match=missing_field):
        validate_scholar(s)


# ── axis letter ─────────────────────────────────────────────────────────────


def test_invalid_axis_letter_fails():
    s = _minimal_scholar()
    s["positions"][0]["axis"] = "Z"  # Z is not in the 16-axis taxonomy
    with pytest.raises(ValidationError, match="axis"):
        validate_scholar(s)


def test_all_valid_axis_letters_accepted():
    for letter in AXIS_LETTERS:
        s = _minimal_scholar()
        s["positions"][0]["axis"] = letter
        validate_scholar(s)  # no raise


# ── commitment enum ────────────────────────────────────────────────────────


def test_invalid_commitment_fails():
    s = _minimal_scholar()
    s["positions"][0]["commitment"] = "absolute"
    with pytest.raises(ValidationError, match="commitment"):
        validate_scholar(s)


@pytest.mark.parametrize("value", COMMITMENT_VALUES)
def test_valid_commitments_accepted(value):
    s = _minimal_scholar()
    s["positions"][0]["commitment"] = value
    validate_scholar(s)


# ── citation shape ─────────────────────────────────────────────────────────


def test_citation_missing_backend_fails():
    s = _minimal_scholar()
    del s["positions"][0]["citations"][0]["backend"]
    with pytest.raises(ValidationError, match="backend"):
        validate_scholar(s)


def test_citation_backend_missing_native_section_id_fails():
    s = _minimal_scholar()
    del s["positions"][0]["citations"][0]["backend"]["nativeSectionId"]
    with pytest.raises(ValidationError, match="nativeSectionId"):
        validate_scholar(s)


def test_citation_sha256_length_fails():
    s = _minimal_scholar()
    s["positions"][0]["citations"][0]["quote"]["sha256"] = "abc"
    with pytest.raises(ValidationError, match="sha256"):
        validate_scholar(s)


def test_citation_with_null_quote_accepted():
    s = _minimal_scholar()
    s["positions"][0]["citations"][0]["quote"] = None
    # When quote is null, supportStatus must not be 'directly-quoted'
    s["positions"][0]["citations"][0]["supportStatus"] = "paraphrase-anchored"
    validate_scholar(s)


def test_citation_page_end_without_page_fails():
    s = _minimal_scholar()
    s["positions"][0]["citations"][0]["frontend"]["page"] = None
    s["positions"][0]["citations"][0]["frontend"]["pageEnd"] = 42
    with pytest.raises(ValidationError, match="pageEnd"):
        validate_scholar(s)


# ── supportStatus ───────────────────────────────────────────────────────────


def test_support_status_required_when_enforced():
    s = _minimal_scholar()
    del s["positions"][0]["citations"][0]["supportStatus"]
    with pytest.raises(ValidationError, match="supportStatus"):
        validate_scholar(s, require_support_status=True)


@pytest.mark.parametrize("value", SUPPORT_STATUS_VALUES)
def test_all_support_status_values_accepted(value):
    s = _minimal_scholar()
    citation = s["positions"][0]["citations"][0]
    citation["supportStatus"] = value
    if value == "uncited-gap":
        # uncited-gap citations have no quote and often minimal shape
        citation["quote"] = None
    elif value in ("paraphrase-anchored", "summary-inference"):
        citation["quote"] = None
    validate_scholar(s)


def test_directly_quoted_requires_quote_text():
    s = _minimal_scholar()
    citation = s["positions"][0]["citations"][0]
    citation["supportStatus"] = "directly-quoted"
    citation["quote"] = None
    with pytest.raises(ValidationError, match="directly-quoted"):
        validate_scholar(s)


def test_uncited_gap_allowed_with_empty_citations():
    """A position with commitment=tentative and no citations still validates
    when the single 'uncited-gap' citation convention is not used (the
    positions[].citations list is simply empty)."""
    s = _minimal_scholar()
    s["positions"].append(
        {
            "axis": "B",
            "axisName": "Fourth kingdom",
            "position": "Unspecified",
            "commitment": "tentative",
            "rationale": "Scholar does not commit",
            "compositional": None,
            "citations": [],
        }
    )
    validate_scholar(s)


# ── cross-book readings ────────────────────────────────────────────────────


def test_cross_book_readings_optional():
    s = _minimal_scholar()
    # Not adding crossBookReadings key at all — should still validate.
    validate_scholar(s)


def test_cross_book_reading_malformed_fails():
    s = _minimal_scholar()
    s["crossBookReadings"] = [{"missing": "targetPassage"}]
    with pytest.raises(ValidationError, match="targetPassage"):
        validate_scholar(s)


# ── passageCoverage (WS0c-8) ───────────────────────────────────────────────


def test_passage_coverage_optional():
    """Files without passageCoverage still validate (legacy compatibility)."""
    s = _minimal_scholar()
    assert "passageCoverage" not in s
    validate_scholar(s)  # no raise


def test_passage_coverage_valid_entries_accepted():
    s = _minimal_scholar()
    s["passageCoverage"] = ["Dan 7:13-14", "Dan 7:9-12", "Rev 13"]
    validate_scholar(s)


def test_passage_coverage_invalid_entry_fails():
    s = _minimal_scholar()
    s["passageCoverage"] = ["Dan 7:13-14", "Dan 99:1-99"]  # second is bogus
    with pytest.raises(ValidationError, match="passageCoverage"):
        validate_scholar(s)


def test_passage_coverage_duplicate_entry_fails():
    s = _minimal_scholar()
    s["passageCoverage"] = ["Dan 7:13-14", "Dan 7:13-14"]
    with pytest.raises(ValidationError, match="duplicate"):
        validate_scholar(s)


def test_passage_coverage_must_be_list():
    s = _minimal_scholar()
    s["passageCoverage"] = "Dan 7:13-14"  # string, not list
    with pytest.raises(ValidationError, match="passageCoverage"):
        validate_scholar(s)


# ── external-resource backend kinds (WS0c-7) ──────────────────────────────


def _external_epub_citation() -> dict:
    """A minimal valid external-EPUB citation."""
    return {
        "backend": {
            "kind": "external-epub",
            "filename": "epubs/9781498221689.epub",
            "passageRef": "Lacocque on Dan 7:13",
        },
        "frontend": {
            "author": "Lacocque",
            "title": "The Book of Daniel",
            "section": "ch. 7",
            "page": None,
            "pageEnd": None,
            "citationString": "Lacocque, Daniel, ch. 7",
        },
        "quote": {"text": "A sample Lacocque quotation", "sha256": "0" * 64},
        "supportStatus": "directly-quoted",
    }


def _greek_ocr_citation() -> dict:
    return {
        "backend": {
            "kind": "external-ocr",
            "filename": "greek/theodoret-pg81-dan7.txt",
            "tlgCanon": "4089.028",
            "mignePgVolume": 81,
            "migneColumn": 1411,
        },
        "frontend": {
            "author": "Theodoret",
            "title": "Commentary on Daniel",
            "section": "PG 81 col. 1411",
            "page": None,
            "pageEnd": None,
            "citationString": "Theodoret, In Dan., PG 81 col. 1411",
        },
        "quote": {
            "text": "Παλαιὸς τῶν ἡμερῶν",
            "sha256": "0" * 64,
            "language": "grc",
        },
        "supportStatus": "directly-quoted",
    }


def _wrap(citation: dict) -> dict:
    """Wrap a citation in a minimal scholar doc for validation."""
    s = _minimal_scholar()
    s["positions"][0]["citations"] = [citation]
    return s


def test_external_epub_backend_validates():
    validate_scholar(_wrap(_external_epub_citation()))


def test_external_ocr_backend_validates():
    validate_scholar(_wrap(_greek_ocr_citation()))


def test_external_backend_missing_filename_fails():
    c = _external_epub_citation()
    del c["backend"]["filename"]
    with pytest.raises(ValidationError, match="filename"):
        validate_scholar(_wrap(c))


def test_external_backend_absolute_path_fails():
    c = _external_epub_citation()
    c["backend"]["filename"] = "/absolute/path.epub"
    with pytest.raises(ValidationError, match="relative"):
        validate_scholar(_wrap(c))


def test_external_backend_with_logos_fields_fails():
    c = _external_epub_citation()
    c["backend"]["resourceId"] = "LLS:WRONG"  # Logos-only field on external
    with pytest.raises(ValidationError, match="Logos-only"):
        validate_scholar(_wrap(c))


def test_unknown_backend_kind_fails():
    c = _external_epub_citation()
    c["backend"]["kind"] = "external-typewriter"
    with pytest.raises(ValidationError, match="kind"):
        validate_scholar(_wrap(c))


def test_logos_backend_default_when_kind_absent():
    """When backend.kind is absent, treat as logos (back-compat)."""
    s = _minimal_scholar()
    # _minimal_scholar already produces a logos-style backend without 'kind'
    assert "kind" not in s["positions"][0]["citations"][0]["backend"]
    validate_scholar(s)  # no raise


def test_external_ocr_typed_extras():
    c = _greek_ocr_citation()
    c["backend"]["mignePgVolume"] = "eighty-one"  # wrong type
    with pytest.raises(ValidationError, match="mignePgVolume"):
        validate_scholar(_wrap(c))
