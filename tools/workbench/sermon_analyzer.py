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
