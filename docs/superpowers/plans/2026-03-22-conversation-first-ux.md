# Conversation-First UX — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the card-based quiz UI with a conversation-first study experience where the AI is Bryan's graduate assistant — one screen, one thread, outline sidebar, behavioral analytics.

**Architecture:** New `/study/` routes alongside existing `/companion/` routes (no breaking changes). Reuses existing backend: CompanionDB, companion_agent.py streaming loop, companion_tools.py tool dispatch. New frontend: study.css, study.js, study templates. New: session_analytics.py for behavioral tracking.

**Tech Stack:** Python/Flask (existing), Jinja2 templates, vanilla JS (no framework), SSE streaming (existing), SQLite (existing), CSS custom properties

**Spec:** `docs/superpowers/specs/2026-03-22-conversation-first-ux-design.md`

**Environment Setup (required for all tasks):**
```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:/opt/homebrew/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

**Test runner:** `/opt/homebrew/bin/python3 -m pytest` from `/Volumes/External/Logos4/tools`

**Security note:** Use textContent or safe DOM methods when rendering user input in JS. Only use innerHTML for pre-sanitized server content. Tool results should be escaped before display.

---

## File Structure

### New files:
```
tools/workbench/
├── static/
│   ├── study.css                  — Conversation-first dark theme, outline sidebar, rich blocks
│   └── study.js                   — SSE streaming, word popups, outline drag/edit, analytics client
├── templates/
│   ├── study_start.html           — Session start / resume page
│   └── study_session.html         — Main conversation + outline view
├── session_analytics.py           — Behavioral tracking: phase time, message patterns, stall detection
└── tests/
    ├── test_study_routes.py       — Route tests for /study/ endpoints
    └── test_session_analytics.py  — Analytics tracking + query tests
```

### Modified files:
```
tools/workbench/
├── app.py                         — Add /study/ routes
├── companion_agent.py             — Add conversation-first system prompt builder + study streaming
```

---

## Task 1: Analytics Database Schema

**Files:**
- Create: `tools/workbench/session_analytics.py`
- Create: `tools/workbench/tests/test_session_analytics.py`

Steps: Write tests for phase time tracking, message recording, outline saves, stall detection, and cross-session patterns. Implement SessionAnalytics class with SQLite tables. All tests pass. Commit.

---

## Task 2: Study Routes + Templates + CSS + JS

**Files:**
- Modify: `tools/workbench/app.py` — add /study/ routes
- Create: `tools/workbench/templates/study_start.html`
- Create: `tools/workbench/templates/study_session.html`
- Create: `tools/workbench/static/study.css`
- Create: `tools/workbench/static/study.js`
- Create: `tools/workbench/tests/test_study_routes.py`

This is the largest task — the full frontend. Routes mirror companion endpoints but under /study/. The CSS implements the dark theme conversation UI with outline sidebar. The JS handles SSE streaming, rich content block rendering, outline CRUD, session clock, and wellbeing nudges.

Key JS architecture:
- handleSSEEvent dispatches text_delta, tool_start, tool_result, error, done events
- renderToolResult formats library quotes, scripture blocks, cross-ref clusters, and insight pills using safe DOM methods (textContent for user content, structured HTML for server content)
- Outline loads via JSON API and renders as nested tree
- Session clock counts up (not down) showing duration
- Wellbeing nudges at 2h and 4h marks

---

## Task 3: Conversation-First System Prompt + Streaming

**Files:**
- Modify: `tools/workbench/companion_agent.py`
- Modify: `tools/workbench/app.py` (update import + route)

Add `build_study_prompt()` — emphasizes graduate assistant role, proactive research, invisible phase steering. No references to cards or visible phases. Includes wellbeing note when session exceeds 2 hours.

Add `stream_study_response()` — uses full conversation history (not phase-scoped), builds messages from all history for natural multi-session flow. Update /study/ discuss route to use it.

---

## Task 4: Nudge Element + Final Polish

**Files:**
- Modify: `tools/workbench/templates/study_session.html`

Add wellbeing nudge element. Run full test suite. Manual test at http://localhost:5111/study/.

---

## Dependency Graph

```
Task 1 (Analytics)
  └→ Task 2 (Routes + Templates + CSS + JS)
       └→ Task 3 (System Prompt + Streaming)
            └→ Task 4 (Nudge + Polish + Manual Test)
```

All tasks are sequential.

## Post-Implementation Verification

1. Open http://localhost:5111/study/
2. Enter "Romans 1:18-23"
3. AI should open proactively with a substantive first move about the text
4. Ask "What's the main verb in v.18?" — AI should answer + pull grammar reference
5. Say "Pull up EDNT on ἀποκαλύπτω" — AI should use lookup_lexicon and show a library block
6. Check outline sidebar grows as conversation progresses
7. After 2+ hours, wellbeing nudge should appear
8. Visit http://localhost:5111/companion/ — old UI still works
