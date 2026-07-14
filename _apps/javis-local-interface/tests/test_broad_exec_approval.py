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


def _server(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_CLAUDE_EXEC", "true")
    monkeypatch.setenv("JAVIS_ENABLE_BROWSER", "true")
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_VP_EFFECTS", "true")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)
    return server


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def _approved_gate(repo, *, action: str, route: str, project_id: str, spec_hash: str = ""):
    approval_id = repo.approvals.add(
        f"{action} test",
        kind="route_gate",
        action=action,
        route=route,
        project_id=project_id,
        risk_level="high",
        spec_hash=spec_hash,
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    return approval_id


def test_agents_run_requires_single_use_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    monkeypatch.setitem(sys.modules, "agent_runner", SimpleNamespace(run_agent=lambda agent_id, task: {"ok": True, "agent_id": agent_id, "task": task}))

    blocked = _json(asyncio.run(server.agents_run(
        server.AgentRunRequest(agent_id="nova", task="x", project_id=server.gate.CORE_SCOPE),
        x_javes_local_token=TEST_TOKEN,
    )))
    assert blocked["status"] == "approval_required"

    approval_id = _approved_gate(repo, action="agents.run", route="/agents/run", project_id=server.gate.CORE_SCOPE)
    first = _json(asyncio.run(server.agents_run(
        server.AgentRunRequest(agent_id="nova", task="x", project_id=server.gate.CORE_SCOPE, approved=True, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))
    second = _json(asyncio.run(server.agents_run(
        server.AgentRunRequest(agent_id="nova", task="x", project_id=server.gate.CORE_SCOPE, approved=True, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert first == {"ok": True, "agent_id": "nova", "task": "x"}
    assert second["status"] == "approval_required"
    assert second["approval_status"] == "consumed"


def test_browser_run_requires_single_use_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    async def _run_task(task):
        return {"ok": True, "result": f"browser:{task}"}

    monkeypatch.setitem(sys.modules, "browser_agent", SimpleNamespace(run_task=_run_task))

    blocked = _json(asyncio.run(server.browser_run(
        server.BrowserRequest(task="abrir site", project_id=server.gate.CORE_SCOPE),
        x_javes_local_token=TEST_TOKEN,
    )))
    assert blocked["status"] == "approval_required"

    # R5.1: a aprovação de browser.run é amarrada ao hash da tarefa aprovada
    task_hash = server._browser_task_hash("abrir site", server.gate.CORE_SCOPE)
    approval_id = _approved_gate(repo, action="browser.run", route="/browser/run",
                                 project_id=server.gate.CORE_SCOPE, spec_hash=task_hash)
    first = _json(asyncio.run(server.browser_run(
        server.BrowserRequest(task="abrir site", project_id=server.gate.CORE_SCOPE, approved=True, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))
    second = _json(asyncio.run(server.browser_run(
        server.BrowserRequest(task="abrir site", project_id=server.gate.CORE_SCOPE, approved=True, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert first == {"ok": True, "result": "browser:abrir site"}
    assert second["status"] == "approval_required"
    assert second["approval_status"] == "consumed"


def test_train_youtube_requires_single_use_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    monkeypatch.setitem(sys.modules, "knowledge", SimpleNamespace(build_index=lambda force=True: {"status": "ok"}))
    monkeypatch.setattr(server, "_extract_yt_transcript", lambda url: {"title": "Video", "channel": "Canal", "text": "transcricao"})
    monkeypatch.setattr(server, "_save_training_doc", lambda agent_id, title, text, url: "khan_Video.md")

    blocked = _json(asyncio.run(server.train_youtube(
        server.TrainRequest(url="https://youtube.com/watch?v=x", project_id=server.gate.CORE_SCOPE),
        x_javes_local_token=TEST_TOKEN,
    )))
    assert blocked["status"] == "approval_required"

    approval_id = _approved_gate(repo, action="train.youtube", route="/train/youtube", project_id=server.gate.CORE_SCOPE)
    first = _json(asyncio.run(server.train_youtube(
        server.TrainRequest(url="https://youtube.com/watch?v=x", project_id=server.gate.CORE_SCOPE, approved=True, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))
    second = _json(asyncio.run(server.train_youtube(
        server.TrainRequest(url="https://youtube.com/watch?v=x", project_id=server.gate.CORE_SCOPE, approved=True, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert first["status"] == "ok"
    assert first["file"] == "khan_Video.md"
    assert second["status"] == "approval_required"
    assert second["approval_status"] == "consumed"
