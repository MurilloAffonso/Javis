"""Testes offline da rota /tts (Piper local grátis -> fallback OpenAI pago).

Toda tentativa de socket falha antes de sair do processo, exceto no teste
`test_piper_real_synthesis_se_modelo_presente`, que só lê o modelo Piper do
disco (sem rede) e roda inferência onnxruntime local de verdade.
"""
from __future__ import annotations

import asyncio
import socket
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import server
import tts_local


_LOOPBACK = ("127.0.0.1", "::1", "localhost")


@pytest.fixture(autouse=True)
def zero_network_and_clean_env(monkeypatch):
    # asyncio.run() no Windows usa socket.socketpair() (loopback) como
    # self-pipe interno do event loop — precisa passar. Só bloqueia conexão
    # de rede real (não-loopback), que é o que importa pro teste offline.
    orig_connect = socket.socket.connect
    orig_connect_ex = socket.socket.connect_ex

    def _is_loopback(address):
        return isinstance(address, tuple) and address and address[0] in _LOOPBACK

    def guarded_connect(self, address, *a, **kw):
        if _is_loopback(address):
            return orig_connect(self, address, *a, **kw)
        raise AssertionError("rede bloqueada pelo teste offline")

    def guarded_connect_ex(self, address, *a, **kw):
        if _is_loopback(address):
            return orig_connect_ex(self, address, *a, **kw)
        raise AssertionError("rede bloqueada pelo teste offline")

    def blocked_create_connection(*_args, **_kwargs):
        raise AssertionError("rede bloqueada pelo teste offline")

    monkeypatch.setattr(socket, "create_connection", blocked_create_connection)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    for name in ("OPENAI_API_KEY", "JAVIS_TTS_PROVIDER", "JAVIS_TTS_VOICE", "JAVIS_TTS_MODEL"):
        monkeypatch.delenv(name, raising=False)


def _run(coro):
    return asyncio.run(coro)


def test_piper_e_o_padrao_e_nao_chama_openai(monkeypatch):
    monkeypatch.setattr(tts_local, "synthesize", lambda *_a, **_kw: b"RIFF...fake-wav")

    def nao_deveria_chamar(*_args, **_kwargs):
        raise AssertionError("OpenAI chamado com Piper disponível")

    monkeypatch.setattr("openai.OpenAI", nao_deveria_chamar, raising=False)

    resp = _run(server.text_to_speech(server.TTSRequest(text="oi")))
    assert resp.status_code == 200
    assert resp.media_type == "audio/wav"
    assert resp.body == b"RIFF...fake-wav"


def test_piper_falha_cai_pro_openai(monkeypatch):
    monkeypatch.setattr(tts_local, "synthesize", lambda *_a, **_kw: None)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    class _FakeResp:
        content = b"mp3-bytes"

    class _FakeAudio:
        def create(self, **_kw):
            return _FakeResp()

    class _FakeClient:
        def __init__(self, **_kw):
            self.audio = type("A", (), {"speech": _FakeAudio()})()

    monkeypatch.setattr("openai.OpenAI", _FakeClient)

    resp = _run(server.text_to_speech(server.TTSRequest(text="oi")))
    assert resp.status_code == 200
    assert resp.media_type == "audio/mpeg"
    assert resp.body == b"mp3-bytes"


def test_sem_piper_e_sem_key_openai_da_503(monkeypatch):
    monkeypatch.setattr(tts_local, "synthesize", lambda *_a, **_kw: None)

    resp = _run(server.text_to_speech(server.TTSRequest(text="oi")))
    assert resp.status_code == 503


def test_voice_explicita_pula_piper_direto_pro_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    chamado = []
    monkeypatch.setattr(
        tts_local, "synthesize",
        lambda *_a, **_kw: chamado.append("piper") or b"nao-devia-ser-usado",
    )

    class _FakeResp:
        content = b"mp3-bytes"

    class _FakeAudio:
        def create(self, **_kw):
            return _FakeResp()

    class _FakeClient:
        def __init__(self, **_kw):
            self.audio = type("A", (), {"speech": _FakeAudio()})()

    monkeypatch.setattr("openai.OpenAI", _FakeClient)

    resp = _run(server.text_to_speech(server.TTSRequest(text="oi", voice="onyx")))
    assert chamado == []
    assert resp.media_type == "audio/mpeg"


def test_provider_openai_forca_pular_piper(monkeypatch):
    monkeypatch.setenv("JAVIS_TTS_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    chamado = []
    monkeypatch.setattr(
        tts_local, "synthesize",
        lambda *_a, **_kw: chamado.append("piper") or b"nao-devia-ser-usado",
    )

    class _FakeResp:
        content = b"mp3-bytes"

    class _FakeAudio:
        def create(self, **_kw):
            return _FakeResp()

    class _FakeClient:
        def __init__(self, **_kw):
            self.audio = type("A", (), {"speech": _FakeAudio()})()

    monkeypatch.setattr("openai.OpenAI", _FakeClient)

    resp = _run(server.text_to_speech(server.TTSRequest(text="oi")))
    assert chamado == []
    assert resp.media_type == "audio/mpeg"


def test_texto_vazio_nao_sintetiza():
    assert tts_local.synthesize("") is None
    assert tts_local.synthesize("   ") is None


def test_piper_real_synthesis_se_modelo_presente():
    """Roda a inferência onnxruntime real (sem rede) se o modelo foi baixado."""
    if not tts_local.is_available():
        pytest.skip("modelo Piper não baixado neste ambiente")
    audio = tts_local.synthesize("Teste real do Piper, sem mock.")
    assert audio is not None
    assert audio[:4] == b"RIFF"
    assert len(audio) > 1000
