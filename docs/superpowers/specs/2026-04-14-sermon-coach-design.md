# Sermon Coach — Design Spec

**Date:** 2026-04-14
**Author:** Bryan Schneider + Claude (with adversarial review by OpenAI Codex CLI)
**Status:** Draft — pending user review
**Parent project:** Logos 4 Library + Sermon Study Companion (`tools/workbench/`)

## Problem

Bryan preps sermons in the existing 12-phase companion Monday through Saturday, preaches Sunday morning, then retrospects his delivery Monday or Tuesday. Today the retrospective is manual: he pastes his sermon transcript into an external Claude chat and asks for feedback. That feedback is context-free — it doesn't know his prep notes, outline, Christ thread, FCF, or time plan, and it doesn't know how last week's sermon ran. His wife's feedback crystallizes the gap that matters most: his sermons run long (40 min vs 25–30 target), they're too exegetically dense, and his homiletical bridge is his own known weak spot. All of those are **longitudinal patterns**, not one-off issues.

What's missing isn't another chat surface. It's a coach that:
- knows every sermon Bryan has actually preached (via SermonAudio sync),
- has deterministic metrics computed the same way every week,
- reads his prep context when a prep session is linked,
- can read deeper than the metrics when it needs to,
- tracks patterns across months,
- and stays in voice with the existing companion's Reformed, Chapell/Robinson/Beeke/Piper DNA.

## Solution

A **pipeline-first sermon coach** layered onto the existing companion. Deterministic code handles ingestion, matching, and metric extraction. A Claude Opus 4.6 coach agent reads the precomputed metrics **and** has agency to go deeper — pulling raw transcripts, full prep sessions, cross-sermon history, and recording structured overrides when it disagrees with the pipeline. Sermons auto-link to prep sessions via explicit rule tiers with a default-unlinked posture on ambiguity. All retrospection lives inside the linked study session's view; historicals and orphans live at a peer `/sermons/` surface that mirrors the same report card. Pattern tracking starts from day one via a 356-sermon historical bootstrap filtered by `speaker=Bryan Schneider AND eventType=Sunday Service`.

The architectural principle, in one line: **the pipeline is a floor, not a ceiling.** The deterministic layer is always recomputable, stable, and auditable. The LLM layer has full depth access and can override the floor with structured, rationale-bearing challenges. Disagreement is first-class data, not silent drift.

---

## Architecture

### Five layers with one direction of data flow

```
                ┌─────────────────────────────────────────────────┐
                │  SermonAudio API (external)                     │
                └──────────────────────┬──────────────────────────┘
                                       │  pulled every ~4h cron
                                       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 1 — INGEST            sermonaudio_sync.py             │
  │  - API client (api key auth)                                 │
  │  - Filter: speaker=Bryan Schneider ∩ eventType∈{Sunday       │
  │    Service} ∪ heuristic (Sunday + duration>20min)            │
  │  - Content-addressed fingerprints (transcript_hash,          │
  │    metadata_hash, source_version counter)                    │
  │  - Idempotent upsert; state machine transitions              │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 2 — MATCH             sermon_matcher.py               │
  │  - Deterministic rule tiers (Tier 1 auto, Tier 2 candidate,  │
  │    Tier 3 no row)                                            │
  │  - Pure function + transactional orchestrator (BEGIN         │
  │    IMMEDIATE)                                                │
  │  - Default UNLINKED on ambiguity                             │
  │  - Supports multi-range passages and topical exclusion       │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 3 — ANALYZE           sermon_analyzer.py              │
  │  - 8-stage pipeline, content-addressed stage cache           │
  │  - Stages 1-4 pure code; 5-7 structured LLM calls            │
  │    (claude-opus-4-6)                                         │
  │  - Per-metric provenance captured in sermon_review_provenance│
  │  - Recomputable from database alone (stable floor)           │
  │  - Calls homiletics_core.py pure functions                   │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 4 — NARRATE (COACH)   sermon_coach_agent.py           │
  │  - Streaming claude-opus-4-6, Reformed voice                 │
  │  - READS precomputed reviews AND has full read access to     │
  │    raw transcript / prep session / cross-sermon history      │
  │  - Cites Chapell, Robinson, Beeke, Piper, Greidanus, Clowney,│
  │    Goldsworthy, Mathewson via lookup_homiletics_book tool    │
  │  - OVERRIDES pipeline via sermon_overrides (structured,      │
  │    rationale-bearing, supersession chain)                    │
  │  - Voice constants shared with companion_agent.py            │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 5 — UI                app.py + templates + static     │
  │  - Review tab inside study_session.html (when linked)        │
  │  - /sermons/ blueprint — authoritative review surface for    │
  │    orphans + historicals + cross-session patterns            │
  │  - Badge fires on review_ready transitions; compare-and-set  │
  │    via ui_last_seen_version                                  │
  │  - HTMX + SSE, partials, dark theme                          │
  └─────────────────────────────────────────────────────────────┘
```

### Two durable invariants

1. **Every downstream layer is recomputable from the database alone.** If the rubric changes, re-running the analyzer updates `sermon_reviews` + `sermon_flags` without touching overrides, and trends refresh automatically. Nothing is trapped in a chat log.

2. **The coach reads everything and writes structured overrides when it disagrees.** Pipeline values are the default. Coach overrides are explicit, auditable, and survive reanalysis. Neither layer is authoritative over the other — they keep each other honest via the `effective_value = latest_active_override ?? latest_pipeline_value` rule.

### Module ownership

| Module | Responsibility | Touches |
|---|---|---|
| `sermonaudio_sync.py` | Ingest + classify + upsert | `sermons`, `sermon_passages`, `sermon_sync_log`, `sermon_sync_checkpoint`, `sync_lock`, `event_type_classification` |
| `sermon_matcher.py` | Deterministic session matching | `sermon_links`, reads `sermons`+`sessions` |
| `sermon_analyzer.py` | Pipeline computation (stages 1-8) | `sermon_reviews`, `sermon_flags`, `sermon_analysis_cache`, `sermon_review_provenance`, `sermon_review_history`, `sermon_analysis_cost_log` |
| `sermon_coach_agent.py` | Conversational coach | `sermon_coach_messages`, `sermon_overrides`, reads everything |
| `homiletics_core.py` | Pure homiletical rules (FORM, Christ thread, density, "so what" gate, time estimator) | Imported by analyzer + coach; no DB access |
| `voice_constants.py` | Shared voice DNA | Imported by companion_agent + coach_agent |
| `app.py` (extended) | Flask routes, APScheduler setup | All new routes |

Existing code **untouched**: `study.py`, `logos_batch.py`, LogosReader C# layer, `libSinaiInterop.dylib`, `companion_agent.py`'s prep phases, and the existing prep-side routes. `companion_db.py` grows new tables and two writer touches (`save_card_response`, `save_message` for homiletical phases) that maintain `sessions.last_homiletical_activity_at`.

---

## Data Model

All new tables added to `companion_db.py`. No changes to existing tables except adding `last_homiletical_activity_at` to `sessions`.

### Primary entity: `sermons`

```sql
CREATE TABLE sermons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermonaudio_id TEXT UNIQUE NOT NULL,

    -- Identity
    broadcaster_id TEXT NOT NULL,
    title TEXT NOT NULL,
    speaker_name TEXT,
    event_type TEXT,
    series TEXT,
    preach_date TEXT,
    preach_date_source TEXT DEFAULT 'sermonaudio'
        CHECK (preach_date_source IN ('sermonaudio','manual','inferred')),
    publish_date TEXT,
    duration_seconds INTEGER,

    -- Passage (primary; secondaries in sermon_passages)
    bible_text_raw TEXT,
    book INTEGER,
    chapter INTEGER,
    verse_start INTEGER,
    verse_end INTEGER,

    -- Content
    audio_url TEXT,
    transcript_text TEXT,
    transcript_source TEXT DEFAULT 'sermonaudio',
    transcript_quality TEXT CHECK (transcript_quality IN
        ('full','partial','low_confidence','unavailable')),

    -- Classification (see §3 Ingest)
    sermon_type TEXT NOT NULL DEFAULT 'expository'
        CHECK (sermon_type IN ('expository','topical')),
    classified_as TEXT NOT NULL
        CHECK (classified_as IN ('sermon','skipped')),
    classification_reason TEXT,
    sermon_aim TEXT,   -- manual disambiguation for same-passage sermons

    -- Source fingerprinting (content-addressed recomputability)
    metadata_hash TEXT,
    transcript_hash TEXT,
    source_version INTEGER NOT NULL DEFAULT 1,
    remote_updated_at TEXT,

    -- State
    sync_status TEXT NOT NULL DEFAULT 'pending_sync',
    sync_error TEXT,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_failure_at TEXT,
    last_state_change_at TEXT NOT NULL,
    last_match_attempt_at TEXT,
    match_status TEXT NOT NULL DEFAULT 'unmatched'
        CHECK (match_status IN (
            'unmatched','matched','awaiting_candidates',
            'unparseable_passage','topical_no_match','rejected_all'
        )),

    -- Tombstones
    deleted_at TEXT,
    is_remote_deleted INTEGER NOT NULL DEFAULT 0,

    -- Lease for in-flight analysis
    analysis_lease_expires_at TEXT,

    -- UI state
    ui_last_seen_version INTEGER NOT NULL DEFAULT 0,

    first_synced_at TEXT NOT NULL,
    last_synced_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_sermons_sermonaudio_id ON sermons(sermonaudio_id);
CREATE INDEX idx_sermons_preach_date ON sermons(preach_date DESC);
CREATE INDEX idx_sermons_sync_status ON sermons(sync_status);
CREATE INDEX idx_sermons_classified ON sermons(classified_as);
CREATE INDEX idx_sermons_match_status ON sermons(match_status);
CREATE INDEX idx_sermons_book_chapter ON sermons(book, chapter);
```

### `sermon_passages` — multi-range passages per sermon

```sql
CREATE TABLE sermon_passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    book INTEGER NOT NULL,
    chapter_start INTEGER NOT NULL,
    verse_start INTEGER,              -- NULL = verse 1
    chapter_end INTEGER NOT NULL,
    verse_end INTEGER,                -- NULL = end of chapter
    raw_text TEXT,                    -- audit
    created_at TEXT NOT NULL,
    UNIQUE(sermon_id, rank)
);
CREATE INDEX idx_sermon_passages_sermon ON sermon_passages(sermon_id);
CREATE INDEX idx_sermon_passages_lookup ON sermon_passages(book, chapter_start);
```

Primary passage (rank 1) is also denormalized on `sermons` for cheap single-lookup filters.

### `sermon_links` — matched sessions with lifecycle

```sql
CREATE TABLE sermon_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    link_status TEXT NOT NULL
        CHECK (link_status IN ('active','candidate','superseded','rejected')),
    link_source TEXT NOT NULL
        CHECK (link_source IN ('auto','manual')),
    confidence REAL,                  -- debug breadcrumb, not a gate
    match_reason TEXT NOT NULL,
    superseded_at TEXT,
    superseded_by_link_id INTEGER REFERENCES sermon_links(id),
    superseded_reason TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(sermon_id, session_id)
);
CREATE UNIQUE INDEX idx_sermon_links_one_active
    ON sermon_links(sermon_id) WHERE link_status = 'active';
CREATE INDEX idx_sermon_links_sermon ON sermon_links(sermon_id);
CREATE INDEX idx_sermon_links_session ON sermon_links(session_id);
```

### `sermon_reviews` — deterministic per-sermon metrics

```sql
CREATE TABLE sermon_reviews (
    sermon_id INTEGER PRIMARY KEY REFERENCES sermons(id),
    analyzer_version TEXT NOT NULL,
    homiletics_core_version TEXT NOT NULL,
    model_version TEXT,

    -- Version fingerprint of the inputs this review was computed against
    analyzed_transcript_hash TEXT,
    source_version_at_analysis INTEGER NOT NULL,

    -- Length & timing
    actual_duration_seconds INTEGER NOT NULL,
    planned_duration_seconds INTEGER,
    duration_delta_seconds INTEGER,
    section_timings TEXT,

    -- Bridge & Christ thread
    bridge_score TEXT CHECK (bridge_score IN ('landed','partial','missed')),
    bridge_evidence TEXT,
    christ_thread_score TEXT CHECK (christ_thread_score IN
        ('explicit','gestured','absent')),
    christ_thread_evidence TEXT,

    -- Density & delivery
    density_score INTEGER CHECK (density_score BETWEEN 1 AND 5),
    density_per_section TEXT,
    jargon_density INTEGER,
    application_concreteness INTEGER CHECK (application_concreteness BETWEEN 1 AND 5),

    -- Structural fidelity (null if unlinked)
    outline_coverage_pct REAL,
    outline_additions TEXT,
    outline_omissions TEXT,

    -- Summary fields
    top_encouragements TEXT,
    top_concerns TEXT,

    computed_at TEXT NOT NULL
);
```

One row per sermon. Re-running the analyzer **overwrites** this row (bumping `analyzer_version` and `source_version_at_analysis`) and **preserves** `sermon_overrides`.

### `sermon_review_history` — append-only snapshots

```sql
CREATE TABLE sermon_review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    review_snapshot_json TEXT NOT NULL,      -- full sermon_reviews row serialized
    analyzer_version TEXT NOT NULL,
    homiletics_core_version TEXT NOT NULL,
    source_version_at_analysis INTEGER NOT NULL,
    archived_at TEXT NOT NULL
);
CREATE INDEX idx_review_history_sermon ON sermon_review_history(sermon_id, archived_at DESC);
```

Populated on each `sermon_reviews` overwrite. Not for runtime; for debugging rubric drift.

### `sermon_flags` — per-moment findings

```sql
CREATE TABLE sermon_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    target_key TEXT NOT NULL,              -- content-hash of flag type+location for override stability
    flag_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info','note','warn','concern')),
    transcript_start_sec INTEGER,
    transcript_end_sec INTEGER,
    section_label TEXT,
    excerpt TEXT,
    rationale TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    homiletics_core_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_sermon_flags_sermon ON sermon_flags(sermon_id);
CREATE INDEX idx_sermon_flags_target_key ON sermon_flags(target_key);
```

Flags are deleted + reinserted per sermon on reanalysis. Overrides reference flags by `target_key` (content-based) so they survive the delete/reinsert cycle.

### `sermon_overrides` — coach/user challenges to pipeline

```sql
CREATE TABLE sermon_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    target_table TEXT NOT NULL CHECK (target_table IN ('sermon_reviews','sermon_flags')),
    target_key TEXT NOT NULL,              -- column name for reviews; content-hash for flags
    pipeline_value TEXT,
    coach_value TEXT NOT NULL,
    rationale TEXT NOT NULL,
    authored_by TEXT NOT NULL DEFAULT 'coach' CHECK (authored_by IN ('coach','user')),
    supersedes_override_id INTEGER REFERENCES sermon_overrides(id),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_overrides_sermon_target
    ON sermon_overrides(sermon_id, target_key, is_active);
```

Override chain: a new override on the same `(sermon_id, target_key)` sets its predecessor's `is_active=0` and records `supersedes_override_id` on the new row. Read-time composition:

```sql
SELECT coach_value FROM sermon_overrides
WHERE sermon_id = ? AND target_key = ? AND is_active = 1
ORDER BY created_at DESC LIMIT 1
```

### `sermon_effective_review` — composed view

```sql
CREATE VIEW sermon_effective_review AS
SELECT
    sr.sermon_id,
    sr.analyzer_version,
    sr.homiletics_core_version,
    sr.model_version,
    sr.analyzed_transcript_hash,
    sr.source_version_at_analysis,
    sr.actual_duration_seconds,
    sr.planned_duration_seconds,
    sr.duration_delta_seconds,
    sr.section_timings,
    COALESCE(
        (SELECT json_extract(coach_value, '$') FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'bridge_score'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.bridge_score
    ) AS effective_bridge_score,
    sr.bridge_score AS pipeline_bridge_score,
    sr.bridge_evidence,
    COALESCE(
        (SELECT json_extract(coach_value, '$') FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'christ_thread_score'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.christ_thread_score
    ) AS effective_christ_thread_score,
    sr.christ_thread_score AS pipeline_christ_thread_score,
    sr.christ_thread_evidence,
    COALESCE(
        (SELECT CAST(json_extract(coach_value, '$') AS INTEGER) FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'density_score'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.density_score
    ) AS effective_density_score,
    sr.density_score AS pipeline_density_score,
    sr.density_per_section,
    sr.jargon_density,
    COALESCE(
        (SELECT CAST(json_extract(coach_value, '$') AS INTEGER) FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'application_concreteness'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.application_concreteness
    ) AS effective_application_concreteness,
    sr.application_concreteness AS pipeline_application_concreteness,
    COALESCE(
        (SELECT CAST(json_extract(coach_value, '$') AS REAL) FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'outline_coverage_pct'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.outline_coverage_pct
    ) AS effective_outline_coverage_pct,
    sr.outline_coverage_pct AS pipeline_outline_coverage_pct,
    sr.outline_additions,
    sr.outline_omissions,
    COALESCE(
        (SELECT coach_value FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'top_encouragements'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.top_encouragements
    ) AS effective_top_encouragements,
    sr.top_encouragements AS pipeline_top_encouragements,
    COALESCE(
        (SELECT coach_value FROM sermon_overrides so
         WHERE so.sermon_id = sr.sermon_id AND so.target_key = 'top_concerns'
           AND so.is_active = 1 ORDER BY so.created_at DESC LIMIT 1),
        sr.top_concerns
    ) AS effective_top_concerns,
    sr.top_concerns AS pipeline_top_concerns,
    sr.computed_at
FROM sermon_reviews sr;
```

**Override-eligible metrics** (the target_keys the coach can override): `bridge_score`, `christ_thread_score`, `density_score`, `application_concreteness`, `outline_coverage_pct`, `jargon_density`, `top_encouragements`, `top_concerns`, plus per-flag overrides via content-based target_keys (`flag:<hash>`). Non-override-eligible metrics (e.g., `duration_delta_seconds`) are mechanical — the coach can narrate them but the view exposes the pipeline value as-is.

UI renders from this view. Pattern queries read from this view. Trend aggregates read from this view. **Both pipeline and effective values are exposed** so the UI can render "pipeline says X, coach overrode to Y" side-by-side.

### `sermon_review_provenance` — per-metric source tracking

```sql
CREATE TABLE sermon_review_provenance (
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    target_key TEXT NOT NULL,                -- 'bridge_score', 'christ_thread_score', etc.
    source TEXT NOT NULL CHECK (source IN ('pure_code','llm','override','default')),
    stage_name TEXT,
    input_hash TEXT,
    model_version TEXT,
    homiletics_core_version TEXT,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (sermon_id, target_key)
);
```

One row per `(sermon, metric)`. Overwritten on each analysis (except override-source rows, which come from the override table's composition logic). Powers the UI's provenance popover — click an info icon next to any metric and see "computed by pipeline stage 5, LLM call at 11:23, input_hash abc123…, source_version 3, or overridden by coach with rationale Z."

### `sermon_coach_messages`

```sql
CREATE TABLE sermon_coach_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER REFERENCES sermons(id),     -- NULL for cross-session /coach
    session_id INTEGER REFERENCES sessions(id),
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user','assistant','tool','tool_result')),
    content TEXT,
    tool_name TEXT,
    tool_input TEXT,
    tool_result TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_coach_messages_sermon ON sermon_coach_messages(sermon_id);
CREATE INDEX idx_coach_messages_session ON sermon_coach_messages(session_id);
CREATE INDEX idx_coach_messages_conv ON sermon_coach_messages(conversation_id);
```

### `sermon_analysis_cache` — content-addressed stage cache

```sql
CREATE TABLE sermon_analysis_cache (
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_json TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    homiletics_core_version TEXT NOT NULL,
    model_version TEXT,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (sermon_id, stage, input_hash)
);
CREATE INDEX idx_analysis_cache_lookup ON sermon_analysis_cache(sermon_id, stage);
```

Each stage hashes ALL its inputs (transcript, outline snapshot, prior stage outputs, rubric version, prompt version, model version) into `input_hash`. Cache hit = exact input match. Cache miss = recompute. Upstream input change cascades via hash mismatch. Version snapshot taken at analysis-run start and held constant for the whole run.

### `sermon_analysis_cost_log`

```sql
CREATE TABLE sermon_analysis_cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    stage TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    estimated_cost_usd REAL NOT NULL,
    called_at TEXT NOT NULL
);
CREATE INDEX idx_cost_log_sermon ON sermon_analysis_cost_log(sermon_id);
CREATE INDEX idx_cost_log_called ON sermon_analysis_cost_log(called_at DESC);
```

### `sermon_sync_log` + `sermon_sync_checkpoint` + `sync_lock`

```sql
CREATE TABLE sermon_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    trigger TEXT NOT NULL CHECK (trigger IN ('cron','manual','deep_sweep','bootstrap')),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    sermons_fetched INTEGER DEFAULT 0,
    sermons_new INTEGER DEFAULT 0,
    sermons_updated INTEGER DEFAULT 0,
    sermons_noop INTEGER DEFAULT 0,
    sermons_skipped INTEGER DEFAULT 0,
    sermons_failed INTEGER DEFAULT 0,
    error_summary TEXT,
    status TEXT NOT NULL CHECK (status IN ('running','completed','failed'))
);

CREATE TABLE sermon_sync_checkpoint (
    name TEXT PRIMARY KEY,
    phase TEXT,
    last_page_processed INTEGER,
    last_sermonaudio_id_processed TEXT,
    total_pages INTEGER,
    total_sermons_expected INTEGER,
    started_at TEXT,
    last_progress_at TEXT,
    completed_at TEXT
);

CREATE TABLE sync_lock (
    name TEXT PRIMARY KEY,
    held_by TEXT,
    acquired_at TEXT,
    lease_expires_at TEXT,
    last_heartbeat_at TEXT
);
INSERT OR IGNORE INTO sync_lock (name) VALUES ('steady_state'), ('bootstrap');
```

### `event_type_classification` + `sermon_settings`

```sql
CREATE TABLE event_type_classification (
    event_type TEXT PRIMARY KEY,
    classification TEXT NOT NULL CHECK (classification IN ('sermon','devotional','ignore')),
    classified_by TEXT DEFAULT 'user' CHECK (classified_by IN ('user','seed','heuristic_promoted')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Seeds
INSERT INTO event_type_classification (event_type, classification, classified_by, created_at, updated_at)
VALUES
    ('Sunday Service', 'sermon', 'seed', datetime('now'), datetime('now')),
    ('Devotional', 'devotional', 'seed', datetime('now'), datetime('now')),
    ('Daily Devotional', 'devotional', 'seed', datetime('now'), datetime('now'));

CREATE TABLE sermon_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Seeds
INSERT INTO sermon_settings (key, value, updated_at) VALUES
    ('bryan_speaker_name', 'Bryan Schneider', datetime('now')),
    ('matcher_tier1_days', '7', datetime('now')),
    ('matcher_tier2_days', '14', datetime('now')),
    ('matcher_cutoff_days', '30', datetime('now')),
    ('cron_interval_hours', '4', datetime('now')),
    ('analysis_transcript_min_words', '1000', datetime('now')),
    ('coach_model', 'claude-opus-4-6', datetime('now')),
    ('analyzer_model', 'claude-opus-4-6', datetime('now'));
```

### `sessions` — one column added

```sql
ALTER TABLE sessions ADD COLUMN last_homiletical_activity_at TEXT;
```

Maintained by `save_card_response` and `save_message` in `companion_db.py` **only when the phase is in the homiletical set** (`exegetical_point`, `fcf_homiletical`, `sermon_construction`, `edit_pray`). Every homiletical write touches two rows: the card/message write AND this timestamp bump.

### `sermon_trends_recent` — view for aggregates

```sql
CREATE VIEW sermon_trends_recent AS
SELECT
    COUNT(*) AS n_sermons,
    AVG(ser.duration_delta_seconds) AS avg_duration_delta,
    1.0 * SUM(CASE WHEN ser.effective_bridge_score='landed' THEN 1 ELSE 0 END) / COUNT(*) AS bridge_landed_rate,
    1.0 * SUM(CASE WHEN ser.effective_christ_thread_score='explicit' THEN 1 ELSE 0 END) / COUNT(*) AS christ_explicit_rate,
    AVG(ser.density_score) AS avg_density,
    AVG(ser.outline_coverage_pct) AS avg_outline_coverage
FROM sermon_effective_review ser
JOIN sermons s ON s.id = ser.sermon_id
WHERE s.preach_date >= date('now', '-60 days')
  AND s.classified_as = 'sermon'
  AND s.is_remote_deleted = 0;
```

Pattern queries and trend cards read from this view. Always fresh, always respects overrides.

---

## Section 3 — Ingest (`sermonaudio_sync.py`)

### 3.1 API client

- Library: `sermonaudio` PyPI package, added to requirements.
- Auth: API key from `.env` as `SERMONAUDIO_API_KEY` + `SERMONAUDIO_BROADCASTER_ID`.
- Transport: serial requests, exponential backoff on 429/5xx (1s → 2s → 4s), 30s per-request timeout, max 3 retries per request.
- Total run budget: 10 min for steady state, unbounded for bootstrap (lease-heartbeat protects against stuck processes).

### 3.2 Classification (AND filter: speaker ∩ event type)

```python
def classify(sermon_remote, settings, classifications) -> tuple[str, str]:
    speaker = (sermon_remote.speaker_name or '').strip()
    event_type = (sermon_remote.event_type or '').strip()
    bryan_name = settings['bryan_speaker_name']

    # Hard gate: only Bryan's sermons enter the pipeline
    if speaker != bryan_name:
        return ('skipped', f'speaker={speaker!r}')

    # Event type via runtime table
    row = classifications.get(event_type)
    if row and row['classification'] == 'sermon':
        return ('sermon', f'eventType={event_type}')
    if row and row['classification'] in ('devotional', 'ignore'):
        return ('skipped', f'eventType={event_type}')

    # Heuristic safety net: Sunday + duration
    pdate = sermon_remote.preach_date
    dur_min = (sermon_remote.duration_seconds or 0) / 60
    if pdate and pdate.weekday() == 6 and dur_min > 20:
        return ('sermon', f'heuristic: Sunday + {int(dur_min)}min')

    return ('skipped', f'eventType={event_type!r} (unknown)')
```

Unknown event types surface in `/sermons/classification-review` for one-click approval into `event_type_classification`. Until approved, they rely on the heuristic (which catches Bryan's Sunday Services with high reliability per his account pattern).

### 3.3 Idempotent upsert + source fingerprinting

- `metadata_hash` = sha256 over {title, event_type, series, preach_date, bible_text_raw, duration_seconds, remote_updated_at}.
- `transcript_hash` = sha256 over transcript (or NULL if not yet available).
- Upsert keyed on `sermonaudio_id`. On hash unchanged → touch `last_synced_at` only. On hash changed → bump `source_version`, update hashes, transition `sync_status` via `CASE` (recycle back to `analysis_pending` if already past that stage).
- Every source change triggers downstream reanalysis via the stale-check rule (`sermons.source_version > sermon_reviews.source_version_at_analysis`).

### 3.4 State machine (full transitions)

```
                          ┌─────────────────┐
                          │  pending_sync   │◄───────────── retry cooldown (SQL-enforced)
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
          ┌─────────────────┐           ┌─────────────────┐
          │ synced_metadata │           │ sync_failed     │
          └────────┬────────┘           └────────┬────────┘
                   │                             │
        ┌──────────┴─┐                           │ cooldown (1h→4h→16h→64h)
        ▼            ▼                           │
┌───────────────┐ ┌──────────────────┐           ▼
│ transcript_   │ │transcript_stalled│    ┌──────────────────┐
│   ready       │ │  (48h timeout)    │    │permanent_failure │
└───────┬───────┘ └────────┬──────────┘    └──────────────────┘
        │                  │
        │                  └────► transcript arrives → transcript_ready
        ▼
┌─────────────────┐
│analysis_pending │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     crash + lease expiry
│analysis_running │─────────┐
└────────┬────────┘         │
         │                  ▼
         ▼           ┌──────────────────┐
┌─────────────────┐  │ analysis_failed  │
│  review_ready   │  └────────┬─────────┘
└─────────────────┘           │
   │    ▲   │                 │ retry
   │    │   │                 ▼
   │    │   └──► archived (user)
   │    │
   │    └── re-enter on source_version bump or rubric bump
   │
   └──► badge fires if source_version > ui_last_seen_version
```

Retry cooldown is SQL-enforced in the sync query, keyed on `failure_count`:

```sql
SELECT id FROM sermons
WHERE sync_status = 'sync_failed'
  AND (last_failure_at IS NULL OR last_failure_at < datetime('now', '-' ||
        CASE failure_count
            WHEN 0 THEN '1 hours'
            WHEN 1 THEN '4 hours'
            WHEN 2 THEN '16 hours'
            ELSE '64 hours'
        END));
```

### 3.5 Pagination

**Bootstrap mode** (one-shot, manual trigger `/sermons/bootstrap`):
- Paginate 100 per page via the library's pagination.
- Persist every row (including skipped ones) for audit.
- Commit a `sermon_sync_checkpoint` update every 5 pages (`phase='paginating'`, `last_page_processed`, `last_sermonaudio_id_processed`).
- If process crashes, next run of bootstrap reads the checkpoint and resumes from `last_page_processed + 1`.
- Completion sets `phase='completed'` and `completed_at`; re-triggering is a no-op unless the user explicitly forces a re-bootstrap.

**Steady-state mode** (every 4h cron or manual):
- Primary filter: `updated_since=last_successful_sync_at - 1 day` via the library's server-side filter.
- Fallback: client-side filter on a wider `publish_date` window (90 days) comparing `remote_updated_at` against stored value.
- Deep sweep: weekly Sunday-night cron (separate APScheduler job) pulls last 180 days by `publish_date` and diffs `remote_updated_at` against stored — catches anything the primary filter missed.

### 3.6 Concurrency — lease-based lock

```sql
-- Acquisition (atomic):
UPDATE sync_lock
SET held_by = :run_id,
    acquired_at = datetime('now'),
    lease_expires_at = datetime('now', '+90 seconds'),
    last_heartbeat_at = datetime('now')
WHERE name = :lock_name
  AND (held_by IS NULL OR lease_expires_at < datetime('now'));
```

If `cursor.rowcount == 1`, the run holds the lock. Otherwise, return HTTP 409 to manual callers / abort silently for cron.

Heartbeat thread extends the lease every 30s during active runs. Process death → lease expires in ≤90s → next run acquires cleanly.

Separate lock names for `steady_state` and `bootstrap`; they don't block each other. Idempotent upsert protects the rare concurrent-touch case.

### 3.7 Cron + manual trigger

- **Cron**: APScheduler `BackgroundScheduler` inside the Flask app, `IntervalTrigger(hours=settings.cron_interval_hours)`. Starts on Flask app boot, shuts down on app teardown.
- **Weekly deep sweep**: `CronTrigger(day_of_week='sun', hour=22)` — runs Sunday 10 PM local, pulls last 180 days by `publish_date`.
- **Manual**: `POST /sermons/sync` endpoint returns `run_id` immediately; UI polls `GET /sermons/sync-log/<run_id>`. `POST /sermons/bootstrap` kicks off a bootstrap run.

### 3.8 Error classification (full matrix)

| Error | Classification | Action |
|---|---|---|
| HTTP 429 | Transient | Backoff, retry up to 3× within this run |
| HTTP 5xx | Transient | Backoff, retry up to 3× |
| Network timeout | Transient | Retry 3×; then mark sermon `sync_failed` |
| HTTP 401 | Fatal-run | Abort, alert in `/sermons/sync-log` |
| HTTP 403 | Fatal-run | Abort, alert in `/sermons/sync-log` |
| HTTP 404 on detail fetch | Fatal-per-sermon | Mark `is_remote_deleted=1`, `deleted_at=now` |
| JSON parse error | Fatal-per-sermon | Mark `sync_failed`, stacktrace in `sync_error`, increment `failure_count` |
| Lock contention | Operational | Return 409 (manual); abort silently (cron) |

---

## Section 4 — Matcher (`sermon_matcher.py`)

### 4.1 Rule tiers

**Tier 1 — auto-link as `active`.** All must hold:

1. **Passage match**: ANY `sermon_passages` row overlaps the session's `(book, chapter, verse_start, verse_end)` exactly (whole-chapter spans treated as covering the chapter).
2. **Prep timing is realistic**: session's `last_homiletical_activity_at` is within `matcher_tier1_days` (default 7) before `preach_date`.
3. **Session created before preach**: `session.created_at < sermon.preach_date`.
4. **Exactly one session qualifies.** Ambiguity demotes to Tier 2.
5. **No prior `rejected` link** between this sermon and the matching session.
6. **`sermon_type = 'expository'`** — topical sermons skip matcher entirely.

→ Writes one `sermon_links` row with `link_status='active'`, `link_source='auto'`, `match_reason='tier1:exact+timing'`.

**Tier 2 — surface as `candidate`.** Any one of:

- Passage overlap but not exact (partial verse range mismatch).
- Loose timing: `last_homiletical_activity_at` is 7–14 days (or 7–30 for long-lead) before `preach_date`.
- Multiple Tier 1 qualifiers (ambiguity).
- Session matches passage + timing but never reached a homiletical phase.

→ Writes one `sermon_links` row **per candidate** with `link_status='candidate'`. UI shows all, one-click approval flips selected to `active` and supersedes any existing active auto-link.

**Tier 3 — no row.** No overlap, `session.created_at > sermon.preach_date`, or beyond `matcher_cutoff_days` (default 30).

### 4.2 Pure function

```python
def match_sermon_to_sessions(
    sermon: SermonInfo,
    sessions: tuple[SessionInfo, ...],
    existing_links: tuple[SermonLink, ...],
    rejected_session_ids: frozenset[int],
    settings: MatcherSettings,
) -> MatchDecision:
    """Deterministic, testable in isolation. No SQL."""
```

Orchestrator wraps in `BEGIN IMMEDIATE` transaction to prevent read/decide/write races against UI rejections.

### 4.3 Triggers

- Sermon → `transcript_ready` or `synced_metadata` with parseable passage.
- `source_version` bump on the sermon.
- `sessions.last_homiletical_activity_at` bump on a session with a matching-passage unlinked sermon within `matcher_cutoff_days`.
- Manual "re-match" button per sermon.
- Manual link via UI dropdown (creates `active`+`manual`).
- Manual unlink → `rejected` (remembered).

Short-circuit filters on session-update rematch sweeps:

```sql
WHERE s.preach_date BETWEEN :session_created_at
                        AND date(:session_created_at, '+' || :cutoff_days || ' days')
  AND (s.last_match_attempt_at IS NULL
       OR s.last_match_attempt_at < :session_last_homiletical_activity_at)
  AND s.sermon_type = 'expository'
  AND s.match_status NOT IN ('matched','rejected_all')
```

### 4.4 Pattern filter (used everywhere pattern data is consumed)

```sql
WHERE link_status = 'active'
```

That's it. `link_source` is stored for audit; `confidence` is debug metadata, not a gate.

### 4.5 Passage parsing

`parse_reference()` in `tools/study.py` is extended to handle:

- Multi-range: `"Romans 8:1-11; Romans 9:1-5"` → two `sermon_passages` rows
- Chapter spans: `"Psalm 1-2"` → one row `(chapter_start=1, verse_start=NULL, chapter_end=2, verse_end=NULL)`
- Whole chapters: `"Romans 8"` → one row `(chapter_start=8, verse_start=NULL, chapter_end=8, verse_end=NULL)`
- Unparseable: zero rows, `match_status='unparseable_passage'`, surfaces in attention queue.

### 4.6 Existing active link behavior

- **Still Tier 1, no better candidate**: no-op.
- **Better auto candidate emerges**: existing `active` auto-link → `superseded`, new → `active`. UI banner: *"Relinked from Session #42 to Session #87. [Revert]"*
- **Existing link is manual**: never auto-superseded. New matches surface only as `candidate` rows.

---

## Section 5 — Analyzer (`sermon_analyzer.py`)

### 5.1 Eight-stage pipeline

```
(inputs: transcript_text, sermon_passages, linked outline, settings, version snapshot)

[1] segment_transcript()       — pure, timing/marker-based segmentation
[2] align_with_outline()       — pure, outline-to-segment alignment if linked
[3] compute_timing_metrics()   — pure, durations and delta vs plan
[4] compute_density_metrics()  — pure, Greek/Hebrew/jargon density
[5] score_bridge()             — LLM (claude-opus-4-6), structured JSON
[6] score_christ_thread()      — LLM, structured JSON
[7] extract_flags()            — LLM, list of structured flag records
[8] summarize_review()         — pure, top 3 encouragements + concerns from flags

(outputs: sermon_reviews row, sermon_flags rows, sermon_review_provenance rows)
```

### 5.2 Content-addressed stage cache

Every stage's `input_hash` is computed over **all** its inputs:

```python
stage_1_input_hash = sha256(transcript_text + segmentation_algo_version)
stage_2_input_hash = sha256(stage_1_output_hash + linked_outline_snapshot_hash + align_algo_version)
stage_3_input_hash = sha256(stage_2_output_hash + timing_algo_version)
stage_4_input_hash = sha256(stage_1_output_hash + density_algo_version)
stage_5_input_hash = sha256(stage_2_output_hash + prep_session_snapshot_hash + bridge_prompt_version + homiletics_core_version + model_version)
stage_6_input_hash = sha256(stage_2_output_hash + prep_session_snapshot_hash + christ_prompt_version + homiletics_core_version + model_version)
stage_7_input_hash = sha256(stage_2_output_hash + stage_3_output_hash + stage_4_output_hash + flags_prompt_version + homiletics_core_version + model_version)
stage_8_input_hash = sha256(stage_7_output_hash + summary_algo_version)
```

Cache lookup: `SELECT output_json FROM sermon_analysis_cache WHERE sermon_id=? AND stage=? AND input_hash=?`. Hit → reuse. Miss → compute + insert.

Any upstream input change cascades automatically: upstream cache miss → new output hash → downstream input hash changes → downstream cache miss. No dependency graph to maintain manually.

### 5.3 Version snapshot at run start

When analysis begins:

```python
version_snapshot = {
    'analyzer_version': __version__,
    'homiletics_core_version': homiletics_core.__version__,
    'model_version': 'claude-opus-4-6',
    'bridge_prompt_version': BRIDGE_PROMPT_VERSION,
    'christ_prompt_version': CHRIST_PROMPT_VERSION,
    'flags_prompt_version': FLAGS_PROMPT_VERSION,
    'segmentation_algo_version': SEGMENTATION_VERSION,
    'align_algo_version': ALIGN_VERSION,
    'density_algo_version': DENSITY_VERSION,
    'timing_algo_version': TIMING_VERSION,
    'summary_algo_version': SUMMARY_VERSION,
}
```

This dict is frozen for the entire run — even if another process bumps a version mid-run, this run uses the snapshot. The final `sermon_reviews` row records the snapshot so downstream consumers know the exact provenance.

### 5.4 Homiletical rules in `homiletics_core.py`

Pure functions, importable by both analyzer and coach, no DB access:

```python
__version__ = '1.0.0'

def classify_bridge_landing(
    outline_points: list[OutlinePoint],
    transcript_segments: list[Segment],
) -> BridgeAssessment: ...

def classify_christ_thread(
    segments: list[Segment],
    prep_christ_notes: Optional[str],
) -> ChristThreadAssessment: ...

def compute_density_score(segments: list[Segment]) -> DensityAssessment: ...

def chapell_form_check(outline: Outline, sermon_segments: list[Segment]) -> FormCheckResult: ...

def so_what_gate(outline_point: OutlinePoint, segment: Segment) -> bool: ...

def time_estimator(outline: Outline) -> int: ...  # seconds
```

Analyzer calls these as part of stages 4-7. Coach agent imports them via tools so it can re-run a specific check on a specific segment during conversation (e.g., *"Let me run the FORM check on your §3 conclusion..."*).

### 5.5 LLM call contract for scoring stages

- **Model**: `claude-opus-4-6` (per user preference).
- **Output**: enforced via tool-use schema (structured JSON). Schema example for bridge scoring:

```json
{
  "bridge_score": "landed|partial|missed",
  "evidence": [
    {"transcript_start_sec": 844, "transcript_end_sec": 880,
     "excerpt": "So what does this mean for...", "rationale": "Explicit 'so what'"}
  ],
  "overall_rationale": "short paragraph"
}
```

- **Cost instrumentation**: every call writes to `sermon_analysis_cost_log` with input/output tokens and estimated cost.
- **Retry**: failed call retries 2× with backoff. Third failure → fall back to simpler prompt (enum-only, no evidence). Third failure of the fallback → stage 5 marked failed, review degrades to partial.

### 5.6 Provenance writes

After each analysis run, `sermon_review_provenance` gets one row per metric:

| target_key | source | stage_name | input_hash | model_version |
|---|---|---|---|---|
| `duration_delta_seconds` | `pure_code` | `compute_timing_metrics` | `stage3_hash` | NULL |
| `density_score` | `pure_code` | `compute_density_metrics` | `stage4_hash` | NULL |
| `bridge_score` | `llm` | `score_bridge` | `stage5_hash` | `claude-opus-4-6` |
| `christ_thread_score` | `llm` | `score_christ_thread` | `stage6_hash` | `claude-opus-4-6` |
| `outline_coverage_pct` | `pure_code` | `align_with_outline` | `stage2_hash` | NULL |

Override-sourced values don't write to this table; they come via `sermon_overrides` composition at read time and render as `source='override'` in the UI popover.

### 5.7 Effective-value rule (coach override vs pipeline)

```
effective(target_key) =
    latest override with is_active=1 for this target_key
    if present
    else pipeline value from sermon_reviews
```

Overrides **always** win when present. Reanalysis updates the pipeline value but **never** touches overrides. The `sermon_effective_review` view composes both. All pattern queries, trend aggregates, and UI rendering read from the view.

### 5.8 Analysis dispatch and triggers

**Dispatch mechanism.** No message queue. The analyzer runs as a function call immediately after each sync run completes (in-process, same APScheduler thread), polling:

```sql
SELECT id FROM sermons
WHERE sync_status = 'transcript_ready'
   OR (sync_status = 'review_ready'
       AND source_version > (SELECT source_version_at_analysis
                             FROM sermon_reviews sr WHERE sr.sermon_id = sermons.id))
LIMIT 10
```

Sermons are processed serially to keep LLM call ordering predictable and respect the one-job-per-sermon lease. Each sermon acquires `analysis_lease_expires_at = now + 10 minutes` before its run begins, releases on completion or expiry.

**Triggers that put a sermon into the dispatch queue:**

- Sermon transitions to `transcript_ready` — sync flow moves the state; the dispatch poll picks it up next.
- Stale detection: `sermons.source_version > sermon_reviews.source_version_at_analysis` (checked on every dispatch poll and on UI view).
- Rubric version bump (`homiletics_core.__version__` change) → mark all reviews stale (`source_version_at_analysis` unchanged but `homiletics_core_version` differs); **lazy reanalysis on first view** of each sermon.
- Manual "reanalyze" button per sermon → explicit state transition `review_ready → analysis_pending`.
- Coach `request_reanalysis` tool call → same, respecting one-job-per-sermon lease (returns "busy" to coach if lease is held).

### 5.9 Errors

- LLM failure after retries and fallback → `sermon_reviews` row written with `bridge_score=NULL`, `bridge_evidence=NULL`. Review is `partial_ready` in the UI.
- Transcript < `analysis_transcript_min_words` (default 1000) → `analysis_skipped`, status reason stored.
- Analyzer crash mid-run → `analysis_lease_expires_at` expires, next run reaps and retries.

---

## Section 6 — Coach Agent (`sermon_coach_agent.py`)

### 6.1 System prompt structure

```
1. Identity & Voice                  — from voice_constants.py
2. Homiletical Framework             — references homiletics_core by rule name
3. Current Sermon Context            — passage, linked session, preach_date, duration
4. Pipeline Findings (structured)    — metrics handed as a JSON block
5. Your Agency + Override Protocol   — when to challenge, how to write overrides
6. Tools                             — inventory + usage guidance
7. Longitudinal Posture              — operational rule (see 6.4)
8. Behavioral Constraints            — no auto-initiation, one action per turn
```

### 6.2 Shared voice via `voice_constants.py`

```python
IDENTITY_CORE = """..."""
HOMILETICAL_TRADITION = """..."""
VOICE_GUARDRAILS = """..."""
```

Both `companion_agent.py` (prep) and `sermon_coach_agent.py` (retrospective) import these constants. Voice drift is prevented by single source of truth — changes flow to both automatically.

### 6.3 Tools

Reused from `companion_tools.py`:
- `read_bible_passage`, `lookup_lexicon`, `lookup_grammar`, `find_commentary_paragraph`, `expand_cross_references`

**NEW** tools in `sermon_coach_tools.py`:

| Tool | Purpose |
|---|---|
| `lookup_homiletics_book` | Search Chapell / Robinson / Beeke / Piper / Greidanus / Clowney / Goldsworthy / Mathewson via the existing ResourceIndex |
| `get_sermon_review(sermon_id)` | Full `sermon_effective_review` row |
| `get_sermon_flags(sermon_id)` | All flags for a sermon |
| `get_sermon_overrides(sermon_id)` | Prior override chain |
| `get_transcript_full(sermon_id, start_sec?, end_sec?)` | Raw transcript slice |
| `get_prep_session_full(session_id)` | Outline + card responses + conversation log |
| `pull_historical_sermons(n, filter_expr)` | N prior sermons + their reviews |
| `get_sermon_patterns(window)` | Rolling aggregates from `sermon_trends_recent` |
| `override_metric(sermon_id, target_key, new_value, rationale)` | Writes `sermon_overrides` row with supersession chain |
| `request_reanalysis(sermon_id, rubric_hint?)` | Queues analyzer re-run; respects one-job-per-sermon lease |
| `compare_outline_to_transcript(session_id, sermon_id)` | Runs alignment stage on demand |
| `save_coach_note(sermon_id, note)` | Persists a short coach note |

### 6.4 Operational longitudinal rule (system prompt fragment)

> **Longitudinal posture.** Cite historical patterns only when:
> - at least 3 prior sermons within the last 12 weeks show the same metric trend, OR
> - the user explicitly asks about patterns, trends, or cross-sermon comparisons.
>
> When citing, label your observations explicitly:
> - **"current-sermon observation"** — something you see in this specific sermon
> - **"historical pattern"** — something you see repeated across prior sermons
> - **"trajectory"** — a direction of change across the last N sermons
>
> Never conflate the three. A historical pattern does not override current-sermon judgment; a current-sermon observation does not claim a pattern.

### 6.5 Override vs reanalysis loop breaker

System prompt: *"Within a single turn, choose one action per `target_key`: either `override_metric` OR `request_reanalysis`. Not both. If reanalysis produces new evidence contradicting your override, you may author a new override in a subsequent turn with the updated rationale."*

Enforcement at tool level: `override_metric` returns an error if a `request_reanalysis` call on the same `target_key` is pending (`sermons.analysis_lease_expires_at > now` AND the queued rubric_hint matches this metric).

One reanalysis lease per sermon: acquiring a new `request_reanalysis` while one is pending returns a "busy" tool result; coach narrates the wait.

### 6.6 Interaction entry points

1. **Inline Review tab** — coach greets with structured summary narrated from `sermon_effective_review`.
2. **Flag click** — coach opens focused on a specific moment, uses `get_transcript_full(start_sec, end_sec)`.
3. **Cross-session `/coach`** — Bryan asks longitudinal questions; coach calls `get_sermon_patterns` + `pull_historical_sermons`.

No entry point 4: coach never auto-initiates.

### 6.7 Override authoring guardrails

- `rationale` minimum 30 characters (enforced by tool).
- Supersession chain enforced at write time.
- UI shows a subtle "overridden" marker next to the metric with hover showing pipeline value + rationale.

---

## Section 7 — UI

### 7.1 `/sermons/<id>` — authoritative review surface

Every sermon has a canonical page at `/sermons/<id>`. The Review tab inside `study_session.html` is a **shortcut** to this content when a link exists — identical partials render on both surfaces. Historicals, orphans, and unlinked sermons live solely at `/sermons/<id>` with full review functionality.

**Page states:**

| State | Triggered by | Rendering |
|---|---|---|
| `no_link_no_candidates` | Match ran, no matches | Metadata + transcript + coach chat; no outline fidelity card |
| `candidates_pending` | Tier 2 matches exist | Metadata + candidate list with approve/reject + preview report card |
| `transcript_pending` | `sync_status='synced_metadata'` or `transcript_stalled` | "Transcript still processing on SermonAudio" |
| `analysis_pending` | `sync_status='analysis_pending'` | "Analysis queued" |
| `analysis_running` | `sync_status='analysis_running'` | "Analysis in progress..." with progress indicator |
| `review_ready` | All 8 stages succeeded | Full report card + flag list + coach chat |
| `partial_ready` | Some LLM stages failed, pure stages OK | Report card with per-card states; failed cards show "data pending" placeholders |
| `reanalysis_in_progress` | Lease held during re-run | Report card with existing data + "Reanalyzing..." banner |
| `analysis_failed` | All retries exhausted | Error card + retry button + partial pure-code metrics |
| `stale` | `source_version > source_version_at_analysis` | Report card with "Source changed — reanalyzing" banner; data shown with stale badge |
| `unreviewable_historical` | `sermon_type='topical'` with no passage or transcript too short | Metadata + transcript only; coach chat available but no pipeline card |

### 7.2 Report card per-card states

Each report card (Length / Bridge / Christ Thread / Density / Outline Fidelity) has its own state:

- `ready` — compute succeeded; render normally
- `partial` — pure-code succeeded, LLM stage failed; render available data + subtle warning
- `failed` — stage fully failed; placeholder + retry link
- `stale` — source_version mismatch; badge + reanalysis queued
- `overridden` — pipeline value exists but override is effective; render override value + provenance info-icon

### 7.3 Provenance popover

Every metric rendered on a report card has a small `ⓘ` icon. Clicking opens a popover:

```
bridge_score: partial
source:       llm (claude-opus-4-6)
stage:        score_bridge
computed:     2026-04-14 11:23 UTC
input_hash:   4f8a2d...
analyzer:     1.2.0
rubric:       homiletics_core 1.0.0
```

For overridden values, the popover shows both pipeline and override:

```
bridge_score: landed   ← EFFECTIVE (override)
pipeline:     partial
source:       override (by coach)
computed:     2026-04-14 11:47 UTC
rationale:    "Bryan explicitly connected the text to FCF at 24:18..."
```

### 7.4 Review tab inside `study_session.html`

New tab peer to the existing prep surface. Visible when the session has a linked sermon OR a candidate pending approval. Renders the same partials as `/sermons/<id>` (`sermon_report_card.html`, `sermon_flag_list.html`, `sermon_coach_chat.html`).

### 7.5 Cross-session `/sermons/` pages

| Route | Purpose |
|---|---|
| `/sermons/` | List of all sermons; sortable; attention-queue badge |
| `/sermons/<id>` | Authoritative per-sermon review page |
| `/sermons/attention` | Sorted queue of `needs_attention` items (aging badges) |
| `/sermons/patterns` | Trend cards (length delta, bridge rate, Christ rate, density trend) from `sermon_trends_recent` |
| `/sermons/sync-log` | Debug view of recent sync runs + `sermon_analysis_cost_log` totals |
| `/sermons/classification-review` | Unknown eventType queue with approval UI |
| `/sermons/bootstrap` | One-shot historical import trigger |
| `/sermons/coach` | Cross-session coach conversation (Bryan's "nice but unnecessary" surface) |
| `/sermons/health` | Operational dashboard — counts by `sync_status`, attention depth, last run result |

### 7.6 Badge logic

```sql
-- Badge fires if:
sermon.sync_status = 'review_ready'
AND sermon.source_version > sermon.ui_last_seen_version
```

On opening any page that renders a sermon, a compare-and-set write:

```sql
UPDATE sermons
SET ui_last_seen_version = :current_source_version
WHERE id = :sermon_id
  AND ui_last_seen_version < :current_source_version;
```

This is monotonic — a new tab can't regress another tab's clear. Badges re-fire on `source_version` bumps (new sync + reanalysis).

### 7.7 HTMX + SSE

Same infrastructure as the existing prep UI. New partials:

```
templates/partials/
├── sermon_report_card.html
├── sermon_flag_list.html
├── sermon_coach_chat.html
├── sermon_candidates_list.html
├── sermon_attention_row.html
└── sermon_pattern_card.html

templates/sermons/
├── list.html
├── detail.html
├── attention.html
├── patterns.html
├── sync_log.html
├── classification_review.html
├── bootstrap.html
├── coach.html
└── health.html

static/
├── sermons.css
└── sermons.js
```

Dark theme matches existing `companion.css` / `study.css`.

---

## Section 8 — Error handling & operational surface

Consolidated recovery matrix:

| Layer | Failure mode | Recovery path |
|---|---|---|
| **Ingest** | API 429/5xx/timeout | Retry in-run (3×, exp backoff); on final failure, SQL-enforced escalating cooldown; terminal after `failure_count ≥ 5` → `permanent_failure` |
| **Ingest** | API 401/403 | Abort entire run; alert on `/sermons/sync-log` |
| **Ingest** | Lock contention | HTTP 409 for manual; silent abort for cron |
| **Ingest** | Process crash mid-run | Lease expires in ≤90s; next run reaps; bootstrap resumes from checkpoint |
| **Ingest** | Unknown eventType | Surfaces in `/sermons/classification-review` for one-click approval; heuristic catches it meanwhile |
| **Match** | Unparseable passage | `match_status='unparseable_passage'` → `/sermons/attention` |
| **Match** | UI rejection race | `BEGIN IMMEDIATE` transaction |
| **Match** | Manual link | Sticky; auto-supersession disabled for `link_source='manual'` |
| **Analyze** | LLM call failure | Retry 2×; fallback to simpler enum-only prompt; 3rd failure → `partial_ready` |
| **Analyze** | JSON parse error | Retry; fallback prompt; log to `sermon_analysis_cost_log` |
| **Analyze** | Transcript too short | `analysis_skipped` + reason |
| **Analyze** | Cache miss on rubric bump | Lazy reanalysis on view |
| **Analyze** | Crash mid-run | `analysis_lease_expires_at` expiry + reaper |
| **Coach** | Tool error | Return error to LLM; coach narrates recovery or retries |
| **Coach** | Override vs reanalyze conflict | Tool-level lock; returns "busy" to coach |
| **UI** | Page crash | Flask 500 logged; friendly error with retry link |

### 8.1 Health dashboard (`/sermons/health`)

Read-only page showing:

- Sermon counts by `sync_status`
- Attention queue depth by `match_status`
- Last 5 sync runs (trigger, counts, status)
- Cost log rolling totals (24h / 7d / 30d)
- Stale review count (`source_version > source_version_at_analysis`)
- Lock state (held_by, expires_at)
- Sermons in `permanent_failure` (with manual retry button)

---

## Section 9 — Testing strategy

### 9.1 Unit tests (pytest, `tools/workbench/tests/`)

| File | Coverage |
|---|---|
| `test_sermonaudio_sync.py` | Classification rules, hash computation, upsert logic, state transitions, lock acquisition (race test), checkpoint resume, error classification |
| `test_sermon_passages.py` | Multi-range parsing, chapter span parsing, whole-chapter parsing, unparseable → zero rows |
| `test_sermon_type_topical.py` | Topical exclusion from matcher; matcher returns no_match for `sermon_type='topical'` |
| `test_sermon_matcher.py` | 30+ scenario tests: Tier 1/2/3 rules, multi-passage overlap, rematch supersession, manual-link stickiness, rejected-link recovery, historical cutoff, `BEGIN IMMEDIATE` race |
| `test_sermon_analyzer.py` | Stages 1-4 pure; stages 5-7 with canned `CannedLLMClient`; flag extraction; degradation to `partial_ready` on LLM failure |
| `test_cache_invalidation.py` | Content-addressed cache hits/misses; upstream change cascades via hash mismatch; version snapshot held constant mid-run |
| `test_effective_values.py` | `sermon_effective_review` view composition; override precedence; override survives reanalysis; null override returns pipeline value |
| `test_provenance.py` | `sermon_review_provenance` writes per metric; override rows not written to provenance (composed at read time); popover data shape |
| `test_homiletics_core.py` | Pure function rules: FORM check, Christ thread classifier, density score, time estimator, "so what" gate |
| `test_sermon_coach_agent.py` | Prompt assembly with `voice_constants`; tool dispatch; `override_metric` 30-char rationale enforcement; one-action-per-turn lock; longitudinal posture labeling |
| `test_sermon_coach_tools.py` | Each new tool: read access to transcripts/sessions/history; `override_metric` supersession chain; `request_reanalysis` lease check |

### 9.2 Integration tests

| File | Coverage |
|---|---|
| `test_sermon_pipeline_end_to_end.py` | Mock SermonAudio → sync → match → analyze → read review; asserts full path including all state transitions |
| `test_sermon_rematch_flow.py` | Create sermon, no session; create session later (auto-match fires); update session non-homiletical (no churn); create competing session (supersession) |
| `test_sermon_override_flow.py` | Analyze → coach overrides → effective view returns override → reanalysis → override persists → effective still returns override |
| `test_sermon_bootstrap_resume.py` | Bootstrap mid-run crash → checkpoint persisted → restart resumes from last page |
| `test_sermon_source_change_flow.py` | Sermon analyzed → SermonAudio updates transcript → source_version bump → stale detection → reanalysis → badge re-fire |

### 9.3 E2E Playwright

Extends existing `tools/workbench/tests/test_e2e_*` pattern:

- Bootstrap flow: click "Bootstrap" → mocked API → progress → completion
- Manual sync: click "Sync now" → mocked new sermon → badge on session card
- Review tab open → report card render → flag click → coach chat open → coach responds
- Override flow: coach overrides bridge score → UI shows both values → popover shows rationale
- Cross-session patterns: open `/sermons/patterns` → trend cards render
- Unlinked historical: open `/sermons/<id>` directly → authoritative review surface renders

### 9.4 Backtest harness

`scripts/backtest_matcher.py` — after bootstrap completes, runs matcher over the real 356 sermons × real sessions and writes a CSV:

```csv
sermon_id, preach_date, sermon_passage, decision, tier, reason, linked_session_id, linked_session_passage
```

Bryan eyeballs for bad decisions. Any surprise becomes a new unit test fixture. Rules get adjusted in `homiletics_core.py` / `sermon_matcher.py` and the CSV is re-run until clean.

### 9.5 LLM test doubles

```python
# test_fixtures.py
class LLMClient(Protocol):
    def call(self, prompt, schema) -> dict: ...

class CannedLLMClient:
    def __init__(self, canned: dict[str, dict]): self.canned = canned
    def call(self, prompt, schema):
        key = sha256(prompt).hexdigest()[:16]
        return self.canned.get(key) or {'error': 'no canned response'}
```

Analyzer takes `LLMClient` via dependency injection. Tests pass `CannedLLMClient`. Live API tests are marked `@pytest.mark.live_api` and excluded from CI by default.

### 9.6 Test database

Same pattern as existing workbench tests: a temp SQLite file seeded via `init_db()` + fixture sermons/sessions. No touching of the real `companion.db`.

---

## Operational costs

| Category | Estimate |
|---|---|
| **CPU** | ~0% idle; brief spikes during sync; LLM calls are network-bound |
| **Memory** | +30 MB baseline (APScheduler + sermonaudio lib); +50 MB peak during sync |
| **Disk** | +100 MB one-time for bootstrap; +5 MB/year steady state |
| **Network** | ~5 MB per steady-state sync; ~100 MB one-time for bootstrap |
| **LLM API** | $0 for ingest; $35–$90 one-time for full 356-sermon historical analysis (opt-in scope picker lets Bryan choose scope); $5–$13/year ongoing at 1 sermon/week |
| **Other apps** | No meaningful impact on couple-companion / mighty-oaks / adhd-align / tendflock |

Cost telemetry persisted in `sermon_analysis_cost_log`; `/sermons/sync-log` shows running totals.

---

## What is explicitly NOT in scope for this spec

- **Multi-user support** — single-user Mac, no auth
- **External push notifications** — badge-only per user's decision
- **Sermon audio playback in the UI** — the audio URL is stored but playback is deferred (phase 2)
- **Real-time patterns dashboard** — trend cards recompute on view, no live updates
- **Automated sermon comparison mode** — coach can do this via tool calls, but no dedicated "compare two sermons" UI
- **Manual transcript paste fallback** — SermonAudio AI transcription is the only source (phase 2 can add this if SA degrades)
- **Automatic rubric tuning** — overrides are tracked, but tuning `homiletics_core.py` is manual review of override history

---

## Open questions deferred to the implementation plan

1. **APScheduler in-process vs separate PM2 worker** — spec goes with in-process; plan will revisit if testing surfaces Flask-scheduler coupling issues.
2. **Live API cost budgets** — whether to add a per-day cost ceiling enforced at the analyzer level (cut off auto-analysis if the day's cost exceeds $X). YAGNI for MVP; revisit after first month's usage data.
3. **Which homiletics books get indexed first for `lookup_homiletics_book`** — probably Chapell + Robinson + Beeke as MVP set; others added as the need surfaces in real use.

---

## References

- **CLAUDE.md** — project instructions
- **`companion_agent.py`** — existing prep-side voice and guardrails (shared via `voice_constants.py`)
- **`companion_db.py`** — existing schema (new tables attach via FKs; one `ALTER` on `sessions`)
- **`companion_tools.py`** — tool layer reused by coach
- **`tools/study.py`** — `parse_reference()` extended for multi-range + chapter spans
- **SermonAudio API v2** — https://api.sermonaudio.com/ (key auth, `sermonaudio` PyPI package)
- **Adversarial review trail** — codex CLI was consulted at four checkpoints during design (approaches, architecture + data model, ingest layer, remaining sections). Its critiques drove substantial revisions to cache invalidation, override precedence, state machines, matching rules, and auditability. The final design integrates those revisions; the review transcripts are archived in the brainstorm conversation for this session.
