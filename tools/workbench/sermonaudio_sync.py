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

import re
import urllib.request
from types import SimpleNamespace

BRYAN_SPEAKER_NAME = 'Bryan Schneider'
SERMON_EVENT_TYPES = frozenset({'Sunday Service'})
DEVOTIONAL_EVENT_TYPES = frozenset({'Devotional', 'Daily Devotional'})


def _fetch_srt_as_text(url: str) -> Optional[str]:
    """Download an SRT caption file and strip timestamps to plain text.

    Uses the sermonaudio library's authenticated session since caption URLs
    require API key auth (403 without it).
    """
    try:
        import sermonaudio
        resp = sermonaudio._session.get(url, timeout=30)
        if not resp.ok:
            return None
        raw = resp.text
        lines = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.isdigit():
                continue
            if re.match(r'\d{2}:\d{2}:\d{2}', line):
                continue
            lines.append(line)
        return ' '.join(lines) if lines else None
    except Exception:
        return None


def normalize_remote(sermon) -> SimpleNamespace:
    """Convert a sermonaudio Sermon model object to the flat shape our code expects."""
    audio = sermon.media.audio[0] if getattr(sermon, 'media', None) and sermon.media.audio else None
    caption = sermon.media.caption[0] if getattr(sermon, 'media', None) and sermon.media.caption else None

    transcript = None
    if caption and caption.download_url:
        transcript = _fetch_srt_as_text(caption.download_url)

    event_type = getattr(sermon.event_type, 'value', str(sermon.event_type)) if sermon.event_type else None

    return SimpleNamespace(
        sermon_id=sermon.sermon_id,
        broadcaster_id=sermon.broadcaster.broadcaster_id if sermon.broadcaster else None,
        title=sermon.full_title,
        speaker_name=sermon.speaker.display_name if sermon.speaker else None,
        event_type=event_type,
        series=sermon.series.title if sermon.series else None,
        preach_date=sermon.preach_date,
        publish_date=sermon.publish_timestamp.date() if getattr(sermon, 'publish_timestamp', None) else None,
        duration=audio.duration if audio else None,
        bible_text=sermon.bible_text,
        audio_url=audio.stream_url if audio else None,
        transcript=transcript,
        update_date=sermon.update_date,
    )


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


def _write_sermon_passages(conn, sermon_id: int, bible_text: Optional[str]) -> tuple[str, str]:
    """Write sermon_passages rows. Returns (sermon_type, match_status) for the parent sermon.

    Deletes any prior rows for this sermon before inserting new ones.
    """
    conn.execute("DELETE FROM sermon_passages WHERE sermon_id = ?", (sermon_id,))
    if not bible_text:
        return ('topical', 'topical_no_match')

    passages = parse_reference_multi(bible_text)
    if not passages:
        return ('topical', 'topical_no_match')

    now = _now()
    for rank, p in enumerate(passages, start=1):
        conn.execute("""
            INSERT INTO sermon_passages (
                sermon_id, rank, book, chapter_start, verse_start,
                chapter_end, verse_end, raw_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sermon_id, rank, p['book'],
            p['chapter_start'], p['verse_start'],
            p['chapter_end'], p['verse_end'],
            p.get('raw_text', bible_text), now,
        ))
    return ('expository', 'unmatched')


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
        sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        sermon_type, match_status = _write_sermon_passages(conn, sermon_id,
                                                            getattr(sermon_remote, 'bible_text', None))
        conn.execute(
            "UPDATE sermons SET sermon_type = ?, match_status = ? WHERE id = ?",
            (sermon_type, match_status, sermon_id),
        )
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
    sermon_type, match_status = _write_sermon_passages(conn, row[0],
                                                        getattr(sermon_remote, 'bible_text', None))
    conn.execute(
        "UPDATE sermons SET sermon_type = ?, match_status = ? WHERE id = ?",
        (sermon_type, match_status, row[0]),
    )
    return 'updated'


import uuid
import fcntl


def run_sync_with_client(db, client, broadcaster_id: str, trigger: str = 'cron',
                         since: Optional[str] = None, limit: int = 100) -> dict:
    """Execute a sync run against an injected SermonAudio-shaped client.

    This is the core logic; the file-lock + APScheduler wrapper lives in run_sync().
    Returns the final sermon_sync_log row as a dict.
    """
    run_id = str(uuid.uuid4())
    started_at = _now()
    counters = {
        'sermons_fetched': 0, 'sermons_new': 0, 'sermons_updated': 0,
        'sermons_noop': 0, 'sermons_skipped': 0, 'sermons_failed': 0,
    }

    conn = db._conn()
    conn.execute("""
        INSERT INTO sermon_sync_log (run_id, trigger, started_at, status)
        VALUES (?, ?, ?, 'running')
    """, (run_id, trigger, started_at))
    conn.commit()

    error_summary = None
    status = 'completed'
    try:
        raw_remotes = client.list_sermons_updated_since(broadcaster_id, since=since, limit=limit)
        counters['sermons_fetched'] = len(raw_remotes)
        for raw in raw_remotes:
            try:
                remote = normalize_remote(raw) if not isinstance(raw, SimpleNamespace) else raw
                result = upsert_sermon(conn, remote)
                if result == 'new':
                    counters['sermons_new'] += 1
                elif result == 'updated':
                    counters['sermons_updated'] += 1
                elif result == 'noop':
                    counters['sermons_noop'] += 1
                conn.commit()
            except Exception as e:
                counters['sermons_failed'] += 1
                try:
                    conn.execute("""
                        UPDATE sermons SET sync_status='sync_failed',
                                           sync_error = ?,
                                           failure_count = failure_count + 1,
                                           last_failure_at = ?,
                                           last_state_change_at = ?
                        WHERE sermonaudio_id = ?
                    """, (str(e), _now(), _now(), getattr(remote, 'sermon_id', None)))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        status = 'failed'
        error_summary = f'{type(e).__name__}: {e}'

    conn.execute("""
        UPDATE sermon_sync_log SET
            ended_at = ?,
            sermons_fetched = ?, sermons_new = ?, sermons_updated = ?,
            sermons_noop = ?, sermons_skipped = ?, sermons_failed = ?,
            error_summary = ?, status = ?
        WHERE run_id = ?
    """, (
        _now(),
        counters['sermons_fetched'], counters['sermons_new'], counters['sermons_updated'],
        counters['sermons_noop'], counters['sermons_skipped'], counters['sermons_failed'],
        error_summary, status, run_id,
    ))
    conn.commit()
    conn.close()

    return {'run_id': run_id, 'status': status, 'error_summary': error_summary, **counters}


class SermonAudioAPIClient:
    """Thin wrapper over the sermonaudio PyPI library with a testable shape."""

    def __init__(self, api_key: str):
        import sermonaudio
        sermonaudio.set_api_key(api_key)
        self._sa = sermonaudio

    def list_sermons_updated_since(self, broadcaster_id, since=None, limit=100):
        from sermonaudio.node.requests import Node
        kwargs = {'broadcaster_id': broadcaster_id, 'page_size': limit}
        if since:
            kwargs['updated_since'] = since
        try:
            result = Node.get_sermons(**kwargs)
        except TypeError:
            result = Node.get_sermons(broadcaster_id=broadcaster_id, page_size=limit)
        return list(getattr(result, 'results', result) or [])

    def get_sermon_detail(self, sermon_id):
        from sermonaudio.node.requests import Node
        return Node.get_sermon(sermon_id)


def _lock_path():
    return os.path.join(os.path.dirname(__file__), '.sermon_sync.lock')


def run_sync(db, api_key: str = '', broadcaster_id: str = '', trigger: str = 'cron',
             client=None, since: Optional[str] = None, limit: int = 100) -> Optional[dict]:
    """Acquire file lock, call run_sync_with_client, release. Returns None if locked."""
    lock_path = _lock_path()
    with open(lock_path, 'w') as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None
        try:
            if client is None:
                client = SermonAudioAPIClient(api_key)
            return run_sync_with_client(db, client, broadcaster_id, trigger=trigger,
                                        since=since, limit=limit)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
