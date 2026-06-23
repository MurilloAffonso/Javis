"""TTS local via Piper — grátis, sem rede, sem chave de API.

Usado só pela rota não-real-time (`/tts`). O ack/streaming de voz em tempo
real (`_tts_sentence`/`_tts_ack` em server.py) continua no OpenAI — latência
ali já foi calibrada (ver _logs/2026-06-17_voz-latencia.md) e não é o alvo
desta rota.
"""
from __future__ import annotations

import io
import os
import wave
from pathlib import Path

_MODEL_DIR = Path(__file__).parent / "models" / "piper"
_DEFAULT_MODEL = "pt_BR-faber-medium"

_voice_cache: dict[str, object] = {}


def _voice_path(model_name: str) -> Path:
    return _MODEL_DIR / f"{model_name}.onnx"


def is_available(model_name: str | None = None) -> bool:
    model_name = model_name or os.environ.get("JAVIS_PIPER_MODEL", _DEFAULT_MODEL)
    return _voice_path(model_name).exists()


def _load_voice(model_name: str):
    if model_name not in _voice_cache:
        from piper import PiperVoice
        _voice_cache[model_name] = PiperVoice.load(str(_voice_path(model_name)))
    return _voice_cache[model_name]


def synthesize(text: str, model_name: str | None = None) -> bytes | None:
    """Gera WAV em memória via Piper local. None se modelo ausente ou erro."""
    model_name = model_name or os.environ.get("JAVIS_PIPER_MODEL", _DEFAULT_MODEL)
    if not text.strip() or not is_available(model_name):
        return None
    try:
        voice = _load_voice(model_name)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        return buf.getvalue()
    except Exception:
        return None
