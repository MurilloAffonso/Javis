"""Rotas do Modo Madrugada no Command Center — read-only + kill switch.

O painel web é deliberadamente read-only: mostra o preflight e deixa desarmar
(direção segura). Rodar a Madrugada continua só no CLI. Estes testes provam que
as rotas exigem token local, não executam nada, e que o kill switch de fato
liga/desliga o arquivo-sentinela.
"""
from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

TEST_TOKEN = "test-local-token"


def _server(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)
    db.init_db()
    # kill switch isolado no tmp, para não tocar no _estado real
    import execution.night_mode as nm
    monkeypatch.setattr(nm, "KILL_SWITCH", tmp_path / "MADRUGADA.OFF")
    return server


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def test_status_exige_token_local(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    out = _json(asyncio.run(server.madrugada_status(x_javes_local_token="errado")))
    assert out["status"] in ("blocked", "gate_denied")


def test_status_readonly_reporta_preflight(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    out = _json(asyncio.run(server.madrugada_status(x_javes_local_token=TEST_TOKEN)))
    assert out["status"] == "ok"
    assert "night_mode_enabled" in out
    assert "preflight" in out
    # sem flags ligados, o preflight é bloqueado — mas a rota nunca executa nada
    assert out["preflight"]["status"] in ("ready", "blocked")


def test_kill_switch_exige_token_local(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    out = _json(asyncio.run(server.madrugada_kill_switch(
        server.MadrugadaKillSwitchRequest(armed=False),
        x_javes_local_token="errado",
    )))
    assert out["status"] in ("blocked", "gate_denied")


def test_kill_switch_desarma_e_rearma(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import execution.night_mode as nm

    # desarmar cria o arquivo-sentinela
    off = _json(asyncio.run(server.madrugada_kill_switch(
        server.MadrugadaKillSwitchRequest(armed=False),
        x_javes_local_token=TEST_TOKEN,
    )))
    assert off["status"] == "ok"
    assert off["kill_switch_active"] is True
    assert nm.KILL_SWITCH.exists()

    # rearmar remove o arquivo
    on = _json(asyncio.run(server.madrugada_kill_switch(
        server.MadrugadaKillSwitchRequest(armed=True),
        x_javes_local_token=TEST_TOKEN,
    )))
    assert on["status"] == "ok"
    assert on["kill_switch_active"] is False
    assert not nm.KILL_SWITCH.exists()


def test_kill_switch_ativo_aparece_no_preflight(monkeypatch, tmp_path):
    """Desarmar pela rota tem que refletir no status read-only."""
    server = _server(monkeypatch, tmp_path)

    asyncio.run(server.madrugada_kill_switch(
        server.MadrugadaKillSwitchRequest(armed=False),
        x_javes_local_token=TEST_TOKEN,
    ))
    out = _json(asyncio.run(server.madrugada_status(x_javes_local_token=TEST_TOKEN)))
    assert out["preflight"]["kill_switch_active"] is True
