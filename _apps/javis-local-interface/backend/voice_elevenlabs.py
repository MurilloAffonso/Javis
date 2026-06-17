"""
voice_elevenlabs.py — adaptador ElevenLabs (TTS mais humano + STT + voice
cloning). Degrada com elegância: sem ELEVENLABS_API_KEY, toda função retorna
None e quem chamou cai no fallback atual (OpenAI tts-1-hd / Whisper).

Não substitui o pipeline de voz atual — é um upgrade opcional, ativado só
quando a key existir no .env. Ver _ferramentas/integracoes/RESERVATORIOS.md.
"""
from __future__ import annotations
import os
import requests

_TIMEOUT = 30
_BASE = "https://api.elevenlabs.io/v1"

# Adam — voz masculina grave em PT-BR, próxima do "onyx" atual da OpenAI
_DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"


def is_configured() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())


def _headers() -> dict:
    return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"].strip()}


def text_to_speech(text: str, voice_id: str = _DEFAULT_VOICE_ID) -> bytes | None:
    """Gera áudio (mp3 bytes) via ElevenLabs. None se sem key ou erro."""
    if not is_configured() or not text.strip():
        return None
    try:
        resp = requests.post(
            f"{_BASE}/text-to-speech/{voice_id}",
            headers={**_headers(), "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def speech_to_text(audio_bytes: bytes, filename: str = "audio.wav") -> str | None:
    """Transcreve áudio via ElevenLabs Scribe. None se sem key ou erro."""
    if not is_configured() or not audio_bytes:
        return None
    try:
        resp = requests.post(
            f"{_BASE}/speech-to-text",
            headers=_headers(),
            data={"model_id": "scribe_v1"},
            files={"file": (filename, audio_bytes)},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("text")
    except Exception:
        return None


def list_voices() -> list[dict]:
    """Lista vozes disponíveis na conta (pra Murillo escolher qual usar)."""
    if not is_configured():
        return []
    try:
        resp = requests.get(f"{_BASE}/voices", headers=_headers(), timeout=_TIMEOUT)
        resp.raise_for_status()
        return [
            {"voice_id": v["voice_id"], "name": v["name"], "category": v.get("category", "")}
            for v in resp.json().get("voices", [])
        ]
    except Exception:
        return []
