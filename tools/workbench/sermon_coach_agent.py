"""Sermon coach agent — streaming Claude Opus 4.6 narrator.

Reads precomputed sermon_reviews + flags + full raw context via tool calls,
narrates the four review cards, runs a conversation over the sermon.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS
from sermon_coach_tools import (
    get_sermon_review, get_sermon_flags, get_transcript_full,
    get_prep_session_full, pull_historical_sermons, get_sermon_patterns,
)


LONGITUDINAL_POSTURE_RULE = """## Longitudinal Posture — YOU MUST FOLLOW THIS

The system has analyzed N recent sermons. The current corpus gate is: {corpus_gate_status}

If corpus_gate_status == 'pre_gate' (fewer than 5 recent sermons):
  - You may NOT use any of these words: "pattern", "persistent", "always",
    "every time", "trajectory", "tendency", "habit", "consistently".
  - You may ONLY describe what you see in this specific sermon.
  - If Bryan asks about patterns, say: "I don't have enough corpus yet to
    speak to patterns — I need at least 5 recent sermons before I can. What
    I see in THIS sermon is ..."

If corpus_gate_status == 'emerging' (5-9 recent sermons):
  - You may say "emerging pattern" when >=3 of the last 5 sermons share the
    same dimension in the same direction.
  - You may NOT say "persistent" or "always" or "stable pattern."
  - Always label: "emerging observation across the last 5 sermons..."

If corpus_gate_status == 'stable' (10+ recent sermons):
  - Full longitudinal voice is available.
  - Always label observations explicitly: "current-sermon observation",
    "historical pattern", or "trajectory".
  - Never conflate the three.

This rule is non-negotiable. Violating it damages Bryan's trust in the system."""


HOMILETICAL_FRAMEWORK = """## Homiletical Framework

Impact -> Faithfulness -> Diagnostic, three tiers:

- Tier 1 (Impact): burden clarity, movement, application specificity, ethos, concreteness.
  These are what rhetoric and sermon-listening research identify as the
  strongest predictors of impact on hearers.
- Tier 2 (Faithfulness): Christ thread + exegetical grounding. Parallel crown
  for a Reformed pastor — faithfulness is a distinct axis from impact.
- Tier 3 (Diagnostic): length, density hotspots, late application, outline drift.
  These are symptoms. Their causes live in Tier 1. When Bryan runs long,
  the length is the surface; the cause is usually late application or density."""


def build_system_prompt(sermon_context: dict, review_json: dict,
                        corpus_gate_status: str) -> str:
    """Assemble the coach's system prompt."""
    sections = [
        IDENTITY_CORE,
        HOMILETICAL_TRADITION,
        VOICE_GUARDRAILS,
        HOMILETICAL_FRAMEWORK,
        _current_sermon_section(sermon_context),
        _pipeline_findings_section(review_json),
        LONGITUDINAL_POSTURE_RULE.replace('{corpus_gate_status}', corpus_gate_status),
        _tools_section(),
        _behavioral_constraints(),
    ]
    return '\n\n'.join(s for s in sections if s)


def _current_sermon_section(ctx: dict) -> str:
    if not ctx:
        return ""
    parts = ["## Current Sermon Context"]
    if 'passage' in ctx:
        parts.append(f"Passage: {ctx['passage']}")
    if 'duration_sec' in ctx:
        d = ctx['duration_sec']
        parts.append(f"Duration: {d // 60}:{d % 60:02d}")
    if 'preach_date' in ctx:
        parts.append(f"Preached: {ctx['preach_date']}")
    if 'linked_session_id' in ctx:
        parts.append(f"Linked prep session: #{ctx['linked_session_id']}")
    return '\n'.join(parts)


def _pipeline_findings_section(review: dict) -> str:
    if not review:
        return "## Pipeline Findings\n\n(no review yet)"
    return "## Pipeline Findings (structured)\n\n```json\n" + json.dumps(review, indent=2, default=str) + "\n```"


def _tools_section() -> str:
    lines = ["## Tools Available\n"]
    for tool in TOOL_DEFINITIONS:
        lines.append(f"- **{tool['name']}**: {tool['description']}")
    return '\n'.join(lines)


def _behavioral_constraints() -> str:
    return """## Behavioral Constraints

- You never auto-initiate. You respond when Bryan enters the Review page or clicks a flag.
- One action per turn per metric: if you override, don't also reanalyze on the same turn.
- When you disagree with a pipeline value, say so in the chat with explicit rationale — your
  disagreement becomes part of the conversation log.
- Lead with the Impact card when Bryan opens the review. Tier 1 is the coaching crown.
- When appropriate, cite Chapell's Christ-Centered Preaching, Robinson's Big Idea, Beeke, or
  Piper — but only when the citation earns its place. Don't pepper quotes unnecessarily."""


TOOL_DEFINITIONS = [
    {
        'name': 'get_sermon_review',
        'description': 'Fetch the full structured review for a sermon (all three tiers + coach summary).',
        'input_schema': {
            'type': 'object',
            'properties': {'sermon_id': {'type': 'integer'}},
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_sermon_flags',
        'description': 'Fetch per-moment flags for a sermon (late_application, density_spike, etc.).',
        'input_schema': {
            'type': 'object',
            'properties': {'sermon_id': {'type': 'integer'}},
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_transcript_full',
        'description': 'Fetch raw transcript text. Optionally slice by seconds.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'sermon_id': {'type': 'integer'},
                'start_sec': {'type': 'integer'},
                'end_sec': {'type': 'integer'},
            },
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_prep_session_full',
        'description': 'Fetch the linked prep session: outline, card responses, homiletical messages. Returns null if no active link.',
        'input_schema': {
            'type': 'object',
            'properties': {'sermon_id': {'type': 'integer'}},
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'pull_historical_sermons',
        'description': 'Return the N most recent classified sermons with their review summary fields. Use for cross-sermon depth — subject to the corpus gate.',
        'input_schema': {
            'type': 'object',
            'properties': {'n': {'type': 'integer', 'default': 5}},
        },
    },
    {
        'name': 'get_sermon_patterns',
        'description': 'Aggregate metrics over recent sermons + corpus_gate_status. Tells you what longitudinal voice you are allowed to use.',
        'input_schema': {
            'type': 'object',
            'properties': {'window_days': {'type': 'integer', 'default': 90}},
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, session_context: dict) -> dict:
    """Dispatch a tool call."""
    db = session_context['db']
    try:
        if tool_name == 'get_sermon_review':
            return get_sermon_review(db, tool_input['sermon_id']) or {'error': 'not found'}
        if tool_name == 'get_sermon_flags':
            return {'flags': get_sermon_flags(db, tool_input['sermon_id'])}
        if tool_name == 'get_transcript_full':
            return {'transcript': get_transcript_full(
                db, tool_input['sermon_id'],
                start_sec=tool_input.get('start_sec'),
                end_sec=tool_input.get('end_sec'),
            )}
        if tool_name == 'get_prep_session_full':
            prep = get_prep_session_full(db, tool_input['sermon_id'])
            return prep if prep else {'linked': False}
        if tool_name == 'pull_historical_sermons':
            return {'sermons': pull_historical_sermons(db, n=tool_input.get('n', 5))}
        if tool_name == 'get_sermon_patterns':
            return get_sermon_patterns(db, window_days=tool_input.get('window_days', 90))
        return {'error': f'unknown tool: {tool_name}'}
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}


@dataclass
class CoachTurnResult:
    assistant_text: str
    input_tokens: int
    output_tokens: int


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stream_coach_response(db, sermon_id: int, conversation_id: int,
                          user_message: str, llm_client):
    """Generator that streams coach output events and persists messages."""
    conn = db._conn()
    sermon_row = conn.execute("""
        SELECT id, bible_text_raw, preach_date, duration_seconds
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    conn.close()
    if not sermon_row:
        yield {'type': 'error', 'error': 'sermon_not_found'}
        return

    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (?, ?, 'user', ?, ?)
    """, (sermon_id, conversation_id, user_message, _now()))
    conn.commit()
    conn.close()

    review = get_sermon_review(db, sermon_id) or {}
    patterns = get_sermon_patterns(db)
    sermon_context = {
        'passage': sermon_row[1],
        'preach_date': sermon_row[2],
        'duration_sec': sermon_row[3] or 0,
    }
    system = build_system_prompt(sermon_context, review, patterns['corpus_gate_status'])

    conn = db._conn()
    history_rows = conn.execute("""
        SELECT role, content FROM sermon_coach_messages
        WHERE sermon_id = ? AND conversation_id = ?
        ORDER BY id
    """, (sermon_id, conversation_id)).fetchall()
    conn.close()
    messages = [{'role': r[0], 'content': r[1]} for r in history_rows if r[1]]

    assistant_text_parts = []
    input_tokens = 0
    output_tokens = 0
    try:
        for event in llm_client.stream_message(system=system, messages=messages,
                                                 tools=TOOL_DEFINITIONS):
            if event.get('type') == 'text_delta':
                assistant_text_parts.append(event.get('text', ''))
                yield event
            elif event.get('type') == 'tool_use':
                tool_result = execute_tool(
                    event['tool_name'], event['tool_input'],
                    session_context={'db': db, 'sermon_id': sermon_id},
                )
                yield {'type': 'tool_result', 'tool_name': event['tool_name'],
                        'result': tool_result}
            elif event.get('type') == 'message_complete':
                usage = event.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                yield event
    except Exception as e:
        yield {'type': 'error', 'error': f'{type(e).__name__}: {e}'}
        return

    assistant_text = ''.join(assistant_text_parts)
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (?, ?, 'assistant', ?, ?)
    """, (sermon_id, conversation_id, assistant_text, _now()))
    conn.commit()
    conn.close()
