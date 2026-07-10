from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import gate  # noqa: E402
import provider_health  # noqa: E402
import provider_registry  # noqa: E402


def test_registry_contem_providers_iniciais():
    ids = {item["id"] for item in provider_registry.all_providers()}
    assert {"ollama", "openai", "gemini", "claude", "openrouter"} <= ids


def test_modo_local_nunca_seleciona_cloud(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    selected = provider_registry.selected_provider_ids("local")

    assert selected == ["ollama"]


def test_modo_auto_escolhe_ollama_primeiro(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    selected = provider_registry.selected_provider_ids("auto")

    assert selected[0] == "ollama"
    assert "openai" in selected


def test_provider_em_cooldown_e_pulado(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    provider_health.record_failure("gemini", type("E", (), {"status_code": 429})())

    selected = provider_registry.selected_provider_ids("cloud")

    assert "gemini" not in selected


def test_rotas_vp_jampa_continuam_exigindo_project_id_explicito():
    assert gate.require_project_scope("", scope=gate.CEREBRO_JAMPA_SCOPE)["reason"] == "project_id_required"
    assert gate.require_project_scope("javes-core", scope=gate.CEREBRO_JAMPA_SCOPE)["reason"] == "project_id_mismatch"
    assert gate.require_project_scope(gate.CEREBRO_JAMPA_SCOPE, scope=gate.CEREBRO_JAMPA_SCOPE) is None
