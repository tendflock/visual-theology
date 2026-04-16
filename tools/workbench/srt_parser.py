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
    - Duration must be positive (0 or negative → degraded)
    - Non-empty text ratio >= 80%
    - Last segment end_ms within 10% of duration
    """
    if not segments:
        return "degraded"

    if duration_sec <= 0:
        return "degraded"

    # First segment must start within 30 seconds
    if segments[0]["start_ms"] >= 30000:
        return "degraded"

    # Monotonic: each segment's start_ms >= previous segment's end_ms
    for i in range(1, len(segments)):
        if segments[i]["start_ms"] < segments[i - 1]["end_ms"]:
            return "degraded"

    # Non-empty text ratio >= 80%
    total = len(segments)
    non_empty = sum(1 for s in segments if s["text"].strip())
    if non_empty / total < 0.80:
        return "degraded"

    # Coverage: last segment's end_ms within 10% of duration
    duration_ms = duration_sec * 1000
    last_end = segments[-1]["end_ms"]
    if last_end < duration_ms * 0.90:
        return "degraded"

    return "good"


def coarsen_srt_segments(segments, duration_sec):
    """Merge fine-grained SRT segments into paragraph-scale chunks.

    Takes the output of parse_srt_segments() and produces coarsened segments
    matching the format expected by homiletics_core.py pure functions
    (compute_section_timings, detect_density_hotspots, align_segments_to_outline).

    Each output segment: {start_sec, end_sec, text, section_label}

    Merging rules:
    - Merge adjacent segments when gap < 2000ms AND previous text doesn't
      end with sentence-ending punctuation (. ! ?)
    - Split when: gap >= 2000ms, OR previous ends a sentence AND gap >= 500ms

    Section labels assigned by position (pct = chunk_start_ms / duration_ms):
    - pct < 0.1 → 'intro'
    - pct > 0.9 → 'close'
    - pct > 0.75 → 'application'
    - else → 'body'
    """
    if not segments or duration_sec <= 0:
        return []

    duration_ms = duration_sec * 1000

    def _ends_sentence(text):
        stripped = text.rstrip()
        return stripped and stripped[-1] in ".!?"

    def _section_label(start_ms):
        pct = start_ms / duration_ms if duration_ms else 0
        if pct < 0.1:
            return "intro"
        elif pct > 0.9:
            return "close"
        elif pct > 0.75:
            return "application"
        else:
            return "body"

    def _flush_chunk(chunk_start_ms, chunk_end_ms, texts):
        return {
            "start_sec": chunk_start_ms // 1000,
            "end_sec": chunk_end_ms // 1000,
            "text": " ".join(texts),
            "section_label": _section_label(chunk_start_ms),
        }

    result = []
    chunk_start_ms = segments[0]["start_ms"]
    chunk_end_ms = segments[0]["end_ms"]
    chunk_texts = [segments[0]["text"]] if segments[0]["text"].strip() else []

    for i in range(1, len(segments)):
        prev = segments[i - 1]
        curr = segments[i]
        gap = curr["start_ms"] - prev["end_ms"]
        prev_ends_sentence = _ends_sentence(prev["text"])

        # Split conditions: long pause OR sentence-end + moderate pause
        if gap >= 2000 or (prev_ends_sentence and gap >= 500):
            # Flush current chunk
            if chunk_texts:
                result.append(_flush_chunk(chunk_start_ms, chunk_end_ms, chunk_texts))
            # Start new chunk
            chunk_start_ms = curr["start_ms"]
            chunk_end_ms = curr["end_ms"]
            chunk_texts = [curr["text"]] if curr["text"].strip() else []
        else:
            # Merge into current chunk
            chunk_end_ms = curr["end_ms"]
            if curr["text"].strip():
                chunk_texts.append(curr["text"])

    # Flush final chunk
    if chunk_texts:
        result.append(_flush_chunk(chunk_start_ms, chunk_end_ms, chunk_texts))

    return result


def build_canonical_transcript(segments):
    """Join segment texts into a single transcript string.

    Skips segments with empty text. Returns empty string for empty list.
    """
    if not segments:
        return ""

    parts = [s["text"] for s in segments if s["text"].strip()]
    return " ".join(parts)
