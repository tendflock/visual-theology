"""Sermon tagger taxonomy constants, LLM prompt builder, and entry point.

Defines the closed enums for dimension keys, section roles, and homiletic
moves used by the tagger prompt.  parse_tagger_output() validates and
filters the raw JSON that the LLM returns into a clean moment list.
build_tagger_prompt() assembles the system prompt.  tag_sermon() is the
entry point that orchestrates the full tagging pass.
"""

from __future__ import annotations
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Taxonomy constants ──────────────────────────────────────────────

DIMENSION_KEYS = frozenset({
    'burden_clarity', 'movement_clarity', 'application_specificity',
    'ethos_rating', 'concreteness_score', 'christ_thread_score',
    'exegetical_grounding',
})

SECTION_ROLES = frozenset({
    'intro', 'setup', 'exposition', 'illustration_section', 'application',
    'transition', 'recap', 'appeal', 'conclusion', 'prayer', 'reading',
})

HOMILETIC_MOVES = frozenset({
    'big_idea_statement', 'structure_signpost', 'textual_observation',
    'doctrinal_claim', 'illustration', 'exhortation', 'application',
    'christ_connection', 'gospel_implication', 'objection_handling',
    'direct_address', 'diagnostic_question', 'pastoral_comfort',
    'warning', 'summary_restatement', 'contextualization',
})

CONFIDENCE_FLOOR = 0.65
MAX_MOMENTS_PER_SERMON = 18
TAGGER_PROMPT_VERSION = '1.0.0'

_VALID_VALENCES = {'positive', 'negative'}
_VALID_IMPACTS = {'minor', 'moderate', 'major'}


# ── Output parser ───────────────────────────────────────────────────

def parse_tagger_output(raw: dict) -> list[dict]:
    """Validate, fix up, and filter moments from the tagger LLM response.

    *raw* is the parsed JSON dict the LLM returned.  Expected shape::

        {"moments": [ {dimension_key, valence, ...}, ... ]}

    Returns a list of validated moment dicts, sorted by confidence
    descending and capped at MAX_MOMENTS_PER_SERMON.
    """
    moments = raw.get('moments')
    if not isinstance(moments, list):
        return []

    accepted: list[dict] = []
    for m in moments:
        if not isinstance(m, dict):
            continue

        # ── Hard-drop checks ────────────────────────────────────
        if m.get('dimension_key') not in DIMENSION_KEYS:
            continue
        if m.get('valence') not in _VALID_VALENCES:
            continue
        if m.get('section_role') not in SECTION_ROLES:
            continue
        if m.get('impact') not in _VALID_IMPACTS:
            continue

        conf = m.get('confidence')
        if not isinstance(conf, (int, float)):
            continue
        if conf < CONFIDENCE_FLOOR:
            continue

        excerpt = m.get('excerpt_text')
        if not isinstance(excerpt, str) or not excerpt.strip():
            continue

        rationale = m.get('rationale')
        if not isinstance(rationale, str) or not rationale.strip():
            continue

        if not isinstance(m.get('start_segment_index'), int):
            continue
        if not isinstance(m.get('end_segment_index'), int):
            continue

        # ── Fixup rules (repair, don't drop) ────────────────────
        if m.get('homiletic_move') not in HOMILETIC_MOVES:
            m['homiletic_move'] = None

        if conf > 1.0:
            conf = 1.0
            m['confidence'] = conf

        accepted.append(m)

    # Sort by confidence descending, then cap.
    accepted.sort(key=lambda x: x['confidence'], reverse=True)
    return accepted[:MAX_MOMENTS_PER_SERMON]


# ── JSON schema for structured LLM output ─────────────────────────

TAGGER_OUTPUT_SCHEMA = {
    'type': 'object',
    'required': ['moments'],
    'properties': {
        'moments': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['dimension_key', 'section_role', 'valence', 'confidence',
                             'impact', 'start_segment_index', 'end_segment_index',
                             'excerpt_text', 'rationale', 'review_source_ref'],
                'properties': {
                    'dimension_key': {'type': 'string'},
                    'section_role': {'type': 'string'},
                    'homiletic_move': {'type': ['string', 'null']},
                    'valence': {'type': 'string', 'enum': ['positive', 'negative']},
                    'confidence': {'type': 'number'},
                    'impact': {'type': 'string', 'enum': ['minor', 'moderate', 'major']},
                    'start_segment_index': {'type': 'integer'},
                    'end_segment_index': {'type': 'integer'},
                    'excerpt_text': {'type': 'string'},
                    'context_text': {'type': ['string', 'null']},
                    'rationale': {'type': 'string'},
                    'review_source_ref': {'type': 'string'},
                }
            }
        }
    }
}


# ── Dimension definitions for the prompt ───────────────────────────

_DIMENSION_DEFINITIONS = {
    'burden_clarity': (
        'The sermon\'s central burden (big idea / thesis). '
        'Positive: burden stated explicitly, repeated, and threaded through the sermon. '
        'Negative: burden is vague, contradicted, or never surfaced.'
    ),
    'movement_clarity': (
        'Whether the sermon flows as a river (clear forward momentum) vs. a lake (circling). '
        'Positive: clear transitions, logical progression, structure signposts. '
        'Negative: repetitive loops, abrupt topic shifts, unclear connections between points.'
    ),
    'application_specificity': (
        'How concrete and actionable the applications are. '
        'Positive: localized to specific situations, names real actions or decisions. '
        'Negative: abstract moralizing, generic exhortations ("be more faithful"), no specifics.'
    ),
    'ethos_rating': (
        'Whether the preacher\'s presence seizes attention or feels detached. '
        'Positive: personal vulnerability, pastoral warmth, direct address, urgency. '
        'Negative: academic distance, reading-from-notes monotone, no eye contact markers.'
    ),
    'concreteness_score': (
        'Density of concrete imagery, stories, and sensory language. '
        'Positive: vivid illustrations, named characters, sensory details, narrative moments. '
        'Negative: abstract theological chains, long stretches of propositional statements only.'
    ),
    'christ_thread_score': (
        'Whether Christ is explicitly connected to the text, not just appended. '
        'Positive: organic christological connection grounded in the passage\'s redemptive context. '
        'Negative: tacked-on gospel summary disconnected from the text, or Christ never mentioned.'
    ),
    'exegetical_grounding': (
        'Whether claims arise from the text or are imported onto it. '
        'Positive: observations anchored in specific words/phrases/structure of the passage. '
        'Negative: eisegesis, proof-texting, claims unsupported by the passage at hand.'
    ),
}

_SECTION_ROLE_DEFINITIONS = {
    'intro': 'Opening — hook, welcome, or scene-setting before the text is read.',
    'setup': 'Context-setting after intro — historical background, book overview, series recap.',
    'exposition': 'Core exegetical work — explaining the text verse by verse or section by section.',
    'illustration_section': 'Extended illustration, story, or analogy (more than a one-liner).',
    'application': 'Direct application — "so what does this mean for you this week?"',
    'transition': 'Bridge between major sections or points.',
    'recap': 'Summary or restatement of ground already covered.',
    'appeal': 'Direct call to action, invitation, or challenge.',
    'conclusion': 'Closing — wrapping up, final word, benediction lead-in.',
    'prayer': 'Prayer within the sermon (opening, closing, or mid-sermon).',
    'reading': 'Scripture reading (the passage itself being read aloud).',
}

_HOMILETIC_MOVE_DEFINITIONS = {
    'big_idea_statement': 'Explicit statement of the sermon\'s central thesis or burden.',
    'structure_signpost': 'Verbal marker of sermon structure ("my second point is...", "finally...").',
    'textual_observation': 'Pointing out something specific in the biblical text.',
    'doctrinal_claim': 'Theological assertion or doctrinal teaching.',
    'illustration': 'Story, analogy, or image used to illuminate a point.',
    'exhortation': 'Direct urging or encouragement.',
    'application': 'Concrete "so what" — connecting text to life.',
    'christ_connection': 'Explicit link to Christ, the gospel, or redemptive history.',
    'gospel_implication': 'Drawing out what the gospel means for the situation at hand.',
    'objection_handling': 'Anticipating and answering a listener\'s objection.',
    'direct_address': 'Speaking directly to the congregation ("you", "we", "brothers and sisters").',
    'diagnostic_question': 'Question aimed at self-examination ("have you ever...?").',
    'pastoral_comfort': 'Words of comfort, assurance, or grace.',
    'warning': 'Sobering caution or admonition.',
    'summary_restatement': 'Restating a prior point in compressed form.',
    'contextualization': 'Connecting the ancient text to contemporary culture or experience.',
}


# ── Prompt builder ─────────────────────────────────────────────────

TAGGER_SYSTEM_PROMPT = """You are a homiletical analysis tagger. Your job is to identify specific transcript moments that exemplify coaching dimensions.

You will receive a sermon transcript broken into numbered segments, a set of review scores as prior context, and the taxonomy definitions below. Your task is to find concrete moments in the transcript that serve as evidence for or against each coaching dimension.

## DIMENSION DEFINITIONS

{dimension_defs}

## SECTION ROLES

{section_role_defs}

## HOMILETIC MOVES

{homiletic_move_defs}

## OUTPUT CONTRACT

- Tag 0-4 moments per dimension, maximum 2 per valence (positive or negative).
- Maximum 18 total moments across all dimensions.
- Prefer fewer, higher-confidence moments over filling slots.
- The same transcript span may be tagged under multiple dimensions.
- Provide a contiguous segment index range (start_segment_index to end_segment_index, inclusive).
- excerpt_text must be a VERBATIM copy from the transcript — do not paraphrase, summarize, or edit.
- Abstain when evidence is weak. Returning zero moments for a dimension is acceptable.

## ANTI-HALLUCINATION RULES

- excerpt_text MUST be a verbatim substring from one of the provided transcript segments. Do not rephrase.
- Do NOT infer audience response, emotion, or vocal tone from text alone.
- Do NOT treat orthodox theology as automatically effective rhetoric. Sound doctrine poorly communicated still hurts impact.
- If a moment's significance depends on vocal delivery, tone, or pacing (which you cannot observe), ABSTAIN.
- Prefer representative moments over merely striking ones. A typical example of a pattern matters more than an outlier."""


def build_tagger_prompt(transcript_segments: list, review: dict,
                        sermon_context: dict) -> str:
    """Assemble the user prompt for the tagger LLM call.

    *transcript_segments* is the list of SRT segment dicts with
    segment_index, start_ms, end_ms, text.

    *review* is the dict from sermon_reviews (or an empty dict if none).

    *sermon_context* has title, passage, duration_sec.
    """
    # Format dimension definitions
    dim_lines = []
    for key, defn in _DIMENSION_DEFINITIONS.items():
        dim_lines.append(f'- **{key}**: {defn}')
    dimension_defs = '\n'.join(dim_lines)

    # Format section role definitions
    sr_lines = []
    for role, defn in _SECTION_ROLE_DEFINITIONS.items():
        sr_lines.append(f'- **{role}**: {defn}')
    section_role_defs = '\n'.join(sr_lines)

    # Format homiletic move definitions
    hm_lines = []
    for move, defn in _HOMILETIC_MOVE_DEFINITIONS.items():
        hm_lines.append(f'- **{move}**: {defn}')
    homiletic_move_defs = '\n'.join(hm_lines)

    system = TAGGER_SYSTEM_PROMPT.format(
        dimension_defs=dimension_defs,
        section_role_defs=section_role_defs,
        homiletic_move_defs=homiletic_move_defs,
    )

    # Build review scores as prior context
    review_lines = ['## REVIEW SCORES (prior context)']
    score_keys = [
        ('burden_clarity', 'Burden clarity'),
        ('movement_clarity', 'Movement clarity'),
        ('application_specificity', 'Application specificity'),
        ('ethos_rating', 'Ethos rating'),
        ('concreteness_score', 'Concreteness score'),
        ('christ_thread_score', 'Christ thread score'),
        ('exegetical_grounding', 'Exegetical grounding'),
    ]
    for db_key, label in score_keys:
        val = review.get(db_key, 'N/A')
        review_lines.append(f'- {label}: {val}')
    review_block = '\n'.join(review_lines)

    # Build transcript segments block
    seg_lines = ['## TRANSCRIPT SEGMENTS']
    for seg in transcript_segments:
        idx = seg.get('segment_index', 0)
        s_ms = seg.get('start_ms', 0)
        e_ms = seg.get('end_ms', 0)
        text = seg.get('text', '')
        seg_lines.append(f'[{idx}] ({s_ms}-{e_ms}ms) {text}')
    transcript_block = '\n'.join(seg_lines)

    title = sermon_context.get('title', 'Untitled')
    passage = sermon_context.get('passage', 'Unknown')
    dur = sermon_context.get('duration_sec', 0)

    user_prompt = f"""{system}

## SERMON METADATA
Title: {title}
Passage: {passage}
Duration: {dur} seconds ({dur // 60}:{dur % 60:02d})

{review_block}

{transcript_block}

Tag this sermon per the output contract. Return the moments array via the tool."""

    return user_prompt


# ── Entry point ────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tag_sermon(db, sermon_id: int, llm_client, review_run_id: str | None = None) -> dict:
    """Run the tagging pass for a single sermon.

    Returns {run_id, moments_stored, moments_suppressed, status}.
    """
    conn = db._conn()
    try:
        # ── 1. Fetch sermon data ────────────────────────────────
        row = conn.execute("""
            SELECT id, transcript_segments, duration_seconds, title, bible_text_raw
            FROM sermons WHERE id = ?
        """, (sermon_id,)).fetchone()
        if not row:
            return {'status': 'skipped', 'reason': 'sermon_not_found'}

        seg_json = row['transcript_segments']
        duration_sec = row['duration_seconds'] or 0
        title = row['title'] or 'Untitled'
        bible_text_raw = row['bible_text_raw'] or ''

        if not seg_json or duration_sec <= 0:
            return {'status': 'skipped', 'reason': 'no_segments_or_zero_duration'}

        transcript_segments = json.loads(seg_json)

        # ── 2. Fetch active review ──────────────────────────────
        review_row = conn.execute("""
            SELECT * FROM sermon_reviews WHERE sermon_id = ?
            ORDER BY computed_at DESC LIMIT 1
        """, (sermon_id,)).fetchone()
        review = dict(review_row) if review_row else {}

        # ── 3. Create analysis_runs row ─────────────────────────
        run_id = str(uuid.uuid4())
        now = _now()
        conn.execute("""
            INSERT INTO analysis_runs (id, sermon_id, run_type, review_run_id,
                                       prompt_version, model_name, is_active, status, created_at)
            VALUES (?, ?, 'tagging', ?, ?, 'claude-opus-4-6', 0, 'running', ?)
        """, (run_id, sermon_id, review_run_id, TAGGER_PROMPT_VERSION, now))
        conn.commit()

        # ── 4. Build prompt and call LLM ────────────────────────
        sermon_context = {
            'title': title,
            'passage': bible_text_raw,
            'duration_sec': duration_sec,
        }
        prompt = build_tagger_prompt(transcript_segments, review, sermon_context)
        result = llm_client.call(prompt=prompt, schema=TAGGER_OUTPUT_SCHEMA)

        if 'error' in result:
            conn.execute("""
                UPDATE analysis_runs SET status='failed' WHERE id=?
            """, (run_id,))
            conn.commit()
            return {'run_id': run_id, 'status': 'failed', 'error': result['error']}

        # ── 5. Parse and validate moments ───────────────────────
        output = result.get('output', {})
        validated = parse_tagger_output(output)
        suppressed = len(output.get('moments', [])) - len(validated)

        # ── 6. Build segment lookup for start_ms / end_ms ───────
        seg_by_idx = {s['segment_index']: s for s in transcript_segments}

        # ── 7. Compute position and rank, then insert ───────────
        # Group by (dimension_key, valence) for moment_rank assignment.
        # Moments are already sorted by confidence descending from the parser.
        rank_counters: dict[tuple[str, str], int] = defaultdict(int)

        moments_stored = 0
        for m in validated:
            start_idx = m['start_segment_index']
            end_idx = m['end_segment_index']

            start_seg = seg_by_idx.get(start_idx)
            end_seg = seg_by_idx.get(end_idx)
            if not start_seg or not end_seg:
                suppressed += 1
                continue

            start_ms = start_seg['start_ms']
            end_ms = end_seg['end_ms']
            midpoint_ms = (start_ms + end_ms) / 2
            sermon_position_pct = min(1.0, midpoint_ms / (duration_sec * 1000))

            group_key = (m['dimension_key'], m['valence'])
            rank_counters[group_key] += 1
            moment_rank = rank_counters[group_key]

            conn.execute("""
                INSERT INTO sermon_moments (
                    sermon_id, analysis_run_id,
                    start_segment_index, end_segment_index,
                    start_ms, end_ms, sermon_position_pct,
                    excerpt_text, context_text,
                    dimension_key, section_role, homiletic_move,
                    valence, confidence, impact, moment_rank,
                    rationale, review_source_ref,
                    prompt_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sermon_id, run_id,
                start_idx, end_idx,
                start_ms, end_ms, sermon_position_pct,
                m['excerpt_text'], m.get('context_text'),
                m['dimension_key'], m['section_role'], m.get('homiletic_move'),
                m['valence'], m['confidence'], m['impact'], moment_rank,
                m['rationale'], m.get('review_source_ref'),
                TAGGER_PROMPT_VERSION, now,
            ))
            moments_stored += 1

        # ── 8. Deactivate prior tagging runs for this sermon ────
        conn.execute("""
            UPDATE analysis_runs SET is_active=0
            WHERE sermon_id=? AND run_type='tagging' AND id != ?
        """, (sermon_id, run_id))

        # ── 9. Mark this run completed and active ───────────────
        conn.execute("""
            UPDATE analysis_runs SET status='completed', is_active=1 WHERE id=?
        """, (run_id,))

        # ── 10. Log cost ────────────────────────────────────────
        input_tokens = result.get('input_tokens', 0)
        output_tokens = result.get('output_tokens', 0)
        model = result.get('model', 'claude-opus-4-6')

        from sermon_analyzer import estimate_cost_usd
        cost = estimate_cost_usd(model, input_tokens, output_tokens)
        conn.execute("""
            INSERT INTO sermon_analysis_cost_log
                (sermon_id, model, input_tokens, output_tokens, estimated_cost_usd, called_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sermon_id, model, input_tokens, output_tokens, cost, now))

        conn.commit()
        return {
            'run_id': run_id,
            'moments_stored': moments_stored,
            'moments_suppressed': suppressed,
            'status': 'completed',
        }

    except Exception as e:
        # Mark run as failed if it was created
        try:
            conn.execute("UPDATE analysis_runs SET status='failed' WHERE id=?", (run_id,))
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        conn.close()
