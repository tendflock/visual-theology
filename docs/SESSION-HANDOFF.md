# Session Handoff: Coaching Bridge + Rubric Refinement Live

**Date:** 2026-04-17 (afternoon)
**Status:** Full coaching bridge operational. Rubric refined with behavioral anchors. 33 sermons analyzed, system end-to-end functional.

## What Was Built Across Sessions (2026-04-16 — 2026-04-17)

### Codex Branch Review + MVP Bug Fixes
- 3 critical + 5 important bugs found and fixed in sermon coach MVP
- Coach streaming fixed (missing `stream_message()`, tool-use loop, TextBlock serialization)
- Sync race fixed (file lock bypass), manual link 500 fixed, analyzer stranding fixed

### API Key Migration to macOS Keychain
- `app_secrets.py` shim (Keychain-first, env-var-fallback)
- All 9 callsites migrated, all 3 keys verified in Keychain Access

### SermonAudio Integration
- `normalize_remote()` adapter for rich API model objects
- Authenticated SRT caption fetch, classification fix (< 20min), cross-chapter range parsing
- API auto-pagination, 33 sermons synced and classified from 200 fetched

### Sermon Matcher Wired Into Pipeline
- `dispatch_matching()` integrated: sync → match → analyze
- Was never called — every sermon was 'unmatched'. Now 3 auto-linked.

### Analysis Pipeline Fixes
- Transcript truncation bug fixed (LLM was seeing 1% of transcript)
- Auto-analysis after sync/backfill/cron (was missing)
- 33 sermons fully analyzed

### Meta-Coach System (built in prior session)
- SRT parser, sermon tagger (535 moments), priority ranker
- 11 corpus-scoped tools, streaming meta-coach agent
- Coaching commitments with partial unique index
- Patterns page chat widget with canned prompts

### Coaching Bridge (spec + 8-task implementation)
- **Spec:** `docs/superpowers/specs/2026-04-17-coaching-bridge-design.md`
- **Plan:** `docs/superpowers/plans/2026-04-17-coaching-bridge.md`
- **New file:** `tools/workbench/coaching_bridge.py`
- **New tables:** `coaching_insights`, `session_coaching_exposure`
- **5 coaching tools** added to study companion
- **Retrieval policy** with escalation ladder (5 levels) + anti-nagging rules
- **Transition question:** "Are we still exploring the text, or are we shaping the sermon now?"
- **linked_session_id** wired into per-sermon coach (was dead code)
- **Save buttons:** "Save as coaching note" + "Save as commitment" on coach chat UIs
- Codex reviewed every task — 6 findings addressed

### Rubric Refinement (informed by SermonScore.ai comparison)
- Deep prompt restructuring: behavioral anchors, decision rules, disqualifiers
- Evidence-first scoring: every dimension requires evidence + "why not scored higher"
- New dimension: `opening_tension` (strong/adequate/weak/absent)
- New dimension: `application_landing` (pressed/touched/gestured/missed)
- New field: `per_dimension_growth_edges`
- Reanalyzed Romans 2:17-29 — calibration visibly improved

### PR Review
- 299/299 tests pass (43 pre-existing auth test failures)
- Connection leak in create_commitment fixed
- MorphGNT book number bug noted (pre-existing, not from this session)

## Current State

- **33 sermons** synced, classified, analyzed (1 with refined rubric, 32 with old)
- **1 active commitment:** "Tuesday at 10am" test for application specificity
- **1 coaching insight** saved: application inconsistency on abstract texts
- **Study companion** has full coaching bridge active
- **PM2 `study-companion`** running with latest code
- **All 3 API keys** in macOS Keychain

## Known Issues

### 1. MorphGNT word study book number conversion (pre-existing)
`_word_study_lookup` passes Logos native book numbers (61-87 for NT) to MorphGNT which uses Protestant numbering (40-66). One-line fix: use `_logos_to_protestant_book()`.

### 2. Old route tests failing (43 tests, pre-existing)
`test_routes.py` and `test_study_routes.py` don't set `session['authenticated'] = True`.

### 3. Reanalyze corpus with refined rubric
32 sermons still have old-rubric reviews. ~$16 and ~15 minutes.

### 4. Calibration research (scoped, not started)
Scope: `docs/superpowers/ideas/2026-04-17-sermon-calibration-corpus.md`
Build corpus of "great" sermons from Bryan's Logos library, run differential analysis against his sermons, rebuild rubric from calibrated metrics.

## Key Architecture

```
Study Companion ←──coaching_bridge.py──→ Sermon Coach System
     ↓                                         ↓
build_study_prompt()                    sermon_analyzer.py
  + coaching_context                      (refined rubric)
  + 5 coaching tools                         ↓
  + retrieval policy                    sermon_tagger.py
  + escalation ladder                     (sermon_moments)
  + anti-nagging rules                       ↓
                                        meta_coach_agent.py
                                          (priority ranking)
                                             ↓
                                        coaching_commitments
                                        coaching_insights
```
