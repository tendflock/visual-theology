# Method and Limits

A statement of what the WS0 / WS0.5 research does and does not do. This document is the
methodological apparatus a reader should consult before reading any of the scholar
surveys, the verification report, or the audit. It exists because "verified quote" is not
the same thing as "warranted academic claim," and the project's tooling enforces the first
but not the second.

## 1. Scope of the survey

The Daniel 7 pilot represents two overlapping corpora:

- **17 JSON-backed primary voices** (the surveyed corpus). Each produces a structured
  scholar JSON at `docs/research/scholars/<scholar>.json` with the dual-citation
  schema, every citation verified by `tools/citations.py:verify_citation`, and every
  file passing `tools/validate_scholar.py --strict`. Composition:
  - **WS0b** (4): Collins (*Hermeneia Daniel*), Walvoord, Blaising & Bock, Durham.
  - **WS0c** (13): Calvin, Goldingay, Hartman & Di Lella, Young, Beale, Pentecost,
    Duguid, Hamilton, Jerome, Theodoret, LaCocque, Menn, 1 Enoch Parables
    (Nickelsburg & VanderKam, treated as a *reception-event survey* rather than a
    single-author Daniel commentary).
- **9 narrative-only legacy voices** (referenced in
  `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` but **not**
  directly surveyed): Bauckham, Wright, Collins (*Apocalyptic Imagination*),
  Newsom & Breed, Longman, Lucas, Hoekema, Riddlebarger, Sproul. Citations to
  these voices are research-doc summary, not verified primary survey, and the
  bibliography marks each entry "Not JSON-backed" so downstream consumers can
  treat them accordingly. Several tradition clusters retain a narrative-only
  voice as their only representative (e.g. partial-preterist via Sproul,
  mediating-evangelical via Longman + Lucas, post-critical via Bauckham + Wright);
  the bibliography flags these cluster-level gaps explicitly per voice.

All 26 are catalogued in `docs/research/bibliography.md` with full edition data,
Logos resource identifiers, and explicit JSON-backed status. Two additional
entries appear there that are *not* surveys: Beeke & Smalley *RST 4* (the
schema's pages-and-sections fixture) and Anderson *ITC Daniel* (held in library,
acquisition-only).

## 2. Inclusion criteria

A scholar/work is included when **all** the following are true:

1. **Tradition representation.** They are a serious primary voice for at least one of the
   eleven Daniel 7 pilot axes (A, B, C, E, F, H, J, K, L, N, O), or one of the meta-axes
   P/Q where applicable.
2. **Logos availability.** A Logos library edition exists in the surveyed library and is
   readable by the project's reader (`tools/LogosReader/Program.cs`).
3. **Direct survey possible.** The scholar's actual prose can be read; we are not
   summarizing them through a critic. (Patterson's *NAC Revelation* is a useful secondary
   summary of dispensational positions, but it does not satisfy this criterion for
   dispensationalism — Walvoord does.)

A scholar represented only through an opponent's paraphrase is not included as a primary
voice for that tradition. This rules out building tradition X's position from
critic-of-X's prose. It is the rule that drove the WS0b push.

## 3. Acquired in WS0c expansion (2026-04-25/26)

The Daniel Expository Preaching Kit (Logos product 226248) plus targeted external
acquisitions added the following primary voices, which the earlier draft of §3 had
listed as out-of-corpus:

- **John Calvin, *Commentary on Daniel*** (`LLS:CALCOM27DA`) — surveyed as
  `calvin-daniel.json`. Reformed exegetical historic.
- **John Goldingay, *WBC Daniel* rev. 2019** (`LLS:WBC30REVED`) — surveyed as
  `goldingay-wbc-daniel.json`. Critical-mediating, deep on Aramaic + Dan 7:9–12.
- **Hartman & Di Lella, *Anchor Bible Daniel*** (`LLS:ANCHOR27DA`) — surveyed as
  `hartman-dilella-anchor-daniel.json`. US Catholic critical, distinct from Collins.
- **Edward J. Young, *Prophecy of Daniel*** (`LLS:PRPHCYDNLCMM`) — surveyed as
  `young-prophecy-of-daniel.json`. Reformed conservative-critical (closes the
  "Walvoord's strawman target" gap).
- **G. K. Beale, *Use of Daniel in Jewish Apocalyptic Lit and Revelation*** (`LLS:SDNLJWSHRVSTJHN`)
  — surveyed as `beale-use-of-daniel-in-revelation.json`. Cross-book / reception
  trajectory authority (Dan 7 → 1 En 37–71 → 4 Ezra → Mark 13 → Rev 1/13).
- **J. Dwight Pentecost, *Things to Come*** (`LLS:9780310873952`) — surveyed as
  `pentecost-things-to-come.json`. Second classical-dispensational voice (systematic
  eschatology, complements Walvoord's commentary).
- **Iain M. Duguid, *REC Daniel*** (`LLS:REC27DA`) — surveyed as
  `duguid-rec-daniel.json`. Reformed contemporary expository (fills the Calvin → Beeke
  gap).
- **James M. Hamilton Jr., *With the Clouds of Heaven*** (`LLS:NSBT32`) — surveyed as
  `hamilton-clouds-of-heaven.json`. Daniel biblical theology (Beale-school).
- **Jerome, *Commentary on Daniel*** (`LLS:JRMSCMMDNL`, Archer 1958 ET) — surveyed as
  `jerome-commentary-on-daniel.json`. Patristic Latin flagship; defends 6th-c date
  against Porphyry's Maccabean argument.
- **Theodoret of Cyrus, *In visiones Danielis prophetae*** (Migne PG 81 cols 1411–1437,
  TLG canon 4089.028; OCR'd from archive.org PG 81 scan to
  `external-resources/greek/theodoret-pg81-dan7.txt` plus Dan 5–6 and Dan 11–12 ranges).
  To be surveyed using the new `external-greek-ocr` citation backend.
- **André LaCocque, *The Book of Daniel*** (Cascade Books reissue, EPUB at
  `external-resources/epubs/9781498221689.epub`) — to be surveyed using the
  `external-epub` citation backend. Continental-French Catholic critical.
- **Jonathan Menn, *Biblical Eschatology* 2nd ed.** (EPUB at
  `external-resources/epubs/9781532643194.epub`) — to be surveyed via `external-epub`
  backend. Mediating historic-premillennial / covenantal-eclectic.
- **Anchor patristic-anthology coverage**: ACCS Daniel volume (`LLS:ACCSREVOT13`)
  surfaces extracts of Hippolytus, Theodoret, Augustine, Origen, Chrysostom, Cyril
  alongside body commentary — pending integration as a reception-anthology entry.
- **Reformation reception**: RCS Daniel/Ezekiel (`LLS:REFORMCOMMOT12`) surfaces
  Bullinger, Vermigli, Œcolampadius, Lambert, Brenz alongside Calvin — pending
  integration.

## 3a. Out of corpus — what remains genuinely missing

After the WS0c expansion, the following are still not represented (acknowledged
explicitly rather than hidden):

- **Continental German-language commentaries**. Klaus Koch's *Das Buch Daniel*
  (Erträge der Forschung 144, 1980) and BKAT XXII fascicles (1986+); Otto Plöger's
  *Das Buch Daniel* (KAT XVIII, 1965). German-only and not in any of the project's
  acquisitions.
- **Otto Plöger, *Theokratie und Eschatologie*** (1959; English 1968). Foundational
  for the post-exilic→apocalyptic-Judaism transition question. English translation
  out of print and not yet acquired.
- **Hippolytus, *Commentary on Daniel*** and ***Scholia on Daniel*** (Salmond ANF 5
  English, public domain via CCEL; Lefèvre SC 14 1947 Greek). The PDF
  `external-resources/pdfs/Hippolytus-EndTimes.pdf` covers his *On Christ and
  Antichrist* + *On the End of the World* but NOT the verse-by-verse Daniel
  commentary or scholia. Acquisition pending — CCEL plain-text fetch is the
  preferred path.
- **Theodoret of Cyrus full Greek for Dan 1–4 and Dan 8–10**. The OCR captures cols
  1411–1437 (Dan 7), 1362–1410 (Dan 5–6), 1493–1546 (Dan 11–12) directly from
  archive.org PG 81. Dan 1–3 is covered only by the legacy TLG-screenshot OCR;
  Dan 4 + Dan 8–10 partial. Hill 2006 SBL English translation (WGRW 7) is
  unobtainable online (out of stock at SBL Press / Brill paywall / dokumen.pub
  intermittent).
- **Hippolytus on Daniel in Greek** (Lefèvre SC 14 1947). Subscription / library.
- **Wright, *Jesus and the Victory of God*** (1996). Would deepen Wright on Dan 7
  → Jesus self-understanding beyond what *NTPG* (already surveyed) provides. Not
  in the Logos library.
- **Lay-popular eschatology** (Lindsey, LaHaye, Hagee). Referenced negatively
  through Collins's *Apocalyptic Imagination* §1415 critique; not surveyed as
  primary voices because they don't engage the academic axes.
- **Pentecostal-charismatic eschatology** in its specific contemporary forms.
  Walvoord + Pentecost cover the dispensational substrate; distinctively
  Pentecostal hermeneutics are not.
- **Roman Catholic post-Vatican II** beyond LaCocque (now in via EPUB). No magisterial
  document or modern RC commentary is surveyed. Hartman/Di Lella is the closest
  proxy but pre-Vatican-II in its theological sensibility.
- **Eastern Orthodox interpretive traditions**. No primary-voice survey. Theodoret
  is the only Greek-tradition voice and he is patristic-Antiochene, not modern
  Orthodox.
- **Non-English continental beyond LaCocque**. Klaus Berger, Hartmut Stegemann,
  Beate Ego — not represented.
- **Manuscript-critical apparatus**. The project does not engage the Old Greek vs.
  Theodotion textual question on Daniel substantively beyond passing references in
  surveyed scholars (Goldingay, Collins, Hartman/Di Lella note it; the project does
  not adjudicate).

## 4. Definition of "primary voice"

A primary voice for a tradition is a scholar whose work:

1. Is positionally claimed by self-identified members of the tradition as representative
   (Walvoord for classical dispensationalism; Hoekema for Reformed amillennialism;
   Collins for critical-modern Daniel scholarship).
2. Is cited from their own published prose, not paraphrased from a secondary summary or a
   critic.
3. Engages multiple pilot axes substantively (a single-axis specialist counts as a
   secondary voice).

This is not the same as "consensus voice." Within each tradition, intra-tradition
divergence is real (Hoekema vs Riddlebarger on the located-ness of the millennium;
Walvoord vs Blaising & Bock on inaugurated eschatology); both are surveyed and the
divergence is captured in their respective scholar JSONs.

## 5. Citation verification — what the tooling does and doesn't check

The verification mechanism (`tools/citations.py:verify_citation` and the sweep at
`tools/sweep_citations.py`) confirms that a stored `quote.text` appears in the cited
article, modulo whitespace and typographic punctuation normalization (curly↔straight
quotes, em/en dashes, ellipsis). It does **not** check:

- Whether the quote actually supports the rationale's broader claim. The
  `supportStatus` taxonomy (`directly-quoted` / `paraphrase-anchored` /
  `summary-inference` / `uncited-gap`) flags this distinction at the citation level, but
  the tooling does not adjudicate it. A citation tagged `directly-quoted` whose
  rationale outruns the quote is a calibration bug the verifier cannot catch.
- Whether the chosen quote represents the scholar's view fairly. Cherry-picking a
  contrarian aside is verifiable but unrepresentative; only adversarial human or codex
  review (WS0.5-6) catches this.
- Whether the cited article number is the optimal anchor. A position may have a stronger
  textual anchor in an adjacent article; the verifier accepts whatever article is named.

The sweep also reports a `demoted-to-paraphrase` count in its preamble: places in the
legacy markdown research where a previously-quoted claim was repaired by removing the
quotation marks and adding an explicit paraphrase note. These are research-doc summary,
not verified quotations, and downstream consumers should treat them as such.

## 6. Page numbers — empirical gap, not editorial laziness

The dual-citation schema's `frontend.page` field is null for every WS0b scholar JSON
file. This is empirical, not editorial: Logos exposes printed page numbers via an
embedded milestone-index database (`MilestoneIndexCerodDb.mstidx`,
`SegmentReferences_page` table), and that database is present only for some resources.
Of the WS0b-relevant works, only Beeke & Smalley's *RST 4* (`LLS:RFRMDSYSTH04`) has it.
The four primary-voice resources for Daniel 7 — Collins *Hermeneia*, Walvoord, Blaising
& Bock, Durham — do not. See `docs/research/2026-04-24-codex-logos-metadata-design.md`
for the empirical investigation.

For external academic review, this means citations against these four resources rely on
`nativeSectionId` plus heading rather than page number. A scholar with the print book in
hand can locate the cited material through the heading; a scholar with only an ISBN
needs the page. Closing this gap requires either a separate page-number ingestion (OCR
of print editions, or alternative editions with embedded pagination), or accepting that
the project is internally tracable but not yet print-locatable across all sources.

## 7. Editions and translations

The Logos resource-manager database records the digital edition of each resource file
(its `ResourceManager.Resources.Version` timestamp; see §8a below).
For older works whose print editions have multiple revisions:

- **Bauckham 1993** is the original SNTG print; the digital edition (2024) is a recut,
  not a revised edition.
- **Hoekema 1994** is the original Eerdmans print; the digital edition is a recut.
- **Riddlebarger 2013** is the *expanded* second edition, not the 2003 first.
- **Collins *Apocalyptic Imagination* 2016** is the third edition; the first (1984) is
  not surveyed.
- **Lucas 2002** is the AOTC first edition; revised printings exist.
- **Durham 1680** is the original imprint, surveyed as the digital reprint.

Quoted text in the scholar JSONs is bound by SHA-256 to the surveyed digital cut. If a
later cut renumbers articles or alters paragraph breaks, `verify_citation` will report
`partial` (case drift after typographic normalization) or `quote-not-found`. This is
edition-discipline, not edition-blindness.

## 8. Limits the project does not yet address

These are honest limits, not features:

- **No multi-edition disambiguation.** The project assumes a single digital edition per
  resource. Reconciling multiple editions of the same work would require a separate
  layer.
- **No formal claim-warrant check at scale.** WS0.5-6 codex audits a sample of strong
  commitments for rationale-vs-quote alignment, but not every position. A
  `directly-quoted` citation whose surrounding rationale is overspecified relative to
  the quote will pass tooling and only be caught by adversarial review.
- **No peer review.** No external scholar has reviewed these surveys or the
  taxonomy for representational fidelity. Internal reasoning, codex adversarial review,
  and quote verification are the only checks. External academic review is a future
  workstream and is required before any of this material is presented as a published
  scholarly apparatus.
- **No translation fidelity check.** Where surveyed works rely on English translations
  of Greek, Hebrew, Aramaic, or Latin sources, the project takes the surveyed scholar's
  translation choice without auditing it. Cross-translation comparison is out of scope.
- **No bibliography-style normalization for inline references inside the surveyed
  works.** When a surveyed scholar cites another work, that nested reference is not
  resolved or verified.
- **No preservation of pre-survey alternatives.** When a tradition has multiple
  reasonable primary-voice candidates (e.g. dispensationalism: Walvoord, Pentecost,
  Ryrie), the project picks one and notes the choice in the bibliography but does not
  survey the alternatives. Adding alternates is a future workstream.

## 8a. Note on date provenance and citation style

The parenthetical digital dates in `docs/research/bibliography.md` are
`ResourceManager.Resources.Version` timestamps, *not* `LibraryCatalog.Records.Version`
or `Records.ElectronicPublicationDate`. Verified for several entries:
`LLS:HRMNEIA27DA` ResourceManager.Version `2006-11-01T18:45:06Z` (matches bibliography);
`LLS:NIVAC27DA` ResourceManager.Version `2011-06-24T21:05:29Z` (catalog
ElectronicPublicationDate is 2010 — different field, different meaning); same shape for
Wright and Riddlebarger.

Citation style throughout `docs/research/bibliography.md` is SBL Handbook of Style
§6.4 / §6.4.2, not Chicago. (Earlier task labels in the workstream sometimes used
"SBL/Chicago" as shorthand for "monograph-style scholarly bibliography"; the actual
deliverable is SBL only.)

## 9. Reproducibility

Every claim in the scholar JSONs is reproducible to the extent that:

1. The named Logos resource is held in the operator's library at the recorded
   `ResourceManager.Resources.Version`.
2. The reader (`tools/LogosReader/Program.cs`) can open it.
3. `tools/citations.py:verify_citation` confirms the stored `quote.text` matches the
   article text (case-insensitive, whitespace-and-typography-normalized).

A second researcher with the same library and software can re-run
`python3 tools/sweep_citations.py --scholars docs/research/scholars --legacy-md
docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` and obtain a comparable
verification report.

A second researcher *without* the Logos library cannot reproduce the verification step.
That is a real reproducibility limit — the source corpus is not open. External academic
review would either need access to the Logos library or would need to verify against the
print editions (page numbers via `frontend.page` where available, otherwise via
`frontend.section` plus heading).
