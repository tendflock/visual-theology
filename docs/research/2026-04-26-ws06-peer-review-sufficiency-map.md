# WS0.6 — Peer-Review Sufficiency Map (Daniel 7 Pilot)

**Date:** 2026-04-26
**Author:** Claude (synthesis-and-rubric session, working dir `/Volumes/External/Logos4`)
**Inputs:** PM-Charter; the 2026-04-26 gap-mapping doc; the WS0c handoff; the visual-theology architecture spec; method-and-limits; bibliography; the dual-citation schema; deep-sample of 5 scholar JSONs (Calvin, Collins, Jerome, Theodoret, 1 Enoch Parables) plus header-scan of all 17.
**Boundary:** This document does **not** modify scholar JSONs, the gap-mapping doc, schema/validators, method-and-limits, bibliography, or any code. It produces a per-mini-dossier rubric the PM session uses to dispatch downstream work.

---

## 1. Overview — Rubric vs. Gap List

The 2026-04-26 gap-mapping doc inventories what the corpus is missing and where each missing piece could come from. It is an **input-side** view: tradition clusters, axes, passages, voices.

This document is the **output-side** view. The unit is the *mini-dossier* — the deliverable the visual-theology pilot will write per Daniel-7 movement and per reception arc. A mini-dossier is **PASS** when its required source classes, required claims, and per-tier sufficiency thresholds are all met by the JSON-backed corpus. Anything less is **PARTIAL** or **FAIL**.

The rubric is binary at the threshold (verified-quote count ≥ floor; required source classes present; primary voice distinguished from corroborators) and explicit at the tier (layman / pastor / scholar). Codex's framing applies: "verified quote exists" is not the standard; "tradition is represented from a primary voice in its own vocabulary, with multiple anchor points" is.

The corpus passes the verbal-verification gate (codex pass-with-conditions; current re-sweep returns **418 / 418 verified** — earlier WS0c handoffs reported 426 / 426 against an in-flight intermediate state, but the corpus committed to scholar JSONs is 418 citations across `positions[]` + `crossBookReadings[]`). It does not yet pass the per-mini-dossier sufficiency gate at scholar tier for most of the eleven dossiers.

### How to use this document

The PM uses §6 (PASS/FAIL summary matrix) to plan dispatch. Each row links to a §4 dossier section that explains the verdict and names the voices needed to flip a non-PASS to PASS. §8 turns those named voices into copy-paste-ready dispatch waves.

### Acquisition vocabulary

Voices are tagged with one of four acquisition classes (per the gap-mapping doc):

- **in-library** — sqlite3-verified `LLS:` resource in the Logos catalog at `Data/e3txalek.5iq/LibraryCatalog/catalog.db`.
- **freely-online** — fetch-verified URL (Sefaria, archive.org, CCEL).
- **acquisition-needed** — copyright + paid; defer with mitigation. Bryan's budget for the pilot is $0; these are not actionable.
- **unobtainable** — language / out-of-print / unavailable; permanent gap.

Only **in-library** and **freely-online** are actionable for the pilot. **Acquisition-needed** and **unobtainable** items are catalogued in §9 as permanent acknowledgments for `method-and-limits.md`.

### Flagged inputs error (gap-mapping §5a #9)

The gap-mapping doc surfaces an error in the prior `method-and-limits.md §3a`: it claimed Wright *Jesus and the Victory of God* is "not in the Logos library." A sqlite3 query in the prior session confirmed `LLS:JESUSVICTYGOD` is present and the file `JESUSVICTYGOD.logos4` exists at the standard Resources path (3.5 MB, dated 2026-04-25). This document treats Wright JVG as **in-library**. **Status (2026-04-26):** `method-and-limits.md §3a` has been amended; Wright JVG is now correctly listed there as in-library at `LLS:JESUSVICTYGOD` (sqlite3-verified) with an explicit note that the WS0a cataloging pass missed it. See §9 item 12 for the resolved record-correction.

---

## 2. The Eleven Mini-Dossiers — Definitions

The Daniel 7 pilot decomposes into eleven mini-dossiers: five passage-block dossiers (M1–M5), five reception/tradition dossiers (M6–M10), and one cross-book dossier (M11). Definitions follow the pilot's three-topic plus two-fold-in scope from the architecture spec, mapped onto the controlled `passageCoverage[]` vocabulary from `tools/validate_scholar.py`.

| # | Dossier | Anchor passage(s) / scope | Pilot topic mapping |
|---|---|---|---|
| M1 | Daniel 7:1-8 — four beasts + fourth kingdom | `Dan 7:1-6` + `Dan 7:7-8` | Topic: Four Beasts (primary) |
| M2 | Daniel 7:9-12 — Ancient of Days + court scene | `Dan 7:9-12` | Fold-in: Ancient of Days (opening frame of Son of Man chapter) |
| M3 | Daniel 7:13-14 — one like a son of man | `Dan 7:13-14` | Topic: Son of Man (primary) |
| M4 | Daniel 7:15-18 — saints + kingdom reception | `Dan 7:15-18` | Fold-in: Saints Receiving the Kingdom (in courtroom transfer) |
| M5 | Daniel 7:19-27 — little horn + persecution | `Dan 7:19-22` + `Dan 7:23-27` | Topic: Little Horn (primary) |
| M6 | Daniel 7 in Second Temple reception | `1 En 37-71` + 4 Ezra 11-13 + 2 Bar 36-40 + Qumran (1QM, 4Q174, 4Q246, 11Q13) + Sib Or III/IV | Pre-Christian Jewish reception backbone |
| M7 | Daniel 7 in Jewish interpretation | Medieval rabbinic + Sephardic + early-modern Hebrew + modern Orthodox | Standing tradition; currently absent |
| M8 | Daniel 7 in patristic + Reformation reception | Greek (Antiochene + non-Antiochene), Latin (Jerome + non-Jerome), Reformation (Calvin + non-Calvin), historicist-Reformation | Reception-history backbone for Christian tradition |
| M9 | Daniel 7 in modern critical scholarship | Pre-Collins (Driver, Montgomery, Charles) + Collins-school + Anchor + WBC + Continental + reception-history (Newsom) + feminist/postcolonial | Critical voice diversity |
| M10 | Daniel 7 in evangelical / Reformed / dispensational readings | Reformed (historic + conservative-critical + contemporary + amil), evangelical-BT, classical-disp, progressive-disp, mediating-evangelical, partial-preterist, historic-premil | Pilot's confessional spectrum |
| M11 | Daniel 7 in Revelation + NT reuse | Mark 13, Matt 24, Acts 7, 2 Thess 2, Rev 1, Rev 13, Rev 17, Rev 20, John 5:27, Heb 1–2 | Cross-book trajectory (the pilot's Son-of-Man-to-Revelation hinge) |

**No splits or merges from the user's eleven**; all are usable as defined. M1 splits the controlled-vocabulary block 7:1-8 across two `passageCoverage` entries (7:1-6 and 7:7-8) but is one dossier. M5 likewise spans 7:19-22 and 7:23-27 as one dossier. M11 previously required a vocabulary expansion (adding `Acts 7`, `2 Thess 2`, `John 5`, `Heb 1`, `Heb 2`) before its source classes could be fully scored at the validator level; that expansion landed 2026-04-26 (see §9 item 14).

---

## 3. Per-Dossier Rubric Template

Every §4 assessment populates these fields:

- **Source classes engaged** — tradition / method / language clusters the dossier should engage. Each is tagged either **(load-bearing)** — must have ≥1 JSON-backed primary voice for the dossier to PASS at scholar tier — or **(enrichment)** — desirable for depth but absence permits PASS-with-acknowledgment (typically borderline-PASS or noted limit). The distinction matters: a Christian visual-theology pilot that omits, say, post-Vatican-II Roman Catholic *enriches* but does not *block* the patristic-Reformation dossier, whereas omitting any patristic-Greek voice *would* block it.
- **Primary voices** — load-bearing JSON-backed scholars whose prose carries the dossier's central claim.
- **Secondary voices** — corroborating JSON-backed scholars whose citations support but do not on their own ground the dossier.
- **Required-claim list** — sub-claims that must rest on a `directly-quoted` citation. `paraphrase-anchored` and `summary-inference` will not satisfy these.
- **Current corpus coverage** — per-passage scholar count (from `passageCoverage[]`; `crossBookReadings[]` voices flagged separately when relevant) plus file-level `supportStatus` density (X dq / Y pa / Z si). Note: `supportStatus` lives at the citation level under `positions[*].citations[*]`; the JSON does not attach individual citations to each `passageCoverage[]` entry, so per-passage direct-quote density is reported at the file level (the scholar's overall direct-quote discipline) rather than at the verse-block level.
- **Verdict** — PASS / PARTIAL / FAIL per tier (layman / pastor / scholar) with the strictest tier setting the headline.
- **Voices to flip non-PASS → PASS** — named voices, each with acquisition class and a short rationale.

---

## 4. Per-Dossier Sufficiency Assessment

Citation counts and `supportStatus` breakdowns derive from a direct scan of all 17 scholar JSONs. Per-passage scholar lists derive from each JSON's `passageCoverage[]` array. Cross-book counts include `crossBookReadings[]` entries.

### M1 — Daniel 7:1-8 (four beasts + fourth kingdom) — **PASS**

**Source classes engaged**

1. **(load-bearing)** ≥1 critical-modern (Greek/Seleucid 4th kingdom; Maccabean date)
2. **(load-bearing)** ≥1 patristic-Latin (Roman 4th kingdom)
3. **(load-bearing)** ≥1 patristic-Greek (Roman 4th kingdom, anti-Maccabean)
4. **(load-bearing)** ≥1 Reformed-historic / Reformation (Roman 4th kingdom)
5. **(load-bearing)** ≥1 Reformed-conservative-critical (6th-c date defense)
6. **(load-bearing)** ≥1 BT / cross-book (typological trajectory)
7. **(load-bearing)** ≥1 dispensational (literal beasts → revived empire / future Antichrist)
8. **(enrichment)** ≥1 medieval-Jewish (Babylon-Persia-Greece-Edom rabbinic scheme) — **absent**; medieval Jewish 4-kingdoms readings parallel the Christian-Roman tradition (Edom = Rome), so absence does not bear load on the four-kingdoms identification dispute itself, only on completeness of the spectrum

**Primary voices** — Collins (critical-Greek 4th kingdom), Jerome (Roman patristic-Latin), Calvin (Roman Reformation-historic), Walvoord (dispensational Roman→revival).

**Secondary voices** — Hartman/Di Lella, Goldingay, LaCocque (critical corroborators); Theodoret (Antiochene Greek Roman reading); Young, Duguid (Reformed-modern Roman); Beale, Hamilton (BT corroborators); Pentecost, Blaising/Bock (dispensational corroborators); Menn (covenantal-amil).

**Required claims (directly-quoted needed)**

- Four beasts represent four kingdoms (consensus statement).
- The fourth kingdom is debated: Greece/Seleucids (critical) vs Rome (traditional / Reformed / dispensational).
- Identification of the fourth kingdom determines the little horn's identity (Antiochus IV vs future Antichrist).
- The vision is symbolic dream-vision in apocalyptic genre.
- Pre-WWI critical scholarship (Driver, Montgomery) is the foil for confessional defenses (Walvoord, Young).

**Current corpus coverage**

Per-passage scholar counts (from `passageCoverage[]`):

| Passage | Scholars |
|---|---|
| `Dan 7:1-6` | 9 / 17 (Beale, Calvin, Duguid, Goldingay, Hartman/Di Lella, Jerome, LaCocque, Theodoret, Young) |
| `Dan 7:7-8` | 16 / 17 (all except 1 Enoch) |

File-level direct-quote discipline across the engaged scholars: high. Walvoord 35 dq; Young 34 dq; Beale 33 dq; Hamilton 26 dq; Pentecost 29 dq; Calvin 25 dq; Hartman/Di Lella 23 dq; Goldingay 25 dq; Duguid 22 dq + 1 si; Jerome 22 dq + 1 si; LaCocque 11 dq + 3 pa + 2 si; Theodoret 14 dq + 1 pa + 7 si. The JSON does not associate individual citations with each `passageCoverage[]` entry; per-passage dq-density at the verse-block level requires citation-level reading and is not reported by the validator today.

Cross-book to `Dan 2:31-45`: 14 / 17 — multiple voices triangulate on the four-kingdoms scheme.

**Verdict per tier**

- **Layman: PASS** — clear options on the table from multiple voices in plain prose; both Greek and Roman 4th-kingdom readings represented without strawmanning.
- **Pastor: PASS** — homiletically-usable map of the central interpretive choice with named voices on each side.
- **Scholar: PASS** — the critical-modern cluster has 4 voices with geographic+methodological diversity (German Hermeneia, US Catholic Anchor, British WBC, French Continental); the Roman-traditional cluster has 7 voices spanning patristic, Reformation, modern Reformed, and dispensational. The medieval-Jewish absence is real but does not bear load on the four-kingdoms identification dispute (medieval Jewish voices held a Rome reading, paralleling the Christian-Roman tradition).

**Voices to add (depth, not necessity)**

- **Newsom & Breed *OTL Daniel*** — `LLS:OTL27DA` (in-library) — adds critical-modern reception-history dimension; closes the gap-mapping §5a-#5 backfill.
- **Driver *Cambridge Bible Daniel*** — `LLS:CAMBC27DA` (in-library) **or** archive.org F9 (freely-online) — Walvoord's named foil; pre-Collins critical baseline.
- **Montgomery *ICC Daniel*** — `LLS:ICC_DA` (in-library) **or** archive.org F10 (freely-online) — second pre-Collins anchor.
- Sefaria Wave (Rashi, Ibn Ezra) for completeness — freely-online; requires `external-sefaria` backend (gap-mapping §6 Wave E).

---

### M2 — Daniel 7:9-12 (Ancient of Days + court scene) — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 critical-modern (court scene; Canaanite Chaoskampf background; Ezekiel parallels)
2. **(load-bearing)** ≥1 patristic-Greek (court scene as theophany; Antichrist's stand before AoD)
3. **(load-bearing)** ≥1 patristic-Latin (court scene as eschatological judgment)
4. **(load-bearing)** ≥1 Reformed (theological identity of AoD; Christological reading)
5. **(load-bearing)** ≥1 Second-Temple parallel (1 En 47:3 court scene)
6. **(load-bearing)** ≥1 BT (court → throne handover; Rev 4-5 cross-book)
7. **(enrichment)** ≥1 textual-criticism / iconographic adjudication (Old Greek vs Theodotion at v.13; AoD-vs-SoM identity question) — currently passing references only; absence does not block dossier PASS but caps it at PARTIAL until Lexham Aramaic Lexicon integration lands and ACCS Cyril of Alexandria extracts surface

**Primary voices** — Goldingay (deep on Aramaic + Dan 7:9-12), Theodoret (court scene as Christ's ascension), Calvin (Christological court).

**Secondary voices** — Beale (cross-book to Rev 1, Rev 4-5), Hamilton (BT throughline), Jerome (Latin patristic), 1 Enoch Parables (Second-Temple parallel via 1 En 47:3), Hartman/Di Lella, LaCocque, Duguid, Young.

**Required claims**

- The court scene is a theophanic vision of divine judgment.
- The Ancient of Days is YHWH (consensus across most traditions).
- White wool / throne fire / myriad attendants imagery has Canaanite background (critical) or strict OT/Ezekiel parallel (Reformed/patristic).
- Judgment results in beasts' dominion removed and given to the Son of Man.
- Old Greek's controversial reading at v.13 ("as the Ancient came" — equating SoM with AoD) vs Theodotion's standard reading.
- Patristic identification of AoD ↔ SoM relationship (theological-identity question; Cyril of Alexandria's later resolution).

**Current corpus coverage**

| Passage | Scholars | Notable absences |
|---|---|---|
| `Dan 7:9-12` | 11 / 17 (1 Enoch, Beale, Calvin, Duguid, Goldingay, Hamilton, Hartman/Di Lella, Jerome, LaCocque, Theodoret, Young) | Collins, Walvoord, Pentecost, Blaising/Bock, Durham, Menn do **not** list 7:9-12 |

Cross-book to `Rev 1`: 5 / 17 (Beale, Collins, 1 Enoch, Jerome, Hamilton).

**Verdict per tier**

- **Layman: PASS** — straightforward theophany exposition supported by multiple voices.
- **Pastor: PASS** — multiple traditions on judgment + handover; pastoral teaching is workable.
- **Scholar: PARTIAL** — Collins's silence on 7:9-12 is striking for a Hermeneia volume (probably an artifact of the `.lbxlls` page-boundary issue, but the dossier rubric reads it as silence); the OG vs Th text-critical adjudication at v.13 is absent except as passing references in Goldingay; the AoD-vs-SoM iconographic theological-identity question is patristic-territory and undertreated (Theodoret hints at it; no Cyril of Alexandria); the Latin patristic anchor is Jerome alone.

**Voices to flip PARTIAL → PASS**

- **Newsom & Breed *OTL Daniel*** — `LLS:OTL27DA` (in-library) — adds reception-history of court-scene iconography.
- **Hippolytus *Fragments on Daniel + Treatise on Christ and Antichrist + Discourse on End of World*** (ANF 5) — `LLS:6.50.5` (in-library) — earliest patristic court-scene reading; closes patristic-Greek-non-Antiochene gap.
- **Augustine *City of God* Bk XX** — `LLS:CITYOFGOD` (in-library) — load-bearing Latin amillennial court reading; closes patristic-Latin-non-Jerome gap.
- **Cyril of Alexandria via ACCS Daniel anthology** — `LLS:ACCSREVOT13` (in-library; **requires anthology-shape schema variant** — gap-mapping §6 Wave I).
- **Lexham Aramaic Lexicon integration** for v.13 text-criticism — `LLS:FBARCLEX` (WS0c-9 queue; tooling integration, not a survey).

---

### M3 — Daniel 7:13-14 (one like a son of man) — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 critical-modern (angelic Son of Man = Michael; corporate Israel options)
2. **(load-bearing)** ≥1 Christological-traditional (SoM = Christ pre-/at-/in-ascension)
3. **(load-bearing)** ≥1 Second-Temple reception (composite figure: 1 En 46-49, 71)
4. **(load-bearing)** ≥1 medieval-Jewish (SoM = Davidic Messiah, mainstream rabbinic) — **absent**; this is the dossier's largest single gap because Christian appeals to Dan 7:13's Son of Man as proof of Christ's deity unavoidably interact with the rabbinic Davidic-messianic reading
5. **(load-bearing)** ≥1 BT / cross-book (Mark 14, Matt 26, Acts 7, Rev 1/14)
6. **(enrichment)** ≥1 4 Ezra 11-13 (Man-from-the-Sea — Davidic-messianic alternate) — **absent**; engaged secondarily by Beale; would deepen Second-Temple cluster
7. **(enrichment)** ≥1 Reformed-amillennial (transhistorical Son of Man + inaugurated kingdom) — Menn covers eclectic-amil; Hoekema/Riddlebarger narrative-only
8. **(enrichment)** ≥1 textual-criticism (OG vs Th at v.13)

**Primary voices** — Collins (angelic Michael), 1 Enoch Parables (transcendent preexistent composite figure), Jerome (Christ-incarnate at Second Coming), Beale (cross-book to Rev throughout), Hamilton (BT throughline through NT).

**Secondary voices** — Theodoret (Christ via Matt 24:30, 1 Thess 4:16), Calvin (Christological), Walvoord (dispensational future SoM), Pentecost, Young, Duguid, Menn, Hartman/Di Lella, Goldingay, LaCocque, Durham, Blaising/Bock.

**Required claims**

- The figure "one like a son of man" comes with the clouds to the Ancient of Days.
- He receives dominion, glory, and an eternal kingdom.
- The referent is debated: angelic-Michael (critical), Christological (traditional), corporate-Israel-saints (some critical).
- 1 Enoch Parables develops the figure as preexistent transcendent judge (1 En 46:1-3 directly reshapes Dan 7:9, 13).
- Daniel 7:13 is the most-cited OT verse in NT (Beale, Hamilton).
- 4 Ezra 11-13 (Eagle Vision; Man-from-the-Sea) represents the alternate Second-Temple Davidic-messianic resolution.
- Medieval Jewish reading: Son of Man = Davidic Messiah (Rashi, Ibn Ezra mainstream); Daniel placed in Ketuvim, not Nevi'im.
- Old Greek's controversial reading ("as the Ancient came" — implying SoM is AoD) vs Theodotion's standard ("to the Ancient").

**Current corpus coverage**

| Passage | Scholars | Direct-quote density |
|---|---|---|
| `Dan 7:13-14` | 17 / 17 | Beale 33 dq; Hamilton 26 dq; Walvoord 35 dq; Young 34 dq; Calvin 25 dq; Pentecost 29 dq; 1 Enoch Parables 19 dq + 6 si |

Cross-book to NT: Rev 1 (6 voices), Mark 13 (5), Matt 24 (7); cross-book to 1 En 37-71 (3 voices in `passageCoverage[]`: 1 Enoch's own survey + Beale + Goldingay; LaCocque has 1 En 37-71 in `crossBookReadings[]` only).

**Verdict per tier**

- **Layman: PASS** — multiple traditions clearly represented; central question (Christ vs angel vs corporate) workable in plain prose.
- **Pastor: PASS** — homiletically rich; cross-book trajectory to Mark 14:62, Acts 7:56, Rev 1:7 well-anchored; multiple voices on the central question.
- **Scholar: PARTIAL** — the absence of medieval Jewish reception (Rashi, Ibn Ezra, ibn Yahya) on the *most central single verse for the Christian-Jewish dialogue around Daniel 7* is the largest single deficiency in the corpus per the gap-mapping §2.3 finding; 4 Ezra 11-13's alternate Second-Temple Davidic-messianic resolution is also absent as a primary voice (Beale engages it secondarily); the OG vs Th text-critical adjudication at v.13 is only passing references.

**Voices to flip PARTIAL → PASS**

- **Sefaria Wave** (Rashi, Ibn Ezra, Joseph ibn Yahya, Malbim, Steinsaltz on Daniel 7:13) — Sefaria URLs (freely-online F1, F2, F3, F7, F8); **requires `external-sefaria` or `external-html` backend** (gap-mapping §6 Wave E).
- **Charlesworth *OT Pseudepigrapha Vol 1*** — `LLS:OTPSEUD01` (in-library) — primary text for 4 Ezra 11-13 + 2 Baruch 36-40 + 39-42; reception-event survey style (per 1 Enoch Parables pattern).
- **Hoekema *The Bible and the Future*** — `LLS:BBLANDTHEFUTURE` (in-library) — Reformed-amillennial heaven-located SoM kingdom; closes legacy-narrative gap.
- **Wright *Jesus and the Victory of God*** — `LLS:JESUSVICTYGOD` (in-library) — Son of Man + Jesus self-understanding deepening beyond NTPG; **fixes the method-and-limits §3a Wright-not-in-library error**.

---

### M4 — Daniel 7:15-18 (saints + kingdom reception) — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 critical-modern (saints = corporate Israel under Antiochene persecution; some readings: heavenly host)
2. **(load-bearing)** ≥1 patristic (saints = elect Christian church / eschatological community)
3. **(load-bearing)** ≥1 Reformed (saints = visible church / elect pilgrims)
4. **(load-bearing)** ≥1 BT / eschatological (saints = inaugurated kingdom community)
5. **(load-bearing)** ≥1 dispensational (saints = faithful remnant of Israel, future tribulation context) — **absent on this passage** (Walvoord/Pentecost/Blaising-Bock do not list 7:15-18 in `passageCoverage[]`; the reading exists in their broader rationales but is not anchored at this verse-block)
6. **(enrichment)** ≥1 partial-preterist (saints = first-century Jewish-Christian community) — **absent**
7. **(enrichment)** ≥1 historicist-Reformation (saints = persecuted Reformed church through history) — **absent on this passage** (Durham doesn't list 7:15-18)
8. **(enrichment)** ≥1 historic-premillennial (Ladd-school inaugurated saints reading) — **absent**

**Primary voices** — Calvin (visible church / elect pilgrims; explicit Reformed reading), Theodoret (eschatological one true unending kingdom), Hartman/Di Lella (corporate Israel anchor).

**Secondary voices** — Goldingay, LaCocque (critical corroborators); Jerome (anti-chiliasm), Duguid, Young (Reformed corroborators); Beale (BT cross-book corroborator).

**Required claims**

- Daniel asks the interpreter for the meaning of the vision (vv. 15-16).
- The "saints of the Most High" receive the kingdom forever (v.18).
- Identity of saints debated: corporate Israel (critical), heavenly angelic host (some critical incl. Collins), elect church (Reformed), faithful remnant (dispensational), eschatological community (BT).
- "Forever and ever" is eschatological-final (most) vs inaugurated-now (some BT/Reformed-amil).

**Current corpus coverage**

| Passage | Scholars | Notable absences |
|---|---|---|
| `Dan 7:15-18` | 9 / 17 (Beale, Calvin, Duguid, Goldingay, Hartman/Di Lella, Jerome, LaCocque, Theodoret, Young) | 1 Enoch, Blaising/Bock, Collins, Durham, Hamilton, Menn, Pentecost, Walvoord all do **not** list 7:15-18 |

**Verdict per tier**

- **Layman: PASS** — multiple traditions on saints' identity; the central question is teachable.
- **Pastor: PASS** — Calvin, Duguid, Young provide Reformed homiletical anchor; critical voices represent academic alternatives; 9 voices is a workable spread.
- **Scholar: PARTIAL** — the dispensational reading of saints (faithful remnant of Israel) is missing because Walvoord/Pentecost/Blaising-Bock don't list 7:15-18 in coverage (the reading exists in their broader rationales but is not anchored at this verse-block); the "saints = angelic host" critical reading is undertreated (Collins does not list 7:15-18); historic-premil and partial-preterist clusters absent entirely.

**Voices to flip PARTIAL → PASS**

- **Newsom & Breed *OTL Daniel*** — `LLS:OTL27DA` (in-library) — fills the critical-modern reception-history dimension; Newsom's reception chapters engage the saints question.
- **Sproul *Last Days according to Jesus*** — `LLS:LSTDYSCCRDNGJSS` (in-library) — partial-preterist primary voice; closes cluster gap.
- **Ladd *Theology of the New Testament*** — `LLS:THEONTLADD` (in-library) — historic-premillennial inaugurated-saints framework (Ladd's eschatological synthesis).
- **Hoekema *The Bible and the Future*** — `LLS:BBLANDTHEFUTURE` (in-library) — Reformed-amil saints-as-inaugurated-church reading (heaven-located kingdom).

---

### M5 — Daniel 7:19-27 (little horn + persecution) — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 critical-modern (Antiochus IV; coinage + cultic-calendar evidence)
2. **(load-bearing)** ≥1 patristic-Greek (Antichrist via Antiochus typology)
3. **(load-bearing)** ≥1 patristic-Latin (Antichrist; rejection of Porphyry's identification)
4. **(load-bearing)** ≥1 Reformed-historic (Roman Caesars typology)
5. **(load-bearing)** ≥1 Reformed-modern (typological / transhistorical)
6. **(load-bearing)** ≥1 dispensational (future Antichrist + 7-year tribulation + revived empire)
7. **(load-bearing)** ≥1 BT (typological-trajectorial; transhistorical-recurrent)
8. **(load-bearing)** ≥1 historicist-Reformation (Papal Rome)
9. **(load-bearing)** ≥1 mediating-evangelical compositional reading (Davis "antichrists before THE Antichrist") — **absent**; the architecture spec's example schema explicitly requires this voice to validate compositional positions
10. **(enrichment)** ≥1 partial-preterist (70 CE fulfillment) — **absent**
11. **(enrichment)** ≥1 medieval-Jewish (Roman/Edom little horn) — **absent**

**Primary voices** — Collins (Antiochus IV), Walvoord (future Antichrist), Theodoret (Antichrist via Antiochus eikōn-archetypon formula), Calvin (Roman Caesars), Durham (Papal Rome historicist), Beale (transhistorical-typological), Menn (covenantal-amil).

**Secondary voices** — Hartman/Di Lella, Goldingay, LaCocque (critical corroborators); Jerome (Latin patristic future-Antichrist with anti-Porphyry refutation); Young, Duguid (Reformed-modern); Pentecost, Blaising/Bock (dispensational corroborators); Hamilton (BT corroborator); 1 Enoch Parables (Second-Temple background).

**Required claims**

- The little horn is the central interpretive crux of Daniel 7.
- Identifications: Antiochus IV (critical), future Antichrist (dispensational, Reformed-traditional, Theodoret-Jerome patristic), Papal Rome (historicist), Roman Caesars (Calvin), transhistorical-recurrent (Reformed-amil, BT).
- 3.5 years ("time, times, half a time") — literal (dispensational), symbolic (most others).
- "Wages war on saints" — Jewish persecution under Antiochus (critical) vs eschatological persecution (most others).
- Compositional/multi-fulfillment options (Davis, Riddlebarger, Lucas) — currently absent.

**Current corpus coverage**

| Passage | Scholars | Direct-quote density |
|---|---|---|
| `Dan 7:19-22` | 13 / 17 | Walvoord 35 dq; Beale 33 dq; Calvin 25 dq |
| `Dan 7:23-27` | 17 / 17 | Pentecost 29 dq; Young 34 dq; Theodoret extensive |

Cross-book to `Rev 13`: 13 / 17 — extensive triangulation.

**Verdict per tier**

- **Layman: PASS** — clear options on the table; multiple traditions clearly represented in plain prose.
- **Pastor: PASS** — homiletically-rich; multiple traditions clearly represented; the central question (Antiochus vs Antichrist vs Papal Rome) is mappable from the corpus directly.
- **Scholar: PARTIAL** — partial-preterist (Sproul/Gentry), mediating-evangelical compositional readings (Davis/Longman/Lucas), and medieval-Jewish are absent. These are real interpretive traditions whose absence would be flagged. The mediating-evangelical compositional reading is *especially* important because the architecture spec's example schema (Davis "antichrists before the Antichrist," Riddlebarger "two threats merging") explicitly requires that voice to validate the schema.

**Voices to flip PARTIAL → PASS**

- **Sproul *Last Days according to Jesus*** — `LLS:LSTDYSCCRDNGJSS` (in-library) — partial-preterist primary voice.
- **Gentry *The Beast of Revelation*** — `LLS:BEASTREVELATION` (in-library) — partial-preterist Revelation-side; closes cluster.
- **Davis *Message of Daniel*** (BST) — `LLS:BST27DA` (in-library) — mediating-evangelical typological "antichrists before THE Antichrist."
- **Longman *NIVAC Daniel*** — `LLS:NIVAC27DA` (in-library) — mediating-evangelical transhistorical-recurrence.
- **Lucas *Daniel*** (AOT) — `LLS:AOT27DA` (in-library) — mediating-evangelical near-far fulfillment.
- **Sefaria Wave** (Rashi, Ibn Ezra) on Daniel 7:19-27 — freely-online; requires backend.
- **Riddlebarger *A Case for Amillennialism*** — `LLS:CSAMLLNLSM` (in-library) — Reformed-amil "two threats merging" mechanic.

---

### M6 — Daniel 7 in Second Temple reception — **FAIL**

**Source classes engaged**

1. **(load-bearing)** ≥1 1 Enoch Parables (1 En 37-71 — composite Son-of-Man figure)
2. **(load-bearing)** ≥1 4 Ezra 11-13 (Eagle Vision + Man-from-the-Sea — Roman 4th kingdom; Davidic-messianic SoM) — **absent**
3. **(load-bearing)** ≥1 Qumran (1QM Michael two-tier; 4Q174 Florilegium; 11Q13 Melchizedek; 4Q246 Aramaic Son of God; 4Q243-245 Pseudo-Daniel) — **absent**
4. **(enrichment)** ≥1 2 Baruch 36-40 + 39-42 (parallel reception) — **absent**
5. **(enrichment)** ≥1 Sibylline Oracles III + IV (Hellenistic-Jewish 4-kingdoms reuse) — **absent**

**Primary voices** — 1 Enoch Parables (Nickelsburg & VanderKam) — the lone direct primary voice.

**Secondary voices** — Beale *Use of Daniel* (engages the broader Second-Temple literature in commentary form); Goldingay (lists 1 En 37-71 in coverage); LaCocque (lists 1 En 37-71).

**Required claims**

- The Parables of Enoch (1 En 37-71) presents the most developed Second-Temple Son-of-Man reception (composite figure: Chosen One / Righteous One / Anointed One / Son of Man).
- 4 Ezra 11-13 retargets the fourth beast onto Rome and presents a Davidic-messianic Man-from-the-Sea SoM.
- 2 Baruch 36-40 + 39-42 parallels 4 Ezra in the late-1st-c-CE Roman context.
- Qumran texts extend Daniel's angelology (1QM Michael two-tier) and messianism (4Q246 Aramaic Son of God).
- Sibylline Oracles III + IV reuse Daniel's four-kingdoms scheme in Hellenistic-Jewish polemic.
- The Maccabean-Greek vs Roman fourth-kingdom shift across this literature is itself reception-history evidence.

**Current corpus coverage**

| Anchor | JSON-backed scholars | Citation density |
|---|---|---|
| `1 En 37-71` | 3 voices in `passageCoverage[]` (1 Enoch Parables itself + Beale + Goldingay); LaCocque has 1 En 37-71 in `crossBookReadings[]` only | 1 Enoch survey = 25 cit (19 dq + 6 si); cross-book mentions in others |
| 4 Ezra 11-13 | 0 | 0 |
| 2 Baruch | 0 | 0 |
| Qumran (1QM, 4Q174, 11Q13, 4Q246) | 0 | 0 |
| Sibylline Oracles III + IV | 0 | 0 |

Codex audit (2026-04-26) labels `1 En 37-71` as "borderline thin"; the supporting passage-level voices (excluding the 1 Enoch survey itself) are Beale + Goldingay = 2 corroborators in `passageCoverage[]`.

**Verdict per tier**

- **Layman: PARTIAL** — Parables of Enoch alone gives a single Jewish-apocalyptic reception; insufficient to portray the full pre-Christian Jewish landscape; reader gets one window into "what 1st-c Jews saw," not the room.
- **Pastor: FAIL** — for an honest "what did 2nd-c-BCE-to-1st-c-CE Jews see in Daniel 7" pastoral picture, you need at minimum 4 Ezra (the alternate Davidic resolution) and Qumran (the angelological deepening) alongside the Parables.
- **Scholar: FAIL** — single-witness for an entire reception-cluster; Dr. Reviewer would mark this as the second-largest single deficiency after medieval-Jewish (M7).

**Voices to flip FAIL → PASS**

- **Charlesworth *OT Pseudepigrapha Vol 1*** — `LLS:OTPSEUD01` (in-library) — primary text for 4 Ezra 11-13 + 2 Baruch 36-40 + 39-42 + Sibylline Oracles + Apocalypse of Abraham; reception-event survey style.
- **Lexham DSS Hebrew-English Interlinear** — `LLS:LDSSHEIB` (in-library) — primary text for Qumran 1QM, 4Q174, 11Q13, 4Q246, 4QDan-a/b/c, 4Q243-245 Pseudo-Daniel; reception-event survey style.
- **Charlesworth *OT Pseudepigrapha Vol 2*** — `LLS:OTPSEUD02` (in-library) — additional pseudepigrapha including Sibylline Oracles supplements.
- **Charles *APOT* Vols 1-2 (1913)** — archive.org F12 (freely-online) — older standard ET as supplement and academic-citation backup.

After 3 reception-event surveys (Charlesworth OTP + Lexham DSS + Sibylline supplements): cluster moves from 1 → 4 voices. PASS achievable at all three tiers.

---

### M7 — Daniel 7 in Jewish interpretation — **FAIL**

**Source classes engaged**

1. **(load-bearing)** ≥1 medieval rabbinic plain-meaning (11c. France) — **absent**
2. **(load-bearing)** ≥1 medieval grammatical (12c. Spain) — **absent**
3. **(load-bearing)** ≥1 Sephardic post-Iberian-exile (16c. Italy) — **absent**
4. **(load-bearing)** ≥1 modern Hebrew anti-Haskalah (19c.) — **absent**
5. **(load-bearing)** ≥1 modern Orthodox commentary (20-21c.) — **absent**
6. **(enrichment)** ≥1 Karaite voice (Yefet ben Eli; rare 1889 OUP) — **unobtainable**
7. **(enrichment)** ≥1 Sephardic Renaissance (Abrabanel) — **freely-online via Sefaria; not yet surveyed**

**Primary voices** — none currently. After Wave E: Rashi (plain-meaning anchor), Ibn Ezra (grammatical anchor), Joseph ibn Yahya (Sephardic post-exile), Malbim (modern Hebrew), Steinsaltz (modern Orthodox).

**Secondary voices** — Metzudat David (verse-by-verse plain-meaning), Metzudat Zion (lexical companion), Minchat Shai (masoretic textual notes).

**Required claims**

- Daniel is included in the Writings (Ketuvim), not the Prophets (Nevi'im), in the Jewish canon — and this canonical placement carries hermeneutical weight (per architecture spec axis: canonical-placement reading rule).
- Four kingdoms = Babylon, Persia, Greece, Edom (Rome) — standard medieval rabbinic.
- Son of Man = Davidic Messiah (Rashi, mainstream rabbinic).
- Little horn = Roman empire / Christianity (medieval anti-Christian polemic emerges in some Sephardic readings).
- Saints = Israel (corporate, the people of the holy ones).
- Daniel's chronology has been central to medieval messianic calculations (controversial within rabbinic tradition).

**Current corpus coverage**

| Anchor | JSON-backed scholars | Citation density |
|---|---|---|
| Rashi on Daniel | 0 | 0 |
| Ibn Ezra on Daniel | 0 | 0 |
| Joseph ibn Yahya on Daniel | 0 | 0 |
| Malbim on Daniel | 0 | 0 |
| Steinsaltz on Daniel | 0 | 0 |

8 freely-online Sefaria URLs verified by the prior session (HTTP 200; full 12 chapters of Daniel; verse-by-verse navigable).

**Verdict per tier**

- **Layman: FAIL** — no Jewish voice on a Jewish text; this single absence delegitimizes any "spectrum" claim a Christian visual-theology pilot would make.
- **Pastor: FAIL** — pastor cannot honestly represent how Jews read this text; Christian uses of Dan 7:13's Son of Man as proof of Christ's deity unavoidably interact with the rabbinic Davidic-messianic reading; absence is dishonest.
- **Scholar: FAIL** — single largest deficiency per gap-mapping §2.3. Dr. Reviewer would mark this dossier as failing the rubric outright.

**Voices to flip FAIL → PASS**

- **Wave E (5 surveys, all freely-online via Sefaria)**:
  - **Rashi on Daniel** — https://www.sefaria.org/Rashi_on_Daniel (freely-online F1) — medieval rabbinic plain-meaning, 11c. France.
  - **Ibn Ezra on Daniel** — https://www.sefaria.org/Ibn_Ezra_on_Daniel (freely-online F2) — grammatical-philological, 12c. Spain.
  - **Joseph ibn Yahya on Daniel** — https://www.sefaria.org/Joseph_ibn_Yahya_on_Daniel (freely-online F3) — Sephardic post-Iberian-expulsion, Bologna 1538.
  - **Malbim on Daniel** — https://www.sefaria.org/Malbim_on_Daniel (freely-online F7) — modern Hebrew anti-Haskalah, 19c.
  - **Steinsaltz on Daniel** — https://www.sefaria.org/Steinsaltz_on_Daniel (freely-online F8) — modern Orthodox, 20-21c.

- **Prerequisite — backend work**: new `external-sefaria` or `external-html` backend kind (per gap-mapping §6 Wave E and §8.4). Verifier needs Hebrew NFC normalization + HTML stripping + verse-anchored matching. Estimated 1-2 days backend + 1-2 days surveys.

- **Permanent gaps catalogued in §9**: Saadia Gaon (only Judeo-Arabic fragments), Yefet ben Eli (rare 1889 OUP, not on archive.org), Ramban (no complete Daniel commentary; references in his other works only), Ralbag (Sefaria 404; not online-digitized in any free repository).

After Wave E (5 surveys + backend): cluster moves from 0 → 5 voices. PASS achievable at all three tiers.

---

### M8 — Daniel 7 in patristic + Reformation reception — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 patristic-Greek Antiochene
2. **(load-bearing)** ≥1 patristic-Greek non-Antiochene (Alexandrian, Roman, or Asian) — **absent**
3. **(load-bearing)** ≥1 patristic-Latin Jerome
4. **(load-bearing)** ≥1 patristic-Latin non-Jerome (Augustine, Cassiodorus, Victorinus) — **absent**
5. **(load-bearing)** ≥1 Reformation-Calvin
6. **(load-bearing)** ≥1 Reformation-non-Calvin (Bullinger, Vermigli, Brenz, Œcolampadius) — **absent**
7. **(enrichment)** ≥1 post-Reformation historicist (Mede, Newton, Durham)

**Primary voices** — Theodoret (patristic-Greek Antiochene anchor; Roman 4th kingdom + Antichrist eikōn/archetypon formula), Jerome (patristic-Latin anchor; Roman 4th kingdom + future Antichrist + anti-Porphyry refutation), Calvin (Reformation-historic anchor; Roman Caesars + indefinite times), Durham (post-Reformation historicist; Papal Rome via Revelation).

**Secondary voices** — Beale *Use of Daniel* (cross-references patristic exegesis); Hamilton (BT engagement with patristic typology).

**Required claims**

- Patristic consensus on Rome as fourth kingdom (vs. pre-millennial Alexandrian voices).
- Antiochus → Antichrist typology (Theodoret eikōn/archetypon formula explicit; Jerome implicit; Western tradition derivative from Jerome).
- Western amillennial reading via Augustine *City of God* Bk XX — load-bearing for Latin tradition's Rev 20 ↔ Dan 7 linkage.
- Reformation voices vary on the little horn: Calvin (Roman Caesars), Bullinger / Brenz (Antichrist), Vermigli (Papal Rome).
- Historicist Reformation: Daniel 7 little horn = Papal Rome (Durham, Mede, Newton, Wordsworth).
- Patristic-Greek vs patristic-Latin diverge on chiliasm (Hippolytus more pre-millennial; Augustine amillennial; Theodoret amillennial-eschatological).

**Current corpus coverage**

| Sub-cluster | Scholars | Direct-quote density |
|---|---|---|
| patristic-Greek Antiochene | Theodoret (22 cit, 14 dq + 1 pa + 7 si) | Several Greek fragments codex-flagged as too short to bear rationale (audit §6.5) |
| patristic-Latin | Jerome (23 cit, 22 dq + 1 si) | Strong; Porphyry-refutation explicit |
| Reformation-historic | Calvin (25 cit, 25 dq) | Strong; distinctive Roman-Caesars reading |
| post-Reformation historicist | Durham (14 cit, 3 dq + 2 pa + 9 si) | Reception-history; lighter dq density appropriate to genre |

ZERO JSON-backed: Hippolytus (in-library at `LLS:6.50.5`), Augustine (in-library at `LLS:CITYOFGOD` + `LLS:6.60.2`), Cyril of Jerusalem (in-library at `LLS:6.60.21`), Chrysostom on Matt 24 (in-library at `LLS:6.60.10`), Victorinus on Apocalypse (in-library at `LLS:6.50.7`), Bullinger / Vermigli / Brenz / Œcolampadius (in-library via RCS anthology `LLS:REFORMCOMMOT12`, requires anthology schema).

**Verdict per tier**

- **Layman: PASS** — patristic + Reformation voices represented; the central historic Christian reading is teachable from the corpus.
- **Pastor: PARTIAL** — would benefit from Augustine (Latin amillennial) for the most cited patristic on Rev 20 + Dan 7 in Reformed homiletics; current Latin patristic is Jerome-only.
- **Scholar: PARTIAL** — single voice per sub-cluster (one Greek patristic = Antiochene; one Latin patristic = Jerome; one Reformation = Calvin); §2.1 rubric calls for ≥2 per sub-cluster. Theodoret OCR-quote tightening still pending (codex audit §6.5). Dr. Reviewer would press hard on the single-witness pattern.

**Voices to flip PARTIAL → PASS**

- **Hippolytus *Fragments on Daniel + Treatise on Christ and Antichrist + Discourse on End of World*** (ANF 5) — `LLS:6.50.5` (in-library) — patristic-Greek non-Antiochene anchor; closes cluster gap; supersedes the redundant `external-resources/pdfs/Hippolytus-EndTimes.pdf`.
- **Augustine *City of God* Bk XX** — `LLS:CITYOFGOD` (in-library; alternate `LLS:6.60.2` NPNF 1.2) — load-bearing Latin amillennial reading of Dan 7 + Rev 20; closes patristic-Latin-non-Jerome gap.
- **Cyril of Jerusalem *Catechetical Lecture* XV** (NPNF 2.7) — `LLS:6.60.21` (in-library) — 4th-c. Greek patristic; explicit Antichrist + Dan 7 reading.
- **Chrysostom *Homilies on Matthew*** (NPNF 1.10) — `LLS:6.60.10` (in-library) — Matt 24 / Olivet → Dan 9:27 / Dan 7 link; deepens M11 as well.
- **Victorinus *Commentary on the Apocalypse*** (ANF 7) — `LLS:6.50.7` (in-library) — early Latin Revelation commentary with Dan 7 cross-references.
- **ACCS Daniel anthology** — `LLS:ACCSREVOT13` (in-library; **requires anthology-shape schema variant**) — extracts of Hippolytus, Theodoret, Augustine, Origen, Chrysostom, Cyril of Alexandria, Cyril of Jerusalem, Gregory the Great.
- **RCS Daniel anthology** — `LLS:REFORMCOMMOT12` (in-library; **requires anthology-shape schema variant**) — Bullinger, Vermigli, Œcolampadius, Lambert, Brenz, Pellican, Melanchthon.
- **Theodoret OCR-quote tightening** — re-extract longer Greek quotes from `external-resources/greek/theodoret-pg81-dan7.txt` for the codex-flagged citations (deferred from WS0c-cleanup).

After Wave B (5 patristic surveys, all in-library): patristic-Greek and patristic-Latin each move from single voice to ≥2 voices. After Wave I (anthology schema + ACCS + RCS): Reformation cluster moves from Calvin alone to multi-voice.

---

### M9 — Daniel 7 in modern critical scholarship — **PASS** (borderline)

**Source classes engaged**

1. **(load-bearing)** ≥1 German-trained critical (Hermeneia school)
2. **(load-bearing)** ≥1 US Catholic critical (Anchor)
3. **(load-bearing)** ≥1 British mediating critical (WBC)
4. **(load-bearing)** ≥1 French-Continental Catholic critical
5. **(enrichment)** ≥1 reception-history critical — **narrative-only (Newsom & Breed in library, unsurveyed)**; absence does not block PASS because the four load-bearing voices already cover the central post-1990 critical-modern position fully, but presence would convert borderline-PASS to solid-PASS
6. **(enrichment)** ≥1 pre-Collins critical baseline (Walvoord's named foils: Driver, Montgomery, Charles) — **absent**; provides academic-history depth, not load-bearing for the contemporary critical position itself
7. **(enrichment)** ≥1 feminist or postcolonial critical method — **partially via Newsom narrative-only**
8. **(enrichment)** ≥1 apocalyptic-genre method (Collins *Apocalyptic Imagination*) — **narrative-only**; Collins's Hermeneia commentary already engages genre method substantively, so the dedicated genre-method volume is enrichment

**Primary voices** — Collins (critical-modern Maccabean-Greek anchor; the field's name-brand voice), Hartman/Di Lella (US Catholic Anchor; major distinct voice from Collins).

**Secondary voices** — Goldingay (WBC; mediating), LaCocque (Continental Catholic).

**Required claims**

- Maccabean dating (167 BCE) is critical-consensus.
- Fourth kingdom = Greece/Seleucids (Babylon-Media-Persia-Greece sequence).
- Little horn = Antiochus IV (with coinage ΘΕΟΥ ΕΠΙΦΑΝΟΥΣ + cultic-calendar suppression evidence).
- Son of Man = angelic figure (probably Michael per Collins).
- Genre = apocalyptic dream-vision; meaning constrained by genre conventions.
- Religio-historical method (Canaanite Chaoskampf, ANE background).
- Pre-Collins critical chorus (Driver, Montgomery, Charles) was Walvoord's named foil and forms the historical-critical baseline.

**Current corpus coverage**

| Voice | Citations | supportStatus | Notes |
|---|---|---|---|
| Collins | 15 | 3 dq + 9 si + 3 pa | Hermeneia anchor; thin direct-quote density due to `.lbxlls` article-boundary issue |
| Hartman/Di Lella | 23 | 23 dq | Anchor; strong direct quotes |
| Goldingay | 25 | 25 dq | WBC; deep on Aramaic + Dan 7:9-12 |
| LaCocque | 16 | 11 dq + 3 pa + 2 si | Continental; EPUB-sourced |

Pre-Collins critical: ZERO JSON-backed (Driver in library, archive.org free; Montgomery in library, archive.org free; Charles in library).
Reception-history: Newsom narrative-only (in library).
Feminist/postcolonial: ZERO JSON-backed (Newsom partial).
Apocalyptic-genre method: Collins *Apocalyptic Imagination* narrative-only.

**Verdict per tier**

- **Layman: PASS** — multiple critical voices clearly represented; the Maccabean-Greek + Antiochene reading is teachable directly.
- **Pastor: PASS** — critical-modern position homiletically representable; can be honestly framed as the academic-mainstream alternative.
- **Scholar: PASS (borderline)** — 4 voices is the critical-modern §2.1 floor (3); geographic+methodological diversity is real (German Hermeneia, US Catholic Anchor, British WBC, French Continental). Pre-Collins baseline absent reduces academic depth; Newsom absent reduces reception-history dimension. Borderline PASS today; would be stronger PASS with Newsom + Driver + Montgomery added.

**Voices to add (to convert borderline PASS to solid PASS)**

- **Newsom & Breed *OTL Daniel*** — `LLS:OTL27DA` (in-library) — fills the critical-modern reception-history dimension; Newsom's reception chapters are unique in scope.
- **Driver *Cambridge Bible Daniel*** — `LLS:CAMBC27DA` (in-library) **or** archive.org F9 (freely-online) — pre-Collins critical anchor; Walvoord's named foil.
- **Montgomery *ICC Daniel*** — `LLS:ICC_DA` (in-library) **or** archive.org F10 (freely-online) — second pre-Collins anchor.
- **Collins *The Apocalyptic Imagination*** — `LLS:PCLYPTCMGNTNPLT` (in-library) — apocalyptic-genre method primary voice (currently narrative-only).

---

### M10 — Daniel 7 in evangelical / Reformed / dispensational readings — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 Reformed-historic (Calvin)
2. **(load-bearing)** ≥1 Reformed-conservative-critical (Young)
3. **(load-bearing)** ≥1 Reformed-contemporary expository (Duguid)
4. **(load-bearing)** ≥1 Reformed-amillennial (Hoekema-school heaven-located; Riddlebarger-school earth-located) — **single eclectic voice (Menn) only; Hoekema + Riddlebarger narrative-only**
5. **(load-bearing)** ≥1 covenantal-amillennial-eclectic (Menn)
6. **(load-bearing)** ≥1 classical-dispensational commentary (Walvoord)
7. **(load-bearing)** ≥1 classical-dispensational systematic (Pentecost)
8. **(load-bearing)** ≥1 progressive-dispensational (Blaising/Bock — single voice; Saucy or alternate needed for triangulation)
9. **(load-bearing)** ≥1 evangelical-BT (Beale + Hamilton)
10. **(load-bearing)** ≥1 mediating-evangelical (Davis/Longman/Lucas) — **absent**
11. **(load-bearing)** ≥1 partial-preterist (Sproul/Gentry/Mathison) — **absent**
12. **(enrichment)** ≥1 historic-premillennial (Ladd) — **absent**; the cluster has limited contemporary footprint; absence reduces breadth but not load

**Primary voices** — Calvin (Reformed-historic anchor), Young (Reformed-conservative-critical anchor), Duguid (Reformed-contemporary expository anchor), Walvoord (classical-disp commentary anchor), Pentecost (classical-disp systematic anchor), Beale + Hamilton (evangelical-BT pair).

**Secondary voices** — Menn (covenantal-amil-eclectic), Blaising/Bock (progressive-disp single voice).

**Required claims**

- Reformed-historic = Calvin's Roman Caesars view + indefinite-time hermeneutic.
- Reformed-conservative-critical = Young's defense of 6c. date + predictive prophecy without dispensationalism (Westminster Theological Seminary OT chair).
- Reformed-amillennial Hoekema-school = heaven-located present reign of deceased-believer souls.
- Reformed-amillennial Riddlebarger-school = earth-located church-militant present reign + "two threats merging into a single end-time figure."
- Classical-dispensational = Walvoord's revived-Roman-empire + future Antichrist + 7-year tribulation.
- Progressive-dispensational = Blaising/Bock inaugurated kingdom (one voice; needs Saucy or Bock-and-Blaising elsewhere for triangulation).
- Evangelical-BT = Beale/Hamilton typological-trajectorial reading.
- Mediating-evangelical = Davis "antichrists before THE Antichrist" / Longman transhistorical-recurrence / Lucas near-far (all narrative-only currently).
- Partial-preterist = Sproul/Gentry historicized 70-CE fulfillment.
- Historic-premillennial = Ladd's inaugurated-saints framework (ToNT).

**Current corpus coverage**

| Sub-cluster | Voices (count, dq density) | Status |
|---|---|---|
| Reformed-historic | Calvin (25 dq) | strong |
| Reformed-conservative-critical | Young (34 dq) | strong (single voice but well-defined) |
| Reformed-contemporary expository | Duguid (22 dq + 1 si) | strong |
| Reformed-amillennial eclectic | Menn (12 dq + 3 pa + 4 si) | single voice |
| Classical-dispensational | Walvoord (35 dq + 1 pa + 2 si) + Pentecost (29 dq + 2 si) | strong (2 voices) |
| Progressive-dispensational | Blaising/Bock (18 dq + 2 pa + 2 si) | single voice |
| Evangelical-BT | Beale (33 dq + 1 pa) + Hamilton (26 dq + 2 si + 1 pa) | strong (2 voices) |
| Mediating-evangelical | 0 JSON-backed (Davis, Longman, Lucas all narrative-only) | absent |
| Partial-preterist | 0 JSON-backed | absent |
| Historic-premillennial | 0 JSON-backed | absent |

**Verdict per tier**

- **Layman: PASS** — multiple clusters represented; Reformed and dispensational poles clearly mappable.
- **Pastor: PASS** — Reformed + dispensational well-covered; pastor can map both sides homiletically.
- **Scholar: PARTIAL** — mediating-evangelical, partial-preterist, historic-premil clusters are zero; Reformed-amillennial relies on Menn's eclectic voice (Hoekema/Riddlebarger narrative-only); progressive-disp single voice. These are real, named interpretive traditions; their absence would be flagged especially given the architecture spec's named pilot-tradition list (Reformed inaugurated amillennial; irenic evangelical mediating; historic premillennial covenantal — all currently absent or under-anchored).

**Voices to flip PARTIAL → PASS**

- **Wave A (legacy-narrative backfill, all in-library)**:
  - **Hoekema *The Bible and the Future*** — `LLS:BBLANDTHEFUTURE` (in-library) — Reformed-amil heaven-located.
  - **Riddlebarger *A Case for Amillennialism*** — `LLS:CSAMLLNLSM` (in-library) — Reformed-amil earth-located.
  - **Sproul *Last Days according to Jesus*** — `LLS:LSTDYSCCRDNGJSS` (in-library) — partial-preterist.
- **Wave D (mediating-evangelical, all in-library)**:
  - **Davis *Message of Daniel*** (BST) — `LLS:BST27DA` (in-library) — typological compositional ("antichrists before THE Antichrist").
  - **Longman *NIVAC Daniel*** — `LLS:NIVAC27DA` (in-library) — transhistorical-recurrence.
  - **Lucas *Daniel*** (AOT) — `LLS:AOT27DA` (in-library) — near-far fulfillment.
- **Wave H (in-library)**:
  - **Ladd *Theology of the New Testament*** — `LLS:THEONTLADD` (in-library) — historic-premil framework.
  - **Gentry *The Beast of Revelation*** — `LLS:BEASTREVELATION` (in-library) — partial-preterist Revelation-side.

---

### M11 — Daniel 7 in Revelation + NT reuse — **PARTIAL**

**Source classes engaged**

1. **(load-bearing)** ≥1 monograph dedicated to Daniel-in-Revelation (Beale)
2. **(load-bearing)** ≥1 BT cross-book (Hamilton)
3. **(load-bearing)** ≥1 Daniel-engaging Revelation commentary distinct from Beale-school — **absent**
4. **(load-bearing)** ≥1 dispensational Olivet (Matt 24, Mark 13)
5. **(load-bearing)** ≥1 Reformed-amil Olivet
6. **(load-bearing)** ≥1 Rev 20 millennium engagement (Augustine Bk XX as Latin amil anchor) — **absent**
7. **(enrichment)** ≥1 patristic Matt 24 (Chrysostom) — **absent**
8. **(enrichment)** ≥1 Acts 7 (Stephen's Son-of-Man-standing) — vocabulary added 2026-04-26; scholar `passageCoverage[]` tagging pending
9. **(enrichment)** ≥1 2 Thess 2 (man of lawlessness) — vocabulary added 2026-04-26; scholar `passageCoverage[]` tagging pending
10. **(enrichment)** ≥1 partial-preterist Rev (Gentry) — **absent**

**Primary voices** — Beale *Use of Daniel in Revelation* (THE primary anchor; 17 passages including Rev 1, Rev 13, Rev 17, Matt 24, Mark 13, 1 En 37-71; 33 dq + 1 pa).

**Secondary voices** — Hamilton (BT throughline; cross-book to Rev 1, Rev 13, Rev 20, Matt 24, Mark 13), Walvoord (cross-book Rev 13/17 + Matt 24), Pentecost (Rev 13/17/20 + Matt 24), Menn (Rev 13/20 + Matt 24), Collins (Rev 1, 13, 17 in coverage), Calvin (Rev 13 + Matt 24), Duguid (Rev 13, Rev 20), Durham (Rev 1, 13, 17, 20 — Revelation commentary), Young (Rev 13 + Matt 24), Jerome (Rev 1, Rev 13), Theodoret (Matt 24 — flagged short OCR), 1 Enoch Parables (cross-book to Rev 1).

**Required claims**

- Daniel 7 is the most-cited OT passage in Revelation (Beale).
- Mark 14:62 / Matt 26:64 / Acts 7:56 / Rev 1:7, 1:13, 14:14 employ Dan 7:13's "Son of Man coming with clouds."
- Olivet Discourse (Matt 24, Mark 13) draws on Dan 9:27's "abomination of desolation" + Dan 7's eschatological framework.
- Rev 13's beast-from-the-sea is a direct allusion to Daniel 7's beasts (with critical-modern questioning Rev's dependence).
- Rev 20's millennium engages Dan 7 obliquely (Augustine *City of God* Bk XX is the load-bearing Latin amil text).
- 2 Thess 2's man of lawlessness draws on Dan 7's little horn (Theodoret explicit).
- The codex audit (2026-04-26) flagged 5 scholars over-applying `directly-quoted` on cross-book rows where the rationale outruns the quote — relabel work pending; this affects M11 most acutely.

**Current corpus coverage**

Counts below reflect `passageCoverage[]` only. Voices that engage the passage in `crossBookReadings[]` but not in `passageCoverage[]` are noted parenthetically.

| NT passage | JSON-backed scholars (`passageCoverage[]`) |
|---|---|
| `Rev 1` | 6 (1 Enoch, Beale, Collins, Durham, Hamilton, Jerome) |
| `Rev 13` | 13 (Beale, Calvin, Collins, Duguid, Durham, Goldingay, Hamilton, Hartman/Di Lella, Jerome, Menn, Pentecost, Walvoord, Young); LaCocque + Theodoret engage Rev 13 in `crossBookReadings[]` only |
| `Rev 17` | 6 (Beale, Collins, Durham, Menn, Pentecost, Walvoord) |
| `Rev 20` | 6 (Blaising/Bock, Durham, Hamilton, Menn, Pentecost, Walvoord); Duguid engages Rev 20 in `crossBookReadings[]` only |
| `Matt 24` | 7 (Beale, Calvin, Hamilton, Menn, Pentecost, Walvoord, Young); Theodoret engages Matt 24 in `crossBookReadings[]` only |
| `Mark 13` | 5 (Beale, Hamilton, Menn, Walvoord, Young) |
| `Acts 7` | in `PASSAGE_COVERAGE_VOCAB` as of 2026-04-26; 0 scholars tagged yet (rationale text engages it) |
| `2 Thess 2` | in vocabulary as of 2026-04-26; 0 scholars tagged yet (Walvoord, Pentecost, Theodoret, Jerome rationale text engages it) |
| `John 5` | in vocabulary as of 2026-04-26; 0 scholars tagged yet (note: vocab uses chapter-only `John 5`, not `John 5:27`) |
| `Heb 1` / `Heb 2` | in vocabulary as of 2026-04-26; 0 scholars tagged yet |

**Verdict per tier**

- **Layman: PASS** — multiple voices on the central NT-reuse story; Daniel 7 → NT trajectory teachable from the corpus.
- **Pastor: PASS** — homiletically rich; Beale + Hamilton + Walvoord + Pentecost give competing readings; Olivet + Rev coverage solid.
- **Scholar: PARTIAL** — relabel work pending (5 scholars over-applied dq); second Daniel-engaging Revelation commentary distinct from Beale-school missing (Patterson NAC dispensational Rev or Koester Lutheran-historical-critical Rev); Acts 7, 2 Thess 2, John 5, Heb 1, Heb 2 are now in `PASSAGE_COVERAGE_VOCAB` (2026-04-26) so they CAN be scored at the validator level — but no scholar has yet been tagged for them in `passageCoverage[]`. Augustine *City of God* Bk XX (THE patristic-Latin amil text on Rev 20 ↔ Dan 7) was added to the corpus 2026-04-26 in Wave 1 — addresses the previous "missing" callout below.

**Voices to flip PARTIAL → PASS**

- **Augustine *City of God* Bk XX** — `LLS:CITYOFGOD` (in-library) — Latin amil Rev 20 + Dan 7 anchor; load-bearing for the Reformed-amil tradition in M10.
- **Patterson *NAC Revelation*** — `LLS:NAC39` (in-library) — dispensational Revelation companion to Walvoord-Daniel.
- **Koester *Revelation and the End of All Things*** — `LLS:RVLTNNDLLTHNGS2ED` (in-library) — Lutheran historical-critical Revelation.
- **Beale *NIGTC Revelation*** — `LLS:29.71.18` (in-library) — Beale's full Revelation commentary, distinct from his Daniel-in-Revelation monograph.
- **Bauckham *Theology of the Book of Revelation*** — `LLS:NTTHEO87REV` (in-library) — post-critical Revelation; pairs with Wright JVG.
- **Chrysostom *Homilies on Matthew*** (NPNF 1.10) — `LLS:6.60.10` (in-library) — patristic Matt 24 / Olivet → Dan 9:27 / Dan 7 link.
- **Apply codex audit relabels** — ~26 directly-quoted → paraphrase-anchored / summary-inference per audit §2; this is the relabel work flagged on the WS0c-cleanup queue.
- **Vocabulary expansion — DONE 2026-04-26** — `Acts 7`, `2 Thess 2`, `John 5`, `Heb 1`, `Heb 2` added to `tools/validate_scholar.py:PASSAGE_COVERAGE_VOCAB`. Remaining work: tag the relevant scholars' `passageCoverage[]` lists with these entries so M11 cross-book breadth is countable in the validator-level coverage report (Walvoord, Pentecost, Theodoret, Jerome for 2 Thess 2; Beale for Acts 7; etc.).

---

## 5. Per-Tier Sufficiency Criteria (Consolidated)

The corpus serves a three-tier audience model from the architecture spec (layman pew / pastor / scholar). Each tier has a different threshold for what counts as "enough."

### Layman tier (pew-level)

**Threshold:** "Enough for an honest plain-language explanation that doesn't pick a tradition's side."

A dossier passes the layman tier when:

- ≥3 distinct interpretive traditions are represented from primary voices in their own vocabulary.
- At least one primary voice per major tradition uses prose that translates into pew-level English without forcing the reader to take a tradition's side as default.
- The "central question" of the passage is teachable to a bright newcomer to eschatology without specialist jargon.
- Confidence tiers (`documented` / `strong-judgment` / `noted-gap`) are nameable on every claim the layman dossier surfaces.

**Current pass count:** **9 / 11** (M6 PARTIAL, M7 FAIL).

### Pastor tier (homiletic)

**Threshold:** "Enough for a homiletically-usable map of how the passage has been read and what's at stake."

A dossier passes the pastor tier when:

- All Layman criteria pass.
- The map of "what's at stake" — what changes for the church's life if reading X is right vs reading Y — is named and supportable from the corpus.
- ≥1 Reformed and ≥1 dispensational voice are present (Bryan's Presbyterian context plus the dispensational tradition's pastoral footprint in North American evangelicalism mean both have to be in the room; this is the architecture spec's "scholarly but accessible" + "no school caricature" rule applied at pastor tier).
- Cross-book trajectories (Daniel → NT) are named and traceable.
- Pastoral de-escalation register is achievable — "here is why serious readers are drawn to this position; here is the cost of adopting it" — for every represented tradition, with cited proponents.

**Current pass count:** **8 / 11** (M6 FAIL, M7 FAIL, M8 PARTIAL).

### Scholar tier (academic-defensible)

**Threshold:** "Enough for an academically-defensible summary no Daniel 7 reviewer would call thin or biased."

A dossier passes the scholar tier when:

- All Pastor criteria pass.
- §2.1 tradition-cluster minimums are met for every cluster the dossier engages: ≥2 JSON-backed primary voices per live cluster; ≥1 per reception cluster.
- Patristic-Greek and patristic-Latin each have ≥2 voices (one Antiochene + one non-Antiochene; one Jerome + one non-Jerome).
- Medieval Jewish reception is represented for any dossier engaging the Son-of-Man identity dispute (M3, M5, M11) or the four-kingdoms scheme (M1).
- Pre-Collins critical baseline (Driver, Montgomery, Charles) is represented for any dossier engaging the dating dispute (M1) or the academic critical tradition's history (M9).
- Text-critical adjudication (Old Greek vs Theodotion at v.13) is engaged where relevant (M2, M3).
- `supportStatus` honesty: no `directly-quoted` citation outruns its quote; codex-flagged relabels are applied.
- All cross-book NT references the dossier needs are in the controlled `PASSAGE_COVERAGE_VOCAB` (M11 vocabulary blocker resolved 2026-04-26 — see §9 item 14; what remains is per-scholar `passageCoverage[]` tagging).

**Current pass count:** **2 / 11** (M1 PASS; M9 PASS-borderline).

### Tier rollups

| Tier | PASS | PARTIAL | FAIL |
|---|---:|---:|---:|
| Layman | 9 | 1 | 1 |
| Pastor | 8 | 1 | 2 |
| Scholar | 2 | 7 | 2 |

The headline verdict per dossier (in §6) is set by the strictest tier: a dossier is PASS only if all three tiers PASS; PARTIAL if any tier is PARTIAL but none FAIL; FAIL if any tier FAILs.

---

## 6. PASS / FAIL Summary Matrix

The headline planning table.

| # | Dossier | Layman | Pastor | Scholar | Voices to add (highest-value) |
|---|---|:---:|:---:|:---:|---|
| M1 | Dan 7:1-8 — four beasts + 4th kingdom | PASS | PASS | PASS | Newsom OTL (depth) + Driver/Montgomery (pre-Collins baseline) + Sefaria (Rashi/Ibn Ezra, requires backend) |
| M2 | Dan 7:9-12 — Ancient of Days + court | PASS | PASS | PARTIAL | Newsom OTL + Hippolytus ANF 5 + Augustine Bk XX + Cyril of Alexandria via ACCS (anthology schema) + Lexham Aramaic |
| M3 | Dan 7:13-14 — Son of Man | PASS | PASS | PARTIAL | **Sefaria Wave (Rashi, Ibn Ezra, ibn Yahya, Malbim, Steinsaltz; backend required)** + Charlesworth OTP (4 Ezra) + Hoekema + Wright JVG |
| M4 | Dan 7:15-18 — saints | PASS | PASS | PARTIAL | Newsom + Sproul + Ladd + Hoekema |
| M5 | Dan 7:19-27 — little horn | PASS | PASS | PARTIAL | Sproul + Gentry + Davis + Longman + Lucas + Riddlebarger + Sefaria |
| M6 | Dan 7 in Second Temple reception | PARTIAL | FAIL | FAIL | **Charlesworth OTP Vol 1 + Lexham DSS + Charlesworth OTP Vol 2** |
| M7 | Dan 7 in Jewish interpretation | FAIL | FAIL | FAIL | **Sefaria Wave (5 voices, requires `external-sefaria` backend)** |
| M8 | Dan 7 in patristic + Reformation | PASS | PARTIAL | PARTIAL | **Hippolytus ANF 5 + Augustine Bk XX** + Cyril of Jerusalem + Chrysostom + Victorinus + ACCS/RCS anthologies (anthology schema) |
| M9 | Dan 7 in modern critical | PASS | PASS | PASS (borderline) | Newsom + Driver + Montgomery + Collins Apoc Imagination |
| M10 | Dan 7 in evangelical/Reformed/disp | PASS | PASS | PARTIAL | **Hoekema + Riddlebarger + Sproul + Wright JVG + Davis + Longman + Lucas + Gentry + Ladd** |
| M11 | Dan 7 in Rev + NT reuse | PASS | PASS | PARTIAL | Augustine Bk XX surveyed 2026-04-26; vocab expansion landed 2026-04-26; remaining: **Patterson NAC + Koester** + Beale NIGTC + Bauckham + Chrysostom + apply codex relabels + per-scholar `passageCoverage[]` tagging for the new NT entries |

**Headline counts:** **2 / 11 PASS** (M1, M9), **7 / 11 PARTIAL** (M2, M3, M4, M5, M8, M10, M11), **2 / 11 FAIL** (M6, M7).

The two FAIL dossiers (M6 Second-Temple, M7 Jewish-interpretation) account for the largest single-action gap-closures available: after Wave E (5 Sefaria surveys + backend) M7 moves 0 → 5 voices; after Wave F (3 reception-event surveys) M6 moves 1 → 4 voices.

The seven PARTIAL dossiers cluster on three repeated voices: **Newsom OTL Daniel** (helps M2, M4, M5, M9 — 4 dossiers), **Augustine *City of God* Bk XX** (helps M2, M8, M11 — 3 dossiers), **Hippolytus ANF 5** (helps M2, M8 — 2 dossiers). These three voices alone shift the overall posture significantly.

---

## 7. Required-Voice List (Sorted P1 → P7)

Per the user's priority order. Each voice annotated with (acquisition class, mini-dossiers served, dispatch wave per §8).

### P1 — Newsom (OTL Daniel 2014)

- **Newsom & Breed *Daniel: A Commentary*** (OTL 2014) — `LLS:OTL27DA` (**in-library**; gap-mapping §5a-#5; the assumption it was acquisition-needed was wrong) — serves M2, M4, M5, M9. **Wave 1.**
  - Mitigation note moot: in-library; survey directly.

### P2 — Hippolytus / earliest Christian Daniel reception

- **Hippolytus *Fragments on Daniel + Treatise on Christ and Antichrist + Discourse on End of World*** (ANF 5) — `LLS:6.50.5` (**in-library**) — serves M2, M8. **Wave 1.**
  - The full *Commentary on Daniel* (Lefèvre SC 14 1947 Greek-French) is **unobtainable** (subscription/library); the ANF 5 fragments + tracts are the maximum freely available. The redundant `external-resources/pdfs/Hippolytus-EndTimes.pdf` is superseded by `LLS:6.50.5`.
- **Augustine *City of God* Bk XX** — `LLS:CITYOFGOD` (**in-library**; alternate `LLS:6.60.2` NPNF 1.2) — serves M2, M8, M11; complements Hippolytus on the patristic anchor. **Wave 1.**
- **Cyril of Jerusalem *Catechetical Lecture* XV** (NPNF 2.7) — `LLS:6.60.21` (**in-library**) — serves M8. **Wave 2.**
- **Chrysostom *Homilies on Matthew*** (NPNF 1.10) — `LLS:6.60.10` (**in-library**) — serves M8, M11. **Wave 2.**
- **Victorinus *Commentary on the Apocalypse*** (ANF 7) — `LLS:6.50.7` (**in-library**) — serves M8, M11. **Wave 2.**

### P3 — Jewish reception (medieval through modern Orthodox)

**All freely-online via Sefaria; all blocked on `external-sefaria` or `external-html` backend (~1-2 days backend work).**

- **Rashi on Daniel** — Sefaria F1 (**freely-online**) — serves M3, M5, M7. **Wave 6 (post-backend).**
- **Ibn Ezra on Daniel** — Sefaria F2 (**freely-online**) — serves M3, M5, M7. **Wave 6.**
- **Joseph ibn Yahya on Daniel** — Sefaria F3 (**freely-online**) — serves M7. **Wave 6.**
- **Malbim on Daniel** — Sefaria F7 (**freely-online**) — serves M7. **Wave 6.**
- **Steinsaltz on Daniel** — Sefaria F8 (**freely-online**) — serves M7. **Wave 6.**

**Permanent Jewish-reception gaps** (catalogued §9): Saadia Gaon (Judeo-Arabic fragments only); Yefet ben Eli (rare 1889 OUP, not freely-online); Ramban (no complete Daniel commentary); Ralbag (Sefaria 404, not online); Abrabanel (Sefaria 404 per gap-mapping; rabbinic anthologies have extracts).

### P4 — Second Temple Son of Man / Jewish-context Christian background

- **Charlesworth *OT Pseudepigrapha Vol 1*** — `LLS:OTPSEUD01` (**in-library**) — primary text for 4 Ezra 11-13 + 2 Baruch 36-40 + 39-42 + Sibylline Oracles + Apocalypse of Abraham; reception-event survey style per 1 Enoch Parables pattern. Serves M3, M6. **Wave 1.**
- **Lexham DSS Hebrew-English Interlinear** — `LLS:LDSSHEIB` (**in-library**) — primary text for Qumran 1QM + 4Q174 + 11Q13 + 4Q246 + 4QDan-a/b/c + 4Q243-245 Pseudo-Daniel; reception-event survey style. Serves M6. **Wave 2.**
- **Charlesworth *OT Pseudepigrapha Vol 2*** — `LLS:OTPSEUD02` (**in-library**) — Sibylline Oracles supplements + additional pseudepigrapha. Serves M6. **Wave 3.**
- **Charles *APOT* Vols 1-2 (1913)** — archive.org F12 (**freely-online**) — older standard ET as supplement and academic-citation backup. Serves M6 (low priority — Charlesworth is the modern equivalent).

### P5 — Beale-deepening / Wright / Hurtado / Fletcher-Louis

- **Wright *Jesus and the Victory of God*** (1996) — `LLS:JESUSVICTYGOD` (**in-library**; gap-mapping §5a-#9 confirms — the prior `method-and-limits.md §3a` "not in library" note was wrong) — Son of Man + Jesus self-understanding deepening beyond NTPG. Serves M3, M10, M11. **Wave 1.**
- **Bauckham *Theology of the Book of Revelation*** — `LLS:NTTHEO87REV` (**in-library**) — post-critical Revelation; pairs with Wright JVG. Serves M10, M11. **Wave 2.**
- **Beale *NIGTC Revelation*** — `LLS:29.71.18` (**in-library**) — Beale's full Revelation commentary, distinct from his Daniel-in-Revelation monograph. Serves M11. **Wave 3.**
- **Hurtado** (e.g., *Lord Jesus Christ*) — not surfaced in gap-mapping in-library list this session; likely in library (general Christology); requires sqlite3-verification before dispatch.
- **Fletcher-Louis** (e.g., *Jesus Monotheism*) — not surfaced; requires sqlite3-verification before dispatch.

### P6 — Modern critical breadth

- **Driver *Cambridge Bible Daniel*** (1900) — `LLS:CAMBC27DA` (**in-library**) **or** archive.org F9 (**freely-online**) — serves M1, M9. **Wave 3.**
- **Montgomery *ICC Daniel*** (1927) — `LLS:ICC_DA` (**in-library**) **or** archive.org F10 (**freely-online**) — serves M1, M9. **Wave 3.**
- **Charles *ICC Revelation*** (1920) — `LLS:ICC_REV` (**in-library**) — serves M11. **Wave 3.**
- **Anderson *Signs and Wonders ITC Daniel*** — `LLS:ITC21DAN` (**in-library**) — serves M9. **Wave 4.**
- **Pace *Daniel*** (Smyth & Helwys) — `LLS:SHC27DA` (**in-library**) — moderate critical Baptist; serves M9. **Wave 4.**
- **Seow *Daniel*** (Westminster Bible Companion) — `LLS:WBCS27DA` (**in-library**) — moderate critical; serves M9. **Wave 4.**
- **Davies *Daniel*** (Sheffield) — `LLS:SHEFFCL27DA` (**in-library**) — critical-introductory; serves M9. **Wave 4.**
- **Collins *The Apocalyptic Imagination*** 3rd ed. — `LLS:PCLYPTCMGNTNPLT` (**in-library**) — apocalyptic-genre method; serves M9. **Wave 4.**

### P7 — Reformed-pastoral (LAST — Bryan is himself Reformed-pastoral; over-weighting biases foundation)

- **Hoekema *The Bible and the Future*** — `LLS:BBLANDTHEFUTURE` (**in-library**) — Reformed-amil heaven-located. Serves M3, M4, M10. **Wave 5.**
- **Riddlebarger *A Case for Amillennialism*** — `LLS:CSAMLLNLSM` (**in-library**) — Reformed-amil earth-located. Serves M5, M10. **Wave 5.**
- **Sproul *Last Days according to Jesus*** — `LLS:LSTDYSCCRDNGJSS` (**in-library**) — partial-preterist. Serves M4, M5, M10. **Wave 5.**
- **Gentry *The Beast of Revelation*** — `LLS:BEASTREVELATION` (**in-library**) — partial-preterist Revelation-side. Serves M5, M10, M11. **Wave 5.**
- **Davis *Message of Daniel*** (BST) — `LLS:BST27DA` (**in-library**) — mediating-evangelical typological. Serves M5, M10. **Wave 5.**
- **Longman *NIVAC Daniel*** — `LLS:NIVAC27DA` (**in-library**) — mediating-evangelical transhistorical-recurrence. Serves M5, M10. **Wave 5.**
- **Lucas *Daniel*** (AOT) — `LLS:AOT27DA` (**in-library**) — mediating-evangelical near-far. Serves M5, M10. **Wave 5.**
- **Ladd *Theology of the New Testament*** — `LLS:THEONTLADD` (**in-library**) — historic-premil framework. Serves M4, M10. **Wave 5.**
- **Patterson *NAC Revelation*** — `LLS:NAC39` (**in-library**) — dispensational Revelation companion. Serves M11. **Wave 5.**
- **Koester *Revelation and the End of All Things*** — `LLS:RVLTNNDLLTHNGS2ED` (**in-library**) — Lutheran historical-critical Revelation. Serves M11. **Wave 5.**

---

## 8. Dispatch Waves — Copy-Paste-Ready Briefings

Each wave is sized to the established 4–5-concurrent-survey ceiling Bryan + codex confirmed. Dispatching in order: Wave 1 immediately; Waves 2–3 once Wave 1 returns and Wave 1 verifications land; Wave 4 after Waves 2–3; Wave 5 after Wave 4; Waves 6–7 after backend / schema work.

### Wave 1 — Highest-priority backfill (5 surveys, all in-library, no schema work)

Maximum priority breadth: P1 + P2 (×2 patristic) + P4 + P5 in one dispatch.

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 1.1 | **Newsom & Breed *OTL Daniel*** (2014) | `LLS:OTL27DA` | critical-modern reception-history | M2, M4, M5, M9 | Existing `logos` backend; `verify_citation` | `docs/research/scholars/newsom-breed-otl-daniel.json` |
| 1.2 | **Hippolytus *Fragments on Daniel + On Christ and Antichrist + On the End of the World*** (ANF 5) | `LLS:6.50.5` | patristic-Greek non-Antiochene | M2, M8 | Existing `logos` backend; **patristic-extension briefing** (anchor sub-section paths within the ANF 5 volume) | `docs/research/scholars/hippolytus-anf5-daniel.json` |
| 1.3 | **Augustine *City of God* Bk XX** | `LLS:CITYOFGOD` | patristic-Latin non-Jerome (load-bearing for amillennial Dan 7 + Rev 20) | M2, M8, M11 | Existing `logos` backend; **patristic-extension briefing** (focus on Bk XX explicitly — *not* the full *City of God*) | `docs/research/scholars/augustine-city-of-god-book-20.json` |
| 1.4 | **Charlesworth *OT Pseudepigrapha Vol 1*** → 4 Ezra 11-13 + 2 Baruch 36-40 + 39-42 reception-event survey | `LLS:OTPSEUD01` | second-temple-reception | M3, M6 | Existing `logos` backend; **reception-event briefing** (per 1 Enoch Parables pattern) | `docs/research/scholars/4-ezra-2-baruch-charlesworth-otp.json` |
| 1.5 | **Wright *Jesus and the Victory of God*** (1996) | `LLS:JESUSVICTYGOD` | post-critical / British BT (Son of Man + Jesus self-understanding) | M3, M10, M11 | Existing `logos` backend | `docs/research/scholars/wright-jesus-victory-of-god.json` |

**Estimated wall time:** 5–7h subagent dispatch + 1–2h verification.
**Outcome:** P1 closed; P2 patristic-Greek-non-Antiochene + patristic-Latin-non-Jerome each gain a JSON-backed voice; P4 advances (4 Ezra + 2 Baruch added); P5 Wright gains JSON status (and the §3a method-and-limits error has now been corrected — see §9 item 12). M9 moves from borderline-PASS to solid-PASS (Newsom adds reception-history dimension); M2 may move to PASS (Newsom + Hippolytus + Augustine all touch 7:9-12); M11 moves toward PASS (Augustine adds Rev 20 anchor); M3 advances toward PASS (4 Ezra + Wright JVG anchors); M6 moves from FAIL to PARTIAL.

### Wave 2 — Patristic / DSS deepening + Bauckham (5 surveys, all in-library, no schema work)

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 2.1 | **Cyril of Jerusalem *Catechetical Lecture* XV** (NPNF 2.7) | `LLS:6.60.21` | patristic-Greek (4th-c. Antichrist + Dan 7) | M8 | Existing `logos` backend; **patristic-extension briefing** | `docs/research/scholars/cyril-jerusalem-catechetical-15.json` |
| 2.2 | **Chrysostom *Homilies on Matthew*** (Olivet Discourse selections, NPNF 1.10) | `LLS:6.60.10` | patristic-Greek Matt 24 | M8, M11 | Existing `logos` backend; **patristic-extension briefing** (focus on Hom. on Matt 24 — Hom. 75-78 in NPNF numbering) | `docs/research/scholars/chrysostom-matt24-homilies.json` |
| 2.3 | **Victorinus *Commentary on the Apocalypse*** (ANF 7) | `LLS:6.50.7` | patristic-Latin Apocalypse (early Latin Revelation, pre-Augustinian millenarian sympathy) | M8, M11 | Existing `logos` backend; **patristic-extension briefing** | `docs/research/scholars/victorinus-apocalypse.json` |
| 2.4 | **Lexham DSS Hebrew-English Interlinear** → 1QM + 4Q174 + 11Q13 + 4Q246 + 4QDan-a/b/c + 4Q243-245 reception-event survey | `LLS:LDSSHEIB` | second-temple-reception (Qumran) | M6 | Existing `logos` backend; **reception-event briefing**; treat each scroll as sub-text citation | `docs/research/scholars/qumran-daniel-reception-lexham-dss.json` |
| 2.5 | **Bauckham *Theology of the Book of Revelation*** | `LLS:NTTHEO87REV` | post-critical / British BT (Revelation-side, pairs with Wright JVG) | M10, M11 | Existing `logos` backend | `docs/research/scholars/bauckham-theology-revelation.json` |

**Estimated wall time:** 6–8h (patristic surveys are slower) + 1–2h verification.
**Outcome:** patristic-Greek and patristic-Latin each move to ≥3 voices (Theodoret + Hippolytus + Cyril Jerusalem + Chrysostom on Greek side; Jerome + Augustine + Victorinus on Latin side); M6 moves from PARTIAL toward PASS (Qumran added); M11 deepens with patristic Matt 24 + early Latin Apocalypse; M10 gains Bauckham as post-critical anchor.

### Wave 3 — Pre-Collins critical + Beale Revelation + Charles (5 surveys, all in-library + freely-online supplements)

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 3.1 | **Driver *Cambridge Bible Daniel*** (1900) | `LLS:CAMBC27DA` (in-library) **or** archive.org F9 (freely-online) | pre-Collins critical (Walvoord's named foil) | M1, M9 | Existing `logos` backend if in-library; otherwise `external-pdf` | `docs/research/scholars/driver-cambridge-bible-daniel.json` |
| 3.2 | **Montgomery *ICC Daniel*** (1927) | `LLS:ICC_DA` (in-library) **or** archive.org F10 (freely-online) | pre-Collins critical | M1, M9 | Existing `logos` backend if in-library | `docs/research/scholars/montgomery-icc-daniel.json` |
| 3.3 | **Charles *ICC Revelation*** (1920) | `LLS:ICC_REV` (in-library) | pre-Beale critical Revelation | M11 | Existing `logos` backend | `docs/research/scholars/charles-icc-revelation.json` |
| 3.4 | **Beale *NIGTC Revelation*** | `LLS:29.71.18` (in-library) | reformed-amil major Revelation; cross-book authority distinct from Beale's Use-of-Daniel monograph | M11 | Existing `logos` backend | `docs/research/scholars/beale-nigtc-revelation.json` |
| 3.5 | **Charlesworth *OT Pseudepigrapha Vol 2*** → Sibylline Oracles III + IV + supplements reception-event survey | `LLS:OTPSEUD02` | second-temple-reception (Sib Or 4-kingdoms reuse) | M6 | Existing `logos` backend; **reception-event briefing** | `docs/research/scholars/sibylline-oracles-charlesworth-otp2.json` |

**Estimated wall time:** 5–6h + 1h verification.
**Outcome:** P6 advances; pre-Collins critical baseline established (M1, M9); M11 gains second Daniel-engaging Revelation commentary distinct from Beale-school (Beale's own NIGTC, distinct work); M6 reaches 5 voices (Parables + 4 Ezra + 2 Baruch + Qumran + Sib Or) — likely PASS.

### Wave 4 — Modern critical breadth (4 surveys; could grow to 5 if Anderson dispatched in parallel)

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 4.1 | **Pace *Daniel*** (Smyth & Helwys) | `LLS:SHC27DA` (in-library) | critical-mediating Baptist | M9 | Existing `logos` backend | `docs/research/scholars/pace-smyth-helwys-daniel.json` |
| 4.2 | **Seow *Daniel*** (Westminster Bible Companion) | `LLS:WBCS27DA` (in-library) | moderate critical | M9 | Existing `logos` backend | `docs/research/scholars/seow-westminster-bible-companion-daniel.json` |
| 4.3 | **Davies *Daniel*** (Sheffield Old Testament Guides) | `LLS:SHEFFCL27DA` (in-library) | critical-introductory | M9 | Existing `logos` backend | `docs/research/scholars/davies-sheffield-daniel.json` |
| 4.4 | **Anderson *Signs and Wonders ITC Daniel*** | `LLS:ITC21DAN` (in-library) | critical-mainline | M9 | Existing `logos` backend | `docs/research/scholars/anderson-itc-daniel.json` |
| 4.5 (optional) | **Collins *The Apocalyptic Imagination* 3rd ed.** | `LLS:PCLYPTCMGNTNPLT` (in-library) | apocalyptic-genre method | M9, M3 | Existing `logos` backend | `docs/research/scholars/collins-apocalyptic-imagination.json` |

**Estimated wall time:** 4–5h + 1h verification.
**Outcome:** M9 moves from borderline-PASS to deep-PASS with reception-history (Newsom Wave 1) + pre-Collins (Wave 3) + critical breadth (Wave 4) all anchored.

### Wave 5 — Reformed-pastoral cluster (5–6 surveys, all in-library; per priority order, dispatched LAST — these are the voices closest to Bryan's own posture and should not anchor the foundation)

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 5.1 | **Hoekema *The Bible and the Future*** | `LLS:BBLANDTHEFUTURE` (in-library) | Reformed-amil heaven-located | M3, M4, M10 | Existing `logos` backend | `docs/research/scholars/hoekema-bible-and-the-future.json` |
| 5.2 | **Riddlebarger *A Case for Amillennialism* (Expanded ed.)** | `LLS:CSAMLLNLSM` (in-library) | Reformed-amil earth-located | M5, M10 | Existing `logos` backend | `docs/research/scholars/riddlebarger-case-for-amillennialism.json` |
| 5.3 | **Sproul *The Last Days according to Jesus*** | `LLS:LSTDYSCCRDNGJSS` (in-library) | partial-preterist (moderate) | M4, M5, M10 | Existing `logos` backend | `docs/research/scholars/sproul-last-days-according-to-jesus.json` |
| 5.4 | **Gentry *The Beast of Revelation*** | `LLS:BEASTREVELATION` (in-library) | partial-preterist (Revelation-side) | M5, M10, M11 | Existing `logos` backend | `docs/research/scholars/gentry-beast-of-revelation.json` |
| 5.5 | **Davis *The Message of Daniel*** (BST) | `LLS:BST27DA` (in-library) | mediating-evangelical (typological compositional) | M5, M10 | Existing `logos` backend | `docs/research/scholars/davis-bst-daniel.json` |
| 5.6 (optional follow-on) | **Longman *NIVAC Daniel*** | `LLS:NIVAC27DA` (in-library) | mediating-evangelical (transhistorical-recurrence) | M5, M10 | Existing `logos` backend | `docs/research/scholars/longman-nivac-daniel.json` |
| 5.7 (optional follow-on) | **Lucas *Daniel*** (AOT) | `LLS:AOT27DA` (in-library) | mediating-evangelical (near-far) | M5, M10 | Existing `logos` backend | `docs/research/scholars/lucas-aot-daniel.json` |
| 5.8 (optional follow-on) | **Ladd *Theology of the New Testament*** | `LLS:THEONTLADD` (in-library) | historic-premillennial (Ladd's eschatological synthesis) | M4, M10 | Existing `logos` backend | `docs/research/scholars/ladd-theology-new-testament.json` |
| 5.9 (optional follow-on) | **Patterson *NAC Revelation*** | `LLS:NAC39` (in-library) | dispensational Revelation companion | M11 | Existing `logos` backend | `docs/research/scholars/patterson-nac-revelation.json` |
| 5.10 (optional follow-on) | **Koester *Revelation and the End of All Things* 2nd ed.** | `LLS:RVLTNNDLLTHNGS2ED` (in-library) | Lutheran historical-critical Revelation | M11 | Existing `logos` backend | `docs/research/scholars/koester-revelation-end-of-all-things.json` |

**Estimated wall time:** First 5 surveys ≈ 5h + 1h verification; full 10-survey expansion ≈ 10h + 2h verification (split across two dispatches if convenient).
**Outcome:** M10 moves from PARTIAL to PASS (mediating-evangelical, partial-preterist, Reformed-amillennial all gain JSON-backed voices); M11 moves toward PASS (dispensational + Lutheran-critical Revelation commentaries added). Bryan's own Reformed-pastoral posture is now well-anchored *as one tradition among many* rather than the foundation.

### Wave 6 — Medieval Jewish reception (5 Sefaria surveys; **prerequisite: backend work**)

**Prerequisite (PM ratification needed):** new `external-sefaria` or `external-html` backend kind. Verifier requires Hebrew NFC normalization, HTML stripping, and verse-anchored matching. Estimated 1–2 days backend work. Schema-extension briefing required.

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 6.1 | **Rashi on Daniel** | https://www.sefaria.org/Rashi_on_Daniel (freely-online F1) | medieval-Jewish plain-meaning (11c. France) | M3, M5, M7 | New `external-sefaria` backend; verifier handles Hebrew NFC | `docs/research/scholars/rashi-on-daniel.json` |
| 6.2 | **Ibn Ezra on Daniel** | https://www.sefaria.org/Ibn_Ezra_on_Daniel (freely-online F2) | medieval-Jewish grammatical (12c. Spain) | M3, M5, M7 | New backend | `docs/research/scholars/ibn-ezra-on-daniel.json` |
| 6.3 | **Joseph ibn Yahya on Daniel** | https://www.sefaria.org/Joseph_ibn_Yahya_on_Daniel (freely-online F3) | early-modern Sephardic (Bologna 1538) | M7 | New backend | `docs/research/scholars/ibn-yahya-on-daniel.json` |
| 6.4 | **Malbim on Daniel** | https://www.sefaria.org/Malbim_on_Daniel (freely-online F7) | modern-Hebrew anti-Haskalah (19c.) | M7 | New backend | `docs/research/scholars/malbim-on-daniel.json` |
| 6.5 | **Steinsaltz on Daniel** | https://www.sefaria.org/Steinsaltz_on_Daniel (freely-online F8) | modern-Orthodox (20-21c.) | M7 | New backend | `docs/research/scholars/steinsaltz-on-daniel.json` |

**Estimated wall time:** 1–2 days backend work + 4–5h surveys + 1h verification.
**Outcome:** M7 moves from FAIL to PASS (0 → 5 voices); the single largest deficiency in the corpus closes; the pilot can credibly claim Jewish-reception representation.

### Wave 7 — Reception-anthology integration (2 surveys; **prerequisite: anthology-shape schema variant**)

**Prerequisite (PM ratification needed):** anthology-shape schema variant — one anthology JSON file = many primary-voice extracts, each with its own backend anchor and own scholar attribution. Estimated 2–3 days schema design + integration. Anthology-shape briefing required.

| # | Voice | Resource | Source class | Mini-dossier(s) served | Verification approach | Output filename |
|---|---|---|---|---|---|---|
| 7.1 | **ACCS Daniel anthology** (Hippolytus, Theodoret, Augustine, Origen, Chrysostom, Cyril of Alexandria, Cyril of Jerusalem, Gregory the Great extracts) | `LLS:ACCSREVOT13` (in-library) | patristic-anthology | M2, M8 | New anthology-shape backend; per-extract attribution | `docs/research/scholars/accs-ot13-daniel.json` |
| 7.2 | **RCS Daniel anthology** (Bullinger, Vermigli, Œcolampadius, Lambert, Brenz, Pellican, Melanchthon extracts) | `LLS:REFORMCOMMOT12` (in-library) | Reformation-anthology | M8, M10 | New anthology-shape backend | `docs/research/scholars/rcs-ot12-daniel.json` |

**Estimated effort:** 2–3 days schema design + 6–8h surveys per anthology + 1–2h verification per anthology.
**Outcome:** M8 moves toward PASS at scholar tier (Reformation cluster moves from Calvin alone to multi-voice; patristic deepens with Cyril of Alexandria, Gregory the Great, Origen).

### Wave J (parallel, supports M2/M3) — Tooling support

- **Lexham Aramaic Lexicon integration** for Dan 7:13 OG vs Th text-criticism + Aramaic anchor field — `LLS:FBARCLEX` (in-library; on existing WS0c-9 queue; ~3h tooling integration, not a survey).

---

## 9. Permanent-Gap Acknowledgments (for `method-and-limits.md`)

These should be added to `method-and-limits.md` §3a (the PM should integrate; this document does not edit). Each item names the reason permanence holds and the dossier(s) it leaves under-anchored.

1. **No Hippolytus *Commentary on Daniel* full Greek-French (Lefèvre SC 14 1947).** Subscription Sources Chrétiennes; library access required. The ANF 5 fragments + tracts (`LLS:6.50.5`) are the maximum freely-available; archive.org F15 (Georgiades 1888) is partial. **Affects M8.**

2. **No medieval-Jewish voices via Saadia Gaon, Yefet ben Eli, Ramban, Ralbag, or Abrabanel direct surveys.** Saadia survives in Judeo-Arabic fragments only; Yefet's commentary is in the rare 1889 Margoliouth OUP edition not freely-online; Ramban did not write a complete Daniel commentary; Ralbag's Daniel commentary survives but is not online-digitized in any free repository found in the prior session; Abrabanel (Sefaria 404 per gap-mapping). **Mitigation:** Wave 6 covers Rashi, Ibn Ezra, ibn Yahya, Malbim, Steinsaltz freely. **Affects M3, M5, M7.**

3. **No German-only continental commentaries.** Klaus Koch (*Das Buch Daniel* + BKAT XXII), Otto Plöger (*Das Buch Daniel* KAT + *Theokratie und Eschatologie*), Klaus Berger, Hartmut Stegemann, Beate Ego — all German with no English translation; not actionable at $0 budget. **Affects M9.**

4. **No Eastern Orthodox modern academic Daniel commentary.** The Eastern Orthodox Daniel-reception tradition is liturgical and homiletical, not academic-monograph; no English-language Orthodox Daniel monograph located in the prior session. Theodoret is Antiochene-Greek but predates the Orthodox-Catholic split. **Affects M8.**

5. **No Pentecostal-charismatic distinctively-eschatological academic commentary.** The field is popular-devotional (Hagee, Lindsey, LaHaye) without academic primary-voice work. Walvoord + Pentecost cover the dispensational substrate. **Affects M10.**

6. **No post-Vatican-II Roman Catholic magisterial commentary on Daniel.** No magisterial document directly engages Dan 7 exegesis at length. LaCocque and Hartman/Di Lella (both JSON-backed) are the closest Catholic proxies; both pre-Vatican-II in theological sensibility. **Affects M9.**

7. **No pre-Tannaitic Jewish reception (Talmud, Midrash) consolidated survey.** Talmudic and midrashic Daniel-7 references are scattered across Bavli, Yerushalmi, and various midrash-collections; no consolidated commentary exists. Survey would require manual extraction; out of pilot scope. **Affects M7.**

8. **No primary-text engagement with Babylonian / Persian apocalyptic parallel literature.** Cuneiform "vaticinium ex eventu" (Akkadian prophecy texts) and Zoroastrian apocalyptic (Bahman Yasht) are relevant background per Collins's religio-historical method; specialist primary-source field; out of pilot scope. **Affects M9 method depth.**

9. **No Theodoret of Cyrus *Commentary on Daniel* — Hill 2006 SBL English translation (WGRW 7).** Out of stock at SBL Press; behind Brill paywall; dokumen.pub intermittent. **Mitigation:** the Greek PG 81 OCR (`external-resources/greek/theodoret-pg81-dan*.txt`) is in-corpus; Theodoret JSON-backed via `external-greek-ocr` backend. **Affects M8 (audit-quality only).**

10. **No comprehensive Aramaic textual-criticism / Old Greek vs. Theodotion treatment.** The corpus has passing references (Goldingay, Collins, Hartman/Di Lella); no scholar JSON adjudicates text-critical questions on Dan 7:13 (OG "as the Ancient" vs. Th "to the Ancient"). Lexham Aramaic Lexicon integration (WS0c-9 / Wave J) addresses linguistic anchoring; textual-criticism adjudication is a future workstream. **Affects M2, M3.**

11. **Theodoret OCR-quote tightening — deferred.** Codex audit §6.5 noted several Greek fragments too short to bear the rationale; the PG 81 OCR text is in `external-resources/greek/theodoret-pg81-dan7.txt` for a future tightening pass. Not a permanent gap, but a documented deferred item. **Affects M8.**

12. **§3a method-and-limits correction (Wright JVG) — RESOLVED 2026-04-26:** the prior `method-and-limits.md §3a` listed Wright *Jesus and the Victory of God* as "not in the Logos library." Gap-mapping §5a-#9 sqlite3-confirmed `LLS:JESUSVICTYGOD` is present; `method-and-limits.md §3a` was amended on 2026-04-26 to list Wright JVG as in-library at `LLS:JESUSVICTYGOD` (sqlite3-verified) with an explicit note that the resource was in the catalog and was missed in the WS0a cataloging pass. Wright JVG is scheduled for survey in WS0c-expansion Wave 1. **Record-correction now landed.**

13. **Acquisition-needed mitigations (per gap-mapping §5c, $0 budget; deferred indefinitely):** Stuckenbruck *1 Enoch 91-108* (M6 deepening); Yarbro Collins *Cosmology and Eschatology* (M6); Wright *Resurrection of the Son of God* (M3, M11 deepening); Henze *Jewish Apocalypticism in Late First Century Israel* (M6 deepening); Mounce *Revelation* (M11); Aune *Revelation 1-22* (M11). Each has a partial mitigation via in-library secondary engagement (Beale + Bauckham + Wright NTPG/JVG + Charlesworth OTP).

14. **Vocabulary expansion for M11 — APPLIED 2026-04-26**: `Acts 7`, `2 Thess 2`, `John 5`, `Heb 1`, `Heb 2` were added to `tools/validate_scholar.py:PASSAGE_COVERAGE_VOCAB` on 2026-04-26 to enable scoring NT cross-book breadth at the validator level. These passages are engaged in scholar rationale text (Walvoord, Pentecost, Theodoret, Jerome on 2 Thess 2; Beale on Acts 7) and are now flag-able by the validator. M11 source-class scoring at the validator level is unblocked.

---

SUFFICIENCY-MAP COMPLETE — 2/11 PASS, 7/11 PARTIAL, 2/11 FAIL. First-wave dispatch (5 surveys ready): Newsom & Breed *OTL Daniel* (`LLS:OTL27DA`), Hippolytus ANF 5 *Fragments on Daniel + On Christ and Antichrist + On the End of the World* (`LLS:6.50.5`), Augustine *City of God* Bk XX (`LLS:CITYOFGOD`), Charlesworth *OT Pseudepigrapha Vol 1* → 4 Ezra 11-13 + 2 Baruch 36-40 reception-event survey (`LLS:OTPSEUD01`), Wright *Jesus and the Victory of God* (`LLS:JESUSVICTYGOD`).
