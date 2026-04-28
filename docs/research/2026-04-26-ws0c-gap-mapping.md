# WS0c Gap Mapping — Daniel 7 Pilot Corpus

**Date:** 2026-04-26
**Author:** Claude (research-and-analysis session, working dir `/Volumes/External/Logos4`)
**Scope:** Map the academic-peer-review gap between the current 17-scholar JSON
corpus and the depth a hostile Daniel-7 reviewer would require, then sort every
named gap into one of four acquisition categories with verified pointers.
**Boundaries:** This document does **not** edit the corpus, schema, validators,
method-and-limits, or bibliography. It surfaces a roadmap for the PM session.

## 1. Overview

### 1.1 Why this exists

Bryan's standing instruction: the foundation of the visual-theology Daniel 7
pilot must reach **academic peer-review depth and scope before any visual
implementation**, because an honest three-tier (layman / pastor / scholar)
distillation is not extractable from a thin or biased corpus. Codex's
2026-04-26 audit returned *pass-with-conditions* on the WS0c expansion
(17 scholars, 418/418 verified citations) (418/418 reflects post-WS0c-cleanup
state; the earlier 426 figure was an in-flight intermediate before the
supportStatus relabel commits landed.); the relabel + repair work is in
flight on the same date, but pass-with-conditions does not equal
*peer-review-ready* for an external Daniel-7 reviewer. This document names
the depth gap concretely and points at the closest verified resources.

### 1.2 Method

1. Read the 17 scholar JSONs (3 deeply: Collins, Jerome, Walvoord; the rest
   skimmed for `traditionTag`, `passageCoverage`, axes, and `crossBookReadings`).
2. Build a peer-review rubric for the Daniel 7 pilot from the spec, audit, and
   method-and-limits docs.
3. Score the existing corpus against the rubric; name the under-anchored axes.
4. For each gap, classify by acquisition feasibility (in-library /
   freely-online / acquisition-needed / unobtainable) with a sqlite3-verified
   LLS-id or a fetch-verified URL.
5. Sequence the actionable gaps into dispatch waves of ≈5 surveys.

Every LLS-id below was confirmed by a SQL query against
`Data/e3txalek.5iq/LibraryCatalog/catalog.db`. Every URL below was fetched
during this session unless explicitly marked as inferred.

### 1.3 Trustable claim, hedge, vs. inferred — terminology used here

- **Verified.** Confirmed in this session by sqlite3 query (LLS-id) or by
  fetching the URL and observing the named text/page.
- **Inferred.** Probable but not yet checked end-to-end (e.g., a URL pattern
  consistent with a known directory; a Logos resource title that *should*
  contain the cited Daniel material but I did not open the article). Marked
  inline.
- **Honest gap.** I checked, did not find a free legitimate path, and did not
  manufacture one. Listed in §5d (unobtainable) or §5c (acquisition-needed).

---

## 2. Peer-Review-Depth Rubric for This Pilot

A hostile academic reviewer working on Daniel 7 — let's call her Dr. Reviewer,
familiar with the post-Collins critical guild, the Beale-school evangelical
guild, the patristic-reception guild, and the Jewish reception guild — would
look at this corpus and ask the questions below. *Each is a binary: either the
JSON corpus has it, or the corpus is not yet at peer-review depth for that
angle.* "Verified quote exists" is not the standard; "tradition is represented
from a primary voice in its own vocabulary, with multiple anchor points"
is.

### 2.1 Tradition-cluster minimums (≥2 JSON-backed primary voices per live cluster, ≥1 per reception cluster)

| cluster | floor | rationale |
|---|---:|---|
| critical-modern (Maccabean date, Greek 4th kingdom, Antiochus little horn, angelic Son of Man) | 3 | core mainline academic position; needs internal triangulation (Hermeneia, Anchor, Continental) |
| critical-mediating | 2 | accepts critical date but affirms canonical/theological authority; distinct from full critical |
| reformed-conservative-critical | 2 | conservative defense of 6th c. date and predictive prophecy without dispensationalism |
| classical-dispensational | 2 | a major North American tradition; Walvoord-style commentary + Pentecost-style systematic |
| progressive-dispensational | 2 | distinct hermeneutic from classical; needs a second voice (Saucy or Bock-and-Blaising co-author elsewhere) |
| reformed-amillennial | 2 | Hoekema-school + Riddlebarger-school + Beale-school divergence on kingdom-locus |
| historic-premillennial covenantal | 2 | Ladd-school; Menn covers some of this but is closer to amil |
| partial-preterist | 1 | Sproul / Gentry / Mathison range |
| historicist-Reformation | 1 | reception-history; Durham acceptable |
| irenic-evangelical-mediating | 2 | Davis / Longman / Lucas pattern |
| patristic-Greek (Antiochene + Alexandrian + Cappadocian) | 2 | Theodoret alone is Antiochene only; need Alexandrian / Asia-Minor patristic |
| patristic-Latin (anti-chiliast Western) | 2 | Jerome + Augustine / Hippolytus-Latin / Cassiodorus |
| medieval Jewish reception | 3 | Rashi (plain-meaning) + Ibn Ezra (grammatical) + at least one Sephardic voice (Abrabanel / ibn Yahya / Malbim) |
| Second-Temple reception | 3 | 1 Enoch Parables + 4 Ezra + Qumran (1QM / 4Q174 / 11Q13) at minimum |
| British biblical theology / post-critical | 2 | Wright + Bauckham (with Wright's Dan 7 discussion in *NTPG* and *JVG*) |
| Eastern Orthodox modern | 1 | not represented; if pilot claims tradition-spectrum breadth, at least 1 |

A rigorous reviewer treats *bibliography mention* and *narrative-only legacy
voice* as **not satisfying** the floor. Only the JSON-backed scholars count
for the rubric.

### 2.2 Patristic separation: Greek and Latin must be independent

Currently Theodoret (Greek-Antiochene) and Jerome (Latin) anchor the
patristic side. Dr. Reviewer would want at least:

- A second Greek patristic anchor distinct from the Antiochene school
  (Hippolytus of Rome, who writes in Greek in early 3rd c.; or Origen via
  fragments; or Cyril of Alexandria via fragments preserved in catenae /
  ACCS).
- A second Latin patristic anchor (Augustine, *De civitate Dei* XX, the
  load-bearing text for Latin amillennial Daniel reception; or Hippolytus's
  Latin-tradition reception via *De Antichristo* — though that work is
  originally Greek, the Latin fathers cite it).

### 2.3 Medieval Jewish reception is currently zero

The Daniel-7 Jewish exegetical tradition is unbroken from the Tannaitic
period through Saadia → Rashi → Ibn Ezra → Ramban → Ralbag → Abrabanel →
Malbim. The current corpus contains **no medieval or early-modern Jewish
voice**. For a Christian visual-theology site that claims to be honest about
tradition spectrum, this is the single largest deficiency. Dr. Reviewer
would mark this as failing.

### 2.4 Second-Temple reception beyond 1 Enoch Parables

Nickelsburg-VanderKam *1 Enoch Parables* covers 1 En 37-71 well. But
Daniel 7's reception in Second-Temple Judaism includes at minimum:

- **4 Ezra 11-13** (Eagle Vision, Man-from-the-Sea) — late 1st c. CE
  retargeting of the fourth beast onto Rome and the Son of Man onto a
  pre-existent messiah.
- **2 Baruch 39-40** — same period, similar move.
- **Qumran**: 1QM (War Scroll: Michael / two-tier angelology — Collins
  cites this), 4Q174 (Florilegium), 11Q13 (Melchizedek scroll: heavenly
  redeemer figure), 4Q243-245 (Pseudo-Daniel fragments), 4Q246 (Aramaic
  apocalyptic with Son-of-God language).
- **Sibylline Oracles** III, IV — Hellenistic-Jewish four-kingdoms reuse.

Currently in the corpus: only 1 En 37-71. Dr. Reviewer would mark Second-
Temple reception as a **single-witness cluster**; Beale's monograph engages
the broader literature, but Beale is the receiver-side authority, not a
primary-voice anchor for 4 Ezra etc.

### 2.5 Text-critical / Aramaic anchor

The Old Greek vs. Theodotion textual question on Daniel is touched by
Goldingay, Collins, and Hartman/Di Lella in passing. The corpus does not
adjudicate; method-and-limits §3a acknowledges this. Dr. Reviewer would
expect at least:

- A textual-criticism overview with explicit OG / Th / MT / 4QDan readings
  for the Dan 7:13 ("the one who came" vs. "as the one who came" — Old
  Greek's controversial reading).
- An Aramaic-grammar anchor for the chapter as a whole (Goldingay does
  this; the Lexham Aramaic Lexicon integration on the WS0c-9 queue would
  formalize it).

### 2.6 Per-topic coverage (Daniel 7's three pilot topics + two fold-ins)

Codex's audit table shows:

- **Four Beasts / Four Kingdoms** — strong (16+ scholars on Dan 7:7-8;
  14 on Dan 2:31-45). Sufficient.
- **Little Horn** — strong (16+ scholars on Dan 7:7-8; 13 on Dan 7:19-22).
  Sufficient.
- **Son of Man** — strong (17 on Dan 7:13-14). Sufficient. But
  cross-tradition triangulation on the Son-of-Man identity is thin in the
  Jewish-reception axis (only 1 Enoch Parables; no 4 Ezra Man-from-the-Sea
  voice; no Rashi / Ibn Ezra; no Aramaic Apocalypse 4Q246 voice).
- **Ancient of Days** — coverage exists in Dan 7:9-12 (11 scholars) but
  the iconographic / theological-identity question (is the Son of Man the
  same divine person as the Ancient of Days, or distinct? Old Greek's
  reading vs. Theodotion's) is patristic-territory and undertreated.
- **Saints receiving the kingdom** — Dan 7:15-18 has 9 scholars,
  Dan 7:23-27 has 17. Sufficient at the verse-block level.

### 2.7 Per-passage coverage (Daniel 7 + Dan 2/8/9/11-12)

Codex audit confirms borderline-thin passages: **Dan 9:1-19** (3 scholars:
Collins, Duguid, Walvoord — the prayer is unevenly engaged) and
**1 En 37-71** (3 — borderline). Genuine gap: **Dan 10:1-21** (0). The
mourning-prayer / angelic-mediator / Tigris-vision frame for chs. 10-12
is theologically generative (Michael, the prince of Persia, the Son-of-Man
prefigure in the man clothed in linen) and would matter if the pilot
visualizes the Daniel 7 Son-of-Man → Daniel 10 Man-in-Linen typological
through-line.

### 2.8 Cross-book NT use of Dan 7

Per codex audit:

- **Rev 1, Rev 13, Rev 17, Rev 20** — adequate (5-13 scholars each).
- **Matt 24, Mark 13** — 7 / 6 scholars. Adequate at the count level, but
  with relabel work pending (5 of those scholars over-applied
  `directly-quoted`).
- **Acts 7 (Stephen's vision: Son of Man standing)** — not in the
  controlled vocabulary; arguably should be.
- **2 Thess 2 (man of lawlessness)** — engaged in rationale text by
  Walvoord, Pentecost, Theodoret, Jerome but not as a controlled-vocabulary
  cross-book passage.
- **John 5:27** (Son-of-Man-judges allusion) — not engaged.
- **Heb 1, 2** (Christological echoes) — not engaged.

The current `crossBookReadings[]` schema covers Rev/Matt/Mark/1 En; if Dr.
Reviewer cared about the *wider* NT reception of Dan 7's Son of Man, the
vocabulary needs Acts 7, 2 Thess 2, John 5, possibly Heb 1.

### 2.9 Method-axis coverage

The pilot's 14+2 axes sit on the spec's `axes` catalog. The 17-JSON corpus
covers axes A, B, C, D, E, F, G, H, I, J, K, L, N, O, P with at least one
voice; the codex audit confirms each pilot axis A/B/C/D/E/F/G/H/I/J/K/L/N/O
has ≥4 voices except G (rapture timing — only Walvoord+Pentecost engage).
But hermeneutical-method axes (L, P) have lopsided representation:

- **L (hermeneutic)**: 13 voices, but heavily weighted toward
  Reformed/dispensational/literal-historical. Only Collins, Goldingay,
  Hartman/Di Lella, LaCocque represent religionsgeschichtlich /
  historical-critical method robustly. Dr. Reviewer would want one
  feminist-critical voice (e.g., Newsom, who is in library
  `LLS:OTL27DA` but not yet JSON-backed) and one
  postcolonial-critical voice to round out method.
- **P (meaning-locus / Axis P)**: only Collins represents it as a strong
  commitment in the JSON. The spec demotes P to a reading-rule, but if
  WS1 visualizes a meaning-locus axis, more voices are needed.

### 2.10 Summary rubric

A peer-review-ready Daniel 7 corpus, by §2.1-2.9, requires:

- ≥2 JSON-backed voices in every live tradition cluster (currently
  partial for ≥4 clusters).
- A second patristic-Greek voice independent of Antiochene Theodoret.
- A second patristic-Latin voice independent of Jerome.
- ≥3 medieval-Jewish primary voices (currently zero).
- ≥3 Second-Temple-reception voices (currently 1).
- A text-critical Aramaic anchor (currently passing references).
- Dan 10:1-21 coverage if visualized; else removed from vocabulary.
- A controlled-vocabulary expansion to cover Acts 7, 2 Thess 2 if those
  appear in NT-reception narrative.
- A feminist or postcolonial critical voice for method axis L.

The current corpus passes the verbal-verification gate (codex pass-with-
conditions, 418/418 verified post-WS0c-cleanup; 426 was the in-flight
intermediate). It does not pass the peer-review-depth gate.

---

## 3. Current Corpus Assessed Against the Rubric

### 3.1 Strong axes (peer-review-ready)

- **classical-dispensational** — Walvoord (commentary) + Pentecost
  (systematic). Two distinct work-types, internal triangulation.
- **reformed-conservative-critical** — Young is a single voice but the
  position is well-defined; sufficient.
- **patristic-Latin** (Jerome alone) — sufficient if Latin is taken as
  one voice; insufficient if internal triangulation desired.
- **patristic-Greek-Antiochene** — Theodoret. Sufficient as Antiochene
  voice; insufficient as the only Greek-tradition voice.
- **historicist-Reformation** — Durham. Sufficient as reception-history
  anchor; the spec already labels it non-live.
- **continental-Catholic-critical** — LaCocque. Single voice but
  distinctive.
- **biblical-theology / Beale-school** — Beale + Hamilton. Two voices,
  close kin but adequate.
- **second-temple-reception** — 1 Enoch Parables (Nickelsburg-VanderKam).
  *Single witness* — under-triangulated.
- **reformed-exegetical-historic** — Calvin alone; sufficient as
  historic anchor.
- **reformed-contemporary-expository** — Duguid alone; adequate.
- **critical-mediating** — Goldingay alone; adequate.

### 3.2 Thin axes (under-anchored)

- **critical-modern** — 4 voices (Collins, Hartman/Di Lella, Goldingay,
  LaCocque). *Quantity is fine; geographic and methodological diversity
  is acceptable (German-trained Hermeneia, US Catholic Anchor, British
  WBC, French Continental Catholic).* This is actually a strength, not
  a thin axis.
- **progressive-dispensational** — Blaising & Bock alone (one
  manifesto). Under-triangulated; needs Saucy or another progressive-disp
  voice.
- **covenantal-amillennial-eclectic** — Menn alone. Under-triangulated;
  could be strengthened by Hoekema (in library, not surveyed) or
  Riddlebarger (in library, not surveyed).

### 3.3 Absent axes (zero JSON-backed primary voices)

- **medieval-Jewish reception** — zero. (Rashi, Ibn Ezra, Ramban,
  Ralbag, Abrabanel, Malbim, Saadia, Yefet ben Eli all absent from
  corpus.)
- **partial-preterist** — zero JSON-backed (Sproul referenced
  narratively only; Gentry absent). The cluster is real.
- **historic-premillennial** — zero JSON-backed (Ladd absent).
- **post-critical / British biblical theology** — zero JSON-backed
  (Bauckham + Wright referenced narratively only).
- **mediating-evangelical / typological-restraint** — zero JSON-backed
  (Longman, Lucas, Davis referenced narratively only).
- **Eastern Orthodox modern** — zero.
- **patristic-Greek non-Antiochene** — zero (no Hippolytus, no Origen,
  no Cyril of Alexandria, no Cyril of Jerusalem, no Chrysostom on Daniel
  text).
- **patristic-Latin non-Jerome** — zero (no Augustine, no Cassiodorus).
- **Reformation non-Calvin** — zero (no Luther, no Bullinger, no
  Vermigli, no Œcolampadius, no Lambert, no Brenz).
- **second-Temple-reception beyond 1 Enoch** — zero (4 Ezra, 2 Baruch,
  Qumran, Sibylline Oracles all absent).
- **pre-Collins critical anchors** — zero (Driver Cambridge, Montgomery
  ICC, Charles ICC Revelation absent).
- **feminist / post-colonial critical** — zero (Newsom-Breed
  referenced narratively only).
- **Daniel-engaging Revelation commentaries** — Beale's
  *Use of Daniel in Revelation* is JSON-backed; Beale's NIGTC Revelation,
  Charles ICC Revelation, Patterson NAC, Koester are all in library but
  not surveyed. Dr. Reviewer would want at least 2 Revelation
  commentaries that exegete Rev 13/17/20 *with their own Dan 7 readings*,
  distinct from the Beale-monograph cross-book frame.

### 3.4 Codex-flagged conditions still material to peer-review depth

From the 2026-04-26 audit, beyond the 26 relabels (now applied per §7 of
the audit), four conditions remain that affect peer-review depth, not just
warrant calibration:

- **Theodoret OCR-quote tightening** (audit §6.5): some Greek fragments
  too short to bear the rationale. The PG 81 OCR text is in
  `external-resources/greek/theodoret-pg81-dan7.txt`; longer extractions
  would tighten Theodoret's evidentiary footing. Codex labeled this
  must-fix-before-WS1, deferred this session.
- **Reception-anthology integration** (ACCS Daniel + RCS Daniel) — both
  in library; the schema needs an "anthology-shape" variant to handle
  one Logos resource = many primary voices (Hippolytus, Origen, Augustine,
  Theodoret, Cyril within ACCS; Bullinger, Vermigli, Œcolampadius within
  RCS). This is a schema-extension blocker, not a survey blocker.
- **Aramaic-anchor field + Lexham Aramaic Lexicon integration**
  (WS0c-9): pending; would close the text-critical / linguistic anchor
  gap.
- **Manifest mismatch already addressed** (1 Enoch Parables backend
  manifest fixed in the audit's §7 close-out).

---

## 4. Gap Matrix (tradition × topic)

Format: `S` = sufficient (≥2 JSON-backed primary voices, or ≥1 where rubric
allows); `T` = thin (single voice, but represented); `0` = absent; `–`
= not applicable for that tradition. *Only JSON-backed counts.*

| tradition cluster | dating | 4 kingdoms | little horn | Son of Man | saints | NT use | method (L) |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| critical-modern | S | S | S | S | S | T | S |
| critical-mediating | T | T | T | T | T | T | T |
| reformed-conserv-critical | T | T | T | T | T | T | T |
| classical-disp | S | S | S | S | T | S | S |
| progressive-disp | T | T | T | T | T | – | T |
| reformed-amil | – | T | T | T | T | T | – |
| historic-premil | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| partial-preterist | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| historicist-Reformation | – | T | T | – | – | T | T |
| mediating-evangelical | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| patristic-Latin | T | T | T | T | T | T | T |
| patristic-Greek (Antiochene) | – | T | T | T | T | T | T |
| patristic-Greek (other) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| medieval-Jewish | 0 | 0 | 0 | 0 | 0 | – | 0 |
| second-Temple beyond 1 En | 0 | 0 | 0 | 0 | 0 | – | – |
| Reformation non-Calvin | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| post-critical (Wright/Bauckham) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Eastern Orthodox modern | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Daniel-engaging Rev. commentaries | – | – | – | – | – | T | – |
| evangelical-cross-book (Beale-school) | – | – | T | T | – | S | T |

`T` cells where the only voice is shared with another tradition (e.g., Jerome
covers patristic-Latin but is the only Latin Father in the corpus) collapse to
`single witness` under §2.1's rubric for clusters that need ≥2.

The matrix's most striking row is **medieval-Jewish: all zero**. The most
striking column is **method (L)**: only critical-modern is fully covered;
every other tradition's hermeneutic-method position rests on one voice.

---

## 5. Acquisition Classification

Each entry below carries a verification anchor:
- **In-library** items: LLS-id confirmed via sqlite3 query against
  `Data/e3txalek.5iq/LibraryCatalog/catalog.db` this session.
- **Freely-online** items: URL fetched this session (or in one case the
  fetch was inconclusive but archive.org search returned the identifier;
  I'll mark which is which).
- **Acquisition-needed** items: copyright + paid; defer with mitigation.
- **Unobtainable** items: language / out-of-print / unavailable; permanent
  gap.

### 5a. In-library (already in Logos library, just unsurveyed)

These resources are currently unsurveyed but readable by the existing reader.
Each LLS-id was sqlite3-verified this session. ★ marks resources that close
a tradition-cluster gap with ≥2 JSON-backed voices once surveyed.

#### Pre-Collins critical anchors (close the historical-critical baseline)

| # | scholar / work | LLS-id | tradition | priority |
|---|---|---|---|---|
| 1 | ★ Driver, *Daniel* (Cambridge Bible 1900) | `LLS:CAMBC27DA` | critical-modern (pre-Collins) | high |
| 2 | ★ Montgomery, *ICC Daniel* (1927) | `LLS:ICC_DA` | critical-modern (pre-Collins; Walvoord's named foil) | high |
| 3 | Lange/Zöckler, *Daniel* | `LLS:LANGE27DA` | 19c. confessional-critical | medium |
| 4 | Keil-Delitzsch OT Commentary (Daniel) | `LLS:29.2.11` | German conservative-critical 19c. | medium |

#### Major narrative-only legacy voices (close Hoekema/Riddlebarger/Newsom/Wright/Sproul gaps)

| # | scholar / work | LLS-id | tradition | priority |
|---|---|---|---|---|
| 5 | ★ Newsom & Breed, *OTL Daniel* (2014) | `LLS:OTL27DA` | critical-modern + reception-history | high |
| 6 | ★ Hoekema, *The Bible and the Future* | `LLS:BBLANDTHEFUTURE` | reformed-amil (heaven-located) | high |
| 7 | ★ Riddlebarger, *A Case for Amillennialism* | `LLS:CSAMLLNLSM` | reformed-amil (earth-located) | high |
| 8 | ★ Sproul, *The Last Days according to Jesus* | `LLS:LSTDYSCCRDNGJSS` | partial-preterist | high |
| 9 | ★ Wright, *Jesus and the Victory of God* (1996) | `LLS:JESUSVICTYGOD` | post-critical / British BT | **fixes a method-and-limits §3a error** |
| 10 | Wright, *NT and the People of God* (1992) | `LLS:NTPPLOFGOD` | post-critical / British BT | medium (already in bibliography) |
| 11 | Bauckham, *Theology of the Book of Revelation* | `LLS:NTTHEO87REV` | post-critical | medium |
| 12 | Collins, *The Apocalyptic Imagination* 3rd ed. | `LLS:PCLYPTCMGNTNPLT` | apocalyptic-genre studies | medium |

> **§3a correction (Wright JVG): method-and-limits.md states JVG is "not in
> the Logos library." sqlite3 confirms `LLS:JESUSVICTYGOD` is present and the
> file `JESUSVICTYGOD.logos4` exists at `Data/e3txalek.5iq/ResourceManager/Resources/`
> (3.5 MB, dated 2026-04-25). PM should amend §3a.**

#### Mediating-evangelical Daniel commentaries (close the Davis/Longman/Lucas gap)

| # | scholar / work | LLS-id | tradition | priority |
|---|---|---|---|---|
| 13 | ★ Longman, *NIVAC Daniel* | `LLS:NIVAC27DA` | mediating-evangelical | high |
| 14 | ★ Lucas, *Daniel* (AOT) | `LLS:AOT27DA` | mediating-evangelical (near-far) | high |
| 15 | Davis, *Message of Daniel* (BST) | `LLS:BST27DA` | reformed-pastoral | medium |
| 16 | Longman, *How to Read Daniel* | `LLS:HOWTOREADDANIEL` | methodological | low |
| 17 | Baldwin, *Daniel* (TOTC orig.) | `LLS:TOTC27DAUS` | moderate-evangelical-conservative | low |
| 18 | House, *Daniel* (TOTC new) | `LLS:TOTC27DAHOUSE` | moderate-evangelical-conservative | low |
| 19 | Miller, *Daniel* (NAC) | `LLS:29.32.3` | moderate-evangelical | low |

#### Reformed-evangelical / preaching Daniel commentaries (closer to homiletics, still primary-voice)

| # | scholar / work | LLS-id | tradition | priority |
|---|---|---|---|---|
| 20 | Tanner, *Daniel* (EEC) | `LLS:EEC27DA` | dispensational-evangelical recent | medium |
| 21 | Sprinkle, *Daniel* (EBTC) | `LLS:EBTC27DA` | reformed-evangelical biblical-theology | medium |
| 22 | Helm, *Daniel for You* (GWFY) | `LLS:GWFY27DA` | popular-expository | low |
| 23 | Akin, *Exalting Jesus in Daniel* | `LLS:9780805496895` | Christ-centered / homiletical | low |
| 24 | Greidanus, *Preaching Christ from Daniel* | `LLS:PRCHNGCHRSTDNL` | reformed-typological-homiletic | low |
| 25 | Schwab, *Hope in the Midst of a Hostile World* | `LLS:GSPLOTDANIEL` | reformed-pastoral | low |
| 26 | Harman, *Daniel* (EP Study) | `LLS:EVPRESS27DA` | reformed-evangelical | low |
| 27 | Fyall, *Daniel: A Tale of Two Cities* (FOTB) | `LLS:FOBC27DA` | reformed-expository | low |
| 28 | Pace, *Daniel* (Smyth & Helwys) | `LLS:SHC27DA` | moderate critical Baptist | medium |
| 29 | Seow, *Daniel* (WBC Westminster) | `LLS:WBCS27DA` | moderate critical | medium |
| 30 | Davies, *Daniel* (Sheffield Old Testament Guides) | `LLS:SHEFFCL27DA` | critical-introductory | medium |
| 31 | Anderson, *Signs and Wonders* (ITC) | `LLS:ITC21DAN` | critical-mainline | low |
| 32 | Towner, *Daniel* (Interpretation) | `LLS:29.32.6` | moderate-critical preaching | low |

#### Pre-modern English Daniel commentaries (in library, low priority for pilot but available)

| # | scholar / work | LLS-id | tradition | priority |
|---|---|---|---|---|
| 33 | Spence (Pulpit Comm.) Daniel | `LLS:29.32.9` | 19c. homiletical | low |
| 34 | Barnes Notes Daniel V1 | `LLS:BARNES27DA01` | 19c. American Reformed | low |
| 35 | Barnes Notes Daniel V2 | `LLS:BARNES27DA02` | 19c. American Reformed | low |
| 36 | Cowles, Ezekiel and Daniel | `LLS:COWLES26EZE` | 19c. American | low |
| 37 | Simeon, *Horae Homileticae* 9 (Jer–Dan) | `LLS:HH09` | 19c. Anglican-Reformed homiletical | low |
| 38 | Leupold, *Daniel* | `LLS:LEUPOLD27DA` | amillennial classic (Walvoord's foil) | medium |
| 39 | Gangel, *Daniel* | `LLS:WS_0_3437` | popular-expository | low |
| 40 | Gingrich, *Daniel* | `LLS:GNG27DA` | popular | low |
| 41 | Mangano, *Esther and Daniel* (CPC) | `LLS:CPC_ESTHDAN` | moderate-evangelical | low |
| 42 | Lederach, *Daniel* | `LLS:29.32.8` | moderate-evangelical | low |
| 43 | Thompson, *Ezekiel and Daniel* (Cornerstone) | `LLS:CSTONECM26EZE` | moderate-evangelical | low |
| 44 | Fyall-Sydserff, *Teaching Daniel* | `LLS:TCHDANIEL` | reformed-homiletical | low |
| 45 | Butler, *Daniel: The Man of Loyalty* | `LLS:BBS21DANIEL` | popular | low |
| 46 | Caldwell, *Outline Study of Daniel* | `LLS:NTLNSTBKDNL` | popular | low |
| 47 | Barrett, *God's Unfailing Purpose* | `LLS:UNFAILPRPSE` | reformed-pastoral | low |
| 48 | Péter-Contesse & Ellington, *UBS Handbook on Daniel* | `LLS:34.0.149` | translation handbook | low |
| 49 | Exell, *Daniel* (Biblical Illustrator) | `LLS:BBLCLLLSTRTRDNL` | 19c. homiletical | low |

#### Patristic primary voices in library (close patristic-Greek-non-Antiochene + patristic-Latin-non-Jerome gaps)

ANF and NPNF series 1 + 2 are present complete in the library. Each volume is
sqlite3-verified.

| # | source | LLS-id | content relevant to Dan 7 |
|---|---|---|---|
| 50 | ★ ANF 5: Hippolytus, Cyprian, Novatian | `LLS:6.50.5` | **Hippolytus *Fragments on Daniel* + *Treatise on Christ and Antichrist* + *Discourse on the End of the World*** — fully patristic-Greek (Hippolytus writes in Greek; the ANF translation is from Greek originals + fragments). The PDF `external-resources/pdfs/Hippolytus-EndTimes.pdf` is **redundant** with this Logos resource. |
| 51 | ★ Augustine, *City of God* (standalone) | `LLS:CITYOFGOD` | Book XX is the load-bearing Latin amillennial reading of Dan 7 + Rev 20 |
| 52 | NPNF 1.2: Augustine *City of God* + *Christian Doctrine* | `LLS:6.60.2` | duplicate of (51) for cross-citation |
| 53 | NPNF 2.7: Cyril of Jerusalem, Gregory Nazianzen | `LLS:6.60.21` | Cyril, *Catechetical Lecture* XV on Antichrist (cites Dan 7 explicitly) |
| 54 | NPNF 1.10: Chrysostom Homilies on Matthew | `LLS:6.60.10` | engages Matt 24 (Olivet → Dan 9:27 / Dan 7) |
| 55 | NPNF 2.3: Theodoret historical writings + Jerome | `LLS:6.60.17` | secondary Theodoret reception (already JSON-backed via PG 81 OCR) |
| 56 | ANF 4: Tertullian, Origen | `LLS:6.50.4` | Origen Dan 7 fragments scattered |
| 57 | ANF 6: Gregory Thaumaturgus, Methodius | `LLS:6.50.6` | Methodius engages eschatology |
| 58 | ANF 7: Lactantius, Victorinus | `LLS:6.50.7` | Victorinus *Commentary on the Apocalypse* engages Dan 7 + Rev 13/17 |
| 59 | NPNF 2.10 Ambrose | `LLS:6.60.24` | Ambrose's Daniel engagement scattered through letters |

#### Reception-anthology resources (close ACCS / RCS gap, but require anthology-shape schema first)

| # | source | LLS-id | content |
|---|---|---|---|
| 60 | ★ ACCS OT XIII: Ezekiel, Daniel | `LLS:ACCSREVOT13` | extracts of Hippolytus, Theodoret, Augustine, Origen, Chrysostom, Cyril of Alexandria, Cyril of Jerusalem, Gregory the Great on Daniel — 70+ patristic voices |
| 61 | ★ RCS OT XII: Ezekiel, Daniel | `LLS:REFORMCOMMOT12` | Bullinger, Vermigli, Œcolampadius, Lambert, Brenz, Pellican, Calvin (cross-cite), Melanchthon, Bullinger again — Reformation reception |

#### Daniel-engaging Revelation commentaries (close Daniel-7-via-Revelation method)

| # | scholar / work | LLS-id | tradition |
|---|---|---|---|
| 62 | ★ Beale, *NIGTC Revelation* | `LLS:29.71.18` | reformed-amillennial; Beale-school cross-book authority distinct from Beale's *Use of Daniel in Revelation* monograph (already JSON-backed) |
| 63 | ★ Charles, *ICC Revelation* (1920) | `LLS:ICC_REV` | early-critical Revelation, cited by all subsequent scholars |
| 64 | ★ Patterson, *NAC Revelation* | `LLS:NAC39` | dispensational Revelation companion to Walvoord's Daniel |
| 65 | ★ Koester, *Revelation and the End of All Things* 2nd ed. | `LLS:RVLTNNDLLTHNGS2ED` | Lutheran / historical-critical Revelation |
| 66 | Mounce, *Romans* (NICNT) | `LLS:29.50.10` | (NB: this is Mounce's Romans, not his Revelation; flagged for caution — Mounce Revelation is the NICNT Revelation but was not in this query) |
| 67 | Morris, *Revelation* (TNTC) | `LLS:TNTC87REUS` | moderate-evangelical |
| 68 | Paul, *Revelation* (TNTC new) | `LLS:TNTC87REVPAUL` | newer TNTC |
| 69 | Beale, *John's Use of the OT in Revelation* | `LLS:JHNSSTSTMNRVLTN` | distinct from Beale's *Use of Daniel* monograph; broader OT reception |
| 70 | Beale-Carson, *Commentary on the NT Use of the OT* | `LLS:COMNTUSEOT` | one-stop NT-citing-OT reference |
| 71 | Lange/Craven, *Revelation* | `LLS:LANGE87RE` | 19c. confessional-critical |
| 72 | Wilcock, *Message of Revelation* (BST) | `LLS:BSTUS87RE` | reformed-pastoral |
| 73 | Spence, *Revelation* (Pulpit Comm.) | `LLS:29.71.17` | 19c. homiletical |

#### Partial-preterist primary voice (close cluster gap)

| # | scholar / work | LLS-id | tradition |
|---|---|---|---|
| 74 | ★ Gentry, *The Beast of Revelation* | `LLS:BEASTREVELATION` | partial-preterist — the standard primary-voice anchor; fills the Sproul-narrative-only gap |

#### Second-Temple-reception + apocalyptic-genre primary anchors (close 4 Ezra / 2 Baruch / Qumran gap)

| # | scholar / work | LLS-id | content |
|---|---|---|---|
| 75 | ★ Charlesworth, *OT Pseudepigrapha* Vol 1 | `LLS:OTPSEUD01` | **4 Ezra (= 2 Esdras 3-14), 2 Baruch, Sibylline Oracles, Apocalypse of Abraham** — primary texts |
| 76 | Charlesworth, *OT Pseudepigrapha* Vol 2 | `LLS:OTPSEUD02` | additional pseudepigrapha |
| 77 | Charles, *Apocrypha and Pseudepigrapha of the OT* (APOT 1913) | `LLS:1.0.13` (Apocrypha vol) + `LLS:33.0.2` (Pseudepigrapha vol) | older standard translations of same texts |
| 78 | ★ Lexham DSS Hebrew-English Interlinear | `LLS:LDSSHEIB` | **Qumran Daniel-relevant texts: 1QM (War Scroll, Michael two-tier), 4Q174 (Florilegium), 11Q13 (Melchizedek), 4QDan-a/b/c, 4Q243-245 (Pseudo-Daniel), 4Q246 (Aramaic apocalyptic Son of God)** |
| 79 | Collins, *Daniel* (FOTL) | `LLS:FRMOTLIT27DA` | apocalyptic-genre framework + Daniel; distinct from Collins Hermeneia |
| 80 | Collins, *Oxford Handbook of Apocalyptic Literature* | `LLS:OXFORDHBKAPOCLIT` | 30+ chapters, including Daniel reception, Qumran, 4 Ezra |

#### Tooling support (Lexham Aramaic Lexicon for WS0c-9)

| # | scholar / work | LLS-id | priority |
|---|---|---|---|
| 81 | Lexham Aramaic Lexicon (per existing handoff queue) | `LLS:FBARCLEX` (per WS0c-9 handoff; not re-verified this session) | medium (already on queue) |

#### Total in-library candidates: **80** (item 81 already on queue)

### 5b. Freely-online (legitimate, fetch-verified URL)

Each URL was fetched this session. Sefaria URLs returned HTTP 200 with content
matching the named text. archive.org identifiers were resolved against the
search API and confirmed by metadata fetch.

#### Medieval / early-modern Jewish reception (closes the medieval-Jewish gap)

All Sefaria pages are full-text + verse-by-verse navigable. Hebrew + English
where translated; some entries Hebrew-only.

| # | scholar / work | URL | content scope |
|---|---|---|---|
| F1 | ★ Rashi on Daniel (1040-1105) | https://www.sefaria.org/Rashi_on_Daniel | All 12 chapters; plain-meaning rabbinic |
| F2 | ★ Ibn Ezra on Daniel (12c.) | https://www.sefaria.org/Ibn_Ezra_on_Daniel | All 12 chapters; grammatical-philological |
| F3 | ★ Joseph ibn Yahya on Daniel (Bologna 1538) | https://www.sefaria.org/Joseph_ibn_Yahya_on_Daniel | All 12 chapters; Sephardic post-Iberian-expulsion |
| F4 | Metzudat David on Daniel (Altschuler c. 1740-1780) | https://www.sefaria.org/Metzudat_David_on_Daniel | Verse-by-verse plain-meaning; all 12 chapters |
| F5 | Metzudat Zion on Daniel (companion to F4) | https://www.sefaria.org/Metzudat_Zion_on_Daniel | Lexical companion |
| F6 | Minchat Shai on Daniel (Yedidiah Norzi 1626) | https://www.sefaria.org/Minchat_Shai_on_Daniel | Masoretic textual notes |
| F7 | ★ Malbim on Daniel (1809-1879) | https://www.sefaria.org/Malbim_on_Daniel | All 12 chapters; modern Hebrew anti-Haskalah |
| F8 | Steinsaltz on Daniel (modern Orthodox 20-21c.) | https://www.sefaria.org/Steinsaltz_on_Daniel | Modern Orthodox commentary |

> Sefaria's URLs use `Joseph_ibn_Yahya` (lowercase `ibn`); verified via the
> Sefaria API call `/api/index/Joseph%20ibn%20Yahya%20on%20Daniel`. Page
> returned HTTP 200 with title `יוסף אבן יחיא על דניאל` and 12 chapters,
> 333 verses, 376 comments. Composition c. 1514-1534, published Bologna 1538.

#### Pre-Collins critical anchors via archive.org (public domain, full text)

| # | scholar / work | URL | year | format |
|---|---|---|---|---|
| F9 | ★ Driver, *Cambridge Bible Daniel* | https://archive.org/details/bookofdanielwith00unse | 1900 | PDF + EPUB + plain text |
| F10 | ★ Montgomery, *ICC Daniel* | https://archive.org/details/criticalexegetic22montuoft | 1927 | PDF + EPUB + plain text |
| F11 | ★ Pusey, *Daniel the Prophet* (9 Oxford lectures) | https://archive.org/details/danielprophetnin0000puse | 1885 (orig. 1864) | PDF + EPUB + plain text |
| F12 | ★ Charles, *Apocrypha and Pseudepigrapha* Vol 2 (incl. 4 Ezra, 2 Baruch) | https://archive.org/details/apocryphapseudep02charuoft | 1913 | PDF + EPUB + plain text |
| F13 | Charles, *Book of Enoch* | https://archive.org/details/thebookofenoch00unknuoft | 1893 | PDF + EPUB + plain text |
| F14 | Mede, *Clavis Apocalyptica* (Cooper trans.) | https://archive.org/details/atranslationmed00medegoog | 1833 | PDF + plain text |
| F15 | Hippolytus, *Part of the Commentary on Daniel* (Greek+English; Georgiades 1888) | https://archive.org/details/partofcommentary00hipp | 1888 | PDF + plain text — **partial only**; ANF 5 (Logos `LLS:6.50.5`) is the better source |

> NB: F12-F14 cover Second-Temple reception (4 Ezra, 2 Baruch in Charles vol 2;
> 1 Enoch separately) and historicist-Reformation primary sources (Mede). The
> Logos library has Charlesworth's OTP, which is the modern translation;
> Charles APOT is the older comparable. F11's Pusey is the historic
> conservative-Anglican Daniel-defense voice (against Driver and the
> Tübingen school).

#### Patristic Daniel reception (free, but Logos library is preferred where it has the same)

| # | source | URL | note |
|---|---|---|---|
| F16 | Jerome on Daniel (English + Latin) | https://www.tertullian.org/fathers/index.htm#Jerome (`jerome_daniel_02_text.htm` for the text) | already JSON-backed via Logos `LLS:JRMSCMMDNL`; URL is backup |
| F17 | Hippolytus on Daniel (CCEL ANF 5, English) | https://ccel.org/ccel/hippolytus/fragments/anf05 | partial fetch (CCEL pages render partly client-side); content matches Logos `LLS:6.50.5` ANF 5 |

> **Inferred:** The CCEL ANF 5 URLs for individual sub-sections (e.g.,
> `Fragments_from_Commentaries/Daniel`) were not reliably fetched this
> session (the CCEL site uses dynamic rendering). The same content is in
> the Logos library at `LLS:6.50.5` and is the recommended primary source.

#### Total freely-online verified URLs: **17** (8 Sefaria + 7 archive.org + 2 patristic backup)

### 5c. Acquisition-needed (paid; defer with mitigation)

These are genuinely valuable but require purchase. Each entry names a
mitigation (which existing in-corpus scholar engages this voice in their
secondary literature) where possible.

| # | scholar / work | reason | mitigation |
|---|---|---|---|
| A1 | Stuckenbruck, *1 Enoch 91-108* (Hermeneia 2007) | extends Second-Temple anchor beyond the Parables; covers 1 En 91-104 (Apocalypse of Weeks, Epistle of Enoch) | partially mitigated by Beale, *Use of Daniel in Jewish Apocalyptic Lit*, who engages Stuckenbruck's English translation |
| A2 | Stuckenbruck, *1 Enoch 1-36* (Hermeneia 2007) | Book of the Watchers — Enochic framework that the Parables presuppose | not directly mitigated; Beale + Hamilton touch some material |
| A3 | Yarbro Collins, *Cosmology and Eschatology in Jewish and Christian Apocalypticism* (Brill 1996) | major reception study | partial via Collins (her husband, distinct field but cross-cited) and Hamilton |
| A4 | Wright, *Resurrection of the Son of God* (CoQG 3, 2003) | Daniel 7 + resurrection / vindication framework | partially via Wright NTPG + JVG (both in library) |
| A5 | Caird, *Revelation* (HNTC 1966) | classic preterist-leaning Revelation; older but still cited | mitigated by Bauckham (in library) for some themes |
| A6 | Henze, *Jewish Apocalypticism in Late First Century Israel* (Mohr Siebeck 2011) | major 4 Ezra + 2 Baruch reception study | partially via Charlesworth OTP texts (in library); secondary engagement via Collins Apocalyptic Imagination |
| A7 | Theodoret of Cyrus, *Commentary on Daniel* — Hill English trans. (WGRW 7, SBL 2006) | parallel English to PG 81 Greek (already OCR'd) | mitigated: PG 81 OCR is in `external-resources/greek/theodoret-pg81-dan*.txt`; Theodoret JSON-backed via Greek-OCR backend |
| A8 | Newsom, *Daniel* (OTL 2014) — *if* the Logos edition's text differs from print | ✗ already in Logos `LLS:OTL27DA` — **not actually acquisition-needed** | n/a (move to in-library) |
| A9 | Mounce, *Revelation* (NICNT 1977 / 2nd ed. 1998) | mainstream evangelical Revelation engaging Dan 7 | partial via Beale NIGTC + Patterson NAC (both in library) |
| A10 | Beasley-Murray, *Revelation* (NCB 1974) | British evangelical Revelation | mitigated by Beale + Patterson |
| A11 | Aune, *Revelation 1-22* (WBC 3 vols. 1997-1998) | the largest critical Revelation commentary; engages Dan 7 reception extensively | partial mitigation via Beale's footnotes citing Aune; Charles ICC available free (F12-style) |
| A12 | Hartman, *Asking for a Meaning* (CBQMS 1979) — early standalone Daniel monograph | Hartman's stand-alone Dan 7 work | mostly mitigated by Hartman/Di Lella Anchor (in JSON corpus) |

#### Total acquisition-needed: **11** (one was misclassified — Newsom is in-library; effective count is 11)

### 5d. Unobtainable (permanent gap)

These cannot be closed via any free-or-paid path the project can pursue at
current resources. Each entry names the permanence reason.

| # | scholar / work | reason permanent |
|---|---|---|
| U1 | Klaus Koch, *Das Buch Daniel* (Erträge der Forschung 144, 1980) | German only; no ET; no digital |
| U2 | Klaus Koch, *Daniel* (BKAT XXII fascicles, 1986+) | German only; no ET |
| U3 | Otto Plöger, *Das Buch Daniel* (KAT XVIII, 1965) | German only; ET (*Theocracy and Eschatology* 1968) out of print, not digital |
| U4 | Klaus Berger, *Daniel*-related works | German only; specialized monographs |
| U5 | Hartmut Stegemann, *Daniel*-related works | German only; specialized |
| U6 | Beate Ego, *Daniel*-related works | German only; specialized |
| U7 | Hippolytus, *Commentary on Daniel* — Lefèvre SC 14 1947 (Greek + French) | subscription Sources Chrétiennes; library access required |
| U8 | Yefet ben Eli on Daniel — Margoliouth ed. (1889) | Karaite Judeo-Arabic; rare 1889 OUP edition; not on archive.org |
| U9 | Saadia Gaon on Daniel | only fragments survive in Judeo-Arabic; no consolidated ET |
| U10 | Ramban (Nahmanides) on Daniel | Sefaria 404; Ramban did not write a complete Daniel commentary; references only in his other works |
| U11 | Ralbag (Gersonides) on Daniel | Sefaria 404; Ralbag's Daniel commentary survives but is not online-digitized in any free repository found this session |
| U12 | Eastern Orthodox modern academic commentary on Daniel | no English-language Orthodox Daniel commentary located; tradition is liturgical/homiletical, not academic-monograph |
| U13 | Pentecostal-charismatic distinctively-eschatological Daniel commentary | no academic primary-voice work located; field is popular not scholarly |
| U14 | Roman Catholic post-Vatican II magisterial commentary on Daniel | LaCocque is the closest proxy (in JSON); no magisterial document directly engages Dan 7 exegesis at length |
| U15 | Sergius Bulgakov, *Apocalypse of John* — Dan 7 reception | Russian original; English (Bulgakov, *Apocalypse*, Eerdmans 2019) is in print, would be acquisition-needed; but no free Daniel-specific text available |
| U16 | Pre-Tannaitic Jewish Daniel reception (Talmud / Midrash) | scattered through Bavli + Yerushalmi + various midrash; no consolidated commentary; would require survey by hand |
| U17 | Babylonian / Persian context primary literature on apocalyptic motifs (cuneiform, Zoroastrian) | specialist primary-source field; out of pilot scope |

#### Total unobtainable: **17**

---

## 6. Prioritized Survey Roadmap

Goal: close the **medieval-Jewish, partial-preterist, post-critical, 4-Ezra/Qumran,
patristic-non-Antiochene-Greek, patristic-non-Jerome-Latin, mediating-evangelical,
narrative-only-legacy, and pre-Collins-critical** gaps via dispatch waves of ≤5
parallel surveys. Each wave is sized to fit within the 4-5-concurrent-survey
ceiling Bryan and codex established in earlier waves.

Order is by **value-per-effort**: fastest tradition-cluster gap-closers first;
schema-extension-needing surveys last (anthology-shape work for ACCS / RCS).

> NB: each dispatch will need a per-scholar prompt that *does* identify the
> Bryan-side context (axes A-O, controlled vocabulary for `passageCoverage[]`,
> dual-citation schema, supportStatus discipline). For Sefaria-sourced
> surveys, a new external backend (e.g., `external-sefaria` or generic
> `external-html` with API-driven URL per verse) would be needed; or, simpler,
> manual extract-and-store using the existing `external-pdf`-style pattern
> with a saved Sefaria HTML/text export. PM should rule on backend.

### Wave A — high-value narrative-only legacy backfill (5 surveys, all in-library, no schema work)

These are the names already cited narratively but lacking JSON. Closing them
removes ≥6 codex-flagged "tradition-cluster relies on bibliography-only voice"
notes from `bibliography.md`.

| dispatch | scholar | LLS-id | tradition closure |
|---|---|---|---|
| A1 | Newsom & Breed *OTL Daniel* | `LLS:OTL27DA` | critical-modern + reception-history (Newsom's reception chapters are unique) |
| A2 | Hoekema *Bible and the Future* | `LLS:BBLANDTHEFUTURE` | reformed-amil (heaven-located) — pairs with Riddlebarger |
| A3 | Riddlebarger *Case for Amillennialism* | `LLS:CSAMLLNLSM` | reformed-amil (earth-located) — pairs with Hoekema |
| A4 | Sproul *Last Days according to Jesus* | `LLS:LSTDYSCCRDNGJSS` | partial-preterist (cluster has zero JSON-backed) |
| A5 | Wright *Jesus and the Victory of God* | `LLS:JESUSVICTYGOD` | post-critical / British BT — pairs with Bauckham (next wave) |

**Estimated wall time:** 4-5h subagent dispatch + 1h verification.
**Outcome:** 5 traditions move from `narrative-only` to `JSON-backed`; the
method-and-limits §3a Wright-JVG error is fixed in passing; codex's
manifest-mismatch §6.3 critique is closed.

### Wave B — patristic non-Jerome / non-Antiochene voices (5 surveys, in-library)

The hardest wave — each requires patristic-text discipline (knowing where in
ANF/NPNF the Daniel material appears, since these aren't standalone Daniel
commentaries). Worth dispatching with an explicit *`patristic-survey` briefing*
that calls out section anchors (e.g., NPNF 1.2 = Augustine *City of God* Bk
XX) and warns about the type/antitype layered reading.

| dispatch | source | LLS-id | content anchor |
|---|---|---|---|
| B1 | Hippolytus *Fragments on Daniel* + *Treatise on Christ and Antichrist* + *Discourse on End of World* (ANF 5) | `LLS:6.50.5` | patristic-Greek non-Antiochene (Roman, 3rd c.) — **closes patristic-Greek-other gap**; supersedes the redundant `external-resources/pdfs/Hippolytus-EndTimes.pdf` |
| B2 | Augustine *City of God* Bk XX | `LLS:CITYOFGOD` (or NPNF `LLS:6.60.2`) | patristic-Latin non-Jerome — **closes patristic-Latin-other gap**; the load-bearing Latin amillennial reading |
| B3 | Cyril of Jerusalem *Catechetical Lecture* XV (NPNF 2.7) | `LLS:6.60.21` | 4th c. Greek patristic; explicit Antichrist + Dan 7 reading |
| B4 | Victorinus *Commentary on the Apocalypse* (ANF 7) | `LLS:6.50.7` | early Latin Revelation commentary; Daniel 7 cross-references; pre-Augustinian millenarian sympathy |
| B5 | Chrysostom *Homilies on Matthew* selections re Matt 24 (NPNF 1.10) | `LLS:6.60.10` | 4th c. Greek; Matt 24/Olivet → Dan 7 + Dan 9:27 link |

**Estimated wall time:** 6-8h (patristic surveys are slower); needs the
patristic-extension briefing. **Outcome:** patristic-Greek and patristic-Latin
clusters each move from `single voice` to `≥2 voices`.

### Wave C — pre-Collins critical anchors (5 surveys, in-library + freely-online supplement)

| dispatch | scholar | source | tradition closure |
|---|---|---|---|
| C1 | Driver *Daniel* (Cambridge Bible 1900) | `LLS:CAMBC27DA` (in-library) or F9 archive.org (backup) | pre-Collins critical — Walvoord's stated foil pair with Montgomery |
| C2 | Montgomery *ICC Daniel* (1927) | `LLS:ICC_DA` (in-library) or F10 archive.org (backup) | pre-Collins critical — Walvoord's stated foil pair with Driver |
| C3 | Charles *ICC Revelation* (1920) | `LLS:ICC_REV` (in-library) | pre-Beale critical Revelation, Daniel 7 cross-references |
| C4 | Lange/Zöckler *Daniel* | `LLS:LANGE27DA` | 19c. confessional-critical; bridge between conservative and critical |
| C5 | Pusey *Daniel the Prophet* | F11 archive.org (1885; not in library) | 19c. conservative-Anglican defense; Driver's named opponent |

**Estimated wall time:** 4-5h. **Outcome:** historical-critical baseline
established; Walvoord's "Maccabean date is anti-supernaturalist" rhetoric
gets a triangulated 19c.-early-20c. critical chorus to test against.

### Wave D — mediating-evangelical (Davis/Longman/Lucas) cluster (3 surveys, low effort)

This cluster currently has zero JSON-backed voices but is real per codex
audit §4. All three are in-library.

| dispatch | scholar | LLS-id | tradition closure |
|---|---|---|---|
| D1 | Davis *Message of Daniel* (BST) | `LLS:BST27DA` | mediating-evangelical (typological-restraint, "antichrists before the Antichrist") |
| D2 | Longman *NIVAC Daniel* | `LLS:NIVAC27DA` | mediating-evangelical (transhistorical-recurrence) |
| D3 | Lucas *Daniel* (AOT) | `LLS:AOT27DA` | mediating-evangelical (near-far fulfillment) |

**Estimated wall time:** 3-4h. **Outcome:** mediating-evangelical cluster
moves from `narrative-only` to `JSON-backed (3 voices)`. Codex's
"irenic-evangelical-mediating tradition is real" finding gets validated.

### Wave E — medieval-Jewish reception (5 Sefaria surveys, requires new external backend)

This is the highest-value gap by §2.3, and it requires schema work first
(a Sefaria backend or `external-html` backend with manual extract). Needs
PM ratification before dispatch.

| dispatch | scholar | URL | tradition closure |
|---|---|---|---|
| E1 | Rashi on Daniel | F1 Sefaria | medieval-Jewish (plain-meaning, 11c. France) |
| E2 | Ibn Ezra on Daniel | F2 Sefaria | medieval-Jewish (grammatical-philological, 12c. Spain) |
| E3 | Joseph ibn Yahya on Daniel | F3 Sefaria | early-modern Jewish (16c. Italy/Iberian-exile) |
| E4 | Malbim on Daniel | F7 Sefaria | modern-Hebrew (19c. anti-Haskalah) |
| E5 | Steinsaltz on Daniel | F8 Sefaria | modern-Orthodox (20-21c.) |

**Prerequisite:** new backend kind (proposed: `external-sefaria` or
`external-html` with `passageRef` + URL slug). Verifier needs to fetch
HTML, strip tags, normalize Hebrew (NFC), and match-and-store. Not
trivial; allow 1-2 days for backend + 1-2 days for surveys.

**Estimated wall time:** 4-5h surveys plus 1-2 days backend work.
**Outcome:** medieval-Jewish gap (the single largest deficiency)
closes from zero to 5 voices. Pilot can credibly claim Jewish reception.

### Wave F — Second-Temple beyond 1 Enoch + Qumran (3 surveys, mixed in-library)

| dispatch | source | LLS-id | tradition closure |
|---|---|---|---|
| F1-(s) | Charlesworth *OTP Vol 1* (4 Ezra 11-13 + 2 Baruch 36-40) | `LLS:OTPSEUD01` | Second-Temple reception: 4 Ezra Eagle Vision + 2 Baruch parallel; treat as a *reception-event survey* like 1 Enoch Parables |
| F2-(s) | Lexham DSS Hebrew-English: 1QM, 4Q174, 11Q13, 4Q246, 4Q243-245 | `LLS:LDSSHEIB` | Qumran reception of Dan 7 motifs (Michael two-tier, heavenly redeemer, Son-of-God language) |
| F3-(s) | Charlesworth *OTP* + Charles APOT comparing Sibylline Oracles III + IV on four-kingdoms reuse | `LLS:OTPSEUD01` + `LLS:OTPSEUD02` | Hellenistic-Jewish reuse of Dan 2/7 four-kingdoms; brief survey |

**Estimated wall time:** 6-8h (these are reception-event surveys, not
single-author — slower per dispatch). Schema-extension question: should
each Qumran scroll get its own JSON (1QM-survey, 4Q246-survey)? PM rules.

**Outcome:** Second-Temple cluster moves from 1 → 4 voices. Pilot's claim
to engage the broader pre-Christian Jewish reception holds up.

### Wave G — partial-preterist + Daniel-engaging Revelation (5 surveys, in-library)

| dispatch | scholar | LLS-id | tradition closure |
|---|---|---|---|
| G1 | Gentry *Beast of Revelation* | `LLS:BEASTREVELATION` | partial-preterist (the JSON-backed primary voice) |
| G2 | Beale *NIGTC Revelation* | `LLS:29.71.18` | reformed-amil major Revelation; cross-book authority distinct from Beale's *Use of Daniel in Revelation* |
| G3 | Patterson *NAC Revelation* | `LLS:NAC39` | dispensational Revelation companion to Walvoord-Daniel |
| G4 | Koester *Revelation and the End of All Things* | `LLS:RVLTNNDLLTHNGS2ED` | Lutheran historical-critical Revelation |
| G5 | Bauckham *Theology of the Book of Revelation* | `LLS:NTTHEO87REV` | post-critical (pairs with Wright JVG from Wave A) |

**Estimated wall time:** 5-6h. **Outcome:** partial-preterist and
post-critical clusters each get JSON-backed voices; Daniel's downstream
in Revelation gets multi-voice triangulation.

### Wave H — historic-premillennial + supplementary critical (3 surveys, mixed library)

| dispatch | scholar | LLS-id | tradition closure |
|---|---|---|---|
| H1 | Ladd *Theology of the New Testament* | `LLS:THEONTLADD` | historic-premillennial (Ladd's eschatological synthesis is in his TNT, not a Daniel commentary; treat similarly to Pentecost) |
| H2 | Pace *Daniel* (Smyth & Helwys) | `LLS:SHC27DA` | moderate critical Baptist; fills out critical-mediating |
| H3 | Seow *Daniel* (Westminster Bible Companion) | `LLS:WBCS27DA` | moderate critical |

**Estimated wall time:** 4h. **Outcome:** historic-premil cluster gains
its first JSON-backed voice; critical-mediating gains depth.

### Wave I — anthology-shape schema + ACCS / RCS (deferred until schema work; 2 anthology surveys after)

This is a schema-design effort, not a survey-dispatch wave. Once the
anthology-shape JSON variant is designed (one anthology JSON file =
many primary-voice extracts, each with its own backend anchor and
own scholar attribution), two surveys land:

| dispatch | source | LLS-id | tradition closure |
|---|---|---|---|
| I1 | ACCS OT XIII (Ezekiel/Daniel) | `LLS:ACCSREVOT13` | patristic-anthology: Hippolytus, Theodoret, Augustine, Origen, Chrysostom, Cyril Jerusalem, Cyril Alexandria, Gregory the Great, Ephraem |
| I2 | RCS OT XII (Ezekiel/Daniel) | `LLS:REFORMCOMMOT12` | Reformation-anthology: Bullinger, Vermigli, Œcolampadius, Lambert, Brenz, Pellican, Melanchthon |

**Estimated effort:** 2-3 days schema design + 6-8h surveys per anthology.
**Outcome:** patristic-anthology and Reformation-anthology clusters move
from absent to richly populated.

### Wave J — schema-only support work (Lexham Aramaic Lexicon integration; per existing handoff queue)

WS0c-9 from the handoff is an in-library tooling integration, not a survey.
Per the Aramaic-anchor rubric in §2.5, this should land before WS1.

### Cumulative coverage projection after Waves A-H (without I, J)

After Waves A-H (32 dispatches across 8 waves, ~30-35 working hours
subagent + ~10h verification + 1-2 days backend for Wave E):

- Tradition-cluster floor in §2.1: **all** clusters except Eastern-Orthodox
  modern have ≥1 JSON-backed voice; live clusters except mediating-evangelical
  (3 voices), reformed-amil (3 voices), critical-modern (still 4), and
  classical-disp (still 2) move toward ≥2 voices.
- Patristic-Greek and patristic-Latin each gain a second voice.
- Medieval-Jewish moves from 0 to 5 voices.
- Second-Temple from 1 to 4 voices.
- Pre-Collins critical baseline established (Driver, Montgomery, Charles ICC).
- Mediating-evangelical, partial-preterist, post-critical, historic-premil
  all gain their first JSON-backed voices.

**Remaining honest gaps after Wave H:** Eastern-Orthodox modern,
Pentecostal-charismatic, post-Vatican-II RC magisterial, German-only
critical, pre-Tannaitic Jewish (these are the §5d unobtainable items).

These remaining gaps should be flagged in `method-and-limits.md` as
permanent under §7 below.

---

## 7. Permanent Gaps (for `docs/research/method-and-limits.md`)

(I am not editing the file. The PM session should integrate these.)

The following should be added to `method-and-limits.md` §3a as permanent
limits, *with reasons*:

1. **No Eastern Orthodox modern academic Daniel commentary surveyed.** The
   Eastern Orthodox Daniel reception tradition is liturgical and
   homiletical, not academic-monograph; no English-language Orthodox
   Daniel monograph located. Mitigation: Theodoret (already JSON-backed)
   is patristic-Antiochene Greek but predates the Orthodox-Catholic
   split.

2. **No Pentecostal-charismatic distinctively-eschatological commentary
   surveyed.** The field is popular-devotional (Hagee, Lindsey, LaHaye)
   without academic primary-voice work. Walvoord + Pentecost cover the
   dispensational substrate.

3. **No post-Vatican-II Roman Catholic magisterial commentary on
   Daniel surveyed.** No magisterial document directly engages Dan 7
   exegesis at length. LaCocque and Hartman/Di Lella (both JSON-backed)
   are the closest Catholic proxies; both pre-Vatican-II in
   theological sensibility.

4. **No German-only continental commentaries surveyed.** Klaus Koch
   (*Das Buch Daniel* + BKAT XXII), Otto Plöger (*Das Buch Daniel*
   KAT), Klaus Berger, Hartmut Stegemann, Beate Ego — all German with
   no English translation; not actionable.

5. **No pre-Tannaitic Jewish reception (Talmud, Midrash) consolidated
   survey.** Talmudic and midrashic Daniel-7 references are scattered
   across Bavli, Yerushalmi, and various midrash-collections; no
   consolidated commentary exists. Survey would require manual
   extraction of every relevant Talmud passage, beyond pilot scope.

6. **No primary-text engagement with Babylonian / Persian apocalyptic
   parallel literature.** Cuneiform "vaticinium ex eventu" (Akkadian
   prophecy texts) and Zoroastrian apocalyptic (Bahman Yasht) are
   relevant background per Collins's religio-historical method;
   specialist primary-source field; out of pilot scope.

7. **No Saadia Gaon on Daniel.** Saadia's Daniel commentary survives
   only fragmentarily in Judeo-Arabic; no consolidated English
   translation. Yefet ben Eli on Daniel (Margoliouth 1889) was rare and
   is not freely-online.

8. **No comprehensive Aramaic textual-criticism / Old Greek vs.
   Theodotion treatment.** The corpus passes references (Goldingay,
   Collins, Hartman/Di Lella); no scholar JSON adjudicates
   text-critical questions on Dan 7:13 (OG "as the Ancient" vs. Th
   "to the Ancient"). Lexham Aramaic Lexicon integration (WS0c-9 on
   handoff queue) addresses linguistic anchoring; textual-criticism
   adjudication is a future workstream.

9. **No Hippolytus Lefèvre SC 14 1947 Greek-French edition.** The 1888
   Georgiades partial edition is on archive.org (free, partial); the
   ANF 5 English fragments are in-library (`LLS:6.50.5`); the
   complete Greek-French SC 14 1947 edition is subscription-only.

10. **Theodoret OCR-quote tightening deferred.** Codex audit §6.5 noted
    several Greek fragments too short to bear the rationale; the PG 81
    text is in `external-resources/greek/theodoret-pg81-dan7.txt` for
    a future tightening pass. Not a permanent gap, but a documented
    deferred item.

In addition, **method-and-limits.md §3a should be amended** to remove the
claim that *Wright, Jesus and the Victory of God* is "not in the Logos
library." sqlite3 confirms `LLS:JESUSVICTYGOD` is present and the file
`JESUSVICTYGOD.logos4` exists at the standard Resources path (3.5 MB,
2026-04-25 dated). Wright JVG should move from §3a's "not in library"
list to the *narrative-only legacy voices in library* category.

---

## 8. Appendix: Copy-Paste Targets

For the next PM session to dispatch surveys without re-doing the legwork.

### 8.1 In-library LLS-ids (sqlite3-verified this session)

```
# Pre-Collins critical
LLS:CAMBC27DA            Driver, Daniel (Cambridge Bible 1900)
LLS:ICC_DA               Montgomery, ICC Daniel (1927)
LLS:LANGE27DA            Lange/Zöckler, Daniel
LLS:29.2.11              Keil-Delitzsch OT Commentary (Daniel)
LLS:ICC_REV              Charles, ICC Revelation (1920)

# Major narrative-only legacy → backfill
LLS:OTL27DA              Newsom & Breed, OTL Daniel
LLS:BBLANDTHEFUTURE      Hoekema, Bible and the Future
LLS:CSAMLLNLSM           Riddlebarger, Case for Amillennialism (Expanded ed.)
LLS:LSTDYSCCRDNGJSS      Sproul, Last Days according to Jesus
LLS:JESUSVICTYGOD        Wright, Jesus and the Victory of God (1996)
LLS:NTPPLOFGOD           Wright, NT and the People of God (1992)
LLS:NTTHEO87REV          Bauckham, Theology of the Book of Revelation
LLS:PCLYPTCMGNTNPLT      Collins, The Apocalyptic Imagination 3rd ed.

# Mediating-evangelical Daniel commentaries
LLS:NIVAC27DA            Longman, NIVAC Daniel
LLS:AOT27DA              Lucas, Daniel (AOT)
LLS:BST27DA              Davis, Message of Daniel (BST)
LLS:HOWTOREADDANIEL      Longman, How to Read Daniel
LLS:TOTC27DAUS           Baldwin, Daniel (TOTC)
LLS:TOTC27DAHOUSE        House, Daniel (TOTC new)
LLS:29.32.3              Miller, Daniel (NAC)

# Reformed-evangelical / preaching Daniel
LLS:EEC27DA              Tanner, Daniel (EEC)
LLS:EBTC27DA             Sprinkle, Daniel (EBTC)
LLS:GWFY27DA             Helm, Daniel for You
LLS:9780805496895        Akin, Exalting Jesus in Daniel
LLS:PRCHNGCHRSTDNL       Greidanus, Preaching Christ from Daniel
LLS:GSPLOTDANIEL         Schwab, Hope in the Midst of a Hostile World
LLS:EVPRESS27DA          Harman, Daniel (EP Study)
LLS:FOBC27DA             Fyall, Daniel: Tale of Two Cities (FOTB)
LLS:SHC27DA              Pace, Daniel (Smyth & Helwys)
LLS:WBCS27DA             Seow, Daniel (Westminster Bible Companion)
LLS:SHEFFCL27DA          Davies, Daniel (Sheffield)
LLS:ITC21DAN             Anderson, Signs and Wonders (ITC)
LLS:29.32.6              Towner, Daniel (Interpretation)

# Pre-modern English Daniel (low priority)
LLS:29.32.9              Spence (Pulpit) Daniel
LLS:BARNES27DA01         Barnes Notes Daniel V1
LLS:BARNES27DA02         Barnes Notes Daniel V2
LLS:COWLES26EZE          Cowles, Ezekiel and Daniel
LLS:HH09                 Simeon, Horae Hom 9 (Jer-Dan)
LLS:LEUPOLD27DA          Leupold, Daniel (amil — Walvoord's foil)
LLS:WS_0_3437            Gangel, Daniel
LLS:GNG27DA              Gingrich, Daniel
LLS:CPC_ESTHDAN          Mangano, Esther and Daniel (CPC)
LLS:29.32.8              Lederach, Daniel
LLS:CSTONECM26EZE        Thompson, Ezekiel and Daniel (Cornerstone)
LLS:TCHDANIEL            Fyall-Sydserff, Teaching Daniel
LLS:BBS21DANIEL          Butler, Daniel: Man of Loyalty
LLS:NTLNSTBKDNL          Caldwell, Outline Study of Daniel
LLS:UNFAILPRPSE          Barrett, God's Unfailing Purpose
LLS:34.0.149             Péter-Contesse & Ellington, UBS Handbook on Daniel
LLS:BBLCLLLSTRTRDNL      Exell, Daniel (Biblical Illustrator)

# Patristic primary voices (in-library, non-anthology)
LLS:6.50.5               ANF 5 (Hippolytus on Daniel + Christ-and-Antichrist + End of World)
LLS:CITYOFGOD            Augustine, City of God (standalone)
LLS:6.60.2               NPNF 1.2 Augustine City of God + Christian Doctrine
LLS:6.60.21              NPNF 2.7 Cyril of Jerusalem (Catechetical XV) + Gregory Nazianzen
LLS:6.60.10              NPNF 1.10 Chrysostom Homilies on Matthew (Olivet)
LLS:6.60.17              NPNF 2.3 Theodoret historical writings + Jerome
LLS:6.50.4               ANF 4 Tertullian, Origen
LLS:6.50.6               ANF 6 Methodius
LLS:6.50.7               ANF 7 Lactantius, Victorinus (Apocalypse)
LLS:6.60.24              NPNF 2.10 Ambrose

# Reception-anthology resources (need anthology-shape schema)
LLS:ACCSREVOT13          ACCS OT XIII Ezekiel / Daniel
LLS:REFORMCOMMOT12       RCS OT XII Ezekiel / Daniel

# Daniel-engaging Revelation
LLS:29.71.18             Beale, NIGTC Revelation
LLS:NAC39                Patterson, NAC Revelation
LLS:RVLTNNDLLTHNGS2ED    Koester, Revelation and the End of All Things 2nd ed.
LLS:JHNSSTSTMNRVLTN      Beale, John's Use of OT in Revelation
LLS:COMNTUSEOT           Beale-Carson, Commentary on NT Use of OT
LLS:LANGE87RE            Lange/Craven, Revelation
LLS:BSTUS87RE            Wilcock, Message of Revelation (BST)
LLS:TNTC87REUS           Morris, Revelation (TNTC)
LLS:TNTC87REVPAUL        Paul, Revelation (TNTC new)
LLS:29.71.17             Spence (Pulpit) Revelation

# Partial-preterist
LLS:BEASTREVELATION      Gentry, Beast of Revelation

# Second-Temple + apocalyptic-genre
LLS:OTPSEUD01            Charlesworth, OT Pseudepigrapha Vol 1 (4 Ezra, 2 Baruch, Sib. Or., Apoc. Abr.)
LLS:OTPSEUD02            Charlesworth, OT Pseudepigrapha Vol 2
LLS:1.0.13               Charles, APOT Vol 1 (Apocrypha)
LLS:33.0.2               Charles, APOT Vol 2 (Pseudepigrapha)
LLS:LDSSHEIB             Lexham DSS Hebrew-English Interlinear
LLS:FRMOTLIT27DA         Collins, Daniel (FOTL)
LLS:OXFORDHBKAPOCLIT     Collins, Oxford Handbook of Apocalyptic Literature

# Tooling
LLS:FBARCLEX             Lexham Aramaic Lexicon (for WS0c-9)

# Historic-premillennial proxy
LLS:THEONTLADD           Ladd, Theology of the New Testament
```

### 8.2 Freely-online URLs (fetch-verified this session unless marked inferred)

```
# Sefaria (medieval / early-modern Jewish; all HTTP 200, all 12 chapters of Daniel)
https://www.sefaria.org/Rashi_on_Daniel                  # Rashi, 11c. France
https://www.sefaria.org/Ibn_Ezra_on_Daniel                # Ibn Ezra, 12c. Spain
https://www.sefaria.org/Joseph_ibn_Yahya_on_Daniel        # Bologna 1538
https://www.sefaria.org/Metzudat_David_on_Daniel          # Altschuler c. 1740-1780
https://www.sefaria.org/Metzudat_Zion_on_Daniel           # companion lexical
https://www.sefaria.org/Minchat_Shai_on_Daniel            # Norzi 1626 masoretic
https://www.sefaria.org/Malbim_on_Daniel                  # 19c. modern-Hebrew
https://www.sefaria.org/Steinsaltz_on_Daniel              # 20-21c. modern-Orthodox

# archive.org (pre-Collins critical, public domain)
https://archive.org/details/bookofdanielwith00unse        # Driver Cambridge Bible Daniel 1900
https://archive.org/details/criticalexegetic22montuoft    # Montgomery ICC Daniel 1927
https://archive.org/details/danielprophetnin0000puse      # Pusey Daniel the Prophet 1885
https://archive.org/details/apocryphapseudep02charuoft    # Charles APOT Vol 2 1913 (4 Ezra, 2 Baruch)
https://archive.org/details/apocryphapseudep00char        # Charles APOT Vol 1 1913 (Apocrypha)
https://archive.org/details/thebookofenoch00unknuoft      # Charles Book of Enoch 1893
https://archive.org/details/atranslationmed00medegoog     # Mede Clavis Apocalyptica 1833
https://archive.org/details/partofcommentary00hipp        # Hippolytus partial Daniel 1888 (Greek+English)

# Patristic backup (Logos resources are primary)
https://www.tertullian.org/fathers/index.htm#Jerome       # Jerome on Daniel (already in Logos as LLS:JRMSCMMDNL)
https://ccel.org/ccel/hippolytus/fragments/anf05          # Hippolytus ANF 5 (CCEL; same content as LLS:6.50.5)

# Inferred (URL pattern consistent with site structure but not end-to-end fetched this session)
# https://ccel.org/ccel/schaff/anf05/anf05.iv.iv.iii.html   — Hippolytus On Daniel sub-section per CCEL ANF 5 structure (couldn't confirm; CCEL pages render dynamically)
```

### 8.3 File paths in repo (for survey briefings)

```
external-resources/pdfs/Hippolytus-EndTimes.pdf           # NOTE: redundant with LLS:6.50.5; flag for removal in cleanup
external-resources/greek/theodoret-pg81-dan7.txt          # Theodoret OCR Dan 7 (existing)
external-resources/greek/theodoret-pg81-dan5_6.txt
external-resources/greek/theodoret-pg81-dan11_12.txt
external-resources/greek/migne-pg81-archiveorg/           # PG 81 PDF + page index + fts.txt
external-resources/epubs/9781498221689.epub               # LaCocque (already JSON-backed)
external-resources/epubs/9781532643194.epub               # Menn (already JSON-backed)
docs/research/scholars/_SURVEY_BRIEFING.md                # template; needs patristic-extension + Sefaria-extension when those waves dispatch
docs/schema/citation-schema.md                            # backend kinds: logos, external-epub, external-greek-ocr, external-pdf; needs external-sefaria + external-html for medieval-Jewish; needs anthology-shape variant for ACCS/RCS
tools/citations.py                                        # backend.kind dispatch
tools/validate_scholar.py                                 # passageCoverage vocab; needs vocabulary extension for Acts 7, 2 Thess 2, John 5 if those passages are added
tools/sweep_citations.py                                  # works against new backends transparently
```

### 8.4 Backend / schema work prerequisite for waves

| wave | prerequisite |
|---|---|
| A, B, C, D, G, H | none — existing `logos` backend works |
| E (medieval-Jewish) | new `external-sefaria` or `external-html` backend; verifier handles Hebrew NFC + HTML stripping; ≈1-2 days |
| F (Second-Temple beyond 1 En) | none for Charlesworth OTP and DSS in library; treat as additional reception-event surveys per 1 Enoch Parables pattern |
| I (ACCS/RCS anthologies) | anthology-shape schema variant: one anthology JSON file = many primary-voice extracts, each with its own backend anchor and own scholar attribution; ≈2-3 days schema design + integration |
| J (Aramaic lexicon) | already on WS0c-9 queue (Lexham Aramaic Lexicon `LLS:FBARCLEX` integration; estimated 3h per existing handoff) |

### 8.5 Briefing-update notes (for `_SURVEY_BRIEFING.md` extension)

- **Patristic-extension briefing** (Wave B): callouts for ANF/NPNF section
  anchors; warn about type/antitype layered Antiochus → Antichrist reading;
  note that Augustine's *City of God* Bk XX is the load-bearing Latin
  text for amillennial Dan 7 + Rev 20.
- **Sefaria-extension briefing** (Wave E): URL patterns; verse-by-verse
  navigation; Hebrew NFC + transliteration handling; treat each Sefaria
  commentator as a *single-author scholar* (not reception-event), but
  with grandparent-text context (Tanakh) treated separately.
- **Reception-event briefing** (already exists for 1 Enoch Parables;
  apply to Wave F's 4 Ezra + 2 Baruch + Qumran in same pattern; treat
  Qumran scrolls as *reception-event surveys* with multiple sub-text
  citations rather than single-author scholars).
- **Anthology-shape briefing** (Wave I): one JSON per anthology resource;
  each `position` includes a `primaryVoice` field (e.g.,
  `primaryVoice: "Augustine"`); citations dispatch to ACCS internal
  numbering rather than to the surveyed scholar's primary-source LLS-id.
  Schema design pending PM ratification.

---

GAP-MAPPING COMPLETE — **effective / actionable counts**: 80 in-library, 17 freely-online, 11 acquisition-needed, 17 unobtainable. (Raw table-row counts are 81/17/12/17, but (i) entry 81 in the in-library table is "already on queue" (excluded); (ii) Newsom (a gap-map acquisition-needed entry) was sqlite3-verified in-library at `LLS:OTL27DA` (excluded from acquisition-needed). Effective counts: 80/17/11/17.)
