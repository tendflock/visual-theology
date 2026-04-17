# Session Handoff: Meta-Coach Live + Calibration Research Scoped

**Date:** 2026-04-17
**Status:** Meta-coach live, all 33 sermons tagged. Trend visualizations paused pending calibration research.

## What Was Done This Session

### Bug Fixes (pre meta-coach)
- Coach chat history now loads on page navigation (GET endpoint + JS fetch)
- Transcript injected into system prompt (was timing out via tool call)
- SermonAudio API auto-pagination (was capped at 100/page)
- Codex adversarial review: conversation_id validation, race guard, fallback filter fix

### Meta-Coach: 3-Layer System Built (18 tasks, 17 commits)
**Layer 1 — SRT Timestamp Preservation:**
- `srt_parser.py`: parse, validate, coarsen SRT captions (43 tests)
- Real millisecond timestamps stored in `sermons.transcript_segments`
- Canonical transcript builder keeps plain text in sync
- All 33 sermons backfilled with SRT data (26 good, 7 degraded quality)

**Layer 2 — Enriched Analysis Tagging:**
- `sermon_tagger.py`: taxonomy-controlled moment extraction via second LLM pass
- 7 dimensions, 11 section roles, 16 homiletic moves (all CHECK-constrained)
- `analysis_runs` table tracks run provenance with `is_active` versioning
- All 33 sermons tagged: 535 moments total, avg 16.2/sermon, avg confidence 0.88
- Total tagging cost: $44.06

**Layer 3 — Meta-Coach:**
- `shared_prompts.py`: HOMILETICAL_FRAMEWORK + LONGITUDINAL_POSTURE_RULE extracted
- `priority_ranker.py`: pre-computed priority ranking with 4 sub-scores
- `meta_coach_tools.py`: 11 corpus-scoped read tools
- `meta_coach_agent.py`: streaming Claude coach with tool-use loop
- `coaching_commitments` table with partial unique index (one active at a time)
- Chat widget on patterns page: "What should I work on?" + "What's improving?" buttons
- Per-sermon coach receives active commitment as coaching lens

### Cross-Navigation
- Study pages link to Sermons/Patterns; sermon pages link back to Study

### Calibration Research Scoped
- Discovered metrics are uncalibrated (LLM rates too generously — 31/33 "clear" on burden clarity)
- Bryan wants empirical verification: build a corpus of "great" sermons, compare against his own, see which metrics actually differentiate
- Full scope doc written: `docs/superpowers/ideas/2026-04-17-sermon-calibration-corpus.md`
- Searched Bryan's Logos library: found 10 volumes of "World's Great Sermons," Edwards, Whitefield, Wesley, Chrysostom, Augustine, 6 vols Puritan Sermons — all readable via LogosReader
- Trend visualizations deferred until metrics are trustworthy

### Design Artifacts
- Meta-coach spec: `docs/superpowers/specs/2026-04-16-meta-coach-design.md` (3 rounds adversarial review)
- Meta-coach plan: `docs/superpowers/plans/2026-04-16-meta-coach.md` (18 tasks)
- Calibration research scope: `docs/superpowers/ideas/2026-04-17-sermon-calibration-corpus.md`

## Outstanding Work — Ordered by Priority

### 1. FOUNDATIONAL: Empirical Sermon Calibration Research
**Scope:** `docs/superpowers/ideas/2026-04-17-sermon-calibration-corpus.md`
**Status:** Scoped, needs brainstorming session

This blocks everything else. The current analyzer metrics are uncalibrated. Before trend visualizations or analyzer improvements are trustworthy, Bryan wants to:

1. **Determine "by the numbers" which are the best sermons ever preached.** Composite scoring across multiple signals: curated list inclusion, play counts (SermonAudio/YouTube), citation frequency in homiletics literature, print run longevity, cross-references. No single signal is sufficient — need multi-signal aggregation.

2. **Build a calibration corpus.** Pull transcripts of 50+ "great" sermons from Bryan's Logos library (World's Great Sermons 10 vols, Edwards, Whitefield, Chrysostom, Wesley, Puritans) + modern great sermons from SermonAudio/YouTube. Bryan's 33 sermons are the comparison baseline.

3. **Run differential analysis.** Analyze both corpora with identical metrics. See which features actually separate great from average. Test the homileticians' claims empirically — don't assume Chapell, Robinson, or anyone else is right without data.

4. **Rebuild the analyzer rubric** based on calibrated metrics. Drop metrics that don't differentiate. Add metrics for features that DO differentiate but aren't currently measured (oral cadence, refrain detection, imagery density, memorable phrasing).

5. **Re-analyze all sermons** with the new rubric.

**Key insight from Bryan:** "I want to learn what will actually help [my congregation] the best. We need to figure out by the numbers what are the most important/best sermons ever preached."

**Resources available in Logos library:**
- The World's Great Sermons (10 vols, Kleiser) — curated corpus across history
- Jonathan Edwards' full sermon collection
- Whitefield's Selected Sermons
- Wesley's Sermons (3 vols)
- Chrysostom's Homilies (6+ vols)
- Augustine's Homilies
- 6 volumes of Puritan Sermons
- Piper's Sermons (1980-2014)
- Chapell, Beeke, Robinson homiletics textbooks (the theories to test)
- Aristotle's Rhetoric, Quintilian, Cicero (classical foundations)

**Online sources to investigate:**
- SermonAudio most-played data (API access available)
- YouTube view counts for sermon content
- Christianity Today "Greatest Sermons" lists
- Pew Research + Barna Group sermon engagement studies
- Journal of the Evangelical Homiletics Society
- Homiletic journal (McMaster Divinity)

### 2. BLOCKED: Trend Visualizations on Patterns Page
**Status:** Design paused — waiting on calibration research (#1)

Sparklines on each stat card + click-to-expand detail view. Cannot build meaningfully until the underlying metrics are trustworthy. Current data is too positive-skewed (nearly flat lines) to be useful.

### 3. ITERATIVE: Coaching Commitment Fine-Tuning
**Status:** Infrastructure built, needs iterative testing

The meta-coach can suggest experiments, the `coaching_commitments` table tracks them, and the per-sermon coach sees active commitments as a lens. But the full flow (meta-coach suggests → user confirms → per-sermon coach checks → meta-coach evaluates progress) hasn't been tested end-to-end. This should be refined through actual use over several weeks of preaching.

### 4. ONGOING: Uncommitted Work from Prior Sessions
Files modified before this session that are still uncommitted:
- `tools/workbench/companion_tools.py` — 84 lines of changes
- `tools/workbench/static/study.js` — 47 lines of changes
- `CLAUDE.md` — minor updates
- Untracked: `tools/morphgnt_cache.py`, `tools/morphgnt_data/`, `tests/test_morphgnt_cache.py` (MorphGNT Greek morphology work)

### 5. MINOR: Test Coverage Gaps
- New GET `/coach/history` endpoint untested (caught by PR review toolkit)
- SermonAudio pagination loop untested
- Full test suite can't run while dev server is up (conftest port check) — 66 new tests only verified via direct Python

## State When Stopped
- PM2 `study-companion` running with latest code
- All 33 sermons: SRT segments + reviews + 535 tagged moments
- No active coaching commitment yet
- Visual companion server was running on port 63506 (may have timed out)
- All API keys in macOS Keychain (verified)

## Commits This Session
```
38881c8 docs: scope empirical sermon calibration research project
6187671 docs: update session handoff with meta-coach completion
6171741 fix: include cost_usd in tag_sermon() return dict
3d8be68 feat: cross-navigation between Study and Sermons sections
60bfe18 feat: add meta-coach routes + chat widget to patterns page
2938d81 feat: add commitment lens to per-sermon coach system prompt
82317df feat: add meta-coach agent with streaming tool-use loop
e354d52 feat: add 11 corpus-scoped read tools for meta-coach agent
02e7ece feat: priority ranker with sub-score formulas (6 tests)
9ad6ef5 refactor: extract HOMILETICAL_FRAMEWORK + LONGITUDINAL_POSTURE_RULE to shared_prompts.py
28928a6 feat: add coaching_commitments table to companion DB schema
b63de36 fix: increase tagger max_tokens to 8192 (4096 truncated output to empty)
4e790a8 feat: add tagger LLM prompt builder + tag_sermon() entry point
edba174 feat: sermon tagger output parser with taxonomy validation (17 tests)
5087921 feat: add analysis_runs + sermon_moments tables to companion DB
1ae01ec feat: use real SRT timestamps in analyzer, add backfill-srt route
b789c90 feat: store SRT segments during ingest, add transcript_segments/quality columns
3425c60 feat: add coarsen_srt_segments to bridge SRT captions to analyzer
b76bcf0 fix: SRT validator — zero duration guard, 80% threshold, boundary tests
b03309d feat: SRT parser with validation and canonical transcript builder
eaf3a74 spec: fix 7 findings from final Codex adversarial review
abf724c spec: fix all PR review findings in meta-coach design
f69285e spec: meta-coach longitudinal coaching system design
a8eff2a plan: meta-coach implementation — 18 tasks across 3 gated layers
5ec8a51 fix: validate conversation_id on POST coach/message endpoint
4ff532d fix: coach history persistence, transcript tool timeout, API pagination
```
