# Visual Theology Architecture — Design Spec

Date: 2026-04-23
Status: Draft (for review)
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
4. Adapts the visual argument per topic/passage (the "multilane interstate" metaphor: schools as lanes that converge, branch, borrow, and reconverge).
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

## Source Discipline

All claims trace to one of three source tiers:

1. **Logos library (primary).** The local installed resources. Each claim names the resource, article number, and a direct quote or paraphrase close enough to the quote that a reader could find it.
2. **Vetted external (secondary).** Used only when the library lacks material. Criteria: named author, published venue (peer-reviewed or equivalent), verifiable citation. The PureBibleForum thread on Psalm 14 in Vaticanus/Sinaiticus/Alexandrinus is an example of an external source that passes because it documents actual manuscript evidence with citations.
3. **Public-domain primary (occasional).** Printed critical editions, manuscript facsimiles, Jerome, Eusebius, Montfaucon.

**Excluded categories:** Facebook posts, social-media discussion, general-web blogs, AI-generated summaries, devotional-only resources without scholarly backing, Wikipedia (except as a starting point to find primary sources).

## Data Model

### Three-layer structure

1. **Axis catalog** — global, reusable across all sibling sites. Each axis is a named question with named positions.
2. **Traditions catalog** — global, optional. Named clusters of correlated positions across axes (e.g., "Reformed amillennial," "dispensational premillennial"). Shortcuts for pedagogy; not ontological claims.
3. **Topics** — site-level. Each topic invokes specific axes and cites positions with library sources.

### Axes

Derived from the library survey at `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md`. The full list (13 axes) appears there. The Daniel 7 pilot invokes axes A, B, C, E, F, J, K, L, N.

```javascript
axes: {
  "dating": {
    id: "dating",
    question: "When was the book of Daniel composed?",
    positions: [
      {
        id: "traditional-6c",
        label: "Traditional (sixth-century)",
        shortLabel: "6th c.",
        color: "oklch(0.55 0.09 25)",
        tint: "oklch(0.96 0.025 25)",
        ink: "oklch(0.35 0.09 25)"
      },
      {
        id: "maccabean-2c",
        label: "Maccabean (second-century)",
        shortLabel: "2nd c.",
        color: "oklch(0.55 0.09 265)",
        tint: "oklch(0.96 0.025 265)",
        ink: "oklch(0.35 0.09 265)"
      }
    ]
  },
  // ... one entry per axis
}
```

### Traditions

```javascript
traditions: {
  "reformed-inaugurated-amillennial": {
    label: "Reformed inaugurated amillennial",
    shortLabel: "Reformed/amil",
    representativePositions: {
      dating: "traditional-6c",
      "fourth-kingdom": "rome",
      "little-horn": "transhistorical",
      "rev-approach": "modified-idealist-eclectic",
      "millennium": "amillennial",
      "rapture-timing": null,
      "eschatological-structure": "inaugurated",
      "disp-cov": "covenantal",
      "son-of-man": "messianic-corporate"
    },
    exemplars: [
      { name: "G. K. Beale", resource: "NIGTCREV", article: 3819, work: "The Book of Revelation (NIGTC)" },
      { name: "Anthony Hoekema", resource: "RFRMDSYSTH04", article: 4716, work: "cited in Beeke and Smalley, Reformed Systematic Theology, Vol. 4" },
      { name: "Geerhardus Vos", resource: "BBLCLTHNTSTMNTS", article: null, work: "Biblical Theology: Old and New Testaments" }
    ]
  },
  "dispensational-premillennial-pretrib": { /* ... */ },
  "critical-maccabean-historical": { /* ... */ },
  "historic-premillennial-covenantal": { /* ... */ }
}
```

### Topics

A topic is the unit the narrative renders. Each topic invokes one or more axes and collects position citations.

```javascript
topics: [{
  id: "dan7-little-horn",
  passage: "Daniel 7:7-8, 19-25",
  question: "Who or what is the little horn?",
  relevantAxes: ["little-horn", "dating", "fourth-kingdom", "rev-approach", "disp-cov"],

  convergence: [
    {
      text: "All surveyed schools agree the little horn is a specific persecuting power hostile to the saints of the Most High.",
      confidence: "documented",
      sources: [
        { resource: "EEC27DA", article: 2557 },
        { resource: "NAC18", article: null },
        { resource: "ICC_DA", article: null },
        { resource: "CAMBC27DA", article: 365 }
      ]
    }
  ],

  divergence: [
    {
      axis: "little-horn",
      text: "Schools split on temporal placement and identity: past (Antiochus IV), future (Antichrist), typological (Antiochus foreshadowing Antichrist), or transhistorical (principle of evil across history).",
      confidence: "documented"
    }
  ],

  positions: [
    {
      axis: "little-horn",
      positionId: "antiochus-iv",
      heldBy: [
        {
          tradition: "critical-maccabean-historical",
          source: "CAMBC27DA",
          article: 365,
          quote: "the Book of Daniel must have been written not earlier than c. 300 b.c., and in Palestine; and there are considerations which make it highly probable that it was, in fact, composed during the persecution of Antiochus Epiphanes, between b.c. 168 and 165"
        },
        {
          tradition: "critical-maccabean-historical",
          source: "ICC_DA",
          article: null,
          quote: "..."
        }
      ],
      strongestCase: "The little horn's specific acts (stops sacrifices, breaks weekly cycles, speaks against the Most High for 'time, times, and half a time' = 3.5 years) match Antiochus IV's persecution precisely (167–164 BC). Daniel 8 explicitly identifies its little horn with the king arising from the Greek empire's fourfold division; the consistency of symbolism across Dan 7 and Dan 8 suggests the same referent.",
      strongestChallenge: "Dan 7's fourth kingdom is not the Greek empire in the traditional reading; on that reading the little horn cannot be Antiochus IV (who arose from the Greek empire, which is then the third kingdom)."
    },
    {
      axis: "little-horn",
      positionId: "future-antichrist",
      heldBy: [
        {
          tradition: "dispensational-premillennial-pretrib",
          source: "NAC39",
          article: null,
          quote: "..."
        },
        {
          tradition: "traditional-evangelical-futurist",
          source: "EEC27DA",
          article: 2557,
          quote: "..."
        }
      ],
      strongestCase: "...",
      strongestChallenge: "..."
    }
    // ... more positions
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

Deferred for codex's design/UX collaboration. The research gives us the data; codex and Bryan work out how to render it per topic. A first set of candidate modalities:

- **Interpretation grid** — rows = axes invoked by a topic; columns = traditions; cells = positions with citation popovers.
- **Multilane interstate** — axes as parallel horizontal lanes, traditions as paths through the lanes, convergence and divergence visible spatially.
- **Symbol-to-referent overlay** — for symbols (beasts, little horn, weeks), the symbol at center, candidate referents ringing it, confidence per tradition.
- **Timeline bands** — stacked chronologies, one band per tradition, showing where each places events.
- **Intertext graph** — Daniel passage at center, NT allusions ringing it, weight of allusion per tradition.
- **Confidence ribbon** — visual indicator next to every claim showing tier.
- **Chapter-paced narrative (Romans 3 pattern)** — the default frame.

Visual treatment varies per topic. The `data.js` schema supports multiple modalities because the axis/tradition/topic structure is flexible enough to render any of them.

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

First deliverable sibling site. Scope:

- **Passage:** Daniel 7 (Aramaic vision of four beasts, Son of Man, Ancient of Days).
- **Topics (3-5 for the pilot):**
  1. The Four Beasts / The Four Kingdoms (invokes axes A, B, L, M)
  2. The Little Horn (invokes axes A, B, C, E, F, K)
  3. The Son of Man (invokes axes J, C, N)
  4. The Saints Receiving the Kingdom (invokes axes F, H, I)
  5. Optional: The Ancient of Days (invokes axes H, I)
- **Traditions in play (5, confirmed against survey):**
  1. Reformed inaugurated amillennial (Beale, Hoekema, Vos via Beeke/Smalley, Goldingay)
  2. Dispensational premillennial pretribulational (Patterson NAC, Tanner EEC futurist elements)
  3. Historic premillennial covenantal (Ladd, Spurgeon via Beeke/Smalley)
  4. Critical-Maccabean historical (Driver CBSC, Montgomery ICC, Koester)
  5. Idealist-modified / eclectic (Beale's own, Wilcock BST implicitly)
- **Motion moments (argumentative, to be designed with codex):**
  - One structural — how the four-beast sequence maps to the two fourth-kingdom traditions.
  - One interactive — symbol-to-referent mapping on the little horn.
  - Optional third — Son-of-Man intertext animation to Rev 1, Rev 14, Mt 24.
- **Confidence tiers applied throughout.**
- **Attribution footer** listing every Logos resource with resource ID, edition, and article numbers.

## Workstream Decomposition (Parallelizable)

Each workstream can run in a separate session.

- **WS1 — Schema + Daniel 7 stub** (Claude). Lock the axis/tradition/topic schema. Populate a Daniel 7 `data.js` stub with the little-horn topic fully populated, to validate the schema against real data.
- **WS2 — Editorial charter** (Claude, codex reviews). Adapt the Romans 3 `STYLE.md` + `CLAUDE.md` to the Daniel project. Add the steelman rule, the axis vocabulary protocol, and how topic-level content maps to HTML chapters.
- **WS3 — Research tooling** (Claude). Build `steelman_query`, `citation_verifier`, `claim_extractor`, `schema_validator`. Extend `companion_tools.py`. Depends on hardening Fix 11.
- **WS4 — Design/UX exploration** (codex). Sketch per-topic visual modalities in rough HTML prototypes. Not final design; a vocabulary of moves to draw from per topic. Visual-companion browser useful here.
- **WS5 — Pilot research** (subagents per tradition, then Claude integrates). One subagent per tradition produces a steelman dossier from Logos sources. Runs after WS1-3 provide the schema, charter, and tooling. Output: `studies/daniel-7/research/steelman/*.md`.
- **WS6 — Pilot writing** (Bryan primary, Claude support). Narrative arc → dossier → layman → proofing for Daniel 7.
- **WS7 — Pilot site build** (Claude builds, codex reviews design). Renders `data.js` into the site matching the Romans 3 pattern.

## Open Decisions (must resolve before WS5 kicks off)

1. **Final traditions list for Daniel 7.** The five listed in Pilot Scope are the proposed default. Bryan ratifies.
2. **Final topic list for Daniel 7.** Five proposed; can tighten to three if scope is too big for the pilot.
3. **Per-topic visual modality.** WS4 output feeds this. No commitment until codex explores.
4. **Color protocol for multi-axis topics.** Romans 3 used one color per source (6 sources = 6 hues). A topic that invokes 5 axes with 3 positions each has up to 15 colors. Either (a) color on one primary axis per topic, other axes use neutral styling; or (b) color per tradition, not per position, giving us 5 colors total. Leaning (b); needs design review.
5. **Sibling vs. single-repo deployment.** Five sibling sites as separate repos (like Romans 3 lives separately) or one monorepo with five subdirectories. Leaning separate repos for the GitHub Pages URL discipline Bryan already uses.

## Spec Review Next Steps

Per the brainstorming workflow, this spec needs:

1. Bryan's review and approval.
2. Codex's creative review (UX, design, editorial, scope).
3. Revision based on feedback.
4. Then the plan: `docs/superpowers/plans/YYYY-MM-DD-visual-theology-daniel-7.md`.

### What Bryan Should Look For

- Does the axis/tradition/topic model fit how you teach?
- Is the steelman rule strong enough?
- Are the five proposed traditions for Daniel 7 the right cut, or are we missing a live voice (e.g., Dale Ralph Davis's mediating "antichrists/Antichrist" position as a distinct tradition)?
- Is the 5-topic pilot scope right, or should we tighten to 3?
- Is the editorial charter import from Romans 3 complete, or are there Daniel-specific rules we should add?
- Is the workstream decomposition parallelizable in practice?

### What Codex Should Look For

- Design and UX soundness for multi-tradition rendering.
- Per-topic visual-modality proposals (the current list is a starting vocabulary, not a final set).
- Editorial voice adjustments for eschatological material.
- Risks in the schema, especially for axes we didn't foreground here (canonical placement M, cross-book coherence N).
- Opportunities to reuse Romans 3's specific motion moments vs. inventing new ones.
- Whether the "multilane interstate" metaphor survives contact with actual visual design, or whether a different organizing metaphor serves the material better.

---

## Appendices

### Appendix A: The 13 Axes

Full axis catalog with positions lives in `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` §"The 13 Axes of Interpretation."

### Appendix B: Research Backbone

Full library survey: `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md`.

### Appendix C: Romans 3 Template Reference

Editorial charter, visual system, and file architecture: `/Users/family/Downloads/_push 2/STYLE.md` and `CLAUDE.md`. Content model pattern: `data.js` in same directory.

### Appendix D: Dependencies

- `docs/plans/2026-04-23-logos-reader-hardening.md` Fix 11 (cataloged-but-not-installed detection) is a prerequisite for WS3 claim verification.
- Existing companion infrastructure in `tools/workbench/` is the tooling foundation. No new Flask app needed; the visual theology sites are pure static.
