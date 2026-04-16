"""Tests for SRT parser: parse_srt_segments, validate_segments, build_canonical_transcript."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from srt_parser import build_canonical_transcript, coarsen_srt_segments, parse_srt_segments, validate_segments


# ── Task 1: Core Parsing ──────────────────────────────────────────────


class TestParseSrtBasic:
    """Basic parsing of well-formed SRT content."""

    def test_single_block(self):
        srt = "1\n00:00:01,000 --> 00:00:04,500\nWelcome to the sermon.\n"
        result = parse_srt_segments(srt)
        assert len(result) == 1
        assert result[0] == {
            "segment_index": 0,
            "start_ms": 1000,
            "end_ms": 4500,
            "text": "Welcome to the sermon.",
        }

    def test_multiple_blocks(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:04,500\nFirst line.\n\n"
            "2\n00:00:05,000 --> 00:00:08,200\nSecond line.\n"
        )
        result = parse_srt_segments(srt)
        assert len(result) == 2
        assert result[0]["segment_index"] == 0
        assert result[0]["text"] == "First line."
        assert result[1]["segment_index"] == 1
        assert result[1]["text"] == "Second line."
        assert result[1]["start_ms"] == 5000
        assert result[1]["end_ms"] == 8200

    def test_empty_input_returns_empty(self):
        assert parse_srt_segments("") == []

    def test_none_input_returns_empty(self):
        assert parse_srt_segments(None) == []

    def test_millisecond_integers(self):
        srt = "1\n00:00:00,000 --> 00:00:01,500\nHello\n"
        result = parse_srt_segments(srt)
        assert isinstance(result[0]["start_ms"], int)
        assert isinstance(result[0]["end_ms"], int)
        assert result[0]["start_ms"] == 0
        assert result[0]["end_ms"] == 1500


# ── Task 2: Robustness Tests ──────────────────────────────────────────


class TestParseSrtRobustness:
    """Edge cases and robustness."""

    def test_crlf_line_endings(self):
        srt = "1\r\n00:00:01,000 --> 00:00:04,500\r\nHello world.\r\n"
        result = parse_srt_segments(srt)
        assert len(result) == 1
        assert result[0]["text"] == "Hello world."

    def test_malformed_block_skipped(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:04,500\nGood block.\n\n"
            "garbage line with no timecode\n\n"
            "3\n00:00:06,000 --> 00:00:09,000\nAnother good block.\n"
        )
        result = parse_srt_segments(srt)
        assert len(result) == 2
        assert result[0]["text"] == "Good block."
        assert result[1]["text"] == "Another good block."

    def test_non_content_lines_filtered(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:03,000\n[Music]\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\n[silence]\n\n"
            "3\n00:00:07,000 --> 00:00:10,000\nActual content here.\n"
        )
        result = parse_srt_segments(srt)
        # Non-content lines should be filtered — only real content remains
        texts = [s["text"] for s in result]
        assert "[Music]" not in texts
        assert "[silence]" not in texts
        assert "Actual content here." in texts

    def test_multiline_caption_joined(self):
        srt = "1\n00:00:01,000 --> 00:00:04,500\nFirst line\nSecond line\n"
        result = parse_srt_segments(srt)
        assert len(result) == 1
        assert result[0]["text"] == "First line Second line"

    def test_hours_greater_than_zero(self):
        srt = "1\n01:30:00,000 --> 01:30:05,500\nLate in the video.\n"
        result = parse_srt_segments(srt)
        assert len(result) == 1
        assert result[0]["start_ms"] == 5400000  # 1h30m = 90min = 5400s
        assert result[0]["end_ms"] == 5405500

    def test_non_monotonic_timestamps_sorted(self):
        srt = (
            "1\n00:00:10,000 --> 00:00:15,000\nSecond segment.\n\n"
            "2\n00:00:01,000 --> 00:00:05,000\nFirst segment.\n"
        )
        result = parse_srt_segments(srt)
        assert result[0]["text"] == "First segment."
        assert result[1]["text"] == "Second segment."
        assert result[0]["segment_index"] == 0
        assert result[1]["segment_index"] == 1

    def test_duplicate_start_ms_deduped(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:05,000\nDuplicate A.\n\n"
            "2\n00:00:01,000 --> 00:00:05,000\nDuplicate B.\n"
        )
        result = parse_srt_segments(srt)
        assert len(result) == 1

    def test_dot_separator_accepted(self):
        """Accept '.' as millisecond separator (some SRT generators use it)."""
        srt = "1\n00:00:01.000 --> 00:00:04.500\nDot separator.\n"
        result = parse_srt_segments(srt)
        assert len(result) == 1
        assert result[0]["start_ms"] == 1000
        assert result[0]["end_ms"] == 4500

    def test_whitespace_only_input(self):
        assert parse_srt_segments("   \n\n  ") == []

    def test_block_with_empty_text_after_timecode(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:04,500\n\n\n"
            "2\n00:00:05,000 --> 00:00:08,000\nReal content.\n"
        )
        result = parse_srt_segments(srt)
        # The empty-text block may be included with empty text or skipped;
        # either way, the real content block must be present
        real = [s for s in result if s["text"]]
        assert len(real) >= 1
        assert real[0]["text"] == "Real content."


# ── Task 3: Validation ───────────────────────────────────────────────


class TestValidateSegments:
    """validate_segments returns 'good' or 'degraded'."""

    def _make_segments(self, specs):
        """Helper: specs is list of (start_ms, end_ms, text)."""
        return [
            {"segment_index": i, "start_ms": s, "end_ms": e, "text": t}
            for i, (s, e, t) in enumerate(specs)
        ]

    def test_good_segments(self):
        segs = self._make_segments([
            (0, 5000, "Hello"),
            (5000, 10000, "World"),
            (10000, 15000, "End"),
        ])
        assert validate_segments(segs, duration_sec=15) == "good"

    def test_empty_segments_degraded(self):
        assert validate_segments([], duration_sec=30) == "degraded"

    def test_late_first_segment_degraded(self):
        segs = self._make_segments([
            (35000, 40000, "Starts late"),
            (40000, 45000, "More"),
        ])
        assert validate_segments(segs, duration_sec=45) == "degraded"

    def test_first_segment_under_30s_good(self):
        segs = self._make_segments([
            (29000, 34000, "Just under 30s"),
            (34000, 39000, "More"),
        ])
        assert validate_segments(segs, duration_sec=39) == "good"

    def test_low_text_ratio_degraded(self):
        # >20% empty text segments
        segs = self._make_segments([
            (0, 1000, "Good"),
            (1000, 2000, ""),
            (2000, 3000, ""),
            (3000, 4000, ""),
            (4000, 5000, "Good"),
        ])
        # 2/5 = 40% non-empty, well below 80%
        assert validate_segments(segs, duration_sec=5) == "degraded"

    def test_coverage_gap_degraded(self):
        # Last segment ends way before duration
        segs = self._make_segments([
            (0, 5000, "Hello"),
            (5000, 10000, "World"),
        ])
        # duration is 60s, last segment ends at 10s — 10/60 = 16.7%, not within 10%
        assert validate_segments(segs, duration_sec=60) == "degraded"

    def test_non_monotonic_timestamps_degraded(self):
        segs = self._make_segments([
            (0, 10000, "First"),
            (5000, 15000, "Overlaps first"),  # start_ms 5000 < prev end_ms 10000
        ])
        assert validate_segments(segs, duration_sec=15) == "degraded"

    def test_coverage_within_10_percent_good(self):
        segs = self._make_segments([
            (0, 5000, "Hello"),
            (5000, 55000, "Long segment"),
        ])
        # duration 60s, last ends at 55s — 55/60 = 91.7%, within 10%
        assert validate_segments(segs, duration_sec=60) == "good"

    def test_zero_duration_degraded(self):
        segs = self._make_segments([(0, 5000, "Hello")])
        assert validate_segments(segs, duration_sec=0) == "degraded"

    def test_negative_duration_degraded(self):
        segs = self._make_segments([(0, 5000, "Hello")])
        assert validate_segments(segs, duration_sec=-1) == "degraded"

    def test_exactly_30s_start_degraded(self):
        segs = self._make_segments([
            (30000, 35000, "Exactly 30s"),
            (35000, 40000, "More"),
        ])
        assert validate_segments(segs, duration_sec=40) == "degraded"

    def test_exactly_80_percent_text_ratio_good(self):
        segs = self._make_segments([
            (0, 1000, "A"), (1000, 2000, "B"), (2000, 3000, "C"),
            (3000, 4000, "D"), (4000, 5000, ""),
        ])
        # 4/5 = 80% — should pass with >= 80%
        assert validate_segments(segs, duration_sec=5) == "good"


# ── Task 3: Canonical Transcript Builder ──────────────────────────────


class TestBuildCanonicalTranscript:
    """build_canonical_transcript joins segment texts."""

    def test_joins_texts(self):
        segs = [
            {"segment_index": 0, "start_ms": 0, "end_ms": 5000, "text": "Hello"},
            {"segment_index": 1, "start_ms": 5000, "end_ms": 10000, "text": "world"},
        ]
        assert build_canonical_transcript(segs) == "Hello world"

    def test_skips_empty_text(self):
        segs = [
            {"segment_index": 0, "start_ms": 0, "end_ms": 5000, "text": "Hello"},
            {"segment_index": 1, "start_ms": 5000, "end_ms": 10000, "text": ""},
            {"segment_index": 2, "start_ms": 10000, "end_ms": 15000, "text": "world"},
        ]
        assert build_canonical_transcript(segs) == "Hello world"

    def test_empty_list_returns_empty_string(self):
        assert build_canonical_transcript([]) == ""

    def test_single_segment(self):
        segs = [{"segment_index": 0, "start_ms": 0, "end_ms": 5000, "text": "Only one."}]
        assert build_canonical_transcript(segs) == "Only one."


# ── Task 4: SRT Coarsening ──────────────────────────────────────────


class TestCoarsenSrtSegments:
    """coarsen_srt_segments merges fine-grained captions into paragraph chunks."""

    def _seg(self, index, start_ms, end_ms, text):
        return {"segment_index": index, "start_ms": start_ms, "end_ms": end_ms, "text": text}

    def test_merges_adjacent_short_segments(self):
        """Adjacent segments with small gaps and no sentence boundaries merge."""
        segs = [
            self._seg(0, 0, 2000, "Welcome to"),
            self._seg(1, 2100, 4000, "the sermon"),
            self._seg(2, 4100, 6000, "today friends"),
        ]
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 1
        assert result[0]["text"] == "Welcome to the sermon today friends"

    def test_splits_on_long_pause(self):
        """Gap >= 2000ms forces a split even without sentence-ending punctuation."""
        segs = [
            self._seg(0, 0, 2000, "First part"),
            self._seg(1, 4500, 6000, "second part after long pause"),
        ]
        # gap = 4500 - 2000 = 2500ms >= 2000ms threshold
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 2
        assert result[0]["text"] == "First part"
        assert result[1]["text"] == "second part after long pause"

    def test_splits_on_sentence_end_with_moderate_pause(self):
        """Sentence-ending punctuation + gap >= 500ms forces a split."""
        segs = [
            self._seg(0, 0, 2000, "This is a sentence."),
            self._seg(1, 2600, 4000, "New thought begins"),
        ]
        # gap = 2600 - 2000 = 600ms >= 500ms AND prev ends with '.'
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 2
        assert result[0]["text"] == "This is a sentence."
        assert result[1]["text"] == "New thought begins"

    def test_no_split_sentence_end_short_pause(self):
        """Sentence-ending punctuation with gap < 500ms does NOT split."""
        segs = [
            self._seg(0, 0, 2000, "End of sentence."),
            self._seg(1, 2300, 4000, "Continues quickly"),
        ]
        # gap = 300ms < 500ms — no split despite sentence-ending punctuation
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 1
        assert result[0]["text"] == "End of sentence. Continues quickly"

    def test_assigns_section_labels_by_position(self):
        """Section labels based on chunk start position relative to duration."""
        # duration = 100s = 100000ms
        segs = [
            self._seg(0, 0, 3000, "Intro text"),          # pct=0.0 → intro
            self._seg(1, 5000, 8000, "Intro still"),       # merged if gap allows
            self._seg(2, 30000, 33000, "Body content."),   # pct=0.3 → body
            self._seg(3, 76000, 79000, "Application."),    # pct=0.76 → application
            self._seg(4, 92000, 95000, "Closing words."),  # pct=0.92 → close
        ]
        result = coarsen_srt_segments(segs, duration_sec=100)
        labels = {r["section_label"] for r in result}
        # Verify we get the expected labels (exact count depends on merge logic)
        assert "intro" in labels
        assert "body" in labels
        assert "application" in labels
        assert "close" in labels
        # Check specific label assignments
        intro_chunks = [r for r in result if r["section_label"] == "intro"]
        assert len(intro_chunks) >= 1
        assert intro_chunks[0]["start_sec"] < 10  # within first 10% of 100s

    def test_preserves_timing_from_constituents(self):
        """start_sec/end_sec come from first/last constituent, in integer seconds."""
        segs = [
            self._seg(0, 1500, 3200, "First word"),
            self._seg(1, 3300, 5800, "second word"),
        ]
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 1
        # 1500ms // 1000 = 1, 5800ms // 1000 = 5
        assert result[0]["start_sec"] == 1
        assert result[0]["end_sec"] == 5

    def test_empty_input_returns_empty(self):
        assert coarsen_srt_segments([], duration_sec=60) == []

    def test_zero_duration_returns_empty(self):
        segs = [self._seg(0, 0, 2000, "Hello")]
        assert coarsen_srt_segments(segs, duration_sec=0) == []

    def test_negative_duration_returns_empty(self):
        segs = [self._seg(0, 0, 2000, "Hello")]
        assert coarsen_srt_segments(segs, duration_sec=-5) == []

    def test_single_segment_returns_one_chunk(self):
        segs = [self._seg(0, 5000, 8000, "Only segment")]
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 1
        assert result[0] == {
            "start_sec": 5,
            "end_sec": 8,
            "text": "Only segment",
            "section_label": "intro",  # pct = 5000/60000 = 0.083 < 0.1
        }

    def test_exclamation_and_question_end_sentences(self):
        """! and ? are also sentence-ending punctuation."""
        segs = [
            self._seg(0, 0, 2000, "Can you believe it!"),
            self._seg(1, 2600, 4000, "Yes indeed"),
            self._seg(2, 4100, 6000, "Right?"),
            self._seg(3, 6700, 8000, "Of course"),
        ]
        result = coarsen_srt_segments(segs, duration_sec=60)
        # ! with 600ms gap → split; ? with 600ms gap → split
        assert len(result) == 3
        assert result[0]["text"] == "Can you believe it!"
        assert result[1]["text"] == "Yes indeed Right?"
        assert result[2]["text"] == "Of course"

    def test_output_format_matches_homiletics_core(self):
        """Output dicts have exactly the keys expected by downstream functions."""
        segs = [self._seg(0, 0, 3000, "Test")]
        result = coarsen_srt_segments(segs, duration_sec=60)
        assert len(result) == 1
        assert set(result[0].keys()) == {"start_sec", "end_sec", "text", "section_label"}
