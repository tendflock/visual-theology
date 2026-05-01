# OCR-prep notes — Judeo-Arabic Wave 6.x voices

Session date: 2026-05-01 (re-check after OCR-1 tool-bug fix)
Tool: `tools/extract_ocr.sh archive-text` (post-fix; uses `/download/`)

## Per-voice status

### Yefet ben Eli (Jephet ibn Ali) — Margoliouth 1889 — **clean** ✅

- File: `yefet-ben-eli-margoliouth-1889.txt`
- Source: `https://archive.org/download/commentaryonbook00japhuoft/commentaryonbook00japhuoft_djvu.txt`
- Size: 12,845 lines / 669,703 bytes
- Tool: `bash tools/extract_ocr.sh archive-text commentaryonbook00japhuoft external-resources/judeo-arabic/yefet-ben-eli-margoliouth-1889.txt`
- **Re-fetched 2026-05-01 via canonical script** after the parallel
  OCR-prep-Latin session fixed the `archive-text` subcommand's URL to use
  `/download/` (raw text) instead of `/stream/` (HTML viewer). The file
  the coordinator previously cached with a manual `/download/` curl
  produced bit-for-bit identical content to the canonical-script output;
  the file was deleted and re-fetched cleanly so future provenance is
  unambiguously the canonical tool path. The current output therefore has
  **no extract_ocr.sh provenance header** — it is the raw archive.org
  `_djvu.txt` byte-for-byte.
- **Coverage: Daniel chapters 1–12 in full** (D-1.6 reversal of the prior
  "1–6 only" framing — empirically reconfirmed this session). English
  running headers progress `VII. 4.] COMMENTARY ON DANIEL. 33` →
  `VII. 12.] COMMENTARY ON DANIEL. 35` → `VII. 25.] COMMENTARY ON DANIEL. 37`
  (= Dan 7 fully covered, including Bar-Enash and the time-times-and-half-a-time
  formula), and the volume terminates at `XII. 13.] COMMENTARY ON DANIEL. 87`
  (Dan 12:13, the final verse). Distinct chapter-prefix tokens
  `I.` `II.` `III.` `IV.` `V.` `VI.` `VII.` `VIII.` `IX.` `X.` `XI.` `XII.`
  are all present.
- Format: facing-page Judeo-Arabic (Hebrew script) + Margoliouth's English
  translation. Quality clean for English; archive.org's pre-OCR pass
  on the Judeo-Arabic verso pages is acceptable for survey-locator use
  but not for typography-sensitive citations — verify any quoted
  Judeo-Arabic against the source PDF directly.
- The post-OCR-1.5 `extract_ocr.sh archive-text` codepath now also fails
  defensively if the response begins with HTML markup; future
  Judeo-Arabic OCR-prep can rely on the subcommand directly without
  pre-link workarounds.

### Saadia Gaon — Klein 1977 BRGS thesis — **acceptable** ⚠

- File: `saadia-tafsir-aramaic-daniel.txt`
- Source: YU repository item `f04a17f7-cc80-422c-8f75-cd5132521785`
  (handle `20.500.12202/6655`); 154-page scanned typewritten thesis.
- Bitstream content URL (DSpace REST API, not WAF-blocked):
  `https://repository.yu.edu/server/api/core/bitstreams/33511654-7ed0-437f-a019-0f36df968f55/content`
- Size: 183,685 bytes across 154 OCR'd pages.
- Tool: `bash tools/extract_ocr.sh pdf <item-url> heb+eng <output> --pages 1-154`
  (PDF pre-staged at `/tmp/extract-ocr-saadia-tafsir-aramaic-daniel/source.pdf`
  via the DSpace REST API; the user-facing `/items/<uuid>` page is
  WAF-blocked with HTTP 202 even with a browser User-Agent, so the
  REST-API path is the working fetch route).
- **Coverage: Daniel 2:4b–7:28 only** (the Aramaic portion of the book).
  Klein's thesis explicitly limits its scope to the Aramaic chapters; the
  audit's scope clarification (D-1.6) is empirically confirmed by the
  Hebrew-script title page on PDF p. 74:
  `תפסיר רבינו סעדיה גאון / על החלק הארמי של ספר דניאל`
  ("Tafsir of R. Saadia Gaon on the Aramaic portion of the book of Daniel").
  **Daniel 1, 8, 9, 10, 11, 12 are NOT covered by this edition** — for
  Wave 6.3 surveys that need Saadia on those chapters, the audit's
  `gap-mapping §5d U9` classification still applies (Alobaidi 2006 paid
  edition is the only modern critical edition; not freely available).
  For the M7 Daniel-7 dossier the coverage is favourable — Dan 7 sits
  inside 2:4b–7:28.
- **Author attribution correction.** The audit's §B2 attributed this
  thesis to **Elazar Hurvitz**. The actual author per the YU DSpace
  metadata (`dc.contributor.author`) is **Stanley Klein** (Hebrew name
  שמאול אהרן קליין). Title and content are unchanged. Wave 6.3
  surveys must record Saadia citations as drawn from
  *Klein, Stanley, 1977, "Rav Saadia Gaon's Tafsir on the Aramaic portion
  of Daniel edited from manuscripts and Cairo Geniza fragments with an
  introduction," M.A. thesis, Bernard Revel Graduate School, Yeshiva
  University.*
- **Document structure.**
  - pp. 1–60: Klein's English introduction (editorial context, history of
    Saadia's Tafsir, manuscript stemma).
  - pp. 61–72: bibliography (mixed English / Hebrew / German entries).
  - p. 74: Hebrew-script title page of the Tafsir edition proper.
  - pp. 75–~150: Saadia's Tafsir text in Judeo-Arabic (Hebrew script),
    edited from Yemenite MSS + Cairo Geniza fragments. Hebrew-character
    density runs ~50–67% across these pages. Verse anchors follow Klein's
    apparatus rather than embedded chapter markers; survey citations
    must locate Daniel 7 sections by content match against the printed
    page rather than by anchor regex.
- **Quality: acceptable.** The PDF is a Xerox VersaLink B7035 scan of a
  typewriter-era original. Klein's English shows the typical
  typewriter-OCR e/o substitution (`Eurepean`, `rediscevery`, `im` for
  `in`, etc.) but is readable for survey-locator purposes. The
  Hebrew-script Tafsir body OCRs cleaner than the English (Hebrew
  letterforms are unambiguous at scan resolution) but apparatus signs
  and small marginalia are unreliable. Treat all citations as
  sample-verify-against-PDF-required.
- **DPI / PSM:** script defaults (DPI 200, PSM 6) work. Higher DPI was
  sample-tested on a quality-poor page and did not improve OCR.
- **TEXT-bundle workaround that did NOT work.** DSpace 7's auto-extracted
  `.pdf.txt` bitstream returns HTTP 401 (authentication required); only
  the ORIGINAL bundle (the PDF) is publicly readable. OCR via
  extract_ocr.sh is therefore the only viable path on the public side.

## Reusable DSpace REST API pattern (for any future YU repository item)

The user-facing `/items/<uuid>` URL is Cloudflare-WAF-blocked even with a
browser User-Agent (HTTP 202 + CAPTCHA). The DSpace 7 REST API at
`/server/api/core/...` is **not** WAF-blocked and exposes the same items.
Working fetch sequence:

```bash
# 1. List bundles
curl -sL -A "Mozilla/5.0" -H "Accept: application/json" \
  "https://repository.yu.edu/server/api/core/items/<uuid>/bundles"
# 2. List bitstreams in the ORIGINAL bundle
curl -sL -A "Mozilla/5.0" -H "Accept: application/json" \
  "https://repository.yu.edu/server/api/core/bundles/<original-bundle-uuid>/bitstreams"
# 3. Download the PDF
curl -sL -A "Mozilla/5.0" \
  "https://repository.yu.edu/server/api/core/bitstreams/<bitstream-uuid>/content" \
  -o /tmp/extract-ocr-<tag>/source.pdf
# 4. Pre-link cache, then run extract_ocr.sh pdf with the item-page URL
#    (extract_ocr.sh's fetch_url is idempotent on a non-empty cache file)
bash tools/extract_ocr.sh pdf "<item-page-url>" <lang> <output> --pages <range>
```

Future audits should record YU items by `<uuid>` (and ideally by ORIGINAL
bitstream UUID) so the API path is one-step reachable.

## Codex review findings (2026-05-01) — pending follow-on session

This session's codex adversarial review (`read-only` sandbox, `model_reasoning_effort=high`)
returned `pass-with-conditions`. Per the PM-CHARTER §4 rule ("Do NOT apply
codex's suggestions during the same session — capture them as findings in
`docs/FOLLOW-UPS-TRACKER.md` and fold them into a follow-on session"), the
findings below are documented here as advisory notes for downstream
consumers; they have **NOT** been applied to the body of this notes file or
to the OCR outputs in this session. **A follow-on session must transcribe
these into `docs/FOLLOW-UPS-TRACKER.md`** (which sits outside the
OCR-PREP-JUDEO-ARABIC scope) and apply the corrections.

1. **Saadia coverage statement.** The notes say `Dan 2:4b–7:28 only`, which
   matches the thesis title's stated scope ("the Aramaic portion of the
   book of Daniel"). Codex observed that Klein's edited Tafsir body
   actually starts at Dan **2:1** (saadia-tafsir-aramaic-daniel.txt:2061
   onward, verse markers א, ב, ג, ד at lines 2061, 2068, 2074, 2077),
   not 2:4b. Klein evidently includes the Hebrew preamble vv 2:1–3 alongside
   the Aramaic chapters proper. The safer coverage statement is
   `Dan 2:1–7:28`, with a note that the *thesis title* restricts scope to
   the Aramaic portion (2:4b–7:28). Practical effect for the M7 dossier:
   none — Daniel 7 sits inside both ranges. Practical effect for any
   future Daniel 2 surveys: Saadia on Dan 2:1–3 is recoverable from this
   file even though the title would have suggested otherwise.

2. **Saadia page-marker count.** The notes claim 154 OCR'd pages. The
   file contains **153** `==== PDF page NNNN ====` markers; PDF page
   `0072` is missing (jumps from `0071` at line 1983 directly to `0073`
   at line 2010), while page `0154` is present at line 4363. Likely
   cause: a blank or near-blank page where the OCR returned 0 bytes and
   `concat_with_markers` skipped the marker (the script only emits a
   marker when the per-page `.txt` is non-empty). Follow-on action:
   inspect PDF page 72 directly to confirm whether content was lost or
   the page is genuinely blank/sigla; re-run with higher DPI / different
   PSM if content was lost.

3. **Saadia document structure.** The notes describe `pp. 75–~150` as
   the Tafsir body. Codex confirms PDF p. 75 is a Hebrew-script
   sigla/abbreviations key (saadia-tafsir-aramaic-daniel.txt:2040), with
   the Tafsir text proper beginning on **p. 76** (line 2061) and running
   through **p. 154** (line 4363+), ending with Dan 7:28 commentary
   around line 4368. Corrected structure for the next revision:
   - pp. 1–60: Klein's English introduction.
   - pp. 61–72: bibliography (mixed English / Hebrew / German).
   - p. 73: blank/recto preamble.
   - p. 74: Hebrew-script title page of the Tafsir edition.
   - p. 75: sigla / abbreviations key.
   - pp. 76–154: Tafsir body (Judeo-Arabic).

4. **Yefet contains a second bound volume — citation-safety issue.**
   The Margoliouth 1889 archive.org item is a multi-work bound volume.
   The Yefet *Commentary on Daniel* English translation ends at
   `XII. 13.] COMMENTARY ON DANIEL. 87` (yefet-ben-eli-margoliouth-1889.txt:5098).
   Yefet's Judeo-Arabic back-matter and apparatus continue after that.
   At **line 9742** a second bound work begins:
   `THE PALESTINIAN VERSION OF THE HOLY SCRIPTURES` (a Margoliouth
   edition of Palestinian-Aramaic biblical fragments — unrelated to
   Yefet). Survey subagents must **not** cite content from
   `yefet-ben-eli-margoliouth-1889.txt:9742-12845` as Yefet on Daniel.
   Follow-on action: either (a) split the file at line 9742 into
   `yefet-...txt` and `margoliouth-palestinian-version.txt`, or (b) add
   a clear in-band boundary marker that the citation backend
   (`tools/citations.py:_load_ocr_text`) can refuse to read past, or
   (c) document the line-9742 boundary in the citation `passageRef`
   contract for any Yefet citation drawn from this file.

The codex log itself is at `/tmp/codex-judeo-arabic-review.log` (126 KB)
for the full reasoning trace; the pending-follow-on summary above
captures the actionable items.
