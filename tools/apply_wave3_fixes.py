"""Apply Wave 3 codex-audit supportStatus relabels.

Driven by ``/tmp/wave3-codex-audit.md`` (verdict pass-with-conditions).
Codex flagged 35 ``directly-quoted`` over-applications across the five
Wave 3 scholar JSONs (Driver, Montgomery, Charles ICC Revelation,
Beale NIGTC Revelation, Sibylline Oracles via Charlesworth OTP).

Each row pinpoints one citation by file + axis (or cross-book
targetPassage) + a unique substring of its ``quote.text`` and downgrades
``directly-quoted`` to ``paraphrase-anchored`` or ``summary-inference``
per codex's framing (the rationale's relevant sub-claim is not pinned
to the quote alone). Mirrors the structure of
``tools/apply_wave2_fixes.py``: idempotent, exits non-zero if any
expected citation is missing or has unexpected current state.

Note on the Sibylline filename: codex's audit references the file as
``sibylline-oracles-charlesworth-otp2.json``; the H-4 session also
renames it to ``sibylline-oracles-charlesworth-otp1.json`` (resourceId
points at OTP Vol 1, ``LLS:OTPSEUD01``). The apply script uses the
post-rename filename so it must be run AFTER the rename.

Run from project root::

    python3 tools/apply_wave3_fixes.py

Total: 35 supportStatus relabels.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Each entry: (filename, kind, key, quote_substring, new_status, reason)
#   kind = "axis" or "xbook"
#   key  = axis letter, or cross-book targetPassage (matched by exact
#          equality first, then startswith)
#   quote_substring = a unique substring of the citation's quote.text
#                     (must be unique within its axis or cross-book row)
#   new_status = recommended supportStatus (paraphrase-anchored or
#                summary-inference)
#   reason  = codex's reason or a paraphrase of the rule application
RELABELS: list[tuple[str, str, str, str, str, str]] = [
    # ── Driver, Cambridge Bible Daniel ───────────────────────────────
    # Codex audit /tmp/wave3-codex-audit.md §"driver-cambridge-bible-daniel.json".

    ("driver-cambridge-bible-daniel.json", "axis", "B",
     "The great, and indeed fatal, objection to this interpretation",
     "paraphrase-anchored",
     "Codex: the quote proves Driver sees a fatal historical "
     "objection to the Roman view, but not the rationale's three-part "
     "rejection of Roman interpretation (Roman empire passed from the "
     "stage of history; ch. 8 parallels; Antiochus as limiting horizon)."),

    ("driver-cambridge-bible-daniel.json", "axis", "N",
     "is it likely that entirely different events should be measured",
     "summary-inference",
     "Codex: the quote is a rhetorical question about the same "
     "interval of time; by itself it does not prove that Daniel 7, 8, "
     "9, and 11-12 are all successive reframings of the Antiochene "
     "crisis (7:25 = 12:7 = 9:27 half-week)."),

    ("driver-cambridge-bible-daniel.json", "axis", "O",
     "The same foreshortening of the future is characteristic",
     "summary-inference",
     "Codex: the quote names foreshortening but does not alone prove "
     "the broader claim that Daniel's apparent immediacy is not a "
     "literal historical claim of imminence in 165 BCE — only that "
     "foreshortening is characteristic."),

    ("driver-cambridge-bible-daniel.json", "xbook", "1 En 37-71",
     "The earliest example of this application is found in the",
     "paraphrase-anchored",
     "Codex: the quote's 'this application' is anaphoric; it does not "
     "by itself identify the application as a personal Messianic "
     "'son of man' / Elect One reading — that referent is fixed by "
     "Driver's surrounding gloss, not the quote."),

    # ── Montgomery, ICC Daniel ───────────────────────────────────────
    # Codex audit /tmp/wave3-codex-audit.md §"montgomery-icc-daniel.json".

    ("montgomery-icc-daniel.json", "axis", "A",
     "His position as to the date of Dan. has been vindicated",
     "paraphrase-anchored",
     "Codex: the quote is anaphoric ('His position') and does not "
     "alone identify Porphyry's Maccabean thesis. Porphyry-as-vindicated "
     "is supplied by the surrounding Montgomery historiography."),

    ("montgomery-icc-daniel.json", "axis", "N",
     "Without doubt this was the primitive judaistic understanding",
     "summary-inference",
     "Codex: the quote refers to 'this' primitive understanding of "
     "Mark 14:62 but does not alone establish the personalization-"
     "into-Messiah trajectory through Enoch, NT, and rabbis."),

    ("montgomery-icc-daniel.json", "xbook", "Mark 13; Matt 24",
     "Without doubt this was the primitive judaistic understanding",
     "summary-inference",
     "Codex: same anaphoric issue as the axis-N citation. In the "
     "Mark 13 / Matt 24 cross-book row the quote alone cannot prove "
     "NT 'Son of Man' Christology mediated through Parables of Enoch "
     "and detailed NT textual tradition."),

    ("montgomery-icc-daniel.json", "xbook", "1 En 37-71",
     "The term is frequent in the Parables of Enoch",
     "paraphrase-anchored",
     "Codex: term frequency in Parables of Enoch does not alone prove "
     "that the Parables are Montgomery's primary witness to early "
     "messianic personalization or that they feed Mark 14:62 and the NT."),

    # ── Charles, ICC Revelation ──────────────────────────────────────
    # Codex audit /tmp/wave3-codex-audit.md §"charles-icc-revelation.json".

    ("charles-icc-revelation.json", "axis", "J",
     "which first applies to the Messiah, this phrase which in Dan 7:13",
     "paraphrase-anchored",
     "Codex: source-table fragment does not name 1 Enoch 46:1 in the "
     "quote itself and is syntactically dependent on omitted context."),

    ("charles-icc-revelation.json", "axis", "J",
     "Here again our author has drawn upon Daniel",
     "paraphrase-anchored",
     "Codex: 'Here again' is anaphoric; the quote does not identify "
     "what Daniel text is drawn upon or what Rev 1 feature it explains."),

    ("charles-icc-revelation.json", "axis", "F",
     "Likewise in Dan. 7:9",
     "paraphrase-anchored",
     "Codex: the quote only names Dan 7:9; it does not prove the "
     "Rev 20:4 thrones/judgment scene is grounded in Dan 7:9, 22, and 26."),

    ("charles-icc-revelation.json", "axis", "F",
     "appear to have suggested the clauses in our text",
     "paraphrase-anchored",
     "Codex: the quote says unnamed passages suggested unnamed clauses; "
     "the rationale supplies the missing Dan 7:9/22/26 and Rev 20:4 "
     "content."),

    ("charles-icc-revelation.json", "axis", "K",
     "I have sought to show in 7:1",
     "paraphrase-anchored",
     "Codex: the quote lists chapters where Charles has 'sought to "
     "show' something, but the omitted something is the source "
     "hypothesis itself."),

    ("charles-icc-revelation.json", "axis", "L",
     "I therefore assume the use of Hebrew sources by our author in this chapter",
     "summary-inference",
     "Codex: the quote proves Hebrew sources in Rev 13, not the global "
     "claim that John translated directly from the OT text — including "
     "Daniel's Aramaic — and never quoted a fixed Greek version."),

    ("charles-icc-revelation.json", "axis", "L",
     "Our text presupposes Dan. 7:9 and 1 Enoch xlvi. 1",
     "paraphrase-anchored",
     "Codex: the quote proves a Dan 7:9 / 1 Enoch presupposition for "
     "one text, but not Charles's broader Hebrew/Aramaic-versus-Greek "
     "source-method claim that John reads Daniel in Aramaic."),

    ("charles-icc-revelation.json", "xbook", "Rev 1",
     "Here again our author has drawn upon Daniel",
     "paraphrase-anchored",
     "Codex: duplicate of the anaphoric 'Here again' issue; in the "
     "Rev 1 cross-book row it cannot prove robe, girdle, eyes, voice, "
     "cloud-coming, and Son-of-Man mediation claims."),

    ("charles-icc-revelation.json", "xbook", "Rev 20",
     "Likewise in Dan. 7:9",
     "paraphrase-anchored",
     "Codex: duplicate of the axis-F relabel inside the Rev 20 "
     "cross-book row."),

    ("charles-icc-revelation.json", "xbook", "Rev 20",
     "appear to have suggested the clauses in our text",
     "paraphrase-anchored",
     "Codex: duplicate of the axis-F relabel inside the Rev 20 "
     "cross-book row."),

    ("charles-icc-revelation.json", "xbook", "1 En 37-71",
     "which first applies to the Messiah, this phrase which in Dan 7:13",
     "paraphrase-anchored",
     "Codex: duplicate source-table fragment; quote does not name "
     "1 Enoch 46:1, though the cross-book summary makes that the key claim."),

    # ── Beale, NIGTC Revelation ──────────────────────────────────────
    # Codex audit /tmp/wave3-codex-audit.md §"beale-nigtc-revelation.json".

    ("beale-nigtc-revelation.json", "axis", "C",
     "the beast is set up as the supreme enemy of Christ and his people",
     "paraphrase-anchored",
     "Codex: the quote identifies the beast with the devil himself; "
     "the position claims a transtemporal corporate Antichrist / "
     "state-agent pattern. That distinction needs contextual paraphrase."),

    ("beale-nigtc-revelation.json", "axis", "C",
     "the three elements of a blaspheming mouth, an authorization clause",
     "paraphrase-anchored",
     "Codex: the quote names only two of the claimed three Danielic "
     "elements and does not include the 'unique to Daniel in the OT' "
     "claim."),

    ("beale-nigtc-revelation.json", "axis", "J",
     "John typically adheres to and consistently develops the contextual ideas",
     "summary-inference",
     "Codex: the quote states Beale's general OT-use principle; it "
     "does not prove the Rev 1 Son-of-Man fusion, Matt 24 influence, "
     "or inaugurated reading of Rev 1:7 that the rationale claims."),

    ("beale-nigtc-revelation.json", "axis", "F",
     "the primary point of the millennium is to demonstrate the victory",
     "paraphrase-anchored",
     "Codex: victory of suffering Christians is relevant, but it does "
     "not by itself prove the Dan 7:22 dative-of-advantage / "
     "judicial-vindication reading."),

    ("beale-nigtc-revelation.json", "axis", "F",
     "executed on behalf of God",
     "paraphrase-anchored",
     "Codex: the phrase is too elliptical; it does not say what is "
     "executed, by whom, or how it maps to Dan 7:22's saints' "
     "corporate-judicial reign."),

    ("beale-nigtc-revelation.json", "xbook", "Rev 1",
     "John typically adheres to and consistently develops the contextual ideas",
     "summary-inference",
     "Codex: same general-method quote as the axis-J relabel; in the "
     "Rev 1 cross-book row it does not prove Matt 24:30 influence, "
     "Dan 10 details, or temple/lampstand claims."),

    ("beale-nigtc-revelation.json", "xbook", "Rev 13",
     "the three elements of a blaspheming mouth, an authorization clause",
     "paraphrase-anchored",
     "Codex: duplicate of the axis-C relabel in the Rev 13 cross-book "
     "row; the quote is a fragment and does not prove the three-element "
     "Danielic pattern."),

    ("beale-nigtc-revelation.json", "xbook", "Rev 20",
     "the primary point of the millennium is to demonstrate the victory",
     "paraphrase-anchored",
     "Codex: duplicate of the axis-F relabel in the Rev 20 cross-book "
     "row; relevant but not sufficient for the Dan 7:22 vindication claim."),

    ("beale-nigtc-revelation.json", "xbook", "Rev 20",
     "executed on behalf of God",
     "paraphrase-anchored",
     "Codex: duplicate of the axis-F relabel in the Rev 20 cross-book row."),

    ("beale-nigtc-revelation.json", "xbook", "Matt 24",
     "About half of the OT references in vv 7",
     "summary-inference",
     "Codex: the quote says about half of Rev 1:7-20's OT references "
     "are from Daniel; it says nothing about Matt 24:30, Synoptic "
     "mediation, false Christs, or Matt 24:13/21-24."),

    ("beale-nigtc-revelation.json", "xbook", "Matt 24",
     "midrash",
     "summary-inference",
     "Codex: the quote proves a Daniel midrash in Rev 1, not a Matt 24 "
     "reading. ('vv 7-20 may be a midrash on these two chapters from "
     "Daniel')"),

    ("beale-nigtc-revelation.json", "xbook", "Mark 13",
     "John typically adheres to and consistently develops the contextual ideas",
     "summary-inference",
     "Codex: the quote is Beale's general OT-context principle; it "
     "does not mention Mark 13, Mark 14:62, AD 70, or Synoptic "
     "mediation."),

    ("beale-nigtc-revelation.json", "xbook", "1 En 37-71",
     "Hendriksen",
     "summary-inference",
     "Codex: the clearest quote-to-claim mismatch in Wave 3. The quote "
     "is about Hendriksen and seven world empires, not 1 Enoch 37-71. "
     "The 'Lord of lords, God of gods, King of kings' title in 1 En 9:4 "
     "is not the quote's subject."),

    # ── Sibylline Oracles (via Charlesworth OTP 1) ───────────────────
    # Codex audit /tmp/wave3-codex-audit.md §"sibylline-oracles-charlesworth-otp2.json".
    # NOTE: the audit references the pre-rename filename. After H-4
    # Phase 3 the file is at sibylline-oracles-charlesworth-otp1.json
    # (resourceId LLS:OTPSEUD01 = OTP Vol 1).

    ("sibylline-oracles-charlesworth-otp1.json", "axis", "C",
     "Then Beliar will come from the Sebast",
     "paraphrase-anchored",
     "Codex: the quote proves only the phrase 'Beliar... from the "
     "Sebastenoi'; the Nero/Augusti interpretation and Ascension of "
     "Isaiah parallel are interpretive context."),

    ("sibylline-oracles-charlesworth-otp1.json", "axis", "K",
     "The composite nature of the book has been recognized",
     "summary-inference",
     "Codex: composite nature alone does not prove the detailed dates, "
     "provenance, or strata assigned to Sib Or 3 and Sib Or 4."),

    ("sibylline-oracles-charlesworth-otp1.json", "axis", "K",
     "The hellenistic oracle is important as a specimen of anti-Macedonian",
     "summary-inference",
     "Codex: the quote supports anti-Macedonian political prophecy "
     "but not the full before/after-Common-Era Daniel-7 reception "
     "range claimed by the rationale."),
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
        for x in doc.get("crossBookReadings", []) or []:
            tp = x.get("targetPassage", "")
            if tp.startswith(key):
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
        if not path.exists():
            errors.append(f"{fname}: file not found at {path}")
            continue
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
            if old_status not in ("directly-quoted", new_status):
                errors.append(
                    f"{fname} [{kind} {key}] sub={sub!r}: "
                    f"unexpected current supportStatus {old_status!r} "
                    f"(expected 'directly-quoted'; new={new_status!r})"
                )
                continue
            audit_line = (
                f"  {fname} [{kind} {key}]: {old_status} -> {new_status}"
                f"  ::  {sub[:60]}"
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

    print("Wave 3 supportStatus relabels (per /tmp/wave3-codex-audit.md)")
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
