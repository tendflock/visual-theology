"""SermonAudio ingest module.

Pulls sermons from Bryan's broadcaster account, classifies them,
fingerprints them, and upserts into the sermons table.
"""

from __future__ import annotations
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from study import parse_reference_multi

BRYAN_SPEAKER_NAME = 'Bryan Schneider'
SERMON_EVENT_TYPES = frozenset({'Sunday Service'})
DEVOTIONAL_EVENT_TYPES = frozenset({'Devotional', 'Daily Devotional'})


def classify(sermon_remote) -> tuple[str, str]:
    """Return (classified_as, reason). Hard gate on speaker, then event type."""
    speaker = (getattr(sermon_remote, 'speaker_name', '') or '').strip()
    event_type = (getattr(sermon_remote, 'event_type', '') or '').strip()

    if speaker != BRYAN_SPEAKER_NAME:
        return ('skipped', f'speaker={speaker!r}')

    if event_type in SERMON_EVENT_TYPES:
        return ('sermon', f'eventType={event_type}')
    if event_type in DEVOTIONAL_EVENT_TYPES:
        return ('skipped', f'eventType={event_type}')

    pdate = getattr(sermon_remote, 'preach_date', None)
    dur_sec = getattr(sermon_remote, 'duration', 0) or 0
    dur_min = dur_sec / 60
    if pdate and hasattr(pdate, 'weekday') and pdate.weekday() == 6 and dur_min > 20:
        return ('sermon', f'heuristic: Sunday + {int(dur_min)}min')

    return ('skipped', f'eventType={event_type!r} (unknown)')


def compute_hashes(sermon_remote) -> tuple[str, Optional[str]]:
    """Compute metadata + transcript hashes. Returns (metadata_hash, transcript_hash)."""
    meta_blob = json.dumps({
        'title': getattr(sermon_remote, 'title', None),
        'event_type': getattr(sermon_remote, 'event_type', None),
        'series': getattr(sermon_remote, 'series', None),
        'preach_date': str(getattr(sermon_remote, 'preach_date', None)),
        'bible_text_raw': getattr(sermon_remote, 'bible_text', None),
        'duration_seconds': getattr(sermon_remote, 'duration', None),
        'remote_updated_at': str(getattr(sermon_remote, 'update_date', None)),
    }, sort_keys=True)
    meta_hash = hashlib.sha256(meta_blob.encode()).hexdigest()[:16]

    transcript = getattr(sermon_remote, 'transcript', None)
    tx_hash = hashlib.sha256(transcript.encode()).hexdigest()[:16] if transcript else None

    return meta_hash, tx_hash


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_passage_fields(bible_text: Optional[str]) -> dict:
    """Return primary passage fields (book, chapter, verse_start, verse_end) or NULLs."""
    if not bible_text:
        return {'book': None, 'chapter': None, 'verse_start': None, 'verse_end': None}
    parsed = parse_reference_multi(bible_text)
    if not parsed:
        return {'book': None, 'chapter': None, 'verse_start': None, 'verse_end': None}
    first = parsed[0]
    return {
        'book': first['book'],
        'chapter': first['chapter_start'],
        'verse_start': first['verse_start'],
        'verse_end': first['verse_end'],
    }


def upsert_sermon(conn, sermon_remote) -> str:
    """Upsert a sermon row, keyed on sermonaudio_id. Returns 'new' | 'noop' | 'updated'."""
    row = conn.execute(
        "SELECT id, metadata_hash, transcript_hash, source_version, sync_status "
        "FROM sermons WHERE sermonaudio_id = ?",
        (getattr(sermon_remote, 'sermon_id'),),
    ).fetchone()

    new_meta, new_tx = compute_hashes(sermon_remote)
    classified_as, reason = classify(sermon_remote)
    now = _now()

    if row is None:
        passage_fields = _parse_passage_fields(getattr(sermon_remote, 'bible_text', None))
        conn.execute("""
            INSERT INTO sermons (
                sermonaudio_id, broadcaster_id, title, speaker_name, event_type, series,
                preach_date, publish_date, duration_seconds,
                bible_text_raw, book, chapter, verse_start, verse_end,
                audio_url, transcript_text, transcript_source,
                sermon_type, classified_as, classification_reason,
                metadata_hash, transcript_hash, source_version, remote_updated_at,
                sync_status, last_state_change_at,
                first_synced_at, last_synced_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      'expository', ?, ?, ?, ?, 1, ?,
                      CASE WHEN ? IS NOT NULL THEN 'transcript_ready' ELSE 'synced_metadata' END,
                      ?, ?, ?, ?, ?)
        """, (
            getattr(sermon_remote, 'sermon_id'),
            getattr(sermon_remote, 'broadcaster_id'),
            getattr(sermon_remote, 'title'),
            getattr(sermon_remote, 'speaker_name', None),
            getattr(sermon_remote, 'event_type', None),
            getattr(sermon_remote, 'series', None),
            str(getattr(sermon_remote, 'preach_date', None)),
            str(getattr(sermon_remote, 'publish_date', None)),
            getattr(sermon_remote, 'duration', None),
            getattr(sermon_remote, 'bible_text', None),
            passage_fields['book'], passage_fields['chapter'],
            passage_fields['verse_start'], passage_fields['verse_end'],
            getattr(sermon_remote, 'audio_url', None),
            getattr(sermon_remote, 'transcript', None),
            'sermonaudio',
            classified_as, reason,
            new_meta, new_tx,
            str(getattr(sermon_remote, 'update_date', None)),
            getattr(sermon_remote, 'transcript', None),
            now, now, now, now, now,
        ))
        return 'new'

    if row[1] == new_meta and row[2] == new_tx:
        conn.execute(
            "UPDATE sermons SET last_synced_at = ? WHERE id = ?",
            (now, row[0]),
        )
        return 'noop'

    new_version = row[3] + 1
    current_status = row[4]
    next_status = current_status
    if current_status in ('review_ready', 'transcript_ready', 'analysis_pending',
                          'analysis_running', 'analysis_failed'):
        next_status = 'analysis_pending' if row[2] and new_tx else 'synced_metadata'
    elif current_status == 'synced_metadata' and new_tx and row[2] != new_tx:
        next_status = 'transcript_ready'

    passage_fields = _parse_passage_fields(getattr(sermon_remote, 'bible_text', None))
    conn.execute("""
        UPDATE sermons SET
            title = ?, speaker_name = ?, event_type = ?, series = ?,
            preach_date = ?, publish_date = ?, duration_seconds = ?,
            bible_text_raw = ?, book = ?, chapter = ?, verse_start = ?, verse_end = ?,
            audio_url = ?, transcript_text = ?,
            classified_as = ?, classification_reason = ?,
            metadata_hash = ?, transcript_hash = ?, source_version = ?, remote_updated_at = ?,
            sync_status = ?, last_state_change_at = ?, last_synced_at = ?, updated_at = ?
        WHERE id = ?
    """, (
        getattr(sermon_remote, 'title'),
        getattr(sermon_remote, 'speaker_name', None),
        getattr(sermon_remote, 'event_type', None),
        getattr(sermon_remote, 'series', None),
        str(getattr(sermon_remote, 'preach_date', None)),
        str(getattr(sermon_remote, 'publish_date', None)),
        getattr(sermon_remote, 'duration', None),
        getattr(sermon_remote, 'bible_text', None),
        passage_fields['book'], passage_fields['chapter'],
        passage_fields['verse_start'], passage_fields['verse_end'],
        getattr(sermon_remote, 'audio_url', None),
        getattr(sermon_remote, 'transcript', None),
        classified_as, reason,
        new_meta, new_tx, new_version,
        str(getattr(sermon_remote, 'update_date', None)),
        next_status, now, now, now, row[0],
    ))
    return 'updated'
