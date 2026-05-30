"""Local Whisper transcription via faster-whisper.

The model is lazy-loaded on first request and kept in memory afterwards.
Default model is `small.en` (~250 MB, English-only, much faster than `small`).
Set WHISPER_MODEL env to override (e.g. `tiny.en` for slower hardware).
"""
from __future__ import annotations

import os
from threading import Lock
from typing import Any

_model_lock = Lock()
_model: Any = None


def _load_model():
    """Lazy-load faster-whisper. Imports are inside so app boot stays fast."""
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        from faster_whisper import WhisperModel

        name = os.environ.get("WHISPER_MODEL", "small.en")
        # Compute type int8 keeps memory low and is fine for short utterances on CPU.
        _model = WhisperModel(name, device="cpu", compute_type="int8")
        return _model


def transcribe(audio_path: str) -> str:
    """Return the recognized text for a recorded audio file."""
    model = _load_model()
    segments, _ = model.transcribe(audio_path, beam_size=5, language="en", vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()
