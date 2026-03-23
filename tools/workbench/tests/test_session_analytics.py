"""Tests for SessionAnalytics — behavioral tracking."""

import os
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from session_analytics import SessionAnalytics


@pytest.fixture
def analytics():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    sa = SessionAnalytics(tmp.name)
    sa.init_db()
    yield sa
    os.unlink(tmp.name)


# ── Phase tracking ──────────────────────────────────────────────────────

def test_phase_time_tracking(analytics):
    t1 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 22, 10, 30, 0, tzinfo=timezone.utc)

    with patch.object(analytics, '_now', return_value=t1.isoformat()):
        analytics.record_phase_enter(1, 'text_work')
    with patch.object(analytics, '_now', return_value=t2.isoformat()):
        analytics.record_phase_exit(1, 'text_work')

    seconds = analytics.get_phase_time_seconds(1, 'text_work')
    assert seconds == 1800.0  # 30 minutes


def test_phase_distribution(analytics):
    t1 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 22, 10, 15, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 3, 22, 10, 15, 0, tzinfo=timezone.utc)
    t4 = datetime(2026, 3, 22, 11, 15, 0, tzinfo=timezone.utc)

    with patch.object(analytics, '_now', return_value=t1.isoformat()):
        analytics.record_phase_enter(1, 'prayer')
    with patch.object(analytics, '_now', return_value=t2.isoformat()):
        analytics.record_phase_exit(1, 'prayer')
    with patch.object(analytics, '_now', return_value=t3.isoformat()):
        analytics.record_phase_enter(1, 'text_work')
    with patch.object(analytics, '_now', return_value=t4.isoformat()):
        analytics.record_phase_exit(1, 'text_work')

    dist = analytics.get_phase_distribution(1)
    assert dist['prayer'] == 900.0  # 15 min
    assert dist['text_work'] == 3600.0  # 60 min


def test_phase_time_no_exit(analytics):
    """If enter without exit, time should be 0 (open interval not counted)."""
    analytics.record_phase_enter(1, 'prayer')
    seconds = analytics.get_phase_time_seconds(1, 'prayer')
    assert seconds == 0.0


# ── Message tracking ────────────────────────────────────────────────────

def test_message_recording(analytics):
    analytics.record_message(1, 'user', 150, 'text_work')
    analytics.record_message(1, 'assistant', 400, 'text_work')
    analytics.record_message(1, 'user', 50, 'text_work')

    assert analytics.get_message_count(1) == 3
    assert analytics.get_message_count(1, role='user') == 2
    assert analytics.get_message_count(1, role='assistant') == 1


def test_average_message_length(analytics):
    analytics.record_message(1, 'user', 100)
    analytics.record_message(1, 'user', 200)

    avg = analytics.get_average_message_length(1, role='user')
    assert avg == 150.0


def test_average_message_length_empty(analytics):
    avg = analytics.get_average_message_length(99)
    assert avg == 0.0


# ── Silence gaps ────────────────────────────────────────────────────────

def test_silence_gaps(analytics):
    t1 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 22, 10, 1, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 3, 22, 10, 12, 0, tzinfo=timezone.utc)  # 11 min gap

    with patch.object(analytics, '_now', return_value=t1.isoformat()):
        analytics.record_message(1, 'user', 50)
    with patch.object(analytics, '_now', return_value=t2.isoformat()):
        analytics.record_message(1, 'assistant', 200)
    with patch.object(analytics, '_now', return_value=t3.isoformat()):
        analytics.record_message(1, 'user', 60)

    gaps = analytics.get_silence_gaps(1, min_gap_seconds=300)
    assert len(gaps) == 1
    assert gaps[0]['seconds'] == 660.0  # 11 min


def test_no_silence_gaps(analytics):
    t1 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 22, 10, 1, 0, tzinfo=timezone.utc)

    with patch.object(analytics, '_now', return_value=t1.isoformat()):
        analytics.record_message(1, 'user', 50)
    with patch.object(analytics, '_now', return_value=t2.isoformat()):
        analytics.record_message(1, 'assistant', 200)

    gaps = analytics.get_silence_gaps(1, min_gap_seconds=300)
    assert len(gaps) == 0


# ── Outline velocity ───────────────────────────────────────────────────

def test_outline_velocity(analytics):
    t1 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 22, 10, 30, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 3, 22, 11, 0, 0, tzinfo=timezone.utc)

    with patch.object(analytics, '_now', return_value=t1.isoformat()):
        analytics.record_outline_event(1, 'add', 'main_point')
    with patch.object(analytics, '_now', return_value=t2.isoformat()):
        analytics.record_outline_event(1, 'add', 'sub_point')
    with patch.object(analytics, '_now', return_value=t3.isoformat()):
        analytics.record_outline_event(1, 'add', 'note')

    velocity = analytics.get_outline_velocity(1)
    assert velocity == 3.0  # 3 adds in 1 hour


def test_outline_velocity_empty(analytics):
    assert analytics.get_outline_velocity(99) == 0.0


def test_last_outline_event_age(analytics):
    analytics.record_outline_event(1, 'add', 'main_point')
    age = analytics.get_last_outline_event_age(1)
    assert age is not None
    assert age < 5.0  # should be nearly instant


def test_last_outline_event_age_none(analytics):
    assert analytics.get_last_outline_event_age(99) is None


# ── Stall detection ─────────────────────────────────────────────────────

def test_stall_detection_no_stall(analytics):
    analytics.record_message(1, 'user', 100)
    analytics.record_outline_event(1, 'add', 'note')
    result = analytics.detect_stall(1)
    assert result['stalled'] is False


def test_stall_detection_outline_stall(analytics):
    old_time = datetime(2026, 3, 22, 8, 0, 0, tzinfo=timezone.utc)
    with patch.object(analytics, '_now', return_value=old_time.isoformat()):
        analytics.record_outline_event(1, 'add', 'note')
    analytics.record_message(1, 'user', 100)  # recent message

    result = analytics.detect_stall(1, outline_stall_minutes=45)
    assert result['stalled'] is True
    assert result['reason'] == 'outline_stall'


def test_stall_detection_message_stall(analytics):
    old_time = datetime(2026, 3, 22, 8, 0, 0, tzinfo=timezone.utc)
    with patch.object(analytics, '_now', return_value=old_time.isoformat()):
        analytics.record_message(1, 'user', 100)

    result = analytics.detect_stall(1, message_stall_minutes=10)
    assert result['stalled'] is True
    assert result['reason'] == 'message_stall'


# ── Cross-session patterns ──────────────────────────────────────────────

def test_session_summary(analytics):
    analytics.record_message(1, 'user', 100)
    analytics.record_message(1, 'assistant', 300)
    analytics.record_outline_event(1, 'add', 'main_point')

    summary = analytics.get_session_summary(1)
    assert summary['session_id'] == 1
    assert summary['message_count'] == 2
    assert summary['user_messages'] == 1
    assert summary['assistant_messages'] == 1


def test_cross_session_averages(analytics):
    t1 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 22, 10, 10, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
    t4 = datetime(2026, 3, 22, 10, 20, 0, tzinfo=timezone.utc)

    # Session 1: prayer = 10 min
    with patch.object(analytics, '_now', return_value=t1.isoformat()):
        analytics.record_phase_enter(1, 'prayer')
    with patch.object(analytics, '_now', return_value=t2.isoformat()):
        analytics.record_phase_exit(1, 'prayer')

    # Session 2: prayer = 20 min
    with patch.object(analytics, '_now', return_value=t3.isoformat()):
        analytics.record_phase_enter(2, 'prayer')
    with patch.object(analytics, '_now', return_value=t4.isoformat()):
        analytics.record_phase_exit(2, 'prayer')

    avgs = analytics.get_cross_session_phase_averages([1, 2])
    assert avgs['prayer'] == 900.0  # average of 600 + 1200 = 900


def test_cross_session_averages_empty(analytics):
    avgs = analytics.get_cross_session_phase_averages([])
    assert avgs == {}
