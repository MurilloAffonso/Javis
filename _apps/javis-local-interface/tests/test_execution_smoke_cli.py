from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"
SCRIPTS = ROOT / "scripts"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import db  # noqa: E402
import repositories as repo  # noqa: E402
import javes_execution_smoke as smoke  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution.execution_facade import ExecutionFacade  # noqa: E402
from execution.result_collector import ResultCollector  # noqa: E402

CORE = "javes-core"


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.delenv("JAVIS_ENABLE_SUPERVISED_EXEC", raising=False)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    (tmp_path / "_estado").mkdir(parents=True)
    (tmp_path / "_estado" / "CURRENT_STATE.md").write_text("# state", encoding="utf-8")
    db._initialized = False
    db.init_db()


def _out(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def _temp_repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init"], cwd=path, shell=False, check=True, capture_output=True)
    return path


class FakeExecutionService:
    def __init__(self, tmp_path: Path, collector: ResultCollector):
        self.tmp_path = tmp_path
        self.collector = collector
        self.calls = []
        self.push_or_merge_called = False

    def run(self, task_id, project_id, *, test_commands):
        self.calls.append((task_id, project_id, test_commands))
        worktree = self.tmp_path / "fake-worktree" / task_id
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: fake", encoding="utf-8")
        repo.execution_tasks.set_workspace(
            task_id,
            project_id,
            work_branch=et.branch_for(task_id),
            worktree_path=str(worktree),
            source_commit="fake-source",
        )
        result_dir = self.collector.results_dir_for(task_id)
        result_dir.mkdir(parents=True)
        result_path = result_dir / "result.json"
        diff_path = result_dir / "diff.patch"
        tests_path = result_dir / "tests.txt"
        result_path.write_text(json.dumps({
            "changed_count": 1,
            "diff_stat": f"{smoke.ROOT}\\secret\\path token=sk-secret123456",
            "diff_truncated": False,
            "collected_at": "2026-07-10T00:00:00",
        }), encoding="utf-8")
        diff_path.write_text("diff --git a/docs/EXECUTION_SMOKE_TEST.md b/docs/EXECUTION_SMOKE_TEST.md", encoding="utf-8")
        tests_path.write_text("ok", encoding="utf-8")
        repo.execution_tasks.set_result_paths(
            task_id,
            project_id,
            result_path=str(result_path),
            diff_path=str(diff_path),
            test_report_path=str(tests_path),
        )
        repo.execution_tasks.update_status(task_id, project_id, et.AWAITING_REVIEW)
        return {"status": et.AWAITING_REVIEW, "reason": "", "task_id": task_id}


def _facade(tmp_path: Path, repo_path: Path, service=None) -> ExecutionFacade:
    collector = ResultCollector(results_root=tmp_path / "results")
    return ExecutionFacade(
        repository_path=repo_path,
        execution_service=service or FakeExecutionService(tmp_path, collector),
        result_collector=collector,
    )


def _prepare(monkeypatch, tmp_path, capsys, executor="claude"):
    repo_path = _temp_repo(tmp_path)
    facade = _facade(tmp_path, repo_path)
    monkeypatch.setattr(smoke, "make_facade", lambda: facade)
    code = smoke.main(["prepare", "--executor", executor])
    assert code == 0
    return _out(capsys), facade


def _approve(monkeypatch, tmp_path, capsys):
    prepared, facade = _prepare(monkeypatch, tmp_path, capsys)
    code = smoke.main([
        "approve-start",
        "--task-id", prepared["task_id"],
        "--approval-id", str(prepared["approval_id"]),
        "--confirm", smoke.APPROVE_PHRASE,
    ])
    assert code == 0
    _out(capsys)
    return prepared, facade


def test_prepare_cria_task_e_approval_sem_executar(monkeypatch, tmp_path, capsys):
    prepared, facade = _prepare(monkeypatch, tmp_path, capsys)

    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    assert task["status"] == et.PENDING_APPROVAL
    assert prepared["approval_id"]
    assert facade.execution_service.calls == []


def test_project_id_diferente_recusado(monkeypatch, tmp_path, capsys):
    repo_path = _temp_repo(tmp_path)
    monkeypatch.setattr(smoke, "make_facade", lambda: _facade(tmp_path, repo_path))

    code = smoke.main(["prepare", "--executor", "claude", "--project-id", "project:cerebro-jampa"])

    assert code == 2
    assert _out(capsys)["reason"] == "project_id_not_allowed"


def test_objetivo_nao_pode_ser_alterado():
    with pytest.raises(SystemExit):
        smoke.main(["prepare", "--executor", "claude", "--objective", "malicioso"])


def test_approve_exige_frase_exata(monkeypatch, tmp_path, capsys):
    prepared, _ = _prepare(monkeypatch, tmp_path, capsys)

    code = smoke.main([
        "approve-start",
        "--task-id", prepared["task_id"],
        "--approval-id", str(prepared["approval_id"]),
        "--confirm", "sim",
    ])

    assert code == 2
    assert _out(capsys)["reason"] == "confirmation_phrase_required"


def test_run_exige_frase_exata(monkeypatch, tmp_path, capsys):
    prepared, _ = _approve(monkeypatch, tmp_path, capsys)

    code = smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", "sim"])

    assert code == 2
    assert _out(capsys)["reason"] == "confirmation_phrase_required"


def test_run_com_flag_false_bloqueia(monkeypatch, tmp_path, capsys):
    prepared, _ = _approve(monkeypatch, tmp_path, capsys)

    code = smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", smoke.RUN_PHRASE])

    assert code == 2
    assert _out(capsys)["reason"] == "supervised_execution_disabled"


def test_task_sem_approval_bloqueia(monkeypatch, tmp_path, capsys):
    repo_path = _temp_repo(tmp_path)
    facade = _facade(tmp_path, repo_path)
    monkeypatch.setattr(smoke, "make_facade", lambda: facade)
    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "1")
    monkeypatch.setattr(smoke, "_repo_clean", lambda path: "")
    monkeypatch.setattr(smoke, "_executor_available", lambda executor: "")
    tid = et.new_task_id()
    repo.execution_tasks.create(
        task_id=tid,
        project_id=CORE,
        executor="claude",
        objective=smoke.SMOKE_OBJECTIVE,
        repository_path=str(repo_path),
        source_branch="master",
        work_branch=et.branch_for(tid),
        worktree_path="",
        status=et.APPROVED,
        timeout_seconds=300,
    )

    code = smoke.main(["run", "--task-id", tid, "--confirm", smoke.RUN_PHRASE])

    assert code == 2
    assert _out(capsys)["reason"] == "approval_not_consumed"


def test_task_ja_executada_bloqueia(monkeypatch, tmp_path, capsys):
    prepared, _ = _approve(monkeypatch, tmp_path, capsys)
    repo.execution_tasks.update_status(prepared["task_id"], CORE, et.AWAITING_REVIEW)
    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "1")

    code = smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", smoke.RUN_PHRASE])

    assert code == 2
    assert _out(capsys)["reason"] == "task_already_executed"


def test_execucao_fake_termina_awaiting_review(monkeypatch, tmp_path, capsys):
    prepared, facade = _approve(monkeypatch, tmp_path, capsys)
    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "1")
    monkeypatch.setattr(smoke, "_repo_clean", lambda path: "")
    monkeypatch.setattr(smoke, "_executor_available", lambda executor: "")

    code = smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", smoke.RUN_PHRASE])
    body = _out(capsys)

    assert code == 0
    assert body["status"] == et.AWAITING_REVIEW
    assert facade.execution_service.calls
    assert repo.execution_tasks.get(prepared["task_id"], CORE)["status"] == et.AWAITING_REVIEW


def test_nenhum_merge_ou_push_e_chamado(monkeypatch, tmp_path, capsys):
    prepared, _ = _approve(monkeypatch, tmp_path, capsys)
    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "1")
    monkeypatch.setattr(smoke, "_executor_available", lambda executor: "")
    calls = []

    def fake_git(args, cwd):
        calls.append(args)
        return subprocess.CompletedProcess(["git", *args], 0, stdout=".git", stderr="")

    monkeypatch.setattr(smoke, "_git", fake_git)
    smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", smoke.RUN_PHRASE])
    _out(capsys)

    assert not any("push" in args or "merge" in args for args in calls)


def test_worktree_preservada_e_status_sanitizado(monkeypatch, tmp_path, capsys):
    prepared, _ = _approve(monkeypatch, tmp_path, capsys)
    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "1")
    monkeypatch.setattr(smoke, "_repo_clean", lambda path: "")
    monkeypatch.setattr(smoke, "_executor_available", lambda executor: "")
    smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", smoke.RUN_PHRASE])
    _out(capsys)

    code = smoke.main(["status", "--task-id", prepared["task_id"]])
    raw = capsys.readouterr().out
    body = json.loads(raw)

    assert code == 0
    assert body["worktree_preservada"] is True
    assert body["changed_files_count"] == 1
    assert "sk-secret" not in raw
    assert str(smoke.ROOT) not in raw
    assert "fake-worktree" not in raw


def test_codex_sem_sandbox_falha_fechado(monkeypatch, tmp_path, capsys):
    prepared, _ = _approve(monkeypatch, tmp_path, capsys)
    repo.execution_tasks.update_status(prepared["task_id"], CORE, et.APPROVED)
    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "1")
    monkeypatch.setattr(smoke, "_repo_clean", lambda path: "")
    monkeypatch.setattr(smoke, "_executor_available", lambda executor: "secure_codex_sandbox_unavailable")

    code = smoke.main(["run", "--task-id", prepared["task_id"], "--confirm", smoke.RUN_PHRASE])

    assert code == 2
    assert _out(capsys)["reason"] == "secure_codex_sandbox_unavailable"


def _review_task(tmp_path: Path, *, status: str = et.AWAITING_REVIEW, project_id: str = CORE) -> tuple[str, Path]:
    tid = et.new_task_id()
    worktree = tmp_path / "worktree" / tid
    result_dir = tmp_path / "results" / tid
    worktree.mkdir(parents=True)
    result_dir.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: fake", encoding="utf-8")
    (worktree / "docs").mkdir()
    (worktree / "docs" / "EXECUTION_SMOKE_TEST.md").write_text("# smoke\n", encoding="utf-8")
    result_path = result_dir / "result.json"
    diff_path = result_dir / "diff.patch"
    tests_path = result_dir / "tests.txt"
    result_path.write_text(json.dumps({"changed_count": 1}), encoding="utf-8")
    diff_path.write_text("diff", encoding="utf-8")
    tests_path.write_text("ok", encoding="utf-8")
    repo.execution_tasks.create(
        task_id=tid,
        project_id=project_id,
        executor="claude",
        objective=smoke.SMOKE_OBJECTIVE,
        repository_path=str(tmp_path / "repo"),
        source_branch="master",
        work_branch=et.branch_for(tid),
        worktree_path=str(worktree),
        status=status,
        timeout_seconds=300,
        source_commit="abc",
    )
    repo.execution_tasks.set_result_paths(
        tid,
        project_id,
        result_path=str(result_path),
        diff_path=str(diff_path),
        test_report_path=str(tests_path),
    )
    return tid, worktree


def test_reject_exige_frase_exata(tmp_path, capsys):
    tid, _ = _review_task(tmp_path)

    code = smoke.main(["reject", "--task-id", tid, "--confirm", "rejeitar"])

    assert code == 2
    assert _out(capsys)["reason"] == "confirmation_phrase_required"
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.AWAITING_REVIEW


def test_reject_task_inexistente_bloqueia(capsys):
    code = smoke.main(["reject", "--task-id", "exec_deadbeef", "--confirm", smoke.REJECT_PHRASE])

    assert code == 2
    assert _out(capsys)["reason"] == "task_not_found"


def test_reject_status_errado_bloqueia(tmp_path, capsys):
    tid, worktree = _review_task(tmp_path, status=et.APPROVED)

    code = smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE])

    assert code == 2
    assert _out(capsys)["reason"] == "task_not_awaiting_review"
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.APPROVED
    assert worktree.exists()


def test_reject_transiciona_para_review_rejected_e_preserva_evidencias(tmp_path, capsys):
    tid, worktree = _review_task(tmp_path)
    before_files = sorted(path.relative_to(worktree).as_posix() for path in worktree.rglob("*"))

    code = smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE])
    body = _out(capsys)
    task = repo.execution_tasks.get(tid, CORE)
    events = repo.task_events.list_by_task(tid)
    after_files = sorted(path.relative_to(worktree).as_posix() for path in worktree.rglob("*"))

    assert code == 0
    assert body["status"] == et.REVIEW_REJECTED
    assert body["evidence_preserved"] is True
    assert task["status"] == et.REVIEW_REJECTED
    assert task["result_path"] and Path(task["result_path"]).exists()
    assert task["diff_path"] and Path(task["diff_path"]).exists()
    assert task["test_report_path"] and Path(task["test_report_path"]).exists()
    assert worktree.exists()
    assert before_files == after_files
    assert any(event["event_type"] == "smoke_review_rejected" for event in events)


def test_reject_nao_faz_merge_push_ou_execucao(monkeypatch, tmp_path, capsys):
    tid, _ = _review_task(tmp_path)
    blocked_facade = object()
    monkeypatch.setattr(smoke, "make_facade", lambda: blocked_facade)
    monkeypatch.setattr(smoke, "_git", lambda *args, **kwargs: pytest.fail("git nao deveria ser chamado"))

    code = smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE])

    assert code == 0
    assert _out(capsys)["merge"] == "not_requested"


# ── R4.3B3 — estados terminais do smoke ────────────────────────────────────

def _status_facade(monkeypatch, tmp_path):
    """Facade de status apontando para o results_root temporário do teste."""
    collector = ResultCollector(results_root=tmp_path / "results")
    facade = ExecutionFacade(
        repository_path=tmp_path / "repo",
        execution_service=FakeExecutionService(tmp_path, collector),
        result_collector=collector,
    )
    monkeypatch.setattr(smoke, "make_facade", lambda: facade)
    return facade


def _prepare_facade(monkeypatch, tmp_path):
    """Facade para prepare criar uma NOVA task smoke sem agente real."""
    repo_path = _temp_repo(tmp_path)
    facade = _facade(tmp_path, repo_path)
    monkeypatch.setattr(smoke, "make_facade", lambda: facade)
    return facade


# Correção 1 — reject coerente e idempotente

def test_reject_em_awaiting_review_retorna_review_rejected_e_estado_coincide(tmp_path, capsys):
    tid, _ = _review_task(tmp_path)

    code = smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE])
    body = _out(capsys)

    assert code == 0
    assert body["status"] == et.REVIEW_REJECTED
    assert body["worktree_preservada"] is True
    # estado persistido coincide com a resposta
    assert repo.execution_tasks.get(tid, CORE)["status"] == body["status"]


def test_segundo_reject_idempotente_nao_duplica_evento(tmp_path, capsys):
    tid, _ = _review_task(tmp_path)

    assert smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE]) == 0
    _out(capsys)
    eventos_1 = [e for e in repo.task_events.list_by_task(tid)
                 if e["event_type"] == "smoke_review_rejected"]

    code = smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE])
    body = _out(capsys)
    eventos_2 = [e for e in repo.task_events.list_by_task(tid)
                 if e["event_type"] == "smoke_review_rejected"]

    assert code == 0
    assert body["status"] == et.REVIEW_REJECTED
    assert body["reason"] == "already_rejected"
    assert body["worktree_preservada"] is True
    assert len(eventos_1) == 1
    assert len(eventos_2) == 1  # segundo reject não duplica evento
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.REVIEW_REJECTED


# Correção 2 — active_smoke_exists só para estados em andamento

@pytest.mark.parametrize("terminal", [
    et.REVIEW_REJECTED, et.FAILED, et.TIMED_OUT, et.CANCELED, et.COMPLETED,
])
def test_estado_terminal_nao_bloqueia_novo_prepare(monkeypatch, tmp_path, capsys, terminal):
    old_tid, old_worktree = _review_task(tmp_path, status=terminal)
    _prepare_facade(monkeypatch, tmp_path)

    code = smoke.main(["prepare", "--executor", "claude"])
    body = _out(capsys)

    assert code == 0
    assert body["project_id"] == CORE
    assert body.get("task_id") and body["task_id"] != old_tid
    # a task terminal antiga permanece intocada
    old = repo.execution_tasks.get(old_tid, CORE)
    assert old["status"] == terminal
    assert old_worktree.exists()


@pytest.mark.parametrize("active", [
    et.PENDING_APPROVAL, et.RUNNING, et.AWAITING_REVIEW,
])
def test_estado_em_andamento_bloqueia_novo_prepare(monkeypatch, tmp_path, capsys, active):
    _review_task(tmp_path, status=active)
    _prepare_facade(monkeypatch, tmp_path)

    code = smoke.main(["prepare", "--executor", "claude"])

    assert code == 2
    assert _out(capsys)["reason"] == "active_smoke_exists"


def test_active_query_escopada_por_javes_core(monkeypatch, tmp_path, capsys):
    # task ativa em OUTRO project_id não pode bloquear smoke de javes-core
    _review_task(tmp_path, status=et.AWAITING_REVIEW, project_id="project:cerebro-jampa")
    _prepare_facade(monkeypatch, tmp_path)

    code = smoke.main(["prepare", "--executor", "claude"])
    body = _out(capsys)

    assert code == 0
    assert body["project_id"] == CORE


# Correção 3 — reject preserva e apresenta o resultado dos testes

def test_reject_preserva_tests_passed_e_evidencias_no_status(monkeypatch, tmp_path, capsys):
    tid, worktree = _review_task(tmp_path)
    _status_facade(monkeypatch, tmp_path)

    smoke.main(["status", "--task-id", tid])
    antes = _out(capsys)
    assert antes["tests"] == "passed"

    before_paths = {
        k: repo.execution_tasks.get(tid, CORE)[k]
        for k in ("result_path", "diff_path", "test_report_path")
    }

    assert smoke.main(["reject", "--task-id", tid, "--confirm", smoke.REJECT_PHRASE]) == 0
    _out(capsys)

    smoke.main(["status", "--task-id", tid])
    depois = _out(capsys)

    assert depois["status"] == et.REVIEW_REJECTED
    assert depois["tests"] == "passed"  # não virou not_run
    assert depois["changed_files_count"] == 1
    assert depois["resultado_sanitizado"]["collected_at"] == antes["resultado_sanitizado"]["collected_at"]
    assert depois["evidencias_preservadas"] == {
        "result_path": True, "diff_path": True, "test_report_path": True,
    }
    assert depois["worktree_preservada"] is True
    # paths de resultado não foram alterados nem apagados pelo reject
    after_paths = {
        k: repo.execution_tasks.get(tid, CORE)[k]
        for k in ("result_path", "diff_path", "test_report_path")
    }
    assert before_paths == after_paths
    for value in after_paths.values():
        assert value and Path(value).exists()
    assert worktree.exists()


def test_status_failed_deriva_tests_failed(monkeypatch, tmp_path, capsys):
    tid, _ = _review_task(tmp_path, status=et.FAILED)
    _status_facade(monkeypatch, tmp_path)

    smoke.main(["status", "--task-id", tid])
    body = _out(capsys)

    assert body["tests"] == "failed"
