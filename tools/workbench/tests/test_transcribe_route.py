"""Integration tests for POST /study/transcribe.

Uses Flask's test client + a monkeypatched ``whisper_service.transcribe_audio``
so tests don't actually load the 1.5 GB Whisper model.
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

import pytest

# Re-use the ``client`` fixture defined for the rest of the /study route tests.
from test_study_routes import client as _raw_client, _make_study_session  # noqa: F401


@pytest.fixture
def client(_raw_client):
    """Authenticated test client — /study routes sit behind require_auth."""
    with _raw_client.session_transaction() as sess:
        sess['authenticated'] = True
    return _raw_client


@pytest.fixture
def stub_transcribe(monkeypatch):
    """Replace the actual Whisper call with a deterministic stub."""
    calls = {'audio': None, 'content_type': None, 'count': 0}

    def fake(audio_bytes, content_type='audio/webm'):
        calls['audio'] = audio_bytes
        calls['content_type'] = content_type
        calls['count'] += 1
        return {
            'text': 'the stubbed transcription result',
            'duration_sec': 1.23,
            'language': 'en',
        }

    import whisper_service
    monkeypatch.setattr(whisper_service, 'transcribe_audio', fake)
    return calls


def _post_audio(client, session_id, data=b'audio-bytes', filename='clip.webm', content_type='audio/webm'):
    return client.post(
        f'/study/session/{session_id}/transcribe',
        data={'audio': (io.BytesIO(data), filename, content_type)},
        content_type='multipart/form-data',
    )


def test_transcribe_returns_text(client, stub_transcribe):
    sid, _ = _make_study_session(client)
    resp = _post_audio(client, sid, data=b'some-audio-bytes')

    assert resp.status_code == 200
    body = resp.get_json()
    assert body['text'] == 'the stubbed transcription result'


def test_transcribe_forwards_audio_bytes_and_content_type(client, stub_transcribe):
    sid, _ = _make_study_session(client)
    _post_audio(client, sid, data=b'abc123', content_type='audio/webm')

    assert stub_transcribe['audio'] == b'abc123'
    assert stub_transcribe['content_type'] == 'audio/webm'


def test_transcribe_rejects_unknown_session(client, stub_transcribe):
    resp = _post_audio(client, 9_999_999)

    assert resp.status_code == 404
    assert stub_transcribe['count'] == 0


def test_transcribe_rejects_missing_audio_field(client, stub_transcribe):
    sid, _ = _make_study_session(client)
    resp = client.post(
        f'/study/session/{sid}/transcribe',
        data={},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 400
    assert stub_transcribe['count'] == 0


def test_transcribe_rejects_empty_audio(client, stub_transcribe):
    sid, _ = _make_study_session(client)
    resp = _post_audio(client, sid, data=b'')

    assert resp.status_code == 400
    assert stub_transcribe['count'] == 0


def test_transcribe_rejects_oversize_audio(client, stub_transcribe):
    sid, _ = _make_study_session(client)
    # Hard cap is 25 MB; send 26 MB to trigger 413.
    big = b'0' * (26 * 1024 * 1024)
    resp = _post_audio(client, sid, data=big)

    assert resp.status_code == 413
    assert stub_transcribe['count'] == 0


def test_transcribe_returns_500_when_model_fails(client, monkeypatch):
    import whisper_service

    def boom(audio_bytes, content_type='audio/webm'):
        raise RuntimeError('model blew up')

    monkeypatch.setattr(whisper_service, 'transcribe_audio', boom)

    sid, _ = _make_study_session(client)
    resp = _post_audio(client, sid, data=b'audio')

    assert resp.status_code == 500
    body = resp.get_json()
    assert 'error' in body
