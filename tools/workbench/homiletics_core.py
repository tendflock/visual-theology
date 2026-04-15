"""Pure homiletical rule functions shared by sermon_analyzer and sermon_coach_tools.

No DB access. No side effects. All functions are deterministic given their inputs.
Version is tracked so that stale reviews can be detected when the rubric evolves.
"""

from __future__ import annotations
import re
from typing import Iterable

__version__ = '1.0.0'

HOMILETICAL_PHASES = (
    'exegetical_point',
    'fcf_homiletical',
    'sermon_construction',
    'edit_pray',
)

# Seminary / technical jargon markers (rough density signal — supplemented by LLM)
JARGON_PATTERNS = [
    r'\b(aorist|genitive|dative|accusative|nominative|vocative)\b',
    r'\banarthrous\b',
    r'\bparticiple\b',
    r'\b(exegetical|hermeneutical|eschatological|soteriological)\b',
    r'\boblique case\b',
    r'\bdative of \w+\b',
    r'\b(Wallace|Robertson|Blass[- ]Debrunner)\b',
    r'\bLXX\b',
    r'\bThGNT\b',
    r'\bMT\b',
    r'\bBDAG\b',
]


def corpus_gate_status(n_sermons: int) -> str:
    """Return the coach's longitudinal permission level based on corpus size."""
    if n_sermons >= 10:
        return 'stable'
    if n_sermons >= 5:
        return 'emerging'
    return 'pre_gate'


def late_application(arrival_sec: int, duration_sec: int) -> bool:
    """True if the application arrived later than 75% of the way through."""
    if duration_sec <= 0:
        return False
    return arrival_sec >= 0.75 * duration_sec


def segment_transcript(transcript_text: str, duration_sec: int) -> list[dict]:
    """Split a transcript into rough segments using paragraph breaks as markers.

    This is a cheap structural pass — the real segmentation happens via the LLM.
    Returns a list of {start_sec, end_sec, text, section_label} dicts where
    times are interpolated linearly over the sermon duration.
    """
    if not transcript_text or duration_sec <= 0:
        return []

    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', transcript_text) if p.strip()]
    if not paragraphs:
        return []

    total_chars = sum(len(p) for p in paragraphs)
    segments = []
    cursor = 0
    for i, p in enumerate(paragraphs):
        char_share = len(p) / total_chars if total_chars else 1 / len(paragraphs)
        duration_share = int(round(char_share * duration_sec))
        start = cursor
        end = min(cursor + duration_share, duration_sec)
        if i == len(paragraphs) - 1:
            end = duration_sec
        pct = start / duration_sec if duration_sec else 0
        if pct < 0.1:
            label = 'intro'
        elif pct > 0.9:
            label = 'close'
        elif pct > 0.75:
            label = 'application'
        else:
            label = 'body'
        segments.append({
            'start_sec': start,
            'end_sec': end,
            'text': p,
            'section_label': label,
        })
        cursor = end
    return segments


def compute_section_timings(segments: Iterable[dict]) -> dict:
    """Sum per-section durations from segment list."""
    timings = {'intro': 0, 'body': 0, 'application': 0, 'close': 0}
    for s in segments:
        label = s.get('section_label', 'body')
        if label not in timings:
            label = 'body'
        timings[label] += s.get('end_sec', 0) - s.get('start_sec', 0)
    return timings


def detect_density_hotspots(segments: list[dict]) -> list[dict]:
    """Find sliding windows of >=3 consecutive segments with jargon counts >=2 each.

    Returns hotspot records: {start_sec, end_sec, note}.
    """
    if not segments:
        return []

    def jargon_count(text: str) -> int:
        count = 0
        for pat in JARGON_PATTERNS:
            count += len(re.findall(pat, text, flags=re.IGNORECASE))
        return count

    counts = [jargon_count(s.get('text', '')) for s in segments]
    hotspots = []
    i = 0
    while i < len(counts):
        if counts[i] >= 2:
            j = i
            total = 0
            while j < len(counts) and counts[j] >= 2:
                total += counts[j]
                j += 1
            if j - i >= 3:
                hotspots.append({
                    'start_sec': segments[i]['start_sec'],
                    'end_sec': segments[j - 1]['end_sec'],
                    'note': f"{total} technical terms across {j - i} consecutive segments",
                })
            i = j
        else:
            i += 1
    return hotspots


def align_segments_to_outline(segments: list[dict], outline_points: list[dict]) -> list[dict]:
    """Cheap alignment: assign each outline point to the segment whose midpoint is closest.

    Returns a list augmented with {outline_point_id, outline_matched} on each segment.
    The real alignment happens in the LLM pass — this is a pre-hint.
    """
    if not outline_points or not segments:
        return [dict(s) for s in segments]

    result = [dict(s) for s in segments]
    for op in outline_points:
        op_text = (op.get('content') or '').lower()
        if not op_text:
            continue
        best_i = None
        best_score = 0
        for i, seg in enumerate(result):
            seg_text = (seg.get('text') or '').lower()
            score = _overlap_score(op_text, seg_text)
            if score > best_score:
                best_score = score
                best_i = i
        if best_i is not None and best_score > 2:
            result[best_i].setdefault('outline_point_ids', []).append(op.get('id'))
            result[best_i]['outline_matched'] = True
    return result


def _overlap_score(a: str, b: str) -> int:
    """Count shared 3+ char tokens."""
    atoks = {t for t in re.findall(r'\w{3,}', a)}
    btoks = {t for t in re.findall(r'\w{3,}', b)}
    return len(atoks & btoks)
