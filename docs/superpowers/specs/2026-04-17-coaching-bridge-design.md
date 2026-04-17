# Coaching Bridge: Sermon Coach → Study Companion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the sermon coaching system's insights, patterns, and commitments into the study companion so that during sermon prep, the AI naturally references Bryan's historical patterns and coaching agreements — without nagging, and only when relevant.

**Architecture:** Three-layer model. Layer 1: active coaching commitment in the system prompt. Layer 2: five coach-aware tools with a retrieval policy and escalation ladder. Layer 3: session memory for coaching exposure tracking and anti-nagging enforcement.

**Tech Stack:** Python (Flask), SQLite, Anthropic Claude Opus 4.6, existing `meta_coach_tools.py` query functions, existing `companion_agent.py` prompt builder.

---

## Context

The sermon coach system analyzes Bryan's past preached sermons (33+ analyzed, with timestamped moments, priority rankings, and coaching commitments). The study companion helps Bryan prep future sermons through a 16-step workflow. Until now, these two systems were one-directional: the coach could read study prep data (via `get_prep_session_full`), but the companion had zero awareness of coaching data.

The matcher has been wired into the sync pipeline (as of 2026-04-16), so sermons are now automatically linked to their prep sessions. This spec completes the bidirectional bridge.

### Design Constraints

- **ADHD-first**: coaching should appear at decision points as simplification choices, not as reflective warnings
- **Not a nag**: the companion is a study partner, not a performance monitor
- **Dynamic**: insights evolve from coach conversations, not hardcoded profiles
- **The AI decides relevance**: not phase-gated, but phase-weighted with an explicit transition question

### What Codex Flagged (addressed in design)

1. Raw coach conversation messages are noisy — use structured insights instead
2. Implicit phase detection is brittle — add an explicit transition question
3. Anti-nagging needs session memory to be enforceable, not aspirational
4. Escalation ladder needs a diagnostic check before pattern references
5. Active commitment is a bias, not a straitjacket

---

## Layer 1: Active Commitment in the System Prompt

The study companion's system prompt gets one new section loaded from `coaching_commitments` (at most one active row). This is the coaching agreement Bryan made with the meta-coach — it changes when they set a new one.

### What it looks like in the prompt

```
## Active Coaching Commitment (background — do not recite verbatim)

Dimension: application_specificity
Practice: Identify two moments where the text touches the listener's life. Write a
concrete sentence for each and put a literal "pause" note in the manuscript.
Target: 2 sermons
```

### Rules for the companion

- Never recite the commitment back verbatim
- Use it as a lens that shapes guidance — e.g., when Bryan reaches application work, the companion naturally asks "where does the text touch the listener's life?" rather than saying "your commitment says..."
- If no active commitment exists, this section is omitted entirely
- Active commitment is a **bias, not a straitjacket** — if today's text demands something different (e.g., the passage is pure lament and doesn't need application mechanics), the companion follows the text

### Data source

`coaching_commitments` table — `WHERE status = 'active'` (partial unique index ensures at most one).

---

## Layer 2: Coach-Aware Tools

Five tools added to the study companion's tool definitions. Four reuse existing query functions; one is new.

### Tool definitions

| Tool | Source | Returns |
|------|--------|---------|
| `get_active_commitment` | `meta_coach_tools.get_active_commitment()` | Active commitment + progress (sermons_since, positive/negative moments found) |
| `get_sermon_patterns` | `sermon_coach_tools.get_sermon_patterns()` | Aggregate rates: burden clarity, movement, application, ethos, concreteness, Christ thread, exegetical grounding, duration delta |
| `get_representative_moments` | `meta_coach_tools.get_representative_moments()` | Specific timestamped moments from past sermons (positive or negative), with excerpts and rationale |
| `get_counterexamples` | `meta_coach_tools.get_counterexamples()` | Sermons where a typically weak dimension was strong — "what worked differently?" |
| `get_coaching_insights` | **New function** | Structured summaries extracted from recent coaching conversations, not raw messages |

### `get_coaching_insights` — New Tool

Returns normalized, structured insights from recent substantive coach exchanges. NOT raw conversation messages.

**Output format:**
```json
{
  "insights": [
    {
      "summary": "Application is present but diffuse and abstract throughout — slow down at moments where the text touches the listener's life rather than returning to exposition.",
      "dimension": "application_specificity",
      "applies_when": ["outline construction", "application development", "delivery refinement"],
      "avoid_when": ["textual observation", "open brainstorming"],
      "source_sermon_title": "Religious Pride or Resting in Jesus?",
      "created_at": "2026-04-16"
    }
  ]
}
```

**Storage:** New `coaching_insights` table:
```sql
CREATE TABLE IF NOT EXISTS coaching_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_key TEXT,
    summary TEXT NOT NULL,
    applies_when TEXT NOT NULL,      -- JSON array of prep modes
    avoid_when TEXT NOT NULL,        -- JSON array of prep modes
    source_sermon_id INTEGER REFERENCES sermons(id),
    source_conversation_id INTEGER,
    superseded_by INTEGER REFERENCES coaching_insights(id),
    created_at TEXT NOT NULL
);
```

**Capture mechanism:** After a substantive conversation with either the per-sermon coach or the meta-coach, the coach explicitly proposes: "Should I save this as a coaching note for your future prep?" Bryan confirms or edits. Only confirmed insights are stored. Both coaches can write to this table. This keeps Bryan in control of what the system "learns."

### Retrieval Policy

Embedded in the study companion's system prompt as behavioral instructions:

```
## Coaching Memory — Retrieval Policy

You have access to Bryan's longitudinal sermon coaching data. Use it to sharpen
your homiletical guidance — never to nag, lecture, or constantly reference the past.

WHEN TO CONSULT:
- During textual work (observation, word study, context, commentaries): Do NOT
  consult coaching tools. Your job here is discovery. The only exception is if
  Bryan explicitly asks about past sermons.
- When transitioning to sermon shaping: Ask "Are we still exploring the text,
  or are we shaping the sermon now?" That question is the gate. Once Bryan says
  "let's shape it," coaching tools activate.
- During sermon construction: Check get_active_commitment. Consult other tools
  when you detect sprawling outline, deferred application, unclear burden, or
  Bryan asks for examples.

TOOL PRECEDENCE (when coaching data conflicts):
1. Active commitment (most specific, Bryan-approved)
2. Stable sermon pattern aggregates (strongest evidence base)
3. Counterexamples (what worked differently)
4. Coaching insights (recent, but may have recency bias)
5. Representative moments (evidence, not guidance)

NO SERMON TITLES/DATES UNPROMPTED:
Do not reference specific sermon titles or dates unless Bryan asks for evidence
or disputes a pattern claim.

GRACEFUL DEGRADATION:
If coaching data is sparse, stale, or doesn't apply to the current sermon type,
do not pretend confidence. Say nothing rather than force irrelevant coaching.
```

### Escalation Ladder

The companion follows this order strictly. Never skip levels.

```
ESCALATION LADDER (never skip levels):

1. SILENT SHAPING
   Guide toward clarity without any coaching reference.
   "Let's tighten this to one governing idea."

2. DIAGNOSTIC CHECK
   Ask a targeted question that tests whether the issue is present.
   "What's the one burden you want them to carry out of the room?"
   Do NOT reference history yet. Let Bryan's answer reveal the state.

3. PATTERN REFERENCE
   Only if the diagnostic confirms drift or confusion.
   "A recurring pattern in your recent sermons is that the burden emerges late.
   Want to state it now before we build the outline?"

4. SPECIFIC EXAMPLE
   Only if Bryan asks, disputes the pattern, or seems stuck.
   "In your Romans 2 sermon, you found the application at minute 10 by naming
   a specific person — 'the coworker you've been avoiding.' That landed."

5. CONCRETE INTERVENTION
   Offer one action, not more analysis.
   "Let's write the burden sentence right now: 'God teaches us that ___.'
   We'll test each movement against it."
```

---

## Layer 3: Session Memory + Anti-Nagging

### Coaching Exposure Tracking

Track per-session which coaching issues have been surfaced and how Bryan responded. This makes anti-nagging enforceable.

**Storage:** New `session_coaching_exposure` table:
```sql
CREATE TABLE IF NOT EXISTS session_coaching_exposure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    dimension_key TEXT NOT NULL,
    escalation_level INTEGER NOT NULL,  -- 1=silent, 2=diagnostic, 3=pattern, 4=example, 5=intervention
    response TEXT CHECK (response IN ('accepted', 'declined', 'deferred', 'pending')),
    created_at TEXT NOT NULL,
    UNIQUE(session_id, dimension_key)
);
```

### Anti-Nagging Rules

```
ANTI-NAGGING RULES:

RELEVANCE GATE — before ANY coaching callback, ALL must be true:
1. Prep mode is sermon-shaping (not textual discovery)
2. Active commitment or pattern is plausibly relevant to this passage/genre
3. Current work actually exhibits the risk (not hypothetical)
4. The issue has not already been surfaced and addressed this session

BACKING OFF:
- If Bryan declines or redirects ("I know, but this passage needs the density"),
  record response='declined' and do not resurface that dimension this session
  unless Bryan reopens it
- If Bryan accepts and acts on it, record response='accepted' and move on
- Maximum one explicit pattern reference per coaching dimension per session

FRAMING:
- Frame as allyship: "To help this land more clearly…" not "Because you usually…"
- Prefer simplification choices over reflective warnings
- Brief, binary or comparative when possible (ADHD-friendly)

HEALTHY DEVIATION:
- If Bryan is doing a typically weak area WELL in the current prep, stay silent.
  Counterexamples should prevent false positives, not just support escalation.
- Do not force the commitment lens onto a sermon that doesn't need it.
```

---

## The Transition Question

The study companion does not track explicit workflow states. Instead, it uses one natural question as the gate between discovery mode (no coaching) and construction mode (coaching active):

> "Are we still exploring the text, or are we shaping the sermon now?"

This question:
- Fires when the conversation shows ambiguous signals (exegesis winding down, outline language emerging, burden language surfacing)
- Is asked at most once per session — once answered, the companion remembers the mode
- If Bryan says "still exploring," coaching stays dormant
- If Bryan says "let's shape it" (or equivalent), coaching tools activate
- Bryan can also trigger the transition explicitly: "let's move to the outline" / "I'm ready to construct"

This is simpler than a full state machine and more reliable than hidden inference. One question, one gate.

---

## Data Flow Summary

```
┌─────────────────────────┐     ┌──────────────────────────┐
│   SERMON COACH SIDE     │     │   STUDY COMPANION SIDE   │
│                         │     │                          │
│ sermon_reviews          │────→│ get_sermon_patterns()    │
│ sermon_moments          │────→│ get_representative_      │
│                         │     │   moments()              │
│ coaching_commitments    │────→│ get_active_commitment()  │
│ coaching_insights (NEW) │────→│ get_coaching_insights()  │
│ sermon_coach_messages   │     │ get_counterexamples()    │
│                         │     │                          │
│ get_prep_session_full() │←────│ sessions, cards, outline │
│   (already works)       │     │ conversation messages    │
│                         │     │                          │
│ sermon_links (matcher)  │←──→│ session linking           │
│   (now automated)       │     │   (now automated)        │
└─────────────────────────┘     └──────────────────────────┘
```

---

## New Schema Summary

| Table | Purpose |
|-------|---------|
| `coaching_insights` | Structured insights captured from coach conversations (Bryan-confirmed) |
| `session_coaching_exposure` | Per-session tracking of which coaching issues were surfaced and Bryan's response |

---

## What This Does NOT Include

- **Meta-coach on patterns page** — already built separately
- **Coaching insights auto-extraction** — insights are captured via explicit "save this?" prompt, not automatic. Automatic extraction is a future enhancement.
- **Full state machine for prep workflow** — one transition question is sufficient for MVP
- **UI changes to the study companion** — this is all backend (prompt + tools + schema). The study companion's conversation UI doesn't change.

---

## Success Criteria

1. During sermon construction, the companion references Bryan's active commitment naturally (without being asked)
2. During textual work, coaching is silent
3. When Bryan declines a coaching intervention, it doesn't resurface that dimension
4. The companion can cite specific past sermon examples when Bryan asks or is stuck
5. Coaching insights from per-sermon and meta-coach conversations persist and surface during future prep
6. The transition question fires naturally and only once
