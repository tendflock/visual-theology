# Meta-Coach: Longitudinal Sermon Coaching System

**Date:** 2026-04-16
**Status:** Approved
**Depends on:** Sermon Coach MVP (merged), SermonAudio sync (live)

## Overview

Three-layer system that transforms sermon analysis from per-sermon feedback into longitudinal coaching. The pastor opens the patterns page, clicks a button, and gets evidence-bounded coaching on his highest-leverage area for improvement — grounded in tagged transcript moments across the full corpus.

### Layers

1. **SRT Timestamp Preservation** — parse and store real caption timestamps at ingest
2. **Enriched Analysis Tagging** — second LLM pass producing taxonomy-controlled tagged moments
3. **Meta-Coach** — corpus-scoped streaming coach on the patterns page

---

## Layer 1: SRT Timestamp Preservation

### Problem

SermonAudio provides SRT caption files with per-line timestamps. Current ingest (`_fetch_srt_as_text()`) strips timestamps and stores plain text. The analyzer approximates positions linearly from character offsets — inaccurate because speech rate varies.

### Design

**New function:** `_parse_srt_segments(srt_text)` returns:
```python
[
    {"segment_index": 0, "start_ms": 1000, "end_ms": 4500, "text": "Welcome to..."},
    {"segment_index": 1, "start_ms": 4800, "end_ms": 9200, "text": "We'll be looking at..."},
    ...
]
```

- **Milliseconds** (integers), not float seconds — avoids comparison bugs in queries
- **segment_index** on each segment — stable anchor even after text normalization

**Storage:** New TEXT column `sermons.transcript_segments` (JSON array). New TEXT column `sermons.transcript_quality` (`'good'` | `'degraded'` | `null`).

**Canonical transcript builder:** `transcript_text` rebuilt deterministically by joining segment texts with single spaces. Plain text and segments always in sync — any excerpt from segments can be located in `transcript_text`.

**Validation pass** after parsing:
- First segment's `start_ms` < 30000 (30s) — if the SRT starts late, flag as degraded
- Monotonic timestamps (each segment's start_ms >= previous end_ms, start_ms < end_ms)
- Non-empty text ratio > 80%
- Coverage: last segment's end_ms within 10% of sermon `duration_seconds * 1000`
- If any check fails: store segments anyway, set `transcript_quality = 'degraded'`

**Backfill:** Re-fetch SRT for all existing sermons via SermonAudio API. Rebuild `transcript_text` from canonical builder. The canonical rebuild will change `transcript_hash`, triggering a full re-analysis cascade (review + tagging). Estimated one-time cost: ~$10-16 for 33 sermons ($0.15-0.25/review + $0.10-0.15/tagging). Consider using a whitespace-normalized content hash to avoid unnecessary re-review when only formatting changed. If an SRT file is no longer available for a sermon, leave `transcript_segments` null and `transcript_quality` null — the system falls back to linear approximation for that sermon.

**Downstream:** The caller (`sermon_analyzer.py`) selects the segmentation strategy: if `transcript_segments` is populated, it converts the parsed SRT segments into the format expected by downstream functions and skips `segment_transcript()`. Otherwise it falls back to the existing `segment_transcript()` linear approximation. This preserves `homiletics_core.py`'s pure-function contract (no DB access, no side effects).

### SRT Parsing Robustness

- Handle CRLF/LF variance
- Handle malformed blocks (missing index, missing timecodes)
- Handle overlapping or non-monotonic timestamps (sort and deduplicate)
- Handle non-content lines: `[Music]`, `[silence]`, blank captions
- Handle multi-line captions (join into single text)
- Handle hours > 0 in timecodes
- Explicit test suite for all of the above

---

## Layer 2: Enriched Analysis Tagging

### Problem

Current analysis produces scores and flags but lacks referenceable tagged moments — specific transcript excerpts tied to specific coaching dimensions with real timestamps. The meta-coach needs these to cite evidence.

### Design

**When it runs:** Second LLM pass, automatically dispatched after main analysis completes. Can be re-run independently.

**What the tagger sees:**
- Transcript segments (with real timestamps)
- Completed `sermon_reviews` row (scores as prior context, not ground truth)
- Primary passage (`bible_text_raw`)
- Sermon title
- Outline (if available from linked prep session)

### Taxonomy (Controlled Enums)

**`dimension_key`** (maps directly to `sermon_reviews` column names):
`burden_clarity`, `movement_clarity`, `application_specificity`, `ethos_rating`, `concreteness_score`, `christ_thread_score`, `exegetical_grounding`

**`section_role`** (where in the sermon arc):
`intro`, `setup`, `exposition`, `illustration_section`, `application`, `transition`, `recap`, `appeal`, `conclusion`, `prayer`, `reading`

Note: `illustration_section` avoids name collision with `illustration` in `homiletic_move`.

**`homiletic_move`** (what the preacher is doing):
`big_idea_statement`, `structure_signpost`, `textual_observation`, `doctrinal_claim`, `illustration`, `exhortation`, `application`, `christ_connection`, `gospel_implication`, `objection_handling`, `direct_address`, `diagnostic_question`, `pastoral_comfort`, `warning`, `summary_restatement`, `contextualization`

**`valence`:** `positive`, `negative`

**`impact`:** `minor`, `moderate`, `major` (required; applies to both valences — "major positive" = high-impact strength)

**`confidence`:** float 0.0–1.0

All taxonomy columns are validated at the schema level via CHECK constraints (see Schema section).

### Output Contract

- 0–4 moments per dimension (max 2 per valence) — do not force symmetry
- Max 18 total moments per sermon (this is the LLM's pre-suppression target)
- "Prefer fewer, higher-confidence moments over filling slots"
- Same span may be tagged under multiple dimensions when justified, but not duplicated within the same dimension and valence (enforced by unique index)
- Each moment must span a contiguous range of segment indices (all segments from `start_segment_index` through `end_segment_index` inclusive; typically 1–5 segments)
- Excerpt must be verbatim from transcript segments
- One-sentence rationale tied to taxonomy definition
- Abstain when evidence is weak or depends on audio delivery cues
- Review scores as prior context, not ground truth
- If review and transcript conflict, privilege transcript evidence and flag tension

`moment_rank` is assigned pre-suppression (the LLM's ranking). Post-processing may suppress low-confidence moments, but ranks are preserved so the meta-coach knows what was considered strongest.

### Anti-Hallucination Rules

- Excerpt must be verbatim — copy from transcript, don't paraphrase
- Don't infer audience response, emotion, or vocal tone
- Don't treat orthodox theological content as automatically effective rhetoric
- If a moment depends on pacing or inflection unavailable in text, abstain
- Prefer moments that are representative, not merely striking
- Avoid redundant adjacent moments

### Few-Shot Calibration

Prompt includes examples for:
- True positive (clear strong moment)
- True negative (clear weak moment)
- Borderline non-tag (abstention)
- Multi-dimension excerpt (model picks primary)
- Abstention case (evidence depends on delivery)

### Schema

```sql
CREATE TABLE analysis_runs (
    id TEXT PRIMARY KEY,  -- uuid4(), e.g. "a1b2c3d4-..."
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    run_type TEXT NOT NULL CHECK (run_type IN ('review', 'tagging')),
    review_run_id TEXT REFERENCES analysis_runs(id),  -- for tagging runs: which review run this was calibrated against
    prompt_version TEXT NOT NULL,
    model_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    created_at TEXT NOT NULL
);
CREATE INDEX idx_analysis_runs_sermon ON analysis_runs(sermon_id, run_type, is_active);

CREATE TABLE sermon_moments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    analysis_run_id TEXT NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    start_segment_index INTEGER NOT NULL,
    end_segment_index INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    sermon_position_pct REAL NOT NULL CHECK (sermon_position_pct >= 0.0 AND sermon_position_pct <= 1.0),
    excerpt_text TEXT NOT NULL,
    context_text TEXT,
    dimension_key TEXT NOT NULL CHECK (dimension_key IN (
        'burden_clarity', 'movement_clarity', 'application_specificity',
        'ethos_rating', 'concreteness_score', 'christ_thread_score', 'exegetical_grounding'
    )),
    section_role TEXT NOT NULL CHECK (section_role IN (
        'intro', 'setup', 'exposition', 'illustration_section', 'application',
        'transition', 'recap', 'appeal', 'conclusion', 'prayer', 'reading'
    )),
    homiletic_move TEXT CHECK (homiletic_move IS NULL OR homiletic_move IN (
        'big_idea_statement', 'structure_signpost', 'textual_observation', 'doctrinal_claim',
        'illustration', 'exhortation', 'application', 'christ_connection', 'gospel_implication',
        'objection_handling', 'direct_address', 'diagnostic_question', 'pastoral_comfort',
        'warning', 'summary_restatement', 'contextualization'
    )),
    valence TEXT NOT NULL CHECK (valence IN ('positive', 'negative')),
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    impact TEXT NOT NULL CHECK (impact IN ('minor', 'moderate', 'major')),
    moment_rank INTEGER NOT NULL,
    rationale TEXT NOT NULL,
    review_source_ref TEXT,
    prompt_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_sermon_moments_sermon_run ON sermon_moments(sermon_id, analysis_run_id);
CREATE INDEX idx_sermon_moments_dimension ON sermon_moments(sermon_id, dimension_key, valence);
CREATE INDEX idx_sermon_moments_position ON sermon_moments(sermon_id, start_segment_index, end_segment_index);
CREATE UNIQUE INDEX uq_sermon_moment_span ON sermon_moments(
    sermon_id, analysis_run_id, dimension_key, valence,
    start_segment_index, end_segment_index
);
```

**`analysis_runs.id`**: generated via `uuid4()`. Tagging runs set `review_run_id` to the active review run they were calibrated against. If a review is re-run, all tagging runs referencing the old review become stale and should be re-triggered.

**`sermon_position_pct`**: midpoint of moment as fraction of sermon duration: `min(1.0, (start_ms + end_ms) / 2 / duration_ms)`. Clamped to [0.0, 1.0] because SRT timestamps occasionally exceed reported duration.

**`moment_rank`**: rank within `(sermon_id, analysis_run_id, dimension_key, valence)` — assigned pre-suppression. Enables deterministic top-N retrieval.

**`review_source_ref`**: structured reference to the upstream review column and value this moment supports/challenges, e.g., `"burden_clarity:crisp"` or `"application_specificity:abstract"`. Format is always `"{dimension_key}:{review_value}"`.

### Re-Run Strategy

**Tagging re-run:**
- Insert new `analysis_runs` row with `run_type='tagging'`, `review_run_id` pointing to current active review
- Insert new moments under that run
- Mark prior tagging run `is_active=0`
- Keep historical runs for auditability and drift analysis
- Meta-coach queries only `is_active=1` moments

**Review re-run:** When the main review is re-run, all tagging runs referencing the old review become stale. The system automatically dispatches a new tagging pass after the new review completes. The old tagging run is marked `is_active=0` only after the new tagging run succeeds.

### Post-Processing

Post-processing runs after the LLM returns moments (pre-suppression count may be up to 18):
- Suppress moments with `confidence < 0.65` (may reduce final stored count below 18)
- Deduplicate near-identical spans (same segment range, same dimension/valence — enforced by unique index)
- Flag sermons with 15+ stored moments (post-suppression) for anomaly review — the LLM target is 18 pre-suppression, so 15+ surviving suppression indicates unusually dense evidence

### Consistency Controls

- Each dimension defined operationally with positive/negative evidence criteria in the prompt
- Abstention threshold: "If no contiguous span contains explicit evidence, return none"
- After first batch run, build a calibration gold set from 5-10 sermons
- Use 2-3 canonical examples per dimension as few-shot exemplars

---

## Layer 3: Meta-Coach

### Problem

The patterns page shows aggregate stat cards only. Bryan wants a coaching conversation that identifies his highest-leverage improvement area, cites evidence across the corpus, and assigns concrete practice experiments.

### Location & Initiation

- Chat widget on `/sermons/patterns` below existing stat cards
- Three buttons:
  1. **"What should I work on?"** — proactive priority with evidence and experiment
  2. **"What's improving?"** — reinforcement coaching (prevents deficit-only fatigue)
  3. **Free text input** — drill-down exploration
- No auto-fire on page load

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sermons/patterns/coach/message` | Stream meta-coach response (SSE) |
| `GET` | `/sermons/patterns/coach/commitment` | Get active coaching commitment |
| `POST` | `/sermons/patterns/coach/commitment` | Create/update coaching commitment |

Note: no history GET endpoint — conversations are fresh each visit. Queries for meta-coach messages use `WHERE sermon_id IS NULL AND conversation_id = ?` (not `WHERE sermon_id = ?` which would miss NULLs).

### Conversation Model

- **Fresh each visit** — no history reloaded on page open
- `conversation_id` generated as `int(time.time())` on each page load — unique per visit, monotonically increasing, no collision risk for a single-user app
- Messages persisted to `sermon_coach_messages` with `sermon_id=NULL` for auditing
- **Coach memory summary** injected into system prompt (see below for data source)

### System Prompt Assembly

`build_meta_system_prompt()` concatenates:
1. `IDENTITY_CORE` (from `voice_constants.py`)
2. `HOMILETICAL_TRADITION` (from `voice_constants.py`)
3. `VOICE_GUARDRAILS` (from `voice_constants.py`)
4. `HOMILETICAL_FRAMEWORK` (three-tier — extracted to new `shared_prompts.py`)
5. `LONGITUDINAL_POSTURE_RULE` (corpus gate — extracted to new `shared_prompts.py`)
6. **Corpus summary section** — full `get_sermon_patterns()` dict
7. **Priority ranking section** — pre-computed ranked candidates with sub-scores
8. **Coach memory summary** — derived from `coaching_commitments` table (see below)
9. **Evidence quality section** — data freshness, confidence distribution, sample sizes
10. Tool descriptions
11. Meta-coach behavioral constraints

`shared_prompts.py` is a new module (not `voice_constants.py`) because `HOMILETICAL_FRAMEWORK` and `LONGITUDINAL_POSTURE_RULE` are domain rules, not voice/identity constants. Both `sermon_coach_agent.py` and `meta_coach_agent.py` import from it.

**Coach memory summary** data source: query the last 3 `coaching_commitments` rows (any status) ordered by `created_at DESC`. Format as structured JSON:
```python
{
    "active_commitment": {"dimension": "...", "experiment": "...", "target_sermons": 2},
    "recent_commitments": [
        {"dimension": "...", "experiment": "...", "status": "superseded", "created_at": "..."},
        ...
    ],
    "progress_on_active": {  # computed from tagged moments in sermons preached after commitment
        "sermons_since": 2,
        "positive_moments_found": 1,
        "negative_moments_found": 3
    }
}
```

### Pre-Computed Priority Ranking

Python function computes ranked priorities before the LLM runs:

Per dimension, compute:
- `negative_moment_rate` — % of sermons with negative moments (confidence >= 0.65)
- `recency_weight` — last 5 sermons weighted 2x vs. older
- `trend_direction` — improving/declining/stable over last 8 sermons
- `confidence_weighted_impact` — high-confidence major moments count more

Each candidate carries sub-scores (all 0.0–1.0, higher = more urgent):
- `impact_priority_score` — weighted negative moment rate: `sum(impact_weight * confidence) / n_sermons` where impact_weight is minor=0.3, moderate=0.6, major=1.0. Measures how often high-impact negative moments appear.
- `evidence_strength_score` — `min(1.0, n_negative_moments / 10) * avg_confidence`. Rewards both quantity and quality of evidence. Capped so a dimension with 10+ negative moments gets full credit.
- `trajectory_score` — slope of negative moment rate over last 8 sermons. Positive slope (worsening) scores higher. Zero or negative slope (stable/improving) scores lower. Normalized to [0, 1].
- `actionability_score` — heuristic: 1.0 if dimension has known behavioral interventions (application_specificity, burden_clarity), 0.7 for dimensions that are partly structural (movement_clarity, ethos_rating), 0.4 for dimensions that depend on theological content (christ_thread_score, exegetical_grounding). Static mapping, not computed.
- `overall_rank` — weighted combination: `0.35 * impact + 0.25 * evidence + 0.25 * trajectory + 0.15 * actionability`. Ties broken by evidence_strength.
- `confidence_in_ranking` — absolute gap between #1 and #2 overall scores. If < 0.05, the LLM gets full freedom to choose among top 3. If > 0.15, the LLM should strongly prefer #1.

**Prompt instruction:** "Start from the top 3 ranked priorities. Choose the one that best combines ministry impact, evidence strength, and coachable next-step clarity. If you do not choose rank #1, explain why in one sentence."

### Canned Prompts

**"What should I work on?"** sends:
> Based on my sermon patterns so far, tell me the single highest-leverage thing to work on next.
> Use corpus evidence, not just averages.
> 1. Name the pattern category you see most clearly.
> 2. Cite the sermon count and moment count supporting it.
> 3. Tell me why this matters for sermon impact.
> 4. Distinguish whether this is recurring, improving, inconsistent, or possibly a one-off.
> 5. Give me one concrete practice experiment for my next 2 sermons.
> 6. If evidence is weak or mixed, say that plainly.

**"What's improving?"** sends:
> What positive patterns are emerging or strengthening in my recent sermons? Cite specific evidence and tell me what to keep reinforcing.

### Four Pattern Types

The coach must classify every pattern claim as one of:
- **Recurring weakness** — negative moments in 60%+ of recent sermons
- **Inconsistent strength** — positive moments appear but sporadically
- **Improving weakness** — was frequent, declining in recent sermons
- **One-off anomaly** — isolated to one sermon, not a pattern

### Contradictory Evidence Handling

When evidence conflicts, classify as:
- **Inconsistent execution** — some sermons strong, some weak, no trend
- **Context-dependent variation** — strong in one sermon type/series, weak in another
- **Recent improvement/regression** — historically weak, recently better (or vice versa)

Every critique paired with a counterexample when possible: "You already do this well in [sermon] — here's what was different."

### Tool Set

| Tool | Purpose |
|------|---------|
| `get_corpus_dimension_summary(filters)` | Per-dimension stats: negative rate, positive rate, trend, sermon count, median impact |
| `get_dimension_trend(dimension, filters)` | Dimension scores over time with recency weighting |
| `get_dimension_distribution(dimension, filters)` | Variance/spread — sermon-level score distribution, not just averages |
| `get_representative_moments(dimension, valence, filters, per_sermon_cap, sort)` | Top moments by dimension/valence with per-sermon cap, min confidence filter |
| `get_counterexamples(dimension, target_pattern, filters)` | Sermons where a weak dimension was unusually strong |
| `get_sermon_context(sermon_id)` | Single sermon metadata for drill-down (title, passage, date, review scores) |
| `get_sermon_moment_sequence(sermon_id, dimension)` | Moments ordered through sermon arc with position_pct, section_role, excerpts |
| `compare_periods(period_a, period_b, dimensions)` | Compare dimension stats between two date ranges |
| `get_evidence_quality(filters)` | Uncertainty: low sample size, low confidence tags, conflicting signals, missing data |
| `get_data_freshness()` | Whether tagging/analysis corpus is complete and current |
| `get_active_commitment()` | Current coaching commitment and progress evidence |

**Filter parameters** supported across tools:
- `window_days` — integer, date range in days from today (default 90)
- `min_confidence` — float, confidence floor (default 0.65)
- `per_sermon_cap` — integer, max moments per sermon in results (default 2, prevents outlier domination)
- `series` — string, filter by sermon series name
- `dimension_key` — string, filter by specific dimension (must be a valid dimension_key enum value)

**Tool-specific parameters:**
- `get_representative_moments.sort` — one of: `'confidence_desc'` (default), `'recency_desc'`, `'impact_desc'`, `'position_asc'`
- `compare_periods.period_a` / `period_b` — objects: `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}`. Example: compare last 3 months vs prior 3 months.
- `get_counterexamples.target_pattern` — one of: `'recurring_weakness'`, `'inconsistent_strength'`, `'improving_weakness'`

### Evidence Thresholds

These complement (not replace) the `LONGITUDINAL_POSTURE_RULE` from the MVP spec, which governs word choice per corpus gate. The meta-coach adds moment-based thresholds:

- No "consistently" or "always" unless 5+ sermons AND 3+ distinct moments across 3+ distinct sermons support it (both sermon count and moment count must meet threshold)
- In `pre_gate` (<5 sermons): "Too early for corpus claims. Here are areas to watch."
- In `emerging` (5-9): prefer "emerging signal" and "watch area" language. May say "emerging pattern" when 3+ of last 5 sermons share a dimension signal (per MVP spec) AND at least 2 tagged moments with confidence >= 0.75 support it.
- In `stable` (10+): full longitudinal voice. Must still cite specific sermon count and moment count.
- When evidence is thin, say so explicitly

### Behavioral Constraints

- Lead with Impact tier (Tier 1)
- Cite evidence pastorally: "across 6 of the last 8 sermons, application becomes concrete only in the closing minute" — not "application weak"
- Provide timestamps when drilling into specific sermons
- Never conflate current-sermon observation with historical pattern with trajectory
- Every critique tries to pair a counterexample (when the dimension was strong)
- Do not infer causes unless evidence supports them — name the pattern before naming the reason
- If top issue is too abstract, translate into a behavioral experiment or choose a more coachable target
- If same priority surfaced repeatedly with no change, vary the intervention — don't repeat the diagnosis

### Coaching Commitments Table

```sql
CREATE TABLE coaching_commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_key TEXT NOT NULL,
    practice_experiment TEXT NOT NULL,
    target_sermons INTEGER NOT NULL DEFAULT 2,
    baseline_sermon_id INTEGER REFERENCES sermons(id),  -- most recent sermon at time of commitment
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'superseded')),
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);
CREATE INDEX idx_coaching_commitments_active ON coaching_commitments(status);
```

- One active commitment at a time
- Behavioral, concrete, for next 1-3 sermons
- `baseline_sermon_id` anchors the commitment: "check sermons preached after this one." Query: `WHERE s.preach_date > (SELECT preach_date FROM sermons WHERE id = baseline_sermon_id)`
- Meta-coach checks if the behavior appeared in tagged moments from subsequent sermons
- Example: "In your next 2 sermons, state the concrete application before the final 20% and revisit it in the conclusion"
- When creating a new commitment, mark the old one `superseded`

### Per-Sermon Coach Integration

**Parameter change:** `build_system_prompt()` in `sermon_coach_agent.py` gains an optional parameter: `active_commitment: Optional[dict] = None`. The caller fetches the active commitment from `coaching_commitments` and passes it.

**Prompt placement:** A new "Coaching Focus" section is inserted between the pipeline findings section and the longitudinal posture rule (between items 6 and 7 in the current system prompt sequence). Format:

```
## Active Coaching Focus

Bryan is currently working on: {commitment.practice_experiment}
Dimension: {commitment.dimension_key}
Target: next {commitment.target_sermons} sermons

After your standard review, add a brief "Commitment check" section:
- Did this sermon show the target behavior?
- If yes, cite the specific moment(s). If no, note what happened instead.
- Do not let the commitment lens override your independent assessment.
```

**Behavioral rules:**
- The commitment lens is additive — it adds a section, it does not replace the standard review
- The per-sermon coach never creates or modifies commitments — only the meta-coach does
- Structured sharing only — no raw meta-coach chat history flows to the per-sermon coach

---

## Files to Create or Modify

### New Files
- `shared_prompts.py` — `HOMILETICAL_FRAMEWORK` and `LONGITUDINAL_POSTURE_RULE` extracted from `sermon_coach_agent.py`
- `meta_coach_agent.py` — system prompt assembly, streaming loop, tool dispatch
- `meta_coach_tools.py` — all meta-coach read tools (corpus summaries, distributions, moments, commitments)
- `sermon_tagger.py` — second-pass tagging LLM prompt, output parsing, post-processing
- `priority_ranker.py` — pre-computed priority ranking logic with sub-score formulas
- `templates/partials/meta_coach_chat.html` — chat widget with three buttons + free text input
- `static/meta_coach.js` — SSE client for meta-coach (conversation_id from `int(Date.now()/1000)`)
- `tests/test_meta_coach_agent.py`
- `tests/test_meta_coach_tools.py`
- `tests/test_priority_ranker.py`
- `tests/test_srt_parser.py`
- `tests/test_sermon_tagger.py`

### Modified Files
- `sermonaudio_sync.py` — add `_parse_srt_segments()`, canonical transcript builder, store segments
- `companion_db.py` — add `transcript_segments`, `transcript_quality` columns; add `analysis_runs`, `sermon_moments`, `coaching_commitments` tables with indexes
- `sermon_analyzer.py` — select segmentation strategy (SRT segments vs linear fallback), dispatch tagging pass after main review, link tagging run to review run via `review_run_id`
- `app.py` — add meta-coach routes (`POST /sermons/patterns/coach/message`, `GET/POST /sermons/patterns/coach/commitment`), update patterns route to pass commitment data
- `templates/sermons/patterns.html` — add meta-coach chat widget below stat cards
- `sermon_coach_agent.py` — import `HOMILETICAL_FRAMEWORK` and `LONGITUDINAL_POSTURE_RULE` from `shared_prompts.py`, add `active_commitment` parameter to `build_system_prompt()`, add "Coaching Focus" section

### Implementation Staging

Layer 1 must be implemented and backfill-run before Layer 2 begins. Layer 2 should be run on 5-10 sermons and manually inspected (calibration gold set) before Layer 3 begins. This is a gating requirement, not a suggestion.
