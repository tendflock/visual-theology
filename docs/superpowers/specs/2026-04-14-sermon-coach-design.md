# Sermon Coach — Design Spec (MVP)

**Date:** 2026-04-14 (rewritten after two consultant rounds)
**Author:** Bryan Schneider + Claude (with adversarial review by OpenAI Codex CLI and an outside research consultant)
**Status:** Draft — MVP scope, pending user approval before implementation
**Parent project:** Logos 4 Library + Sermon Study Companion (`tools/workbench/`)

## Problem

Bryan preps sermons in the existing 12-phase companion Monday through Saturday, preaches Sunday morning, then retrospects his delivery Monday or Tuesday. Today the retrospective is manual: he pastes his sermon transcript into an external Claude chat and asks for feedback. That feedback is context-free — it doesn't know his prep notes, his outline, his FCF, or his time plan, and it doesn't know how last week's sermon ran. His wife's crystallizing feedback — *"too long, too dense, application comes late"* — is a pattern across sermons, not a one-off. What Bryan actually needs is a **weekly coaching loop** that helps him preach **shorter, clearer, warmer, and more pointedly**, grounded in his prep context and accumulating longitudinal signal over time.

Two rounds of consultant review sharpened what that means in practice:

1. **Build the spine, cut the limbs.** A first version should be ruthlessly scoped to deterministic metrics + one interpretive pass + one review page + one trends view. Override chains, provenance popovers, content-addressed stage caches, and elaborate locking are premature for a single-user weekly workflow.

2. **Major on impact, not just analyzability.** The metrics that are easy to engineer from prep artifacts (outline fidelity, Christ-thread presence, density score) are not what rhetoric and sermon-listening research identify as the strongest predictors of *impact on hearers*. Impact comes from clarity of burden, movement, application specificity, ethos, and concreteness. Faithfulness metrics (Christ thread, exegetical grounding) matter for a Reformed pastor but are orthogonal to listener impact and belong in their own lane.

This MVP is built on both corrections.

## Solution

A **pipeline-first sermon coach** layered onto the existing companion. A small number of deterministic modules handle ingestion, matching, and metric extraction from SermonAudio-synced transcripts. A single Opus 4.6 LLM pass scores each sermon against a three-tier rubric (impact / faithfulness / diagnostic) and emits a structured review. A coach chat surface lets Bryan interrogate the findings and read deeper — the coach has full read access to raw transcripts, prep sessions, and cross-sermon history, but it never computes canonical metrics on the fly. Everything is recomputable by re-running the analyzer. No overrides, no provenance graph, no stage cache — just the core loop.

The architectural line stays: **the pipeline is a floor, not a ceiling.** Metrics come from deterministic code and one structured LLM pass. The coach narrates from the floor, and when it sees something the pipeline missed, it says so in plain chat — coach disagreement is just a conversation message, not a structured override table.

The **corpus-gated longitudinal rule** (research-derived) governs what the coach is allowed to claim:

| Corpus | Coach voice |
|---|---|
| 1 sermon | single-sermon observations only — no pattern language |
| 2–4 sermons | "early observations" — no "persistent" claims |
| 5–9 sermons (~15,000 words) | "emerging pattern" framing allowed when ≥3/5 sermons share the trend |
| 10+ sermons (~25,000 words) | full longitudinal voice ("pattern," "trajectory," "persistent") |

This prevents the coach from over-speaking during the early weeks when there's not enough recent corpus to distinguish a real habit from a single sermon's quirk.

---

## MVP scope in one screen

**In (MVP):**
- SermonAudio ingest filtered to `speaker=Bryan Schneider` AND `eventType=Sunday Service` (heuristic fallback of Sunday + >20min)
- Last-24 recent sermons backfill as the historical baseline (~$5 one-time, ~6 months)
- Tier-based auto-matching (high confidence only; default unlinked, manual approval UI for candidates)
- 8-table schema (sermons, passages, links, reviews, flags, coach_messages, sync_log, cost_log)
- Deterministic stage pipeline: segmentation, outline alignment (when linked), timing, density hotspots
- **One** combined Opus 4.6 LLM call per sermon emitting the full three-tier rubric as structured JSON
- **Four-card review page**: Impact / Faithfulness / Diagnostic / Prescription
- Streaming Opus 4.6 coach chat below the cards, reading precomputed review + full raw context
- Trends page showing last 8–12 sermons across the Tier 1 impact dimensions + diagnostic trend lines
- Corpus-gated longitudinal rule enforced in the coach prompt and at the `get_sermon_patterns` tool level
- Manual "Sync now" button + 4h APScheduler cron
- Simple file-based lock; idempotent upsert handles concurrent or crashed runs
- Cost transparency via `sermon_analysis_cost_log`

**Out (deferred to Phase 2+, see appendix):**
- Structured override chains and effective-value views
- Per-metric provenance + popovers + input-hash tracking
- Content-addressed stage cache
- Bootstrap resumability / checkpoint tables
- Lease-based locking with heartbeat
- Cross-session `/sermons/coach` standalone chat
- `lookup_homiletics_book` tool (Chapell/Robinson/Beeke citations — available as a single tool but not promoted)
- Per-metric rubric versioning and staleness gates
- Coach notes table (coach writes chat messages instead)
- Classification-review UI for unknown eventTypes
- Health dashboard beyond `/sermons/sync-log`
- Topical sermon handling (MVP only supports expository; topical get `sermon_type='topical'` and are excluded from auto-analysis)
- Full 356-sermon historical backfill

---

## Architecture

### Five layers, one direction

```
                ┌─────────────────────────────────────────────────┐
                │  SermonAudio API (external, AI transcripts)     │
                └──────────────────────┬──────────────────────────┘
                                       │  4h cron + manual trigger
                                       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 1 — INGEST            sermonaudio_sync.py             │
  │  - API client, speaker+eventType filter                      │
  │  - Idempotent hash-based upsert                              │
  │  - Simple state machine (pending → ready → analyzed)         │
  │  - File-based lock, retry with SQL-enforced cooldown         │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 2 — MATCH             sermon_matcher.py               │
  │  - Three rule tiers (auto / candidate / no match)            │
  │  - Pure function + transactional orchestrator                │
  │  - Default UNLINKED on ambiguity                             │
  │  - Multi-range passages via sermon_passages                  │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 3 — ANALYZE           sermon_analyzer.py              │
  │  - Pure stages: segment, align_with_outline, timing, density │
  │  - ONE combined LLM call (claude-opus-4-6) emitting the full │
  │    three-tier rubric in structured JSON                      │
  │  - Writes sermon_reviews + sermon_flags                      │
  │  - Calls homiletics_core.py pure functions                   │
  │  - Recomputable: re-run overwrites rows                      │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 4 — NARRATE (COACH)   sermon_coach_agent.py           │
  │  - Streaming claude-opus-4-6                                 │
  │  - Reads precomputed review + full raw context               │
  │  - Corpus-gated longitudinal rule enforced in prompt         │
  │  - Narrates from the review, can chat deeper                 │
  │  - Disagreement = chat message, not structured override      │
  │  - Voice constants shared with companion_agent.py            │
  └──────────────────────┬───────────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 5 — UI                app.py + templates + static     │
  │  - /sermons/<id> = authoritative review surface              │
  │  - Review tab inside study_session.html = linked shortcut    │
  │  - /sermons/patterns = trends view                           │
  │  - /sermons/sync-log = debug                                 │
  │  - Badge on session card when review lands                   │
  └─────────────────────────────────────────────────────────────┘
```

### Two durable invariants

1. **Recomputable from the database alone.** If the rubric changes or a transcript updates, re-running the analyzer overwrites `sermon_reviews` + `sermon_flags` and trends refresh automatically. No state lives outside tables.

2. **The coach reads everything, writes nothing canonical.** Pipeline values are the default. When the coach disagrees, it narrates the disagreement in chat — that disagreement is logged in `sermon_coach_messages` but doesn't silently rewrite metric values. If Bryan wants to make a coach disagreement persistent, he can flag it via a chat message that stays in the log.

### Module ownership

| Module | Responsibility |
|---|---|
| `sermonaudio_sync.py` | Ingest, classify, upsert |
| `sermon_matcher.py` | Deterministic session matching |
| `sermon_analyzer.py` | Pure stages + one structured LLM call |
| `sermon_coach_agent.py` | Streaming coach conversation |
| `homiletics_core.py` | Pure rule functions (imported by analyzer) |
| `voice_constants.py` | Shared voice DNA (imported by both companion_agent and coach_agent) |
| `sermon_coach_tools.py` | Tools the coach uses for depth reads |

Existing code is untouched except:
- `companion_db.py` grows the new tables and gains two writer touches in `save_card_response` / `save_message` for homiletical phases to maintain `sessions.last_homiletical_activity_at`
- `tools/study.py` `parse_reference()` is extended for multi-range and chapter-span passages

---

## Data Model

Eight new tables, one column added to `sessions`, one view. All new tables hang off existing schema via FKs and can be ripped out cleanly.

### `sermons`

```sql
CREATE TABLE sermons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermonaudio_id TEXT UNIQUE NOT NULL,
    broadcaster_id TEXT NOT NULL,
    title TEXT NOT NULL,
    speaker_name TEXT,
    event_type TEXT,
    series TEXT,
    preach_date TEXT,
    publish_date TEXT,
    duration_seconds INTEGER,

    -- Primary passage (secondaries in sermon_passages)
    bible_text_raw TEXT,
    book INTEGER,
    chapter INTEGER,
    verse_start INTEGER,
    verse_end INTEGER,

    -- Content
    audio_url TEXT,
    transcript_text TEXT,
    transcript_source TEXT DEFAULT 'sermonaudio',

    -- Type and classification
    sermon_type TEXT NOT NULL DEFAULT 'expository'
        CHECK (sermon_type IN ('expository','topical')),
    classified_as TEXT NOT NULL
        CHECK (classified_as IN ('sermon','skipped')),
    classification_reason TEXT,

    -- Fingerprint for idempotent upsert and stale detection
    metadata_hash TEXT,
    transcript_hash TEXT,
    source_version INTEGER NOT NULL DEFAULT 1,
    remote_updated_at TEXT,

    -- State
    sync_status TEXT NOT NULL DEFAULT 'pending_sync' CHECK (sync_status IN (
        'pending_sync',
        'synced_metadata',
        'transcript_ready',
        'analysis_pending',
        'analysis_running',
        'review_ready',
        'sync_failed',
        'analysis_failed',
        'analysis_skipped',
        'permanent_failure'
    )),
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
    is_remote_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,

    -- UI state: simple monotonic version
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

**State machine transitions:**

```
pending_sync → synced_metadata → transcript_ready → analysis_pending → analysis_running → review_ready
      │              │                  │                    │
      └──► sync_failed                   └──► analysis_failed
             │                                      │
             │ (1h→4h→16h→64h SQL cooldown,          │ (retry)
             │  then permanent_failure at ≥5)        │
             ▼                                      ▼
       pending_sync / permanent_failure      analysis_pending
```

Badge fires on transition into `review_ready` **OR** when `source_version > ui_last_seen_version` on a sermon that's already in `review_ready` (e.g., the source mutated and the sermon got re-analyzed).

### `sermon_passages` — multi-range support

```sql
CREATE TABLE sermon_passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    book INTEGER NOT NULL,
    chapter_start INTEGER NOT NULL,
    verse_start INTEGER,           -- NULL = verse 1
    chapter_end INTEGER NOT NULL,
    verse_end INTEGER,             -- NULL = end of chapter
    raw_text TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(sermon_id, rank)
);
CREATE INDEX idx_sermon_passages_sermon ON sermon_passages(sermon_id);
CREATE INDEX idx_sermon_passages_lookup ON sermon_passages(book, chapter_start);
```

Primary passage (`rank=1`) is also denormalized on `sermons` for cheap single-lookup filters. `"Romans 8:1-11; Romans 9:1-5"` parses to two rows.

### `sermon_links` — matched sessions

```sql
CREATE TABLE sermon_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    link_status TEXT NOT NULL
        CHECK (link_status IN ('active','candidate','rejected')),
    link_source TEXT NOT NULL CHECK (link_source IN ('auto','manual')),
    match_reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(sermon_id, session_id)
);
CREATE UNIQUE INDEX idx_sermon_links_one_active
    ON sermon_links(sermon_id) WHERE link_status = 'active';
CREATE INDEX idx_sermon_links_sermon ON sermon_links(sermon_id);
CREATE INDEX idx_sermon_links_session ON sermon_links(session_id);
```

MVP drops `superseded` status (just delete and re-create), drops `confidence` (tier rules are enough), drops supersession audit fields. When the matcher finds a better link for an already-linked sermon, it updates the existing `active` row directly rather than creating a supersession chain.

### `sermon_reviews` — three-tier rubric

```sql
CREATE TABLE sermon_reviews (
    sermon_id INTEGER PRIMARY KEY REFERENCES sermons(id),
    analyzer_version TEXT NOT NULL,
    homiletics_core_version TEXT NOT NULL,
    model_version TEXT,
    analyzed_transcript_hash TEXT NOT NULL,
    source_version_at_analysis INTEGER NOT NULL,

    -- ── TIER 1: IMPACT PREDICTORS ────────────────────────────────
    burden_clarity TEXT CHECK (burden_clarity IN
        ('crisp','clear','implied','muddled','absent')),
    burden_statement_excerpt TEXT,
    burden_first_stated_at_sec INTEGER,

    movement_clarity TEXT CHECK (movement_clarity IN
        ('river','mostly_river','uneven','lake')),
    movement_rationale TEXT,

    application_specificity TEXT CHECK (application_specificity IN
        ('localized','concrete','abstract','absent')),
    application_first_arrived_at_sec INTEGER,
    application_excerpts TEXT,            -- JSON array of {start_sec, excerpt}

    ethos_rating TEXT CHECK (ethos_rating IN
        ('seized','engaged','professional','detached')),
    ethos_markers TEXT,                   -- JSON array of observations

    concreteness_score INTEGER CHECK (concreteness_score BETWEEN 1 AND 5),
    imagery_density_per_10min REAL,
    narrative_moments TEXT,               -- JSON array of {start_sec, end_sec, excerpt}

    -- ── TIER 2: FAITHFULNESS ─────────────────────────────────────
    christ_thread_score TEXT CHECK (christ_thread_score IN
        ('explicit','gestured','absent')),
    christ_thread_excerpts TEXT,          -- JSON
    exegetical_grounding TEXT CHECK (exegetical_grounding IN
        ('grounded','partial','pretext')),
    exegetical_grounding_notes TEXT,

    -- ── TIER 3: DIAGNOSTIC (symptoms) ────────────────────────────
    actual_duration_seconds INTEGER NOT NULL,
    planned_duration_seconds INTEGER,
    duration_delta_seconds INTEGER,
    section_timings TEXT,                 -- JSON: {intro, body, app, close}
    length_delta_commentary TEXT,
    density_hotspots TEXT,                -- JSON array of {start_sec, end_sec, note}
    late_application_note TEXT,
    outline_coverage_pct REAL,            -- NULL if unlinked
    outline_additions TEXT,               -- JSON
    outline_omissions TEXT,               -- JSON
    outline_drift_note TEXT,

    -- ── COACH SUMMARY (emitted by same LLM pass) ─────────────────
    top_impact_helpers TEXT NOT NULL,     -- JSON array of 2-3 strings
    top_impact_hurters TEXT NOT NULL,     -- JSON array of 2-3 strings
    faithfulness_note TEXT,               -- one-line summary, nullable
    one_change_for_next_sunday TEXT NOT NULL,

    computed_at TEXT NOT NULL
);
```

One row per sermon. Re-running the analyzer overwrites this row.

### `sermon_flags` — granular per-moment flags

```sql
CREATE TABLE sermon_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
    flag_type TEXT NOT NULL,            -- 'density_spike','late_application','abstract_app','cold_ethos','narrative_moment','refrain','burden_restate','etc.'
    severity TEXT NOT NULL CHECK (severity IN ('info','note','warn','concern')),
    transcript_start_sec INTEGER,
    transcript_end_sec INTEGER,
    section_label TEXT,
    excerpt TEXT,
    rationale TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_sermon_flags_sermon ON sermon_flags(sermon_id);
CREATE INDEX idx_sermon_flags_type ON sermon_flags(flag_type);
```

Deleted + reinserted per sermon on re-analysis. Clickable in UI to open a focused coach conversation.

### `sermon_coach_messages`

```sql
CREATE TABLE sermon_coach_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER REFERENCES sermons(id),
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

This table also holds any "coach-disagrees-with-the-pipeline" narration as an ordinary assistant turn. No separate override table in MVP.

### `sermon_sync_log`

```sql
CREATE TABLE sermon_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    trigger TEXT NOT NULL CHECK (trigger IN ('cron','manual','backfill')),
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
```

### `sermon_analysis_cost_log`

```sql
CREATE TABLE sermon_analysis_cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id INTEGER NOT NULL REFERENCES sermons(id),
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    estimated_cost_usd REAL NOT NULL,
    called_at TEXT NOT NULL
);
CREATE INDEX idx_cost_log_sermon ON sermon_analysis_cost_log(sermon_id);
CREATE INDEX idx_cost_log_called ON sermon_analysis_cost_log(called_at DESC);
```

### `sessions` — one column added

```sql
ALTER TABLE sessions ADD COLUMN last_homiletical_activity_at TEXT;
```

Maintained by `save_card_response` and `save_message` in `companion_db.py` when the phase is in the homiletical set (`exegetical_point`, `fcf_homiletical`, `sermon_construction`, `edit_pray`).

### `sermon_trends_recent` — aggregate view

```sql
CREATE VIEW sermon_trends_recent AS
SELECT
    COUNT(*) AS n_sermons,
    SUM(LENGTH(s.transcript_text) - LENGTH(REPLACE(s.transcript_text, ' ', ''))) + COUNT(*)
        AS approx_total_words,

    -- Tier 1 aggregates
    1.0 * SUM(CASE WHEN sr.burden_clarity IN ('crisp','clear') THEN 1 ELSE 0 END) / COUNT(*)
        AS burden_clear_rate,
    1.0 * SUM(CASE WHEN sr.movement_clarity IN ('river','mostly_river') THEN 1 ELSE 0 END) / COUNT(*)
        AS movement_clear_rate,
    1.0 * SUM(CASE WHEN sr.application_specificity IN ('localized','concrete') THEN 1 ELSE 0 END) / COUNT(*)
        AS application_concrete_rate,
    1.0 * SUM(CASE WHEN sr.ethos_rating IN ('seized','engaged') THEN 1 ELSE 0 END) / COUNT(*)
        AS ethos_engaged_rate,
    AVG(sr.concreteness_score) AS avg_concreteness,

    -- Tier 2 aggregates
    1.0 * SUM(CASE WHEN sr.christ_thread_score = 'explicit' THEN 1 ELSE 0 END) / COUNT(*)
        AS christ_explicit_rate,
    1.0 * SUM(CASE WHEN sr.exegetical_grounding = 'grounded' THEN 1 ELSE 0 END) / COUNT(*)
        AS exegetical_grounded_rate,

    -- Tier 3 aggregates
    AVG(sr.duration_delta_seconds) AS avg_duration_delta_sec,
    AVG(1.0 * sr.application_first_arrived_at_sec / sr.actual_duration_seconds)
        AS avg_app_arrival_ratio,
    AVG(sr.outline_coverage_pct) AS avg_outline_coverage,

    -- Corpus gate computation
    CASE
        WHEN COUNT(*) >= 10 THEN 'stable'
        WHEN COUNT(*) >= 5 THEN 'emerging'
        ELSE 'pre_gate'
    END AS corpus_gate_status
FROM sermon_reviews sr
JOIN sermons s ON s.id = sr.sermon_id
WHERE s.preach_date >= date('now', '-90 days')
  AND s.classified_as = 'sermon'
  AND s.is_remote_deleted = 0;
```

Pattern queries and trend cards read from this view. `corpus_gate_status` drives the coach's longitudinal permissions.

---

## Section 3 — Ingest (`sermonaudio_sync.py`)

### 3.1 API client

- Library: `sermonaudio` PyPI package, added to requirements
- Auth: API key + broadcaster ID from `.env` (`SERMONAUDIO_API_KEY`, `SERMONAUDIO_BROADCASTER_ID`)
- Transport: serial requests, exponential backoff (1s → 2s → 4s) on 429/5xx, 30s timeout per request, max 3 retries per request, soft 10-minute run budget

### 3.2 Classification

Hard gate on speaker, then eventType + heuristic union:

```python
BRYAN_SPEAKER_NAME = 'Bryan Schneider'
SERMON_EVENT_TYPES = frozenset({'Sunday Service'})
DEVOTIONAL_EVENT_TYPES = frozenset({'Devotional', 'Daily Devotional'})

def classify(sermon_remote) -> tuple[str, str]:
    speaker = (sermon_remote.speaker_name or '').strip()
    event_type = (sermon_remote.event_type or '').strip()

    if speaker != BRYAN_SPEAKER_NAME:
        return ('skipped', f'speaker={speaker!r}')

    if event_type in SERMON_EVENT_TYPES:
        return ('sermon', f'eventType={event_type}')
    if event_type in DEVOTIONAL_EVENT_TYPES:
        return ('skipped', f'eventType={event_type}')

    pdate = sermon_remote.preach_date
    dur_min = (sermon_remote.duration_seconds or 0) / 60
    if pdate and pdate.weekday() == 6 and dur_min > 20:
        return ('sermon', f'heuristic: Sunday + {int(dur_min)}min')

    return ('skipped', f'eventType={event_type!r} (unknown)')
```

Constants live in code for MVP. If unknown eventTypes start accumulating, Phase 2 adds the runtime classification table.

### 3.3 Idempotent upsert with source fingerprint

```python
def compute_hashes(sermon_remote) -> tuple[str, Optional[str]]:
    meta = json.dumps({
        'title': sermon_remote.title, 'event_type': sermon_remote.event_type,
        'series': sermon_remote.series, 'preach_date': str(sermon_remote.preach_date),
        'bible_text_raw': sermon_remote.bible_text,
        'duration_seconds': sermon_remote.duration,
        'remote_updated_at': str(sermon_remote.update_date),
    }, sort_keys=True)
    meta_hash = hashlib.sha256(meta.encode()).hexdigest()[:16]
    tx_hash = hashlib.sha256((sermon_remote.transcript or '').encode()).hexdigest()[:16] \
              if sermon_remote.transcript else None
    return meta_hash, tx_hash
```

Upsert is keyed on `sermonaudio_id`. Unchanged hashes → no-op touch of `last_synced_at`. Changed hashes → bump `source_version`, update hashes, push `sync_status` back to `analysis_pending` if it had advanced past that.

### 3.4 Fetch strategy

- **Backfill mode** (one-shot, triggered manually via `POST /sermons/backfill?limit=24`):
  - Pulls the most recent 24 classified-as-sermon items from the broadcaster, newest first
  - No page-resumability: if it crashes, click the button again — idempotent upsert handles dupes
  - Writes status and counters to `sermon_sync_log`
- **Steady-state mode** (every 4h cron or manual `POST /sermons/sync`):
  - Primary filter: `updated_since = last_successful_sync_at - 1 day` (small clock-skew overlap) if the SermonAudio SDK supports it
  - Fallback: pull last 30 days by `publish_date` and compare `remote_updated_at` client-side

### 3.5 Concurrency

Simple file-based advisory lock at `/tmp/logos4_sermon_sync.lock` (or `app.instance_path`). Acquired via `fcntl.flock(LOCK_EX | LOCK_NB)`:

```python
def with_sync_lock(fn):
    lock_path = os.path.join(app.instance_path, 'sermon_sync.lock')
    with open(lock_path, 'w') as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None  # caller returns 409
        try:
            return fn()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

If Flask crashes mid-run, the OS releases the lock when the process dies. Next cron run acquires cleanly. Idempotent upsert protects the rare concurrent-touch case.

### 3.6 Retry cooldown (SQL-enforced)

```sql
SELECT id FROM sermons
WHERE sync_status = 'sync_failed'
  AND failure_count < 5
  AND (last_failure_at IS NULL OR last_failure_at < datetime('now', '-' ||
        CASE failure_count
            WHEN 0 THEN '1 hours'
            WHEN 1 THEN '4 hours'
            WHEN 2 THEN '16 hours'
            ELSE '64 hours'
        END));
```

`failure_count ≥ 5` → explicit `UPDATE sermons SET sync_status='permanent_failure'` inside the sync function. Permanent failures surface on `/sermons/sync-log` with a manual retry button that clears `failure_count`.

### 3.7 Cron + manual trigger

- **Cron**: APScheduler `BackgroundScheduler` inside the Flask app, `IntervalTrigger(hours=4)`, added on app boot
- **Manual**: `POST /sermons/sync` calls the same sync function, returns `run_id` immediately, UI polls `GET /sermons/sync-log/<run_id>`

### 3.8 Error classification

| Error | Action |
|---|---|
| HTTP 429/5xx/timeout | In-run retry (backoff 1s→2s→4s), then mark `sync_failed`, escalate via cooldown |
| HTTP 401/403 | Abort entire run, alert in `/sermons/sync-log` |
| HTTP 404 on detail fetch | Mark `is_remote_deleted=1`, `deleted_at=now` |
| Parse error | Mark `sync_failed`, stacktrace in `sync_error`, `failure_count++`, continue run |

---

## Section 4 — Matcher (`sermon_matcher.py`)

### 4.1 Rule tiers

**Tier 1 — auto-link as `active`.** All must hold:

1. **Exact passage match**: at least one `sermon_passages` row's `(book, chapter_start, verse_start, chapter_end, verse_end)` tuple matches a session's `(book, chapter, verse_start, verse_end)` (whole-chapter semantics respected)
2. **Prep timing realistic**: session's `last_homiletical_activity_at` is within 7 days before `preach_date`
3. **Session created before sermon**: `session.created_at < sermon.preach_date`
4. **Exactly one session qualifies** — ambiguity demotes to Tier 2
5. **No prior `rejected` link** between this sermon and this session
6. **`sermon_type = 'expository'`** — topical sermons never auto-match

→ Write one `sermon_links` row with `link_status='active'`, `link_source='auto'`, `match_reason='tier1:exact+timing'`.

**Tier 2 — surface as `candidate`.** Any one of:

- Passage overlaps but verse range differs (same book/chapter, non-exact verses)
- Timing 7–14 days
- Multiple Tier 1 qualifiers (ambiguity)
- Session matches passage + timing but never reached a homiletical phase

→ Write one `sermon_links` row per candidate with `link_status='candidate'`. UI shows them in a "Candidates for this sermon" panel; one-click approval flips selected candidate to `active` and deletes the others (or leaves them as rejected if Bryan explicitly rejects).

**Tier 3 — no row.** No passage overlap, no session within 30 days, or session created after sermon.

### 4.2 Pure function interface

```python
def match_sermon_to_sessions(
    sermon: SermonInfo,
    sessions: tuple[SessionInfo, ...],
    existing_links: tuple[SermonLink, ...],
    rejected_session_ids: frozenset[int],
) -> MatchDecision: ...
```

Orchestrator (`apply_match_decision`) wraps in `BEGIN IMMEDIATE` to prevent races against UI rejections.

### 4.3 Triggers

- Sermon transitions to `transcript_ready` with parseable passage
- `source_version` bumps
- A session's `last_homiletical_activity_at` updates AND an unlinked sermon with matching passage exists within 30 days
- Manual "re-match" button per sermon
- Manual link via UI (creates `active` + `manual`)
- Manual unlink (flips to `rejected`)

### 4.4 Pattern query scope

- **Queries that need prep context** (outline fidelity, outline additions/omissions) join through `sermon_links WHERE link_status='active'`
- **Queries that don't need prep context** (length, density, Tier 1 impact aggregates) don't join `sermon_links` — orphan sermons still contribute; SQL `AVG` ignores NULLs for outline_coverage_pct

### 4.5 Passage parsing extensions

`parse_reference()` in `tools/study.py` extended to handle:

- `"Romans 8:1-11; Romans 9:1-5"` → 2 `sermon_passages` rows
- `"Psalm 1-2"` → 1 row, `(chapter_start=1, verse_start=NULL, chapter_end=2, verse_end=NULL)`
- `"Romans 8"` → 1 row, whole chapter
- Unparseable → zero rows, `match_status='unparseable_passage'` surfaces in attention queue

Topical sermons (`sermon_type='topical'`): MVP just marks them and excludes from auto-matching. Bryan can link them manually.

---

## Section 5 — Analyzer (`sermon_analyzer.py`)

### 5.1 Pipeline (deterministic stages + one LLM pass)

```
(input: sermon row + sermon_passages + optional linked session outline)

[1] segment_transcript()         — pure, rule-based on transcript markers and timing
[2] align_with_outline()         — pure (only if linked), sections mapped to prep outline points
[3] compute_timing_metrics()     — pure, durations per section + delta vs prep plan
[4] compute_density_metrics()    — pure, Greek/Hebrew density, jargon count, density hotspots

[5] LLM RUBRIC PASS              — single claude-opus-4-6 call emitting the full three-tier JSON rubric
                                    (see §5.2)

[6] extract_flags()              — pure post-processing of LLM output + deterministic signals

write → sermon_reviews (overwrite), sermon_flags (delete + insert)
write → sermon_analysis_cost_log (LLM call metadata)
```

**No stage cache.** If the source changes, re-run the whole pipeline. 30–60 seconds, ~$0.15–$0.25. Simpler than tracking per-stage cache keys, and the cost is well inside the $5–$13/year budget.

### 5.2 The LLM rubric prompt

One structured call to `claude-opus-4-6` with the full review schema. System prompt anchors the three-tier framing and the impact-first posture. Input includes: transcript segments from stage 1, outline + prep context from stage 2 (if linked), timing + density output from stages 3-4, and the sermon metadata.

**Expected output (enforced via tool-use schema):**

```json
{
  "tier1_impact": {
    "burden_clarity": "crisp|clear|implied|muddled|absent",
    "burden_statement_excerpt": "<verbatim from transcript, or null>",
    "burden_first_stated_at_sec": 180,
    "movement_clarity": "river|mostly_river|uneven|lake",
    "movement_rationale": "<2-3 sentences>",
    "application_specificity": "localized|concrete|abstract|absent",
    "application_first_arrived_at_sec": 1860,
    "application_excerpts": [{"start_sec": 1860, "excerpt": "..."}],
    "ethos_rating": "seized|engaged|professional|detached",
    "ethos_markers": ["<observation>", "..."],
    "concreteness_score": 3,
    "imagery_density_per_10min": 4.2,
    "narrative_moments": [{"start_sec": 440, "end_sec": 520, "excerpt": "..."}]
  },
  "tier2_faithfulness": {
    "christ_thread_score": "explicit|gestured|absent",
    "christ_thread_excerpts": [{"start_sec": 2400, "excerpt": "..."}],
    "exegetical_grounding": "grounded|partial|pretext",
    "exegetical_grounding_notes": "<2-3 sentences>"
  },
  "tier3_diagnostic": {
    "length_delta_commentary": "<contextual note, not just the number>",
    "density_hotspots": [{"start_sec": 820, "end_sec": 1060, "note": "..."}],
    "late_application_note": "<if application_first_arrived_at_sec > 0.75 * duration>",
    "outline_drift_note": "<if linked session>"
  },
  "coach_summary": {
    "top_impact_helpers": ["<3 bullets on what drove impact this sermon>"],
    "top_impact_hurters": ["<3 bullets on what blocked impact this sermon>"],
    "faithfulness_note": "<one line on faithfulness dimension>",
    "one_change_for_next_sunday": "<single concrete actionable change>"
  },
  "flags": [
    {"flag_type": "late_application", "severity": "concern",
     "start_sec": 0, "end_sec": 1860,
     "section": "intro+body", "excerpt": "...",
     "rationale": "Application didn't arrive until 31:00; first 20 min was exegetical heat."}
  ]
}
```

**Cost instrumentation**: the one call writes a row to `sermon_analysis_cost_log` with input/output tokens and estimated cost.

**Retry**: on LLM failure, retry 2× with backoff. On JSON parse failure, one retry with a simplified prompt asking only for the required fields. Final failure → `sermon_reviews` row written with `NULL` for LLM-sourced fields, `sync_status='analysis_failed'`, UI shows deterministic stages' output only.

### 5.3 `homiletics_core.py` — pure rule functions

Shared constants and small rule helpers used by analyzer and (optionally) coach tools:

```python
__version__ = '1.0.0'

HOMILETICAL_PHASES = ('exegetical_point', 'fcf_homiletical',
                       'sermon_construction', 'edit_pray')

# Pure helpers analyzer uses in stages 2–4 before the LLM call
def segment_transcript(transcript_text: str, duration_sec: int) -> list[Segment]: ...
def align_segments_to_outline(segments: list[Segment],
                               outline: Outline) -> list[AlignedSegment]: ...
def compute_section_timings(segments: list[Segment]) -> dict: ...
def detect_density_hotspots(segments: list[Segment]) -> list[Hotspot]: ...
def count_jargon_terms(segments: list[Segment]) -> int: ...

# Pure rule checks the coach can also call via tool
def late_application(arrival_sec: int, duration_sec: int) -> bool:
    return arrival_sec > 0.75 * duration_sec

def corpus_gate_status(n_sermons: int) -> str:
    if n_sermons >= 10: return 'stable'
    if n_sermons >= 5: return 'emerging'
    return 'pre_gate'
```

`homiletics_core.__version__` is written to `sermon_reviews.homiletics_core_version`. If the code version bumps, downstream consumers can detect stale reviews and lazily re-analyze.

### 5.4 Analysis dispatch

After each sync run completes, the analyzer polls:

```sql
SELECT id FROM sermons
WHERE sync_status = 'transcript_ready'
   OR (sync_status = 'review_ready'
       AND source_version > (SELECT source_version_at_analysis
                             FROM sermon_reviews sr
                             WHERE sr.sermon_id = sermons.id))
LIMIT 10
```

Sermons are processed serially. No queue, no message bus.

### 5.5 Triggers

- Sermon → `transcript_ready` (sync flow moves the state; dispatch poll picks it up)
- `sermons.source_version > sermon_reviews.source_version_at_analysis` (stale)
- `homiletics_core.__version__` bump (code-level; lazy re-analysis on first view)
- Manual "reanalyze" button per sermon

### 5.6 Errors

- LLM failure after retry + fallback → partial review with deterministic fields populated, LLM fields NULL, `sync_status='analysis_failed'`
- Transcript below 1000 words → `analysis_skipped`

---

## Section 6 — Coach Agent (`sermon_coach_agent.py`)

### 6.1 System prompt structure

```
1. Identity & Voice                  — from voice_constants.py
2. Homiletical Framework             — impact/faithfulness/diagnostic tiers, concepts not prompt strings
3. Current Sermon Context            — passage, linked session, preach_date, duration
4. Pipeline Findings                 — the full sermon_reviews row, handed as a structured JSON block
5. Your Agency                       — full read access to transcript, prep session, history; if you
                                       disagree with a pipeline value, say so in chat with rationale
6. Tools                             — inventory + usage guidance
7. Longitudinal Posture              — corpus-gated rule, verbatim (see 6.3)
8. Behavioral Constraints            — no auto-initiation, one action per turn
```

### 6.2 Shared voice via `voice_constants.py`

```python
IDENTITY_CORE = """..."""
HOMILETICAL_TRADITION = """..."""
VOICE_GUARDRAILS = """..."""
```

Both `companion_agent.py` (prep) and `sermon_coach_agent.py` (retrospective) import these. Voice drift is prevented by single source of truth.

### 6.3 Corpus-gated longitudinal rule (verbatim in the prompt)

```
LONGITUDINAL POSTURE — YOU MUST FOLLOW THIS:

The system has analyzed N sermons. The current corpus gate is: {corpus_gate_status}

If corpus_gate_status == 'pre_gate' (fewer than 5 recent sermons):
  - You may NOT use any of these words: "pattern", "persistent", "always",
    "every time", "trajectory", "tendency", "habit", "consistently".
  - You may ONLY describe what you see in this specific sermon.
  - If Bryan asks about patterns, say: "I don't have enough corpus yet to
    speak to patterns — I need at least 5 recent sermons before I can. What
    I see in THIS sermon is ..."

If corpus_gate_status == 'emerging' (5-9 recent sermons):
  - You may say "emerging pattern" when ≥3 of the last 5 sermons share the
    same dimension in the same direction.
  - You may NOT say "persistent" or "always" or "stable pattern."
  - Always label: "emerging observation across the last 5 sermons..."

If corpus_gate_status == 'stable' (10+ recent sermons):
  - Full longitudinal voice is available.
  - Always label observations explicitly: "current-sermon observation",
    "historical pattern", or "trajectory".
  - Never conflate the three.

This rule is non-negotiable. Violating it damages Bryan's trust in the system.
```

The prompt always includes the current `corpus_gate_status` from `sermon_trends_recent`.

### 6.4 Tools

Reused from `companion_tools.py`:
- `read_bible_passage`, `lookup_lexicon`, `lookup_grammar`, `find_commentary_paragraph`

**NEW** in `sermon_coach_tools.py`:

| Tool | Purpose |
|---|---|
| `get_sermon_review(sermon_id)` | Full `sermon_reviews` row |
| `get_sermon_flags(sermon_id)` | All flags |
| `get_transcript_full(sermon_id, start_sec?, end_sec?)` | Raw transcript slice |
| `get_prep_session_full(session_id)` | Outline + card responses + homiletical-phase messages |
| `pull_historical_sermons(n, filter_expr?)` | N prior sermons + their reviews (for cross-sermon depth) |
| `get_sermon_patterns(window?)` | Aggregate row from `sermon_trends_recent` including `corpus_gate_status` |

**Not in MVP:** `lookup_homiletics_book`, `override_metric`, `request_reanalysis`, `compare_outline_to_transcript`, `save_coach_note`. Coach can still mention Chapell/Robinson from training knowledge; dedicated library tool comes in Phase 2. Coach disagreements become ordinary assistant turns in `sermon_coach_messages`. Reanalysis is triggered by a UI button, not by the coach directly.

### 6.5 Interaction model

- **Entry point 1 — from Review page**: coach greets with a narrated summary of the Impact / Faithfulness / Diagnostic / Prescription cards. Opens with the `one_change_for_next_sunday` framed as a conversation opener.
- **Entry point 2 — flag click**: coach opens focused on that moment, calls `get_transcript_full(start_sec, end_sec)`, narrates from the flag's rationale.
- Coach never auto-initiates.

### 6.6 Streaming + persistence

Same SSE + `anthropic.Client.messages.stream` pattern as `companion_agent.py`. Messages persist to `sermon_coach_messages` at each turn. `conversation_id` groups turns (one conversation per sermon, extended as Bryan returns over weeks).

---

## Section 7 — UI

### 7.1 `/sermons/<id>` — authoritative review page

Single canonical page per sermon. The Review tab inside `study_session.html` is a shortcut when a link exists; both surfaces render the same partials. Historicals, orphans, and unlinked sermons live solely at `/sermons/<id>`.

**Four-card layout:**

```
┌─ IMPACT ─────────────────────────────────────────────────┐
│  Burden:        CLEAR   "You stated the big idea at 2:58:│
│                         'Paul's no-condemnation is real  │
│                         because Jesus took the full..."  │
│  Movement:      RIVER   Arc was coherent; transitions    │
│                         felt natural through §3.         │
│  Application:   ABSTRACT arrived at 31:00 of 38:42       │
│  Ethos:         ENGAGED                                  │
│  Concreteness:  3 / 5   4.2 images per 10 min             │
│                                                          │
│  What helped:                                            │
│   ✓ Burden stated early and restated at 15:00            │
│   ✓ Personal confession at 24:15 earned the turn         │
│   ✓ Narrative at 7:40 carried the theological weight     │
│                                                          │
│  What hurt:                                              │
│   ⚠ Application arrived at 31:00 — 81% through.          │
│     Hearers were in exegesis mode for 20 min with no     │
│     concrete pressure on their week.                     │
│   ⚠ Abstract application ("we should trust the gospel")  │
│     — no specific image of WHO or WHEN.                  │
│   ⚠ Density spike in §2 held the genitive for 4 min      │
└──────────────────────────────────────────────────────────┘

┌─ FAITHFULNESS ───────────────────────────────────────────┐
│  Christ Thread:    GESTURED  Implied in §1, explicit in  │
│                              close. Didn't land mid-body.│
│  Exegetical:       GROUNDED  Text is the sermon's center;│
│                              not pretext.                │
└──────────────────────────────────────────────────────────┘

┌─ DIAGNOSTIC ─────────────────────────────────────────────┐
│  Length:    38:42  /  28:00 planned   +10:42             │
│             Length hurts here because application came   │
│             late — cut §2 Greek hold by 2 min + start    │
│             application at 22:00 = 31:00 sermon.         │
│  Section timings: intro 02:15 · body 28:30 · app 05:20   │
│                    · close 02:37                         │
│  Outline fidelity: 83%  (added: families; omitted: v.7   │
│                          participle)                     │
│  Density hotspots:  §2 [13:40–17:20] genitive hold        │
└──────────────────────────────────────────────────────────┘

┌─ FOR NEXT SUNDAY ────────────────────────────────────────┐
│  Start your application at the 22-minute mark, not 31.   │
│  Cut the §2 Greek hold to a single sentence summary.     │
└──────────────────────────────────────────────────────────┘

[🎙 open coach conversation]
```

**Page states:**

| State | Triggered by | Rendering |
|---|---|---|
| `no_link` | Match ran, no matches | All four cards render; Outline fidelity shows "no linked session" |
| `candidates_pending` | Tier 2 candidates exist | Candidate list at top + partial review below |
| `transcript_pending` | `sync_status='synced_metadata'` | "Transcript still processing" |
| `analysis_pending` | `sync_status='analysis_pending'` | "Analysis queued" |
| `analysis_running` | `sync_status='analysis_running'` | "Analysis in progress..." |
| `review_ready` | All stages succeeded | Full four-card render |
| `analysis_failed` | LLM retries exhausted | Deterministic cards + error banner + retry button |
| `unreviewable` | `sermon_type='topical'` or transcript < 1000 words | Metadata + transcript only, no review cards |

### 7.2 Review tab inside `study_session.html`

New tab peer to the existing prep surface. Visible when the session has an `active` sermon link OR `candidate` pending. Renders the same partials as `/sermons/<id>`.

### 7.3 Cross-session routes

| Route | Purpose |
|---|---|
| `GET /sermons/` | List of all sermons, sortable, attention-queue badge |
| `GET /sermons/<id>` | Authoritative review page |
| `POST /sermons/sync` | Manual sync trigger |
| `POST /sermons/backfill?limit=24` | One-shot historical backfill |
| `POST /sermons/<id>/reanalyze` | Manual reanalysis |
| `POST /sermons/<id>/link/<session_id>` | Manual link (creates `active` + `manual`) |
| `POST /sermons/<id>/unlink` | Flip active link to `rejected` |
| `POST /sermons/<id>/approve-candidate/<link_id>` | Promote candidate to active |
| `GET /sermons/patterns` | Trends from `sermon_trends_recent` with corpus_gate_status |
| `GET /sermons/sync-log` | Debug view + cost log totals |
| `POST /sermons/<id>/coach/message` | Coach chat turn (SSE) |

### 7.4 Badge logic

```sql
-- Badge fires when:
sermon.sync_status = 'review_ready'
AND sermon.source_version > sermon.ui_last_seen_version
```

On opening the review page, compare-and-set:

```sql
UPDATE sermons
SET ui_last_seen_version = source_version
WHERE id = :sermon_id AND ui_last_seen_version < source_version;
```

Simpler than the composite signature — good enough for a single-user Mac. If rubric version bumps become a real MVP pain point, Phase 2 upgrades the signature.

### 7.5 HTMX + SSE

Same infrastructure as existing prep UI. New partials:

```
templates/partials/
├── sermon_impact_card.html
├── sermon_faithfulness_card.html
├── sermon_diagnostic_card.html
├── sermon_prescription_card.html
├── sermon_flag_list.html
├── sermon_coach_chat.html
└── sermon_candidates_list.html

templates/sermons/
├── list.html
├── detail.html
├── patterns.html
└── sync_log.html

static/
├── sermons.css
└── sermons.js
```

Dark theme matches `companion.css` / `study.css`.

### 7.6 `/sermons/patterns` trend view

Shows `sermon_trends_recent` as trend cards. Corpus gate status displayed prominently:

- **Pre-gate (< 5 sermons)**: grey-toned; "Not enough corpus yet. Need N more sermons to start speaking about patterns."
- **Emerging (5-9)**: yellow-toned; trend lines visible with "emerging observation" labels.
- **Stable (10+)**: full color; "persistent pattern" language permitted.

Each of the five Tier 1 dimensions + the four Tier 3 diagnostics gets a small card with the rolling rate and a sparkline across the window.

---

## Section 8 — Error handling

Consolidated recovery matrix:

| Layer | Failure | Recovery |
|---|---|---|
| Ingest | API 429/5xx/timeout | In-run retry + SQL cooldown + `permanent_failure` at `failure_count ≥ 5` |
| Ingest | API 401/403 | Abort run, alert on `/sermons/sync-log` |
| Ingest | Concurrent run | File lock returns 409 for manual; cron skips silently |
| Ingest | Process crash | File lock released by OS; next run picks up |
| Match | Unparseable passage | `match_status='unparseable_passage'` in attention queue |
| Match | Race with UI rejection | `BEGIN IMMEDIATE` |
| Analyze | LLM failure | Retry 2× + simplified fallback prompt → partial review with deterministic fields only |
| Analyze | JSON parse | Retry simplified prompt → partial review |
| Analyze | Transcript too short | `analysis_skipped` |
| Analyze | Crash | Next dispatch poll picks it up again |
| Coach | Tool error | Coach narrates recovery |
| UI | Page crash | Flask 500 logged; friendly error with retry link |

No separate health dashboard in MVP — `/sermons/sync-log` is the operational surface.

---

## Section 9 — Testing

### 9.1 Unit tests

| File | Coverage |
|---|---|
| `test_sermonaudio_sync.py` | Classification (speaker + eventType + heuristic), hash computation, upsert logic, state transitions, file lock, error classification |
| `test_sermon_passages.py` | Multi-range parsing, chapter span parsing, whole-chapter parsing, unparseable |
| `test_sermon_type_topical.py` | Matcher excludes topical sermons; analyzer skips them with `sermon_type='topical'` |
| `test_sermon_matcher.py` | 20+ scenario tests over Tier 1/2/3 rules, re-match behavior, manual-link stickiness, `BEGIN IMMEDIATE` race, historical cutoff |
| `test_sermon_analyzer.py` | Pure stages (1–4); LLM stage with `CannedLLMClient`; full rubric schema validation; partial-review fallback on LLM failure |
| `test_homiletics_core.py` | Segmentation, alignment, timing, density hotspots, `corpus_gate_status`, `late_application` |
| `test_sermon_coach_agent.py` | Prompt assembly with `voice_constants`; corpus-gated longitudinal rule enforcement (prompt sanity check) |
| `test_sermon_coach_tools.py` | Each new tool: read access, `get_sermon_patterns` returns `corpus_gate_status` |

### 9.2 Integration tests

| File | Coverage |
|---|---|
| `test_sermon_pipeline_end_to_end.py` | Mock SermonAudio → sync → match → analyze → read review; asserts state transitions |
| `test_sermon_rematch_flow.py` | Create sermon, no session. Create session later. Assert auto-match fires. Update session with non-homiletical write (no churn). Create competing session (ambiguity → candidate). |
| `test_sermon_source_change_flow.py` | Sermon analyzed → source_version bumps → dispatch poll picks up → re-analyze → badge re-fires |

### 9.3 E2E Playwright

- Manual sync: click "Sync now" → mocked new sermon → badge on session card
- Review page render: open `/sermons/<id>` → four cards render → coach chat opens → coach responds
- Candidate approval: approve candidate → link flips to active → pattern view updates
- Trends page: open `/sermons/patterns` → corpus gate status visible → trend cards render

### 9.4 Backtest harness

`scripts/backtest_matcher.py` runs the matcher over the last-24 backfilled sermons + real sessions and writes a CSV for eyeball audit. Same shape as the existing e2e-tests backtest script.

### 9.5 LLM test doubles

```python
class LLMClient(Protocol):
    def call(self, prompt: str, schema: dict) -> dict: ...

class CannedLLMClient:
    def __init__(self, fixtures: dict): self.fixtures = fixtures
    def call(self, prompt, schema):
        key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return self.fixtures.get(key, {'error': 'no canned response'})
```

Analyzer takes an `LLMClient` via dependency injection. Unit tests pass `CannedLLMClient`; live-API tests are marked `@pytest.mark.live_api` and excluded from CI.

---

## Operational costs

| Category | Estimate |
|---|---|
| CPU | ~0% idle; brief spikes during sync and analysis |
| Memory | +30 MB baseline; +50 MB peak during active sync |
| Disk | +20–30 MB one-time for last-24 backfill; +5 MB/year ongoing |
| Network | ~5 MB per steady-state sync; ~25 MB one-time for backfill |
| LLM API | ~$0.15–$0.25 per sermon (single combined Opus 4.6 call); ~$4–$6 for last-24 backfill; ~$8–$13/year ongoing |
| Other apps on this Mac | No meaningful impact |

Cost telemetry persisted per call in `sermon_analysis_cost_log`; rolling totals visible on `/sermons/sync-log`.

---

## What is explicitly NOT in MVP (Phase 2+ appendix)

The following were specified in detail in the pre-pruned design and are deliberately deferred. Each represents real future value but is not essential for the core weekly coaching loop.

### Deferred Phase 2 features

1. **Override system** — structured `sermon_overrides` table with supersession chain, `effective_value` rule, `sermon_effective_review` view composing pipeline + override. Phase 2 adds this only if "coach disagrees" becomes a recurring pattern that chat-only narration can't handle.

2. **Per-metric provenance** — `sermon_review_provenance` table + UI popovers showing which stage, which model, which input hash produced each metric. Adds auditability; defer until debugging pressure demands it.

3. **Content-addressed stage cache** — `sermon_analysis_cache` keyed on input hashes for partial re-runs. MVP re-runs the full pipeline on any source change; at one sermon/week this is cheap.

4. **Frozen prep snapshots** — `sermon_prep_snapshots` table preserving an immutable snapshot of the linked session at analysis time. MVP accepts that later edits to the session can change re-analysis inputs; this matters more when you have 50+ sermons and want to audit rubric drift.

5. **Bootstrap resumability** — `sermon_sync_checkpoint` table for resumable page-by-page bulk import. MVP backfill is last-24 and idempotent-upsert-safe; click the button again if it fails.

6. **Lease-based locking with heartbeat** — atomic `sync_lock` table with heartbeat thread. MVP uses file-based `fcntl.flock`.

7. **Cross-session `/sermons/coach`** — standalone coach chat surface without a specific sermon in context. MVP coach lives inside a sermon's Review page. The "nice but unnecessary" surface earns inclusion when Bryan actually finds himself wanting it.

8. **`lookup_homiletics_book` tool** — Chapell/Robinson/Beeke/Piper library lookup via the existing ResourceIndex. MVP coach cites these from training knowledge when relevant but doesn't have a dedicated tool.

9. **Runtime `event_type_classification` table** — UI approval flow for unknown eventTypes. MVP hardcodes `SERMON_EVENT_TYPES` and `DEVOTIONAL_EVENT_TYPES` as Python constants.

10. **Review history / `sermon_review_history`** — append-only snapshots of reviews on each overwrite. Useful for debugging rubric drift; not needed before you've changed the rubric.

11. **Standalone `sermon_coach_notes`** — persistent coach notes beyond conversation history. MVP folds this into conversation messages.

12. **Composite badge signature** — `review_signature = sha256(source_version || analyzer_version || homiletics_core_version)` so rubric bumps re-notify. MVP uses source_version alone; if you find yourself missing rubric reanalysis notifications, Phase 2 adds this.

13. **Health dashboard** — `/sermons/health` with per-status counts, attention queue depth, last runs. MVP has `/sermons/sync-log` only.

14. **Deep sweep** — weekly Sunday-night 180-day sweep as insurance against `updated_since` filter gaps. MVP relies on primary filter + manual "resync" button.

15. **Full 356-sermon historical backfill** — MVP backfills last-24 (~6 months). If pattern tracking wants deeper baseline, an explicit button runs "extend backfill" for another 24 at a time.

16. **Topical sermon analysis** — MVP marks topical and excludes from auto-analysis. Phase 2 adds a topical-friendly analyzer variant.

17. **Cost ceiling** — per-day LLM spend cap that pauses analysis if exceeded. MVP trusts the scope of last-24 backfill + weekly single sermon.

18. **Classification review UI** — surface unknown eventTypes for one-click approval. MVP watches in `/sermons/sync-log`.

19. **Coach-initiated reanalysis** — `request_reanalysis` tool for the coach. MVP only supports manual UI-driven reanalysis.

### Why this split

The MVP is ~60% of the pre-pruned design by surface area and ~30% by implementation complexity. The cuts protect the weekly coaching loop from getting delayed by engineering that doesn't yet have a user-demonstrated need. If any Phase 2 feature proves essential after 4-6 weeks of real use, it earns a place — and by then, the coach's weekly report is already helping Bryan preach shorter, clearer, warmer, and more pointedly.

---

## References

- **CLAUDE.md** — project instructions
- **`companion_agent.py`** — prep-side voice (shared via new `voice_constants.py`)
- **`companion_db.py`** — existing schema (new tables attach via FKs; one `ALTER` on `sessions`)
- **`companion_tools.py`** — tools reused by coach
- **`tools/study.py`** — `parse_reference()` extended for multi-range + chapter spans
- **SermonAudio API v2** — https://api.sermonaudio.com/ (key auth, `sermonaudio` PyPI package)
- **Codex adversarial review trail** — 5 rounds over the pre-MVP design; critiques drove the major revisions
- **Outside consultant rounds** — 2 rounds: first round cut the overbuilt machinery; second round reframed the metric set around impact predictors (Tier 1) separated from faithfulness (Tier 2) and diagnostic symptoms (Tier 3), and introduced corpus-gated longitudinal claims based on stylometry research
