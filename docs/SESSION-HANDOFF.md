# Session Handoff: Sermon Coach MVP Live + Analysis Running

**Date:** 2026-04-16
**Status:** Sermon coach merged to main. 33 sermons synced, reanalysis in progress with full transcripts.

## What Was Done This Session

### Codex Adversarial Review
- Ran codex (gpt-5.4) against entire `feat/sermon-coach-mvp` branch
- Found 3 critical + 5 important bugs, all fixed in commit `e73a307`:
  - Coach streaming broken (missing `stream_message()` on AnthropicClient)
  - Tool-use loop never fed results back to model (bounded at 5 rounds now)
  - Sync routes bypassed file lock (now routed through `run_sync()`)
  - Manual link could 500 on partial unique index
  - Analyzer could strand rows in `analysis_running`
  - Reanalyze race (conditional UPDATE)
  - SQL injection in `get_sermon_patterns` (parameterized)

### API Key Migration to macOS Keychain
- Created `tools/workbench/app_secrets.py` — Keychain-first, env-var-fallback
- Updated all 9 callsites across `app.py`, `companion_agent.py`, `workbench_agent.py`
- Bryan stored all 3 keys in Keychain Access (verified working)
- `keyring` package installed with macOS Keychain backend

### SermonAudio Integration Fixes
- API returns rich model objects, not flat dicts — added `normalize_remote()` adapter
- Transcript is SRT caption behind auth — uses library's authenticated session to fetch + strip timestamps
- Classification fix: Sunday Service < 20min → skipped (catches mistagged devotionals)
- Synced 200 sermons (page 1 + page 2), 33 classified as real sermons

### Analysis Pipeline Fixes
- `dispatch_pending_analyses()` now auto-runs after sync/backfill/cron (was missing)
- Transcript truncation bug: segments were capped at 400 chars — LLM only saw 1% of transcript. Fixed.
- Reanalysis running with full transcripts (was at 10/33 when session ended)

## Fixed This Session

### 1. Coach chat history restored on page navigation (was bug #1)
- Added `GET /sermons/<id>/coach/history` endpoint returning persisted messages as JSON
- Frontend JS fetches and renders history on DOMContentLoaded
- Submit button disabled until history loads (prevents race condition with first message)
- Codex review: added try/except on `conversation_id` parsing to prevent 500s on bad input

### 2. Coach transcript no longer causes timeouts (was bug #2)
- Full transcript injected into the system prompt (coach already has it in context)
- Tool renamed from `get_transcript_full` to `get_transcript_excerpt` — now requires `start_sec` + `end_sec` (time slicing only)
- Added 50K char truncation cap on transcript in system prompt as safety net
- Codex review: confirmed Opus 200K context handles 25K chars (~7K tokens) with plenty of room

### 3. SermonAudio API auto-pagination (was bug #4)
- `list_sermons_updated_since()` now loops through pages using `page` param and `next_url`
- Stops when batch < page_size or no `next_url`, respects overall `limit`
- Codex review: fixed TypeError fallback to preserve `since` filter (was silently dropped)

## Known Bugs to Fix Next Session

### 1. Patterns page needs interactive meta-coach
`/sermons/patterns` currently shows aggregate stat cards only. Bryan wants:
- A chat interface on this page (like the per-sermon coach but corpus-scoped)
- Coach sees aggregate data and can drill into specific sermons
- Pull best examples and worst examples to help develop his homiletic
- This is the "where the metacoaching happens" page

## Commits on Main Since Merge
```
878be7a fix: send full transcript to LLM, not 400-char truncated segments
645ab83 fix: auto-run analysis after sync/backfill/cron  
71b8a29 fix: skip Sunday Service entries under 20min (mistagged devotionals)
e76864c fix: normalize SermonAudio API objects + auth caption fetch
74c7487 Merge feat/sermon-coach-mvp: sermon coach MVP
```

## State When Stopped
- 33 sermons classified as real sermons
- Reanalysis in progress (~10/33 done, rest finishing in background)
- PM2 `study-companion` process running with latest code
- All 3 API keys in macOS Keychain (verified)
