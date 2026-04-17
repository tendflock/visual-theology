"""Sermon analyzer — deterministic stages + one structured LLM call.

Stages 1-4 are pure. Stage 5 (LLM rubric pass) and stage 6 (writer + dispatch)
come in Tasks 12 and 13.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
import logging

from homiletics_core import (
    __version__ as homiletics_core_version,
    segment_transcript,
    compute_section_timings,
    detect_density_hotspots,
    align_segments_to_outline,
    late_application,
)

ANALYZER_VERSION = '1.0.0'

# Bryan's wife's stated target is 25-30 min; midpoint is 27.5 min ≈ 1650 sec.
# Round to 28 min = 1680 sec for a slightly more forgiving default.
# Phase 2 will read a per-session target from prep data; for MVP this default
# makes duration_delta_seconds non-null for every sermon so the length signal works.
DEFAULT_PLANNED_DURATION_SEC = 1680


@dataclass(frozen=True)
class AnalyzerInput:
    sermon_id: int
    transcript_text: str
    duration_sec: int
    planned_duration_sec: Optional[int]
    outline_points: list = field(default_factory=list)
    bible_text_raw: str = ''
    srt_segments: list = field(default=None)


@dataclass(frozen=True)
class PureStageOutput:
    segments: list
    section_timings: dict
    actual_duration_sec: int
    planned_duration_sec: Optional[int]
    duration_delta_sec: Optional[int]
    density_hotspots: list
    outline_coverage_pct: Optional[float]
    outline_additions: list
    outline_omissions: list


def run_pure_stages(inp: AnalyzerInput) -> PureStageOutput:
    """Stages 1-4: segment, align, timing, density. Pure and cheap."""
    if inp.srt_segments:
        from srt_parser import coarsen_srt_segments
        segments = coarsen_srt_segments(inp.srt_segments, inp.duration_sec)
    else:
        segments = segment_transcript(inp.transcript_text, inp.duration_sec)
    aligned = align_segments_to_outline(segments, inp.outline_points) if inp.outline_points else segments
    section_timings = compute_section_timings(aligned)
    density_hotspots = detect_density_hotspots(aligned)

    duration_delta = (
        inp.duration_sec - inp.planned_duration_sec
        if inp.planned_duration_sec is not None else None
    )

    if inp.outline_points:
        matched_point_ids = set()
        for seg in aligned:
            for pid in seg.get('outline_point_ids', []):
                matched_point_ids.add(pid)
        total = len(inp.outline_points)
        coverage_pct = len(matched_point_ids) / total if total else None
        omitted = [p for p in inp.outline_points if p.get('id') not in matched_point_ids]
        additions = []
    else:
        coverage_pct = None
        omitted = []
        additions = []

    return PureStageOutput(
        segments=aligned,
        section_timings=section_timings,
        actual_duration_sec=inp.duration_sec,
        planned_duration_sec=inp.planned_duration_sec,
        duration_delta_sec=duration_delta,
        density_hotspots=density_hotspots,
        outline_coverage_pct=coverage_pct,
        outline_additions=additions,
        outline_omissions=omitted,
    )


REVIEW_SCHEMA = {
    'type': 'object',
    'required': ['tier1_impact', 'tier2_faithfulness', 'tier3_diagnostic',
                 'coach_summary', 'flags'],
    'properties': {
        'tier1_impact': {
            'type': 'object',
            'required': ['burden_clarity', 'movement_clarity', 'application_specificity',
                         'application_landing', 'opening_tension',
                         'ethos_rating', 'concreteness_score'],
            'properties': {
                'burden_clarity': {'type': 'string',
                                    'enum': ['crisp', 'clear', 'implied', 'muddled', 'absent']},
                'burden_statement_excerpt': {'type': ['string', 'null']},
                'burden_first_stated_at_sec': {'type': ['integer', 'null']},
                'movement_clarity': {'type': 'string',
                                      'enum': ['river', 'mostly_river', 'uneven', 'lake']},
                'movement_rationale': {'type': 'string'},
                'application_specificity': {'type': 'string',
                                             'enum': ['localized', 'concrete', 'abstract', 'absent']},
                'application_landing': {'type': 'string',
                                         'enum': ['pressed', 'touched', 'gestured', 'missed']},
                'application_first_arrived_at_sec': {'type': ['integer', 'null']},
                'application_excerpts': {'type': 'array', 'items': {'type': 'object'}},
                'opening_tension': {'type': 'string',
                                     'enum': ['strong', 'adequate', 'weak', 'absent']},
                'opening_tension_note': {'type': ['string', 'null']},
                'ethos_rating': {'type': 'string',
                                  'enum': ['seized', 'engaged', 'professional', 'detached']},
                'ethos_markers': {'type': 'array', 'items': {'type': 'string'}},
                'concreteness_score': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                'imagery_density_per_10min': {'type': 'number'},
                'narrative_moments': {'type': 'array', 'items': {'type': 'object'}},
            },
        },
        'tier2_faithfulness': {
            'type': 'object',
            'required': ['christ_thread_score', 'exegetical_grounding'],
            'properties': {
                'christ_thread_score': {'type': 'string',
                                         'enum': ['explicit', 'gestured', 'absent']},
                'christ_thread_excerpts': {'type': 'array', 'items': {'type': 'object'}},
                'exegetical_grounding': {'type': 'string',
                                          'enum': ['grounded', 'partial', 'pretext']},
                'exegetical_grounding_notes': {'type': 'string'},
            },
        },
        'tier3_diagnostic': {
            'type': 'object',
            'properties': {
                'length_delta_commentary': {'type': ['string', 'null']},
                'density_hotspots': {'type': 'array', 'items': {'type': 'object'}},
                'late_application_note': {'type': ['string', 'null']},
                'outline_drift_note': {'type': ['string', 'null']},
            },
        },
        'coach_summary': {
            'type': 'object',
            'required': ['top_impact_helpers', 'top_impact_hurters',
                         'one_change_for_next_sunday'],
            'properties': {
                'top_impact_helpers': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 3},
                'top_impact_hurters': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 3},
                'faithfulness_note': {'type': ['string', 'null']},
                'one_change_for_next_sunday': {'type': 'string'},
                'per_dimension_growth_edges': {'type': 'object'},
            },
        },
        'flags': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['flag_type', 'severity', 'rationale'],
                'properties': {
                    'flag_type': {'type': 'string'},
                    'severity': {'type': 'string', 'enum': ['info', 'note', 'warn', 'concern']},
                    'start_sec': {'type': ['integer', 'null']},
                    'end_sec': {'type': ['integer', 'null']},
                    'section_label': {'type': ['string', 'null']},
                    'excerpt': {'type': ['string', 'null']},
                    'rationale': {'type': 'string'},
                },
            },
        },
    },
}


RUBRIC_SYSTEM_PROMPT = """You are scoring a preached sermon for Bryan, a Reformed Presbyterian pastor.
Emit a structured review following the tool schema exactly.

SCORING METHOD — for every dimension you must:
1. Quote or paraphrase 1-2 specific transcript moments as evidence
2. State what level you are scoring and why
3. State why you did NOT score it one level higher (this prevents over-scoring)

## Tier 1: Impact (strongest predictors of whether the sermon lands)

### burden_clarity — Can the congregation say what the sermon was about?
- crisp: One sentence the congregation could repeat after leaving. Stated in the
  first 25% of the sermon and returned to at least once. The sermon orbits this sentence.
- clear: Identifiable theme, present throughout, but not crystallized into a single
  quotable sentence. A listener could paraphrase it but wouldn't use the same words.
- implied: The burden is inferable from the text but never explicitly stated. The
  preacher assumes the congregation will connect the dots.
- muddled: Multiple competing ideas. A listener would struggle to say what the sermon
  was about. More than one candidate burden and none clearly governs.
- absent: No discernible governing burden. The sermon covers material without a unifying claim.
DISQUALIFIER: If the burden is stated only in the final 10% of the sermon, cap at 'clear.'

### movement_clarity — Does the sermon move forward with intention?
- river: Crystal clear architecture. Every section earns its place. Transitions are
  signposted. The ending feels inevitable.
- mostly_river: Clear forward momentum. Occasional eddies (redundant examples, digressions)
  but overall direction is unmistakable.
- uneven: Structure present but loose. Some sections circle or repeat. Listener may lose
  the thread in places before it's recovered.
- lake: No clear forward movement. The sermon stays in one place, circles back repeatedly,
  or ends without a sense of arrival.

### application_specificity — How specific is the application?
- localized: Names a specific person, situation, or action the hearer can take THIS WEEK.
  "Picture the coworker you've been avoiding this conversation with. That's where this
  text meets your life." The listener can see their own Monday morning.
- concrete: Gives clear behavioral direction but at category level. "Confess your sin
  to a brother." "Read your Bible daily." True but not localized to the hearer's life.
- abstract: Acknowledges application exists but stays theological. "We should trust Jesus
  more." "Let us rest in grace." The hearer agrees but doesn't know what to DO differently.
- absent: No application addressed to the hearer's life at any point.
DISQUALIFIER: If application only appears in the final 10% of the sermon as a brief coda,
cap at 'concrete' even if the content is specific.

### application_landing — Does the application PRESS into the hearer's life? (NEW)
- pressed: Application pauses, sits with the hearer, names their situation. The preacher
  slows down and lets the weight land. The hearer feels personally addressed.
- touched: Application makes contact with real life but moves on quickly. The preacher
  gestures toward the hearer's world but returns to exposition before it lands.
- gestured: Application is present as a rhetorical move but doesn't slow down enough to
  press. The hearer hears the category but not the weight.
- missed: Application either absent or so abstract it makes no contact with lived experience.

### opening_tension — Does the sermon create urgency in the first 2 minutes? (NEW)
- strong: Tension, question, or stakes established in the first 60 seconds. The listener
  immediately knows why they need to keep listening.
- adequate: Some tension emerges within the first 2 minutes, but preceded by logistics,
  throat-clearing, or Bible navigation that delays engagement.
- weak: Tension doesn't emerge until 3+ minutes in. The opening is primarily logistical
  or expositional setup without urgency.
- absent: No discernible tension or hook. The sermon begins with reading and exposition
  without establishing why the listener should care.

### ethos_rating — Does the preacher seem personally seized by the text?
- seized: The preacher is visibly wrestling with the text. Personal confession, vulnerability,
  or evident emotional weight. The congregation sees a man under the Word, not above it.
- engaged: Warm, present, relational. The preacher clearly cares. But the personal stake
  is professional rather than confessional.
- professional: Competent delivery with appropriate tone but no personal exposure.
  The preacher could be teaching anyone's sermon.
- detached: Flat, distant, or going through the motions. No relational warmth.

### concreteness_score — 1 to 5. How vivid and tangible is the language?
5 = The sermon is full of images, stories, and sensory language. You can see, hear, feel it.
4 = Strong imagery present. Most points are grounded in concrete examples.
3 = Mixed. Some concrete moments, some stretches of abstract theological language.
2 = Predominantly abstract. Theological propositions with few images or stories.
1 = Entirely abstract. Dense theological discourse with no imagery.

## Tier 2: Faithfulness (the Reformed pastoral crown)

### christ_thread_score — Is Christ the resolution, not an appendix?
- explicit: Christ is named as the text's resolution and the congregation's hope. The
  Christological move is exegetically earned from the passage, not imported.
- gestured: Christ is referenced but not developed. A brief mention at the end or a
  formulaic "and this points to Jesus" without exegetical grounding.
- absent: No Christological connection. The sermon could be preached in a synagogue.
DISQUALIFIER: A last-minute "and this is why we need Jesus" without textual grounding
from the passage caps at 'gestured.'

### exegetical_grounding — Is the sermon driven by the text or decorating pre-existing points?
- grounded: The sermon's claims arise from careful reading of the passage. Key terms are
  explained, context is established, and the argument follows the text's logic.
- partial: Some exegetical work present but the sermon also imports ideas not arising
  from this text. The text is used but not fully governing.
- pretext: The passage is read but the sermon's content could exist without it. Scripture
  decorates rather than drives.

## Tier 3: Diagnostic (symptoms — root causes live in Tier 1)

Report these as factual observations, not scored dimensions:
- length_delta_commentary: How far over/under plan and where the excess/deficit accumulates
- density_hotspots: Specific timestamp ranges where the argument stalls, circles, or overloads
- late_application_note: If application arrives late, when and why
- outline_drift_note: Where the sermon departed from the prep outline (if linked)

## Coach Summary

- top_impact_helpers: 2-3 concrete things that drove impact THIS sermon (with timestamps)
- top_impact_hurters: 2-3 concrete things that blocked impact THIS sermon (with timestamps)
- faithfulness_note: Brief assessment of theological fidelity
- one_change_for_next_sunday: ONE concrete actionable change
- per_dimension_growth_edges: For each scored dimension, one sentence naming the specific
  growth edge. Not generic advice — grounded in what THIS sermon did and what would make
  it one level better. Format: {"burden_clarity": "...", "movement_clarity": "...", ...}

## Flags

Return 3-8 per-moment observations tied to transcript timestamps.
Each flag needs: flag_type, severity (info/note/warn/concern), start_sec, excerpt, rationale."""


def build_rubric_prompt(inp: AnalyzerInput, pure: PureStageOutput) -> str:
    """Compose the prompt string from inputs and deterministic outputs."""
    outline_summary = 'No linked prep session.' if not inp.outline_points else \
        '\n'.join(f"- [{p.get('id')}] {p.get('content', '')[:160]}" for p in inp.outline_points)

    segments_text = '\n'.join(
        f"[{s['start_sec']}s-{s['end_sec']}s {s.get('section_label', 'body')}] {s['text']}"
        for s in pure.segments
    )

    return f"""SERMON METADATA
Passage: {inp.bible_text_raw}
Duration: {inp.duration_sec} seconds ({inp.duration_sec // 60}:{inp.duration_sec % 60:02d})
Planned: {inp.planned_duration_sec or 'unknown'} seconds
Duration delta: {pure.duration_delta_sec or 'N/A'} seconds

PREP OUTLINE
{outline_summary}

SEGMENTED TRANSCRIPT
{segments_text}

DETERMINISTIC STAGE OUTPUT
Section timings: {json.dumps(pure.section_timings)}
Density hotspots: {json.dumps(pure.density_hotspots)}
Outline coverage: {pure.outline_coverage_pct}

Score this sermon per the schema."""


def run_llm_rubric(client, inp: AnalyzerInput, pure: PureStageOutput) -> dict:
    """Call the LLM client with the assembled prompt and the REVIEW_SCHEMA."""
    prompt = build_rubric_prompt(inp, pure)
    return client.call(prompt=prompt, schema=REVIEW_SCHEMA, system=RUBRIC_SYSTEM_PROMPT)


import hashlib
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Rough Opus 4.6 pricing per 1M tokens (update as needed)
OPUS_INPUT_COST_PER_MTOK = 15.0
OPUS_OUTPUT_COST_PER_MTOK = 75.0


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model.startswith('claude-opus'):
        return (input_tokens * OPUS_INPUT_COST_PER_MTOK +
                output_tokens * OPUS_OUTPUT_COST_PER_MTOK) / 1_000_000
    return 0.0


def _load_analyzer_input(conn, sermon_id: int) -> AnalyzerInput:
    row = conn.execute("""
        SELECT id, transcript_text, duration_seconds, bible_text_raw, transcript_segments
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    if not row or not row[1]:
        raise ValueError(f"sermon {sermon_id} has no transcript")
    srt_json = row[4]
    srt_segments = json.loads(srt_json) if srt_json else None

    link_row = conn.execute("""
        SELECT s.id FROM sermon_links sl
        JOIN sessions s ON s.id = sl.session_id
        WHERE sl.sermon_id = ? AND sl.link_status = 'active'
        LIMIT 1
    """, (sermon_id,)).fetchone()
    outline_points = []
    # Phase 2 will read this from a per-session target field. For MVP, default to
    # the midpoint of Bryan's wife's stated 25-30min target so length deltas fire.
    planned_duration_sec = DEFAULT_PLANNED_DURATION_SEC
    if link_row:
        session_id = link_row[0]
        point_rows = conn.execute("""
            SELECT id, content FROM outline_nodes
            WHERE session_id = ? AND type IN ('main_point','sub_point','bullet')
            ORDER BY rank
        """, (session_id,)).fetchall()
        outline_points = [{'id': r[0], 'content': r[1]} for r in point_rows]

    return AnalyzerInput(
        sermon_id=row[0],
        transcript_text=row[1],
        duration_sec=row[2] or 0,
        planned_duration_sec=planned_duration_sec,
        outline_points=outline_points,
        bible_text_raw=row[3] or '',
        srt_segments=srt_segments,
    )


def _transcript_hash(text: str) -> str:
    return hashlib.sha256((text or '').encode()).hexdigest()[:16]


def _write_review(conn, sermon_id: int, inp: AnalyzerInput, pure: PureStageOutput,
                  llm_output: dict, model: str) -> None:
    """Overwrite sermon_reviews row and replace flags."""
    now = _now()
    tier1 = llm_output.get('tier1_impact', {})
    tier2 = llm_output.get('tier2_faithfulness', {})
    tier3 = llm_output.get('tier3_diagnostic', {})
    summary = llm_output.get('coach_summary', {})

    conn.execute("DELETE FROM sermon_reviews WHERE sermon_id = ?", (sermon_id,))
    conn.execute("""
        INSERT INTO sermon_reviews (
            sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis,
            burden_clarity, burden_statement_excerpt, burden_first_stated_at_sec,
            movement_clarity, movement_rationale,
            application_specificity, application_landing, application_first_arrived_at_sec, application_excerpts,
            opening_tension, opening_tension_note,
            ethos_rating, ethos_markers,
            concreteness_score, imagery_density_per_10min, narrative_moments,
            christ_thread_score, christ_thread_excerpts,
            exegetical_grounding, exegetical_grounding_notes,
            actual_duration_seconds, planned_duration_seconds, duration_delta_seconds,
            section_timings, length_delta_commentary, density_hotspots,
            late_application_note, outline_coverage_pct, outline_additions, outline_omissions,
            outline_drift_note,
            top_impact_helpers, top_impact_hurters, faithfulness_note, one_change_for_next_sunday,
            per_dimension_growth_edges,
            computed_at
        ) VALUES (?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sermon_id, ANALYZER_VERSION, homiletics_core_version, model,
        _transcript_hash(inp.transcript_text),
        conn.execute("SELECT source_version FROM sermons WHERE id=?", (sermon_id,)).fetchone()[0],
        tier1.get('burden_clarity'), tier1.get('burden_statement_excerpt'),
        tier1.get('burden_first_stated_at_sec'),
        tier1.get('movement_clarity'), tier1.get('movement_rationale'),
        tier1.get('application_specificity'), tier1.get('application_landing'),
        tier1.get('application_first_arrived_at_sec'),
        json.dumps(tier1.get('application_excerpts', [])),
        tier1.get('opening_tension'), tier1.get('opening_tension_note'),
        tier1.get('ethos_rating'), json.dumps(tier1.get('ethos_markers', [])),
        tier1.get('concreteness_score'), tier1.get('imagery_density_per_10min'),
        json.dumps(tier1.get('narrative_moments', [])),
        tier2.get('christ_thread_score'), json.dumps(tier2.get('christ_thread_excerpts', [])),
        tier2.get('exegetical_grounding'), tier2.get('exegetical_grounding_notes'),
        pure.actual_duration_sec, pure.planned_duration_sec, pure.duration_delta_sec,
        json.dumps(pure.section_timings),
        tier3.get('length_delta_commentary'),
        json.dumps(tier3.get('density_hotspots', [])),
        tier3.get('late_application_note'),
        pure.outline_coverage_pct,
        json.dumps(pure.outline_additions),
        json.dumps(pure.outline_omissions),
        tier3.get('outline_drift_note'),
        json.dumps(summary.get('top_impact_helpers', [])),
        json.dumps(summary.get('top_impact_hurters', [])),
        summary.get('faithfulness_note'),
        summary.get('one_change_for_next_sunday', ''),
        json.dumps(summary.get('per_dimension_growth_edges', {})),
        now,
    ))

    conn.execute("DELETE FROM sermon_flags WHERE sermon_id = ?", (sermon_id,))
    for f in llm_output.get('flags', []):
        conn.execute("""
            INSERT INTO sermon_flags (
                sermon_id, flag_type, severity,
                transcript_start_sec, transcript_end_sec,
                section_label, excerpt, rationale, analyzer_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sermon_id, f.get('flag_type'), f.get('severity', 'note'),
            f.get('start_sec'), f.get('end_sec'),
            f.get('section_label'), f.get('excerpt'),
            f.get('rationale', ''), ANALYZER_VERSION, now,
        ))


def analyze_sermon(db, sermon_id: int, llm_client) -> dict:
    """Run the full pipeline for a single sermon. Returns {status, ...}."""
    conn = db._conn()
    try:
        try:
            inp = _load_analyzer_input(conn, sermon_id)
        except ValueError as e:
            conn.execute("UPDATE sermons SET sync_status='analysis_failed', sync_error=?, last_state_change_at=? WHERE id=?",
                         (str(e), _now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_failed', 'error': str(e)}

        if len((inp.transcript_text or '').split()) < 1000:
            conn.execute("UPDATE sermons SET sync_status='analysis_skipped', last_state_change_at=? WHERE id=?",
                         (_now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_skipped', 'reason': 'transcript_too_short'}

        conn.execute("UPDATE sermons SET sync_status='analysis_running', last_state_change_at=? WHERE id=?",
                     (_now(), sermon_id))
        conn.commit()

        pure = run_pure_stages(inp)
        result = run_llm_rubric(llm_client, inp, pure)

        if 'error' in result:
            conn.execute("UPDATE sermons SET sync_status='analysis_failed', sync_error=?, last_state_change_at=? WHERE id=?",
                         (result['error'], _now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_failed', 'error': result['error']}

        model = result.get('model', 'claude-opus-4-6')
        output = result.get('output', {})
        try:
            _write_review(conn, sermon_id, inp, pure, output, model)
        except Exception as e:
            conn.execute("UPDATE sermons SET sync_status='analysis_failed', sync_error=?, last_state_change_at=? WHERE id=?",
                         (f'write_review_failed: {e}', _now(), sermon_id))
            conn.commit()
            return {'status': 'analysis_failed', 'error': f'write_review_failed: {e}'}

        input_tokens = result.get('input_tokens', 0)
        output_tokens = result.get('output_tokens', 0)
        cost = estimate_cost_usd(model, input_tokens, output_tokens)
        conn.execute("""
            INSERT INTO sermon_analysis_cost_log
                (sermon_id, model, input_tokens, output_tokens, estimated_cost_usd, called_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sermon_id, model, input_tokens, output_tokens, cost, _now()))

        conn.execute("UPDATE sermons SET sync_status='review_ready', last_state_change_at=? WHERE id=?",
                     (_now(), sermon_id))
        conn.commit()

        # Dispatch tagging pass if SRT segments are available
        if inp.srt_segments and inp.duration_sec > 0:
            try:
                from sermon_tagger import tag_sermon
                tag_result = tag_sermon(db, sermon_id, llm_client)
            except Exception as e:
                # Tagging failure is non-fatal — the review is already saved
                logging.getLogger(__name__).warning(
                    f'Tagging failed for sermon {sermon_id}: {e}')

        return {'status': 'review_ready', 'cost_usd': cost,
                'input_tokens': input_tokens, 'output_tokens': output_tokens}
    finally:
        conn.close()


def dispatch_pending_analyses(db, llm_client, limit: int = 10) -> int:
    """Poll for sermons ready to analyze and process them serially."""
    conn = db._conn()
    rows = conn.execute("""
        SELECT id FROM sermons
        WHERE classified_as = 'sermon'
          AND sermon_type = 'expository'
          AND (
            sync_status = 'transcript_ready'
            OR (sync_status = 'review_ready'
                AND source_version > COALESCE(
                    (SELECT source_version_at_analysis FROM sermon_reviews WHERE sermon_id = sermons.id),
                    0))
          )
        ORDER BY preach_date DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    count = 0
    for (sid,) in rows:
        result = analyze_sermon(db, sid, llm_client=llm_client)
        if result.get('status') == 'review_ready':
            count += 1
    return count
