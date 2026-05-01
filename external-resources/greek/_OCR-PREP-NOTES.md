# OCR-prep notes — Greek Wave 7 voices

Session date: 2026-05-01
Tool: `tools/extract_ocr.sh` (Wave 6.3 / Wave 7 generalised pipeline)
Tesseract `grc` + `lat` traineddata: confirmed installed.

This file accompanies the Greek OCR-prep run that fed the Wave 7 survey-dispatch
queue. It records per-voice quality verdicts, the column-to-page formula
empirically derived for PG 13, and the honest gap on Origen's PG 13 Daniel
surface that the pre-session audit flagged.

The existing Theodoret PG 81 files (`theodoret-pg81-dan*.txt`,
`theodoret-daniel-pg81-ocr.txt`) are out of scope for this session and were
not modified.

## Per-voice status

### 1. Origen — PG 13, *Selecta in Ezechielem* CAP. XIV — **clean** ✅

- File: `origen-pg13-daniel-fragments.txt` (29.5 KB / 321 lines / 4 PDF pages)
- Source: Migne PG 13 (Origen vol. 3) via archive.org
  `patrologiae_cursus_completus_gr_vol_013` — full PDF (93 MB).
- Extraction: `extract_ocr.sh pdf-columns 805 810 grc+lat ... --col-formula "(col + 45) / 2" --dpi 300 --psm 4`.
- PDF page range: 425-428; Migne PG 13 column range: 805-810.
- Quality: clean Greek + Latin parallel-column OCR. Daniel keyword density:
  `Δανι` 6 hits, `Δανιὴλ`/`Δανιήλ` 3+3 hits, `Νῶε` 5 hits, `Daniel` (Lat) 7
  hits. The captured block is the Ezek 14:14 Noah-Daniel-Job typology — the
  canonical Origen-on-Daniel reception locus. Greek is readable; the small
  body of text means a single fresh OCR pass at 300 DPI psm 4 was sufficient.

#### Pre-session audit caveat — confirmed

The pre-session patristic-Reformation audit flagged Origen's PG 13
Daniel surface as `VERIFIED` on volume-availability + `INFERRED` on
column-locations. **This session confirmed the audit's posture: PG 13
contains no contiguous "Selecta in Danielem" block.** Direct grep of
archive.org's `_djvu.txt` for "Δανιήλ" / "Δανι" / "Daniel" returned only
6 scattered allusions across the 11.3 MB whole-volume text:

| djvu line | PDF page (probed) | Migne PG 13 col | Context |
|---|---|---|---|
| 20474 | ~267 (pageindex unreliable) | unknown | *Selecta in Jeremiam* — passing reference |
| 49228 | unknown | unknown | passing allusion in *Selecta in Threnos* / *In Lamentationes* |
| 63170 | **426** (verified by direct probe) | **807** | *Selecta in Ezechielem* cap. XIV — **Noah-Daniel-Job typology, Ezek 14:14** |
| 63192 | **426** (same block) | **807** | continuation of same Ezek 14:14 commentary |
| 97274 | unknown | unknown | *Comment. in Matt.* — passing reference |
| 113481 | unknown | unknown | *Comment. in Matt.* tom. XVI/XVII — passing reference |

Of the 6 Daniel hits, only the Ezek 14:14 cluster (lines 63170-63192,
PDF p. 426, col 807) is a substantive Daniel-engaging passage. The
remaining 5 are passing allusions — useful as cross-reference anchors
but not freestanding citation surface.

This file therefore **captures only the Ezek 14:14 cluster** (cols
805-810 = PDF pp. 425-428, with one page of buffer either side of col
807 to capture the surrounding Ezek-13 / Ezek-14 commentary that anchors
the Noah-Daniel-Job passage). Wave 7 dispatch should treat the other 5
Daniel hits in PG 13 as "look-up the column number first, then re-extract
in a follow-on session" — they are not in this file.

#### What's not in PG 13 (per audit)

The audit explicitly noted the prior research's "PG 13 *Selecta in
Danielem*" claim was incorrect. The closest thing PG 13 contains is
Origen's Selecta-tradition on the prophets generally, with Daniel
appearing in cross-reference and allusion only. The audit's recommended
Origen-on-Daniel surface for the Daniel 7 pilot is **CCEL Origen *Contra
Celsum*** via the `external-html` backend (work-slug pattern,
`https://ccel.org/ccel/origen/against_celsus/...`) — a separate
acquisition path not handled by this OCR-prep session.

### 2. Cyril of Alexandria — Mai *Nova Bibliotheca Patrum* tom. 2 pp. 467-468 — **acceptable** ✅

- File: `cyril-alexandria-daniel-fragments-greek.txt` (10.6 KB / 178 lines / 3 PDF pages)
- Source: Mai *Nova Patrum Bibliotheca* tom. 2 (Rome, 1844) via archive.org
  `bub_gb__VlU6XtRKPgC` — full PDF (37 MB).
- Extraction: `extract_ocr.sh pdf <url> grc+lat <output> --pages 485-487 --psm 4 --dpi 300`.
- PDF page range: 485-487; book page range: 467-469.
  - Book p. 467 (PDF p. 485 bottom): "In catena a nobis edita ad Danielem,
    editionis principis p. 195, et seq." — header + opening of the Daniel
    fragment block.
  - Book p. 468 (PDF p. 486): main Daniel-fragment body — `παλαιοῦ τῶν ἡμερῶν
    ἔφθασιν` (Ancient of Days reached/came, Dan 7:13-22) + `Βιβλοι ἐνεύχϑησαν`
    (Books were opened, Dan 7:10) + the *contra pneumatomachos* fragments
    that the Mai TOC entry "XIII. In proverbia, Danielem, et contra
    pneumatomachos fragmenta p. 467-468" packages with the Daniel material.
  - Book p. 469 (PDF p. 487): start of the next work, `HOMILIA DE PARABOLA
    VINEAE` — included as a boundary marker; not Daniel content.
- Quality: acceptable Greek + Latin parallel-column OCR. Daniel keyword
  density: `Daniel` (Lat) 1 hit, `Παλαι` 1 hit, `ἡμερῶν` 1 hit, `Cyril/Κυριλλ`
  7 hits. Greek polytonic accents survive; some Greek letter forms are mangled
  in low-contrast areas (typical of 1844 typography).

#### Page-mapping correction

archive.org's `hocr_pageindex.json` for Mai vol. 2 was off by ~6 PDF pages
(reported PDF p. 491-493 for book pp. 467-468; the actual content lives on
PDF p. 485-487). Empirical probe via `pdftoppm -r 200 + tesseract -l grc+lat`
on candidate PDF pages 484-490 located the correct range by content
matching. **Future extractions from this volume should ignore the
hocr_pageindex and probe PDF pages directly against the book-page running
header.** The extract_ocr.sh `pdf` subcommand's `--pages N-M` flag accepts
any PDF page range; the cache is idempotent (re-runs with corrected ranges
re-OCR only new pages).

#### Greek/Latin interleaving

Mai vol. 2 prints Greek and Latin in parallel two columns (Latin left,
Greek right). At `--psm 4` (single column of variable text), tesseract
reads the page row-by-row and **interleaves** Latin and Greek lines in
the output: each line carries a Latin sentence followed by its Greek
parallel, separated by whitespace. The Wave 7 dispatch should expect
this format. Strategies:

1. Anchor citations on Greek text only. Greek lines tend to start with
   non-ASCII characters (`Κ`, `π`, `ϑ`, etc.); a `[^ -~]` regex isolates
   them.
2. Anchor citations on Latin text only when Greek OCR mangles the
   anchor. Latin parallel column is cleaner here than the Greek (matching
   the `lat` traineddata's stronger 19th-c. Latin support).
3. Document interleaved anchor pairs so quote.text + a parallel
   Latin-language translations[] entry can both be verified.

### Summary verdict

| Voice | OCR'd this session | Quality | Output | Daniel keyword hits |
|---|---|---|---|---|
| Origen PG 13 (Selecta in Ezech. cap. XIV) | ✅ pdf-columns 805-810 | clean | `origen-pg13-daniel-fragments.txt` (29.5 KB) | Δανι 6, Δανιὴλ 3, Νῶε 5, Daniel 7 |
| Cyril Mai vol. 2 pp. 467-468 | ✅ pdf 485-487 | acceptable | `cyril-alexandria-daniel-fragments-greek.txt` (10.6 KB) | Daniel 1, Παλαι 1, ἡμερῶν 1, Κυριλλ 7 |

Both voices completed scripted OCR-prep this session. No deferred /
manual-download voices in the Greek bucket.

## Tesseract grc + lat language pack

Confirmed installed (from prior Theodoret precedent — no fresh install
needed). Verified at session start via `tesseract --list-langs`.

## Migne PG column→page formulae

| Volume | Formula | Verified by |
|---|---|---|
| PG 13 (Origen vol. 3) | `PDF page = (col + 45) / 2` | Probed PDF p 400 (col 755), p 414 (col 783), p 425 (col 805), p 426 (col 807) — all match |
| PG 81 (Theodoret) | `PDF page = (col + 55) / 2` | Existing `extract_pg81_range.sh` — unchanged |

Different volumes have different front-matter offsets; pass `--col-formula`
to `extract_ocr.sh pdf-columns` for each PG / PL volume.

## Pipeline observations (for future Greek OCR-prep sessions)

- **archive.org `hocr_pageindex.json` is unreliable as a PDF-page index.**
  For Mai vol. 2 the offset was ~6 pages; for PG 13 the offset was inconsistent
  across the volume (works are concatenated with their own page numbering and
  the index appears to use one of them, not the canonical PDF page count).
  Always probe candidate PDF pages directly with `pdftoppm + tesseract`
  against a known content-string before committing to a page range.

- **`--psm 4` + 300 DPI is the right default** for Migne / Mai parallel
  Greek+Latin two-column layouts. The `pdf` subcommand defaults to `--psm 6`
  + 200 DPI, which mangles two-column text by reading across columns row-by-
  row. The `pdf-columns` subcommand correctly defaults to `--psm 4` for this
  reason.

- **Greek polytonic accents** survive OCR at 300 DPI for clean pages but
  swap circumflex/grave/acute on low-contrast pages (matching the
  Theodoret PG 81 OCR's quirks documented in `README.md`). Citation
  matching at quote-anchor time should use `tools/citations.py:_normalize`
  whitespace + casefold + Unicode NFC.

- **Pre-session audit caveats matter.** The Origen PG 13 row in the
  patristic-Reformation audit explicitly flagged the Daniel-fragment
  column-locations as `INFERRED, not VERIFIED`. This session confirmed
  the audit was right: PG 13 has no contiguous Daniel block. Honest
  documentation of that gap is the deliverable, not a fabricated
  contiguous-block extraction.

## Implications for Wave 7 survey dispatch

- **Origen PG 13** survey should anchor on the Ezek 14:14 Noah-Daniel-Job
  typology in this file. Other 5 PG 13 Daniel hits are passing allusions;
  if the survey wants to capture them, a follow-on session must first
  pin their PDF page numbers (audit's recommended tightening step).
- **Origen *Contra Celsum*** via CCEL HTML backend remains the audit-
  recommended primary Origen-on-Daniel surface for the Daniel 7 pilot —
  separate acquisition path, not handled by this OCR-prep session.
- **Cyril Mai vol. 2** survey should anchor on the *Ancient of Days* and
  *Books were opened* citations in this file (Dan 7:9-13, 7:10). The
  whole-volume djvu.txt in `external-resources/latin/cyril-alexandria-daniel-fragments.txt`
  remains the broader index, but the Greek body in this file is the
  citation-grade surface for Greek-language quote anchors.

## Out-of-scope workspace state — *not* this session's changes

`git status --short` at session start (per the SessionStart snapshot)
showed several pre-existing untracked / modified paths outside
`external-resources/greek/`. This Greek session wrote only to
`external-resources/greek/`:

- `cyril-alexandria-daniel-fragments-greek.txt` (untracked, this session)
- `origen-pg13-daniel-fragments.txt` (untracked, this session)
- `_OCR-PREP-NOTES.md` (untracked, this session — this file)

The existing committed Theodoret PG 81 files
(`theodoret-pg81-dan*.txt`, `theodoret-daniel-pg81-ocr.txt`,
`extract_pg81_range.sh`, `ingest_theodoret.sh`, `migne-pg81-archiveorg/`,
`README.md`) were not modified by this session. Confirmed via
`git status --short -- external-resources/greek/` and
`git diff -- external-resources/greek/`.
