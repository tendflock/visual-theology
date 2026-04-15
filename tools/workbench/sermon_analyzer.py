"""Sermon analyzer — deterministic stages + one structured LLM call.

Stages 1-4 are pure. Stage 5 (LLM rubric pass) and stage 6 (writer + dispatch)
come in Tasks 12 and 13.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json

from homiletics_core import (
    __version__ as homiletics_core_version,
    segment_transcript,
    compute_section_timings,
    detect_density_hotspots,
    align_segments_to_outline,
    late_application,
)

ANALYZER_VERSION = '1.0.0'


@dataclass(frozen=True)
class AnalyzerInput:
    sermon_id: int
    transcript_text: str
    duration_sec: int
    planned_duration_sec: Optional[int]
    outline_points: list = field(default_factory=list)
    bible_text_raw: str = ''


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
                'application_first_arrived_at_sec': {'type': ['integer', 'null']},
                'application_excerpts': {'type': 'array', 'items': {'type': 'object'}},
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
Emit a structured review following the tool schema exactly. Ground every score in transcript evidence.

The three tiers:
- Tier 1 (Impact): burden clarity, movement, application specificity, ethos, concreteness — these
  are what rhetoric research identifies as the strongest impact predictors.
- Tier 2 (Faithfulness): Christ thread + exegetical grounding — parallel crown for a Reformed pastor.
- Tier 3 (Diagnostic): symptoms whose causes live in Tier 1 — length, density hotspots, late application.

For the coach_summary:
- top_impact_helpers: 2-3 concrete things that drove impact THIS sermon
- top_impact_hurters: 2-3 concrete things that blocked impact THIS sermon
- one_change_for_next_sunday: ONE concrete actionable change

For flags: return 3-8 per-moment observations tied to transcript timestamps."""


def build_rubric_prompt(inp: AnalyzerInput, pure: PureStageOutput) -> str:
    """Compose the prompt string from inputs and deterministic outputs."""
    outline_summary = 'No linked prep session.' if not inp.outline_points else \
        '\n'.join(f"- [{p.get('id')}] {p.get('content', '')[:160]}" for p in inp.outline_points)

    segments_text = '\n'.join(
        f"[{s['start_sec']}s-{s['end_sec']}s {s.get('section_label', 'body')}] {s['text'][:400]}"
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
        SELECT id, transcript_text, duration_seconds, bible_text_raw
        FROM sermons WHERE id = ?
    """, (sermon_id,)).fetchone()
    if not row or not row[1]:
        raise ValueError(f"sermon {sermon_id} has no transcript")

    link_row = conn.execute("""
        SELECT s.id FROM sermon_links sl
        JOIN sessions s ON s.id = sl.session_id
        WHERE sl.sermon_id = ? AND sl.link_status = 'active'
        LIMIT 1
    """, (sermon_id,)).fetchone()
    outline_points = []
    planned_duration_sec = None
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
            application_specificity, application_first_arrived_at_sec, application_excerpts,
            ethos_rating, ethos_markers,
            concreteness_score, imagery_density_per_10min, narrative_moments,
            christ_thread_score, christ_thread_excerpts,
            exegetical_grounding, exegetical_grounding_notes,
            actual_duration_seconds, planned_duration_seconds, duration_delta_seconds,
            section_timings, length_delta_commentary, density_hotspots,
            late_application_note, outline_coverage_pct, outline_additions, outline_omissions,
            outline_drift_note,
            top_impact_helpers, top_impact_hurters, faithfulness_note, one_change_for_next_sunday,
            computed_at
        ) VALUES (?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sermon_id, ANALYZER_VERSION, homiletics_core_version, model,
        _transcript_hash(inp.transcript_text),
        conn.execute("SELECT source_version FROM sermons WHERE id=?", (sermon_id,)).fetchone()[0],
        tier1.get('burden_clarity'), tier1.get('burden_statement_excerpt'),
        tier1.get('burden_first_stated_at_sec'),
        tier1.get('movement_clarity'), tier1.get('movement_rationale'),
        tier1.get('application_specificity'), tier1.get('application_first_arrived_at_sec'),
        json.dumps(tier1.get('application_excerpts', [])),
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
        _write_review(conn, sermon_id, inp, pure, output, model)

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
