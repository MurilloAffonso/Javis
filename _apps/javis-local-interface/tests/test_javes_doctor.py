from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

BACKEND = Path(__file__).resolve().parents[1] / "backend"
ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import db  # noqa: E402
import javes_doctor  # noqa: E402
import system_health  # noqa: E402


def _blocked_module(name: str) -> ModuleType:
    module = ModuleType(name)

    def _getattr(attr: str):
        raise AssertionError(f"{name} nao deveria ser chamado pelo doctor: {attr}")

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    return module


def test_doctor_nao_mostra_token_ou_chave(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(system_health, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "missing.db")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", "token-super-secreto")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")

    assert javes_doctor.main(["--no-probe"]) == 0
    out = capsys.readouterr().out

    assert "token-super-secreto" not in out
    assert "sk-secret-value" not in out
    assert "local_token_configured: sim" in out


def test_doctor_nao_chama_provider_cloud(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(system_health, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "missing.db")
    for name in ("openai", "anthropic", "google.generativeai"):
        monkeypatch.setitem(sys.modules, name, _blocked_module(name))

    assert javes_doctor.main(["--no-probe"]) == 0
    assert "Javes doctor" in capsys.readouterr().out


def test_doctor_funciona_sem_servidor_json(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(system_health, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "missing.db")

    assert javes_doctor.main(["--json", "--no-probe"]) == 0
    data = json.loads(capsys.readouterr().out)

    assert data["provider_mode"] in {"local", "cloud", "auto"}
    assert "providers" in data


def test_doctor_detecta_current_state(monkeypatch, tmp_path):
    state = tmp_path / "_estado" / "CURRENT_STATE.md"
    state.parent.mkdir(parents=True)
    state.write_text("# CURRENT STATE", encoding="utf-8")
    monkeypatch.setattr(system_health, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "missing.db")

    data = system_health.snapshot(probe_ollama=False)

    assert data["current_state_present"] is True
