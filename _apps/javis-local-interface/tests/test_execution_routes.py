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
CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


def _server(monkeypatch):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    return importlib.import_module("server")


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


class FakeFacade:
    def __init__(self):
        self.started = False
        self.merged = False

    def list_tasks(self, project_id, status=None):
        return [{"task_id": "exec_aaaaaaaaaaaaaaaa", "project_id": project_id, "status": status or "draft"}]

    def create_task(self, **kwargs):
        assert "repository_path" not in kwargs
        assert "worktree_path" not in kwargs
        return {"task_id": "exec_aaaaaaaaaaaaaaaa", "project_id": kwargs["project_id"], "status": "draft"}

    def get_task(self, task_id, project_id):
        if project_id != CORE:
            return {"status": "blocked", "reason": "project_scope_mismatch"}
        return {"task_id": task_id, "project_id": project_id, "status": "draft"}

    def result_summary(self, task_id, project_id):
        return {"status": "ok", "task_id": task_id, "project_id": project_id, "summary": {}, "diff": "", "tests": ""}

    def request_start_approval(self, task_id, project_id):
        return {"task_id": task_id, "project_id": project_id, "status": "pending_approval", "approval_id": 1}

    def approve_start(self, task_id, project_id, approval_id):
        return {"task_id": task_id, "project_id": project_id, "status": "approved", "approval_id": approval_id}

    def start_execution(self, task_id, project_id, test_commands):
        self.started = True
        return {"status": "blocked", "reason": "supervised_execution_disabled", "task_id": task_id}

    def request_merge_approval(self, task_id, project_id):
        return {"task_id": task_id, "project_id": project_id, "status": "awaiting_review", "merge_approval_id": 2}

    def approve_merge(self, task_id, project_id, approval_id):
        return {"task_id": task_id, "project_id": project_id, "status": "approved_for_merge", "merge_approval_id": approval_id}

    def perform_merge(self, task_id, project_id):
        self.merged = True
        return {"status": "blocked", "reason": "merge_approval_id_required", "task_id": task_id}

    def cancel_task(self, task_id, project_id):
        return {"status": "canceled", "task_id": task_id, "project_id": project_id}


def test_execution_routes_exigem_token(monkeypatch):
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.execution_tasks_list()))

    assert body["status"] == "blocked"
    assert body["reason"] == "unauthorized_local_token_required"


def test_create_route_nao_aceita_paths_do_frontend(monkeypatch):
    server = _server(monkeypatch)
    fake = FakeFacade()
    monkeypatch.setattr(server, "_execution_facade", lambda: fake)

    req = server.ExecutionTaskCreateRequest(
        objective="programar x",
        project_id=CORE,
        executor="codex",
    )
    body = _json(asyncio.run(server.execution_tasks_create(req, x_javes_local_token=TEST_TOKEN)))

    assert body["task_id"] == "exec_aaaaaaaaaaaaaaaa"
    assert "repository_path" not in body
    assert "worktree_path" not in body


def test_outro_project_id_nao_le_task(monkeypatch):
    server = _server(monkeypatch)
    monkeypatch.setattr(server, "_execution_facade", lambda: FakeFacade())

    body = _json(asyncio.run(server.execution_tasks_get(
        "exec_aaaaaaaaaaaaaaaa",
        project_id=JAMPA,
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body["status"] == "blocked"
    assert body["reason"] == "project_scope_mismatch"


def test_start_com_flag_false_bloqueia_sem_adapter(monkeypatch):
    server = _server(monkeypatch)
    fake = FakeFacade()
    monkeypatch.setattr(server, "_execution_facade", lambda: fake)

    body = _json(asyncio.run(server.execution_start(
        "exec_aaaaaaaaaaaaaaaa",
        server.ExecutionStartRequest(project_id=CORE, test_commands=[]),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body["reason"] == "supervised_execution_disabled"
    assert fake.started is True


def test_merge_sem_segundo_approval_bloqueia_e_nao_faz_push(monkeypatch):
    server = _server(monkeypatch)
    fake = FakeFacade()
    monkeypatch.setattr(server, "_execution_facade", lambda: fake)

    body = _json(asyncio.run(server.execution_merge(
        "exec_aaaaaaaaaaaaaaaa",
        server.ExecutionProjectRequest(project_id=CORE),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body["reason"] == "merge_approval_id_required"
    assert fake.merged is True
