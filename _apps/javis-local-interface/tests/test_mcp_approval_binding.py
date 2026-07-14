"""R5.1 — MCP agora exige gate completo: token, project_id, approval amarrada ao payload.

Antes de R5.1, `/mcp/{server_id}/call` só checava `mcp_enabled()` — rotas HTTP
completamente abertas. Chamadas MCP = tools remotos = risco alto → gate completo
agora (token local, escopo, approval persistido) e approval amarrada ao hash da
chamada (servidor + tool + argumentos).
"""
from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

TEST_TOKEN = "test-local-token"
CORE = "javes-core"


def _server(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_MCP", "true")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)
    db.init_db()
    return server


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def _call(server, server_id="test", tool="list", arguments=None, approval_id=None,
          approved=False, project_id=CORE):
    return _json(asyncio.run(server.mcp_call(
        server_id,
        server.MCPCallRequestWithAuth(
            tool=tool, arguments=arguments or {},
            project_id=project_id, approved=approved, approval_id=approval_id,
        ),
        x_javes_local_token=TEST_TOKEN,
    )))


def _approve_for(server, repo, server_id, tool, arguments, project_id=CORE):
    """Cria e aprova um approval amarrado ao hash da chamada MCP."""
    call_hash = server._mcp_call_hash(server_id, tool, arguments, project_id)
    approval_id = repo.approvals.add(
        "mcp call", kind="route_gate", project_id=project_id,
        action="mcp.call", route=f"/mcp/{server_id}/call", risk_level="high",
        spec_hash=call_hash,
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    return approval_id


# ── token local ────────────────────────────────────────────────────────
def test_mcp_exige_token_local(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)

    result = _json(asyncio.run(server.mcp_call(
        "test",
        server.MCPCallRequestWithAuth(tool="list"),
        x_javes_local_token="wrong-token",  # token inválido
    )))

    assert result["status"] in ("blocked", "gate_denied")


# ── project_id obrigatório ────────────────────────────────────────────
def test_mcp_exige_project_scope(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)

    result = _json(asyncio.run(server.mcp_call(
        "test",
        server.MCPCallRequestWithAuth(tool="list", project_id="unknown-scope"),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert result["status"] in ("blocked", "gate_denied", "project_scope_mismatch")


# ── flag ────────────────────────────────────────────────────────────────
def test_mcp_flag_desligada_bloqueia(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_MCP", "false")  # flag off
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)

    result = _call(server, server_id="test", tool="list")

    assert result["status"] == "disabled_by_default"


# ── approval é single-use e amarrada ao payload ──────────────────────
def test_mcp_approval_single_use(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    call_hash = server._mcp_call_hash("test", "list", {}, CORE)
    approval_id = repo.approvals.add(
        "mcp", kind="route_gate", project_id=CORE,
        action="mcp.call", route="/mcp/test/call", spec_hash=call_hash,
    )
    repo.approvals.decide(approval_id, True, approved_by="test")

    # primeira chamada (mesma que foi aprovada)
    first = _call(server, server_id="test", tool="list", arguments={}, approval_id=approval_id)
    assert first["status"] == "ok" or first["status"] == "error"  # sucesso ou erro da MCP, não gate
    assert repo.approvals.get(approval_id)["consumed_at"] is not None

    # segunda chamada com a mesma approval
    second = _call(server, server_id="test", tool="list", arguments={}, approval_id=approval_id)
    assert second["status"] == "approval_required"
    assert second["approval_status"] == "consumed"


def test_mcp_trocar_server_invalida_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = _approve_for(server, repo, "server-a", "list", {})

    # chamar o MESMO tool no servidor DIFERENTE com MESMA approval = recusado
    result = _call(server, server_id="server-b", tool="list", arguments={}, approval_id=approval_id)

    assert result["status"] == "approval_required"
    assert not repo.approvals.get(approval_id)["consumed_at"]  # não consumido


def test_mcp_trocar_tool_invalida_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = _approve_for(server, repo, "test", "list", {})

    # chamar FERRAMENTA DIFERENTE no MESMO servidor com MESMA approval = recusado
    result = _call(server, server_id="test", tool="execute", arguments={}, approval_id=approval_id)

    assert result["status"] == "approval_required"
    assert not repo.approvals.get(approval_id)["consumed_at"]


def test_mcp_trocar_argumentos_invalida_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = _approve_for(server, repo, "test", "run", {"script": "echo ok"})

    # mesma chamada mas argumentos diferentes = recusado
    result = _call(server, server_id="test", tool="run", arguments={"script": "rm -rf /"},
                   approval_id=approval_id)

    assert result["status"] == "approval_required"
    assert not repo.approvals.get(approval_id)["consumed_at"]


def test_mcp_isolation_por_projeto(monkeypatch, tmp_path):
    """Approval pra MCP no projeto A não vale pro projeto B."""
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = _approve_for(server, repo, "test", "list", {}, project_id="project-a")

    # tentar usar a mesma approval no projeto B
    result = _call(server, server_id="test", tool="list", arguments={},
                   approval_id=approval_id, project_id="project-b")

    # Bloqueia no gate de project_scope OU no approval (diferentes hashes por projeto)
    assert result["status"] in ("blocked", "gate_denied", "approval_required", "project_scope_mismatch")


def test_mcp_hash_inclui_argumentos_ordem_nao_importa(monkeypatch, tmp_path):
    """Hash de arguments é canônico JSON: ordem não muda o hash."""
    server = _server(monkeypatch, tmp_path)

    h1 = server._mcp_call_hash("s", "t", {"a": 1, "b": 2}, CORE)
    h2 = server._mcp_call_hash("s", "t", {"b": 2, "a": 1}, CORE)
    assert h1 == h2
