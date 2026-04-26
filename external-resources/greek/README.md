# Greek primary-text OCR (non-Logos resources)

Greek-language primary patristic and biblical-commentary texts that are not held in
the Logos library. Like `external-resources/pdfs/` and `external-resources/epubs/`,
these are not readable by `tools/LogosReader/Program.cs`; they need a separate
ingestion path before they can be cited under the dual-citation schema.

## Primary source: archive.org Migne PG 81

`migne-pg81-archiveorg/` (123 MB) — the canonical 1864 Migne *Patrologiae Graecae*
Volume 81 from the archive.org Google Books scan. Contains:

- `patrologiae_cursus_completus_gr_vol_081.pdf` — 1027-page scan, 119 MB
- `fts.txt` — full-text OCR (9.8 MB, mixed Greek/Latin, archive.org's own pass)
- `patrologiae_cursus_completus_gr_vol_081_hocr_pageindex.json` — page-to-byte index

**Mapping**: PDF page = (Migne col + 55) / 2. Theodoret on Daniel runs Migne PG 81
cols 1256–1546, which is PDF pages ~656–800. Verified anchors:

| PDF page | Migne col | Daniel chapter |
|---|---|---|
| 730 | 1405–1406 | VI |
| 733 | 1411–1412 | **VII (chapter opener)** |
| 740 | 1425–1426 | VII (mid) |
| 772 | 1489–1490 | X |

## Extraction tool

`extract_pg81_range.sh <first-col> <last-col> <tag>` — primary tool. Extracts the
named Migne column range from the PG 81 PDF, OCRs with `tesseract -l grc+lat`, and
emits `theodoret-pg81-<tag>.txt` with column markers preserved. Both Greek and
parallel Latin are captured (Migne's facing-column layout). Idempotent per-page
cache at `/tmp/pg81-extract-<tag>/`. Daniel-7 marker check runs at the end so
coverage of pivotal phrases (Παλαιὸς τῶν ἡμερῶν, θρόνοι ἐτέθησαν, υἱὸς ἀνθρώπου,
κέρας) is automatically visible.

```bash
# Examples
extract_pg81_range.sh 1411 1437 dan7        # Daniel 7 (already done)
extract_pg81_range.sh 1362 1410 dan5_6      # Daniel 5–6 (gap-fill)
extract_pg81_range.sh 1493 1546 dan11_12    # Daniel 11–12
```

**macOS Leptonica quirk**: tesseract on `/Volumes/External` working directory fails
with absolute paths; the script `cd`s to the cache directory before invocation.
Don't refactor that without testing.

## Inventory

| filename | author | work | source | TLG canon | coverage |
|---|---|---|---|---|---|
| `theodoret-pg81-dan7.txt` | Theodoret of Cyrus | *In visiones Danielis prophetae* | Migne PG 81 cols 1411–1437 (PDF pp. 733–747) | `4089.028` | **Daniel 7 complete** — Vers. 1 through end + Latin parallel. 4 verbatim Παλαιὸς τῶν ἡμερῶν hits, full chapter-7 vocabulary present. Extracted 2026-04-26 via `extract_pg81_range.sh`. |
| `theodoret-daniel-pg81-ocr.txt` | Theodoret of Cyrus | *In visiones Danielis prophetae* | TLG/Scribd screenshots (legacy) | `4089.028` | **Legacy reference**: Migne PG 81 cols 1256–1361 (Preface + Dan 1–3 + early Dan 4) and 1453–1492 (Dan 8 end + Dan 9 + Dan 10 start), built from 100 TLG screenshots before the canonical PDF was acquired. Superseded by `extract_pg81_range.sh` for new content; preserved for traceability. |

## Legacy: TLG-screenshot pipeline

`ingest_theodoret.sh` is the older (now superseded) one-command incremental ingestor
for Migne-PG-81 column-view screenshots from the TLG/Scribd interface. It scanned
`~/Desktop/Theodorus<N>/` folders and OCR'd new images. The screenshot folders
themselves were deleted on 2026-04-26 once the PG 81 PDF made them redundant; the
ingestor remains in this directory in case a similar TLG-export workflow is needed
in the future for a different patristic resource. For Theodoret on Daniel, prefer
`extract_pg81_range.sh`.

## OCR pipeline (reproducible)

Source images: PNG screenshots from `~/Desktop/Theodorus/`, `~/Desktop/Theodorus2/`,
`~/Desktop/Theodorus3/`, … (one fresh folder per capture session) — captured from
the TLG (Thesaurus Linguae Graecae) reading interface via Scribd. Each screenshot
shows one column of Migne PG 81. **One-command incremental ingestor**: see
`ingest_theodoret.sh` in this directory. Drop new screenshots into the
next-numbered `Theodorus<N>/` folder, then run
`external-resources/greek/ingest_theodoret.sh`. The script OCRs only new images
(per-image cache), rebuilds the master OCR text, and reports current Migne PG 81
column coverage plus a Daniel-7 marker check so progress toward Dan 7
(cols ~1452–1490) is auto-visible.

The original ad-hoc commands below are preserved for reproducibility but the
script is the maintained path.

```bash
brew install tesseract tesseract-lang        # tesseract 5.5.2 + grc (Ancient Greek)
mkdir -p /tmp/theod-ocr/up /tmp/theod-ocr/txt
cd ~/Desktop/Theodorus
i=0
for f in Screen*.png; do
  i=$((i+1)); printf -v idx '%03d' "$i"
  sips -s format png --resampleHeight 1800 "$f" --out "/tmp/theod-ocr/up/p${idx}.png"
done
cd /tmp/theod-ocr/up
for f in p*.png; do tesseract "$f" "../txt/${f%.png}" -l grc --psm 6; done
# Concatenate into one file with page markers
{
  echo "# header lines..."
  for i in $(seq -f "%03g" 1 44); do
    echo "==== screenshot p${i} ===="
    cat "/tmp/theod-ocr/txt/p${i}.txt"
  done
} > theodoret-daniel-pg81-ocr.txt
```

The macOS quirk: filenames contain a non-breaking space (` `) before `PM`,
which Tesseract+Leptonica cannot parse on the command line. Renaming to ASCII IDs
(`p001.png`, `p002.png`, …) before OCR is the workaround.

Image upscale to 1800px height markedly improved OCR quality on these column-view
screenshots; tesseract `--psm 6` (single uniform block of text) is the right
segmentation mode for Migne's two-column layout when each screenshot already shows
one column.

## OCR-quality notes

The `grc` traineddata reads polytonic Greek well but is not perfect:

- Some Greek letters are misread as their Latin lookalikes when isolated
  (e.g. column-break letters reading as `α → ω`, `υ → υ`/`ν` confusion).
- Polytonic accents survive on most words but circumflex/grave/acute can swap
  in low-contrast areas (e.g. OCR shows `ῥᾷάδιον` where the Greek is `ῥᾴδιον`).
- Migne's running headers (page footer text like
  `THEODORETUS, Interpretatio in Danielem. (4089.028)`) are captured but
  fragmented (often as `ΤΗΕΟΒΟΒΕΤΙΚ` Latin-as-Greek lookalike runs).
- Migne column numbers `(1256)`, `(1257)` are reliably preserved and serve as
  citation anchors.

For citation verification, use whitespace + typographic-punctuation normalized
matching (`tools/citations.py:_normalize`). Direct verbatim match against the OCR
text will fail too often to be useful; the normalized match is robust to ~95% of
the OCR quirks we observed in spot-checks.

## Coverage gap — Daniel 7 not yet captured

The Daniel 7 pilot's primary topic is not yet in the current capture. Dan 7 lives in
Migne PG 81 cols. 1452–1490 (approximate); the captured cols are 1256–1361
as of 2026-04-25 (Preface + Dan 1–3 + early Dan 4).

Key Daniel-7-distinctive Greek phrases absent from the current OCR (verified by
grep):

- `Παλαιὸς τῶν ἡμερῶν` (Ancient of Days, Dan 7:9, 13, 22) — 0 hits
- `ὡς υἱὸς ἀνθρώπου` (like a son of man, Dan 7:13) — 0 hits
- `θρόνοι ἐτέθησαν` (thrones were set, Dan 7:9) — 0 hits
- `κέρας` (horn, Dan 7:8 etc.) — 0 hits
- `ἕως καιροῦ καὶ καιρῶν` (until time and times, Dan 7:25) — 0 hits

To use Theodoret on the Daniel 7 pilot, additional screenshots are needed from
the Dan 7 section of PG 81. A targeted capture of cols 1452–1490 (≈ 40–50
screenshots in the same column-view format) would be sufficient. Dan 8–12
material remains a future capture.

## Citation backend

WS0c-7 schema extension (in progress) will add a `backend.kind: external-greek-ocr`
discriminator with this shape:

```json
{
  "backend": {
    "kind": "external-greek-ocr",
    "filename": "theodoret-daniel-pg81-ocr.txt",
    "tlgCanon": "4089.028",
    "mignePgVolume": 81,
    "migneColumn": 1265,
    "passageRef": "Theodoret on Dan 2:23"
  },
  "frontend": { "...standard frontend fields..." },
  "quote": { "text": "...verbatim Greek...", "sha256": "..." }
}
```

The verifier opens the OCR text, normalizes whitespace + typography, and confirms
the quote substring appears. Citation `frontend.section` for Theodoret should
follow the convention `Theodoret, In Dan., PG 81, col. {migneColumn}`.

## Provenance

- Screenshots taken by Bryan Schneider on 2026-04-25 from the TLG interface (the
  user `apollodoro87` Scribd document hosting the same TLG data)
- Migne PG 81 (1864) is public domain
- TLG itself is the University of California, Irvine subscription database; their
  text is the canonical electronic edition of Greek patristic literature
- This OCR derives from images of TLG screen output, not from any direct TLG
  data export. The OCR'd text is a derivative reading of the underlying
  Migne PG 81 Greek; for canonical citation purposes the underlying Migne column
  number is the authoritative reference, not this OCR file.
