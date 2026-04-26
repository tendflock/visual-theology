"""Apply WS0c codex-audit relabels and mismatch repairs.

Driven by the per-citation table in
``docs/research/2026-04-26-ws0c-corpus-audit.md`` §2 + the four
cross-book/coverage mismatches called out in the same audit's §6.2 +
the WS0c session handoff.

This is a one-shot record of what changed. Each row pinpoints one citation
by file + axis (or cross-book targetPassage) + the substring of its
quote.text that codex's reason names. Idempotent: re-running on already-
relabeled files is a no-op.

Run from project root::

    python3 tools/apply_ws0c_relabels.py

Total: 33 supportStatus relabels + 3 structural repairs (Goldingay
xMark 13 removal, Goldingay/Walvoord passageCoverage trim).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Each entry: (filename, kind, key, quote_substring, new_status)
#   kind = "axis" or "xbook"
#   key  = axis letter (e.g. "L") or cross-book targetPassage (e.g. "Rev 13")
#   quote_substring = a unique substring of the citation's quote.text that
#                     identifies which citation in the citations[] list
RELABELS: list[tuple[str, str, str, str, str]] = [
    # ── 1 Enoch Parables (Nickelsburg & VanderKam) ────────────────────
    ("1-enoch-parables-nickelsburg-vanderkam.json", "axis", "L",
     "exegetical conflation of several strands", "summary-inference"),
    ("1-enoch-parables-nickelsburg-vanderkam.json", "axis", "L",
     "Judaism” and “Christianity” would go their separate ways",
     "summary-inference"),
    ("1-enoch-parables-nickelsburg-vanderkam.json", "axis", "K",
     "I date the Parables between the latter part",
     "summary-inference"),
    ("1-enoch-parables-nickelsburg-vanderkam.json", "xbook", "Rev 1",
     "provides the closest parallel to the Book of Parables",
     "summary-inference"),
    ("1-enoch-parables-nickelsburg-vanderkam.json", "xbook", "Rev 1",
     "He is “one like a son of man”",
     "summary-inference"),
    ("1-enoch-parables-nickelsburg-vanderkam.json", "xbook", "1 En 37-71",
     "if these sections, and especially chap. 71, are additions",
     "summary-inference"),

    # ── Beale, Use of Daniel in Revelation ────────────────────────────
    ("beale-use-of-daniel-in-revelation.json", "xbook", "Matt 24",
     "Revelation 1:7a speaks of the eschatological coming",
     "paraphrase-anchored"),

    # ── Duguid, REC Daniel ────────────────────────────────────────────
    ("duguid-rec-daniel.json", "xbook", "Rev 20",
     "in the midst of this beastly world, our challenge is to live",
     "summary-inference"),

    # ── Hamilton, With the Clouds of Heaven ───────────────────────────
    ("hamilton-clouds-of-heaven.json", "xbook", "Rev 20",
     "thousand-year reign of Christ with his saints",
     "summary-inference"),
    ("hamilton-clouds-of-heaven.json", "xbook", "Matt 24",
     "Olivet Discourse in Matthew 24 and Mark 13 is almost a commentary",
     "summary-inference"),
    ("hamilton-clouds-of-heaven.json", "xbook", "Mark 13",
     "Mark uses a masculine participle after the neuter",
     "paraphrase-anchored"),

    # ── Jerome, Commentary on Daniel ──────────────────────────────────
    ("jerome-commentary-on-daniel.json", "xbook", "Rev 13",
     "this is the man of sin", "summary-inference"),

    # ── LaCocque, The Book of Daniel ──────────────────────────────────
    ("lacocque-book-of-daniel.json", "axis", "E",
     "later, Dan 7 was added, also in Aramaic", "summary-inference"),
    ("lacocque-book-of-daniel.json", "axis", "H",
     "corporate personality", "paraphrase-anchored"),
    ("lacocque-book-of-daniel.json", "axis", "O",
     "carried away by the heavenly decor", "paraphrase-anchored"),
    ("lacocque-book-of-daniel.json", "xbook", "Rev 13",
     "intimately associated with the Messiah in the book of Revelation",
     "summary-inference"),
    ("lacocque-book-of-daniel.json", "xbook", "1 En 37-71",
     "human righteous and elect have an individual counterpart",
     "paraphrase-anchored"),

    # ── Menn, Biblical Eschatology ────────────────────────────────────
    ("menn-biblical-eschatology.json", "axis", "F",
     "two bodily resurrections and two judgments",
     "paraphrase-anchored"),
    ("menn-biblical-eschatology.json", "axis", "J",
     "the Danielic background of Jesus' reference",
     "paraphrase-anchored"),
    ("menn-biblical-eschatology.json", "axis", "N",
     "Antichrist seen in parallels between Daniel,",
     "summary-inference"),
    ("menn-biblical-eschatology.json", "axis", "N",
     "Daniel's beasts describe four", "summary-inference"),
    ("menn-biblical-eschatology.json", "xbook", "Rev 20",
     "amillennial position best accords with the biblical data",
     "summary-inference"),
    ("menn-biblical-eschatology.json", "xbook", "Matt 24",
     "the Danielic background of Jesus' reference",
     "summary-inference"),

    # ── Pentecost, Things to Come ─────────────────────────────────────
    ("pentecost-things-to-come.json", "xbook", "Rev 17",
     "There will be a federation of ten separate kings",
     "summary-inference"),
    ("pentecost-things-to-come.json", "xbook", "Matt 24",
     "perfect harmony between that part of the Olivet discourse",
     "summary-inference"),

    # ── Theodoret, In Daniel (PG 81) ──────────────────────────────────
    ("theodoret-pg81-daniel.json", "axis", "C",
     "Σαφῶς δὲ ἡμᾶς ὁ μακάριος Παῦλος", "paraphrase-anchored"),
    # Axis E: codex says "the short OCR snippets" — all 3 citations
    ("theodoret-pg81-daniel.json", "axis", "E",
     "θαυμάζω χομιδῇ", "summary-inference"),
    ("theodoret-pg81-daniel.json", "axis", "E",
     "οἱ δὲ ἅγιοι τοῦ Ὑψίστου", "summary-inference"),
    ("theodoret-pg81-daniel.json", "axis", "E",
     "οὔτε πάντες ἅγιοι", "summary-inference"),
    # Axis J: codex names both ("foretelling an appearance" + Ps 2 incipit)
    ("theodoret-pg81-daniel.json", "axis", "J",
     "ἐπιφάνειαν προθεσπίζων", "summary-inference"),
    ("theodoret-pg81-daniel.json", "axis", "J",
     "Κύριος εἶπε πρός με", "summary-inference"),
    ("theodoret-pg81-daniel.json", "axis", "N",
     "ἀσώματος ὧν ὁ Θεὸς", "summary-inference"),
    ("theodoret-pg81-daniel.json", "xbook", "Matt 24",
     "ἐπιφάνειαν προθεσπίζων", "summary-inference"),
]


def _find_citations(doc: dict, kind: str, key: str) -> list[dict]:
    """Return the citations[] list for an axis or cross-book row."""
    if kind == "axis":
        for pos in doc.get("positions", []) or []:
            if pos.get("axis") == key:
                return pos.get("citations", []) or []
        raise KeyError(f"axis {key!r} not found")
    if kind == "xbook":
        for x in doc.get("crossBookReadings", []) or []:
            if x.get("targetPassage") == key:
                return x.get("citations", []) or []
        raise KeyError(f"crossBookReadings target {key!r} not found")
    raise ValueError(f"unknown kind {kind!r}")


def apply_relabels(scholars_dir: Path) -> tuple[int, int, list[str]]:
    """Apply RELABELS in place. Returns (changed, no-op, errors)."""
    changed = 0
    noop = 0
    errors: list[str] = []
    by_file: dict[str, list[tuple[str, str, str, str]]] = {}
    for fname, kind, key, sub, new in RELABELS:
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
            if c.get("supportStatus") == new_status:
                noop += 1
            else:
                c["supportStatus"] = new_status
                changed += 1
        with path.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return changed, noop, errors


def repair_mismatches(scholars_dir: Path) -> list[str]:
    """Apply the structural repairs called out in audit §6.2 + handoff.

    1. Goldingay xMark 13: remove the empty cross-book row AND remove
       "Mark 13" from passageCoverage[] (no anchored citation backs it).
    2. Walvoord: remove "Rev 1" from passageCoverage[] (no Rev 1
       cross-book row exists; Walvoord's Rev allusions are 4-5/13/17).
    """
    notes: list[str] = []

    g_path = scholars_dir / "goldingay-wbc-daniel.json"
    with g_path.open(encoding="utf-8") as fh:
        g = json.load(fh)
    before_xrows = len(g.get("crossBookReadings", []) or [])
    g["crossBookReadings"] = [
        x for x in g.get("crossBookReadings", []) or []
        if not (x.get("targetPassage") == "Mark 13"
                and not (x.get("citations") or []))
    ]
    after_xrows = len(g["crossBookReadings"])
    if after_xrows < before_xrows:
        notes.append("goldingay: removed empty xMark 13 row")
    if "Mark 13" in (g.get("passageCoverage") or []):
        g["passageCoverage"] = [
            p for p in g["passageCoverage"] if p != "Mark 13"
        ]
        notes.append("goldingay: removed 'Mark 13' from passageCoverage")
    with g_path.open("w", encoding="utf-8") as fh:
        json.dump(g, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    w_path = scholars_dir / "walvoord-daniel.json"
    with w_path.open(encoding="utf-8") as fh:
        w = json.load(fh)
    if "Rev 1" in (w.get("passageCoverage") or []):
        w["passageCoverage"] = [
            p for p in w["passageCoverage"] if p != "Rev 1"
        ]
        notes.append("walvoord: removed 'Rev 1' from passageCoverage")
    with w_path.open("w", encoding="utf-8") as fh:
        json.dump(w, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    return notes


def main() -> int:
    scholars_dir = Path("docs/research/scholars")
    if not scholars_dir.exists():
        sys.stderr.write(
            f"scholars dir not found: {scholars_dir} "
            f"(run from project root)\n"
        )
        return 2

    changed, noop, errors = apply_relabels(scholars_dir)
    repairs = repair_mismatches(scholars_dir)

    print(f"relabels: {changed} applied, {noop} already correct (no-op)")
    print(f"repairs:  {len(repairs)} applied")
    for r in repairs:
        print(f"  - {r}")
    if errors:
        print(f"errors:   {len(errors)}")
        for e in errors:
            print(f"  ! {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
