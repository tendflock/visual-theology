# external-resources/

Texts that are **not** in the Logos library and therefore cannot be read via
`tools/LogosReader/Program.cs`. Each per-language subdirectory holds the
plain-text outputs that the `external-ocr` citation backend
(`tools/citations.py:_load_ocr_text`) reads at verification time.

| Subdir | Languages | Used by | Notes |
|---|---|---|---|
| `greek/` | grc | Theodoret PG 81, planned Origen / Cyril | parallel Greek+Latin Migne layout |
| `latin/` | la  | Gregory PL 75/76, Bullinger, Œcolampadius, Pellican, Melanchthon, Lambert, Mede | long-s pitfall in pre-1800 scans |
| `german/` | de | Luther WA DB 11/II, 1545 Wittenberg Bibel | Fraktur (`frk`) for 16th-c. printing |
| `hebrew/` | he | Abrabanel, Ralbag (when off Sefaria) | NFC normalization mandatory |
| `aramaic/` | arc | Targumic / Talmudic-Aramaic OCR (sparse for Daniel) | shares `heb` traineddata |
| `judeo-arabic/` | jrb | Yefet ben Eli (Margoliouth 1889), Saadia Tafsir | Hebrew script |
| `french/` | fr  | reserved (no audited Wave 6/7 voice) | provisioned, empty |
| `pdfs/` | mixed | external-pdf backend | uses `pdftotext`, not OCR |
| `epubs/` | mixed | external-epub backend | uses `unzip` + HTML strip |
| `sefaria-cache/` | he/en | external-sefaria backend | API responses, gitignored |

## OCR pipeline overview

Two scripts produce the plain-text the verifier reads:

1. **`external-resources/greek/extract_pg81_range.sh`** — Theodoret-specific
   convenience wrapper. Hard-codes the PG 81 PDF path, the column-to-page
   formula, and a Daniel-7 marker check. Kept as-is for backward compatibility
   with existing Theodoret regenerations.
2. **`tools/extract_ocr.sh`** — generalised successor. Handles every
   audited input format from Wave 6.3 (Hebrew + Judeo-Arabic) and Wave 7
   (Latin + German + Greek + English) source documents.

For new voices, use `tools/extract_ocr.sh`. The Theodoret-specific script
is preserved but should be considered frozen.

## Format-coverage map

`tools/extract_ocr.sh` ships four subcommands; each maps to one acquisition
shape from the D-1.5 / D-1J audits:

| Subcommand | Audited use case | Source-host examples |
|---|---|---|
| `pdf` | Single-volume scan; OCR every page or a `--pages` slice | archive.org, e-rara, MDZ/BSB digitale-sammlungen.de, Google Books `?output=pdf` |
| `pdf-columns` | Migne-shaped two-column volume; col-range OCR | Migne PG 13, PG 70, PG 75/76, PG 81; PL volumes by overriding `--col-formula` |
| `archive-text` | archive.org `_djvu.txt` plain-text already exists | Yefet ben Eli `commentaryonbook00japhuoft`, Mai vol. 2 `bub_gb__VlU6XtRKPgC` |
| `html` | CCEL / online-only HTML sources | Origen *Against Celsus* via CCEL work-slug pattern |

### Sources that are not directly fetchable

Some hosts block scripted access. For these, download in a browser, stage
the PDF under the right per-language subdirectory, and run `extract_ocr.sh
pdf` against a `file://` cache by pre-linking the cache. (See "Pre-linking
the cache" below.)

| Host | Block | Workaround |
|---|---|---|
| HebrewBooks.org | Cloudflare challenge | manual browser download, then pre-link cache |
| e-rara.ch | JS challenge on titleinfo pages | manual download via the viewer's PDF export, then pre-link cache |
| MDZ / digitale-sammlungen.de | intermittent "error while serving" | retry, or use the IIIF / URN resolver path |
| Google Books | country-sensitive `?output=pdf` | retry from a different network or pre-stage |

## Per-use-case run instructions

### Greek — Migne PG column range (Theodoret precedent)

```bash
tools/extract_ocr.sh pdf-columns \
  https://archive.org/download/patrologiaecursusxx81mign/patrologiae_cursus_completus_gr_vol_081.pdf \
  1411 1437 grc+lat \
  external-resources/greek/theodoret-pg81-dan7.txt
```

The `grc+lat` language pair captures both columns of the parallel Migne
layout. `--psm 4` is the default for `pdf-columns` and reads two-column
pages best.

For a different Migne volume whose column-to-page formula differs (PG 13,
PG 70, PG 76 all have different front-matter offsets), measure two known
column → page mappings empirically, then derive the formula and pass it:

```bash
tools/extract_ocr.sh pdf-columns \
  https://archive.org/download/<id>/<file>.pdf \
  <first-col> <last-col> grc+lat <output> \
  --col-formula "(col + 49) / 2"
```

### Latin — Reformation PDF (e-rara, BSB, archive.org)

```bash
tools/extract_ocr.sh pdf \
  https://archive.org/download/bim_early-english-books-1641-1700_bullinger-heinrich_1571_0/bim_early-english-books-1641-1700_bullinger-heinrich_1571_0.pdf \
  lat \
  external-resources/latin/bullinger-1571-apoc.txt
```

Pre-1800 Latin scans suffer long-s (ſ) → `f` substitution; after OCR,
spot-check the output for `f`-where-`s`-should-be in citation anchors and
either pick a different anchor or post-process. The audit's
`§4d Latin-OCR normalization caveat` enumerates the period-orthography
quirks the OCR-prep pipeline should handle (long-s, æ/œ ligatures,
abbreviations, u/v + i/j orthography).

### German — Fraktur (Luther 1545 Bibel, WA DB volumes)

```bash
tools/extract_ocr.sh pdf \
  https://archive.org/download/diedeutschebibel1121unse/diedeutschebibel1121unse.pdf \
  deu+frk \
  external-resources/german/luther-wa-db-11-2.txt \
  --pages 1-50
```

`frk` is the Fraktur traineddata (homebrew tesseract-lang ships it as `frk`,
not `deu_frak`); `deu+frk` reads modern + Fraktur mixed text best.

### Hebrew — HebrewBooks (manual download path)

HebrewBooks blocks scripted access. Download the PDF in a browser to
`/tmp/abrabanel-23900.pdf`, then:

```bash
mkdir -p /tmp/extract-ocr-abrabanel-mayanei
cp /tmp/abrabanel-23900.pdf /tmp/extract-ocr-abrabanel-mayanei/source.pdf
tools/extract_ocr.sh pdf \
  https://hebrewbooks.org/23900 \
  heb \
  external-resources/hebrew/abrabanel-mayanei.txt
```

The pre-linked cache means `fetch_url` sees the file already exists and
doesn't try to re-download; the URL is recorded in the output header for
provenance.

### Judeo-Arabic — archive.org plain-text (preferred for Yefet)

```bash
tools/extract_ocr.sh archive-text \
  commentaryonbook00japhuoft \
  external-resources/judeo-arabic/yefet-daniel-margoliouth.txt
```

archive.org publishes a pre-OCR'd plain-text alongside every uploaded scan;
when it exists, prefer it over re-OCRing the PDF.

### English — CCEL HTML (Origen via work-slug)

```bash
tools/extract_ocr.sh html \
  https://ccel.org/ccel/origen/against_celsus/anf04.vi.ix.vi.lv.html \
  external-resources/pdfs/origen-celsus-vi-lv.txt
```

CCEL section pages occasionally render the table-of-contents popover with
`loading…` placeholders; the script warns if the body looks JS-hydrated.
For load-bearing citations, prefer the work-level XML / TML / plain-text
export when CCEL exposes it.

## Pre-linking the cache (manual-download workaround)

`tools/extract_ocr.sh` caches every fetch under `/tmp/extract-ocr-<tag>/`,
where `<tag>` is the basename of the output path with the `.txt` suffix
stripped. To use a manually-downloaded file, copy or symlink it to the
expected cache location before invoking the script:

```bash
TAG=abrabanel-mayanei
mkdir -p "/tmp/extract-ocr-${TAG}"
cp ~/Downloads/abrabanel-23900.pdf "/tmp/extract-ocr-${TAG}/source.pdf"
tools/extract_ocr.sh pdf <url> heb "external-resources/hebrew/${TAG}.txt"
```

The script's `fetch_url` is idempotent: a non-empty cache file is reused
verbatim. The recorded URL becomes provenance metadata in the output's
header lines.

## Language packs

`tools/extract_ocr.sh` calls `tesseract --list-langs` and refuses to run if
the requested pack isn't installed. To install on macOS:

```bash
brew install tesseract            # core engine
brew install tesseract-lang       # adds 100+ language packs incl. grc, lat,
                                  # deu, frk, heb, ara, fra, eng
```

Confirmed available on this dev machine (2026-04-30): `grc lat deu heb ara
fra eng frk`. `deu_frak` is *not* in homebrew's tesseract-lang; use `frk`.

For DjVu sources where archive.org does not provide a `_djvu.txt`, install
djvulibre (`brew install djvulibre`) and pipe `djvutxt` into a file
manually; the script does not embed a DjVu mode because every audited
DjVu source has an archive.org `_djvu.txt` companion.

## URL hygiene

The tool accepts only `https://` URLs and rejects URLs containing shell
metacharacters (`` ` ``, `$`, `;`, `&`, `|`, `<`, `>`, whitespace).
`file://` and `javascript:` schemes are explicitly refused. Output paths
containing `..` segments are refused. Beyond these mechanical guards, URL
trustworthiness is the caller's responsibility — the tool will fetch
whatever https URL it is told to fetch.

## Tests

```bash
bash tools/tests/test_extract_ocr.sh
```

Tests cover dispatch, help, argument-shape errors, URL hygiene, output-path
hygiene, archive-id hygiene, `pdf-columns` numeric / formula validation,
language-pack absence, and unknown-flag rejection. The Theodoret regression
(re-OCR cols 1411–1413 against the local PG 81 PDF) and the live archive.org
+ CCEL fetches are session-level smoke tests; they are not part of the
offline test suite.

## See also

- `external-resources/greek/README.md` — Theodoret-specific provenance and
  the legacy TLG-screenshot pipeline.
- `docs/research/2026-04-28-patristic-reformation-fulltext-audit.md` — Wave 7
  Latin / German / Greek / English source-document audit.
- `docs/research/2026-04-28-jewish-reception-multilingual-audit.md` — Wave 6.3
  Hebrew / Judeo-Arabic source-document audit.
- `docs/schema/citation-schema.md` — `external-ocr` backend contract.
- `tools/citations.py:_load_ocr_text` — verification-side reader.
