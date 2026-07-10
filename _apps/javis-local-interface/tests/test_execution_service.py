from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution import process_utils  # noqa: E402
from execution.execution_service import ExecutionService  # noqa: E402
from execution.test_runner import TestRunReport  # noqa: E402


CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


class FakeWorktreeManager:
    def __init__(self, root: Path):
        self.root = root
        self.created = False

    def create(self, task_id, repository_path, source_branch, project_id=None):
        self.created = True
        wt = self.root / task_id
        wt.mkdir(parents=True, exist_ok=True)
        (wt / ".git").write_text("gitdir: fake", encoding="utf-8")
        return {
            "task_id": task_id,
            "project_id": project_id,
            "repository_path": repository_path,
            "source_branch": source_branch,
            "work_branch": et.branch_for(task_id),
            "worktree_path": str(wt),
        }


class FakeAdapter:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def run(self, request):
        self.requests.append(request)
        return self.result


class FakeTestRunner:
    def __init__(self, report):
        self.report = report
        self.calls = []

    def run(self, commands, worktree_path):
        self.calls.append((commands, worktree_path))
        return self.report


class FakeCollector:
    def __init__(self):
        self.calls = []

    def collect(self, task_id, project_id, worktree_path, stdout="", stderr="", test_report=""):
        self.calls.append((task_id, project_id, worktree_path, stdout, stderr, test_report))
        return {"result_path": "fake"}


def _proc(status="success", exit_code=0, timed_out=False):
    return process_utils.ProcessResult(exit_code, status, "out", "err", timed_out, 1, "cmd")


def _report(ok=True, status="success"):
    return TestRunReport(status, ok, [_proc(status=status, exit_code=0 if ok else 1)], "tests")


def _task(status=et.APPROVED, project_id=CORE, approval_id=123, executor="codex"):
    tid = et.new_task_id()
    repo.execution_tasks.create(
        task_id=tid,
        project_id=project_id,
        executor=executor,
        objective="objective",
        repository_path="/repo",
        source_branch="master",
        work_branch=et.branch_for(tid),
        worktree_path="",
        status=status,
        approval_id=approval_id,
    )
    return tid


def _service(tmp_path, *, enabled=True, adapter_result=None, test_report=None, collector=None):
    collector = collector or FakeCollector()
    return ExecutionService(
        worktree_manager=FakeWorktreeManager(tmp_path / "worktrees"),
        result_collector=collector,
        test_runner=FakeTestRunner(test_report or _report()),
        adapters={"codex": FakeAdapter(adapter_result or _proc()), "claude": FakeAdapter(adapter_result or _proc())},
        enabled=enabled,
    ), collector


def test_flag_false_impede_execucao_real(tmp_path):
    tid = _task()
    service, _ = _service(tmp_path, enabled=False)
    result = service.run(tid, CORE, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    assert result == {"status": "blocked", "reason": "supervised_execution_disabled"}
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.APPROVED


def test_tarefa_sem_approved_bloqueada(tmp_path):
    tid = _task(status=et.PENDING_APPROVAL)
    service, _ = _service(tmp_path)
    result = service.run(tid, CORE, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    assert result["status"] == "blocked"
    assert result["reason"] == "task_not_approved"


def test_project_id_errado_recusado(tmp_path):
    tid = _task(project_id=CORE)
    service, _ = _service(tmp_path)
    result = service.run(tid, JAMPA, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    assert result["status"] == "blocked"
    assert result["reason"] == "project_scope_mismatch"


def test_sucesso_percorre_ate_awaiting_review(tmp_path):
    tid = _task()
    service, collector = _service(tmp_path)
    result = service.run(tid, CORE, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    assert result["status"] == et.AWAITING_REVIEW
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.AWAITING_REVIEW
    assert collector.calls


def test_erro_do_adapter_vira_failed_e_preserva_worktree(tmp_path):
    tid = _task()
    service, collector = _service(tmp_path, adapter_result=_proc(status="failed", exit_code=1))
    result = service.run(tid, CORE, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    task = repo.execution_tasks.get(tid, CORE)
    assert result["status"] == et.FAILED
    assert task["status"] == et.FAILED
    assert Path(task["worktree_path"]).exists()
    assert collector.calls


def test_timeout_do_adapter_vira_timed_out(tmp_path):
    tid = _task()
    service, _ = _service(tmp_path, adapter_result=_proc(status="timed_out", exit_code=-9, timed_out=True))
    result = service.run(tid, CORE, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    assert result["status"] == et.TIMED_OUT
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.TIMED_OUT


def test_testes_falhando_impedem_awaiting_review(tmp_path):
    tid = _task()
    service, collector = _service(tmp_path, test_report=_report(ok=False, status="failed"))
    result = service.run(tid, CORE, test_commands=[["python", "-m", "pytest", "-q", "tests/test_x.py"]])
    assert result["status"] == et.FAILED
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.FAILED
    assert collector.calls
