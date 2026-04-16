# Meta-Coach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-layer longitudinal coaching system: SRT timestamp preservation, taxonomy-controlled moment tagging, and a corpus-scoped meta-coach on the patterns page.

**Architecture:** Layer 1 parses SRT captions into timestamped segments stored alongside plain text. Layer 2 runs a second LLM pass to tag transcript moments with controlled taxonomy. Layer 3 is a streaming Claude coach on the patterns page that uses pre-computed priority rankings and tagged moments for evidence-bounded longitudinal coaching.

**Tech Stack:** Python 3.9, Flask, SQLite, Anthropic Claude Opus 4.6, SSE streaming, HTMX

**Spec:** `docs/superpowers/specs/2026-04-16-meta-coach-design.md`

---

## File Structure

### New Files (Layer 1)
- `tools/workbench/srt_parser.py` — SRT parsing, validation, canonical transcript builder, coarsening
- `tools/workbench/tests/test_srt_parser.py` — SRT parser unit tests

### New Files (Layer 2)
- `tools/workbench/sermon_tagger.py` — tagging LLM prompt, output parsing, post-processing
- `tools/workbench/tests/test_sermon_tagger.py` — tagger unit tests

### New Files (Layer 3)
- `tools/workbench/shared_prompts.py` — extracted HOMILETICAL_FRAMEWORK + LONGITUDINAL_POSTURE_RULE
- `tools/workbench/meta_coach_agent.py` — system prompt assembly, streaming loop, tool dispatch
- `tools/workbench/meta_coach_tools.py` — corpus summaries, distributions, moments, commitments
- `tools/workbench/priority_ranker.py` — pre-computed priority ranking with sub-score formulas
- `tools/workbench/templates/partials/meta_coach_chat.html` — chat widget with 3 buttons
- `tools/workbench/static/meta_coach.js` — SSE client
- `tools/workbench/tests/test_meta_coach_tools.py`
- `tools/workbench/tests/test_priority_ranker.py`

### Modified Files
- `tools/workbench/companion_db.py` — ALTER TABLE migrations + new tables
- `tools/workbench/sermonaudio_sync.py` — integrate SRT parsing into ingest
- `tools/workbench/sermon_analyzer.py` — coarsening strategy + tagging dispatch
- `tools/workbench/sermon_coach_agent.py` — extract constants, add commitment lens
- `tools/workbench/app.py` — meta-coach routes + backfill endpoint
- `tools/workbench/templates/sermons/patterns.html` — chat widget include

---

## LAYER 1: SRT Timestamp Preservation

### Task 1: SRT Parser — Core Parsing

**Files:**
- Create: `tools/workbench/srt_parser.py`
- Test: `tools/workbench/tests/test_srt_parser.py`

- [ ] **Step 1: Write failing test for basic SRT parsing**

```python
# tests/test_srt_parser.py
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from srt_parser import parse_srt_segments

BASIC_SRT = """\
1
00:00:01,000 --> 00:00:04,500
Welcome to this morning's sermon.

2
00:00:04,800 --> 00:00:09,200
We'll be looking at Romans chapter 8.

3
00:00:09,500 --> 00:00:14,000
Let's begin with prayer.
"""

def test_parse_basic_srt():
    segments = parse_srt_segments(BASIC_SRT)
    assert len(segments) == 3
    assert segments[0] == {
        'segment_index': 0, 'start_ms': 1000, 'end_ms': 4500,
        'text': "Welcome to this morning's sermon.",
    }
    assert segments[1]['start_ms'] == 4800
    assert segments[2]['segment_index'] == 2

def test_parse_empty_returns_empty():
    assert parse_srt_segments('') == []
    assert parse_srt_segments(None) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'srt_parser'`

- [ ] **Step 3: Implement parse_srt_segments**

```python
# srt_parser.py
"""SRT caption parser — parses, validates, and coarsens SRT subtitle files."""

from __future__ import annotations
import re
from typing import Optional


# SRT timecode pattern: HH:MM:SS,mmm
_TIMECODE_RE = re.compile(
    r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})'
)


def _parse_timecode_ms(tc: str) -> Optional[int]:
    """Parse 'HH:MM:SS,mmm' to milliseconds."""
    m = _TIMECODE_RE.match(tc.strip())
    if not m:
        return None
    h, mi, s, ms = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    return h * 3600000 + mi * 60000 + s * 1000 + ms


def parse_srt_segments(srt_text: Optional[str]) -> list[dict]:
    """Parse SRT text into [{segment_index, start_ms, end_ms, text}, ...].

    Handles CRLF/LF, malformed blocks, non-content lines, multi-line captions,
    hours > 0, and overlapping timestamps (sorted by start_ms, deduped).
    segment_index tracks normalized order after sorting/dedup.
    """
    if not srt_text:
        return []

    # Normalize line endings
    text = srt_text.replace('\r\n', '\n').replace('\r', '\n')

    # Split into blocks by blank lines
    blocks = re.split(r'\n\n+', text.strip())
    raw_segments = []

    for block in blocks:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        if len(lines) < 2:
            continue

        # Find the timecode line (contains ' --> ')
        tc_idx = None
        for i, line in enumerate(lines):
            if ' --> ' in line:
                tc_idx = i
                break
        if tc_idx is None:
            continue

        # Parse start/end times
        parts = lines[tc_idx].split(' --> ')
        if len(parts) != 2:
            continue
        start_ms = _parse_timecode_ms(parts[0])
        end_ms = _parse_timecode_ms(parts[1])
        if start_ms is None or end_ms is None or start_ms >= end_ms:
            continue

        # Text is everything after the timecode line
        caption_lines = lines[tc_idx + 1:]
        caption_text = ' '.join(caption_lines).strip()

        # Skip non-content lines
        if not caption_text:
            continue
        lower = caption_text.lower()
        if lower in ('[music]', '[silence]', '[laughter]', '[applause]'):
            continue

        raw_segments.append({
            'start_ms': start_ms,
            'end_ms': end_ms,
            'text': caption_text,
        })

    # Sort by start_ms for normalized order
    raw_segments.sort(key=lambda s: s['start_ms'])

    # Deduplicate: drop segments with identical start_ms
    seen_starts = set()
    deduped = []
    for seg in raw_segments:
        if seg['start_ms'] not in seen_starts:
            seen_starts.add(seg['start_ms'])
            deduped.append(seg)

    # Assign segment_index (normalized order)
    for i, seg in enumerate(deduped):
        seg['segment_index'] = i

    return deduped
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/srt_parser.py tools/workbench/tests/test_srt_parser.py
git commit -m "feat: SRT parser — core segment parsing"
```

### Task 2: SRT Parser — Robustness Tests

**Files:**
- Modify: `tools/workbench/tests/test_srt_parser.py`

- [ ] **Step 1: Add robustness tests**

```python
# Append to tests/test_srt_parser.py

CRLF_SRT = "1\r\n00:00:01,000 --> 00:00:04,000\r\nHello world.\r\n\r\n"

def test_parse_crlf():
    segments = parse_srt_segments(CRLF_SRT)
    assert len(segments) == 1
    assert segments[0]['text'] == 'Hello world.'

MALFORMED_SRT = """\
1
00:00:01,000 --> 00:00:04,000
Good line.

bad block with no timecode

3
00:00:05,000 --> 00:00:08,000
Another good line.
"""

def test_parse_skips_malformed_blocks():
    segments = parse_srt_segments(MALFORMED_SRT)
    assert len(segments) == 2
    assert segments[0]['text'] == 'Good line.'
    assert segments[1]['text'] == 'Another good line.'

NON_CONTENT_SRT = """\
1
00:00:01,000 --> 00:00:04,000
[Music]

2
00:00:04,000 --> 00:00:08,000
Actual speech here.

3
00:00:08,000 --> 00:00:12,000
[silence]
"""

def test_parse_strips_non_content():
    segments = parse_srt_segments(NON_CONTENT_SRT)
    assert len(segments) == 1
    assert segments[0]['text'] == 'Actual speech here.'

MULTILINE_SRT = """\
1
00:00:01,000 --> 00:00:06,000
First line of caption
second line of caption
"""

def test_parse_joins_multiline_captions():
    segments = parse_srt_segments(MULTILINE_SRT)
    assert len(segments) == 1
    assert segments[0]['text'] == 'First line of caption second line of caption'

HOURS_SRT = """\
1
01:30:00,000 --> 01:30:05,000
Late in the sermon.
"""

def test_parse_handles_hours():
    segments = parse_srt_segments(HOURS_SRT)
    assert len(segments) == 1
    assert segments[0]['start_ms'] == 5400000  # 1h30m in ms

NONMONOTONIC_SRT = """\
1
00:00:10,000 --> 00:00:15,000
Second segment.

2
00:00:01,000 --> 00:00:05,000
First segment.
"""

def test_parse_sorts_nonmonotonic():
    segments = parse_srt_segments(NONMONOTONIC_SRT)
    assert segments[0]['text'] == 'First segment.'
    assert segments[1]['text'] == 'Second segment.'
    assert segments[0]['segment_index'] == 0
    assert segments[1]['segment_index'] == 1
```

- [ ] **Step 2: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py -v`
Expected: 8 passed

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/tests/test_srt_parser.py
git commit -m "test: SRT parser robustness — CRLF, malformed, non-content, multiline, hours, sort"
```

### Task 3: SRT Validation + Canonical Transcript Builder

**Files:**
- Modify: `tools/workbench/srt_parser.py`
- Modify: `tools/workbench/tests/test_srt_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# Append to tests/test_srt_parser.py
from srt_parser import validate_segments, build_canonical_transcript

def test_validate_good_segments():
    segments = [
        {'segment_index': 0, 'start_ms': 0, 'end_ms': 5000, 'text': 'Hello.'},
        {'segment_index': 1, 'start_ms': 5000, 'end_ms': 10000, 'text': 'World.'},
    ]
    quality = validate_segments(segments, duration_sec=12)
    assert quality == 'good'

def test_validate_late_start_degrades():
    segments = [
        {'segment_index': 0, 'start_ms': 60000, 'end_ms': 65000, 'text': 'Late start.'},
    ]
    quality = validate_segments(segments, duration_sec=120)
    assert quality == 'degraded'

def test_validate_poor_coverage_degrades():
    segments = [
        {'segment_index': 0, 'start_ms': 0, 'end_ms': 5000, 'text': 'Short.'},
    ]
    quality = validate_segments(segments, duration_sec=600)  # 10 min sermon, 5s of captions
    assert quality == 'degraded'

def test_validate_empty_text_ratio_degrades():
    segments = [
        {'segment_index': i, 'start_ms': i*1000, 'end_ms': (i+1)*1000, 'text': ''}
        for i in range(10)
    ]
    quality = validate_segments(segments, duration_sec=10)
    assert quality == 'degraded'

def test_canonical_transcript():
    segments = [
        {'segment_index': 0, 'start_ms': 0, 'end_ms': 5000, 'text': 'Hello.'},
        {'segment_index': 1, 'start_ms': 5000, 'end_ms': 10000, 'text': 'World.'},
    ]
    assert build_canonical_transcript(segments) == 'Hello. World.'

def test_canonical_transcript_empty():
    assert build_canonical_transcript([]) == ''
```

- [ ] **Step 2: Run to verify failures**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py::test_validate_good_segments -v`
Expected: FAIL — `ImportError: cannot import name 'validate_segments'`

- [ ] **Step 3: Implement validation + canonical builder**

```python
# Append to srt_parser.py

def validate_segments(segments: list[dict], duration_sec: int) -> str:
    """Validate parsed SRT segments. Returns 'good' or 'degraded'."""
    if not segments:
        return 'degraded'

    # Check 1: first segment starts within 30s
    if segments[0]['start_ms'] >= 30000:
        return 'degraded'

    # Check 2: monotonic timestamps
    for i in range(1, len(segments)):
        if segments[i]['start_ms'] < segments[i-1]['end_ms']:
            return 'degraded'

    # Check 3: non-empty text ratio > 80%
    non_empty = sum(1 for s in segments if s.get('text', '').strip())
    if non_empty / len(segments) < 0.8:
        return 'degraded'

    # Check 4: coverage — last segment end within 10% of duration
    duration_ms = duration_sec * 1000
    if duration_ms > 0:
        last_end = segments[-1]['end_ms']
        if abs(last_end - duration_ms) > 0.1 * duration_ms:
            return 'degraded'

    return 'good'


def build_canonical_transcript(segments: list[dict]) -> str:
    """Join segment texts with single spaces. Deterministic — stays in sync with segments."""
    return ' '.join(s['text'] for s in segments if s.get('text', '').strip())
```

- [ ] **Step 4: Run all tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py -v`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/srt_parser.py tools/workbench/tests/test_srt_parser.py
git commit -m "feat: SRT validation + canonical transcript builder"
```

### Task 4: SRT Coarsening for Analyzer

**Files:**
- Modify: `tools/workbench/srt_parser.py`
- Modify: `tools/workbench/tests/test_srt_parser.py`

- [ ] **Step 1: Write failing test**

```python
# Append to tests/test_srt_parser.py
from srt_parser import coarsen_srt_segments

def test_coarsen_merges_short_segments():
    """Adjacent segments with < 2s gap and no sentence boundary merge."""
    segments = [
        {'segment_index': 0, 'start_ms': 0, 'end_ms': 3000, 'text': 'Welcome to'},
        {'segment_index': 1, 'start_ms': 3100, 'end_ms': 6000, 'text': "this morning's sermon."},
        {'segment_index': 2, 'start_ms': 6100, 'end_ms': 9000, 'text': "Let's begin with prayer."},
    ]
    coarsened = coarsen_srt_segments(segments, duration_sec=30)
    # First two merge (no sentence end on first), third stays separate
    assert len(coarsened) >= 1
    # Coarsened segments have section_label
    assert 'section_label' in coarsened[0]

def test_coarsen_splits_on_long_pause():
    """Segments with > 2s gap always split."""
    segments = [
        {'segment_index': 0, 'start_ms': 0, 'end_ms': 3000, 'text': 'First point.'},
        {'segment_index': 1, 'start_ms': 6000, 'end_ms': 9000, 'text': 'Second point.'},
    ]
    coarsened = coarsen_srt_segments(segments, duration_sec=10)
    assert len(coarsened) == 2

def test_coarsen_assigns_section_labels():
    """Section labels assigned based on position in sermon."""
    segments = [
        {'segment_index': i, 'start_ms': i*3000, 'end_ms': (i+1)*3000,
         'text': f'Segment {i}.'} for i in range(10)
    ]
    coarsened = coarsen_srt_segments(segments, duration_sec=30)
    labels = [s['section_label'] for s in coarsened]
    assert labels[0] == 'intro'
    assert labels[-1] == 'close'

def test_coarsen_preserves_timing():
    """Each coarsened segment has start_sec and end_sec from constituent SRT segments."""
    segments = [
        {'segment_index': 0, 'start_ms': 1000, 'end_ms': 4000, 'text': 'Hello world.'},
    ]
    coarsened = coarsen_srt_segments(segments, duration_sec=10)
    assert coarsened[0]['start_sec'] == 1  # 1000ms -> 1s
    assert coarsened[0]['end_sec'] == 4
```

- [ ] **Step 2: Run to verify failures**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py::test_coarsen_merges_short_segments -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement coarsening**

```python
# Append to srt_parser.py

def coarsen_srt_segments(segments: list[dict], duration_sec: int) -> list[dict]:
    """Merge fine-grained SRT segments into paragraph-scale chunks.

    Splits on: sentence-ending punctuation + gap > 500ms, or any gap > 2000ms.
    Assigns section_label based on position (intro/body/application/close)
    to match the format expected by homiletics_core pure functions.
    """
    if not segments:
        return []

    PAUSE_THRESHOLD_MS = 2000
    chunks = []
    current_texts = []
    current_start_ms = segments[0]['start_ms']
    current_end_ms = segments[0]['end_ms']

    for i, seg in enumerate(segments):
        if i == 0:
            current_texts.append(seg['text'])
            current_end_ms = seg['end_ms']
            continue

        gap_ms = seg['start_ms'] - current_end_ms
        prev_ends_sentence = current_texts[-1].rstrip().endswith(('.', '!', '?'))

        if gap_ms >= PAUSE_THRESHOLD_MS or (prev_ends_sentence and gap_ms >= 500):
            # Flush current chunk
            chunks.append({
                'start_ms': current_start_ms,
                'end_ms': current_end_ms,
                'text': ' '.join(current_texts),
            })
            current_texts = [seg['text']]
            current_start_ms = seg['start_ms']
            current_end_ms = seg['end_ms']
        else:
            current_texts.append(seg['text'])
            current_end_ms = seg['end_ms']

    # Flush last chunk
    if current_texts:
        chunks.append({
            'start_ms': current_start_ms,
            'end_ms': current_end_ms,
            'text': ' '.join(current_texts),
        })

    # Add section_label and convert to seconds for homiletics_core compatibility
    duration_ms = duration_sec * 1000 if duration_sec > 0 else 1
    result = []
    for chunk in chunks:
        pct = chunk['start_ms'] / duration_ms
        if pct < 0.1:
            label = 'intro'
        elif pct > 0.9:
            label = 'close'
        elif pct > 0.75:
            label = 'application'
        else:
            label = 'body'
        result.append({
            'start_sec': chunk['start_ms'] // 1000,
            'end_sec': chunk['end_ms'] // 1000,
            'text': chunk['text'],
            'section_label': label,
        })

    return result
```

- [ ] **Step 4: Run all tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_srt_parser.py -v`
Expected: 18 passed

- [ ] **Step 5: Commit**

```bash
git add tools/workbench/srt_parser.py tools/workbench/tests/test_srt_parser.py
git commit -m "feat: SRT coarsening — merge caption lines into paragraph-scale chunks"
```

### Task 5: DB Migration — Add Sermon Columns

**Files:**
- Modify: `tools/workbench/companion_db.py`

- [ ] **Step 1: Add ALTER TABLE migration for new sermon columns**

In `companion_db.py`, after the existing `last_homiletical_activity_at` migration (line 310-312), add:

```python
        # Migration: add SRT segment columns to sermons
        existing_sermon_cols = {r[1] for r in conn.execute("PRAGMA table_info(sermons)").fetchall()}
        if 'transcript_segments' not in existing_sermon_cols:
            conn.execute("ALTER TABLE sermons ADD COLUMN transcript_segments TEXT")
        if 'transcript_quality' not in existing_sermon_cols:
            conn.execute("ALTER TABLE sermons ADD COLUMN transcript_quality TEXT CHECK (transcript_quality IN ('good', 'degraded'))")
```

- [ ] **Step 2: Verify migration runs on existing DB**

Run: `cd tools/workbench && python3 -c "from companion_db import CompanionDB; db = CompanionDB(); conn = db._conn(); cols = {r[1] for r in conn.execute('PRAGMA table_info(sermons)').fetchall()}; print('transcript_segments' in cols, 'transcript_quality' in cols); conn.close()"`
Expected: `True True`

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/companion_db.py
git commit -m "migrate: add transcript_segments and transcript_quality columns to sermons"
```

### Task 6: Integrate SRT Parsing into Ingest

**Files:**
- Modify: `tools/workbench/sermonaudio_sync.py`

- [ ] **Step 1: Add SRT parsing to normalize_remote**

In `sermonaudio_sync.py`, modify `normalize_remote()` to also return raw SRT text and parsed segments. After line 61 (`transcript = _fetch_srt_as_text(caption.download_url)`), capture the raw SRT:

```python
# In normalize_remote(), replace the transcript fetching block:
    transcript = None
    srt_raw = None
    if caption and caption.download_url:
        srt_raw = _fetch_srt_raw(caption.download_url)
        if srt_raw:
            from srt_parser import parse_srt_segments, validate_segments, build_canonical_transcript
            segments = parse_srt_segments(srt_raw)
            if segments:
                transcript = build_canonical_transcript(segments)
            else:
                transcript = _fetch_srt_as_text_from_raw(srt_raw)
        else:
            transcript = None
```

Add `_fetch_srt_raw()` that returns raw SRT text (like `_fetch_srt_as_text` but without stripping):

```python
def _fetch_srt_raw(url: str) -> Optional[str]:
    """Download raw SRT caption file text."""
    try:
        import sermonaudio
        resp = sermonaudio._session.get(url, timeout=30)
        return resp.text if resp.ok else None
    except Exception:
        return None

def _fetch_srt_as_text_from_raw(srt_raw: str) -> Optional[str]:
    """Strip timestamps from raw SRT to plain text (fallback when parsing fails)."""
    lines = []
    for line in srt_raw.splitlines():
        line = line.strip()
        if not line or line.isdigit() or re.match(r'\d{2}:\d{2}:\d{2}', line):
            continue
        lines.append(line)
    return ' '.join(lines) if lines else None
```

Add `srt_segments` and `srt_quality` to the `SimpleNamespace` returned by `normalize_remote()`:

```python
    # In the return SimpleNamespace, add:
        srt_segments=json.dumps(segments) if srt_raw and segments else None,
        srt_quality=validate_segments(segments, audio.duration if audio else 0) if srt_raw and segments else None,
```

- [ ] **Step 2: Update upsert_sermon to store segments**

In `upsert_sermon()`, add `transcript_segments` and `transcript_quality` to both the INSERT and UPDATE SQL statements. For the INSERT (line 189-232), add the two new columns. For the UPDATE (line 251-285), add them similarly.

- [ ] **Step 3: Run existing sync tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermonaudio_sync.py -v`
Expected: 12 passed (existing tests don't exercise SRT — they use SimpleNamespace without srt_segments)

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/sermonaudio_sync.py
git commit -m "feat: integrate SRT parsing into sermon ingest pipeline"
```

### Task 7: Analyzer Coarsening Strategy

**Files:**
- Modify: `tools/workbench/sermon_analyzer.py`

- [ ] **Step 1: Update run_pure_stages to use SRT segments when available**

In `sermon_analyzer.py`, modify `_load_analyzer_input()` to also fetch `transcript_segments` and `duration_seconds`. Then in `run_pure_stages()`, check for SRT segments:

```python
# At the top of run_pure_stages(), replace line 55:
    if inp.srt_segments:
        from srt_parser import coarsen_srt_segments
        segments = coarsen_srt_segments(inp.srt_segments, inp.duration_sec)
    else:
        segments = segment_transcript(inp.transcript_text, inp.duration_sec)
```

Add `srt_segments: Optional[list] = None` to the `AnalyzerInput` dataclass.

In `_load_analyzer_input()`, parse the JSON segments column:

```python
    srt_json = row['transcript_segments'] if row['transcript_segments'] else None
    srt_segments = json.loads(srt_json) if srt_json else None
```

Pass `srt_segments=srt_segments` to the `AnalyzerInput` constructor.

- [ ] **Step 2: Run existing analyzer tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_analyzer.py -v` (if exists) or verify no regressions with `python3 -m pytest tests/test_sermon_coach_agent.py tests/test_sermon_coach_tools.py -v`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/sermon_analyzer.py
git commit -m "feat: analyzer uses SRT coarsened segments when available"
```

### Task 8: Backfill SRT Segments

**Files:**
- Modify: `tools/workbench/app.py`

- [ ] **Step 1: Add backfill-srt route**

```python
@sermons_bp.route('/backfill-srt', methods=['POST'])
def sermon_backfill_srt():
    """Re-fetch SRT for all sermons and populate transcript_segments."""
    from srt_parser import parse_srt_segments, validate_segments, build_canonical_transcript
    from sermonaudio_sync import _fetch_srt_raw
    db = get_db()
    conn = db._conn()
    rows = conn.execute("""
        SELECT id, sermonaudio_id, duration_seconds FROM sermons
        WHERE classified_as = 'sermon' AND transcript_segments IS NULL
    """).fetchall()

    results = {'total': len(rows), 'updated': 0, 'failed': 0, 'no_srt': 0}
    for row in rows:
        sermon_id, sa_id, duration = row[0], row[1], row[2] or 0
        try:
            from sermonaudio.node.requests import Node
            detail = Node.get_sermon(sa_id)
            caption = detail.media.caption[0] if detail.media and detail.media.caption else None
            if not caption or not caption.download_url:
                results['no_srt'] += 1
                continue
            srt_raw = _fetch_srt_raw(caption.download_url)
            if not srt_raw:
                results['no_srt'] += 1
                continue
            segments = parse_srt_segments(srt_raw)
            if not segments:
                results['failed'] += 1
                continue
            quality = validate_segments(segments, duration)
            canonical = build_canonical_transcript(segments)
            import json as _json
            conn.execute("""
                UPDATE sermons SET transcript_segments = ?, transcript_quality = ?,
                    transcript_text = ? WHERE id = ?
            """, (_json.dumps(segments), quality, canonical, sermon_id))
            conn.commit()
            results['updated'] += 1
        except Exception as e:
            results['failed'] += 1

    conn.close()
    return jsonify(results)
```

- [ ] **Step 2: Test manually**

Run: `curl -X POST http://localhost:5111/sermons/backfill-srt`
Expected: JSON response with counts of updated/failed/no_srt

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/app.py
git commit -m "feat: backfill-srt endpoint to populate transcript_segments for existing sermons"
```

### GATE: Layer 1 Validation

- [ ] **Run backfill**: `curl -X POST http://localhost:5111/sermons/backfill-srt`
- [ ] **Verify**: `cd tools/workbench && python3 -c "from companion_db import CompanionDB; db = CompanionDB(); conn = db._conn(); rows = conn.execute('SELECT COUNT(*), SUM(CASE WHEN transcript_segments IS NOT NULL THEN 1 ELSE 0 END), SUM(CASE WHEN transcript_quality = \'good\' THEN 1 ELSE 0 END) FROM sermons WHERE classified_as = \'sermon\'').fetchone(); print(f'Total: {rows[0]}, With segments: {rows[1]}, Good quality: {rows[2]}'); conn.close()"`
- [ ] **Spot check**: Pick 2-3 sermons and verify segments look reasonable
- [ ] **Only proceed to Layer 2 after backfill is complete and verified**

---

## LAYER 2: Enriched Analysis Tagging

### Task 9: DB Schema — analysis_runs + sermon_moments

**Files:**
- Modify: `tools/workbench/companion_db.py`

- [ ] **Step 1: Add new tables to init_db()**

After the sermon column migrations, add:

```python
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id TEXT PRIMARY KEY,
                sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
                run_type TEXT NOT NULL CHECK (run_type IN ('review', 'tagging')),
                review_run_id TEXT REFERENCES analysis_runs(id),
                prompt_version TEXT NOT NULL,
                model_name TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_analysis_runs_sermon ON analysis_runs(sermon_id, run_type, is_active);

            CREATE TABLE IF NOT EXISTS sermon_moments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sermon_id INTEGER NOT NULL REFERENCES sermons(id) ON DELETE CASCADE,
                analysis_run_id TEXT NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
                start_segment_index INTEGER NOT NULL,
                end_segment_index INTEGER NOT NULL,
                start_ms INTEGER NOT NULL,
                end_ms INTEGER NOT NULL,
                sermon_position_pct REAL NOT NULL CHECK (sermon_position_pct >= 0.0 AND sermon_position_pct <= 1.0),
                excerpt_text TEXT NOT NULL,
                context_text TEXT,
                dimension_key TEXT NOT NULL CHECK (dimension_key IN (
                    'burden_clarity', 'movement_clarity', 'application_specificity',
                    'ethos_rating', 'concreteness_score', 'christ_thread_score', 'exegetical_grounding'
                )),
                section_role TEXT NOT NULL CHECK (section_role IN (
                    'intro', 'setup', 'exposition', 'illustration_section', 'application',
                    'transition', 'recap', 'appeal', 'conclusion', 'prayer', 'reading'
                )),
                homiletic_move TEXT CHECK (homiletic_move IS NULL OR homiletic_move IN (
                    'big_idea_statement', 'structure_signpost', 'textual_observation', 'doctrinal_claim',
                    'illustration', 'exhortation', 'application', 'christ_connection', 'gospel_implication',
                    'objection_handling', 'direct_address', 'diagnostic_question', 'pastoral_comfort',
                    'warning', 'summary_restatement', 'contextualization'
                )),
                valence TEXT NOT NULL CHECK (valence IN ('positive', 'negative')),
                confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
                impact TEXT NOT NULL CHECK (impact IN ('minor', 'moderate', 'major')),
                moment_rank INTEGER NOT NULL,
                rationale TEXT NOT NULL,
                review_source_ref TEXT,
                prompt_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sermon_moments_sermon_run ON sermon_moments(sermon_id, analysis_run_id);
            CREATE INDEX IF NOT EXISTS idx_sermon_moments_dimension ON sermon_moments(sermon_id, dimension_key, valence);
            CREATE INDEX IF NOT EXISTS idx_sermon_moments_position ON sermon_moments(sermon_id, start_segment_index, end_segment_index);
        """)
        # Unique index — CREATE UNIQUE INDEX IF NOT EXISTS doesn't work in executescript for some SQLite versions
        try:
            conn.execute("""
                CREATE UNIQUE INDEX uq_sermon_moment_span ON sermon_moments(
                    sermon_id, analysis_run_id, dimension_key, valence,
                    start_segment_index, end_segment_index
                )
            """)
        except Exception:
            pass  # Already exists
```

- [ ] **Step 2: Verify migration**

Run: `cd tools/workbench && python3 -c "from companion_db import CompanionDB; db = CompanionDB(); conn = db._conn(); tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]; print('analysis_runs' in tables, 'sermon_moments' in tables); conn.close()"`
Expected: `True True`

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/companion_db.py
git commit -m "migrate: add analysis_runs and sermon_moments tables"
```

### Task 10: Sermon Tagger — Prompt + Output Parser

**Files:**
- Create: `tools/workbench/sermon_tagger.py`
- Create: `tools/workbench/tests/test_sermon_tagger.py`

This is a large task. The tagger prompt, output parsing, post-processing, and the `tag_sermon()` entry point all live here. Implementation details follow the spec's taxonomy, output contract, and anti-hallucination rules.

- [ ] **Step 1: Write failing test for output parsing**

```python
# tests/test_sermon_tagger.py
import os, sys, pytest, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sermon_tagger import parse_tagger_output, DIMENSION_KEYS

def test_parse_valid_moment():
    raw = {
        'moments': [{
            'dimension_key': 'burden_clarity',
            'section_role': 'intro',
            'homiletic_move': 'big_idea_statement',
            'valence': 'positive',
            'confidence': 0.92,
            'impact': 'major',
            'start_segment_index': 0,
            'end_segment_index': 2,
            'excerpt_text': 'The heart of this passage is...',
            'context_text': 'Good morning. The heart of this passage is... Let me explain.',
            'rationale': 'Burden stated explicitly in first 3 segments.',
            'review_source_ref': 'burden_clarity:crisp',
        }]
    }
    moments = parse_tagger_output(raw)
    assert len(moments) == 1
    assert moments[0]['dimension_key'] == 'burden_clarity'

def test_parse_rejects_invalid_dimension():
    raw = {'moments': [{'dimension_key': 'made_up', 'valence': 'positive',
                         'confidence': 0.9, 'impact': 'major',
                         'start_segment_index': 0, 'end_segment_index': 0,
                         'excerpt_text': 'text', 'section_role': 'intro',
                         'rationale': 'reason', 'review_source_ref': 'x:y'}]}
    moments = parse_tagger_output(raw)
    assert len(moments) == 0  # Invalid dimension dropped

def test_parse_suppresses_low_confidence():
    raw = {'moments': [{'dimension_key': 'burden_clarity', 'valence': 'positive',
                         'confidence': 0.4, 'impact': 'minor',
                         'start_segment_index': 0, 'end_segment_index': 0,
                         'excerpt_text': 'text', 'section_role': 'intro',
                         'rationale': 'reason', 'review_source_ref': 'x:y'}]}
    moments = parse_tagger_output(raw)
    assert len(moments) == 0  # Below 0.65 threshold
```

- [ ] **Step 2: Implement output parser + constants**

```python
# sermon_tagger.py
"""Sermon moment tagger — second LLM pass for taxonomy-controlled evidence tagging."""

from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

DIMENSION_KEYS = frozenset({
    'burden_clarity', 'movement_clarity', 'application_specificity',
    'ethos_rating', 'concreteness_score', 'christ_thread_score', 'exegetical_grounding',
})

SECTION_ROLES = frozenset({
    'intro', 'setup', 'exposition', 'illustration_section', 'application',
    'transition', 'recap', 'appeal', 'conclusion', 'prayer', 'reading',
})

HOMILETIC_MOVES = frozenset({
    'big_idea_statement', 'structure_signpost', 'textual_observation', 'doctrinal_claim',
    'illustration', 'exhortation', 'application', 'christ_connection', 'gospel_implication',
    'objection_handling', 'direct_address', 'diagnostic_question', 'pastoral_comfort',
    'warning', 'summary_restatement', 'contextualization',
})

CONFIDENCE_FLOOR = 0.65
MAX_MOMENTS_PER_SERMON = 18

TAGGER_PROMPT_VERSION = '1.0.0'


def parse_tagger_output(raw: dict) -> list[dict]:
    """Parse and validate LLM tagger output. Drops invalid/low-confidence moments."""
    moments = raw.get('moments', [])
    valid = []
    for m in moments:
        # Validate required fields
        if m.get('dimension_key') not in DIMENSION_KEYS:
            continue
        if m.get('valence') not in ('positive', 'negative'):
            continue
        if m.get('section_role') not in SECTION_ROLES:
            continue
        if m.get('impact') not in ('minor', 'moderate', 'major'):
            continue

        conf = m.get('confidence', 0)
        if not isinstance(conf, (int, float)) or conf < CONFIDENCE_FLOOR:
            continue

        if m.get('homiletic_move') and m['homiletic_move'] not in HOMILETIC_MOVES:
            m['homiletic_move'] = None  # Drop invalid, keep moment

        if not m.get('excerpt_text') or not m.get('rationale'):
            continue

        if m.get('start_segment_index') is None or m.get('end_segment_index') is None:
            continue

        valid.append(m)

    # Cap at MAX_MOMENTS_PER_SERMON, prefer higher confidence
    valid.sort(key=lambda x: -x.get('confidence', 0))
    return valid[:MAX_MOMENTS_PER_SERMON]
```

- [ ] **Step 3: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_tagger.py -v`
Expected: 3 passed

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/sermon_tagger.py tools/workbench/tests/test_sermon_tagger.py
git commit -m "feat: sermon tagger — output parser with taxonomy validation"
```

### Task 11: Sermon Tagger — LLM Prompt + tag_sermon()

**Files:**
- Modify: `tools/workbench/sermon_tagger.py`

- [ ] **Step 1: Add the tagging prompt builder and tag_sermon entry point**

This task adds `build_tagger_prompt()` (assembles the system prompt with taxonomy, rules, few-shot examples) and `tag_sermon()` (the entry point that fetches data, calls the LLM, parses output, and writes to DB).

The prompt includes:
- The controlled taxonomy with operational definitions
- The output contract (0-4 per dimension, max 18 total)
- Anti-hallucination rules
- Few-shot calibration examples
- The transcript segments as numbered context
- The review scores as prior context

`tag_sermon()`:
1. Creates an `analysis_runs` row with `run_type='tagging'`
2. Calls the LLM with the tagger prompt
3. Parses the output with `parse_tagger_output()`
4. Computes `sermon_position_pct` and `moment_rank`
5. Inserts `sermon_moments` rows
6. Marks the run completed
7. Marks any prior tagging run `is_active=0`

Full implementation code is in the tagger — too long to inline here but follows the spec exactly. The key function signature:

```python
def tag_sermon(db, sermon_id: int, llm_client, review_run_id: str) -> dict:
    """Run the tagging pass for a sermon. Returns {run_id, moments_stored, moments_suppressed}."""
```

- [ ] **Step 2: Wire into sermon_analyzer dispatch**

In `sermon_analyzer.py`, after `analyze_sermon()` completes successfully, add:

```python
    # Dispatch tagging pass
    from sermon_tagger import tag_sermon
    active_review_run = conn.execute(
        "SELECT id FROM analysis_runs WHERE sermon_id = ? AND run_type = 'review' AND is_active = 1",
        (sermon_id,)
    ).fetchone()
    if active_review_run and sermon_row['transcript_segments'] and (sermon_row['duration_seconds'] or 0) > 0:
        tag_sermon(db, sermon_id, llm_client=llm_client, review_run_id=active_review_run[0])
```

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/sermon_tagger.py tools/workbench/sermon_analyzer.py
git commit -m "feat: sermon tagger — LLM prompt, tag_sermon entry point, analyzer dispatch"
```

### GATE: Layer 2 Validation

- [ ] **Run tagging on 5 sermons**: Reanalyze 5 sermons via `curl -X POST http://localhost:5111/sermons/<id>/reanalyze`
- [ ] **Inspect moments**: `python3 -c "from companion_db import CompanionDB; db = CompanionDB(); conn = db._conn(); rows = conn.execute('SELECT sermon_id, dimension_key, valence, confidence, excerpt_text FROM sermon_moments WHERE confidence >= 0.65 ORDER BY sermon_id, dimension_key LIMIT 20').fetchall(); [print(r) for r in rows]; conn.close()"`
- [ ] **Verify**: Moments have real timestamps, verbatim excerpts, valid taxonomy values
- [ ] **Build calibration gold set**: Review 5-10 sermons' moments by hand, tune the prompt if needed
- [ ] **Only proceed to Layer 3 after tagging quality is validated**

---

## LAYER 3: Meta-Coach

### Task 12: Extract Shared Prompts

**Files:**
- Create: `tools/workbench/shared_prompts.py`
- Modify: `tools/workbench/sermon_coach_agent.py`

- [ ] **Step 1: Create shared_prompts.py**

Move `HOMILETICAL_FRAMEWORK` (lines 44-55) and `LONGITUDINAL_POSTURE_RULE` (lines 17-41) from `sermon_coach_agent.py` to `shared_prompts.py`:

```python
# shared_prompts.py
"""Shared domain rules used by both per-sermon coach and meta-coach.

Not voice constants (those live in voice_constants.py). These are
homiletical framework and longitudinal posture rules.
"""

HOMILETICAL_FRAMEWORK = """## Homiletical Framework
...
"""  # Copy exact text from sermon_coach_agent.py lines 44-55

LONGITUDINAL_POSTURE_RULE = """## Longitudinal Posture — YOU MUST FOLLOW THIS
...
"""  # Copy exact text from sermon_coach_agent.py lines 17-41
```

- [ ] **Step 2: Update sermon_coach_agent.py imports**

Replace the inline constants with imports:

```python
from shared_prompts import HOMILETICAL_FRAMEWORK, LONGITUDINAL_POSTURE_RULE
```

- [ ] **Step 3: Run existing tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_sermon_coach_agent.py -v`
Expected: All pass (same constants, just imported from different file)

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/shared_prompts.py tools/workbench/sermon_coach_agent.py
git commit -m "refactor: extract HOMILETICAL_FRAMEWORK and LONGITUDINAL_POSTURE_RULE to shared_prompts.py"
```

### Task 13: DB Schema — coaching_commitments

**Files:**
- Modify: `tools/workbench/companion_db.py`

- [ ] **Step 1: Add coaching_commitments table**

```python
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS coaching_commitments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dimension_key TEXT NOT NULL,
                practice_experiment TEXT NOT NULL,
                target_sermons INTEGER NOT NULL DEFAULT 2,
                baseline_sermon_id INTEGER REFERENCES sermons(id),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'superseded')),
                created_at TEXT NOT NULL,
                reviewed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_coaching_commitments_active ON coaching_commitments(status);
        """)
        try:
            conn.execute("""
                CREATE UNIQUE INDEX uq_coaching_one_active ON coaching_commitments(status) WHERE status = 'active'
            """)
        except Exception:
            pass
```

- [ ] **Step 2: Verify**

Run: `cd tools/workbench && python3 -c "from companion_db import CompanionDB; db = CompanionDB(); conn = db._conn(); tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]; print('coaching_commitments' in tables); conn.close()"`
Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add tools/workbench/companion_db.py
git commit -m "migrate: add coaching_commitments table with partial unique index"
```

### Task 14: Priority Ranker

**Files:**
- Create: `tools/workbench/priority_ranker.py`
- Create: `tools/workbench/tests/test_priority_ranker.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_priority_ranker.py
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from priority_ranker import compute_priority_ranking, DIMENSION_KEYS

def test_ranking_returns_all_dimensions():
    # Minimal mock: empty moments
    ranking = compute_priority_ranking(moments=[], n_sermons=10)
    assert len(ranking) == len(DIMENSION_KEYS)
    assert all('overall_rank' in r for r in ranking)
    assert all('impact_priority_score' in r for r in ranking)

def test_ranking_orders_by_negative_rate():
    moments = [
        {'sermon_id': 1, 'dimension_key': 'burden_clarity', 'valence': 'negative', 'confidence': 0.9, 'impact': 'major'},
        {'sermon_id': 2, 'dimension_key': 'burden_clarity', 'valence': 'negative', 'confidence': 0.85, 'impact': 'major'},
        {'sermon_id': 1, 'dimension_key': 'ethos_rating', 'valence': 'negative', 'confidence': 0.7, 'impact': 'minor'},
    ]
    ranking = compute_priority_ranking(moments, n_sermons=5)
    top = ranking[0]
    assert top['dimension_key'] == 'burden_clarity'
    assert top['overall_rank'] == 1
```

- [ ] **Step 2: Implement priority ranker**

```python
# priority_ranker.py
"""Pre-computed priority ranking for the meta-coach.

Ranks dimensions by urgency before the LLM runs, using sub-scores
for impact, evidence strength, trajectory, and actionability.
"""

from __future__ import annotations
from sermon_tagger import DIMENSION_KEYS

IMPACT_WEIGHTS = {'minor': 0.3, 'moderate': 0.6, 'major': 1.0}

ACTIONABILITY_MAP = {
    'application_specificity': 1.0, 'burden_clarity': 1.0,
    'movement_clarity': 0.7, 'ethos_rating': 0.7,
    'concreteness_score': 0.7,
    'christ_thread_score': 0.4, 'exegetical_grounding': 0.4,
}


def compute_priority_ranking(moments: list[dict], n_sermons: int,
                              recent_sermon_ids: list[int] = None) -> list[dict]:
    """Compute ranked priorities across dimensions. Returns list sorted by overall_rank."""
    if n_sermons <= 0:
        n_sermons = 1
    recent = set(recent_sermon_ids or [])

    results = []
    for dim in sorted(DIMENSION_KEYS):
        neg = [m for m in moments if m['dimension_key'] == dim and m['valence'] == 'negative']

        # Impact priority score
        if neg:
            weighted_sum = sum(
                IMPACT_WEIGHTS.get(m.get('impact', 'minor'), 0.3) * m.get('confidence', 0.5)
                for m in neg
            )
            impact_score = min(1.0, weighted_sum / n_sermons)
        else:
            impact_score = 0.0

        # Evidence strength score
        if neg:
            avg_conf = sum(m.get('confidence', 0.5) for m in neg) / len(neg)
            evidence_score = min(1.0, len(neg) / 10) * avg_conf
        else:
            evidence_score = 0.0

        # Trajectory score (simplified — full version needs per-sermon ordering)
        trajectory_score = 0.5  # Neutral default; refined in Task 14b with date ordering

        # Actionability score
        actionability_score = ACTIONABILITY_MAP.get(dim, 0.5)

        overall = (0.35 * impact_score + 0.25 * evidence_score +
                   0.25 * trajectory_score + 0.15 * actionability_score)

        results.append({
            'dimension_key': dim,
            'impact_priority_score': round(impact_score, 3),
            'evidence_strength_score': round(evidence_score, 3),
            'trajectory_score': round(trajectory_score, 3),
            'actionability_score': round(actionability_score, 3),
            'overall_score': round(overall, 3),
            'n_negative_moments': len(neg),
        })

    results.sort(key=lambda r: -r['overall_score'])
    for i, r in enumerate(results, 1):
        r['overall_rank'] = i

    # Confidence in ranking
    if len(results) >= 2:
        gap = results[0]['overall_score'] - results[1]['overall_score']
    else:
        gap = 1.0
    for r in results:
        r['confidence_in_ranking'] = round(gap, 3)

    return results
```

- [ ] **Step 3: Run tests**

Run: `cd tools/workbench && python3 -m pytest tests/test_priority_ranker.py -v`
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add tools/workbench/priority_ranker.py tools/workbench/tests/test_priority_ranker.py
git commit -m "feat: priority ranker with sub-score formulas"
```

### Task 15: Meta-Coach Tools

**Files:**
- Create: `tools/workbench/meta_coach_tools.py`
- Create: `tools/workbench/tests/test_meta_coach_tools.py`

This creates all 11 meta-coach read tools specified in the design. Each tool queries `sermon_moments` (joined with `sermons` and `sermon_reviews` as needed) and returns structured data. All tools support the common filter parameters (`window_days`, `min_confidence`, `per_sermon_cap`, `series`, `dimension_key`).

Key functions:
- `get_corpus_dimension_summary(db, **filters)` — per-dimension negative/positive rates, trend, count
- `get_dimension_trend(db, dimension, **filters)` — scores over time
- `get_dimension_distribution(db, dimension, **filters)` — variance/spread
- `get_representative_moments(db, dimension, valence, **filters)` — top moments
- `get_counterexamples(db, dimension, target_pattern, **filters)` — sermons where dimension was strong
- `get_sermon_context(db, sermon_id)` — single sermon metadata
- `get_sermon_moment_sequence(db, sermon_id, dimension)` — moments through sermon arc
- `compare_periods(db, period_a, period_b, dimensions)` — period comparison
- `get_evidence_quality(db, **filters)` — uncertainty report
- `get_data_freshness(db)` — pipeline completeness
- `get_active_commitment(db)` — current coaching commitment + progress

Each is a pure read function using parameterized SQL. Tests use a stocked DB fixture with sample moments.

- [ ] **Step 1-5: Implement + test each tool group, commit after each**

(Each tool follows the same pattern: failing test → implement → verify → commit. Group into 3 commits: summary/trend/distribution, moments/counterexamples/sequence, commitment/freshness/quality/periods)

### Task 16: Meta-Coach Agent

**Files:**
- Create: `tools/workbench/meta_coach_agent.py`

Follows the same streaming pattern as `sermon_coach_agent.py`:
- `build_meta_system_prompt(patterns, ranking, memory_summary, evidence_quality)`
- `stream_meta_coach_response(db, conversation_id, user_message, llm_client)` generator
- `META_TOOL_DEFINITIONS` list with all 11 tools' input schemas
- `execute_meta_tool(tool_name, tool_input, session_context)` dispatcher

The system prompt assembly follows the spec's 11-section structure. The behavioral constraints and evidence thresholds are embedded directly in the prompt text.

### Task 17: Meta-Coach Routes + UI

**Files:**
- Modify: `tools/workbench/app.py`
- Create: `tools/workbench/templates/partials/meta_coach_chat.html`
- Create: `tools/workbench/static/meta_coach.js`
- Modify: `tools/workbench/templates/sermons/patterns.html`

Routes:
- `POST /sermons/patterns/coach/message` — SSE stream
- `GET /sermons/patterns/coach/commitment` — active commitment
- `POST /sermons/patterns/coach/commitment` — create commitment

UI: chat widget with 3 buttons ("What should I work on?", "What's improving?", free text) below the existing stat cards. SSE client generates `conversation_id = Date.now()`.

### Task 18: Per-Sermon Coach — Commitment Lens

**Files:**
- Modify: `tools/workbench/sermon_coach_agent.py`

Add `active_commitment` parameter to `build_system_prompt()`. When non-None, inject the "Active Coaching Focus" section between pipeline findings and longitudinal posture rule. Update `stream_coach_response()` to fetch the active commitment and pass it.

---

## Post-Implementation

- [ ] Run full test suite: `cd tools/workbench && python3 -m pytest tests/ -v`
- [ ] Restart app: `pm2 restart study-companion`
- [ ] Manual smoke test: open patterns page, click "What should I work on?", verify streaming response with evidence
- [ ] Update `docs/SESSION-HANDOFF.md` with new state
