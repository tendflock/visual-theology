"""Run ``verify_citation`` across every citation in a set of research inputs.

Two input modes:

1. **JSON scholar files** (WS0b output) — ``docs/research/scholars/*.json``. Each
   file's ``positions[].citations`` and ``crossBookReadings[].citations`` are
   verified individually.

2. **Legacy markdown research doc** — the 2026-04-23 taxonomy survey uses
   inline ``(art. N)`` references with adjacent direct quotes. We spot-check
   those pairs: each `"quote" (art. N)` pattern gets a best-effort citation
   built against the nearest referenced scholar/resource mapping.

Output: a markdown report at the path given via ``--out`` (default
``docs/research/2026-04-24-citation-verification-report.md``) plus a one-line
summary on stdout.

CLI::

    python tools/sweep_citations.py \
        --scholars docs/research/scholars \
        --legacy-md docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md \
        --out docs/research/2026-04-24-citation-verification-report.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from citations import build_citation, verify_citation  # noqa: E402


# ── data types ──────────────────────────────────────────────────────────────


@dataclass
class SweepResult:
    source: str
    ident: str
    status: str
    notes: str = ""


# ── scholar JSON files ──────────────────────────────────────────────────────


def sweep_scholar_files(scholars_dir: Path) -> list[SweepResult]:
    results: list[SweepResult] = []
    for json_path in sorted(scholars_dir.glob("*.json")):
        if json_path.name.startswith("_"):
            continue
        try:
            with json_path.open(encoding="utf-8") as fh:
                scholar = json.load(fh)
        except (OSError, ValueError) as e:
            results.append(
                SweepResult(
                    source=str(json_path),
                    ident="<parse-error>",
                    status="resource-unreadable",
                    notes=f"failed to load JSON: {e}",
                )
            )
            continue

        scholar_id = scholar.get("scholarId", json_path.stem)
        results.extend(_sweep_scholar(scholar, scholar_id, json_path.name))

    return results


def _sweep_scholar(
    scholar: dict, scholar_id: str, filename: str
) -> list[SweepResult]:
    out: list[SweepResult] = []
    for pos in scholar.get("positions", []) or []:
        axis = pos.get("axis", "?")
        for i, c in enumerate(pos.get("citations", []) or []):
            v = verify_citation(c)
            out.append(
                SweepResult(
                    source=filename,
                    ident=f"{scholar_id}/axis-{axis}/citation-{i}",
                    status=v["status"],
                    notes=v.get("notes", ""),
                )
            )
    for x in scholar.get("crossBookReadings", []) or []:
        target = x.get("targetPassage", "?")
        for i, c in enumerate(x.get("citations", []) or []):
            v = verify_citation(c)
            out.append(
                SweepResult(
                    source=filename,
                    ident=f"{scholar_id}/crossBook-{target}/citation-{i}",
                    status=v["status"],
                    notes=v.get("notes", ""),
                )
            )
    return out


# ── legacy markdown quotes ──────────────────────────────────────────────────


# Match direct `"quote text" (art. N)` patterns. The quote body may contain
# any chars except " or newline, AND must not span a prior `(art. X)` — so the
# greedy body is bounded by `[^"(]` to stop before a `(art…)` reference.
# Minimum 15-char quote to reduce false positives on one-word quotes.
_LEGACY_QUOTE_RE = re.compile(
    r'"([^"(\n]{15,})"[^()\n]{0,40}\(art[s]?\.\s*([0-9]+(?:\s*,\s*[0-9]+)*)\)',
    re.MULTILINE,
)

# A scholar section header introduces the resource mapping for following quotes.
# e.g., `**Collins, *The Apocalyptic Imagination* (3rd ed)** —`
# Keys map author substring → (resource_file, short_title, author_display).
LEGACY_SCHOLAR_MAP: dict[str, tuple[str, str, str]] = {
    "Bauckham": ("NTTHEO87REV.logos4", "Bauckham Theology of Revelation", "Bauckham"),
    "Wright, *The New Testament": ("NTPPLOFGOD.logos4", "Wright NTPG", "Wright"),
    "Collins, *The Apocalyptic Imagination*": (
        "PCLYPTCMGNTNPLT.logos4",
        "Collins Apocalyptic Imagination",
        "Collins",
    ),
    "Newsom & Breed": ("OTL27DA.logos4", "Newsom OTL Daniel", "Newsom & Breed"),
    "Longman, *Daniel*": ("NIVAC27DA.logos4", "Longman NIVAC Daniel", "Longman"),
    "Lucas, *Daniel*": ("AOT27DA.logos4", "Lucas AOTC Daniel", "Lucas"),
    "Hoekema": ("BBLANDTHEFUTURE.logos4", "Hoekema Bible and the Future", "Hoekema"),
    "Riddlebarger": ("CSAMLLNLSM.logos4", "Riddlebarger Amil", "Riddlebarger"),
    "Sproul": ("LSTDYSCCRDNGJSS.logos4", "Sproul Last Days", "Sproul"),
}


def sweep_legacy_markdown(
    md_path: Path, max_samples: int | None = 20
) -> list[SweepResult]:
    text = md_path.read_text(encoding="utf-8")
    results: list[SweepResult] = []
    # Walk by scholar block (split at `^### ` or `^**<Author>`)
    current_scholar: tuple[str, str, str] | None = None
    total_matched = 0

    for line_start, end, scholar_key in _scholar_sections(text):
        mapping = LEGACY_SCHOLAR_MAP.get(scholar_key)
        if not mapping:
            continue
        current_scholar = mapping
        section = text[line_start:end]
        for m in _LEGACY_QUOTE_RE.finditer(section):
            if max_samples and total_matched >= max_samples:
                break
            quote = m.group(1).strip()
            arts = [int(a.strip()) for a in m.group(2).split(",")]
            first_art = arts[0]
            resource_file, short_title, author_display = current_scholar
            try:
                citation = build_citation(
                    resource_file=resource_file,
                    article_num=first_art,
                    quote_text=quote,
                    author=author_display,
                    short_title=short_title,
                )
                v = verify_citation(citation)
                status = v["status"]
                notes = v.get("notes", "")
            except RuntimeError as e:
                status = "resource-unreadable"
                notes = str(e)
            results.append(
                SweepResult(
                    source=md_path.name,
                    ident=f"{author_display} (art. {first_art})",
                    status=status,
                    notes=notes,
                )
            )
            total_matched += 1
        if max_samples and total_matched >= max_samples:
            break
    return results


def _scholar_sections(text: str) -> list[tuple[int, int, str]]:
    """Return list of (start, end, scholar_key) spans."""
    # Find `**Author, *Work***` patterns starting a scholar block.
    # Content may contain italic markers (single asterisks), so allow them.
    pattern = re.compile(r"^\*\*(.+?)\*\*\s*—", re.MULTILINE)
    hits: list[tuple[int, int, str]] = []
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        key = _match_scholar_key(m.group(1))
        if key:
            hits.append((start, end, key))
    return hits


def _match_scholar_key(heading_text: str) -> str | None:
    for key in LEGACY_SCHOLAR_MAP:
        if key in heading_text:
            return key
    return None


# ── report ──────────────────────────────────────────────────────────────────


STATUSES = ["verified", "partial", "quote-not-found", "resource-unreadable"]


_LEGACY_PARAPHRASE_RE = re.compile(
    r"\(paraphrase;\s*verbatim quote not located in art\.\s*([0-9]+)",
    re.IGNORECASE,
)


def count_legacy_paraphrase_demotions(md_path: Path | None) -> int:
    """Count places in a legacy markdown research doc where a previously-quoted
    claim has been explicitly demoted to a paraphrase (the form
    ``(paraphrase; verbatim quote not located in art. N — …)``).

    These are NOT verified quotations; they're claims retained as research-doc
    summary. The verification sweep's regex will not match them (they don't
    have surrounding double-quotes), so without this counter they would
    disappear silently from the totals — making the verification rate look
    higher than it is in fact.
    """
    if md_path is None or not md_path.exists():
        return 0
    text = md_path.read_text(encoding="utf-8")
    return len(_LEGACY_PARAPHRASE_RE.findall(text))


def render_report(
    results: list[SweepResult], demoted_paraphrases: int = 0
) -> str:
    tally = {s: 0 for s in STATUSES}
    for r in results:
        tally[r.status] = tally.get(r.status, 0) + 1
    total = len(results) or 1

    lines: list[str] = []
    lines.append("# Citation Verification Report")
    lines.append("")
    lines.append(f"Total citations swept: **{total}**")
    lines.append("")
    for s in STATUSES:
        pct = 100.0 * tally[s] / total
        lines.append(f"- `{s}`: {tally[s]} ({pct:.1f}%)")
    if demoted_paraphrases:
        lines.append(
            f"- `demoted-to-paraphrase` (legacy doc, not counted in totals): "
            f"{demoted_paraphrases}"
        )
        lines.append("")
        lines.append(
            "> **Counting note.** The sweep's quote-extraction regex matches "
            "only material wrapped in double-quotes adjacent to an `(art. N)` "
            "reference. When a previously-quoted claim is repaired by removing "
            "the quotation marks and adding a `(paraphrase; verbatim quote not "
            "located...)` note, it is no longer counted as a quotation — and "
            "therefore not counted in the verified total. The line above tracks "
            "those demotions so the methodology is transparent: a demoted "
            "claim is research-doc summary, not a verified quotation, and "
            "should be treated as such by downstream consumers."
        )
    lines.append("")

    # Group results by source
    by_source: dict[str, list[SweepResult]] = {}
    for r in results:
        by_source.setdefault(r.source, []).append(r)

    for source, rs in by_source.items():
        lines.append(f"## {source}")
        lines.append("")
        s_tally = {s: 0 for s in STATUSES}
        for r in rs:
            s_tally[r.status] = s_tally.get(r.status, 0) + 1
        lines.append(
            "Summary: "
            + ", ".join(f"{s}={s_tally[s]}" for s in STATUSES if s_tally[s])
        )
        lines.append("")

        # List non-verified up front
        non_verified = [r for r in rs if r.status != "verified"]
        if non_verified:
            lines.append("### Flagged")
            lines.append("")
            for r in non_verified:
                note = f" — {r.notes}" if r.notes else ""
                lines.append(f"- `{r.status}` | {r.ident}{note}")
            lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scholars", type=Path, default=Path("docs/research/scholars")
    )
    parser.add_argument("--legacy-md", type=Path, default=None)
    parser.add_argument(
        "--legacy-sample",
        type=int,
        default=20,
        help="Cap on how many legacy-markdown quotes to sample (default 20).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/research/2026-04-24-citation-verification-report.md"),
    )
    args = parser.parse_args(argv)

    results: list[SweepResult] = []
    if args.scholars.exists():
        results.extend(sweep_scholar_files(args.scholars))
    else:
        sys.stderr.write(f"[info] scholars dir missing: {args.scholars}\n")

    if args.legacy_md and args.legacy_md.exists():
        results.extend(
            sweep_legacy_markdown(args.legacy_md, max_samples=args.legacy_sample)
        )

    demoted = count_legacy_paraphrase_demotions(args.legacy_md)
    report = render_report(results, demoted_paraphrases=demoted)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")

    tally = {s: sum(1 for r in results if r.status == s) for s in STATUSES}
    total = len(results) or 1
    summary = ", ".join(f"{s}={tally[s]}" for s in STATUSES if tally[s])
    sys.stdout.write(f"{total} citations swept → {summary}; report: {args.out}\n")
    return 0 if tally.get("verified", 0) / total >= 0.90 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
