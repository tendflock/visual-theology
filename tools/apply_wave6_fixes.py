"""Apply Wave 6.1 + Wave 6.2 codex-audit supportStatus relabels.

Driven by:

* Wave 6.1 codex audit (`/tmp/wave6-1-codex-log.txt`, verdict
  PASS_WITH_CONCERNS) — flagged the Malbim 100%-dq distribution as
  containing synthetic-profile-claim citations where the quote alone
  does not carry the rationale's sub-claim. Codex named
  "anti-Christological" and "eschatological telos" as profile-level
  framings particularly prone to this pattern. We audited Malbim's 25
  dq citations and downgrade 4.
* Wave 6.2 codex audit (`/tmp/codex-wave62-log.txt`, verdict
  PASS_WITH_CONDITIONS) — 5 dq over-applications across Bavli (×2),
  Vayikra Rabbah (×2), and Yalkut Shimoni (×1). Two more codex
  IMPORTANT findings (translation drift, anthology provenance) are
  addressed outside this script.

Mirrors the structure of ``tools/apply_wave1_relabels.py``: each row
pinpoints one citation by file + axis (or cross-book targetPassage) +
a substring of its quote.text. Idempotent: re-running on already-
relabeled files is a no-op. Exits non-zero if any expected citation is
missing or has unexpected current state — no silent skips.

Run from project root::

    python3 tools/apply_wave6_fixes.py

Total: 9 supportStatus relabels (5 from codex IMPORTANT findings,
4 from Malbim synthetic-profile-claim audit).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Each entry: (filename, kind, key, quote_substring, new_status, reason)
#   kind = "axis" or "xbook"
#   key  = axis letter, or cross-book targetPassage prefix (matched as
#          startswith)
#   quote_substring = a unique substring of the citation's quote.text
#   reason  = codex's verbatim reason from the audit log (or, for
#             Malbim audit rows, the synthetic-profile-claim
#             explanation derived by applying codex's named pattern)
RELABELS: list[tuple[str, str, str, str, str, str]] = [
    # ── Wave 6.2 codex IMPORTANT findings ────────────────────────────

    # Bavli #1: axis B pos 3 cit 0 — "the worthless kingdom" only;
    # Rome/fourth-beast tie is interpretive bridge.
    ("bavli-sanhedrin-daniel7-reception.json", "axis", "B",
     "מַלְכוּת הַזָּלָה",
     "paraphrase-anchored",
     "supportStatus: directly-quoted overstates the quote's direct "
     "force. The quote says 'the worthless kingdom' (מַלְכוּת הַזָּלָה); "
     "the position/rationale identifies this as Rome and ties it to "
     "Daniel's fourth kingdom, but that Rome/fourth-beast connection "
     "is an interpretive bridge."),

    # Bavli #2: crossBookReadings[0] cit 0 — quote ends at "today";
    # Ps 95:7 conditional resolution outruns the anchor.
    ("bavli-sanhedrin-daniel7-reception.json", "xbook", "Dan 7:13-14",
     "לְאֵימַת אָתֵי מָר",
     "paraphrase-anchored",
     "The quote is too short for the stated claim. It quotes only "
     "'when does the master come? today' (לְאֵימַת אָתֵי מָר ... הַיּוֹם), "
     "while the positionSummary relies on the Ps 95:7 resolution "
     "'today, if you hear His voice.' As-is, the citation anchors "
     "'today,' not the Torah-listening conditional interpretation."),

    # Vayikra #1: axis N pos 3 cit 4 — Lev 11 grid claim outruns
    # citation. Only camel=Babylon is anchored; rationale uses it
    # for shafan/hare/swine doubled-grid Lev 11 reading.
    ("vayikra-rabbah-13-5-daniel7.json", "axis", "N",
     "אֶת הַגָּמָל, זוֹ בָּבֶל",
     "summary-inference",
     "The rationale claims the Lev 11 unclean-animal grid is captured "
     "(including doubled swine mapping), but this citation quotes only "
     "'the camel — this is Babylon' (אֶת הַגָּמָל, זוֹ בָּבֶל); there are "
     "no per-citation anchors for shafan/coney = Media, hare = Greece, "
     "or first-swine = Persia. Quote anchors only camel=Babylon; the "
     "doubled-grid Lev 11 reading is an inference."),

    # Vayikra #2: axis O pos 4 cit 2 — ruler-parable quote lacks
    # Edom/swine language inline.
    ("vayikra-rabbah-13-5-daniel7.json", "axis", "O",
     "מַעֲשֶׂה בְּשִׁלְטוֹן אֶחָד",
     "paraphrase-anchored",
     "supportStatus: directly-quoted is too strong if this citation "
     "is meant to support 'Edom-as-swine polemic'. The quote says "
     "only the ruler-parable (מַעֲשֶׂה בְּשִׁלְטוֹן אֶחָד ... שְׁלָשְׁתָּן "
     "עָשִׂיתִי בְּלַיְלָה אֶחָד); it lacks Edom/swine language unless "
     "supplied from surrounding context."),

    # Yalkut: axis J pos 1 cit 1 — Stone-Messiah anchor supported,
    # son-of-man framing requires compositional inference from
    # חזה הוית.
    ("yalkut-shimoni-nach-1066-daniel7.json", "axis", "J",
     "וראה מלך המשיח שנאמר חזה הוית עד די התגזרת אבן",
     "summary-inference",
     "The Son-of-Man claim is stronger than the quoted anchor. The "
     "quote directly supports Stone-Messiah (Resh Lakish on Dan 2:34 "
     "splice with חזה הוית), but does not anchor בר אנש, clouds, or "
     "the Dan 7:13-14 son-of-man figure except by compositional "
     "inference from חזה הוית."),

    # ── Wave 6.1 Malbim synthetic-profile-claim audit ────────────────
    # Codex flagged the pattern but did not enumerate citations. The
    # rule applied: where the rationale's sub-claim is profile-level
    # (e.g., anti-Christological framing, anti-Maccabean architecture,
    # named-medieval-engagement) but the quote anchors only a narrower
    # exegetical point, downgrade to paraphrase-anchored.

    # Malbim P3 J C0: quote anchors corporate-Torah-elect reading;
    # the rationale's "anti-Christological" framing is overlay.
    ("malbim-on-daniel.json", "axis", "J",
     "ומלכות ה' תבא ע\"י ההשכלה בתורת ה'",
     "paraphrase-anchored",
     "Quote anchors the corporate-Torah-elect reading (kingdom of God "
     "comes via Torah-enlightenment, attributed to wise son of man). "
     "The position rationale's broader 'anti-Christological' framing "
     "is profile-level overlay, not directly quoted — codex's named "
     "synthetic-profile-claim pattern."),

    # Malbim P3 J C1: quote describes spiritual ascent; the
    # "clouds = spiritual ascent" inference requires linking the
    # quote to Dan 7:13's clouds (not in the quote).
    ("malbim-on-daniel.json", "axis", "J",
     "ראה שיתנשא במעשיו הטובים למעלה ראש עד יקרב אל האלהים",
     "paraphrase-anchored",
     "Quote describes spiritual ascent through good deeds. The "
     "section frames this as 'clouds = spiritual ascent', but the "
     "clouds-link to Dan 7:13 is inferential — the quote does not "
     "name the clouds. Synthetic-profile-claim pattern."),

    # Malbim P5 L C0: quote shows philosophical vocabulary
    # ("separated intellects"); rationale claims engagement with
    # named medieval commentators (Rashi/Ramban/Rambam/Abrabanel)
    # not anchored in this quote.
    ("malbim-on-daniel.json", "axis", "L",
     "השפעה שכליית מעולם השכליים הנפרדים",
     "paraphrase-anchored",
     "Quote anchors Malbim's philosophic vocabulary (intellectual "
     "influx from the world of separated intellects), but the "
     "position rationale's named-engagement claim (Rashi, Ramban, "
     "Rambam, Abrabanel by name; integrates Hazal) is profile-level "
     "and not anchored in this specific quote. "
     "Synthetic-profile-claim pattern."),

    # Malbim P6 A C1: quote describes vision's principal intent;
    # rationale's "Maccabean-dating thesis presupposed-rejected"
    # architecture is profile-level inference.
    ("malbim-on-daniel.json", "axis", "A",
     "עקר כונת המחזה הזאת הוא להגיד סילוק הד' מלכיות",
     "paraphrase-anchored",
     "Quote anchors the vision's principal intent (removal of four "
     "kingdoms and standing of the kingdom of heaven at the end). "
     "The position's anti-Maccabean-dating framing is profile-level "
     "architecture, not directly quoted. Synthetic-profile-claim "
     "pattern."),
]


def _find_citations(doc: dict, kind: str, key: str) -> list[dict]:
    """Return the citations[] list for an axis or cross-book row.

    For ``xbook`` rows the key is matched as a startswith() against
    ``targetPassage`` so that prefix keys like ``Ps 95`` resolve on
    ``Ps 95:7-11``.
    """
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

    print("Wave 6.1 + 6.2 supportStatus relabels (per "
          "/tmp/wave6-1-codex-log.txt + /tmp/codex-wave62-log.txt)")
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
