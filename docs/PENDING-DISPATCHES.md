# Pending Dispatches — picked up after pause 2026-05-01

> **For the new PM session picking this up:** read `docs/PM-CHARTER.md`,
> `docs/SESSION-HANDOFF-WS0c-OCR-PREP-COMPLETE.md`,
> `docs/PROJECT-DECISIONS.md`, and `docs/FOLLOW-UPS-TRACKER.md` first.
> Then this doc carries the next three ready-to-dispatch session prompts
> verbatim, plus the future-trajectory outline.

## Quick state on pause (2026-05-01, K-5 = `85d2f49`)

- **Corpus**: 40 scholars / 1242 verified citations / 40/40 strict-validate
- **OCR-prep × 5 sessions**: all complete; text files committed in K-5
  under `external-resources/{latin,german,greek,hebrew,judeo-arabic}/`
- **Wave 3 + H-4 cleanup**: complete; committed in K-5
- **Origin**: https://github.com/tendflock/visual-theology @ `85d2f49`
- **Pending dispatches**: 3 wave coordinators drafted in this doc;
  not yet dispatched

## Dispatch ordering on resume

The three prompts in §1 below are **parallel-safe** — they write to
distinct output paths and use distinct backends. Spin all three up
concurrently when resuming. Each takes 6-8h subagent time + 1-2h
verification. Each will produce a codex review at the end with the
familiar dq-relabel pattern that gets cleaned in a follow-on H-* session
(see §2 trajectory below).

After the three return, dispatch H-5 / H-7 / H-8 codex relabel passes
in parallel (one per wave). Then K-6 consolidates and pushes. Then the
remaining trajectory in §2.

---

## §1. Three ready-to-dispatch prompts

### 1A. Wave 4 — Modern critical breadth (5 in-library Logos surveys)

```
[ROLE]
You are the Wave 4 dispatch coordinator for the visual-theology Daniel 7
pilot at /Volumes/External/Logos4. Fan out 5 parallel scholar surveys via
the Agent tool (general-purpose subagents, run_in_background); verify
each on return; report a summary back to the PM. You COORDINATE;
subagents EXECUTE.

[BACKGROUND READING — required before dispatch]

  1. docs/PM-CHARTER.md (note §5 parallel-coordinator + subagent
     staging-file rules — do NOT delete sibling files)
  2. docs/research/scholars/_SURVEY_BRIEFING.md
  3. docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md §8 Wave 4
  4. docs/SESSION-HANDOFF-WS0c-OCR-PREP-COMPLETE.md (current trajectory)
  5. Representative completed surveys for emulation:
       walvoord-daniel.json, newsom-breed-otl-daniel.json,
       collins-hermeneia-daniel.json, hartman-dilella-anchor-daniel.json
  6. docs/FOLLOW-UPS-TRACKER.md (codex's standing concerns about dq
     over-application — do NOT repeat the Wave 1/2/3 pattern; ~30
     relabels per wave is the existing failure mode)

[CROSS-COORDINATOR CONFLICT AVOIDANCE]

Wave 6.3 + Wave 7-pt-1 may be running in parallel. They write to
docs/research/scholars/* (different filenames) + may use external-ocr
backend. None of them write to your 5 output files. If unexpected files
appear in scholars/, leave them alone (parallel-coordinator rule). Same
for subagent staging files (_*.json, *_citations.json, *.tmp.*) — leave
alone if they're not yours.

[CONTEXT]

Corpus is at 40 scholars, 1242/1242 verified, on origin/main at 85d2f49.
WS0.6 §8 Wave 4 strengthens M9 (Daniel 7 in modern critical scholarship)
which is currently PASS-borderline. All 5 voices are in-library Logos
resources via existing logos backend.

[YOUR DISPATCH PROTOCOL]

For each of the 5 assignments below, dispatch an Agent call:
  - subagent_type: general-purpose
  - run_in_background: true
  - description: "Wave 4 survey: [scholar short name]"
  - prompt: paste the assignment block as the agent's prompt.

Wait for notifications — do not poll.

[ASSIGNMENT 4.1 — Pace, Daniel (Smyth & Helwys)]

Survey: Sharon Pace, *Daniel* (Smyth & Helwys Bible Commentary)
Resource: LLS:SHC27DA (in-library; sqlite3-confirm before dispatch)
Source class: critical-mediating Baptist
Tradition tag: critical-mediating (verify alignment with corpus's
              existing tags)
Mini-dossier: M9
Output filename: docs/research/scholars/pace-smyth-helwys-daniel.json
Backend: existing logos backend
Special instructions:
  - Pace's S&H Daniel is a moderate critical commentary in a Baptist
    series. Capture her exegetical moves on the four kingdoms,
    Son-of-Man, and Maccabean dating. Note where she diverges from
    standard ICC/Hermeneia critical readings.
  - English; quote.language defaults "en"; no translations[] needed.
  - Same supportStatus discipline as Wave 3: do NOT over-apply
    directly-quoted. Quote alone must prove the rationale's sub-claim.

[ASSIGNMENT 4.2 — Seow, Daniel (Westminster Bible Companion)]

Survey: C. L. Seow, *Daniel* (Westminster Bible Companion, 2003)
Resource: LLS:WBCS27DA (in-library; sqlite3-confirm)
Source class: moderate critical
Tradition tag: critical-mediating
Mini-dossier: M9
Output filename: docs/research/scholars/seow-westminster-bible-companion-daniel.json
Backend: existing logos backend
Special instructions:
  - Seow's WBC is shorter than ICC/Hermeneia but theologically engaged.
    Capture his canonical-critical synthesis, especially on Dan 7's
    relation to the rest of the canon.
  - Same supportStatus discipline.

[ASSIGNMENT 4.3 — Davies, Daniel (Sheffield)]

Survey: Philip R. Davies, *Daniel* (Old Testament Guides, Sheffield
        Academic Press)
Resource: LLS:SHEFFCL27DA (in-library; sqlite3-confirm)
Source class: critical-introductory
Tradition tag: critical-modern
Mini-dossier: M9
Output filename: docs/research/scholars/davies-sheffield-daniel.json
Backend: existing logos backend
Special instructions:
  - Davies' Sheffield Guide is concise and survey-style; capture his
    methodological framing of Daniel's apocalyptic + the Maccabean
    consensus. He's especially useful for M9's "what does the
    academic-critical mainstream actually believe" anchor.

[ASSIGNMENT 4.4 — Anderson, Signs and Wonders ITC Daniel]

Survey: Robert A. Anderson, *Signs and Wonders: A Commentary on the
        Book of Daniel* (International Theological Commentary)
Resource: LLS:ITC21DAN (in-library; sqlite3-confirm)
Source class: critical-mainline
Tradition tag: critical-modern (or critical-mediating depending on
              corpus alignment)
Mini-dossier: M9
Output filename: docs/research/scholars/anderson-itc-daniel.json
Backend: existing logos backend
Special instructions:
  - Anderson ITC is older critical (1984) and somewhat less rigorous
    than ICC/Hermeneia/Anchor. Useful as a critical-mainline anchor
    distinct from the ICC giants. Capture his framework + any
    distinctive moves.

[ASSIGNMENT 4.5 — Collins, Apocalyptic Imagination 3rd ed (optional 5th)]

Survey: John J. Collins, *The Apocalyptic Imagination* (3rd ed.)
Resource: LLS:PCLYPTCMGNTNPLT (in-library; sqlite3-confirm)
Source class: apocalyptic-genre method
Tradition tag: critical-modern
Mini-dossiers: M9, M3 (for the apocalyptic-genre method side)
Output filename: docs/research/scholars/collins-apocalyptic-imagination.json
Backend: existing logos backend
Special instructions:
  - This is Collins's genre-defining academic monograph on apocalyptic,
    distinct from his Hermeneia Daniel commentary already in corpus.
    Capture his methodological framework: what is "apocalyptic," what
    are its features, where does Daniel fit, how does Son-of-Man
    function in the genre. Don't duplicate his Hermeneia Daniel exegesis;
    focus on the genre-method side.

[VERIFICATION DISCIPLINE — non-negotiable]

Each subagent before claiming done:
  - tools/citations.py:verify_citation on every citation; status="verified"
    required.
  - passageCoverage[] uses controlled vocab.
  - supportStatus is honest — quote-outruns-rationale → demote to pa/si.
  - Cross-book entries in crossBookReadings[] only.

After all 5 subagents return, YOU run:
  1. pm2 stop study-companion
  2. python3 tools/validate_scholar.py docs/research/scholars/ --strict
  3. python3 tools/sweep_citations.py --scholars docs/research/scholars
       --out /tmp/wave4-sweep.md
  4. cd tools/workbench && python3 -m pytest tests/test_validate_scholar.py
       tests/test_citations.py -q
  5. pm2 start study-companion
  Confirm: 45/45 files validate (40 prior + 5 new); all citations verified;
  all tests pass.

[CODEX ADVERSARIAL REVIEW — REQUIRED, read-only sandbox]

  codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high \
    < prompt.txt > log.txt 2>&1

Codex SCOPED to YOUR coordination output (same structure as Wave 1/2/3
codex reviews). If codex returns no usable verdict, document + self-check.

[BOUNDARIES]

  - DO NOT commit. Leave new files unstaged.
  - DO NOT modify scholar JSONs other than the 5 you produce.
  - DO NOT delete files outside your 5-output set (parallel-coordinator
    + subagent staging-file rules).
  - DO NOT modify schema, validator, citations.py, or other tools/ files.
  - DO NOT touch external-resources/ (Wave 6.3 + 7 are reading there).
  - DO NOT exceed 5 concurrent subagents.

[REPORT BACK]

    WAVE 4 COMPLETE
    Files added: 5 (or 4 if optional 4.5 deferred)
    Per-file: [as Wave 1/2/3 format]
    Validator: 45/45 OK (or 44/44)
    Sweep: NN/NN verified
    Codex review: [verdict + findings]
    Stop. PM dispatches H-5 (Wave 4 cleanup) + Wave 5 next.
```

---

### 1B. Wave 6.3 — Jewish reception OCR-fed surveys (3 voices)

```
[ROLE]
Wave 6.3 dispatch coordinator for the visual-theology Daniel 7 pilot at
/Volumes/External/Logos4. Fan out 3 parallel surveys reading the
Hebrew/Judeo-Arabic OCR text files committed in K-5. M7 (Daniel 7 in
Jewish interpretation) — currently PARTIAL post-Wave 6.1+6.2 — moves
toward PASS.

[BACKGROUND READING]

  1. docs/PM-CHARTER.md (§5 parallel-coordinator + subagent staging-
     file rules)
  2. docs/research/scholars/_SURVEY_BRIEFING.md (Multilingual surveys
     section)
  3. docs/research/scholars/_TRANSLATION_CONFIG.md (translator SSoT)
  4. docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md §8
     Wave 6.3
  5. docs/research/2026-04-28-jewish-reception-multilingual-audit.md
     §B1, §B2, §B3 (the 3 voices' details)
  6. external-resources/hebrew/_OCR-PREP-NOTES.md
  7. external-resources/judeo-arabic/_OCR-PREP-NOTES.md
  8. docs/FOLLOW-UPS-TRACKER.md "OCR-prep × 5" section — esp. the
     Abrabanel visual-PDF-anchored discipline + Saadia/Klein attribution
     correction + Saadia Dan 2:1+ scope + Yefet line-9742 boundary
  9. docs/research/scholars/rashi-on-daniel.json AND
     bavli-sanhedrin-daniel7-reception.json (representative Wave 6.1 +
     6.2 surveys; subagents emulate)
  10. docs/research/scholars/theodoret-pg81-daniel.json (existing
      external-ocr precedent — Wave 6.3 voices follow this structural
      pattern)

[CROSS-COORDINATOR]

Wave 4 + Wave 7-pt-1 may run in parallel. Different output files; same
parallel-safety rules.

[YOUR DISPATCH PROTOCOL]

3 parallel Agent calls, run_in_background:true, descriptions
"Wave 6.3 survey: <voice>".

[ASSIGNMENT 6.3.1 — Abrabanel, Mayyenei ha-Yeshuah]

Survey: Don Isaac Abrabanel, *Mayyenei ha-Yeshuah* (Amsterdam print,
        1647 standard ed; Hebrew commentary on Daniel)
Backend: external-ocr
Source file: external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt
quote.language: "he"
Translations: ≥1 entry with language="en" REQUIRED per validator
              (D-2.6 enforcement). Use latest Opus per
              _TRANSLATION_CONFIG.md.
Source class: late-medieval Jewish (Iberian / Naples / Italy 1437-1508)
Tradition tag: medieval-jewish-rabbanite (verify against existing
              Wave 6.1 tags)
Mini-dossier: M7 (and possibly M3 / M5 if Daniel 7 engagement runs
              there)
Output filename: docs/research/scholars/abrabanel-mayyenei-ha-yeshuah.json
Special instructions (CRITICAL):
  - **Visual-PDF-anchored quote discipline**: the OCR text file has
    acceptable-with-caveat quality (HebrewBooks watermark frames + OCR
    character substitutions corrupting Hebrew proper nouns). Daniel
    keyword density in the OCR is unexpectedly low (דניאל=16 hits;
    בן.אנש=0 hits) — blind keyword-grep WILL miss content. Subagent
    workflow:
      1. Open the source PDF
         (/Volumes/External/Logos4/daniel/Hebrewbooks_org_23900.pdf)
         in a viewer.
      2. Identify Daniel-7-engaging passages by reading the Hebrew
         text directly.
      3. Locate the matching OCR substring as a SHORT CONSONANTAL
         PHRASE (3-7 Hebrew letters) — short enough that OCR character
         substitution doesn't break the match.
      4. Use that short phrase as quote.text; provide en translation
         alongside.
  - The HebrewBooks watermark frame ("Available for FREE at
    www.hebrewbooks.org" + ID 23900) appears around every page in the
    OCR. Filter quote anchors to AVOID the frame text — anchor only on
    Abrabanel's actual commentary body.
  - RTL Hebrew: tesseract heb output is logical-order; quote.text
    should reflect the actual Hebrew character sequence as it appears
    in the source.

[ASSIGNMENT 6.3.2 — Saadia Tafsir on Aramaic Daniel]

Survey: Saadia Gaon, *Tafsir on Aramaic Daniel* (Klein 1977 critical
        edition, YU thesis — corrects audit §B2's "Hurvitz 1977"
        attribution)
Backend: external-ocr
Source file: external-resources/judeo-arabic/saadia-tafsir-aramaic-daniel.txt
quote.language: "jrb" (Judeo-Arabic; some sections may have
                Hebrew-script fallback — verify per-citation)
Translations: ≥1 entry with language="en" REQUIRED.
Source class: medieval rabbanite (Babylonia 882-942 CE; Klein's modern
              edition publishes Saadia's medieval Aramaic Daniel)
Tradition tag: medieval-jewish-rabbanite (early; Geonic period)
Mini-dossier: M7
Output filename: docs/research/scholars/saadia-tafsir-aramaic-daniel.json
Special instructions (CRITICAL):
  - **Author attribution**: the YU thesis is by Klein, NOT Hurvitz as
    audit §B2 originally said. The audit error has been logged in
    docs/FOLLOW-UPS-TRACKER.md. In the survey JSON's frontend.author
    field, list "Saadia Gaon" (the source author whose work is being
    edited); in the editor/critical-edition note, cite "Klein 1977
    YU thesis."
  - **Scope correction**: codex flagged that Klein's edited body
    actually starts at Dan 2:1, not Dan 2:4b as the thesis title
    suggests. Survey can cite from Dan 2:1 onward. Document the
    full scope in the JSON's uncertainties[] field if relevant.
  - The OCR file's lines 1-60 are Klein's English typewriter intro
    (with OCR substitution issues); lines ~76-154 are Saadia's
    Aramaic body (cleaner, usable for survey-locator). Survey
    primarily cites from the body; if citing Klein's intro for
    framing, attribute clearly.

[ASSIGNMENT 6.3.3 — Yefet ben Eli on Daniel]

Survey: Yefet ben Eli ha-Levi (Karaite, late-10th-c. Jerusalem),
        *Commentary on Daniel* (Margoliouth 1889 ed., archive.org;
        chs 1-12 confirmed via running headers)
Backend: external-ocr
Source file: external-resources/judeo-arabic/yefet-ben-eli-margoliouth-1889.txt
quote.language: "jrb" (Judeo-Arabic; Margoliouth's edition publishes
                with Hebrew-script transliteration of Arabic where
                relevant — some sections may carry "he" or "arc")
Translations: ≥1 en REQUIRED.
Source class: medieval Karaite (10th-c. Jerusalem)
Tradition tag: medieval-jewish-karaite
Mini-dossier: M7
Output filename: docs/research/scholars/yefet-ben-eli-on-daniel.json
Special instructions (CRITICAL):
  - **Bound-volume boundary at line 9742**: the OCR file contains
    Margoliouth's Yefet edition (lines 1-9741) bound together with a
    second unrelated work, "THE PALESTINIAN VERSION" (lines 9742+ —
    likely a Karaite Hexapla witness). DO NOT cite from lines 9742+.
    Constrain quote anchors to lines ≤ 9741. Document this constraint
    in the JSON's uncertainties[] field.
  - Karaite tradition is distinct from Rabbanite (already covered by
    Rashi/Ibn Ezra/Saadia). Capture Yefet's Karaite-distinctive
    moves on Dan 7 — likely a focus on plain-text reading + polemic
    against Rabbanite midrashic interpretation.

[VERIFICATION DISCIPLINE]

Same as Wave 6.1: each subagent runs verify_citation; quote.language
correct; translations[] non-empty with ≥1 en; translator from
_TRANSLATION_CONFIG.md.

After all 3 return, YOU run validate + sweep + tests; confirm 48/48
files validate (45 post-Wave-4 + 3 Wave 6.3 — assumes Wave 4 also lands
before; if Wave 4 still in flight, your count will be 43/43 here, PM
reconciles).

[CODEX ADVERSARIAL REVIEW — REQUIRED, read-only sandbox]

Same shape as Wave 6.1 codex review. Spot-check 2-3 translations[]
entries per file (visual-PDF-anchored discipline produces tighter
quotes; the en translations should still be modern-faithful).

[BOUNDARIES]

Same as prior Jewish-reception coordinators (Wave 6.1 / 6.2). DO NOT
modify the OCR text files or _OCR-PREP-NOTES.md; READ-ONLY use of
external-resources/. DO NOT commit. DO NOT delete sibling-coordinator
files.

[REPORT BACK]

    WAVE 6.3 COMPLETE
    Files added: 3
    Per-file:
      abrabanel-mayyenei-ha-yeshuah.json — N cit (visual-anchor discipline applied)
      saadia-tafsir-aramaic-daniel.json — N cit (Klein attribution; Dan 2:1+ scope)
      yefet-ben-eli-on-daniel.json — N cit (Karaite voice; constrained to lines ≤9741)
    Validator: NN/NN OK
    Sweep: NN/NN verified
    Codex review: [verdict + findings]
    Stop. PM dispatches H-7 (Wave 6.3 codex relabel pass) next.
```

---

### 1C. Wave 7-pt-1 — Patristic + Reformation OCR-fed surveys (7 ready voices)

```
[ROLE]
Wave 7-pt-1 dispatch coordinator at /Volumes/External/Logos4. Fan out 7
parallel surveys reading the Latin/German OCR text files committed in
K-5. M8 (Daniel 7 in patristic + Reformation reception) moves toward
PASS. Origen + Mede defer to Wave 7-pt-2 after Wave 7-prep extracts
CCEL Contra Celsum (separate small session).

EXCEEDS THE 5-CONCURRENT-SUBAGENT CEILING. Per PM-CHARTER §4 the
established ceiling is 5 for Logos-reader contention; Wave 7's voices
read OCR text files (no Logos contention). Coordinate as TWO sub-waves
of subagents:
  Wave 7-pt-1a: 4 subagents in parallel (Cyril, Gregory, Bullinger, Œcolampadius)
  Wave 7-pt-1b (after 1a returns): 3 subagents (Melanchthon, Lambert, Luther)
This avoids piling up too many concurrent sessions while staying under
the file-conflict-free OCR-text-read pattern.

[BACKGROUND READING]

  1. docs/PM-CHARTER.md
  2. docs/research/scholars/_SURVEY_BRIEFING.md (Multilingual surveys)
  3. docs/research/scholars/_TRANSLATION_CONFIG.md
  4. docs/research/2026-04-28-patristic-reformation-fulltext-audit.md
     (final D-1.6 audit — voice details + sources)
  5. external-resources/latin/_OCR-PREP-NOTES.md (long-s caveats; quality
     per voice; Lambert's Daniel-INFERRED status)
  6. external-resources/german/_OCR-PREP-NOTES.md (Luther WA canonical
     vs 1545 Bibel witness)
  7. external-resources/greek/_OCR-PREP-NOTES.md (Cyril Mai vol 2
     Greek-Latin parallel-column layout — relevant to Cyril Latin
     extraction)
  8. docs/FOLLOW-UPS-TRACKER.md (Wave 7 / OCR-prep follow-ups)
  9. Existing Wave 6.2 reception-event JSONs as structural model:
     1-enoch-parables-nickelsburg-vanderkam.json (for Cyril fragments
     + Gregory Moralia where citations are scattered)

[CROSS-COORDINATOR]

Wave 4 + Wave 6.3 may run in parallel. Different output files +
backends; same parallel-safety rules. Wave 7-prep + Wave 7-pt-2 are
separate later sessions and don't conflict.

[ASSIGNMENT 7.1 — Cyril of Alexandria, Daniel fragments (Latin)]

Source file: external-resources/latin/cyril-alexandria-daniel-fragments.txt
quote.language: "la"
Backend: external-ocr
Translations: ≥1 en REQUIRED per D-2.6 enforcement
Source class: patristic-Greek (5th-c. Alexandria; surviving Daniel
              fragments via Mai *Nova Bibliotheca Patrum* vol 2 +
              PG 70 listing)
Tradition tag: patristic
Mini-dossier: M8
Output: docs/research/scholars/cyril-alexandria-daniel-fragments.json
Notes:
  - Mai vol 2 Latin column (the Greek column lives in
    cyril-alexandria-daniel-fragments-greek.txt; this assignment is the
    Latin parallel). Cyril's Daniel work survives only in fragments;
    the Latin Mai column is the canonical parallel publication.
  - Long-s caveat per OCR notes; quote anchors should be short distinctive
    phrases robust to long-s OCR substitution.

[ASSIGNMENT 7.2 — Gregory the Great, Moralia in Job (PL 75)]

Source file: external-resources/latin/gregory-moralia-vol1.txt
quote.language: "la"
Backend: external-ocr
Translations: ≥1 en REQUIRED
Source class: patristic-Latin (6th-c. Rome; *Moralia* engages Daniel
              typologically across many books — Vita pp. ~1-17,000;
              substantive content from there)
Tradition tag: patristic
Mini-dossier: M8
Output: docs/research/scholars/gregory-moralia-daniel.json
Notes:
  - The Moralia is a vast work; Daniel-engagement is scattered. Survey
    finds the Daniel-7-engaging passages within the Moralia (typology
    of beasts; little horn = Antichrist; saints' kingdom).
  - PL 75 is the source volume per the audit (M-3 reframed from Bliss
    English to PL Latin).

[ASSIGNMENT 7.3 — Bullinger, In Danielem (1571)]

Source file: external-resources/latin/bullinger-daniel-1571.txt
quote.language: "la"
Backend: external-ocr
Translations: ≥1 en REQUIRED
Source class: Reformation (Zürich; Bullinger 1571 Daniel commentary
              edition — distinct from his 1576 *homiliis 66* form)
Tradition tag: reformation-reformed
Mini-dossier: M8 (with M5 if little-horn engagement is rich; M11 if
              Revelation cross-references are dense)
Output: docs/research/scholars/bullinger-in-danielem-1571.json
Notes:
  - Pervasive long-s in OCR per notes; same anchoring discipline.
  - Bullinger's Reformation-Reformed reading: typically four-kingdoms
    historicist + Antichrist-as-papacy. Capture explicit moves.

[ASSIGNMENT 7.4 — Œcolampadius, In Danielem (1530)]

Source file: external-resources/latin/oecolampadius-in-danielem-1530.txt
quote.language: "la"
Backend: external-ocr
Translations: ≥1 en REQUIRED
Source class: Reformation (Basel 1530; foundational early Reformation
              Daniel commentary — predates Bullinger / Calvin)
Tradition tag: reformation-reformed
Mini-dossier: M8
Output: docs/research/scholars/oecolampadius-in-danielem-1530.json
Notes:
  - 1530 Basel typesetting; long-s pervasive. Greek epigram on title
    page may show inline; ignore for Daniel survey purposes.
  - Œcolampadius is the earliest Reformation full-text Daniel
    commentary in the corpus; capture his methodology + his
    engagement with the typological tradition.

[ASSIGNMENT 7.5 — Melanchthon, In Danielem (1543)]

Source file: external-resources/latin/melanchthon-daniel.txt
quote.language: "la"
Backend: external-ocr
Translations: ≥1 en REQUIRED
Source class: Reformation (Wittenberg 1543; Lutheran reform-foundational)
Tradition tag: reformation-lutheran
Mini-dossier: M8
Output: docs/research/scholars/melanchthon-in-danielem-1543.json
Notes:
  - 1543 Wittenberg edition; long-s + page-edge artefacts (vertical
    pipes / stray glyphs at periphery — filter these out of quote
    anchors).
  - Melanchthon is the load-bearing Lutheran Reformation Daniel voice
    distinct from Luther's Vorrede (Luther's coverage is the
    preface, not a full commentary; Melanchthon wrote the commentary).

[ASSIGNMENT 7.6 — Lambert, In Apocalypsim (1528)]

Source file: external-resources/latin/lambert-in-apocalypsim-1528.txt
quote.language: "la"
Backend: external-ocr
Translations: ≥1 en REQUIRED
Source class: Reformation (Marburg 1528; commentary on Revelation,
              not Daniel — Daniel-INFERRED via Rev 13/17/20
              cross-references per audit M-3 demotion)
Tradition tag: reformation-reformed
Mini-dossier: M8 (engagement is INFERRED — verify; if Daniel-7
              engagement density is below 5 substantive citations,
              survey marks Lambert as enrichment-tier, not load-bearing)
Output: docs/research/scholars/lambert-in-apocalypsim-1528.json
Notes:
  - Lambert's *In Apocalypsim* is a Revelation commentary, not a Daniel
    commentary. His Daniel-7 engagement comes through Rev 13 (beast),
    Rev 17 (kingdoms), Rev 20 (millennium + saints) cross-references
    where he reads back to Daniel.
  - If Daniel-7 engagement is sparse (< 5 substantive citations), the
    survey JSON should still land but with explicit
    `commitmentProfile.daniel_engagement_density: "INFERRED — primary
    work is on Apocalypse"` so Wave 8 / Phase D rescore knows.

[ASSIGNMENT 7.7 — Luther, Vorrede über den Propheten Daniel (WA DB 11/II)]

Source file: external-resources/german/luther-vorrede-wa-db-11-ii.txt
  (canonical critical surface)
Witness file: external-resources/german/luther-1545-bibel-vorrede.txt
  (1545 Wittenberg Bibel — witness; Fraktur OCR caveat)
quote.language: "de" (note: "de" not "deu" — match the corpus's
                ISO-639-1 convention; verify against existing
                D-2.5 OCR_LANGUAGE_DIRS keys)
Backend: external-ocr
Translations: ≥1 en REQUIRED
Source class: Reformation (Wittenberg 1545 / WA edition; Luther's
              preface to Daniel — the canonical Lutheran
              hermeneutical statement on Dan 7)
Tradition tag: reformation-lutheran
Mini-dossier: M8
Output: docs/research/scholars/luther-vorrede-daniel.json
Notes:
  - Cite from WA DB 11/II as canonical; reference 1545 Bibel as
    witness/acquisition surface where helpful.
  - Luther's Vorrede is shorter than Melanchthon's commentary but
    establishes the Lutheran reading of Dan 7 (four kingdoms with
    contemporary Roman/Turkish + Antichrist application).

[VERIFICATION DISCIPLINE]

Same as prior multilingual waves. quote.language correct per voice;
translations[] non-empty with ≥1 en; long-s OCR caveats handled via
short distinctive quote anchors.

After all 7 (4 in 7-pt-1a + 3 in 7-pt-1b) return, YOU run validate +
sweep + tests; confirm corpus count = 40 + 5 (Wave 4) + 3 (Wave 6.3) +
7 (Wave 7-pt-1) = 55, MINUS however many of those waves are still in
flight. PM reconciles.

[CODEX ADVERSARIAL REVIEW — REQUIRED, read-only sandbox]

Same shape. Spot-check 2-3 translations[] per file. Watch for
over-application of dq (the Wave 1/2/3 systematic pattern; Wave 7's
Latin quotes are short due to long-s discipline, which may push
toward dq more than Wave 6.1; codex review will flag).

[BOUNDARIES]

Same as prior coordinators. DO NOT modify OCR text files (read-only
use). DO NOT commit. DO NOT delete sibling-coordinator files.
DO NOT begin Wave 7-pt-2 surveys (Origen + Mede; separate session
after Wave 7-prep).

[REPORT BACK]

    WAVE 7-PT-1 COMPLETE
    Files added: 7
    Sub-wave 1a (4 voices): Cyril, Gregory, Bullinger, Œcolampadius
    Sub-wave 1b (3 voices): Melanchthon, Lambert, Luther
    Per-file: [as Wave 1/2/3 format with long-s caveat status]
    Validator: NN/NN OK
    Sweep: NN/NN verified
    Codex review: [verdict + findings; expect dq over-application
      flags similar to Wave 1/2/3]
    Stop. PM dispatches H-8 (Wave 7-pt-1 codex relabel pass) +
      Wave 7-prep (CCEL Contra Celsum + Mede Cooper extract) next.
```

---

## §2. Future trajectory — outline (no full prompts yet)

After Wave 4 / 6.3 / 7-pt-1 return + their codex relabel passes
(H-5 / H-7 / H-8) land, K-6 consolidates and pushes. Then:

**Wave 7-prep** (small ~1h session): extend `external-ocr` to accept
`"en"` (currently restricted to non-en languages by D-2.6 enforcement);
provision `external-resources/english/` with README.md; update validator
+ tests + schema doc + briefing; run extract_ocr.sh --html on CCEL
Contra Celsum → `external-resources/english/origen-contra-celsum-ccel.txt`;
codex review at end. Smaller alternative if scope creep concerns: implement
`external-html` backend as a distinct kind (the audit's original wording).
PM ratifies which path before dispatch.

**Wave 7-pt-2** (after Wave 7-prep): 2 voices via the now-available
`en` OCR path:
  - Origen *Contra Celsum* (CCEL ANF 4 English; primary Daniel surface
    per the audit redirect logged in method-and-limits §3a)
  - Mede *Clavis Apocalyptica* via Cooper 1833 ET (archive.org;
    extract via extract_ocr.sh --djvu mode → english/ output)

**Wave 5** (Reformed-pastoral cluster, dispatched LAST per WS0.6 §8
P7 ordering rule — Bryan is himself Reformed-pastoral, over-weighting
biases foundation): 5-10 in-library Logos surveys: Hoekema,
Riddlebarger, Sproul, Gentry, Davis BST, Longman, Lucas, Ladd,
Patterson, Koester. Strengthens M3/M4/M5/M10/M11. Same coordinator
shape as Wave 1/2/3/4. Likely 2 dispatch sub-waves (5 + 5).

**Phase D** — codex adversarial end-to-end audit of the entire corpus
once all waves above + their cleanups are committed. If PASS, declare
peer-review-grade. If FAIL, address findings before WS1.

**WS1** — visual implementation per
`docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md`.
Only after Phase D PASS.

---

## §3. New PM session bootstrap

When a new PM session picks up, the bootstrap is:

1. Read `docs/PM-CHARTER.md` (§5 for parallel-coordinator + subagent
   staging-file rules; §11 reading list pointing here)
2. Read `docs/SESSION-HANDOFF-WS0c-OCR-PREP-COMPLETE.md` (current state)
3. Read `docs/PROJECT-DECISIONS.md` (architectural ratifications)
4. Read `docs/FOLLOW-UPS-TRACKER.md` (deferred items + active
   follow-ups by source session)
5. Read this doc for ready-to-dispatch prompts
6. Verify git state matches handoff (`git log --oneline -10` should
   show K-5 commits 60c9b43 / c199811 / b3a5ce6 / 85d2f49 as the
   most recent visual-theology-track commits)
7. Spin up Wave 4 / 6.3 / 7-pt-1 per §1 above (parallel-safe;
   ratify with Bryan first if any has changed since 2026-05-01)
