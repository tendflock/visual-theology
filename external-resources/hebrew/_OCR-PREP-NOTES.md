# Hebrew OCR-prep notes

Per-voice notes on acquisition, OCR quality, and any workarounds applied.
Companion to `external-resources/hebrew/README.md` (which documents the
backend contract and extraction pattern in the abstract).

## Audited tooling state (2026-05-01)

- `tesseract --list-langs` confirms `heb` is installed (homebrew
  `tesseract-lang`, audited from `/opt/homebrew/share/tessdata/`).
- `tools/extract_ocr.sh pdf <url> heb <out>` is the intended invocation.
- A parallel session modified `tools/extract_ocr.sh` mid-pass (an
  `archive-text` /stream/ → /download/ + HTML-sniff fix). This affected
  only the `archive-text` subcommand; the `pdf` subcommand used here is
  unchanged. Re-probe of HebrewBooks endpoints with browser-class UA +
  `Accept-Language: en-US,en;q=0.9,he;q=0.8` headers still returned 403
  (Cloudflare). State unchanged after restart.

## Voices

### Abrabanel, *Ma'yanei ha-Yeshuah* (HebrewBooks #23900, Amsterdam 1647)

- **Audit row:** D-1J §B1 (`docs/research/2026-04-28-jewish-reception-multilingual-audit.md`).
- **Source-of-record:** `https://hebrewbooks.org/23900` (catalog page).
- **Intended output:** `external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt`.
- **Cache tag** (per `tools/extract_ocr.sh:output_tag`): `abrabanel-mayyenei-ha-yeshuah`.
- **Cache dir:** `/tmp/extract-ocr-abrabanel-mayyenei-ha-yeshuah/` — created
  empty by this session, ready to receive `source.pdf`.

#### Acquisition status: BLOCKED (Cloudflare)

This session attempted scripted acquisition via `curl` with a desktop-class
User-Agent against the documented endpoints. All six probed endpoints
returned HTTP 403 with a Cloudflare challenge body (5,549 bytes of HTML,
no PDF):

| Endpoint probed | Result |
|---|---|
| `https://hebrewbooks.org/23900` | 403 text/html |
| `https://hebrewbooks.org/pdfpager.aspx?req=23900` | 403 text/html |
| `https://hebrewbooks.org/downloadhandler.ashx?req=23900` | 403 text/html |
| `https://download.hebrewbooks.org/downloadhandler.ashx?req=23900` | 403 text/html |
| `https://beta.hebrewbooks.org/pdfpager.aspx?req=23900` | 403 text/html |
| `https://hebrewbooks.org/reader/reader.aspx?sfid=23900` | 403 text/html |

This matches the audit's prediction (D-1J §B1, gap-mapping reversal block).
A Cloudflare-aware fetcher would require either solving the JS challenge
in-process (out of scope for `extract_ocr.sh`) or proxying through a real
browser session. The intended workaround is the manual-download path
documented in `external-resources/README.md` ("Pre-linking the cache").

#### Mirror search: no mirrors found

- archive.org: queries `abrabanel+mayanei`, `abrabanel+daniel`,
  `אברבנאל+דניאל` — only hit was a secondary work (`doctrineofmessia0000sara`,
  Sarachek), not the commentary itself.
- No NLI / Otzar HaHochma alternate located in this pass; Otzar is paywalled,
  NLI's scan (if any) was not surfaced by the audit.
- The audit's framing stands: HebrewBooks #23900 is the only known PD
  full-text source for the Amsterdam 1647 edition.

#### Hand-off instructions for Bryan

To unblock OCR, download the PDF manually and stage it at the cache path:

```bash
# 1. In a browser, visit https://hebrewbooks.org/23900
#    Click "Download PDF" (or use the built-in viewer's save action) and
#    save as ~/Downloads/abrabanel-23900.pdf .
# 2. Stage at the cache path the script expects:
mkdir -p /tmp/extract-ocr-abrabanel-mayyenei-ha-yeshuah
cp ~/Downloads/abrabanel-23900.pdf \
   /tmp/extract-ocr-abrabanel-mayyenei-ha-yeshuah/source.pdf
# 3. Run the OCR pass:
cd /Volumes/External/Logos4
bash tools/extract_ocr.sh pdf \
  https://hebrewbooks.org/23900 \
  heb \
  external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt
```

The `fetch_url` step is a no-op when `source.pdf` is already non-empty
(see `tools/extract_ocr.sh:173`); the recorded URL becomes provenance
metadata in the output header. After OCR completes, sample-check with:

```bash
wc -l external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt
head -50 external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt
grep -c -E 'דניאל|מלכות|חיות' external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt
```

A typical Hebrew OCR pass at default 200 dpi / `--psm 6` will be slow
(this work is verbose; the audit calls it "the longest of [Abrabanel's]
prophetic commentaries"). Consider `--pages 1-50` first to confirm OCR
quality before committing to a full-volume pass.

#### OCR-quality expectations

- Vocalization (niqqud) and cantillation in the Amsterdam 1647 print are
  not consistent; quote anchors should default to consonantal text per
  `external-resources/hebrew/README.md` §"OCR-quality notes".
- The interior margins may carry Rashi-script gloss material; this is a
  known weak point for `heb` traineddata. Plan a manual cleanup pass on
  any Rashi-script columns.
- After OCR, NFC-normalize before storing — both the pre-existing voices
  in this directory and the verifier (`tools/citations.py:_load_ocr_text`)
  expect NFC.

#### Acquisition + OCR completed (2026-05-01, OCR-prep-Hebrew-pt-2)

Bryan downloaded the PDF in a browser (bypassing Cloudflare) and staged it
at `/Volumes/External/Logos4/daniel/Hebrewbooks_org_23900.pdf` (11.4 MB,
183 pages, `pdfinfo` confirms title `מעיני הישועה` + author Abrabanel).
The pre-link workflow from `external-resources/README.md` §"Pre-linking the
cache" was applied verbatim:

```bash
cp /Volumes/External/Logos4/daniel/Hebrewbooks_org_23900.pdf \
   /tmp/extract-ocr-abrabanel-mayyenei-ha-yeshuah/source.pdf
bash tools/extract_ocr.sh pdf \
  https://hebrewbooks.org/23900 heb \
  external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt
```

`fetch_url` saw the cached `source.pdf` and skipped the download; the URL
is recorded in the auto-generated header for provenance. Full 183-page run
completed in roughly 4 minutes wall-clock (faster than predicted).

**Output:** `external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt`
— 1,034,858 bytes, 7,779 lines, default `--dpi 200 --psm 6`.

A 6-line manual-provenance preamble was prepended above the script's
auto-generated header, mirroring the OCR-prep-Latin-pt-2 pattern (URL,
local staging path, date, tesseract lang, RTL note, HebrewBooks watermark
caveat). The script's `# Source:` line points at the catalog URL
`https://hebrewbooks.org/23900`; the manual-preamble URL preserves the
exact `pdfpager.aspx?req=23900` form for downstream provenance.

**Quality verdict:** acceptable, with substantive OCR error rate.

- **Daniel keyword density** (`grep -c -E …`):
  - `דניאל` = 16 (lower than the audit's "hundreds" prediction; OCR character
    substitutions are corrupting the lemma — confirmed by sampling p100, where
    the running text is recognizable Hebrew commentary but `ד-נ-י-א-ל` letters
    are frequently mis-read as similar-looking glyphs)
  - `מלכות` = 54, `חיות` = 20, `קרן` = 24 (all within the audit's
    "tens-to-hundreds" plausible band)
  - `בן.אנש` = 0 (likely OCR-corrupted; expected non-zero)
  - `נבוכדנצר` = 1, `בלשאצר` = 1, `משיח` = 2 (all should be tens; OCR
    error rate on proper nouns is high)
- **Spot-check of pp. 30, 50, 100:** title page (p1) is heavily fragmented
  as expected; mid-volume pages show recognizable running Hebrew
  commentary punctuated by glyph substitutions, broken word boundaries,
  and occasional injected non-Hebrew characters (the print's interior
  margin gloss material bleeds into the main column under `--psm 6`).
- **HebrewBooks watermark:** captured 1× per page on the surveyed sample
  (`grep -c hebrewbooks` = 1, `grep -c 23900` = 1 — both in the auto-header
  metadata, which means the OCR did NOT capture the printed-frame
  watermark text reliably; confirmed only on p1's Hebrew copy notice
  `הועתק והוכנס לאינטרנט`). Wave 6.3 quote anchors must still filter
  watermark fragments where they do appear; do not assume the OCR
  output is watermark-free.
- **RTL handling:** logical order is preserved character-by-character;
  visual order in editors depends on the editor's RTL handling. The OCR
  text is suitable for verifier-side hash matching (operates on logical
  order) but requires NFC normalization at storage time (already
  enforced by `tools/citations.py:_load_ocr_text`).
- **Niqqud / cantillation:** none preserved (the Amsterdam 1647 print's
  consonantal text matches the README's expectation).

**Implication for Wave 6.3:** Abrabanel quote anchors should be **short
consonantal phrases** chosen from text that survives the OCR cleanly.
Long verbatim quotes against this OCR are unlikely to verify. Consider
selecting anchors by reading the source PDF in a viewer and locating the
matching OCR substring, rather than letting an LLM extract them blind.
A future quality-improvement pass might re-OCR with `--psm 4` (single
column of variable text) or tile-by-tile pre-processing to suppress the
HebrewBooks watermark frame before tesseract runs.

**Status:** unstaged, awaiting K-5 PM consolidation with Greek + Wave 3
cleanup. Source PDF retained at `/Volumes/External/Logos4/daniel/`;
cache directory `/tmp/extract-ocr-abrabanel-mayyenei-ha-yeshuah/`
retained (re-runs are no-ops).
