# OCR-prep notes — Latin Wave 7 voices

Session date: 2026-04-30 → 2026-05-01
Tool: `tools/extract_ocr.sh` (Wave 6.3 / Wave 7 generalised pipeline)
Tesseract `lat` traineddata: confirmed installed.

This file accompanies the Latin OCR-prep run that fed the Wave 7 survey-dispatch
queue. It records per-voice quality verdicts, the failure modes that prevented
several voices from being scripted in this session, and one tool bug surfaced
by the codex adversarial review.

> **Codex pass:** the first pass of this session returned VERDICT: fail with
> five issues. Four (Cyril HTML contamination, Bullinger long-s downgrade,
> Pellican/Melanchthon/Lambert rerun-commands too vague, `archive-text`
> URL bug) are resolved and reflected in the per-voice rows below.
> The fifth (out-of-scope workspace changes) is addressed in the
> "Out-of-scope workspace state" section at the end of this file.
>
> **Tool-bug fix landed (2026-05-01):** `tools/extract_ocr.sh` now uses
> `archive.org/download/<id>/<id>_djvu.txt` (was `/stream/...`) and an
> HTML-sniff guard fails the subcommand when archive.org returns a viewer
> page rather than plain text. Cyril was regenerated cleanly through the
> fixed tool; no manual override remains in the output.

## Per-voice status

### 1. Cyril of Alexandria — Mai *Nova Bibliotheca Patrum* tom. 2 — **acceptable** ✅

- File: `cyril-alexandria-daniel-fragments.txt`
- Source: `https://archive.org/download/bub_gb__VlU6XtRKPgC/bub_gb__VlU6XtRKPgC_djvu.txt`
  — archive.org's pre-extracted plain text (no fresh OCR), via the now-fixed
  `tools/extract_ocr.sh archive-text` subcommand.
- Size: 3.0 MB / 77,720 lines. Whole-volume text. No provenance header
  (the `archive-text` subcommand preserves archive.org's djvu output verbatim).
- **First-pass bug + fix:** codex's adversarial review caught that the file
  initially contained archive.org's HTML viewer because the tool was hitting
  `/stream/<id>/<id>_djvu.txt`. Tool was fixed (now uses `/download/...`
  with an HTML-sniff guard); Cyril was regenerated cleanly through the
  fixed tool with no manual override. `grep -c '<html\|<!DOCTYPE\|<body'`
  on the current output returns 0.
- Quality: archive.org's djvu pre-OCR is clean for the Latin editorial
  apparatus; Greek script is mangled (Latin-transliteration artefacts) — that
  is the documented djvu-pass behaviour for Greek and matches the audit's
  expectation. Survey path: anchor on Latin fragment incipits, not on Greek
  body. Useful entry points (line numbers in the post-fix file):
  - line 712 — TOC entry "XIII. In proverbia, Danielem, et contra
    pneumalomachos fragmenta p. 467-468."
  - line 507 — "Polychronium in Danielem" (Mai's prefatory matter).
  - line 48223 — "Sic videlicet eum vidit Daniel" (mid-volume Daniel
    citation in Latin).

### 2. Gregory the Great — Migne PL 75 (*Moralia* bks. 1–16) — **clean (with front-matter caveat)** ✅

- File: `gregory-moralia-vol1.txt`
- Source: `https://archive.org/download/patrologiaecursu75mign/patrologiaecursu75mign.pdf`
  (Latin PL volume — **not** the Bliss English translation).
- Size: 3.5 MB / 39,062 lines / 593 pages OCR'd.
- Quality: clean Latin OCR; chapter and book markers visible. Front-matter
  *Vita* runs through ~line 17,000; *Moralia* book 1 begins near line 17,637.
  Survey-dispatch should expect the citation-bearing text to start mid-file.
  Daniel-engaging passages span throughout *Moralia*; the audit notes
  ~20–35 citation surface across PL 75 + PL 76.
- **Dispatch-instruction discrepancy resolved:** the dispatch named
  `archive.org/details/moralsonbookofj01greg` as the source URL; that
  identifier resolves to the **English Bliss translation**, which would
  have failed the verifier's `latin/` ↔ `quote.language=la` cross-check
  (`tools/citations.py:_load_ocr_text`). Used the audit-canonical Latin
  PL 75 instead. PL 76 (Moralia bks. 17+ + *Hom. on Ezekiel*) is **not
  yet OCR'd** — flagged as a Wave 7 sub-followup if survey density
  warrants.

### 3. Bullinger 1571 — *In Danielem* — **acceptable; long-s normalization required** ✅

- File: `bullinger-daniel-1571.txt`
- Source: `https://archive.org/download/bim_early-english-books-1641-1700_bullinger-heinrich_1571_0/...pdf`
  (the EEBO collection-prefix is non-strict on dates, per the audit; the scan
  itself is the canonical 1571 Latin Zurich Bullinger).
- Size: 2.0 MB / 31,652 lines / 547 pages OCR'd.
- Quality: clean character-level Latin OCR with the canonical 16th-c. long-s
  pitfall. **Codex pass-2 downgrade from "clean" to "acceptable":** long-s
  → `f` confusion is pervasive, not occasional. Examples in front-matter
  (`bullinger-daniel-1571.txt:45-48` — `tàmfenfus`, `ufus`, `commonftratur`,
  `pofsit`) and main text (`:1589-1606` — `fancti`, `fcriptí`, `effe`,
  `fuiffe`, `ftudioforü`). The audit's §4d pre-flagged this as a structural
  Latin-OCR caveat; pre-survey verifier `_normalize` step needs long-s
  reversal before quote-anchor matching. 1,267 keyword hits across
  `Danie|caput|sermo|prophet`. Strongest Wave 7 voice in the Latin bucket
  for citation density; weakest for raw-byte verbatim matching.

### 4. Œcolampadius — *In Danielem* 1530 (Google Books `tzViAAAAcAAJ`) — **DEFERRED, manual download required** ❌

- Output: not produced this session.
- Failure mode: Google Books `?output=pdf` redirects through a CAPTCHA-
  protected `capid=AFLRE...` continue-URL; HEAD probes return 200 OK PDF
  (26 MB content-disposition `In_Danielem_prophetam_Joannis_Oecolampad.pdf`),
  but GET requests with curl + cookie jar + Referer + Chrome UA all land on
  the HTML viewer page, never the PDF body.
- **Rerun command after manual download** (`<DOWNLOADED.pdf>` is the file
  staged by the human operator from a browser session against
  `https://books.google.com/books?id=tzViAAAAcAAJ&printsec=frontcover&output=pdf`):
  ```bash
  TAG=oecolampadius-in-danielem-1530
  mkdir -p "/tmp/extract-ocr-${TAG}"
  cp <DOWNLOADED.pdf> "/tmp/extract-ocr-${TAG}/source.pdf"
  bash tools/extract_ocr.sh pdf \
    "https://books.google.com/books?id=tzViAAAAcAAJ" \
    lat \
    "external-resources/latin/${TAG}.txt"
  ```
  The pre-linked cache is honoured by `fetch_url`'s idempotent skip-if-non-empty
  logic; the recorded URL becomes provenance metadata. (URL above is the
  ampersand-free listing form — `extract_ocr.sh`'s validator rejects `&`.)
- e-rara fallback: the audit lists e-rara as canonical for Œcolampadius but
  also notes JS-challenge wall on titleinfo pages. Same manual-download
  workaround applies.
- archive.org search (`Oecolampadius+1530`, `Oecolampadius+Daniel`): no hits.

### 5. Pellican on Daniel (BSB `bsb10142935`) — **DEFERRED, no scriptable PDF endpoint** ❌

- Output: not produced this session.
- Failure mode: BSB's IIIF manifest exposes `seeAlso` (MARCXML, RDF) and
  `related` (OPAC, details page) but **no `rendering` PDF download URL**.
  The viewer's "Werk-PDF herunterladen" button issues a session-protected
  download token that cannot be reproduced from a scripted client. The
  earlier WebFetch on the viewer page returned BSB's "Leider ist ein Fehler
  bei der Darstellung aufgetreten" interstitial.
- **Rerun command after manual download** from the BSB viewer at
  `https://www.digitale-sammlungen.de/de/view/bsb10142935`:
  ```bash
  TAG=pellican-daniel
  mkdir -p "/tmp/extract-ocr-${TAG}"
  cp <DOWNLOADED.pdf> "/tmp/extract-ocr-${TAG}/source.pdf"
  bash tools/extract_ocr.sh pdf \
    "https://www.digitale-sammlungen.de/details/bsb10142935" \
    lat \
    "external-resources/latin/${TAG}.txt"
  ```
- Alternative path (more work): walk the IIIF manifest's canvases and
  download each page as JPEG/PNG via
  `https://api.digitale-sammlungen.de/iiif/image/v2/<image-id>/full/full/0/default.jpg`,
  then OCR each. Out of scope for this OCR-prep session.
- archive.org search (`Pellicanus+Daniel`, `Pellicanus+Bibliorum`): no hits.

### 6. Melanchthon on Daniel (Google Books `DPU7AAAAcAAJ`) — **DEFERRED, manual download required** ❌

- Output: not produced this session.
- Failure mode: identical to Œcolampadius — Google Books CAPTCHA continue-URL
  blocks scripted GET requests for the PDF body.
- **Rerun command after manual download** from
  `https://books.google.com/books?id=DPU7AAAAcAAJ&printsec=frontcover&output=pdf`:
  ```bash
  TAG=melanchthon-daniel
  mkdir -p "/tmp/extract-ocr-${TAG}"
  cp <DOWNLOADED.pdf> "/tmp/extract-ocr-${TAG}/source.pdf"
  bash tools/extract_ocr.sh pdf \
    "https://books.google.com/books?id=DPU7AAAAcAAJ" \
    lat \
    "external-resources/latin/${TAG}.txt"
  ```
- BSB alternative `bsb10176881` exists per audit but has the same
  no-scriptable-PDF block as Pellican.
- archive.org search (`Melanchthon+Daniel`): no relevant hits.

### 7. Lambert *In Apocalypsim* 1528 (Google Books `GKtkAAAAcAAJ`) — **DEFERRED, manual download required** ❌

- Output: not produced this session.
- Failure mode: identical Google Books CAPTCHA wall.
- **Rerun command after manual download** from
  `https://books.google.com/books?id=GKtkAAAAcAAJ&printsec=frontcover&output=pdf`:
  ```bash
  TAG=lambert-in-apocalypsim-1528
  mkdir -p "/tmp/extract-ocr-${TAG}"
  cp <DOWNLOADED.pdf> "/tmp/extract-ocr-${TAG}/source.pdf"
  bash tools/extract_ocr.sh pdf \
    "https://books.google.com/books?id=GKtkAAAAcAAJ" \
    lat \
    "external-resources/latin/${TAG}.txt"
  ```
- Audit notes the Daniel-engagement density of Lambert is **INFERRED, not
  verified**, so the survey should treat this voice as a density-survey
  target (Rev 13 / 17 / 20 sections specifically) rather than a high-yield
  Daniel commentator. Alternate id `bupgAAAAcAAJ` (1539 Basel re-edition)
  likely faces the same Google Books wall; not probed this session.

### 8. Mede Latin original (*Clavis Apocalyptica* 1627/1632/1644/1649) — **DEFERRED, no open-access Latin scan located** ❌

- Output: not produced this session.
- Search: `archive.org/advancedsearch.php?q=clavis+apocalyptica+mede` returns
  only the Cooper 1833 ET (`atranslationmed00medegoog`, already on the
  english/ track per existing handoff). `q=clavis+apocalyptica+1627+OR+1632
  +OR+1644+OR+1649` returns no patristic-volume hits — only Archive-It
  crawler artefacts.
- Audit's recommended next move stands: focused Cambridge / Bodleian /
  EEBO-TCP search outside the scope of an OCR-prep session.
- Cooper 1833 ET (English) remains the verified path for Mede; this voice
  is not blocked, just not yet expanded into the Latin corpus path.

## Summary verdict

| Voice | OCR'd this session | Quality | Output |
|---|---|---|---|
| Cyril of Alexandria | ✅ archive-text (via fixed tool) | acceptable (Latin clean; Greek mangled per djvu) | `cyril-alexandria-daniel-fragments.txt` (3.0 MB) |
| Gregory the Great | ✅ PDF OCR (PL 75) | clean (front-matter caveat) | `gregory-moralia-vol1.txt` (3.5 MB) |
| Bullinger 1571 | ✅ PDF OCR | acceptable (long-s normalization required) | `bullinger-daniel-1571.txt` (2.0 MB) |
| Œcolampadius 1530 | ❌ Google Books CAPTCHA | n/a | (manual download required) |
| Pellican | ❌ BSB no scriptable PDF | n/a | (manual download required) |
| Melanchthon | ❌ Google Books CAPTCHA | n/a | (manual download required) |
| Lambert 1528 | ❌ Google Books CAPTCHA | n/a | (manual download required) |
| Mede Latin | ❌ no open-access scan | n/a | (out-of-session search step) |

**3 of 8 voices** completed scripted OCR-prep this session; **4 voices** require
a manual browser-download step that this session cannot perform; **1 voice**
(Mede Latin) is a defer-to-later-search.

## Implications for Wave 7 survey dispatch

- The 3 successfully-OCR'd voices (Cyril, Gregory PL 75, Bullinger) are
  ready for survey dispatch against the Latin corpus path, with the
  per-voice caveats above.
- The 4 manual-download voices (Œcolampadius, Pellican, Melanchthon, Lambert)
  need a one-shot browser-download intervention before their surveys can
  run. Recommend either (a) a brief manual session to download all four
  PDFs at once and re-run extract_ocr.sh against the pre-linked caches, or
  (b) a per-voice anthology-fallback for the Wave 7 dispatch with the
  Latin-original survey deferred until the manual download lands.
- Mede Latin remains an audit follow-up (Cambridge / Bodleian / EEBO-TCP);
  the Cooper 1833 ET path is independently verified and unaffected.

## Tool-bug follow-up — `archive-text` subcommand URL — **RESOLVED**

`tools/extract_ocr.sh` `archive-text` previously hard-coded
`https://archive.org/stream/${archive_id}/${archive_id}_djvu.txt`, which
serves an HTML viewer wrapping the plain text — not the plain text itself.
The HTML wrapper was large enough to clear the `< 1000 bytes` quality
floor, so the wrong endpoint was silently producing citation-unsafe
files (caught by codex pass-1 on this session).

Tool fix landed 2026-05-01:
- Endpoint changed to `/download/<id>/<id>_djvu.txt` (302-redirects to the
  data server and serves plain text directly).
- New defensive sniff: subcommand exits 3 if the first 256 bytes of the
  output match `<!DOCTYPE\|<html\|<body`.
- Cyril regenerated through the fixed tool — output is HTML-free, exit 0.

**Yefet ben Eli cross-check still owed.** The Judeo-Arabic Yefet output
(`external-resources/judeo-arabic/yefet-daniel-margoliouth.txt` per audit;
the actual filename in this repo is
`external-resources/judeo-arabic/yefet-ben-eli-margoliouth-1889.txt`)
was generated by the same `archive-text` subcommand before the fix. It
should be inspected for the same HTML-wrapper contamination and
regenerated if affected. Out of scope for this Latin session — flag for
the Judeo-Arabic OCR-prep coordinator (cross-coordinator hand-off).

## Out-of-scope workspace state — *not* this session's changes

The codex review correctly flagged that `git status --short` shows several
untracked / modified paths outside `external-resources/latin/`. Per the
session-start `gitStatus` snapshot, the only pre-session untracked items
were `.claude/`, `Romans3/`, and one `docs/research/2026-04-23-...` file.
The expanded set seen at codex-review time
(`docs/FOLLOW-UPS-TRACKER.md` modified; `docs/research/scholars/*.json`
untracked; `external-resources/judeo-arabic/yefet-ben-eli-margoliouth-1889.txt`
untracked; `tools/_smoke_script.py` untracked) reflects parallel work in
other coordinator sessions (Wave 3 dispatch, Hebrew / Judeo-Arabic /
German / Greek OCR-prep sessions per the dispatch's "cross-coordinator
conflict avoidance" notice).

This Latin session wrote only to `external-resources/latin/`:
- `cyril-alexandria-daniel-fragments.txt` (untracked, this session)
- `gregory-moralia-vol1.txt` (untracked, this session)
- `bullinger-daniel-1571.txt` (untracked, this session)
- `_OCR-PREP-NOTES.md` (untracked, this session)

`git status --short -- external-resources/latin/` confirms the four-file
scope. No tracked files were modified by this session; nothing was
staged or committed.

## Pipeline observations (for future OCR-prep sessions)

- `extract_ocr.sh`'s URL validator rejects `&` as a shell metacharacter,
  which is the correct security posture but blocks every Google Books
  `?id=…&output=pdf` query string from being passed directly. The
  pre-link-cache workaround (README §"Pre-linking the cache") is the right
  pattern; document it more prominently in the per-language READMEs.
- For voices behind Google Books or BSB walls, document the failure mode
  in the per-voice OCR-prep notes (this file) so the Wave-7 dispatch can
  branch on (scripted-OCR-ready) vs (needs-manual-download-step) per voice.
- For `archive-text` outputs, the tool now exits non-zero if archive.org
  returns an HTML viewer rather than plain text — no caller-side sanity
  check needed.

---

## Pt-2 supplement — 2026-05-01 (manual-download voices)

This supplement is appended after the original OCR-prep-Latin run. The
original per-voice rows above remain in place for historical record; the
authoritative current status of voices 4 (Œcolampadius), 5 (Pellican),
6 (Melanchthon), and 7 (Lambert) is the Pt-2 supplement below.

> **Pt-2 scope.** Bryan manually downloaded 3 of the 4 deferred PDFs to
> `/Volumes/External/Logos4/daniel/` and dispatched OCR-prep-Latin-pt-2 to
> run them through `tools/extract_ocr.sh pdf` against pre-linked caches.
> Pellican remained undownloadable across BSB / Google Books / e-rara /
> archive.org probes and is logged here as a documented gap; PM applies
> the gap entry to `docs/research/method-and-limits.md` and the follow-ups
> tracker before K-5.

### Pt-2 / 4. Œcolampadius — *In Danielem* 1530 — **acceptable; long-s caveat** ✅

- File: `oecolampadius-in-danielem-1530.txt`
- Provenance URL: `https://books.google.com/books?id=tzViAAAAcAAJ`
- Local PDF (cleared after K-5 commit, *not* tracked):
  `/Volumes/External/Logos4/daniel/In_Danielem_prophetam_Joannis_Oecolampad.pdf`
- 26 MB / 335 pages / `In Danielem prophetam Joannis Oecolampadij libri duo,
  omnigena et abstrusiore cum Hebraeorum tum Graecorum scriptoru doctrina
  referti` (matches PDF metadata title; author Johannes Ökolampadius).
- Output: 800 KB / 13,381 lines (= 13,375 OCR-body lines + 6-line
  manual-download preamble), with manual-download preamble + the tool's
  auto-generated `# Extracted from PDF` header (the preamble was prepended
  per dispatch; tool's own header records the same provenance URL).
- Quality: clean character-level Latin OCR with the canonical 16th-c.
  long-s pitfall. Examples around `oecolampadius-in-danielem-1530.txt:50`
  on PDF page 50: `téntiam` (sententiam), `fapientia` (sapientia), `plendoris`
  (splendoris), `fummo` (summo), `fnis` (suis). Greek epigram on the
  title-verso is mangled (lat tesseract pack does not handle Greek).
  Long-s normalization required before quote-anchor matching, same as
  Bullinger.
- Daniel keyword density: 358 hits on `Danie`, 46 on `caput|capvt`, 144 on
  `visio|regnum|bestia` — strong density; this is the foundational
  Reformation Daniel commentary and the OCR is workable.

### Pt-2 / 5. Pellican on Daniel — **DOCUMENTED GAP** ❌

- Output: not produced. Pellican remains undownloadable across BSB
  (`bsb10142935` — IIIF manifest exposes no `rendering` PDF; viewer
  download protected by session token), Google Books (no listing for the
  Daniel volume of *Commentaria Bibliorum* tom. 3 located), e-rara
  (JS-challenge wall on titleinfo pages), and archive.org (`Pellicanus+Daniel`,
  `Pellicanus+Bibliorum` returned no hits).
- The original Pellican row #5 above remains accurate for the failure-mode
  surface and the would-be rerun command if the PDF surfaces.
- PM action: gap entry to `docs/research/method-and-limits.md` + follow-ups
  tracker before K-5 commits (out of scope for this session).
- Wave-7 dispatch implication: Pellican stays in anthology-fallback for
  Wave 7. This is non-blocking for the Wave-7 deliverable per the Pt-2
  dispatch's framing.

### Pt-2 / 6. Melanchthon — *In Danielem prophetam commentarius* 1543 — **acceptable; long-s + page-edge artefacts** ✅

- File: `melanchthon-daniel.txt`
- Provenance URL: `https://books.google.com/books?id=DPU7AAAAcAAJ`
- Local PDF (cleared after K-5 commit, *not* tracked):
  `/Volumes/External/Logos4/daniel/In_Danielem_prophetam_commentarius.pdf`
- 13 MB / 397 pages / `In Danielem prophetam commentarius` (matches PDF
  metadata; author Philipp Melanchthon; 1543 Wittenberg edition).
- Output: 377 KB / 12,398 lines (= 12,392 OCR-body lines + 6-line preamble;
  smallest bytes-per-page of the Pt-2 set —
  ~950 bytes/page vs. Œcolampadius 2,390 and Lambert 1,287). Reflects the
  edition's narrower text-block and tighter typesetting, plus some
  layout-confusion at page edges (vertical pipes, stray glyphs at sample
  page 100).
- Quality: Latin recognizable; long-s pervasive (1543 typesetting); page-edge
  artefacts (`MEER`, `|`, `;`) appear in the OCR at the periphery of pages.
  Survey will need long-s normalization + edge-glyph filtering. `CAPVT
  DANIELIS` chapter markers are preserved (page 100 sample shows
  `CAPVT DANIELIS`).
- Daniel keyword density: 204 on `Danie`, 76 on `caput|capvt`, 51 on
  `visio|regnum|bestia` — solid density; one of the foundational Lutheran
  Daniel commentaries and the OCR is workable.

### Pt-2 / 7. Lambert — *In Apocalypsim* 1528 — **acceptable; Daniel cross-refs sparse (per audit M-3)** ✅

- File: `lambert-in-apocalypsim-1528.txt`
- Provenance URL: `https://books.google.com/books?id=GKtkAAAAcAAJ`
- Local PDF (cleared after K-5 commit, *not* tracked):
  `/Volumes/External/Logos4/daniel/Exegeseos_Francisci_Lamberti_in_sanctam.pdf`
- 30 MB / 689 pages / `Exegeseos, Francisci Lamberti ... in sanctam Diui
  Ioannis Apocalypsim, libri VII. In Academia Marpurgensi prælecti.
  [With the text.]` (matches PDF metadata; 1528 Marburg first edition).
- Output: 887 KB / 21,340 lines (= 21,334 OCR-body lines + 6-line preamble).
- Quality: Latin recognizable; long-s pervasive (1528 typesetting); page
  300 sample shows `domine Deus usquequo finis horum` cleanly.
- **Lambert is a Revelation commentary, not a Daniel commentary.** Per the
  audit's M-3 demotion (codex pass-2 M-1.5/B), Lambert's Daniel engagement
  is INFERRED via Rev 13 / 17 / 20 cross-references where Apocalypsim
  re-uses Dan 7's beasts + saints + millennial frame. The Wave-7 dispatch
  decides whether the Daniel-engaging density warrants a JSON or stays
  anthology-fallback.
- Keyword density (counts via `grep -c -i -E <pattern>` — case-insensitive
  matching-**line** counts, not raw occurrence counts; case-sensitive raw
  occurrences are slightly higher: 15 for `Danie`, 168 for the Revelation
  triplet):
  - `Danie` (Daniel-name): **14** matching lines — sparse, as expected
    for an Apocalypse commentary.
  - `caput|capvt` (chapter markers): **77** matching lines.
  - `visio|regnum|bestia` (Daniel-shared imagery): **55** matching lines.
  - `apocalyps|septem|millia.{0,10}anno`: **5** matching lines.
  - `draco|agnus|ierusalem` (Revelation core imagery): **164** matching
    lines — high, confirming Revelation focus.
- The 14:164 Daniel-name to Revelation-core-imagery ratio (matching-line
  count) matches the
  audit's framing of Lambert as Apocalypse-with-Daniel-cross-references,
  not Daniel-engaging primarily. Wave-7 survey should target Rev 13 /
  17 / 20 sections (where Dan 7 reception is concentrated) rather than
  walking the whole 689-page commentary.

### Pt-2 summary table

| Voice | Pt-2 OCR'd | Quality | Output | Long-s | Daniel-keyword density |
|---|---|---|---|---|---|
| Œcolampadius 1530 | ✅ pdf (manual-staged cache) | acceptable | `oecolampadius-in-danielem-1530.txt` (800 KB / 13,381 file-lines) | yes | 358 / 46 / 144 |
| Pellican | ❌ documented gap | n/a | (none — gap entry pending) | — | — |
| Melanchthon 1543 | ✅ pdf (manual-staged cache) | acceptable | `melanchthon-daniel.txt` (377 KB / 12,398 file-lines) | yes + edge artefacts | 204 / 76 / 51 |
| Lambert 1528 | ✅ pdf (manual-staged cache) | acceptable | `lambert-in-apocalypsim-1528.txt` (887 KB / 21,340 file-lines) | yes | 14 / 77 / 55 (sparse, per M-3) |

(Per-voice density numbers above are `grep -c -i -E` matching-line counts.
File-line counts include the 6-line manual-download preamble; subtract 6
for OCR-body line counts (13,375 / 12,392 / 21,334).)

### Pt-2 cumulative status (combined with Pt-1)

| Voice | OCR'd path | Status |
|---|---|---|
| 1. Cyril of Alexandria | archive-text (Mai vol 2 djvu) | ✅ acceptable |
| 2. Gregory PL 75 | pdf | ✅ clean (front-matter caveat) |
| 3. Bullinger 1571 | pdf | ✅ acceptable (long-s) |
| 4. Œcolampadius 1530 | pdf (Pt-2 manual-staged) | ✅ acceptable (long-s) |
| 5. Pellican | — | ❌ documented gap (PM applies entry before K-5) |
| 6. Melanchthon 1543 | pdf (Pt-2 manual-staged) | ✅ acceptable (long-s + edge) |
| 7. Lambert 1528 | pdf (Pt-2 manual-staged) | ✅ acceptable (Rev-not-Daniel; Daniel cross-refs sparse per M-3) |
| 8. Mede Latin | — | ❌ deferred (no open-access Latin scan; Cooper 1833 ET on english/ track is independent) |

**6 of 8 voices** now have OCR'd Latin originals ready for Wave-7 survey
dispatch. **1 voice** (Pellican) is a documented gap. **1 voice**
(Mede Latin) remains an audit follow-up.

### Pt-2 file-scope check

This Pt-2 session wrote only to `external-resources/latin/`:
- `oecolampadius-in-danielem-1530.txt` (new, this session)
- `melanchthon-daniel.txt` (new, this session)
- `lambert-in-apocalypsim-1528.txt` (new, this session)
- `_OCR-PREP-NOTES.md` (extended; original body preserved verbatim)

Source PDFs in `/Volumes/External/Logos4/daniel/` were read-only —
unmodified per dispatch boundary. Cache directories
`/tmp/extract-ocr-{oecolampadius-in-danielem-1530,melanchthon-daniel,lambert-in-apocalypsim-1528}/`
contain the staged source PDFs + per-page PNG/txt artefacts; can be
removed after K-5 commits.

> **Pt-1 mtime context (codex pass-2 advisory).** Pt-1 outputs:
> Gregory + Bullinger have mtime 2026-04-30 (Pt-1 OCR run);
> `cyril-alexandria-daniel-fragments.txt` has mtime 2026-05-01 08:19,
> reflecting the OCR-1.5 regeneration through the post-fix `archive-text`
> subcommand (not Pt-2 — Pt-2 staging began ~08:40 and Pt-2 only writes
> the three new files above plus this notes extension). Pt-1 file content
> integrity should be verified against the Pt-1 handoff hash (or a fresh
> `archive-text` re-run) before K-5 if any concern remains.
