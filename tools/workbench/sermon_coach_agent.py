"""Sermon coach agent — streaming Claude Opus 4.6 narrator.

Reads precomputed sermon_reviews + flags + full raw context via tool calls,
narrates the four review cards, runs a conversation over the sermon.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS
from shared_prompts import HOMILETICAL_FRAMEWORK, LONGITUDINAL_POSTURE_RULE
from sermon_coach_tools import (
    get_sermon_review, get_sermon_flags, get_transcript_full,
    get_prep_session_full, pull_historical_sermons, get_sermon_patterns,
)


def build_system_prompt(sermon_context: dict, review_json: dict,
                        corpus_gate_status: str,
                        active_commitment: dict = None) -> str:
    """Assemble the coach's system prompt."""
    sections = [
        IDENTITY_CORE,
        HOMILETICAL_TRADITION,
        VOICE_GUARDRAILS,
        HOMILETICAL_FRAMEWORK,
        _current_sermon_section(sermon_context),
        _pipeline_findings_section(review_json),
        _coaching_focus_section(active_commitment),
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
    if ctx.get('transcript'):
        transcript = ctx['transcript']
        if len(transcript) > 50000:
            transcript = transcript[:50000] + '\n\n[... transcript truncated at 50K chars — use get_transcript_excerpt tool for later sections]'
        parts.append(f"\n## Full Transcript\n\n{transcript}")
    return '\n'.join(parts)


def _pipeline_findings_section(review: dict) -> str:
    if not review:
        return "## Pipeline Findings\n\n(no review yet)"
    return "## Pipeline Findings (structured)\n\n```json\n" + json.dumps(review, indent=2, default=str) + "\n```"


def _coaching_focus_section(commitment: dict) -> str:
    if not commitment:
        return ""
    return f"""## Active Coaching Focus

Bryan is currently working on: {commitment.get('practice_experiment', '')}
Dimension: {commitment.get('dimension_key', '')}
Target: next {commitment.get('target_sermons', 2)} sermons

After your standard review, add a brief "Commitment check" section:
- Did this sermon show the target behavior?
- If yes, cite the specific moment(s). If no, note what happened instead.
- Do not let the commitment lens override your independent assessment."""


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
  Piper — but only when the citation earns its place. Don't pepper quotes unnecessarily.
- When a conversation produces a refined coaching insight that would help future
  sermon prep, propose: "Should I save this as a coaching note for your future
  prep?" If Bryan confirms, summarize the insight as: what dimension it relates to,
  a 1-2 sentence summary, and when it applies vs when to avoid it. The frontend
  will save it via the coaching-insight endpoint."""


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
        'name': 'get_transcript_excerpt',
        'description': 'Extract a time-sliced excerpt from the transcript by start/end seconds. The full transcript is already in your system prompt — use this only when you need a precise time-bounded slice (e.g. around a flagged moment).',
        'input_schema': {
            'type': 'object',
            'properties': {
                'sermon_id': {'type': 'integer'},
                'start_sec': {'type': 'integer'},
                'end_sec': {'type': 'integer'},
            },
            'required': ['sermon_id', 'start_sec', 'end_sec'],
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
        if tool_name == 'get_transcript_excerpt':
            return {'transcript': get_transcript_full(
                db, tool_input['sermon_id'],
                start_sec=tool_input['start_sec'],
                end_sec=tool_input['end_sec'],
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


MAX_TOOL_ROUNDS = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_sermon_context(db, sermon_id: int) -> dict | None:
    """Load sermon context including linked prep session ID if one exists.

    Returns a dict with passage, preach_date, duration_sec, transcript,
    and optionally linked_session_id.  Returns None if the sermon doesn't exist.
    """
    conn = db._conn()
    try:
        sermon_row = conn.execute("""
            SELECT id, bible_text_raw, preach_date, duration_seconds, transcript_text
            FROM sermons WHERE id = ?
        """, (sermon_id,)).fetchone()
        if not sermon_row:
            return None

        link_row = conn.execute("""
            SELECT session_id FROM sermon_links
            WHERE sermon_id = ? AND link_status = 'active'
        """, (sermon_id,)).fetchone()
    finally:
        conn.close()

    ctx = {
        'passage': sermon_row[1],
        'preach_date': sermon_row[2],
        'duration_sec': sermon_row[3] or 0,
        'transcript': sermon_row[4],
    }
    if link_row:
        ctx['linked_session_id'] = link_row[0]
    return ctx


def stream_coach_response(db, sermon_id: int, conversation_id: int,
                          user_message: str, llm_client):
    """Generator that streams coach output events and persists messages."""
    sermon_context = _load_sermon_context(db, sermon_id)
    if not sermon_context:
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

    # Fetch active coaching commitment
    conn2 = db._conn()
    commitment_row = conn2.execute(
        "SELECT dimension_key, practice_experiment, target_sermons FROM coaching_commitments WHERE status = 'active' LIMIT 1"
    ).fetchone()
    conn2.close()
    active_commitment = {
        'dimension_key': commitment_row[0],
        'practice_experiment': commitment_row[1],
        'target_sermons': commitment_row[2],
    } if commitment_row else None

    system = build_system_prompt(sermon_context, review, patterns['corpus_gate_status'],
                                 active_commitment=active_commitment)

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

    for _round in range(MAX_TOOL_ROUNDS):
        tool_use_blocks = []
        stop_reason = 'end_turn'
        content = []
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
                    tool_use_blocks.append({'tool': event, 'result': tool_result})
                    yield {'type': 'tool_result', 'tool_name': event['tool_name'],
                            'result': tool_result}
                elif event.get('type') == 'message_complete':
                    usage = event.get('usage', {})
                    input_tokens += usage.get('input_tokens', 0)
                    output_tokens += usage.get('output_tokens', 0)
                    stop_reason = event.get('stop_reason', 'end_turn')
                    content = event.get('content', [])
                    yield event
                elif event.get('type') == 'error':
                    yield event
                    return
        except Exception as e:
            yield {'type': 'error', 'error': f'{type(e).__name__}: {e}'}
            return

        if stop_reason != 'tool_use' or not tool_use_blocks:
            break

        messages.append({'role': 'assistant', 'content': content})
        tool_results = []
        for block in tool_use_blocks:
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': block['tool']['tool_use_id'],
                'content': json.dumps(block['result']) if isinstance(block['result'], dict) else str(block['result']),
            })
        messages.append({'role': 'user', 'content': tool_results})

    assistant_text = ''.join(assistant_text_parts)
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (?, ?, 'assistant', ?, ?)
    """, (sermon_id, conversation_id, assistant_text, _now()))
    conn.commit()
    conn.close()
