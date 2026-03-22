# Sermon Study Companion — Design Spec

**Date:** 2026-03-21
**Author:** Bryan Schneider + Claude
**Status:** Draft

## Problem

Bryan is a Reformed Presbyterian pastor who preaches weekly through books of the Bible. He has ADHD, which makes the 14-hour sermon prep process feel insurmountable — especially when facing 16 steps with dozens of sub-questions. He has a battle-tested workflow (used 47+ times) but stalls when steps feel too big, when he hits exegetical walls, or when life interrupts.

His wife's feedback crystallizes the deeper issue: sermons are too long (40 min vs. 25-30 target), too exegetically dense for the congregation, and Christ gets pushed to the final application instead of being woven throughout. Bryan is excellent at exegesis but struggles with the bridge to homiletics.

Current tools (Logos 4 + manual workflow) give him no help with pacing, no accountability for time, no coaching on the exegesis-to-homiletics transition, and no way to resume interrupted work without losing momentum.

## Solution

A web-based sermon study companion that:
1. Walks Bryan through his prep workflow **one question at a time** (no visible mountain of steps)
2. Acts as an **engaged study partner + direct coach** — challenges weak exegesis, surfaces resources, and manages time
3. **Coaches the homiletical transition** — enforces the "so what?" test, the Christ thread, and preaching time estimates
4. Reads from Bryan's 4,652-book Logos 4 library programmatically
5. **Builds the sermon outline incrementally** from Bryan's work, exportable as a printable PDF

## Core Interaction Model: Card Flow with Companion

### Two States, One Screen

**Default State (Card):**
A single focused card showing:
- The current question (dynamically chosen for the passage and genre)
- Relevant resource pre-loaded (Bible text, previous translation, word study data)
- Text area for Bryan's response
- Timer for the current phase (not the whole workflow)
- Progress as small dots (completed = green, current = blue, future = dim). No numbers. No "step 7 of 12"

**Companion State (Discussion):**
Triggered by clicking "Discuss" or typing a question instead of an answer. The card slides up, conversation thread opens below. The companion:
- Answers questions ("What does Hodge say here?")
- Surfaces commentary: one-line summary of the author's position, then full paragraph(s) with key sentences highlighted
- Challenges thinking ("You said this is about grace — but what about the wrath language in v18?")
- Manages time ("Good insight. 12 minutes left — save that and move on?")
- Pulls up any resource on request

Return to card mode via "Back to questions" or when the companion suggests moving on.

**Outline Drawer:**
Slide-out panel (not always visible). Accumulates from card responses and saved conversation insights. Always editable. Always exportable.

### Frontend State Management

HTMX handles server-driven updates (card content, conversation messages, outline items). A small amount of vanilla JS manages client-side state:
- Card/discussion mode toggle (CSS class swap, no server round-trip)
- Timer countdown (client-side interval, syncs to server on phase transitions)
- Outline drawer open/close
- SSE connection for streaming companion responses

Card submission is an HTMX POST that returns the next card. Discussion messages use SSE streaming. Outline operations are HTMX POSTs with `hx-swap` to update the drawer.

## Workflow Structure: 12 Phases as Cards

Bryan's 16-step workflow maps to 12 phases (see `docs/research/exegetical-methodology.md` for the full question bank). Bryan never sees "12 phases." He sees the current phase name, a timer, and one question at a time.

### Phases and Time Budgets

This is the canonical phase list for the companion. The methodology document provides the full question bank; these phases organize when those questions are presented.

| Phase | Core Focus | Budget |
|-------|-----------|--------|
| 1. Prayer | Spiritual preparation, pray through text | 15 min |
| 2. Text Work | Translation, odd words, repetition, textual variants | 2 hrs |
| 3. Digestion | Devotional engagement, pray through each phrase | 1 hr |
| 4. Observation | Who/what/when/where/why/how, literary type, figures of speech | 1 hr |
| 5. Word Study | 2-4 key terms, semantic range, lexicon entries | 30 min |
| 6. Context | Immediate, book-level, canonical; geographic/cultural setting | 45 min |
| 7. Theological Analysis | Christ-connection (7 roads), systematic theology, fathers pre-600 AD, WCF/WLC/WSC | 2 hrs |
| 8. Commentary Consultation | Targeted questions to commentaries — not browsing | 30 min |
| 9. Exegetical Point | Subject + complement → one propositional sentence | 30 min |
| 10. FCF + Homiletical Point | Fallen Condition Focus, take-home truth, purpose statement, application categories | 30 min |
| 11. Sermon Construction | Outline, amplify, illustrate, apply — with homiletical coaching | 3 hrs |
| 12. Edit & Pray | Cut ruthlessly, land the sermon, pray over it | 1.5 hrs |

**Total: ~14 hours** (matching Bryan's existing workflow design)

### Question Selection Architecture

Each phase has a **local question bank** — the 113 questions from the methodology document, tagged by:
- **Phase** (which of the 12 phases)
- **Genre applicability** (epistle, narrative, poetry, wisdom, prophecy, law, apocalyptic)
- **Priority** (core vs. supplemental — core questions always appear, supplemental appear if time allows)

Genre detection happens once at session start: Bryan enters the reference, the system identifies the book and applies a static genre map (Romans = epistle, 1 Samuel = narrative, Psalms = poetry, etc.).

The companion presents core questions for the detected genre in order. **No Claude API call is needed for question selection.** Claude is only called when Bryan enters discussion mode. This keeps card transitions instant and costs low.

Phase completion is determined by: (a) Bryan clicks "Next phase," (b) all core questions are answered, or (c) the timer expires and the companion suggests moving on.

### Timer Behavior

- **Display:** Countdown number in the top bar, always visible in both card and discussion mode
- **On expire:** The companion sends a gentle nudge via the conversation: *"Time's up on text work. You've covered the key questions — ready to move on, or do you need 10 more minutes?"* No alarm, no forced transition.
- **Pause/resume:** Timer pauses automatically after 5 minutes of inactivity. Resumes when Bryan interacts. Total elapsed time and remaining time are stored in the database.
- **Between sessions:** Timer state persists. If Bryan closes the browser Tuesday and returns Thursday, the timer shows remaining time for the current phase, not elapsed wall-clock time.

### ADHD Re-engagement

If Bryan is inactive for 10+ minutes without closing the session, the companion sends a gentle prompt: *"Still here? No rush — when you're ready, we were looking at the main verb in v18."* This re-states where he was so he doesn't have to figure out context. After 30 minutes of inactivity, the timer auto-pauses and the companion saves state.

## Companion Personality

Three fluid modes:

**Guide mode** — presenting questions, moving through workflow. Direct, clear, one thing at a time. *"Let's look at your translation. What's the main verb in v18?"*

**Study partner mode** — in conversation discussing the text. Intellectually engaged, challenges, brings sources. *"Here's what Hodge says, see for yourself... But Murray disagrees. Where do you land?"*

**Coach mode** — managing time and momentum. Warm but firm. *"That's a great rabbit trail but it's a thesis, not a sermon point. Save it and let's come back to the FCF."*

### The companion NEVER:
- Gives a wall of text unprompted
- Shows how many steps remain
- Says "Great job!" without substance
- Writes sermon content for Bryan (it helps him think, not thinks for him)

### The companion DOES:
- Celebrate genuine insights with specificity
- Push back on weak exegesis
- Name what Bryan is doing well so he knows to keep doing it
- Redirect rabbit holes with specificity: *"Interesting, but that's systematic theology. You've got a slot for that in phase 7. Bookmark it."*

### System Prompt Structure

The companion's Claude system prompt has these dynamic sections, assembled per request:

1. **Identity & voice** — Reformed Presbyterian seminary study partner + direct coach. Knows Greek/Hebrew. Challenges, doesn't coddle.
2. **Current phase context** — Which phase, which question, time remaining, what Bryan has done so far this session.
3. **Passage context** — The text, Bryan's translation (if completed), genre, book-level context.
4. **Homiletical guardrails** — The "So What?" gate, Christ thread check, time estimator rules. These are always present regardless of phase.
5. **Research summary** — Card responses and outline items so far. Kept concise to manage context window.
6. **Available tools** — The tool definitions for library access (commentary lookup, word study, cross-refs, etc.).
7. **Behavioral constraints** — Never dump walls of text. Never show step counts. Never write sermon content. Always mention time naturally.

## The Homiletical Coach

Three mechanisms that address Bryan's core struggle:

### 1. The "So What?" Gate
At each outline point: *"That's solid exegesis. But if I'm sitting in your pew — so what? What changes for me because ἀποκαλύπτεται is present tense?"*

If Bryan can't answer in one sentence, it's study notes, not sermon content. The companion helps distinguish "things I discovered" from "things my congregation needs to hear."

### 2. The Christ Thread
At each main point — not just the close: *"Where's Jesus in this point? Right now Christ doesn't show up until point III. Can your congregation wait that long?"*

Chapell's core insight enforced in real time. FCF in the introduction. Redemptive arc through every point. Christ throughout is a sermon; Christ at the end is a lecture with a gospel appendix.

### 3. The Time Estimator
As the outline takes shape: *"Bryan, this outline has 4 main points with 12 sub-points. At your pace, that's 40+ minutes. Your target is 28. Which point could become a footnote?"*

Makes the math visible during construction — not after Bryan has fallen in love with all his points.

**Estimation formula:** ~3 minutes per main point heading + ~1.5 minutes per sub-point + ~2 minutes for introduction + ~2 minutes for close. Calibrate after Bryan uses it for a few sermons.

### The Ultimate Test
*"Would your wife know the point? Would she know why it matters for Monday morning? Would she hear Jesus in it?"*

## Resource Access

### Commentary Display Pattern
1. Companion identifies which paragraph(s) answer the specific question
2. Presents: one-line summary of the author's argument
3. Followed by: full paragraph(s) with key sentences highlighted
4. Tone: *"Here's what Hodge says — see for yourself..."*

The companion does the FINDING. Bryan does the THINKING.

### Commentary AI Layer

When Bryan asks about a commentary or the companion surfaces one:
1. `find_commentary_section()` retrieves the section text via TOC (existing, works)
2. The section text (typically 1,000-5,000 words) is sent to Claude with a focused prompt: "The user is studying [passage] and asking [question]. Which paragraph(s) in this commentary section address that question? Return the relevant paragraph(s) verbatim, a one-sentence summary of the author's position, and which sentences to highlight."
3. This uses **Haiku** for speed and cost — paragraph selection doesn't need Opus-level reasoning.
4. Result is cached per (commentary, passage, question-hash) so repeated lookups are instant.

**Cost/latency:** Haiku processes 1,000-5,000 words in ~1-2 seconds at minimal cost. Surveying 6 commentaries = 6 parallel Haiku calls, all returning within 2-3 seconds. Well within the 5-second target.

### Resource Types

| Resource | How It Works |
|----------|-------------|
| Bible text | Clean output — annotation markers stripped entirely, not converted. Multiple translations side-by-side. |
| Commentaries | TOC-based section finding → Haiku paragraph selection → summary + highlighted text |
| Word studies | MVP: interlinear data (lemma, morphology, Strong's, gloss) from embedded Bible data. Phase 2: lexicon .logos4 reading if feasible (needs testing — .lbslms files currently fail to load). |
| Cross-references | Reference list with actual verse text expanded inline |
| Westminster Standards | Deferred to Priority 2. Requires identifying .logos4 resource IDs and building a proof-text index. |
| Systematic theology | Reformed/Presbyterian authors. Same display pattern as commentaries |
| Church fathers | Pre-600 AD only. Same display pattern |
| Sentence diagrams | Deferred to Priority 3. For MVP, Bryan exports from Logos and references the PDF. |

### Clean Bible Text Definition

"Clean" means: all annotation markers (`[a]`, `[fn9]`, `[h]`, FEFF-based markers) are **stripped entirely** from the display text. Cross-reference letters and footnote numbers are removed. The text reads as it would in a printed Bible without study apparatus. The raw annotated text is still available in the cache for annotation-specific features (cross-ref lookup).

### Theological Preferences
- Default to Reformed/Presbyterian voices (Hodge, Murray, Calvin, Owen, Edwards, Berkhof, Bavinck, Vos)
- Church fathers pre-600 AD only
- Confessions: Westminster Standards only (WCF, WLC, WSC)
- Don't surface irrelevant traditions unless specifically asked

## Outline Builder

### How Content Enters
- **Card responses** — companion asks if the insight belongs in the outline (not everything does)
- **Conversation saves** — "Save to outline?" after landing on an insight
- **Companion suggestions** — *"That's your second main point. Want me to slot it in?"*

### Outline Structure (matching Bryan's actual format)
- Title / THT (Take-Home Truth) at top
- Theme line
- Main points as questions or statements (I, II, III)
- Sub-points with verse references (v.1, v.2)
- Bullet points for observations, illustrations, applications
- Greek/Hebrew terms inline
- Cross-references as margin notes
- FCF and Christ-connection flagged

### Outline Data Model

The outline is a tree stored as rows with parent references:

- Each node has: `id`, `parent_id` (null for root), `type` (title | theme | main_point | sub_point | bullet | cross_ref | note), `content` (text), `verse_ref` (optional), `rank` (sort order within siblings), `flags` (fcf, christ_connection, needs_review)
- This allows reordering, re-parenting, and deletion without losing structure
- Export walks the tree to generate formatted output

### Export
- **HTML-to-print**: Generate a styled HTML page matching Bryan's typed outline format (bold headings, bullet points, clean hierarchy). Use the browser's native print-to-PDF. No additional dependency required.
- Ready to print and take to the pulpit
- Available at any point during prep, not just when "done"

## Session Management

### Starting a Session
One question on load: *"What are you preaching?"*
Type a Bible reference (Romans 1:18-23). Topic-based prep (e.g., "Spiritual warfare") is deferred — the companion handles book/chapter/verse references for MVP.

The companion:
1. Pulls text in preferred translations
2. Checks for previous session on this passage
3. Identifies genre from static book→genre map
4. Loads relevant data (commentary inventory for this passage)
5. Sets up phase timers
6. Opens with a brief orientation and asks if Bryan is ready to pray

### Resuming
*"Welcome back. Last time you finished your translation and identified three key terms. You're 4 hours into a 14-hour budget. Ready to pick up with word study?"*

### Multiple Sessions
Can have multiple active sessions (e.g., 1 Samuel for Sunday AM, Romans for Sunday PM). Switch between them from the start screen.

### History
Completed sessions stay accessible. The companion can reference past work within the same book series by querying previous session card responses and outline content. This is a direct database query — no embeddings or vector search needed for same-book lookups.

## Database Schema

### Tables

**sessions**
- `id`, `passage_ref`, `book`, `chapter`, `verse_start`, `verse_end`, `genre`
- `current_phase`, `current_question_id`
- `timer_remaining_seconds`, `timer_paused` (bool), `total_elapsed_seconds`
- `status` (active | completed), `created_at`, `updated_at`

**card_responses**
- `id`, `session_id`, `phase`, `question_id`, `content` (Bryan's response text)
- `saved_to_outline` (bool), `created_at`

**conversation_messages**
- `id`, `session_id`, `phase`, `role` (user | assistant | tool_result)
- `content`, `tool_name`, `tool_input`, `created_at`

**outline_nodes**
- `id`, `session_id`, `parent_id` (nullable, self-referencing)
- `type` (title | theme | main_point | sub_point | bullet | cross_ref | note)
- `content`, `verse_ref`, `rank`, `flags` (JSON: fcf, christ_connection, etc.)
- `source` (card_response_id or conversation_message_id — where this came from)
- `created_at`, `updated_at`

**question_bank**
- `id`, `phase`, `question_text`, `guidance_text` (the subtitle/hint below the question)
- `genre_tags` (JSON array: epistle, narrative, poetry, prophecy, law, apocalyptic)
- `priority` (core | supplemental), `resource_type` (what to pre-load: bible_text, translation, interlinear, none)
- `rank` (order within phase)

## Error Handling and Degradation

### Claude API unavailable (no internet, rate limited, key expired)
- Card flow continues to work — questions come from the local question bank, Bryan can type responses, outline builder works. The companion is silent but the workflow isn't blocked.
- Discussion mode shows: *"I can't connect right now. You can keep working through the questions — I'll be back when the connection is restored."*
- Commentary paragraph selection falls back to showing the full section text without AI highlights.

### LogosReader crashes
- The batch reader subprocess can die. `logos_batch.py` already handles this with automatic restart.
- If restart fails, resources show: *"Can't read [resource name] right now. LogosReader needs a restart."* with a retry button.
- Card flow continues — Bryan can still answer questions and build the outline manually.

### Commentary not found for passage
- Some commentaries don't cover every passage (e.g., a Psalms commentary for a Romans passage).
- Companion says: *"Hodge doesn't have a section on this passage. Want to try Murray or Cranfield instead?"*
- The system knows which commentaries cover which books from catalog metadata.

### Reference parsing fails
- If `parse_reference()` can't parse input, ask for clarification: *"I couldn't parse that — try something like 'Romans 1:18-23' or '1 Sam 25:1-13'."*
- No crash, no blank screen.

### Browser loses SSE connection
- Auto-reconnect with exponential backoff. On reconnect, reload the current card state from the server.
- No work is lost — all state is server-side in SQLite.

## API Cost Management

Different operations use different Claude models:

| Operation | Model | Why |
|-----------|-------|-----|
| Commentary paragraph selection | Haiku | Fast, cheap, pattern-matching task |
| Cross-ref text expansion | No AI | Direct lookup, no Claude needed |
| Interactive conversation | Opus | Seminary-level theological depth for study partner role |
| Homiletical coaching (Phase 11-12) | Opus | Needs real nuance for FCF/Christ-thread checks |
| Question selection | No AI | Local question bank, no Claude needed |

Estimated cost per sermon prep: ~$6-15 at current pricing, assuming ~30-50 conversation turns (Opus) and ~10 commentary lookups (Haiku). The study partner quality justifies the cost — a human TA would cost far more per week.

## Tech Stack

### Frontend
- Single-page app served by Flask
- HTMX for server-driven updates + vanilla JS for client-side state (timer, mode toggle, drawer)
- Vanilla CSS, no framework
- SSE for streaming companion responses (must use `client.messages.stream()`, not synchronous-then-SSE)

### Backend
- Flask (Python)
- Claude API via `anthropic` SDK — streaming responses with `client.messages.stream()`
- SQLite for persistence
- `study.py` + `logos_batch.py` + `logos_cache.py` (library access, already working)
- LogosReader (C# .NET 8, already working)

### What Changes
- `workbench_agent.py` → rewrite (new system prompt structure, card/conversation model, phase-aware tool dispatch)
- `app.py` → new routes (card flow, conversation, outline, export, session management)
- `workbench_db.py` → new schema (sessions, card_responses, outline_nodes, question_bank, conversation_messages)
- Templates → completely new (card UI, conversation thread, outline drawer, export template)
- `sermon_agent.py` → refactor tools (drop generic, add specific: `find_commentary_paragraph`, `word_study_lookup`, `cross_ref_expand`)

### What Stays
- LogosReader — don't touch
- `logos_batch.py` — works
- `logos_cache.py` — works
- `study.py` — core works, fix `clean_bible_text()`, add new functions

### Run
```bash
cd tools/workbench && python3 app.py
# Open http://localhost:5111
```

No new Python dependencies beyond what we have (Flask, anthropic, sqlite3). No build step. PDF export uses browser print-to-PDF (no server-side PDF library).

## Success Criteria

1. Bryan can start a prep session in under 30 seconds
2. He never sees more than one question at a time
3. Commentary paragraphs are surfaced with summary + highlights within 5 seconds
4. The companion challenges at least one exegetical point per session
5. The companion flags when the outline exceeds 30 minutes of preaching time
6. Every main point is checked for Christ-connection before export
7. Bryan can resume an interrupted session and be productive within 60 seconds
8. The exported outline matches the format Bryan actually preaches from
9. Bryan's wife notices the sermons are clearer and shorter
