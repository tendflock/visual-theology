"""Local speech-to-text using faster-whisper.

Audio bytes in, transcribed text out. The model is lazy-loaded on first real
call so ``import whisper_service`` is cheap (app startup doesn't block on the
1.5 GB model download). Tests inject a fake model via ``set_model_for_testing``.
"""
import os
import tempfile
import threading

_MODEL = None
_MODEL_LOCK = threading.Lock()
_MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'medium')
_MODEL_DEVICE = os.environ.get('WHISPER_DEVICE', 'cpu')
_MODEL_COMPUTE = os.environ.get('WHISPER_COMPUTE_TYPE', 'int8')


def _suffix_for(content_type):
    """Pick a file suffix Whisper/ffmpeg will recognize from the browser MIME type."""
    ct = (content_type or '').lower().split(';')[0].strip()
    mapping = {
        'audio/webm': '.webm',
        'audio/ogg': '.ogg',
        'audio/mp4': '.mp4',
        'audio/m4a': '.m4a',
        'audio/mpeg': '.mp3',
        'audio/mp3': '.mp3',
        'audio/wav': '.wav',
        'audio/x-wav': '.wav',
    }
    return mapping.get(ct, '.webm')


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(_MODEL_SIZE, device=_MODEL_DEVICE, compute_type=_MODEL_COMPUTE)
    return _MODEL


def set_model_for_testing(model):
    """Inject a fake model (test hook)."""
    global _MODEL
    _MODEL = model


def _reset_for_testing():
    global _MODEL
    _MODEL = None


def transcribe_audio(audio_bytes, content_type='audio/webm'):
    """Transcribe an audio blob. Returns ``{"text", "duration_sec", "language"}``."""
    if not audio_bytes:
        raise ValueError('audio_bytes is empty')

    suffix = _suffix_for(content_type)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.close()
        model = _get_model()
        segments, info = model.transcribe(tmp.name, beam_size=5, vad_filter=True)
        text = ''.join(seg.text for seg in segments).strip()
        return {
            'text': text,
            'duration_sec': float(getattr(info, 'duration', 0.0)),
            'language': getattr(info, 'language', '') or '',
        }
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
