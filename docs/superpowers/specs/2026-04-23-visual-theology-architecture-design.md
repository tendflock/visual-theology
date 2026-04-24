# Visual Theology Architecture — Design Spec

Date: 2026-04-23 (revised 2026-04-24)
Status: Draft v2 (integrates codex creative review + second-pass library survey)
Author: Bryan + Claude (with parallel research delegated to multiple subagents)

## Project Context

Bryan built a visual study site for Romans 3:10-18 at **tendflock.github.io/Romans3** — a scrolling narrative that traces Paul's catena through six OT sources, with interactive mosaic, back-absorption animation, and confidence-tagged claims. Source files are in `/Users/family/Downloads/_push 2/` and the editorial charter is there as `STYLE.md` and `CLAUDE.md`.

The Romans 3 build proved a pattern: `data.js` as single-source-of-truth content model, `app.js` as renderer, `styles.css` for design system, dual HTML files for GitHub Pages, and an opinionated editorial charter. It works because the underlying argument is tight and the motion moments are argumentative rather than decorative.

The user wants to extend this pattern to Daniel — starting with Daniel 7 — and eventually to other topics and passages. Daniel is larger and more contentious than a single pericope. Eschatology is a teaching domain Bryan has avoided precisely because of its contentiousness, but the visual-theology approach makes entering it approachable.

## Project Goal

Build a repeatable, Logos-library-grounded, research-backed visual theology system that:

1. Teaches a first-time learner (including the author) the interpretive landscape of a passage or topic.
2. Represents each interpretive school in its own best terms, with cited proponents, without strawman summaries.
3. Uses layered disclosure — scroll for narrative, click for detail, confidence tiers for trust, attribution footer for outbound sources — rather than modal toggles.
4. Adapts the visual argument per topic/passage. The working metaphor is **decision cascade** — Daniel's interpretive disagreements are rule-driven and upstream-downstream (an answer on axis A constrains axis B, N governs whether Revelation can override Daniel, M is a rule about how you enter the map), not parallel lanes. An interstate metaphor was an early draft; codex's creative review flagged that it fails under five axes with five traditions. Final visual metaphor is deferred to design/UX exploration (WS4).
5. Produces sibling static sites that share schema, editorial rules, and tooling.

Daniel 7 is the pilot. If the architecture holds, Daniel 9:24-27, Daniel 11-12, and topic sites ("Son of Man", "The Seventy Weeks") follow.

## Audience and Pedagogy

**Single audience, layered depth.** Every site serves every audience by exposing depth progressively:

- **Layer 1 (pew):** the narrative, the symbol, the "so what." Readable by a bright newcomer to eschatology.
- **Layer 2 (intermediate):** exegesis, interpretation schools, key arguments, why scholars disagree.
- **Layer 3 (deep):** original languages, textual witnesses, historical background, outbound links to commentaries, monographs, primary sources.

Layering is not a mode toggle. It is realized through four orthogonal axes:

1. **Scroll = argument progression.** Each chapter earns its place in the arc.
2. **Click/hover = detail depth.** Phrase → drawer with deeper material.
3. **Confidence tiers (`documented` / `strong-judgment` / `noted-gap`) = trust depth.** Named on every claim.
4. **Attribution footer = outbound source depth.** Named proponents, works, editions, pages.

## Editorial Charter

Inherited from the Romans 3 build, with Daniel-specific additions.

### From Romans 3 (non-negotiable)

- **Scholarly but accessible voice.** Educated reader who isn't a specialist. Translate every Greek/Hebrew/Aramaic word the first time in prose.
- **No emoji. BC/AD** (not BCE/CE). Dates: `c. AD 57`, `c. 150 BC`, `3rd c. AD`.
- **Paraphrastic English only.** All English glosses written fresh for this project. No pasted ESV, NIV, NRSV, NASB, KJV, or any copyrighted translation. The NET Bible's translator's notes may inform a fresh paraphrase; NET translation text must not be reproduced wholesale.
- **Ancient text from public-domain critical editions only.** BHS / BHQ for Hebrew and Aramaic, Rahlfs-Hanhart / Göttingen for LXX, Nestle-Aland / UBS for NT.
- **No filler.** If a paragraph doesn't move the argument forward, cut it.
- **Muted oklch palette**, chroma ~0.08. No hard-coded hex.
- **Type stack fixed:** Source Serif 4 (English), Gentium Plus (Greek), Frank Ruhl Libre (Hebrew). Add no fourth face.
- **Motion argues or doesn't exist.** No scroll-driven decorative animation, no parallax, no entrance effects beyond the `.reveal` fade. Every motion moment must make an argument.
- **Confidence tiers named on every claim.** `documented`, `strong-judgment`, `noted-gap`. Noted gaps stay noted — never quietly upgraded.
- **Dual HTML files** (GitHub Pages `index.html` + canonical named file) stay byte-for-byte identical.

### Daniel-specific additions

- **Steelman rule.** Every interpretive school represented must be cited from its own best proponents in the Logos library, with a direct quote, not a summary. No strawmen. No "X school believes Y simplification" paraphrases that a holder of X wouldn't recognize.
- **Source discipline.** The research backbone is the Logos library. Vetted external sources (e.g., peer-reviewed articles, the PureBibleForum textual-criticism thread on Psalm 14/Romans 3/Vaticanus) may be cited as aids. Facebook posts, general-web blogs, and AI-generated summaries are excluded.
- **Schools as vectors, not flat labels.** A scholar's position is a combination of positions across multiple axes (see Data Model §). Compound labels ("Reformed inaugurated amillennial," "dispensational pretribulational premillennial futurist") are welcome; flat single-axis labels are usually wrong.
- **No school caricature in narrative.** If the narrative has to describe what a school believes in its own voice, use its proponents' vocabulary. "Dispensationalists think history is divided into watertight dispensations" fails. "Classical dispensationalists distinguish Israel and the church as two peoples of God with distinct plans, following Darby, Scofield, and Chafer" passes.
- **Name the kind of disagreement.** Before reporting a disagreement, name it: textual, historical, typological, theological, or inferential. Readers handle heat better when they know whether the split is over Daniel's date, over Revelation's control on Daniel, or over eschatological system-building. This habit lowers temperature without abdicating judgment.
- **Pastoral de-escalation register.** Frame each position as a careful host would: "here is why serious readers are drawn to this position; here is the cost of adopting it." Not an end-times cage match. Write like a pastor introducing a newcomer to the sanctuary, not a debater.
- **Text / inference / system distinction.** Keep the three layers visibly separate in the narrative. What the text says. What the reader must infer to apply it. What eschatological system the inference belongs to. Worked example: *"Daniel 7 shows a blasphemous persecuting power hostile to the saints of the Most High. Identifying that power as Antiochus IV, future Antichrist, a typological pattern, or a transhistorical principle is the next interpretive move."* That sentence holds text, inference, and system apart in one breath.

## Source Discipline

All claims trace to one of three source tiers:

1. **Logos library (primary).** The local installed resources. Each claim names the resource, article number, and a direct quote or paraphrase close enough to the quote that a reader could find it.
2. **Vetted external (secondary).** Used only when the library lacks material. Criteria: named author, published venue (peer-reviewed or equivalent), verifiable citation. The PureBibleForum thread on Psalm 14 in Vaticanus/Sinaiticus/Alexandrinus is an example of an external source that passes because it documents actual manuscript evidence with citations.
3. **Public-domain primary (occasional).** Printed critical editions, manuscript facsimiles, Jerome, Eusebius, Montfaucon.

**Excluded categories:** Facebook posts, social-media discussion, general-web blogs, AI-generated summaries, devotional-only resources without scholarly backing, Wikipedia (except as a starting point to find primary sources).

## Data Model

### Five-layer structure (v2)

The v1 schema (axes → traditions → topics) has been revised after codex's creative review and the v2 library survey. The changes are substantive: scholars become the primary index with traditions as tags; positions become compositional; canonical placement and cross-book coherence move into a separate `readingRules` layer; and every position gets a `commitment` field distinct from claim confidence.

1. **Axes catalog** — global. Sixteen named questions with named positions. Axes A–O cover first-order content positions on the text. Axes P (meaning-locus) and Q (genre-eschatology relation) are optional meta-axes used for framing in editorial voice rather than first-order positions. See `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` for the full catalog.
2. **Reading rules** — global. Meta-hermeneutical constraints separate from first-order axes: canonical placement (was M), cross-book coherence (was N), meaning-locus (P), and genre-eschatology relation (Q). These govern how positions combine, not what positions exist. A scholar's reading rules affect many axes at once.
3. **Scholars catalog** — global, primary. Every named scholar is a record with a compositional position per axis. Scholars are the atomic unit of citation; traditions are aggregations over scholars.
4. **Traditions catalog** — global, optional. Named clusters of correlated positions for pedagogical shortcut (e.g., "Reformed inaugurated amillennial"). Members may diverge from the characteristic vector on some axes (e.g., Hoekema and Riddlebarger both amil but diverge on kingdom ontology, heaven vs. earth). Includes reception-history traditions (e.g., Reformation historicism) explicitly labeled as non-live.
5. **Topics** — site-level. Each topic invokes specific axes + reading rules, lists the scholars in play, and collects citations. Convergence and divergence are topic-level summaries.

### Axes

```javascript
axes: {
  "dating": {
    id: "dating",
    question: "When was the book of Daniel composed?",
    positions: [
      { id: "traditional-6c", label: "Traditional (sixth-century)" },
      { id: "maccabean-2c",   label: "Maccabean (second-century)" },
      { id: "bifurcated",     label: "Bifurcated: Persian-Diaspora stories + Antiochene visions (Lucas)" }
    ]
  },
  "little-horn": {
    id: "little-horn",
    question: "Who or what is the little horn of Daniel 7?",
    positions: [
      { id: "antiochus-iv",          label: "Antiochus IV Epiphanes" },
      { id: "future-antichrist",     label: "Future Antichrist" },
      { id: "papal-rome",            label: "Papal Rome (Reformation historicist)" },
      { id: "transhistorical",       label: "Transhistorical evil power" },
      { id: "literary-symbol",       label: "Literary symbol of oppressor, no personal identity (Wright)" }
    ]
  },
  // ... 16 axes total
}
```

No `color` field on positions. Color lives at a higher level (chapter identity or argument role, not position identity) — see Open Decisions §4.

### Reading rules (separate from axes)

```javascript
readingRules: {
  "cross-book-coherence": {
    id: "cross-book-coherence",
    question: "Must Daniel and Revelation readings cohere? In which direction?",
    positions: [
      { id: "strict",               label: "Strict coherence (Beale, dispensationalists)" },
      { id: "loose",                label: "Loose coherence (Davis, Longman)" },
      { id: "nt-reinterprets",      label: "NT reinterprets Daniel (Riddlebarger, Wright)" },
      { id: "none",                 label: "No coherence requirement" }
    ]
  },
  "meaning-locus": { /* Axis P — origin / reception / canonical / literal-future */ },
  "genre-eschatology": { /* Axis Q */ },
  "canonical-placement": { /* Writings / Prophets */ }
}
```

### Scholars (primary)

```javascript
scholars: {
  "davis-dale-ralph": {
    id: "davis-dale-ralph",
    name: "Dale Ralph Davis",
    work: "The Message of Daniel: His Kingdom Cannot Fail (BST)",
    resource: "BST27DA",
    positions: {
      "dating": {
        basePosition: "traditional-6c",
        commitment: "strong",
        citation: { article: 379, quote: "..." }
      },
      "little-horn": {
        // Compositional position — codex's schema recommendation
        basePosition: "future-antichrist",
        fulfillmentMode: "typological-chain",
        extendsTo: ["antiochus-iv", "other-historical-antichrists"],
        scope: "both-past-and-future",
        commitment: "strong",
        citation: { article: 381, quote: "antichrists before the Antichrist..." }
      }
      // ... one entry per axis the scholar addresses
    },
    readingRules: {
      "cross-book-coherence": { position: "loose", commitment: "moderate" }
    }
  },
  "riddlebarger-kim": {
    id: "riddlebarger-kim",
    name: "Kim Riddlebarger",
    work: "A Case for Amillennialism: Understanding the End Times",
    resource: "CSAMLLNLSM",
    positions: {
      "little-horn": {
        basePosition: "transhistorical",
        fulfillmentMode: "transhistorical-recurrence-with-climactic-singular",
        // "Two threats merging into a single end-time figure" (art. 667)
        commitment: "strong",
        citation: { article: 667, quote: "these two distinct threats merge into a single threat at the time of the end..." }
      },
      "millennium": {
        basePosition: "amil",
        subPosition: "earth-located-church-militant",
        commitment: "strong",
        citation: { article: 702, quote: "There is a real millennium despite the amillennial nomenclature..." }
      }
      // ...
    }
  },
  "hoekema-anthony": {
    // Amil like Riddlebarger, diverges on kingdom-locus
    id: "hoekema-anthony",
    positions: {
      "millennium": {
        basePosition: "amil",
        subPosition: "heaven-located-reigning-souls",
        commitment: "strong",
        citation: { article: 743, quote: "the present reign of the souls of deceased believers with Christ in heaven" }
      }
    }
  },
  "walvoord-john": { /* dispensational-premillennial-pretrib */ },
  "newsom-carol": { /* Maccabean critical; angelic-Michael Son of Man */ },
  "longman-tremper": { /* 6c dating + unspecified fourth-kingdom + transhistorical-recurrence */ },
  "lucas-ernest": { /* bifurcated dating + Greek fourth-kingdom + near-far fulfillment */ }
  // ... many more
}
```

Compositional positions (`basePosition` + `fulfillmentMode` + `extendsTo` + `scope`) handle mediating positions that break flat enums: Davis's "antichrists before the Antichrist," Riddlebarger's "two threats merging," Koester's Antiochus-expanding-to-imperial-type, Lucas's near-far with Christological extension.

`commitment` (`strong` / `moderate` / `tentative`) is separate from claim confidence (`documented` / `strong-judgment` / `noted-gap`). Confidence is about the claim's evidential standing; commitment is about how central the position is to the scholar's system. Sproul's "I must confess that I am still unsettled on some crucial matters" (art. 225) is a `tentative` commitment on the millennium but a `strong` commitment on partial preterism.

### Traditions (cluster tags)

```javascript
traditions: {
  "reformed-inaugurated-amillennial": {
    label: "Reformed inaugurated amillennial",
    characteristicVector: {
      "dating": "traditional-6c",
      "fourth-kingdom": "rome",
      "little-horn": "transhistorical",
      "millennium": "amil",
      "rev-approach": "modified-idealist-eclectic",
      "disp-cov": "covenantal",
      "eschatological-structure": "inaugurated"
    },
    members: ["beale-gk", "hoekema-anthony", "riddlebarger-kim", "vos-geerhardus"],
    // Intra-tradition divergences must be surfaced, not averaged away:
    intraTraditionNotes: [
      "Hoekema and Riddlebarger both amil but diverge on kingdom ontology — Hoekema heaven-located, Riddlebarger earth-located.",
      "Riddlebarger is Beale-era updated amil; Hoekema is Hendriksen-era classic amil."
    ]
  },
  "historicist-reformation": {
    label: "Historicist Reformation tradition",
    status: "reception-history",  // Not a live academic option; preserved for pedagogy
    characteristicVector: {
      "little-horn": "papal-rome",
      "rev-approach": "historicist",
      "disp-cov": "covenantal"
    },
    primarySources: [
      { name: "Joseph Mede",     work: "Clavis Apocalyptica (1627)",                 publicDomain: true },
      { name: "Isaac Newton",    work: "Observations upon the Prophecies of Daniel", publicDomain: true },
      { name: "Christopher Wordsworth", work: "The New Testament: Revelation",       publicDomain: true }
    ],
    note: "Dominant 16th–19th c. Protestant reading; not held by any modern academic voice in the library. Included for historical awareness."
  },
  "dispensational-premillennial-pretrib": { /* Walvoord, Patterson, Tanner (futurist elements) */ },
  "critical-maccabean-historical": { /* Collins, Newsom, Driver, Montgomery, Koester */ },
  "historic-premillennial-covenantal": { /* Ladd, Spurgeon via Beeke&Smalley */ },
  "irenic-evangelical-mediating": { /* Longman, Lucas, Davis — the pattern codex flagged as real */ }
}
```

### Topics

```javascript
topics: [{
  id: "dan7-little-horn",
  passage: "Daniel 7:7-8, 19-25",
  question: "Who or what is the little horn?",
  relevantAxes: ["little-horn", "dating", "fourth-kingdom", "rev-approach", "disp-cov"],
  relevantRules: ["cross-book-coherence", "meaning-locus"],

  convergence: [{
    text: "All surveyed scholars agree the little horn is a specific persecuting power hostile to the saints of the Most High.",
    confidence: "documented",
    sources: [ /* named scholars + article numbers */ ]
  }],

  divergence: [{
    axis: "little-horn",
    text: "Scholars split on temporal placement, personal identity, and fulfillment structure.",
    confidence: "documented"
  }],

  // Scholars in play — the primary index. Tradition-level patterns surface as notes.
  scholarsInPlay: [
    "beale-gk", "hoekema-anthony", "riddlebarger-kim", "walvoord-john",
    "patterson-paige", "driver-sr", "montgomery-james", "koester-craig",
    "davis-dale-ralph", "longman-tremper", "lucas-ernest", "tanner-j-paul",
    "newsom-carol", "collins-john-j", "sproul-rc"
  ],

  traditionPatterns: [
    { tradition: "critical-maccabean-historical", summary: "All hold Antiochus IV with single fulfillment; Newsom adds angelic-Michael Son of Man interpretation." },
    { tradition: "reformed-inaugurated-amillennial", summary: "Transhistorical / symbolic-recurrence readings; Riddlebarger adds two-threats climactic-singular mechanic." },
    { tradition: "irenic-evangelical-mediating", summary: "Refuse to fix identity flat-enum — Davis types, Longman transhistorical-unspecified, Lucas near-far." }
  ]
}]
```

## Research Workflow

Five stages per topic. Each stage leaves a durable artifact.

```
/studies/daniel-7/
  research/
    sources.md            # curated Logos resources + vetted external, with rationale
    schools.md            # which axes apply to this topic; which traditions are in play
    steelman/
      reformed-amillennial.md         # each tradition's steelman from its own best voices
      dispensational-premillennial.md
      critical-maccabean.md
      historic-premillennial.md
      idealist-modified.md
    claims.json           # claim registry with confidence + citations
    convergence.md        # where schools converge on this topic
    divergence.md         # where they genuinely split
  writing/
    narrative-arc.md      # draft argument progression
    dossier.md            # integrated academic version
    layman.md             # pew-level rendering
    proofing-notes.md     # flagged overstatements, strawmen
  site/
    data.js
    index.html
    ...
```

### Stage 1 — Scope

Define the topic, the passage anchor, and which axes apply. Output: `sources.md` opening section, `schools.md`.

### Stage 2 — Source discovery

For each relevant axis, find the primary library sources for each named position. Use existing `companion_tools.py`; extend with steelman-query, citation-verifier, claim-extractor tools. Output: `sources.md` full list.

### Stage 3 — Steelman research

One dossier per tradition in play. Each dossier quotes named proponents from the library verbatim, in the proponent's own vocabulary. Codex or a steelman-review agent verifies no strawmen. Output: `steelman/*.md`.

### Stage 4 — Claim extraction and cross-verification

Extract atomic claims with confidence tiers. Cross-verification agent reads the cited source and confirms the claim is supported. Output: `claims.json`.

### Stage 5 — Convergence / divergence analysis

Where do the traditions agree? Where do they split? This becomes the teaching structure of the site. Output: `convergence.md`, `divergence.md`.

## Writing Workflow

Four stages per topic. Each stage has a review gate.

### Stage 1 — Narrative arc

Draft the argument progression — what chapter comes first, what the motion moments argue, what the confidence footer holds. Output: `narrative-arc.md`.

### Stage 2 — Academic dossier

The integrated, scholarly version. Quote-heavy, citation-heavy, honest about gaps. Output: `dossier.md`.

### Stage 3 — Layman rendering

The pew-level narrative. Fresh paraphrase. No jargon untranslated. Claims stay confidence-tagged. Output: `layman.md`.

### Stage 4 — Proofing

Re-read for overstatement, oversimplification, strawman, false dichotomy. Output: `proofing-notes.md` with fixes applied to `layman.md`.

## Quality Gates

Non-negotiable checks before a topic advances:

1. **Source discipline.** Every claim traces to a Logos-library citation or a vetted external. Orphan claims fail.
2. **Steelman pass.** Each tradition in play is represented from its named best proponent, in its own vocabulary, with a direct quote. Codex verifies.
3. **Cross-verification.** A second-pass agent reads the cited source and confirms the claim is supported. The hallucination kill-switch.
4. **Overstatement / strawman review.** The layman rendering re-read for caricature, false dichotomy, or sneaking in of a conclusion.
5. **First-time-learner readability.** A reader unfamiliar with "preterist" can follow without prior knowledge, because the site defines terms before using them.

## Visual Modalities

A vocabulary of rendering moves — not a menu one picks from per topic. Each topic's visual treatment is argumentative and specific; this list is the vocabulary design/UX collaboration (WS4) draws from.

**Core modalities:**

- **Courtroom transfer map** (added from codex review). Data: thrones, court session, verdict, beastly dominion removed, Son of Man receiving kingdom, saints receiving kingdom, with each scholar's sequencing and referent claims attached. What it teaches: Daniel 7 is a judicial transfer scene before it is anything else. Beale, Patterson, and Koester disagree on timing and referents, but all must account for the same transfer of authority. Cross-domain analogy: baseball win-probability charts where the same game state is read through changing leverage.
- **Typology escalator** (added from codex review). Data: candidate fulfillments arranged in layers (Antiochus IV → Rome/imperial oppression → final Antichrist), with scholars placed at the layer where they stop or continue. What it teaches: mediating readings (Davis, Morris, Koester) are not fuzzy compromises; they are structured escalation claims. Cross-domain analogy: phylogenetic trees or malware-family lineage maps.
- **Interpretation grid** — rows = axes invoked; columns = scholars (not traditions); cells = positions with citation popovers. Scholar-indexed, following codex's "scholars first" critique. Tradition grouping is an optional overlay.
- **Symbol-to-referent overlay** — for symbols (beasts, little horn, weeks), the symbol at center, candidate referents ringing it, commitment + confidence per scholar. Includes a **symbol-pressure meter**: what features each scholar treats as literal-historical, typological, or transhistorical.
- **Timeline bands** — stacked chronologies, one band per tradition, showing where each places events.
- **Intertext graph** — Daniel passage at center, NT allusions ringing it, weight of allusion per scholar.
- **Confidence ribbon** — visual indicator next to every claim showing both confidence tier and commitment strength.
- **Chapter-paced narrative (Romans 3 pattern)** — the default frame; scroll-as-argument.

**Key motion moment (Daniel 7 signature — codex proposal):**
- **Branch-and-lock animation** — the user toggles one upstream decision (e.g., fourth-kingdom = Greek vs. Rome), and downstream readings visibly re-route and then lock into place. This replaces Romans 3's back-absorption autoplay. Daniel's pedagogy is cascade, not absorption; branch-and-lock argues cascade visibly.

Back-absorption (Romans 3's final motion) does NOT transfer to Daniel. In Romans 3 it argued source-formation; in Daniel it would imply a canonical sink that dissolves live disagreement.

The `data.js` schema supports all of these because the scholars + compositional-positions + reading-rules structure is rich enough to render any of them.

## Tooling Requirements

### Existing and reusable

- `tools/study.py` — Logos reader orchestrator
- `tools/workbench/companion_tools.py` — 7 working tools (Bible, lexicon, grammar, commentary, cross-refs, outline, interlinear)
- `tools/logos_batch.py` — persistent reader subprocess
- `tools/resource_index.py` — resource indexing for lookup
- `resource_index.db` — cached index

### New tools to build (reusable across all sibling sites)

- **`steelman_query`**: "Summarize tradition X's reading of passage Y from sources A, B, C in the tradition's own vocabulary, with direct quotes ≥ 2 per source."
- **`citation_verifier`**: "Given claim C and citation (resource R, article A), read the source and confirm the claim is actually supported. Return verified / partially-supported / not-supported / source-unreadable."
- **`claim_extractor`**: "Given a research dossier or commentary reading, extract atomic claims with confidence tiers and citations."
- **`schema_validator`**: Static validator that every `data.js` conforms to the axis/tradition/topic schema.
- **`site_renderer`**: Adapter that takes `axes + traditions + topics` and produces the site content in the Romans 3 pattern.

### Hardening dependency

Fix 11 (cataloged-but-not-installed detection) in `docs/plans/2026-04-23-logos-reader-hardening.md` is a prerequisite for reliable claim verification, because the reader currently returns 0 articles silently for uninstalled resources. Without the fix, verification agents will miss this failure mode.

## Roles

- **Bryan.** Owner, theological compass, steelman judge, final edit, pew-reader representative.
- **Claude (this repo).** Schema, tooling, research-dossier generation, cross-verification scripts, writing support.
- **Codex.** Adversarial review (pushes back on conclusions, flags strawmen, checks that nothing got over-softened); design/UX collaboration on per-topic visual modalities; review of this spec.
- **Subagents.** Bounded bulk research — one agent per tradition, or one agent per Logos resource family — producing steelman dossiers that land in `research/steelman/`.
- **Logos library + companion_tools.py.** Source-of-truth for all library content.

## Pilot Scope: Daniel 7

First deliverable sibling site. Scope (tightened from 5 topics to 3 on codex's creative-review recommendation).

- **Passage:** Daniel 7 (Aramaic vision of four beasts, Son of Man, Ancient of Days, saints receiving kingdom).

- **Three pilot topics:**
  1. **The Four Beasts / The Four Kingdoms** — backbone. Invokes axes A, B, L, M (canonical placement as reading rule). Without this, later disagreements float.
  2. **The Little Horn** — sharpest divergence point and best stress test for the compositional schema. Invokes axes A, B, C, E, F, K, O (fulfillment structure); reading rules include cross-book coherence and meaning-locus.
  3. **The Son of Man** — theological payoff and Daniel-to-Gospels-to-Revelation intertextual hinge. Invokes axes J, C, N (cross-book coherence rule).

  Saints Receiving the Kingdom and Ancient of Days are folded in rather than separate: Saints→the courtroom transfer map embedded in the four-kingdoms chapter; Ancient of Days→opening frame of the Son of Man chapter.

- **Scholars in play across the pilot** (from v2 survey; ~15 primary voices, more as auxiliary):
  Beale, Koester, Beeke/Smalley (+Hoekema, Vos via), Riddlebarger, Hoekema directly, Bauckham, Wright, Collins (Hermeneia pending Fix 12; Apocalyptic Imagination available), Newsom, Longman, Lucas, Davis, Tanner, Patterson, Walvoord (pending Fix 12), Driver, Montgomery, Sproul.

- **Traditions surfaced as pedagogical tags** (not primary containers):
  Critical-Maccabean historical · Reformed inaugurated amillennial · Irenic evangelical mediating (Davis/Longman/Lucas) · Dispensational premillennial pretribulational · Historic premillennial covenantal · Historicist Reformation tradition (reception-history only, clearly labeled).

- **Signature motion moment:** **branch-and-lock** on the fourth-kingdom decision. User toggles Greek or Rome, the little-horn identity, seventy-sevens terminus, and fourth-beast referent re-route and lock. Argues the cascade of consequences.

- **Secondary motion moments (Romans 3 motifs that transfer):**
  - **Hinge thread** for dependency chains (fourth kingdom ↔ little horn).
  - **Mosaic hover** for Son of Man intertexts (Dan 7:13 → Mt 24, Mk 14, Rev 1:7, Rev 14:14) and beast imagery.

- **Confidence tiers + commitment strength** shown on every claim.
- **Attribution footer** listing every Logos resource with resource ID, edition, and article numbers. Public-domain historicist sources (Mede, Newton) linked separately.

## Workstream Decomposition (Parallelizable)

Each workstream can run in a separate session.

- **WS1 — Schema + Daniel 7 stub** (Claude). Lock the scholar/axis/tradition/reading-rule schema. Populate a Daniel 7 `data.js` stub with the little-horn topic fully populated — including compositional positions (Davis, Riddlebarger) and commitment-strength fields — to validate the schema against real data.
- **WS2 — Editorial charter** (Claude, codex reviews). Adapt the Romans 3 `STYLE.md` + `CLAUDE.md` to the Daniel project. Add the steelman rule, the three new voice habits (disagreement-kind naming, pastoral de-escalation, text/inference/system distinction), the axis vocabulary protocol, and how topic-level content maps to HTML chapters.
- **WS3 — Research tooling** (Claude). Build `steelman_query`, `citation_verifier`, `claim_extractor`, `schema_validator`. Extend `companion_tools.py`. Depends on hardening Fix 11 and Fix 12 (`.lbxlls` support for Collins Hermeneia + Walvoord + Blaising/Bock).
- **WS4 — Design/UX exploration** (codex). Sketch per-topic visual modalities in rough HTML prototypes — courtroom transfer, typology escalator, branch-and-lock motion, interpretation grid. Not final design; a vocabulary of moves. **Overlaps with WS1** — schema and visual requirements co-evolve. If a modality needs a schema field we haven't encoded (e.g., `mediates`, `escalatesTo`), it gets added to WS1 before WS5 kicks off.
- **WS5 — Pilot research** (subagents per scholar-cluster, then Claude integrates). Subagents produce steelman dossiers from Logos sources, one per tradition-cluster. Runs after WS1-3 provide the schema, charter, and tooling. Output: `studies/daniel-7/research/steelman/*.md`.
- **WS6 — Pilot writing** (Bryan primary, Claude support). Narrative arc → dossier → layman → proofing for Daniel 7.
- **WS7 — Pilot site build** (Claude builds, codex reviews design). Renders `data.js` into the site matching the Romans 3 pattern.

## Open Decisions (must resolve before WS5 kicks off)

1. **Scholars-primary schema validated against real data.** WS1 populates a little-horn stub; if Davis's "antichrists before the Antichrist" and Riddlebarger's "two threats merging" cleanly encode with the compositional-position fields, schema is ratified. If they don't, schema gets revised.
2. **Tradition list and intra-tradition divergences.** Current six traditions named in Pilot Scope. Intra-tradition divergences (Hoekema vs. Riddlebarger on kingdom-locus) are encoded as notes — but do we surface them as first-class in the site, or leave them for attentive readers? Bryan decides.
3. **Topic list for Daniel 7 pilot — confirmed at three.** Four Beasts, Little Horn, Son of Man. Saints and Ancient of Days fold in. Bryan can expand if momentum allows.
4. **Per-topic visual modality.** WS4 output feeds this. Codex explores the vocabulary (courtroom transfer, typology escalator, branch-and-lock, interpretation grid, symbol-to-referent). The chosen motion for each topic is argumentative, not decorative.
5. **Color protocol — dropped per-tradition coloring** (codex critique: five tradition colors = tribal design). Color is reserved for argument role (textual / historical / typological / theological / inferential) or chapter identity. Scholar and tradition identity are encoded by **line style, badges, proximity, typography** — not hue. Design review in WS4.
6. **Sibling vs. single-repo deployment.** Three sibling sites as separate repos (like Romans 3 lives separately) or one monorepo with subdirectories. Leaning separate repos for GitHub Pages URL discipline.
7. **Axes P and Q elevation.** P (meaning-locus) and Q (genre-eschatology relation) live in the reading-rules layer; they do not surface as first-order axes in the Daniel 7 pilot. Later topic sites (e.g., "Son of Man," "Apocalyptic Genre") may elevate them. Bryan decides topic-by-topic.
8. **Historicist Reformation tradition rendering.** Included as reception-history with public-domain sources (Mede, Newton, Wordsworth). Render as a labeled "historical tradition, no longer widely held" voice, not as a live academic option. Final visual treatment determined in WS4.

## Spec Review Next Steps

Per the brainstorming workflow, this spec needs:

1. Bryan's review and approval.
2. Codex's creative review (UX, design, editorial, scope).
3. Revision based on feedback.
4. Then the plan: `docs/superpowers/plans/YYYY-MM-DD-visual-theology-daniel-7.md`.

### What Bryan Should Look For (v2)

- Does the scholars-primary schema with compositional positions fit how you teach? Specifically: can you see Davis's mediating position ("antichrists before the Antichrist") correctly encoded?
- The three new editorial voice habits (disagreement-kind naming, pastoral de-escalation, text/inference/system distinction) — these are *your* voice habits. Do they fit what you want to sound like? Would you write differently?
- Axes P and Q live in the reading-rules layer, not the main axis list. Is that the right demotion, or should meaning-locus (especially) be a first-class axis?
- Tradition-level intra-divergences (Hoekema heaven-located vs. Riddlebarger earth-located amil) — surface these in the site for pedagogy, or leave them as dossier notes?
- Pilot tightened from 5 to 3 topics. Does that feel right, or would you expand?

### What Codex Should Look For (v2 changes addressed; new questions)

Addressed from first-round review:
- Schema inverted to scholars-primary with traditions as tags (✓)
- Compositional positions (basePosition / fulfillmentMode / extendsTo / scope) (✓)
- Commitment-strength field distinct from confidence tiers (✓)
- Reading rules layer for axes M, N, P, Q (✓)
- Multilane interstate replaced with decision cascade; final visual metaphor deferred to WS4 (✓)
- Three voice habits added to editorial charter (✓)
- Back-absorption dropped; branch-and-lock is signature motion (✓)
- Pilot tightened to 3 topics; Saints and Ancient of Days fold in (✓)
- No per-tradition coloring; color for argument role or chapter identity only (✓)
- WS1 and WS4 now overlap (schema + visuals co-evolve) (✓)
- Historicism added as reception-history tradition with public-domain sources (✓)
- Axis O (fulfillment structure) added (✓)

New questions for codex's next review:
- Does the scholars-primary encoding actually support the courtroom transfer and typology escalator modalities at the data level, or do we need more compositional structure?
- Is the "irenic evangelical mediating" tradition (Davis/Longman/Lucas) a real tradition or a pedagogical grouping that should stay a note rather than a cluster tag?
- The six-tradition list — is one still missing, given that partial preterism (Sproul) doesn't fit any of them?

---

## Appendices

### Appendix A: The 16 Axes (14 content + 2 meta)

Full axis catalog with positions lives in `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` §"The 13 Axes of Interpretation" (v1) and §"Second-Pass Survey (2026-04-24): Nine New Voices" → "Expanded axis catalog (v2)." Axes P and Q are meta-hermeneutical and live in the `readingRules` layer of the data model rather than the primary `axes` catalog.

### Appendix B: Research Backbone

Full library survey: `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md`.

### Appendix C: Romans 3 Template Reference

Editorial charter, visual system, and file architecture: `/Users/family/Downloads/_push 2/STYLE.md` and `CLAUDE.md`. Content model pattern: `data.js` in same directory.

### Appendix D: Dependencies

- `docs/plans/2026-04-23-logos-reader-hardening.md` Fix 11 (cataloged-but-not-installed detection) is a prerequisite for WS3 claim verification.
- **Fix 12** (`.lbxlls` caller-level audit — design at `docs/research/2026-04-24-codex-lbxlls-design.md`) unblocks Collins *Daniel* (Hermeneia), Walvoord *Daniel*, and Blaising & Bock *Progressive Dispensationalism*. These are the primary voices for critical-modern Daniel, classical-dispensational Daniel, and progressive dispensationalism respectively.
- Codex's first-round creative review archived at `docs/research/2026-04-24-codex-review-visual-theology-spec.md`. This spec v2 integrates those recommendations.
- Existing companion infrastructure in `tools/workbench/` is the tooling foundation. No new Flask app needed; the visual theology sites are pure static.
