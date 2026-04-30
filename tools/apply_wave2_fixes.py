"""Apply Wave 2 codex-audit supportStatus relabels.

Driven by `/tmp/wave2-codex-review.md` (verdict pass-with-conditions).
Codex flagged supportStatus over-application across the five Wave 2
scholar JSONs (Cyril, Chrysostom, Victorinus, DSS, Bauckham). All
relabels move ``directly-quoted`` -> ``paraphrase-anchored`` per
codex's named recommendations and the per-axis audit codex prescribed
("relabel sampled DQ citations to paraphrase-anchored where the quote
is a biblical lemma the scholar is glossing, not their own
interpretive claim").

Mirrors the structure of ``tools/apply_wave6_fixes.py``: each row
pinpoints one citation by file + axis (or cross-book targetPassage) +
a unique substring of its ``quote.text``. Idempotent: re-running on
already-relabeled files is a no-op. Exits non-zero if any expected
citation is missing or has unexpected current state -- no silent
skips.

Run from project root::

    python3 tools/apply_wave2_fixes.py

Total: 36 supportStatus relabels (34 from H-3 + 2 added in M-3 for the
two remaining Cyril axis N art. 4870 Pauline lemmata flagged by the
H-3 codex review).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Each entry: (filename, kind, key, quote_substring, new_status, reason)
#   kind = "axis" or "xbook"
#   key  = axis letter, or cross-book targetPassage prefix (matched as
#          startswith on actual targetPassage)
#   quote_substring = a unique substring of the citation's quote.text
#   reason  = codex's verbatim reason or the audit-rule application
RELABELS: list[tuple[str, str, str, str, str, str]] = [
    # ── Cyril of Jerusalem (Cat. Lecture XV) ─────────────────────────
    # Codex named: B / C / F / J epigraph / K / Matt 24 (XV.4/6/22) /
    # Dan 12 (XV.17). Audit extends to J#3, J#4 (Dan 7 lemma quotes,
    # same pattern as the epigraph) and the cross-book Dan 2:44 lemma
    # mirror of axis K's "His kingdom shall not be left" relabel.

    ("cyril-jerusalem-catechetical-15.json", "axis", "B",
     "The fourth beast shall be a fourth kingdom upon earth",
     "paraphrase-anchored",
     "Codex: this is the Dan 7:23 lemma, not Cyril's Rome/tradition "
     "claim. The interpretive sub-claim that the fourth kingdom = "
     "Rome is in surrounding rationale, not in the quote itself."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "C",
     "brings in a certain man who is a magician",
     "paraphrase-anchored",
     "Codex: fragmentary; does not prove the full personal-Antichrist "
     "profile. The quote anchors only 'a magician' as introductory "
     "framing; the personal-Antichrist profile is composed across "
     "multiple Cyril paragraphs."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "F",
     "the dead in Christ shall rise first",
     "paraphrase-anchored",
     "Codex: biblical lemma (1 Thess 4:16) supporting one sequence "
     "element, not the whole eschatological chronology that the "
     "rationale claims."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "J",
     "I beheld till thrones were placed, and one that was ancient of days",
     "paraphrase-anchored",
     "Codex: Lecture XV epigraph (Dan 7:9, 13). Proves the verse is "
     "quoted, not Cyril's Christological identification by itself."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "J",
     "I saw in a vision of the night, and behold, one like the Son of Man",
     "paraphrase-anchored",
     "Audit extension of codex's epigraph finding: bare Dan 7:13 "
     "lemma quote. The Christological identification is Cyril's "
     "gloss in surrounding text, not in the quoted verse."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "J",
     "And to Him was given the honour, and the dominion, and the kingdom",
     "paraphrase-anchored",
     "Audit extension: bare Dan 7:14 lemma quote. The 'Son-of-Man "
     "receives universal dominion = Christ' identification is "
     "Cyril's interpretive claim, anchored elsewhere."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "K",
     "And His kingdom shall not be left to another people",
     "paraphrase-anchored",
     "Codex: Dan 2:44 / Dan 7:14 biblical proof-text fragment. Does "
     "not alone prove the anti-chiliastic polemical rationale; that "
     "is composed across Cyril's anti-chiliast paragraphs."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Matt 24",
     "Tell us, when shall these things be",
     "paraphrase-anchored",
     "Codex: Matt 24:3 lemma. Proves the verse is quoted, not "
     "Cyril's ordered Olivet synthesis."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Matt 24",
     "And ye shall hear of wars and rumours of wars",
     "paraphrase-anchored",
     "Codex: Matt 24:6 lemma; same pattern as XV.4 / XV.6 quotes."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Matt 24",
     "And then shall appear, He says, the sign of the Son of Man",
     "paraphrase-anchored",
     "Codex: Matt 24:30 lemma; XV.22 quotes the verse but the "
     "Olivet-synthesis claim spans multiple sections."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Dan 2:31-45",
     "And His kingdom shall not be left to another people",
     "paraphrase-anchored",
     "Mirror of axis K relabel: same Dan 2:44 lemma reused as a "
     "cross-book citation."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Dan 12:1-13",
     "And they shall be given into his hand until a time and times",
     "paraphrase-anchored",
     "Codex: Dan 7:25 / 12:7 lemma (XV.17). Quoted text, not Cyril's "
     "Daniel 7-12 integration rationale."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Dan 12:1-13",
     "And at that time thy people shall be delivered",
     "paraphrase-anchored",
     "Codex: Dan 12:1 lemma; quote alone does not prove the "
     "Daniel-7/Daniel-12 integration."),

    ("cyril-jerusalem-catechetical-15.json", "xbook", "Dan 12:1-13",
     "many of them that sleep in the dust of the earth shall awake",
     "paraphrase-anchored",
     "Codex: Dan 12:2 lemma; same biblical-lemma pattern as the "
     "other Dan 12 quotes."),

    # H-3 codex audit (cross-book synthesis axis N): two remaining
    # Pauline lemmata under art. 4870 still labeled DQ. The second is
    # the same 1 Thess 4:16 lemma already relabeled under axis F; axis
    # N's separate citation needs the same treatment for consistency.

    ("cyril-jerusalem-catechetical-15.json", "axis", "N",
     "For that day shall not come, except there came first the falling away",
     "paraphrase-anchored",
     "H-3 codex: 2 Thess 2:3 Pauline lemma under the cross-book "
     "synthesis axis. Quote anchors the verse-text Cyril is citing, "
     "not the integrated Daniel 7 / 2 Thess 2 / Olivet synthesis the "
     "rationale claims."),

    ("cyril-jerusalem-catechetical-15.json", "axis", "N",
     "For the Lord Himself shall descend from heaven with a shout",
     "paraphrase-anchored",
     "H-3 codex: 1 Thess 4:16 Pauline lemma. Same lemma already "
     "relabeled on axis F; axis N's separate citation under the "
     "cross-book synthesis needs the same treatment — the quote "
     "proves the verse, not the integrated parousia chronology."),

    # ── Chrysostom (Homilies on Matt 24) ─────────────────────────────
    # Codex named exactly two:
    #   axis J art. 7339 ("He shall separate them..."); biblical
    #   judgment-scene lemma supports judgment, not Son-of-Man /
    #   Danielic claim alone.
    #   axis F art. 7261 ("But of that day and hour..."); biblical
    #   lemma; Chrysostom's anti-Arian/pedagogical interpretation is
    #   in the surrounding argument.

    ("chrysostom-matt24-homilies.json", "axis", "J",
     "And He shall separate them one from another, as the shepherd",
     "paraphrase-anchored",
     "Codex: art. 7339 / Matt 25:32 judgment-scene lemma. Supports "
     "the judgment scene, not the Son-of-Man / Danielic claim "
     "alone."),

    ("chrysostom-matt24-homilies.json", "axis", "F",
     "But of that day and hour knoweth no man",
     "paraphrase-anchored",
     "Codex: art. 7261 / Matt 24:36 biblical lemma. Chrysostom's "
     "anti-Arian / pedagogical interpretation lives in the "
     "surrounding argument."),

    # ── Victorinus (Apocalypse) ──────────────────────────────────────
    # Codex named: B (5326, 5330), C (5331, 5331), A (5315), F/K/Rev 20
    # arts 5333-5338 (compositional inference), Rev 17 (5327). Axis
    # C/N row applies the same 5331 quote on both axes, so both must
    # be relabeled. Rev 20 cross-book duplicates the F/K body
    # citations; relabel both occurrences for consistency.

    ("victorinus-apocalypse.json", "axis", "B",
     "The seven heads are the seven hills, on which the woman sitteth",
     "paraphrase-anchored",
     "Codex: art. 5326 / Rev 17:9 lemma. Does not itself say Rome; "
     "the Rome identification lives in the surrounding rationale."),

    ("victorinus-apocalypse.json", "axis", "B",
     "And Daniel sets forth the ten horns and the ten diadems",
     "paraphrase-anchored",
     "Codex: art. 5330; only a Daniel/Revelation lemma bridge, not "
     "the synchronized ten-king schema the rationale claims."),

    ("victorinus-apocalypse.json", "axis", "C",
     "he speaks of Nero. For it is plain that when the cavalry sent",
     "paraphrase-anchored",
     "Codex: art. 5331; supports the Nero tradition, not the full "
     "Nero-redivivus pseudo-messiah composite."),

    ("victorinus-apocalypse.json", "axis", "C",
     "He shall not know the lust of women, although before he was most impure",
     "paraphrase-anchored",
     "Codex: art. 5331 / Dan 11:37 lemma; not sufficient for the "
     "broader Antichrist composite the rationale builds."),

    ("victorinus-apocalypse.json", "axis", "A",
     "Daniel had previously predicted his contempt and provocation of God",
     "paraphrase-anchored",
     "Codex: art. 5315 supports predictive use of Daniel, not the "
     "(anachronistic) sixth-century-authorship claim that axis A's "
     "rationale frames."),

    ("victorinus-apocalypse.json", "axis", "F",
     "the thousand years should be completed, that is, what is left of the sixth day",
     "paraphrase-anchored",
     "Codex: art. 5333 is good evidence for the received text's "
     "anti-chiliast layer, but the rationale's 'post-Victorinus / "
     "Augustinian recension' claim requires compositional "
     "inference beyond the quote."),

    ("victorinus-apocalypse.json", "axis", "K",
     "There are two resurrections. But the first resurrection is now",
     "paraphrase-anchored",
     "Codex: art. 5334 anchors the redactor's spiritualized "
     "first-resurrection reading, not the recension-layer claim "
     "that the rationale architects across multiple citations."),

    ("victorinus-apocalypse.json", "axis", "K",
     "I do not think the reign of a thousand years is eternal",
     "paraphrase-anchored",
     "Codex: art. 5335 anchors one editorial gloss; the "
     "post-Victorinus-redactor claim is compositional inference "
     "across 5333-5338."),

    ("victorinus-apocalypse.json", "axis", "K",
     "Therefore they are not to be heard who assure themselves",
     "paraphrase-anchored",
     "Codex: art. 5338 anchors the anti-Cerinthian polemic of the "
     "received text; the recension-stratum reading is "
     "compositional inference."),

    ("victorinus-apocalypse.json", "axis", "N",
     "He shall not know the lust of women, although before he was most impure",
     "paraphrase-anchored",
     "Codex C/N: same art. 5331 / Dan 11:37 lemma reused on axis N; "
     "Dan 11 lemma alone does not prove the broader Antichrist "
     "composite."),

    ("victorinus-apocalypse.json", "xbook", "Rev 17",
     "These are the five who have fallen. One remains",
     "paraphrase-anchored",
     "Codex: art. 5327; does not prove the named-emperor list in "
     "the rationale by itself."),

    ("victorinus-apocalypse.json", "xbook", "Rev 20",
     "Those years wherein Satan is bound are in the first advent",
     "paraphrase-anchored",
     "Mirror of axis F#2 (art. 5333) under Rev 20 cross-book row; "
     "same compositional-inference issue."),

    ("victorinus-apocalypse.json", "xbook", "Rev 20",
     "I do not think the reign of a thousand years is eternal",
     "paraphrase-anchored",
     "Mirror of axis K#1 (art. 5335) under Rev 20 cross-book row; "
     "same compositional-inference issue."),

    ("victorinus-apocalypse.json", "xbook", "Rev 20",
     "Therefore they are not to be heard who assure themselves",
     "paraphrase-anchored",
     "Mirror of axis K#2 (art. 5338) under Rev 20 cross-book row; "
     "same compositional-inference issue."),

    # ── DSS (Lexham Hebrew-English Interlinear, Daniel reception) ────
    # Codex named: art. 8242 (apparatus shorthand) -- relabel away
    # from DQ AND tighten translation. Other DQ citations on the
    # biblical-text-preservation pattern stand per codex ("DQ is
    # appropriate where the claim is 'this biblical verse-text is
    # preserved'").

    ("qumran-daniel-reception-lexham-dss.json", "axis", "K",
     "ג֯ב 4QDanA",
     "paraphrase-anchored",
     "Codex: art. 8242 is apparatus shorthand. Quote alone does not "
     "prove the textual-history / active-transmission claim that "
     "axis K's rationale builds; that is paraphrased from the "
     "apparatus context."),

    # ── Bauckham (Theology of Revelation) ────────────────────────────
    # Codex named axis N art. 118, axis O art. 149, and Rev 1 art. 135
    # (conditional). All three: rationale outruns the quote.

    ("bauckham-theology-revelation.json", "axis", "N",
     "John not only writes in the tradition of the Old Testament prophets",
     "paraphrase-anchored",
     "Codex: art. 118 supports the broad climax-of-prophecy thesis, "
     "not the detailed Daniel mapping listed in the rationale."),

    ("bauckham-theology-revelation.json", "axis", "O",
     "Now that the destroyers of the earth have been destroyed",
     "paraphrase-anchored",
     "Codex: art. 149 supports one Daniel-7 kingdom-transfer "
     "subclaim, not the three-stage fulfillment structure the "
     "rationale claims."),

    ("bauckham-theology-revelation.json", "xbook", "Rev 1",
     "It does not designate him a second god, but includes him",
     "paraphrase-anchored",
     "Codex (conditional): art. 135 supports divine inclusion "
     "(monotheism), not the full chiastic Alpha/Omega argument "
     "unless paired with broader context."),
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

    print("Wave 2 supportStatus relabels (per /tmp/wave2-codex-review.md)")
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
