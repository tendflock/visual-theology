# Session Handoff: Hybrid Card→Conversation Study UI

**Date:** 2026-03-22
**Status:** Conversation-first UI built and deployed. Needs redesign as hybrid card→conversation flow based on Bryan's feedback.

## What Was Done This Session

### Conversation-First UI (BUILT, NEEDS REDESIGN)
Built and deployed the `/study/` UI:

1. **Session analytics** — `session_analytics.py` with phase time tracking, stall detection, outline velocity, silence gaps, cross-session patterns (18 tests)
2. **Study routes** — 8 new endpoints at `/study/` alongside existing `/companion/` (17 tests)
3. **Frontend** — `study.css`, `study.js`, `study_start.html`, `study_session.html` with conversation thread, outline sidebar, session clock, wellbeing nudges
4. **Study prompt + streaming** — `build_study_prompt()` and `stream_study_response()` in `companion_agent.py` with full conversation history
5. **Bible tool fix** — defaults to THGNT (NT) / BHS (OT) instead of ESV
6. **PM2 deployment** — running as `sermon-study` with venv + dotnet env vars

### Bryan's Feedback (CRITICAL — REDESIGN NEEDED)
Bryan tested the conversation-first UI and gave clear direction:

**The conversation-only approach is wrong.** Bryan needs structured cards for the first 5 phases where HE does the work, then conversation mode where the AI helps. The AI was "spoon-feeding" him instead of letting him drive.

## What the Next Session Should Do

Build the **hybrid card→conversation UI**. Steps 1-5 are cards (Bryan drives), steps 6+ are conversation (AI as interlocutor).

```
Read the feedback memories at:
  memory/feedback_hybrid_workflow.md
  memory/feedback_study_pacing.md

Then implement the hybrid /study/ UI:

CARD PHASES (Bryan drives, AI is quiet):
  1. Prayer — simple prompt, textarea for Bryan's prayer
  2. Read the text — AUTO-SHOW full THGNT (NT) / BHS (OT) passage
  3. Working translation — Bryan writes his own translation
  4. Digestion — pray through the text phrase by phrase
  5. Study Bible consultation — AUTO-PULL notes from Bryan's 7 study Bibles:
     - Ancient Faith Study Bible: Notes
     - ESV Study Bible
     - FSB (Faithlife Study Bible)
     - GB Notes (Geneva Bible Notes)
     - NIV Cultural Backgrounds Study Bible
     - NIVBTSB
     - The Reformation Study Bible

CONVERSATION PHASE (AI as interlocutor):
  6. Context / big picture
  7. Identify Christ
  8. Word study, theological analysis, commentary
  9. Exegetical point → FCF → Sermon construction

Key requirements:
- Step 2 auto-loads original language text (no button click needed)
- Step 5 auto-pulls study bible notes for the passage
- Transition from cards to conversation should be seamless
- The existing /companion/ routes must keep working
- 105 tests must continue passing
- Bryan is in the driver's seat — especially in phases 1-5
- The AI becomes an active interlocutor only at phase 6+
```

### Study Bible Resources to Find
The next session needs to locate these resources in catalog.db and verify they're readable:
- Ancient Faith Study Bible: Notes
- ESV Study Bible
- FSB (Faithlife Study Bible)
- GB Notes (Geneva Bible Notes)
- NIV Cultural Backgrounds Study Bible
- NIVBTSB
- The Reformation Study Bible

Query: `SELECT ResourceId, AbbreviatedTitle, Title FROM Records WHERE Title LIKE '%Study Bible%' AND Availability = 2`

## Key Files

| Purpose | Path |
|---------|------|
| **Study Routes + Templates** | `tools/workbench/app.py`, `templates/study_*.html` |
| **Study CSS/JS** | `tools/workbench/static/study.css`, `static/study.js` |
| **Companion Agent** | `tools/workbench/companion_agent.py` (build_study_prompt, stream_study_response) |
| **Companion Tools** | `tools/workbench/companion_tools.py` |
| **Session Analytics** | `tools/workbench/session_analytics.py` |
| **Companion DB** | `tools/workbench/companion_db.py` |
| **Existing Card System** | `tools/workbench/templates/session.html`, `static/companion.js` |
| **Feedback: Pacing** | `memory/feedback_study_pacing.md` |
| **Feedback: Hybrid** | `memory/feedback_hybrid_workflow.md` |

## Test Status

105 tests passing across 13 test files. Run with:
```bash
cd /Volumes/External/Logos4/tools
/opt/homebrew/bin/python3 -m pytest workbench/tests/ -v
```

## Server

Running under pm2 as `sermon-study`:
```bash
pm2 logs sermon-study    # view logs
pm2 restart sermon-study # restart after code changes
```

Venv at `tools/workbench/venv/` with anthropic + flask installed.
API key in `tools/workbench/.env` (Max subscription).

## Environment

```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:/opt/homebrew/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```
