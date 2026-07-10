from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution.execution_facade import ExecutionFacade  # noqa: E402

CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


class FakeExecutionService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def run(self, task_id, project_id, *, test_commands):
        self.calls.append((task_id, project_id, test_commands))
        return self.result


class FakeMergeService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def merge(self, task_id, project_id):
        self.calls.append((task_id, project_id))
        return self.result


def test_create_task_and_request_start_cria_approval_sem_executar_adapter(tmp_path):
    service = FakeExecutionService({"status": "should_not_run"})
    facade = ExecutionFacade(execution_service=service, repository_path=tmp_path)

    out = facade.create_task_and_request_start(objective="programar x", project_id=CORE)

    task = repo.execution_tasks.get(out["task_id"], CORE)
    assert out["status"] == et.PENDING_APPROVAL
    assert out["approval_id"]
    assert task["status"] == et.PENDING_APPROVAL
    assert service.calls == []
    assert "repository_path" not in out
    assert "worktree_path" not in out


def test_project_id_errado_nao_le_task_de_outro_projeto(tmp_path):
    facade = ExecutionFacade(repository_path=tmp_path)
    out = facade.create_task(objective="programar x", project_id=CORE)

    blocked = facade.get_task(out["task_id"], JAMPA)

    assert blocked["status"] == "blocked"
    assert blocked["reason"] == "project_scope_mismatch"


def test_start_com_flag_false_bloqueia_sem_adapter(tmp_path):
    service = FakeExecutionService({"status": "blocked", "reason": "supervised_execution_disabled"})
    facade = ExecutionFacade(execution_service=service, repository_path=tmp_path)
    out = facade.create_task(objective="programar x", project_id=CORE)
    repo.execution_tasks.set_approval(out["task_id"], CORE, 123)
    repo.execution_tasks.update_status(out["task_id"], CORE, et.APPROVED)

    result = facade.start_execution(out["task_id"], CORE, [["python", "-m", "pytest", "-q", "tests/test_x.py"]])

    assert result["reason"] == "supervised_execution_disabled"
    assert service.calls == [(out["task_id"], CORE, [["python", "-m", "pytest", "-q", "tests/test_x.py"]])]


def test_merge_sem_segundo_approval_bloqueia(tmp_path):
    merge = FakeMergeService({"status": "blocked", "reason": "merge_approval_id_required"})
    facade = ExecutionFacade(merge_service=merge, repository_path=tmp_path)
    out = facade.create_task(objective="programar x", project_id=CORE)

    result = facade.perform_merge(out["task_id"], CORE)

    assert result["status"] == "blocked"
    assert merge.calls == [(out["task_id"], CORE)]


def test_cancelamento_nao_apaga_evidencia(tmp_path):
    facade = ExecutionFacade(repository_path=tmp_path)
    out = facade.create_task(objective="programar x", project_id=CORE)

    result = facade.cancel_task(out["task_id"], CORE)

    assert result["status"] == et.CANCELED
    assert repo.execution_tasks.get(out["task_id"], CORE)["status"] == et.CANCELED
