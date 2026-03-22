# Conversation-First Sermon Study UX — Design Spec

**Date:** 2026-03-22
**Goal:** Replace the card-based quiz UI with a conversation-first study experience. The AI is Bryan's graduate assistant — it reads the library, surfaces the best material, debates exegesis, and helps build the sermon. The conversation IS the workflow.

## The Problem

Bryan has ADHD. His current Logos workflow has 28 visible steps, and he stalls at steps 8-12 where he's supposed to read through 10 commentaries, systematics, and biblical theologies. He reads slowly but deeply. The volume of material + lack of direction = paralysis. He either skims and rushes to sermon writing (producing a dense outline with no homiletical development) or preaches extemporaneously from Greek notes (which his wife says is unstructured).

The AI should do the reading. Bryan should do the thinking.

## Core Metaphor

**A working session with your graduate research assistant.** The RA has read the library, brings the best material, debates your ideas, and helps organize the sermon. You're the professor — the RA supports, challenges, and sharpens, but you write.

## Screen Layout

```
┌──────────────────────────────────────────────────────────┬─────────────────┐
│  Romans 1:18-23                                 1h 42m  │ Sermon Outline  │
├──────────────────────────────────────────────────────────┤                 │
│                                                          │ I. God's wrath  │
│  [AI message with scripture block, library quotes,       │   is revealed   │
│   cross-references embedded inline]                      │   A. Present    │
│                                                          │      tense =    │
│                          [Your message, right-aligned]   │      ongoing    │
│                                                          │   B. Against    │
│  [AI response with another library quote]                │      suppression│
│                                                          │      of truth   │
│                          [Your message]                  │                 │
│                                                          │ II. (empty)     │
│  [AI with insight capture: ✓ Saved: ...]                │                 │
│                                                          │ + add note      │
│                                                          │                 │
├──────────────────────────────────────────────────────────┤                 │
│  [input area, auto-growing]                    Send      │                 │
└──────────────────────────────────────────────────────────┴─────────────────┘
```

### Top Bar (minimal)
- **Left**: Session name / passage reference
- **Right**: Subtle session duration clock ("1h 42m"), menu icon
- **No progress dots. No phase badges. No countdown timers.**

### Conversation Area (center, max ~800px)
- Full conversation thread, scrollable
- AI messages: left-aligned, no background, rich content blocks inline
- Your messages: right-aligned, subtle blue-gray background
- Input area fixed at bottom: auto-growing textarea, Enter to send, Shift+Enter for newline

### Outline Sidebar (right, ~300px, always visible)
- Persistent — not a drawer. Always on screen.
- Title area (editable — starts as passage ref, you rename to sermon title)
- Nested outline tree: main points (Roman numerals, bold), sub-points (lettered, indented), notes (gray italic), scripture refs (blue)
- Each item tagged with source phase (small gray text: "from text work")
- Drag to reorder
- Click to edit inline
- Right-click to delete
- "Add note" input at bottom with type selector
- **The outline is the deliverable.** Export produces the sermon document.

## Rich Content Blocks

### Scripture (original language only)
```
┌─ Romans 1:18  THGNT ────────────────────┐
│ Ἀποκαλύπτεται γὰρ ὀργὴ θεοῦ ἀπ'        │
│ οὐρανοῦ ἐπὶ πᾶσαν ἀσέβειαν καὶ         │
│ ἀδικίαν ἀνθρώπων τῶν τὴν ἀλήθειαν      │
│ ἐν ἀδικίᾳ κατεχόντων                    │
└──────────────────────────────────────────┘
```
- **Original language only** — THGNT for NT, BHS for OT. No English alongside.
- **Clickable words**: Tap any word → tooltip popup with lemma, root, parsing (person/number/tense/voice/mood or declension), and short gloss. Like Logos's inline interlinear.
- If Bryan wants English, he asks the AI and it quotes NKJV or NET (his primary translations).

### Library Quotes
```
┌─ EDNT, s.v. ἀποκαλύπτω ─────────────────┐
│ "The present tense ἀποκαλύπτεται         │
│ indicates that God's wrath is not merely │
│ eschatological but is currently being    │
│ revealed in the moral deterioration      │
│ described in vv. 24-32..."              │
│                              [read more] │
└──────────────────────────────────────────┘
```
- Source in header (lexicon/grammar/commentary name + article reference)
- Actual quote text, not raw data
- "Read more" expands to full entry
- Works for: lexicons, grammars, commentaries, any library resource

### Cross-Reference Clusters
```
┌─ Cross-references for v.18 ──────────────┐
│ • Ps 19:1-2 — The heavens declare the   │
│   glory of God; the skies proclaim the   │
│   work of his hands.              (NKJV) │
│ • Acts 14:17 — Nevertheless He did not   │
│   leave Himself without witness...       │
│ • Rom 2:5 — But in accordance with your  │
│   hardness and your impenitent heart...  │
│                          [show 12 more]  │
└──────────────────────────────────────────┘
```
- Shows full verse text (NKJV default, NET available)
- Compact but readable
- Expandable for large clusters

### Church Father / Ancient Literature Citations
```
┌─ Augustine, De Civitate Dei ─────────────┐
│ Quotation on Rom 1:18                    │
│ "For the wrath of God is not a          │
│ disturbance of His mind, but His        │
│ judgment by which punishment is          │
│ assigned to sin..."                      │
└──────────────────────────────────────────┘
```

### Insight Capture (inline)
```
 ✓ Saved: ἀποκαλύπτεται — present tense = ongoing revelation of wrath
```
Small green pill in the conversation flow. Tells Bryan what was saved without breaking flow.

## Session Flow

### Starting
- Open app → see recent sessions (resumable) + text input: "What are you preaching?"
- Type passage reference → session begins
- AI does 2-3 seconds of background research (reads text, scans datasets), then opens the conversation proactively with a substantive first move

### The Invisible Phase Engine
The AI internally tracks which phase the conversation is in. It never announces phases. It steers naturally:

| Internal Phase | AI Behavior |
|---|---|
| Prayer | Opens with: "Before we dig in — have you prayed over this text?" |
| Text Work | "I've got THGNT pulled up. That ἀποκαλύπτεται in v.18 mirrors v.17..." |
| Word Study | "You keep circling back to δικαιοσύνη — want me to pull up EDNT?" |
| Context | "Let's zoom out. Where does this pericope fit in Paul's argument?" |
| Theological | "Cranfield has a sharp paragraph here. And the WCF speaks to this in chapter 6..." |
| Commentary | Surfaces relevant paragraphs proactively, doesn't wait to be asked |
| Exegetical Point | "What's the one thing this passage is saying?" |
| FCF & Homiletical | "What's broken in your congregation that this text addresses?" |
| Sermon Construction | "Let's build the sermon. How do you want to open?" |
| Edit | "Read me your outline. Let me push back where it's thin." |

### Resuming
- Click previous session from start screen
- AI picks up where you left off: "Last time we nailed down the EP. We hadn't started on the FCF yet. Want to pick up there?"
- Full conversation history scrollable above

### Ending
- No formal end. Close the tab. Everything auto-saves.
- "I'm done for today" → AI gives session summary, marks checkpoint
- Next time: seamlessly resumable

## Behavioral Analytics

### What It Tracks (SQLite, silent)

| Metric | Purpose |
|---|---|
| Time per internal phase | Detect exegesis/homiletics imbalance |
| Message frequency + length | Detect engagement vs. stalling |
| Time on same sub-topic | Rabbit-trail detection |
| Research-to-synthesis ratio | Bryan's pattern: 80% exegesis, 20% homiletics |
| Outline velocity | Items saved per hour — stalled = stuck |
| Silence gaps | >5 min = stepped away, >10 min = may need re-engagement |
| Session-over-session patterns | Build profile of prep habits across sermons |

### What It Does With the Data

**Gentle pivots** (not interruptions):
- "We've been deep in the Greek for 90 minutes — your exegetical work is solid. Want to start thinking about what this means for Sunday?"
- Only suggests, never forces

**Pattern alerts** (across sessions):
- "Across your last 5 sermons, commentary consultation takes 3x longer than other phases. Want me to pre-read and give you a 3-paragraph summary?"

**Stall detection**:
- If outline hasn't grown in 45+ minutes, AI gently asks: "We've covered a lot of ground. Want me to summarize what we've found so far?"

**Wellbeing nudges**:
- After 2+ hours continuous: "You've been locked in for 2 hours — grab some water?"
- After 4+ hours: "Seriously, eat something. The Greek will still be here."

**Post-session summary**:
- "Today: 2h 15m. We covered text work, word study on δικαιοσύνη and ἀδικία, and contextual placement. Open items: theological analysis, commentary, sermon construction."

### What Bryan Can See (optional, not default)
- "Session stats" view accessible from menu: time breakdown, phase distribution, sermon-over-sermon comparison
- Never visible during active prep

## Visual Design

### Color Palette
- Background: Very dark blue-black (`#1a1a2e`)
- Conversation area: Dark surface for content blocks (`#16213e`)
- Your messages: Subtle blue-gray (`#1e3a5f`)
- AI messages: No background — text on dark canvas
- Accents: Green for saves/completion (`#7fdb98`), Blue for interactive elements (`#5b8def`), Muted gray for secondary text (`#a0a0b0`)

### Typography
- System sans-serif for conversation: `-apple-system, BlinkMacSystemFont, "Segoe UI"`
- Good Unicode support required for polytonic Greek and pointed Hebrew
- 16px base, 1.6 line-height
- Monospace for code/data only: `"SF Mono", "Fira Code"`

### Key Rules
- **No animations.** Everything instant. No transitions, no fades, no slides.
- **No smooth scrolling.** Instant scroll behavior.
- **Subtle scrollbars.** 4-6px, nearly invisible.
- **Generous whitespace.** Don't crowd the conversation.
- **13" MacBook minimum.** Conversation (~800px) + sidebar (~300px) + margins = ~1200px total. Works on 1280px+ screens.

## Default Translations
- **Original language**: THGNT (NT), BHS (OT) — always shown
- **English when requested**: NKJV primary, NET secondary
- NOT ESV (previous default was wrong)

## Files to Create/Modify

### New files:
```
tools/workbench/
├── static/
│   ├── study.css              — New conversation-first styles
│   └── study.js               — New JS: streaming, word popups, outline interactions, analytics
├── templates/
│   ├── study_base.html        — Base template for new UI
│   ├── study_start.html       — Session start / resume page
│   └── study_session.html     — Main conversation + outline view
├── session_analytics.py       — Behavioral analytics tracking + queries
```

### Modified files:
```
tools/workbench/
├── app.py                     — Add /study/ routes (keep /companion/ for backward compat)
├── companion_agent.py         — Update streaming to emit rich content block events
├── companion_tools.py         — Update tool result formatting for inline display
├── companion_db.py            — Add analytics tables, update session schema
```

## What This Is NOT

- Not a mobile app. Laptop/desktop only.
- Not a card quiz system. No "next question" buttons.
- Not a dashboard. No charts on the main screen.
- Not a document editor. The outline sidebar is simple — not Google Docs.
- Not a timer-driven workflow. No countdowns, no phase deadlines.
