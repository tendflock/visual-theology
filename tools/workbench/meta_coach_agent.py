"""Meta-coach agent — corpus-scoped streaming coach for the patterns page.

Follows the same streaming tool-use loop as sermon_coach_agent.py but
operates on aggregate data across sermons rather than a single sermon.
Uses meta_coach_tools.py for all 11 corpus-scoped query tools.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS
from shared_prompts import HOMILETICAL_FRAMEWORK, LONGITUDINAL_POSTURE_RULE
from sermon_coach_tools import get_sermon_patterns
from meta_coach_tools import (
    get_corpus_dimension_summary, get_dimension_trend,
    get_dimension_distribution, get_representative_moments,
    get_counterexamples, get_sermon_context, get_sermon_moment_sequence,
    compare_periods, get_evidence_quality, get_data_freshness,
    get_active_commitment,
)
from priority_ranker import compute_priority_ranking


# ── Tool definitions ──────────────────────────────────────────────

META_TOOL_DEFINITIONS = [
    {
        'name': 'get_corpus_dimension_summary',
        'description': 'Per-dimension aggregate stats across the corpus: positive/negative counts, rates, median confidence.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'window_days': {'type': 'integer', 'default': 90},
                'min_confidence': {'type': 'number', 'default': 0.65},
                'series': {'type': 'string'},
            },
        },
    },
    {
        'name': 'get_dimension_trend',
        'description': 'Dimension scores over time — one row per sermon ordered by preach_date. Use to see improvement or regression.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'dimension': {'type': 'string'},
                'window_days': {'type': 'integer', 'default': 90},
                'min_confidence': {'type': 'number', 'default': 0.65},
            },
            'required': ['dimension'],
        },
    },
    {
        'name': 'get_dimension_distribution',
        'description': 'Variance/spread for one dimension — net score per sermon to see consistency vs. volatility.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'dimension': {'type': 'string'},
                'window_days': {'type': 'integer', 'default': 90},
            },
            'required': ['dimension'],
        },
    },
    {
        'name': 'get_representative_moments',
        'description': 'Top moments for a dimension + valence, with sermon context and timestamps. Use for evidence citations.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'dimension': {'type': 'string'},
                'valence': {'type': 'string', 'enum': ['positive', 'negative']},
                'sort': {'type': 'string', 'enum': [
                    'confidence_desc', 'recency_desc', 'impact_desc', 'position_asc',
                ]},
                'per_sermon_cap': {'type': 'integer', 'default': 2},
                'min_confidence': {'type': 'number', 'default': 0.65},
                'window_days': {'type': 'integer', 'default': 90},
            },
            'required': ['dimension', 'valence'],
        },
    },
    {
        'name': 'get_counterexamples',
        'description': 'Sermons where a typically weak dimension was unusually strong. Use to pair critiques with evidence that Bryan CAN do this.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'dimension': {'type': 'string'},
                'target_pattern': {'type': 'string', 'enum': [
                    'recurring_weakness', 'inconsistent_strength', 'improving_weakness',
                ]},
            },
            'required': ['dimension'],
        },
    },
    {
        'name': 'get_sermon_context',
        'description': 'Single sermon metadata + review scores (no moment data). Use when drilling into a specific sermon.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'sermon_id': {'type': 'integer'},
            },
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'get_sermon_moment_sequence',
        'description': 'Moments ordered through the sermon arc (by start_ms). Optionally filter to one dimension.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'sermon_id': {'type': 'integer'},
                'dimension': {'type': 'string'},
            },
            'required': ['sermon_id'],
        },
    },
    {
        'name': 'compare_periods',
        'description': 'Compare dimension stats between two date ranges. Use for before/after comparisons.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'period_a': {
                    'type': 'object',
                    'properties': {
                        'start_date': {'type': 'string'},
                        'end_date': {'type': 'string'},
                    },
                    'required': ['start_date', 'end_date'],
                },
                'period_b': {
                    'type': 'object',
                    'properties': {
                        'start_date': {'type': 'string'},
                        'end_date': {'type': 'string'},
                    },
                    'required': ['start_date', 'end_date'],
                },
                'dimensions': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
            },
            'required': ['period_a', 'period_b'],
        },
    },
    {
        'name': 'get_evidence_quality',
        'description': 'Uncertainty report — how much to trust the moment data. Check this before making strong claims.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'window_days': {'type': 'integer', 'default': 90},
                'min_confidence': {'type': 'number', 'default': 0.65},
            },
        },
    },
    {
        'name': 'get_data_freshness',
        'description': 'Pipeline completeness — how much of the sermon corpus has been processed (transcribed, reviewed, tagged).',
        'input_schema': {
            'type': 'object',
            'properties': {},
        },
    },
    {
        'name': 'get_active_commitment',
        'description': 'Current coaching commitment and progress toward it. Returns null if no active commitment.',
        'input_schema': {
            'type': 'object',
            'properties': {},
        },
    },
]


# ── Tool dispatcher ───────────────────────────────────────────────

def execute_meta_tool(tool_name: str, tool_input: dict,
                      session_context: dict) -> dict:
    """Dispatch a meta-coach tool call."""
    db = session_context['db']
    try:
        if tool_name == 'get_corpus_dimension_summary':
            return {'dimensions': get_corpus_dimension_summary(
                db,
                window_days=tool_input.get('window_days', 90),
                min_confidence=tool_input.get('min_confidence', 0.65),
                series=tool_input.get('series'),
            )}
        if tool_name == 'get_dimension_trend':
            return {'trend': get_dimension_trend(
                db, tool_input['dimension'],
                window_days=tool_input.get('window_days', 90),
                min_confidence=tool_input.get('min_confidence', 0.65),
            )}
        if tool_name == 'get_dimension_distribution':
            return get_dimension_distribution(
                db, tool_input['dimension'],
                window_days=tool_input.get('window_days', 90),
            )
        if tool_name == 'get_representative_moments':
            return {'moments': get_representative_moments(
                db, tool_input['dimension'], tool_input['valence'],
                sort=tool_input.get('sort', 'confidence_desc'),
                per_sermon_cap=tool_input.get('per_sermon_cap', 2),
                min_confidence=tool_input.get('min_confidence', 0.65),
                window_days=tool_input.get('window_days', 90),
            )}
        if tool_name == 'get_counterexamples':
            return {'counterexamples': get_counterexamples(
                db, tool_input['dimension'],
                target_pattern=tool_input.get('target_pattern', 'recurring_weakness'),
            )}
        if tool_name == 'get_sermon_context':
            ctx = get_sermon_context(db, tool_input['sermon_id'])
            return ctx if ctx else {'error': 'sermon not found'}
        if tool_name == 'get_sermon_moment_sequence':
            return {'moments': get_sermon_moment_sequence(
                db, tool_input['sermon_id'],
                dimension=tool_input.get('dimension'),
            )}
        if tool_name == 'compare_periods':
            return compare_periods(
                db, tool_input['period_a'], tool_input['period_b'],
                dimensions=tool_input.get('dimensions'),
            )
        if tool_name == 'get_evidence_quality':
            return get_evidence_quality(
                db,
                window_days=tool_input.get('window_days', 90),
                min_confidence=tool_input.get('min_confidence', 0.65),
            )
        if tool_name == 'get_data_freshness':
            return get_data_freshness(db)
        if tool_name == 'get_active_commitment':
            commitment = get_active_commitment(db)
            return commitment if commitment else {'active': False}
        return {'error': f'unknown tool: {tool_name}'}
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}


# ── System prompt builder ─────────────────────────────────────────

def build_meta_system_prompt(patterns: dict, ranking: list[dict],
                             memory_summary: dict,
                             evidence_quality: dict) -> str:
    """Assemble the meta-coach system prompt."""
    sections = [
        IDENTITY_CORE,
        HOMILETICAL_TRADITION,
        VOICE_GUARDRAILS,
        HOMILETICAL_FRAMEWORK,
        LONGITUDINAL_POSTURE_RULE.replace(
            '{corpus_gate_status}', patterns.get('corpus_gate_status', 'pre_gate'),
        ),
        _corpus_summary_section(patterns),
        _priority_ranking_section(ranking),
        _memory_summary_section(memory_summary),
        _evidence_quality_section(evidence_quality),
        _tools_section(),
        _behavioral_constraints(),
    ]
    return '\n\n'.join(s for s in sections if s)


def _corpus_summary_section(patterns: dict) -> str:
    lines = ["## Corpus Summary"]
    lines.append(f"- Sermons in window: {patterns.get('n_sermons', 0)}")
    lines.append(f"- Corpus gate: {patterns.get('corpus_gate_status', 'pre_gate')}")
    lines.append(f"- Window: {patterns.get('window_days', 90)} days")

    rate_fields = [
        ('burden_clear_rate', 'Burden clarity rate'),
        ('movement_clear_rate', 'Movement clarity rate'),
        ('application_concrete_rate', 'Application concrete rate'),
        ('ethos_engaged_rate', 'Ethos engaged rate'),
        ('christ_explicit_rate', 'Christ thread explicit rate'),
        ('exegetical_grounded_rate', 'Exegetical grounded rate'),
    ]
    for key, label in rate_fields:
        val = patterns.get(key)
        if val is not None:
            lines.append(f"- {label}: {val:.0%}")

    avg_fields = [
        ('avg_concreteness', 'Avg concreteness'),
        ('avg_outline_coverage', 'Avg outline coverage'),
        ('avg_duration_delta_sec', 'Avg duration delta (sec)'),
    ]
    for key, label in avg_fields:
        val = patterns.get(key)
        if val is not None:
            lines.append(f"- {label}: {val:.1f}")

    return '\n'.join(lines)


def _priority_ranking_section(ranking: list[dict]) -> str:
    if not ranking:
        return "## Priority Ranking\n\n(no ranking computed)"
    lines = ["## Priority Ranking (most urgent first)\n"]
    for r in ranking:
        lines.append(
            f"{r['overall_rank']}. **{r['dimension_key']}** "
            f"(overall={r['overall_score']:.3f}, "
            f"impact={r['impact_priority_score']:.3f}, "
            f"evidence={r['evidence_strength_score']:.3f}, "
            f"trajectory={r['trajectory_score']:.3f}, "
            f"actionability={r['actionability_score']:.2f}, "
            f"neg_moments={r['n_negative_moments']})"
        )
    return '\n'.join(lines)


def _memory_summary_section(memory: dict) -> str:
    lines = ["## Coach Memory"]
    commitment = memory.get('active_commitment')
    if commitment:
        lines.append(f"- Active commitment: {commitment.get('practice_experiment', '(none)')}")
        lines.append(f"  - Dimension: {commitment.get('dimension_key')}")
        lines.append(f"  - Target sermons: {commitment.get('target_sermons')}")
        progress = commitment.get('progress', {})
        lines.append(f"  - Sermons since: {progress.get('sermons_since', 0)}")
        lines.append(f"  - Positive moments found: {progress.get('positive_moments_found', 0)}")
        lines.append(f"  - Negative moments found: {progress.get('negative_moments_found', 0)}")
    else:
        lines.append("- No active coaching commitment.")

    recent = memory.get('recent_commitments', [])
    if recent:
        lines.append("- Recent commitments:")
        for c in recent:
            lines.append(f"  - [{c.get('status', '?')}] {c.get('dimension_key')}: "
                         f"{c.get('practice_experiment', '?')}")

    return '\n'.join(lines)


def _evidence_quality_section(eq: dict) -> str:
    lines = ["## Evidence Quality"]
    lines.append(f"- Sermons analyzed: {eq.get('total_sermons_analyzed', 0)}")
    lines.append(f"- Total moments: {eq.get('total_moments', 0)}")
    lines.append(f"- Low-confidence moments: {eq.get('low_confidence_pct', 0):.0%}")
    thin = eq.get('dimensions_with_few_moments', [])
    if thin:
        lines.append(f"- Thin dimensions (<3 moments): {', '.join(thin)}")
    lines.append(f"- Sermons missing tagging: {eq.get('sermons_missing_tagging', 0)}")
    return '\n'.join(lines)


def _tools_section() -> str:
    lines = ["## Tools Available\n"]
    for tool in META_TOOL_DEFINITIONS:
        lines.append(f"- **{tool['name']}**: {tool['description']}")
    return '\n'.join(lines)


def _behavioral_constraints() -> str:
    return """## Meta-Coach Behavioral Constraints

- Start from the top 3 ranked priorities. Choose the one that best combines
  ministry impact, evidence strength, and coachable next-step clarity.
  If you do not choose rank #1, explain why in one sentence.
- Lead with Impact tier (Tier 1).
- Cite evidence pastorally: "across 6 of the last 8 sermons, application
  becomes concrete only in the closing minute" — not "application weak."
- Provide timestamps when drilling into specific sermons.
- Never conflate current-sermon observation with historical pattern with trajectory.
- Every critique tries to pair a counterexample (when the dimension was strong).
- Do not infer causes unless evidence supports them — name the pattern before the reason.
- If top issue is too abstract, translate it into a behavioral experiment.
- If same priority surfaced repeatedly with no change, vary the intervention.
- Classify every pattern claim as: recurring weakness, inconsistent strength,
  improving weakness, or one-off anomaly.
- When evidence conflicts, classify as: inconsistent execution,
  context-dependent variation, or recent improvement/regression.

Evidence thresholds:
- No "consistently" or "always" unless 5+ sermons AND 3+ distinct moments
  across 3+ distinct sermons support it.
- In pre_gate (<5 sermons): "Too early for corpus claims."
- In emerging (5-9): prefer "emerging signal" and "watch area" language.
- Must cite specific sermon count and moment count.
- When evidence is thin, say so explicitly."""


# ── Streaming response generator ──────────────────────────────────

MAX_TOOL_ROUNDS = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_moments_for_ranking(db, window_days: int = 90) -> list[dict]:
    """Fetch all moments in the window for priority ranking input."""
    conn = db._conn()
    try:
        cur = conn.execute("""
            SELECT sm.dimension_key, sm.valence, sm.confidence, sm.impact,
                   sm.sermon_id
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
            WHERE ar.is_active = 1
              AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
              AND s.preach_date >= date('now', '-' || ? || ' days')
        """, (int(window_days),))
        desc = cur.description
        return [{desc[i][0]: row[i] for i in range(len(desc))}
                for row in cur.fetchall()]
    finally:
        conn.close()


def _build_memory_summary(db) -> dict:
    """Build the coach memory summary from commitments."""
    active = get_active_commitment(db)
    conn = db._conn()
    try:
        cur = conn.execute("""
            SELECT dimension_key, practice_experiment, status, created_at
            FROM coaching_commitments
            ORDER BY created_at DESC LIMIT 5
        """)
        recent = [
            {'dimension_key': r[0], 'practice_experiment': r[1],
             'status': r[2], 'created_at': r[3]}
            for r in cur.fetchall()
        ]
    finally:
        conn.close()
    return {
        'active_commitment': active,
        'recent_commitments': recent,
    }


def stream_meta_coach_response(db, conversation_id: int,
                               user_message: str, llm_client):
    """Generator that streams meta-coach output events and persists messages.

    Unlike stream_coach_response, this operates without a sermon_id —
    all queries use sermon_id IS NULL to distinguish meta-coach messages.
    """
    # Persist user message (sermon_id=NULL for meta-coach)
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (NULL, ?, 'user', ?, ?)
    """, (conversation_id, user_message, _now()))
    conn.commit()
    conn.close()

    # Gather context for the system prompt
    patterns = get_sermon_patterns(db)
    n_sermons = patterns.get('n_sermons', 0)

    moments = _fetch_moments_for_ranking(db, window_days=patterns.get('window_days', 90))
    ranking = compute_priority_ranking(moments, n_sermons)

    memory_summary = _build_memory_summary(db)
    evidence = get_evidence_quality(db)

    system = build_meta_system_prompt(patterns, ranking, memory_summary, evidence)

    # Load conversation history
    conn = db._conn()
    history_rows = conn.execute("""
        SELECT role, content FROM sermon_coach_messages
        WHERE sermon_id IS NULL AND conversation_id = ?
        ORDER BY id
    """, (conversation_id,)).fetchall()
    conn.close()
    messages = [{'role': r[0], 'content': r[1]} for r in history_rows if r[1]]

    # Streaming tool-use loop
    assistant_text_parts = []
    input_tokens = 0
    output_tokens = 0

    for _round in range(MAX_TOOL_ROUNDS):
        tool_use_blocks = []
        stop_reason = 'end_turn'
        content = []
        try:
            for event in llm_client.stream_message(system=system, messages=messages,
                                                   tools=META_TOOL_DEFINITIONS):
                if event.get('type') == 'text_delta':
                    assistant_text_parts.append(event.get('text', ''))
                    yield event
                elif event.get('type') == 'tool_use':
                    tool_result = execute_meta_tool(
                        event['tool_name'], event['tool_input'],
                        session_context={'db': db},
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

        # Feed tool results back for the next round
        messages.append({'role': 'assistant', 'content': content})
        tool_results = []
        for block in tool_use_blocks:
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': block['tool']['tool_use_id'],
                'content': json.dumps(block['result']) if isinstance(block['result'], dict) else str(block['result']),
            })
        messages.append({'role': 'user', 'content': tool_results})

    # Persist assistant message
    assistant_text = ''.join(assistant_text_parts)
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_coach_messages
            (sermon_id, conversation_id, role, content, created_at)
        VALUES (NULL, ?, 'assistant', ?, ?)
    """, (conversation_id, assistant_text, _now()))
    conn.commit()
    conn.close()
