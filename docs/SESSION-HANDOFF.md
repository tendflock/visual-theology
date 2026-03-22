# Session Handoff: Sermon Study Companion

**Date:** 2026-03-21
**Status:** Design complete, implementation plan written, ready to build.

## What This Is

We're building a sermon study companion for Bryan Schneider, a Reformed Presbyterian pastor with ADHD who preaches weekly. The companion walks him through a 12-phase sermon prep workflow one question at a time, with an AI study partner that challenges his thinking, surfaces resources from his Logos 4 library, and coaches the transition from exegesis to homiletics.

## The Problem It Solves

Bryan has a 16-step sermon prep workflow he's used 47+ times. But:
- Seeing all 16 steps with sub-questions triggers ADHD overwhelm and procrastination
- He stalls when steps feel too big or he hits exegetical walls
- He goes down commentary rabbit holes (700 pages) without knowing what questions to answer
- His sermons run 40 min instead of target 25-30 min
- His wife says they're too exegetically dense — Christ gets pushed to a final application instead of woven throughout
- He struggles with the bridge from exegesis to homiletics

## The Solution

A web app (Flask, HTMX, Claude API) with:
- **Card-based UI** — one question at a time, no visible mountain of steps
- **Discussion mode** — click "Discuss" to open a streaming conversation with the companion (Claude) who knows his library, challenges weak exegesis, and surfaces commentary paragraphs with summary + highlights
- **Homiletical coaching** — "So What?" gate on every outline point, Christ-thread check at every main point, time estimator that flags outlines over 30 min
- **Outline builder** — builds incrementally from his work, exportable as printable PDF matching the format he actually preaches from
- **Timers** — per-phase countdown, auto-pause on inactivity, gentle nudges to stay on track

## Key Documents

| Document | Path | Purpose |
|----------|------|---------|
| **Design Spec** | `docs/specs/2026-03-21-sermon-companion-design.md` | Complete design — UX, backend, database schema, error handling, cost model |
| **Implementation Plan** | `docs/plans/2026-03-21-sermon-companion-plan.md` | 12 tasks with TDD steps, code samples, file paths, dependency graph |
| **Methodology / Question Bank** | `docs/research/exegetical-methodology.md` | 113 exegetical questions across 12 phases (source for question bank seeding) |
| **Workflow Template** | `docs/workflow_template.json` | Bryan's original 16-step Logos workflow (JSON) |

## Key User Context

Read these memory files for full context:
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/user_bryan.md` — who Bryan is, ADHD, workflow habits
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/user_preaching_style.md` — his pulpit outline format, verse-by-verse, question-driven
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/user_theological_prefs.md` — Reformed/Presbyterian, Westminster Standards only, fathers pre-600 AD
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/feedback_companion_voice.md` — engaged peer + direct coach, not a yes-man
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/feedback_clear_questions.md` — steps need specific answerable questions, not vague instructions
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/feedback_commentary_display.md` — summary + full paragraph with highlights, not digested summaries
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/feedback_exegesis_to_homiletics.md` — core struggle, companion must coach the homiletical side
- `/Users/family/.claude/projects/-Volumes-External-Logos4/memory/feedback_docs_location.md` — docs go in project folder, not hidden directories

## Architecture

```
Browser (HTMX + vanilla JS)
  ↕ SSE streaming
Flask app (tools/workbench/app.py, /companion/ routes)
  ↓
companion_agent.py → Claude API (Sonnet for conversation, Haiku for commentary extraction)
  ↓
companion_tools.py → study.py → logos_batch.py → LogosReader (C# P/Invoke)
  ↓                                                    ↓
companion_db.py (SQLite)                     libSinaiInterop.dylib → .logos4 files
```

## What Already Works (Don't Touch)

- **LogosReader** (`tools/LogosReader/Program.cs`) — C# .NET 8 P/Invoke wrapper that reads encrypted .logos4 files. 1,663 lines. Works perfectly. Never modify.
- **logos_batch.py** (`tools/logos_batch.py`) — Python wrapper for persistent LogosReader subprocess. Works.
- **logos_cache.py** (`tools/logos_cache.py`) — SQLite caching for extracted text/TOC/verse indexes. Works.
- **study.py** (`tools/study.py`) — 1,662 lines. Core library access functions: `parse_reference()`, `find_commentaries_for_ref()`, `read_bible_chapter()`, `find_commentary_section()`, `get_interlinear_for_chapter()`, etc. All work. Two fixes needed: `clean_bible_text()` (strip markers instead of converting) and `parse_reference()` (raise ValueError instead of sys.exit).

## What Gets Built (New Files)

All new files go in `tools/workbench/`:

| File | Purpose |
|------|---------|
| `companion_db.py` | Database layer — sessions, card_responses, conversation_messages, outline_nodes, question_bank |
| `companion_agent.py` | Claude agent loop — 12-phase system prompt, streaming with tool use, homiletical coaching |
| `companion_tools.py` | Focused tools — `find_commentary_paragraph` (Haiku), `word_study_lookup`, `expand_cross_references`, `save_to_outline` |
| `genre_map.py` | Static book→genre mapping for question filtering |
| `seed_questions.py` | 113 questions embedded as Python data, populates question_bank table |
| `static/companion.css` | ADHD-first dark theme, card layout, discussion thread, outline drawer |
| `static/companion.js` | Timer, mode toggle, SSE client, inactivity detection |
| `templates/companion_base.html` | Minimal shell (no navbar clutter) |
| `templates/start.html` | "What are you preaching?" entry screen |
| `templates/session.html` | Main view — card + discussion + outline drawer |
| `templates/partials/card.html` | Card component — question + resource + response area |
| `templates/partials/discussion.html` | Chat-style conversation thread |
| `templates/partials/outline_drawer.html` | Slide-out outline tree |
| `templates/partials/progress_dots.html` | Phase progress dots (no numbers) |
| `templates/export.html` | Printable outline (standalone, no app chrome) |

New routes live under `/companion/` — old workbench at `/` remains untouched during development.

## Implementation Plan Summary

12 tasks, dependency graph allows parallelism on tasks 1, 2, 4, 6:

```
Task 1 (DB) ──┬── Task 3 (Questions) ──┐
              │                         │
Task 2 (Genre + Clean Text)             │
              │                         ├── Task 8 (Routes) ── Task 9 (Streaming) ── Task 12 (Integration)
Task 4 (Tools) ──── Task 5 (Agent) ─────┤
                                        │
Task 6 (CSS/JS) ── Task 7 (Templates) ──┤
                                        │
                              Task 10 (Timer) ── Task 11 (Export)
```

| Task | What | Key Detail |
|------|------|------------|
| 1 | Database layer | 5 tables: sessions, card_responses, conversation_messages, outline_nodes, question_bank |
| 2 | Genre map + study.py fixes | Fix clean_bible_text() to strip markers, fix parse_reference() to not sys.exit, add genre mapping |
| 3 | Question bank seeder | 113 questions as Python data, mapped to 12 phases with genre tags |
| 4 | Companion tools | Commentary paragraph finder (Haiku), word study, cross-ref expansion |
| 5 | Companion agent | System prompt with 7 sections, streaming with tool use, homiletical guardrails |
| 6 | CSS + JS | Dark theme, timer class, SSE client with fetch/ReadableStream, inactivity monitor |
| 7 | Templates | Card, discussion, outline drawer, progress dots |
| 8 | Flask routes | All /companion/ endpoints for card flow, discussion, outline, timer, export |
| 9 | Wire streaming | End-to-end SSE with actual client.messages.stream() and tool-use loop |
| 10 | Timer + inactivity | Auto-pause at 5 min, nudge at 10 min, persist across sessions |
| 11 | Export | Printable HTML outline matching Bryan's actual pulpit format |
| 12 | Integration testing | Smoke test, error cases, homiletical coaching verification |

## How to Execute

Start by reading the full implementation plan at `docs/plans/2026-03-21-sermon-companion-plan.md`. Use the `superpowers:subagent-driven-development` skill (recommended) or `superpowers:executing-plans` to work through tasks.

Each task has:
- Exact file paths to create/modify
- Failing tests to write first (TDD)
- Implementation code/guidance
- Test commands to verify
- Commit messages

## Environment Setup

```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
export ANTHROPIC_API_KEY="<Bryan's key>"
cd /Volumes/External/Logos4/tools/workbench
python3 app.py  # starts on port 5111
```

## Critical Design Decisions Already Made

1. **Card flow, not chat-first** — Bryan sees one question at a time. Discussion is opt-in via "Discuss" button.
2. **Local question bank, no AI for question selection** — Card transitions are instant and free. Claude only called in discussion mode.
3. **Haiku for commentary extraction, Opus for conversation** — ~$6-15 per sermon prep. Opus is worth it for seminary-level study partner quality.
4. **Build alongside, don't replace** — New /companion/ routes coexist with old / routes. Old workbench still works.
5. **No new Python dependencies** — Flask + anthropic + sqlite3. PDF export uses browser print-to-PDF.
6. **7 genres** — epistle, narrative, poetry, wisdom, prophecy, law, apocalyptic. Questions tagged for genre filtering.
7. **Commentary display: summary + full paragraph with highlights** — the companion does the finding, Bryan does the thinking. Tone: "Here's what Hodge says — see for yourself..."
8. **Timer auto-pauses at 5 min inactivity** — nudge at 10 min. Timer persists across sessions (remaining time, not wall clock).
9. **Progress shown as dots, never numbers** — Bryan never sees "step 7 of 12" or "question 3 of 8".
10. **Streaming must use client.messages.stream()** — not the synchronous-then-SSE pattern in the old workbench_agent.py.

## Known Limitations for MVP

- **Word study** uses interlinear data only (lemma, morphology, Strong's, gloss). Lexicon .logos4 reading is untested and deferred.
- **Topic-based prep** (e.g., "Spiritual warfare") is deferred — MVP handles Bible references only.
- **Westminster Standards lookup** is deferred to Priority 2.
- **Sentence diagram display** is deferred — Bryan exports from Logos as PDF for now.
- **EncryptedVolume API** (structured datasets) is deferred — documented but not built.

## Bryan's Data You Can Access

- **4,652 books** in Logos 4 library (302 Bibles, 1,025 commentaries, 49 lexicons, etc.)
- **Catalog DB**: `Data/e3txalek.5iq/LibraryCatalog/catalog.db`
- **ResourceManager DB**: `Data/e3txalek.5iq/ResourceManager/ResourceManager.db`
- **Resources**: `Data/e3txalek.5iq/ResourceManager/Resources/*.logos4`
- **Workflows DB**: `Documents/e3txalek.5iq/Workflows/Workflows.db` — 47 completed sermon preps
- **Sermon DB**: `Documents/e3txalek.5iq/Documents/Sermon/Sermon.db` — ~45 sermons with block structure
- **Notes DB**: `Documents/e3txalek.5iq/NotesToolManager/notestool.db` — 4,511 notes, 1,139 workflow-anchored
- **User ID**: 5621617

## Success Criteria

1. Bryan starts a prep session in under 30 seconds
2. He never sees more than one question at a time
3. Commentary paragraphs surfaced with summary + highlights within 5 seconds
4. The companion challenges at least one exegetical point per session
5. The companion flags outlines exceeding 30 minutes of preaching time
6. Every main point checked for Christ-connection before export
7. Bryan resumes an interrupted session within 60 seconds
8. Exported outline matches the format Bryan actually preaches from
9. Bryan's wife notices the sermons are clearer and shorter
