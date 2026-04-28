"""Apply Wave 1 codex-audit supportStatus relabels.

Driven by the per-citation table in
``docs/research/2026-04-27-wave1-codex-audit.md`` §2. Codex flagged 17
citations across the 5 Wave 1 scholar JSONs as ``directly-quoted``
over-applications: 3 should drop to ``paraphrase-anchored``, 14 should
drop to ``summary-inference``.

Mirrors the structure of ``tools/apply_ws0c_relabels.py``: each row
pinpoints one citation by file + axis (or cross-book targetPassage) +
a substring of its quote.text that codex's reason names. Idempotent:
re-running on already-relabeled files is a no-op. Exits non-zero if
any expected citation is missing or has unexpected current state — no
silent skips.

Run from project root::

    python3 tools/apply_wave1_relabels.py

Total: 17 supportStatus relabels (3 → paraphrase-anchored,
14 → summary-inference).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Each entry: (filename, kind, key, quote_substring, new_status, reason)
#   kind = "axis" or "xbook"
#   key  = axis letter (e.g. "L") or cross-book targetPassage prefix (e.g.
#          "Rev 13" or "1 En 37-71"; matched as a startswith() on the actual
#          targetPassage so newsom's "1 En 37-71 (Similitudes/Parables of
#          Enoch)" resolves)
#   quote_substring = a unique substring of the citation's quote.text
#   reason  = codex's verbatim reason from the audit doc §2 (kept here for
#             grep-traceability; not written into the JSON)
RELABELS: list[tuple[str, str, str, str, str, str]] = [
    # ── 4 Ezra (Stone, Hermeneia) ─────────────────────────────────────
    ("4-ezra-stone-hermeneia.json", "axis", "L",
     "Therefore, the three heads should be regarded as the three Flavian emperors",
     "summary-inference",
     "The quote proves Flavian identification, but not Stone's whole "
     "critical-historical method, source/redaction analysis, comparative "
     "apocalyptic method, or Hermeneia-style synthesis."),
    ("4-ezra-stone-hermeneia.json", "axis", "L",
     "the date of the composition of the vision in the time of Domitian",
     "summary-inference",
     "The quote proves Domitian dating for the vision, not the broader "
     "methodological profile claimed for Stone."),
    ("4-ezra-stone-hermeneia.json", "axis", "L",
     "composed in the time of Domitian",
     "summary-inference",
     "The quote proves the Domitian date, but the rationale claims a broad "
     "adjudication of source, redaction, tradition-history, and "
     "literary-structural method."),
    ("4-ezra-stone-hermeneia.json", "axis", "C",
     "The pride of sinners recurs in the book in an eschatological context",
     "summary-inference",
     "The quote only supports an eschatological pride motif; it does not "
     "prove the Dan 7:8/11/25 little-horn mapping, antichrist associations, "
     "collective-Rome reading, or resistance to a single-individual "
     "identification."),
    ("4-ezra-stone-hermeneia.json", "axis", "H",
     "The messianic kingdom will come to an end; it is not eternal.",
     "summary-inference",
     "The quote directly proves only that the messianic kingdom is "
     "temporary; the rationale synthesizes a multi-stage eschatological "
     "sequence across several sections."),

    # ── Wright, Jesus and the Victory of God ──────────────────────────
    ("wright-jesus-victory-of-god.json", "axis", "N",
     "Behind this in turn, of course, there stand three passages in Daniel",
     "paraphrase-anchored",
     "The quote says only that three Daniel passages stand behind the "
     "argument; it does not identify Dan 7:25, 11:31, and 9:26-27 or prove "
     "the full Mark 13 / Mark 14 / Daniel / Psalm 110 integration."),
    ("wright-jesus-victory-of-god.json", "xbook", "Matt 24",
     "It is crass literalism",
     "summary-inference",
     "The quote supports Wright's anti-literalist reading of cosmic-collapse "
     "language, but it does not by itself prove the Matt 24 parousia-language, "
     "abomination citation, AD 70 setting, or Mark/Matthew synthesis."),

    # ── Augustine, City of God Book 20 ────────────────────────────────
    ("augustine-city-of-god-book-20.json", "xbook", "Rev 13",
     "Antichrist means not the prince himself alone, but his whole body",
     "summary-inference",
     "The quote supports Augustine's corporate-or-personal Antichrist option "
     "from 2 Thessalonians, not a direct Rev 13 reading."),
    ("augustine-city-of-god-book-20.json", "xbook", "Rev 13",
     "refer to the Roman empire",
     "summary-inference",
     "The quote supports a possible Roman-empire restrainer reading in "
     "2 Thessalonians, but not Rev 13 beast exegesis."),

    # ── Hippolytus, ANF 5 (on Daniel) ─────────────────────────────────
    ("hippolytus-anf5-daniel.json", "axis", "F",
     "By the stretching forth of His two hands He signified His passion",
     "paraphrase-anchored",
     "The quote names Christ's passion typology, but it does not prove the "
     "6,000-year chronology, Christ-at-year-5,500 calculation, or "
     "Sabbath-millennium structure."),
    ("hippolytus-anf5-daniel.json", "axis", "N",
     "Now we beseech you, brethren, concerning the coming of our Lord Jesus Christ",
     "paraphrase-anchored",
     "The quote is only the opening of 2 Thessalonians 2; it does not prove "
     "the Daniel/Revelation/Paul/Matthew synthesis."),
    ("hippolytus-anf5-daniel.json", "xbook", "Rev 17",
     "the great whore that sitteth upon many waters",
     "summary-inference",
     "The quote reproduces Rev 17 whore imagery but does not prove "
     "Hippolytus's Rome/Babylon identification, Dan 7 overlay, or later "
     "reception significance."),
    ("hippolytus-anf5-daniel.json", "xbook", "Rev 17",
     "The seven heads are seven mountains",
     "summary-inference",
     "The quote proves the seven-heads/seven-mountains text, but not the "
     "broader Dan 7 + Rev 17 synthesis stated in the summary."),
    ("hippolytus-anf5-daniel.json", "xbook", "Rev 20",
     "the Sabbath is the type and emblem of the future kingdom of the saints",
     "summary-inference",
     "The quote supports a future Sabbath-kingdom motif, but the rationale "
     "itself admits Hippolytus does not cite Rev 20 directly and infers the "
     "Rev 20 link from the whole schema."),
    ("hippolytus-anf5-daniel.json", "xbook", "Rev 20",
     "a day with the Lord is as a thousand years",
     "summary-inference",
     "The quote proves the thousand-years-as-day premise, but not a direct "
     "Rev 20 millennium reading."),

    # ── Newsom & Breed, OTL Daniel ────────────────────────────────────
    ("newsom-breed-otl-daniel.json", "xbook", "1 En 37-71",
     "1 En. 14:18–23 and Dan 7:9–10 provide details concerning the divine throne",
     "summary-inference",
     "The quote supports a throne-scene parallel with 1 Enoch 14, not the "
     "Similitudes' messianic Son-of-Man trajectory or Animal Apocalypse "
     "judgment parallel."),
    ("newsom-breed-otl-daniel.json", "xbook", "Rev 1; Rev 13",
     "Christ and the Ancient of Days are often conflated in medieval theology and iconography",
     "summary-inference",
     "The quote supports medieval Christ/Ancient-of-Days conflation from the "
     "OG variant, but not Rev 13 and only indirectly supports the Rev 1 "
     "reception summary."),
]


def _find_citations(doc: dict, kind: str, key: str) -> list[dict]:
    """Return the citations[] list for an axis or cross-book row.

    For ``xbook`` rows the key is matched as a startswith() against
    ``targetPassage`` so that newsom's
    ``1 En 37-71 (Similitudes/Parables of Enoch)`` resolves on the bare
    ``1 En 37-71`` key while ``Rev 13`` keeps matching exactly.
    """
    if kind == "axis":
        for pos in doc.get("positions", []) or []:
            if pos.get("axis") == key:
                return pos.get("citations", []) or []
        raise KeyError(f"axis {key!r} not found")
    if kind == "xbook":
        # Prefer exact match; fall back to startswith() for prefix keys.
        for x in doc.get("crossBookReadings", []) or []:
            if x.get("targetPassage") == key:
                return x.get("citations", []) or []
        for x in doc.get("crossBookReadings", []) or []:
            tp = x.get("targetPassage", "")
            if tp.startswith(key + " ") or tp.startswith(key + "("):
                return x.get("citations", []) or []
        raise KeyError(f"crossBookReadings target {key!r} not found")
    raise ValueError(f"unknown kind {kind!r}")


def apply_relabels(scholars_dir: Path) -> tuple[int, int, list[str], list[str]]:
    """Apply RELABELS in place. Returns (changed, no-op, errors, audit)."""
    changed = 0
    noop = 0
    errors: list[str] = []
    audit: list[str] = []

    by_file: dict[str, list[tuple[str, str, str, str]]] = {}
    for fname, kind, key, sub, new, _reason in RELABELS:
        by_file.setdefault(fname, []).append((kind, key, sub, new))

    for fname, ops in by_file.items():
        path = scholars_dir / fname
        with path.open(encoding="utf-8") as fh:
            doc = json.load(fh)
        for kind, key, sub, new_status in ops:
            try:
                cits = _find_citations(doc, kind, key)
            except KeyError as e:
                errors.append(f"{fname}: {e}")
                continue
            matches = [
                c for c in cits
                if (c.get("quote") or {}).get("text", "").find(sub) >= 0
            ]
            if not matches:
                errors.append(
                    f"{fname} [{kind} {key}]: no citation matches "
                    f"substring {sub!r}"
                )
                continue
            if len(matches) > 1:
                errors.append(
                    f"{fname} [{kind} {key}]: substring {sub!r} matches "
                    f"{len(matches)} citations (expected 1)"
                )
                continue
            c = matches[0]
            old_status = c.get("supportStatus")
            # Audit-doc rows all expect current=directly-quoted. If the
            # current state is something else (and not already the new
            # target — which would be a clean re-run), surface it loudly.
            if old_status not in ("directly-quoted", new_status):
                errors.append(
                    f"{fname} [{kind} {key}] sub={sub!r}: "
                    f"unexpected current supportStatus {old_status!r} "
                    f"(expected 'directly-quoted' per audit; new={new_status!r})"
                )
                continue
            audit_line = (
                f"  {fname} [{kind} {key}]: {old_status} -> {new_status}"
            )
            if old_status == new_status:
                noop += 1
                audit.append(audit_line + "  (no-op)")
            else:
                c["supportStatus"] = new_status
                changed += 1
                audit.append(audit_line)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return changed, noop, errors, audit


def main() -> int:
    scholars_dir = Path("docs/research/scholars")
    if not scholars_dir.exists():
        sys.stderr.write(
            f"scholars dir not found: {scholars_dir} "
            f"(run from project root)\n"
        )
        return 2

    changed, noop, errors, audit = apply_relabels(scholars_dir)

    print("Wave 1 supportStatus relabels (per "
          "docs/research/2026-04-27-wave1-codex-audit.md §2)")
    for line in audit:
        print(line)
    print(
        f"\nrelabels: {changed} applied, {noop} already correct (no-op), "
        f"{len(RELABELS)} expected"
    )
    if errors:
        print(f"errors:   {len(errors)}")
        for e in errors:
            print(f"  ! {e}")
        return 1
    if changed + noop != len(RELABELS):
        print(
            f"  ! processed {changed + noop} of {len(RELABELS)} relabels "
            f"(some did not resolve)"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
