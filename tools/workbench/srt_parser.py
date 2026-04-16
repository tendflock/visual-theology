"""
SRT subtitle parser with validation and transcript builder.

Parses SRT subtitle text into timestamped segments, validates coverage
quality, and builds canonical transcript strings for sermon analysis.
"""
import re

# Timecode pattern: HH:MM:SS,mmm --> HH:MM:SS,mmm (also accepts '.' for ',')
_TIMECODE_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})"
)

# Non-content patterns: [Music], [silence], [Applause], etc.
_NON_CONTENT_RE = re.compile(r"^\s*\[.*\]\s*$")


def _timecode_to_ms(hours, minutes, seconds, millis):
    """Convert timecode components to milliseconds."""
    return int(hours) * 3600000 + int(minutes) * 60000 + int(seconds) * 1000 + int(millis)


def parse_srt_segments(srt_text):
    """Parse SRT subtitle text into a sorted, deduplicated list of segment dicts.

    Each segment: {"segment_index": int, "start_ms": int, "end_ms": int, "text": str}

    Handles: CRLF/LF, malformed blocks, non-content lines ([Music] etc.),
    multi-line captions, hours > 0, non-monotonic timestamps, duplicate start_ms.
    """
    if not srt_text or not srt_text.strip():
        return []

    # Normalize line endings to LF
    text = srt_text.replace("\r\n", "\n").replace("\r", "\n")

    # Split into blocks by blank lines
    blocks = re.split(r"\n\n+", text.strip())

    raw_segments = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # Find the timecode line (may or may not have a sequence number before it)
        timecode_match = None
        timecode_idx = -1
        for i, line in enumerate(lines):
            m = _TIMECODE_RE.search(line)
            if m:
                timecode_match = m
                timecode_idx = i
                break

        if timecode_match is None:
            # Malformed block -- no timecode found, skip
            continue

        # Parse timestamps
        g = timecode_match.groups()
        start_ms = _timecode_to_ms(g[0], g[1], g[2], g[3])
        end_ms = _timecode_to_ms(g[4], g[5], g[6], g[7])

        # Collect text lines (everything after the timecode line)
        text_lines = []
        for line in lines[timecode_idx + 1 :]:
            stripped = line.strip()
            if stripped and not _NON_CONTENT_RE.match(stripped):
                text_lines.append(stripped)

        caption_text = " ".join(text_lines)

        raw_segments.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "text": caption_text,
        })

    # Sort by start_ms
    raw_segments.sort(key=lambda s: s["start_ms"])

    # Deduplicate by start_ms (keep first occurrence)
    seen_starts = set()
    deduped = []
    for seg in raw_segments:
        if seg["start_ms"] not in seen_starts:
            seen_starts.add(seg["start_ms"])
            deduped.append(seg)

    # Assign segment_index after sort/dedup
    result = []
    for i, seg in enumerate(deduped):
        result.append({
            "segment_index": i,
            "start_ms": seg["start_ms"],
            "end_ms": seg["end_ms"],
            "text": seg["text"],
        })

    return result


def validate_segments(segments, duration_sec):
    """Validate segment quality. Returns 'good' or 'degraded'.

    Checks:
    - Non-empty segments list
    - First segment starts within 30s
    - Monotonic timestamps (each start_ms >= previous end_ms)
    - Non-empty text ratio > 80%
    - Last segment end_ms within 10% of duration
    """
    if not segments:
        return "degraded"

    # First segment must start within 30 seconds
    if segments[0]["start_ms"] >= 30000:
        return "degraded"

    # Monotonic: each segment's start_ms >= previous segment's end_ms
    for i in range(1, len(segments)):
        if segments[i]["start_ms"] < segments[i - 1]["end_ms"]:
            return "degraded"

    # Non-empty text ratio must exceed 80%
    total = len(segments)
    non_empty = sum(1 for s in segments if s["text"].strip())
    if non_empty / total <= 0.80:
        return "degraded"

    # Coverage: last segment's end_ms within 10% of duration
    duration_ms = duration_sec * 1000
    last_end = segments[-1]["end_ms"]
    if duration_ms > 0 and last_end < duration_ms * 0.90:
        return "degraded"

    return "good"


def build_canonical_transcript(segments):
    """Join segment texts into a single transcript string.

    Skips segments with empty text. Returns empty string for empty list.
    """
    if not segments:
        return ""

    parts = [s["text"] for s in segments if s["text"].strip()]
    return " ".join(parts)
