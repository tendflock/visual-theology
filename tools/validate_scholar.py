"""Structural validator for ``docs/research/scholars/*.json``.

Scope: structural/shape validation only. Enforces the shape documented in
``docs/schema/citation-schema.md`` plus the scholar-file envelope
(authorDisplay, commitmentProfile, positions[] etc.). Catches the class of
drift codex surfaced manually during the WS0 audit: axis-letter misassignment,
missing required fields, commitment values outside the fixed enum, citations
with a page-end but no page-start, directly-quoted citations with a null
quote, etc.

Deliberate non-goals (semantic checks left to other tools):
- Does ``quote.sha256`` equal ``sha256(quote.text)``? Not checked here; use
  ``tools/citations.py:verify_citation`` (it rejects the citation as
  ``partial`` when the stored hash and text disagree).
- Does the claimed ``axisName`` match the locked taxonomy's name for that
  letter? Not checked; the letter is validated but its human-readable name
  is free text.
- Does each axis's ``position`` value come from an allowed enum per axis?
  The taxonomy specifies allowed positions per axis, but those are not yet
  codified as a machine-readable enum here.
- Does the ``rationale`` actually follow from the ``citations``? That is a
  semantic warrant question and requires human or adversarial-agent review
  (see ``docs/research/2026-04-24-ws05-6-claim-warrant-audit.md``).

CLI::

    # Strict mode (requires supportStatus on every citation — the default):
    python tools/validate_scholar.py docs/research/scholars/

    # Legacy/lenient mode (accepts files that predate WS0.5-2 tagging):
    python tools/validate_scholar.py --no-require-support-status docs/research/scholars/

Exits 0 when every input validates, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


# Locked axis taxonomy (see docs/research/2026-04-23-daniel-interpretive-
# taxonomy-survey.md §"Expanded axis catalog (v2)"). Letters A–O are the
# content axes; P and Q are the meta-axes from the second-pass survey.
AXIS_LETTERS: tuple[str, ...] = tuple("ABCDEFGHIJKLMNOPQ")

COMMITMENT_VALUES: tuple[str, ...] = ("strong", "moderate", "tentative")

SUPPORT_STATUS_VALUES: tuple[str, ...] = (
    "directly-quoted",      # quote.text is a verbatim fragment from the article
    "paraphrase-anchored",  # claim anchored to the article, but stored as summary
    "summary-inference",    # scholar summary spanning multiple articles/sections
    "uncited-gap",          # commitment tagged but no supporting citation present
)

# Controlled vocabulary for the scholar-file `passageCoverage[]` field (WS0c-8).
# A scholar JSON declares which biblical verse-blocks the surveyed material engages
# substantively; the validator enforces membership in this set so typos can't drift
# the project's per-passage coverage diagnostics.
#
# To extend: append to this tuple AND document the new entry in
# `docs/schema/citation-schema.md` §"Scholar-file passage coverage".
PASSAGE_COVERAGE_VOCAB: tuple[str, ...] = (
    # Daniel 7 pilot — primary verse-blocks
    "Dan 7:1-6",
    "Dan 7:7-8",
    "Dan 7:9-12",
    "Dan 7:13-14",
    "Dan 7:15-18",
    "Dan 7:19-22",
    "Dan 7:23-27",
    # Adjacent Daniel passages a Dan 7 site cross-references
    "Dan 2:31-45",
    "Dan 8:1-27",
    "Dan 9:1-19",
    "Dan 9:20-27",
    "Dan 10:1-21",
    "Dan 11:1-45",
    "Dan 12:1-13",
    # New-Testament cross-references
    "Rev 1",
    "Rev 13",
    "Rev 17",
    "Rev 20",
    "Matt 24",
    "Mark 13",
    # Second-Temple reception
    "1 En 37-71",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SCHOLAR_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ValidationError(Exception):
    """Raised when a scholar document fails validation."""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)


def _require_type(value: Any, typ: type | tuple[type, ...], path: str) -> None:
    if not isinstance(value, typ):
        type_name = (
            typ.__name__ if isinstance(typ, type) else "/".join(t.__name__ for t in typ)
        )
        raise ValidationError(f"{path}: expected {type_name}, got {type(value).__name__}")


def validate_scholar(doc: Any, *, require_support_status: bool = True) -> None:
    """Raise ``ValidationError`` if ``doc`` does not match the scholar schema.

    Pass ``require_support_status=False`` to accept legacy scholar files that
    predate the per-citation ``supportStatus`` field (WS0.5-2). Structural
    checks still apply.
    """
    _require_type(doc, dict, "<root>")

    # ── top-level required fields ────────────────────────────────────────
    required_top = [
        "scholarId",
        "authorDisplay",
        "workDisplay",
        "resourceId",
        "resourceFile",
        "traditionTag",
        "commitmentProfile",
        "positions",
    ]
    for field in required_top:
        _require(field in doc, f"<root>: missing required field {field!r}")

    _require_type(doc["scholarId"], str, "scholarId")
    _require(
        _SCHOLAR_ID_RE.match(doc["scholarId"]),
        f"scholarId: must be kebab-case, got {doc['scholarId']!r}",
    )
    for f in ("authorDisplay", "workDisplay", "resourceId", "resourceFile", "traditionTag"):
        _require_type(doc[f], str, f)
        _require(doc[f].strip(), f"{f}: must be non-empty")

    # Top-level resourceId conventions:
    #   - Logos-sourced scholars use the canonical "LLS:STEM" identifier
    #     (matches each citation's backend.resourceId).
    #   - External-sourced scholars (EPUB, PDF, Greek-OCR) use a project-
    #     local identifier; the file path lives in citations' backend.filename.
    # Required: when ANY citation in the file has a logos-kind backend, the
    # top-level resourceId must use the LLS: convention.
    _has_logos_citation = any(
        (c.get("backend") or {}).get("kind", "logos") == "logos"
        for pos in (doc.get("positions") or [])
        for c in (pos.get("citations") or [])
    ) or any(
        (c.get("backend") or {}).get("kind", "logos") == "logos"
        for x in (doc.get("crossBookReadings") or [])
        for c in (x.get("citations") or [])
    )
    if _has_logos_citation:
        _require(
            doc["resourceId"].startswith("LLS:"),
            f"resourceId: must start with 'LLS:' for Logos-sourced scholars, "
            f"got {doc['resourceId']!r}",
        )

    # ── commitmentProfile ────────────────────────────────────────────────
    cp = doc["commitmentProfile"]
    _require_type(cp, dict, "commitmentProfile")
    for bucket in COMMITMENT_VALUES:
        _require(bucket in cp, f"commitmentProfile: missing bucket {bucket!r}")
        _require_type(cp[bucket], list, f"commitmentProfile.{bucket}")
        for i, item in enumerate(cp[bucket]):
            _require_type(item, str, f"commitmentProfile.{bucket}[{i}]")

    # ── positions[] ──────────────────────────────────────────────────────
    positions = doc["positions"]
    _require_type(positions, list, "positions")
    _require(positions, "positions: must contain at least one entry")
    for i, pos in enumerate(positions):
        _validate_position(pos, f"positions[{i}]", require_support_status)

    # ── crossBookReadings (optional) ─────────────────────────────────────
    for i, reading in enumerate(doc.get("crossBookReadings", []) or []):
        _validate_cross_book(reading, f"crossBookReadings[{i}]", require_support_status)

    # ── distinctiveMoves / uncertainties (optional lists of strings) ─────
    for field in ("distinctiveMoves", "uncertainties"):
        if field in doc:
            _require_type(doc[field], list, field)
            for i, m in enumerate(doc[field]):
                _require_type(m, str, f"{field}[{i}]")

    # ── passageCoverage (optional list of vocabulary-controlled strings) ──
    # WS0c-8: each scholar declares which verse-blocks the surveyed material
    # engages substantively. Optional today (legacy files predate it); the
    # validator enforces membership in PASSAGE_COVERAGE_VOCAB when present.
    if "passageCoverage" in doc:
        _require_type(doc["passageCoverage"], list, "passageCoverage")
        seen = set()
        for i, p in enumerate(doc["passageCoverage"]):
            _require_type(p, str, f"passageCoverage[{i}]")
            _require(
                p in PASSAGE_COVERAGE_VOCAB,
                f"passageCoverage[{i}]: {p!r} not in PASSAGE_COVERAGE_VOCAB "
                f"(see docs/schema/citation-schema.md §'Scholar-file passage coverage')",
            )
            _require(p not in seen, f"passageCoverage[{i}]: duplicate entry {p!r}")
            seen.add(p)


def _validate_position(
    pos: Any, path: str, require_support_status: bool
) -> None:
    _require_type(pos, dict, path)
    for f in ("axis", "axisName", "position", "commitment", "rationale", "citations"):
        _require(f in pos, f"{path}: missing required field {f!r}")

    _require_type(pos["axis"], str, f"{path}.axis")
    _require(
        pos["axis"] in AXIS_LETTERS,
        f"{path}.axis: {pos['axis']!r} not in locked taxonomy {AXIS_LETTERS}",
    )

    _require_type(pos["axisName"], str, f"{path}.axisName")
    _require_type(pos["position"], str, f"{path}.position")
    _require_type(pos["rationale"], str, f"{path}.rationale")

    _require_type(pos["commitment"], str, f"{path}.commitment")
    _require(
        pos["commitment"] in COMMITMENT_VALUES,
        f"{path}.commitment: {pos['commitment']!r} not in {COMMITMENT_VALUES}",
    )

    # compositional is optional. Spec envisions a structured dict
    # (basePosition + fulfillmentMode + extendsTo + scope), but the WS0b
    # surveys also use free-form strings as compositional notes — accept
    # both shapes for now.
    comp = pos.get("compositional", None)
    if comp is not None and not isinstance(comp, (dict, str)):
        raise ValidationError(
            f"{path}.compositional: expected dict|str|null, got {type(comp).__name__}"
        )

    citations = pos["citations"]
    _require_type(citations, list, f"{path}.citations")
    for j, c in enumerate(citations):
        _validate_citation(c, f"{path}.citations[{j}]", require_support_status)


def _validate_cross_book(
    reading: Any, path: str, require_support_status: bool
) -> None:
    _require_type(reading, dict, path)
    for f in ("targetPassage", "positionSummary", "citations"):
        _require(f in reading, f"{path}: missing required field {f!r}")
    _require_type(reading["targetPassage"], str, f"{path}.targetPassage")
    _require_type(reading["positionSummary"], str, f"{path}.positionSummary")
    _require_type(reading["citations"], list, f"{path}.citations")
    for j, c in enumerate(reading["citations"]):
        _validate_citation(c, f"{path}.citations[{j}]", require_support_status)


_BACKEND_KINDS = (
    "logos",
    "external-epub",
    "external-pdf",
    "external-greek-ocr",
)


def _validate_citation(
    c: Any, path: str, require_support_status: bool
) -> None:
    _require_type(c, dict, path)

    # backend (dispatched by kind)
    _require("backend" in c, f"{path}: missing 'backend'")
    b = c["backend"]
    _require_type(b, dict, f"{path}.backend")

    # WS0c-7: backend.kind defaults to "logos" for back-compat.
    kind = b.get("kind", "logos")
    _require(
        kind in _BACKEND_KINDS,
        f"{path}.backend.kind: {kind!r} not in {_BACKEND_KINDS}",
    )

    if kind == "logos":
        for f in ("resourceId", "logosArticleNum", "nativeSectionId"):
            _require(f in b, f"{path}.backend(logos): missing required field {f!r}")
        _require_type(b["resourceId"], str, f"{path}.backend.resourceId")
        _require_type(b["logosArticleNum"], int, f"{path}.backend.logosArticleNum")
        _require_type(b["nativeSectionId"], str, f"{path}.backend.nativeSectionId")
    else:
        # External resources require backend.filename (path rel to
        # external-resources/) and forbid the Logos-only fields.
        _require(
            "filename" in b,
            f"{path}.backend({kind}): missing required field 'filename'",
        )
        _require_type(b["filename"], str, f"{path}.backend.filename")
        _require(
            b["filename"] and not b["filename"].startswith("/"),
            f"{path}.backend.filename: must be a relative path under external-resources/",
        )
        for forbidden in ("resourceId", "logosArticleNum", "nativeSectionId"):
            _require(
                forbidden not in b,
                f"{path}.backend({kind}): field {forbidden!r} is Logos-only",
            )
        # Optional kind-specific extras (no enforcement, just type if present)
        if kind == "external-greek-ocr":
            for opt in ("tlgCanon", "mignePgVolume", "migneColumn", "passageRef"):
                if opt in b and b[opt] is not None:
                    if opt == "mignePgVolume" or opt == "migneColumn":
                        _require_type(b[opt], int, f"{path}.backend.{opt}")
                    else:
                        _require_type(b[opt], str, f"{path}.backend.{opt}")

    # frontend
    _require("frontend" in c, f"{path}: missing 'frontend'")
    fe = c["frontend"]
    _require_type(fe, dict, f"{path}.frontend")
    for f in ("author", "title", "section", "page", "pageEnd", "citationString"):
        _require(f in fe, f"{path}.frontend: missing required field {f!r}")
    if fe["author"] is not None:
        _require_type(fe["author"], str, f"{path}.frontend.author")
    if fe["title"] is not None:
        _require_type(fe["title"], str, f"{path}.frontend.title")
    if fe["section"] is not None:
        _require_type(fe["section"], str, f"{path}.frontend.section")
    if fe["page"] is not None:
        _require_type(fe["page"], int, f"{path}.frontend.page")
    if fe["pageEnd"] is not None:
        _require_type(fe["pageEnd"], int, f"{path}.frontend.pageEnd")
    _require_type(fe["citationString"], str, f"{path}.frontend.citationString")

    # page/pageEnd consistency
    _require(
        not (fe["page"] is None and fe["pageEnd"] is not None),
        f"{path}.frontend: pageEnd is set but page is null",
    )

    # quote
    _require("quote" in c, f"{path}: missing 'quote'")
    q = c["quote"]
    if q is not None:
        _require_type(q, dict, f"{path}.quote")
        _require("text" in q, f"{path}.quote: missing 'text'")
        _require("sha256" in q, f"{path}.quote: missing 'sha256'")
        _require_type(q["text"], str, f"{path}.quote.text")
        _require_type(q["sha256"], str, f"{path}.quote.sha256")
        _require(
            _SHA256_RE.match(q["sha256"]),
            f"{path}.quote.sha256: must be 64 lowercase hex chars",
        )

    # supportStatus — required when enforced
    if require_support_status:
        _require(
            "supportStatus" in c,
            f"{path}: missing 'supportStatus' (enforced per WS0.5-2)",
        )
        status = c["supportStatus"]
        _require_type(status, str, f"{path}.supportStatus")
        _require(
            status in SUPPORT_STATUS_VALUES,
            f"{path}.supportStatus: {status!r} not in {SUPPORT_STATUS_VALUES}",
        )
        # A 'directly-quoted' citation MUST carry a quote.
        if status == "directly-quoted":
            _require(
                q is not None and q.get("text"),
                f"{path}: supportStatus='directly-quoted' requires quote.text",
            )
    elif "supportStatus" in c:
        # Still validate the enum if present.
        _require(
            c["supportStatus"] in SUPPORT_STATUS_VALUES,
            f"{path}.supportStatus: {c['supportStatus']!r} not in {SUPPORT_STATUS_VALUES}",
        )


# ── CLI ─────────────────────────────────────────────────────────────────────


def _iter_paths(paths: Iterable[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_dir():
            for child in sorted(p.glob("*.json")):
                if not child.name.startswith("_"):
                    yield child
        else:
            yield p


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--no-require-support-status",
        action="store_true",
        help="Accept files that predate WS0.5-2 supportStatus tagging.",
    )
    args = parser.parse_args(argv)

    failed = 0
    checked = 0
    for path in _iter_paths(args.paths):
        checked += 1
        try:
            with path.open(encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as e:
            failed += 1
            sys.stderr.write(f"FAIL {path}: could not load: {e}\n")
            continue
        try:
            validate_scholar(
                doc, require_support_status=not args.no_require_support_status
            )
        except ValidationError as e:
            failed += 1
            sys.stderr.write(f"FAIL {path}: {e}\n")
            continue
        sys.stdout.write(f"OK   {path}\n")

    sys.stdout.write(f"\n{checked - failed}/{checked} files valid\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
