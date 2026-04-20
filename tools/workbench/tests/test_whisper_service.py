"""Unit tests for whisper_service — faster-whisper wrapper.

The real model is too heavy to load in tests, so we inject a fake model via
``set_model_for_testing``. The tests verify the wrapper's wiring: how it feeds
audio bytes into the model, how it joins segments, and how it handles errors.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


class _FakeSegment:
    def __init__(self, text):
        self.text = text


class _FakeInfo:
    def __init__(self, duration=1.5, language='en'):
        self.duration = duration
        self.language = language


class _FakeModel:
    """Stand-in for faster_whisper.WhisperModel."""

    def __init__(self, segments_text=None, duration=1.5, language='en', raise_on_transcribe=None):
        self.segments_text = segments_text or ['hello world']
        self.duration = duration
        self.language = language
        self.raise_on_transcribe = raise_on_transcribe
        self.last_audio_path = None
        self.last_kwargs = None

    def transcribe(self, audio_path, **kwargs):
        self.last_audio_path = audio_path
        self.last_kwargs = kwargs
        if self.raise_on_transcribe:
            raise self.raise_on_transcribe
        segments = (_FakeSegment(t) for t in self.segments_text)
        return segments, _FakeInfo(self.duration, self.language)


@pytest.fixture(autouse=True)
def _reset_module_state():
    import whisper_service
    whisper_service._reset_for_testing()
    yield
    whisper_service._reset_for_testing()


def test_transcribe_joins_segments_into_text():
    import whisper_service
    fake = _FakeModel(segments_text=[' Hello', ' world.', ' How are you?'])
    whisper_service.set_model_for_testing(fake)

    result = whisper_service.transcribe_audio(b'fake-webm-bytes', content_type='audio/webm')

    assert result['text'] == 'Hello world. How are you?'


def test_transcribe_returns_duration_and_language():
    import whisper_service
    fake = _FakeModel(segments_text=['hi'], duration=2.25, language='en')
    whisper_service.set_model_for_testing(fake)

    result = whisper_service.transcribe_audio(b'\x00\x01', content_type='audio/webm')

    assert result['duration_sec'] == pytest.approx(2.25)
    assert result['language'] == 'en'


def test_transcribe_writes_audio_to_tempfile_and_cleans_up():
    import whisper_service
    fake = _FakeModel(segments_text=['ok'])
    whisper_service.set_model_for_testing(fake)

    whisper_service.transcribe_audio(b'audio-bytes', content_type='audio/webm')

    assert fake.last_audio_path is not None
    # File should be gone after the call returns
    assert not os.path.exists(fake.last_audio_path), \
        'Temp audio file should be cleaned up after transcription'


def test_transcribe_empty_audio_raises():
    import whisper_service
    with pytest.raises(ValueError, match='empty'):
        whisper_service.transcribe_audio(b'', content_type='audio/webm')


def test_transcribe_uses_suffix_matching_content_type():
    """webm -> .webm, mp4 -> .mp4, wav -> .wav (helps ffmpeg sniff format)."""
    import whisper_service
    fake = _FakeModel(segments_text=['ok'])
    whisper_service.set_model_for_testing(fake)

    whisper_service.transcribe_audio(b'x', content_type='audio/mp4')
    assert fake.last_audio_path.endswith('.mp4')

    whisper_service.transcribe_audio(b'x', content_type='audio/wav')
    assert fake.last_audio_path.endswith('.wav')

    whisper_service.transcribe_audio(b'x', content_type='audio/webm;codecs=opus')
    assert fake.last_audio_path.endswith('.webm')


def test_transcribe_propagates_model_error():
    import whisper_service
    fake = _FakeModel(raise_on_transcribe=RuntimeError('decode failed'))
    whisper_service.set_model_for_testing(fake)

    with pytest.raises(RuntimeError, match='decode failed'):
        whisper_service.transcribe_audio(b'bad-bytes', content_type='audio/webm')


def test_transcribe_strips_leading_trailing_whitespace():
    import whisper_service
    fake = _FakeModel(segments_text=['   padded   '])
    whisper_service.set_model_for_testing(fake)

    result = whisper_service.transcribe_audio(b'x', content_type='audio/webm')

    assert result['text'] == 'padded'
