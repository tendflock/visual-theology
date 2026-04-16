import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from companion_db import CompanionDB
from sermon_coach_agent import stream_coach_response


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


class FakeStreamingClient:
    """Stub for testing. Yields fake deltas, no tool use."""
    def __init__(self, final_text='Hello from the coach.'):
        self.final_text = final_text

    def stream_message(self, system, messages, tools):
        yield {'type': 'text_delta', 'text': 'Hello'}
        yield {'type': 'text_delta', 'text': ' from'}
        yield {'type': 'text_delta', 'text': ' the coach.'}
        yield {'type': 'message_complete', 'usage': {'input_tokens': 100, 'output_tokens': 20}}


@pytest.fixture
def db_with_sermon():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = CompanionDB(path)
    db.init_db()
    conn = db._conn()
    conn.execute("""
        INSERT INTO sermons (sermonaudio_id, broadcaster_id, title, classified_as,
                              sync_status, preach_date, duration_seconds, bible_text_raw,
                              transcript_text, last_state_change_at,
                              first_synced_at, last_synced_at, created_at, updated_at)
        VALUES ('sa-c', 'bcast', 'Romans 8', 'sermon', 'review_ready',
                '2026-04-12', 2322, 'Romans 8:1-11', 'hello transcript',
                datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))
    """)
    sermon_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sermon_reviews (sermon_id, analyzer_version, homiletics_core_version, model_version,
            analyzed_transcript_hash, source_version_at_analysis, actual_duration_seconds,
            burden_clarity, top_impact_helpers, top_impact_hurters, one_change_for_next_sunday,
            computed_at)
        VALUES (?, '1.0.0', '1.0.0', 'claude-opus-4-6', 'h', 1, 2322,
                'clear', '["a"]', '["b"]', 'change', datetime('now'))
    """, (sermon_id,))
    conn.commit()
    conn.close()
    yield db, sermon_id
    os.unlink(path)


def test_stream_coach_response_persists_user_and_assistant_messages(db_with_sermon):
    db, sermon_id = db_with_sermon
    client = FakeStreamingClient()
    chunks = []
    for event in stream_coach_response(
        db=db, sermon_id=sermon_id, conversation_id=1,
        user_message='Walk me through the review',
        llm_client=client,
    ):
        chunks.append(event)
    full_text = ''.join(e['text'] for e in chunks if e.get('type') == 'text_delta')
    assert 'Hello' in full_text

    conn = db._conn()
    msgs = conn.execute(
        "SELECT role, content FROM sermon_coach_messages WHERE sermon_id = ? ORDER BY id",
        (sermon_id,)
    ).fetchall()
    conn.close()
    assert len(msgs) == 2
    # rows may be sqlite3.Row; compare via tuple()
    assert tuple(msgs[0]) == ('user', 'Walk me through the review')
    assert msgs[1][0] == 'assistant'
    assert 'Hello' in msgs[1][1]
