# OCR-prep notes — German Wave 7 (Luther / Daniel-Vorrede)

Session date: 2026-05-01
Tool: `tools/extract_ocr.sh` (Wave 6.3 / Wave 7 generalised pipeline,
post-`archive-text` URL-fix patch dated 2026-05-01).
Tesseract `deu` and `frk` traineddata: confirmed installed.

This file accompanies the German OCR-prep run for the Luther row of the
Wave 7 patristic-reformation full-text audit
(`docs/research/2026-04-28-patristic-reformation-fulltext-audit.md`,
§2.11). Per the D-1.6 reframing, Luther's Daniel preface ships with **two**
source surfaces:

1. **Canonical critical** — Weimarer Ausgabe Deutsche Bibel Bd. 11/II
   (Bd.11:Hlft.2 c.1, 1906). Modern Antiqua typesetting in the WA's
   editorial frame around the Luther original. OCR engine: `deu`.
2. **Witness / acquisition** — *Biblia. Das Ist, Die Gantze Heilige
   Schrifft, Deudsch Auffs New Zugericht. Wittenberg, 1545* (Hans Lufft
   printing). 16th-century Fraktur. OCR engine: `frk` (the homebrew
   tesseract-lang ships Fraktur as `frk`, not `deu_frak`; the per-language
   README has the standing note).

The two outputs are not redundant: the WA is the scholarly-critical surface
that Wave 7 quote-citation should anchor against, while the 1545 Bibel is
the printing-witness surface that confirms the printed-form text the WA
edits. A citation that quotes the German with the WA spelling is
load-bearing on the WA file; a citation that quotes the 1545 Wittenberg
spelling is load-bearing on the 1545 file.

## Per-voice status

### 1. Luther WA DB 11/II (canonical critical surface) — **clean / acceptable** ✅

- File: `luther-vorrede-wa-db-11-ii.txt`
- Source: `https://archive.org/download/diedeutschebibel1121unse/diedeutschebibel1121unse.pdf`
  (43 MB Text PDF, archive.org metadata: title "Die deutsche Bibel.",
  volume "Bd.11:Hlft.2 c.1", date 1906).
- Coverage: full volume, pdfinfo-reported 568 OCR'd pages.
- Size: 1.5 MB / 26,480 lines.
- Quality verdict: **acceptable / readable** under `deu`. Codex review
  (2026-05-01) downgraded the prior "clean / exemplary" framing: the
  long-s / `ſ`-`f` confusions (`ſein` ↔ `fein`, `ſol` ↔ `fol`) and
  ß-rendering wobble appear **broadly**, not only in Luther-quotation
  pull-out blocks. The WA's Antiqua editorial frame is cleaner than the
  Fraktur set-text passages but still carries the noise. Treat the file
  as anchor-finding-grade, not verbatim-quotation-grade — see "Survey-side
  caveat" below.
- Daniel-Vorrede locator: codex sampling places the *Vorrede über den
  Propheten Daniel* critical text around PDF p. 160 onward in the
  volume; survey side should grep on "Vorrede über den Propheten Daniel"
  + "Daniel etliche jar vor der" + "vier Königreichen" anchors that
  span both 1530 and 1541 versions in the WA's apparatus.
- Non-citation pages (skip for any quote-anchoring work):
  - **Front matter**: PDF pages 1-3 are binding-cover and verso scans
    that OCR as garbage glyphs ("Hin / / Hi / / / / IN ...").
  - **Back matter**: PDF pages 565-568 are end-flyleaf and back-cover
    scans, also garbage. Codex sampling confirms.
  - The output's `==== PDF page 0001 ====` … `0003 ====` and
    `0565 ====` … `0568 ====` blocks should be ignored.

### 2. Luther 1545 Wittenberg Bibel — Daniel preface (witness surface) — **acceptable** ⚠️

- File: `luther-1545-bibel-vorrede.txt`
- Source: `https://archive.org/download/1545-biblia-wittenberg/1545%20Biblia%2C%20Wittenberg.pdf`
  (411 MB Image Container PDF, 1535 pages of 600-DPI Fraktur scans).
- Coverage: **PDF pages 915-938** only (24 pages). The Daniel preface
  starts on p. 916 ("DVorredeyber den Propheten CIU. / Daniel ZD. art,
  Lutber,") and continues through the end of p. 937; p. 938 is the
  beginning of Daniel ch. 1 ("Der Prophet Daniel. CXIIII. dritten jar
  des Weichs Jolakum…"). The OCR range deliberately includes one
  flanking page on either side for safe boundary capture. **Full-Bible
  Fraktur OCR was out of scope** for this 1-2h session: 1535 Fraktur
  pages × ~30s each = ~13h of OCR wall time, dwarfing the session
  budget. The Daniel-preface slice covers the witness surface the audit
  actually requires.
- Page-range derivation: fetched the archive.org `_djvu.xml` (61 MB)
  directly; the 1535 page-objects were searched for the WORD-content
  combination `"Vorrede" + "Daniel" + "Mart" + "Luther"`, which uniquely
  matched page 916. End-of-preface confirmed by inspecting pp. 936-940
  for the chapter-1 incipit ("dritten jar des Reichs Joiakim"). The
  djvu.xml-based locator is the right pattern for any future
  Daniel-preface-only slice of a Bible-scale Fraktur scan.
- Size: 103 KB / 1,468 lines across 24 pages.
- Codex spot-check (2026-05-01) confirmed boundaries: PDF p. 915 is the
  Ezekiel tail, p. 916 begins the Daniel preface, p. 937 ends with the
  preface's "AMEN", p. 938 begins Daniel ch. 1 ("Der Prophet Daniel.
  CXIIII. dritten jar des Reichs Joiakim…").
- Quality verdict: **acceptable** Fraktur OCR.
  - Anchor phrases preserved: "Vorrede vber den Propheten Daniel",
    "D. Mart. Luther", "vier Königreichen" / "vier könige", "Nebucad
    Nezar", "Antiochus", "Vmb dieſes Scheimen", "Ptolemeus
    Philometor".
  - Decorative drop-caps at section starts OCR as garbage (e.g.
    `DVorredeyber`, `ZD. art, Lutber` on page 916 — the `D` and `M.`
    initials are decorated woodcut letters); avoid these as quote
    anchors.
  - Long-s/round-s confusions throughout: `ſ`-rendered glyphs interleave
    with `f`/`ſ`/`s` outputs; survey citations should normalise via
    NFC + manual eszett review per the German README §"Extraction
    pattern".
  - Page-edge ornament noise ("/Î/Ï/" type artefacts) on every page from
    decorative borders in the 1545 print; these are harmless but bloat
    the line count.
- The 1545 Bibel files include `1545 Biblia, Wittenberg_text.pdf`
  (501 MB Additional Text PDF) and `1545 Biblia, Wittenberg_djvu.txt`
  (4.2 MB pre-extracted plain-text). The djvu.txt is the archive's own
  Fraktur OCR pass and is roughly comparable in quality to a fresh `frk`
  pass; we used `frk` directly for parity with the rest of the German
  pipeline and to honour the dispatch instruction.
- Output filename note: the source PDF's filename contains a literal
  space and comma (`1545 Biblia, Wittenberg.pdf`). The script's
  URL-validator rejects spaces; the URL-encoded form
  (`%20`/`%2C`) passes. No pre-link-cache workaround was needed.

## WA-canonical vs 1545-witness — citation routing

For the Wave 7 Luther row, anchor citation backends to:

- `german/luther-vorrede-wa-db-11-ii.txt` when quoting in WA-edited
  Antiqua/Fraktur orthography (e.g. "vier Königreichen" with modern
  ä/ö/ü), OR when the citation is a textual variant the WA editors
  themselves identify.
- `german/luther-1545-bibel-vorrede.txt` when quoting in 1545 Wittenberg
  print orthography (e.g. "vier Königreich" without umlauts, with
  combining-e diacritics), OR when the citation is doing 16th-c.
  printing-witness work.

Both files are valid for the same Luther voice; choice of surface depends
on what the citation is doing.

## Pipeline observations (carry-forward to next OCR-prep)

- The `archive-text` URL-fix patch (2026-05-01, `/stream/`→`/download/`
  + HTML-sniff) was applied mid-session. It does **not** affect the
  `pdf` codepath that this session used for both German voices. The
  WA OCR run was unaffected by the tool change; cache-honouring let
  the post-patch re-invocation regenerate the output identically in
  seconds.
- For Bible-scale Fraktur scans (1500+ pages), the
  djvu.xml-WORD-content-search pattern is the right page-range
  locator. Fetching the XML costs 60 MB of one-shot bandwidth and
  saves ~12h of pointless full-volume OCR. Document this pattern for
  future witness-surface slices.
- Fraktur drop-caps at section starts OCR as garbage. Survey-side
  citation anchoring should pick a phrase 5-10 words past any chapter
  or section initial.
- DPI 200 against a 600-DPI scan downsamples 3x; per-page Fraktur
  reads cleanly enough. Bumping to `--dpi 300` would marginally
  improve quality at ~2x wall-clock cost; not worth it for this
  witness use case.

## Survey-side caveat

Both files are **anchor-finding-grade** OCR, not **verbatim-quotation-grade**.
A survey citation that pulls a verbatim German quote from either file
must be verified against the printed page (WA DB 11/II for the canonical
critical surface; the 1545 Wittenberg Bibel facsimile for the witness
surface) before the citation is treated as final. The OCR is good enough
to locate where Luther says what; it is not good enough to reproduce
exactly how he said it. This is the standard Wave 7 OCR-prep posture
(see Latin precedent in `external-resources/latin/_OCR-PREP-NOTES.md`).

## Summary verdict

| Voice | OCR'd this session | Quality | Output |
|---|---|---|---|
| Luther WA DB 11/II | ✅ full PDF (568 pp, `deu`) | acceptable / readable (broad ſ/f/s noise per codex) | `luther-vorrede-wa-db-11-ii.txt` (1.5 MB / 26,480 lines) |
| Luther 1545 Bibel — Daniel preface | ✅ PDF pp. 915-938 (`frk`) | acceptable (Fraktur typical; preface boundaries codex-verified) | `luther-1545-bibel-vorrede.txt` (103 KB / 1,468 lines) |

**Both Luther source surfaces** prepped this session. The Wave 7 Luther row
is unblocked for survey dispatch, with the verbatim-verification caveat
above.

## Codex review (2026-05-01)

- Verdict: **pass-with-conditions**.
- Sampling: WA pp. 80-84, 130-134, 160-161, 205-210, 470-476, 565-568;
  1545 Bibel pp. 915, 916, 937, 938 boundary-checked.
- Conditions applied to this notes file in the same session:
  - Line-count fix for `luther-1545-bibel-vorrede.txt` (1,468, not 1,860).
  - Broadened WA non-citation page list (pp. 1-3 and 565-568).
  - Downgraded "clean / exemplary" WA framing to "acceptable / readable".
  - Added the survey-side verbatim-verification caveat above.
- No file modifications by codex (read-only sandbox).
