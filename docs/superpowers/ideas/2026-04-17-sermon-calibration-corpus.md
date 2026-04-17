# Research Project: Empirical Sermon Quality Calibration

**Date:** 2026-04-17
**Status:** Scoped, not yet brainstormed
**Priority:** Foundational — blocks accurate metrics, trend visualizations, and meta-coach effectiveness
**Prerequisite for:** Analyzer redesign, trend visualizations, coaching commitment calibration

## The Problem

The current sermon analyzer uses an LLM rubric to score 7 dimensions (burden clarity, movement clarity, application specificity, ethos, concreteness, Christ thread, exegetical grounding). But the metrics are uncalibrated — they produce heavily positive-skewed results (31/33 sermons score "clear" on burden clarity) because the LLM is a lenient rater with no external standard to calibrate against.

Before we can visualize trends or trust the meta-coach's priorities, we need to know: **are we measuring what actually matters, and are we measuring it accurately?**

## The Research Question

**What measurable properties of sermon transcripts actually correlate with impact, memorability, and effectiveness?**

This decomposes into two sub-questions:

### Sub-question 1: How do we identify "the best sermons ever preached"?

This is itself an empirical question. Possible signals, each with bias:

| Signal | What it measures | Bias |
|--------|-----------------|------|
| Attendance at delivery | Draw power | Favors revivals, large venues, famous preachers |
| Downloads / plays online | Modern engagement | Favors English, post-internet, platform-promoted |
| Shares / forwards | Virality | Favors controversy, emotional peaks, short clips |
| Print runs (published sermons) | Historical durability | Favors literate cultures, publishing access |
| Cross-references in other works | Scholarly influence | Favors academic/theological circles |
| Inclusion on curated "greatest" lists | Expert consensus | Favors the curators' traditions and biases |
| Citations in academic literature | Research significance | Favors analyzable, unusual, or historically pivotal sermons |
| Reported conversions / life changes | Spiritual impact | Unreliable data, hagiographic inflation |
| Historical influence (movements sparked) | Cultural impact | Conflates sermon quality with historical moment |
| Longevity (still read/listened centuries later) | Enduring value | Survivorship bias — we lost most sermons |

**No single signal is sufficient.** A multi-signal approach is needed: sermons that score high across MULTIPLE independent signals (list inclusion + citation count + longevity + play counts) are more likely to be genuinely excellent than sermons that score high on only one.

### Sub-question 2: What differentiates great sermons from average ones?

Once we have a calibration corpus (great + average), run both through identical analysis and look for which metrics separate them. Possible differential markers:

**From the homileticians' theories (to be tested, not assumed):**
- Burden clarity and single-idea focus (Robinson's "Big Idea")
- Application specificity and existential pressure (Chapell's FCF)
- Concrete imagery and memorable phrasing
- Oral design (refrains, repetition, cadence)
- Ethos / preacherly conviction
- Movement and listener-followability
- Christ-centeredness

**From the data itself (may emerge, not theorized):**
- Sentence length distribution
- Vocabulary diversity
- Question frequency
- Imperative/declarative ratio
- Image density per segment
- Repetition patterns (anaphora, epistrophe)
- Transition markers
- Direct address frequency ("you", "we")
- Temporal framing ("today", "now", "this morning")

**The experiment:** analyze 50+ "great" sermons and 50+ "average" sermons with the same pipeline. See which features actually differentiate the groups. Some theoretical markers may not hold up. Some unexpected features may emerge.

## What Bryan Wants

Bryan is a Reformed Presbyterian pastor who preaches weekly. His wife says sermons run long and are too exegetically dense. He wants to genuinely become a better preacher for the benefit of his congregation — not just build a tool.

He wants to learn: **what actually helps listeners?** Not what theorists say should help, but what the data shows actually works.

His 5 hearer-centered questions (developed through prior analysis):
1. Can the hearer follow it?
2. Can the hearer feel its claim?
3. Can the hearer picture it?
4. Can the hearer remember it?
5. Does the preacher sound personally seized by it?

## Available Resources

### In Bryan's Logos 4 Library (readable via LogosReader)
- **The World's Great Sermons** — 10 volumes (Kleiser) — curated corpus across history
- **Jonathan Edwards' Sermons** — full collection including "Sinners in the Hands of an Angry God"
- **Selected Sermons of George Whitefield**
- **Wesley's Sermons** (3 volumes of his Works)
- **Chrysostom's Homilies** — 6+ volumes (Matthew, John, Acts, Romans, Corinthians, etc.)
- **Augustine's Homilies** — on John, 1 John, Gospels
- **6 volumes of Puritan Sermons** (Nichols ed.)
- **Piper's Sermons** — 3 decades (1980-2014)
- **Princeton Sermons**
- **Chapell's Christ-Centered Preaching** (the theory to test)
- **Beeke's Reformed Preaching** (the theory to test)
- **Robinson's Art and Craft of Biblical Preaching** (the theory to test)
- **Aristotle's Rhetoric** (Greek + English)
- **Quintilian's Institutio Oratoria** (12 books, Latin + English)
- **Cicero's De Oratore, Orator** (classical rhetoric)
- **Simeon's Horae Homileticae** — 21 volumes (homiletical commentary, whole Bible)
- **Preaching Themes Dataset** (Logos dataset)

### Online Sources to Investigate
- **SermonAudio** — publishes play counts, has "most listened" data. Bryan's own account syncs via API.
- **YouTube** — play counts for famous sermons (Lockridge, Washer, Baucham, Chandler)
- **Christianity Today** — "Greatest Sermons" lists (multiple iterations)
- **Richard Lischer, "The Company of Preachers"** (Eerdmans, 2002) — scholarly anthology with critical introductions
- **Fant & Pinson, "Twenty Centuries of Great Preaching"** (13 volumes) — most comprehensive scholarly compilation
- **Pew Research** — 83% of churchgoers say sermon quality is a top factor in church selection
- **Barna Group** — studies on sermon retention (most congregants can't recall the topic by Monday)
- **Journal of the Evangelical Homiletics Society** — published rubrics and empirical studies
- **Homiletic journal** (McMaster Divinity) — academic empirical homiletics research

### Bryan's Own Corpus
- 33 sermons synced from SermonAudio (Romans series + Ecclesiastes series)
- All with SRT timestamps, reviews, and 535 tagged moments
- Real play count data available via SermonAudio API

## Empirical Findings Already Known (to verify, not assume)

From the research agent's findings:
- Listeners remember stories/illustrations at 3-6x the rate of propositional content
- Listener attention drops significantly after 15-18 minutes
- The gap between what preachers think they communicated and what listeners received is the most consistently documented phenomenon in empirical homiletics
- Listeners in all demographics rank "relevance to daily life" as their top sermon criterion
- African American congregations have higher tolerance for sermon length (45-60 min) vs. white evangelical (25-35 min)

## Proposed Approach (for next session to brainstorm)

### Phase 1: Build the calibration corpus
- Pull sermon texts from "The World's Great Sermons" (10 vols) via LogosReader
- Pull Edwards, Whitefield, Chrysostom, Wesley sermon texts
- Identify modern "great" sermons via cross-referencing: SermonAudio play counts + YouTube views + list inclusion
- Pull transcripts for modern great sermons (SermonAudio SRT, YouTube auto-captions)
- Curate 50+ "great" sermons across eras, traditions, and styles
- Bryan's 33 sermons serve as the "average" comparison corpus (not pejorative — just the baseline)

### Phase 2: Quantitative feature extraction
- Run both corpora through identical analysis
- Extract both theorized features (burden clarity, application, etc.) and emergent features (sentence length, repetition patterns, question frequency, etc.)
- Compute differential statistics: which features actually separate great from average?

### Phase 3: Build calibrated metrics
- Drop or demote metrics that don't differentiate
- Add metrics for features that DO differentiate but aren't currently measured (e.g., oral cadence/repetition, imagery density, memorable phrasing)
- Weight metrics by their predictive power
- Build a scoring rubric that's empirically grounded, not theoretically assumed

### Phase 4: Rebuild the analyzer
- New LLM rubric prompt based on calibrated metrics
- Re-analyze all 33 sermons
- Validate: do the new scores match Bryan's own intuition about which sermons were his best/worst?

### Phase 5: Trend visualizations (finally)
- Now that the metrics are trustworthy, visualize them
- Sparklines on the patterns page, click to expand
- The meta-coach cites evidence from calibrated moments

## The "By the Numbers" Question

Bryan specifically asked: how do we determine by the numbers which are the best sermons ever preached? This needs its own research design:

1. **Multi-source aggregation**: scrape/compile curated lists, cross-reference which sermons appear on 3+ independent lists
2. **Platform analytics**: SermonAudio most-played, YouTube view counts for sermon content
3. **Citation analysis**: which sermons are most referenced in other published sermons and homiletics textbooks
4. **Longevity weighting**: sermons still being read/listened to after 50+ years get bonus weight
5. **Tradition diversity**: ensure the corpus isn't all Reformed or all revivalist — include expository, narrative, prophetic, pastoral, liturgical traditions
6. **Composite score**: weight across multiple signals to produce a "confidence of greatness" score per sermon

This composite approach avoids the bias of any single signal.

## Key Decisions for Brainstorming Session

1. How large should the "great" corpus be? (50? 100? 200?)
2. Should we include non-English sermons (Chrysostom, Luther, Calvin) in translation?
3. How do we handle delivery vs. text? (Some sermons are great because of delivery that doesn't show in text)
4. Should we use Bryan's congregation's feedback as a signal? (e.g., survey after sermons)
5. How do we weight historical vs. modern sermons?
6. What's the MVP — smallest experiment that would tell us if this approach works?
