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
