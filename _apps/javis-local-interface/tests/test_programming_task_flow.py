"""R4.4B1 — fluxo real exercitado somente em Git/SQLite/worktrees temporários."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"
SCRIPTS = ROOT / "scripts"
for entry in (BACKEND, SCRIPTS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import db  # noqa: E402
import javes_execution_smoke as smoke  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution._gitcmd import clean_git_env, run_git  # noqa: E402
from execution.process_utils import ProcessResult  # noqa: E402
from execution.programming_task_admission import prepare_file  # noqa: E402
from execution.programming_task_flow import (  # noqa: E402
    APPROVE_MERGE_PHRASE,
    APPROVE_START_PHRASE,
    MERGE_PHRASE,
    REJECT_MERGE_PHRASE,
    REJECT_PHRASE,
    RUN_PHRASE,
    ProgrammingTaskFlow,
)
from execution.programming_task_policy import (  # noqa: E402
    PolicyViolation,
    ProfileReport,
    ProgrammingChangePolicy,
    ProgrammingTestProfiles,
)
from execution.project_execution_registry import ProjectExecutionRegistry  # noqa: E402
from execution.result_collector import ResultCollector  # noqa: E402
from execution.worktree_manager import WorktreeManager  # noqa: E402


CORE = "javes-core"


def _git(path: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=path, shell=False, env=clean_git_env(), check=check,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _init_repo(path: Path) -> None:
    path.mkdir()
    _git(path, "init", "-b", "master")
    _git(path, "config", "user.email", "tests@javes.local")
    _git(path, "config", "user.name", "Javes Tests")
    (path / "docs").mkdir()
    (path / "docs" / "base.md").write_text("# Base\n", encoding="utf-8")
    (path / "README.md").write_text("# Repo\n", encoding="utf-8")
    _git(path, "add", "--", "docs/base.md", "README.md")
    _git(path, "commit", "-m", "initial")


def _spec(**overrides) -> dict:
    data = {
        "schema_version": 1,
        "project_id": CORE,
        "title": "Atualiza documentação controlada",
        "objective": "Adicionar documentação pequena pelo fluxo supervisionado.",
        "executor": "claude",
        "allowed_paths": ["docs/"],
        "test_profile": "docs_only",
        "limits": {"max_duration_seconds": 300, "max_changed_files": 5,
                   "max_diff_lines": 300},
    }
    for key, value in overrides.items():
        if key.startswith("limit_"):
            data["limits"][key.removeprefix("limit_")] = value
        else:
            data[key] = value
    return data


class FakeAdapter:
    def __init__(self, edit=None, *, result: ProcessResult | None = None):
        self.edit = edit or (lambda worktree: None)
        self.requests = []
        self.result = result or ProcessResult(0, "success", "ok", "", False, 5, "fake")

    def run(self, request):
        self.requests.append(request)
        self.edit(Path(request.worktree_path))
        return self.result


class FailedProfiles:
    def run(self, *args, **kwargs):
        return ProfileReport("failed", False, "falha controlada", 1)


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.delenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", raising=False)
    monkeypatch.delenv("JAVIS_ENABLE_SUPERVISED_EXEC", raising=False)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()
    main = tmp_path / "repo"
    _init_repo(main)
    registry = ProjectExecutionRegistry(main)
    manager = WorktreeManager(allowed_repo_roots=[main],
                              worktree_root=tmp_path / "worktrees")
    collector = ResultCollector(results_root=tmp_path / "results")
    return {"tmp": tmp_path, "main": main, "registry": registry,
            "manager": manager, "collector": collector, "monkeypatch": monkeypatch}


def _write_spec(env, data=None, name="spec.json") -> Path:
    path = env["tmp"] / name
    path.write_text(json.dumps(data or _spec(), ensure_ascii=False), encoding="utf-8")
    return path


def _flow(env, adapter=None, **kwargs) -> ProgrammingTaskFlow:
    adapter = adapter or FakeAdapter(lambda wt: (wt / "docs" / "real.md").write_text(
        "# Real\n", encoding="utf-8"))
    return ProgrammingTaskFlow(
        registry=env["registry"], worktree_manager=env["manager"],
        result_collector=env["collector"], adapters={"claude": adapter, "codex": adapter},
        **kwargs,
    )


def _prepare(env, data=None):
    env["monkeypatch"].setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    return prepare_file(_write_spec(env, data), registry=env["registry"])


def _approve(env, flow, data=None):
    prepared = _prepare(env, data)
    approved = flow.approve_start(prepared["task_id"], prepared["approval_id"],
                                  APPROVE_START_PHRASE)
    assert approved["status"] == et.APPROVED
    return prepared


def _run_success(env, flow, data=None):
    prepared = _approve(env, flow, data)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    result = flow.run(prepared["task_id"], RUN_PHRASE)
    assert result["status"] == et.AWAITING_REVIEW, result
    return prepared


def test_approve_start_exige_flag_e_run_exige_ambas(env):
    prepared = _prepare(env)
    flow = _flow(env)
    env["monkeypatch"].delenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS")
    assert flow.approve_start(prepared["task_id"], prepared["approval_id"],
                              APPROVE_START_PHRASE)["reason"] == "real_programming_tasks_disabled"
    env["monkeypatch"].setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    assert flow.approve_start(prepared["task_id"], prepared["approval_id"],
                              APPROVE_START_PHRASE)["status"] == et.APPROVED
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "supervised_execution_disabled"


def test_approve_start_exige_frase_exata_e_consumo_e_atomico(env):
    prepared = _prepare(env)
    flow = _flow(env)
    assert flow.approve_start(prepared["task_id"], prepared["approval_id"], "quase")["reason"] == "confirmation_phrase_required"
    assert repo.approvals.get(prepared["approval_id"])["status"] == "pending"
    out = flow.approve_start(prepared["task_id"], prepared["approval_id"], APPROVE_START_PHRASE)
    assert out["status"] == et.APPROVED
    approval = repo.approvals.get(prepared["approval_id"])
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    assert approval["status"] == "approved" and approval["consumed_at"]
    assert task["status"] == et.APPROVED and task["approval_id"] == prepared["approval_id"]


def test_approval_outro_hash_e_snapshot_ausente_ou_modificado_bloqueiam(env):
    flow = _flow(env)
    prepared = _prepare(env)
    db.execute("UPDATE approvals SET spec_hash='falso' WHERE id=?", (prepared["approval_id"],))
    assert flow.approve_start(prepared["task_id"], prepared["approval_id"],
                              APPROVE_START_PHRASE)["reason"] == "spec_hash_mismatch"
    db.execute("DROP TRIGGER execution_task_specs_no_delete")
    db.execute("DELETE FROM execution_task_specs WHERE task_id=?", (prepared["task_id"],))
    assert flow.approve_start(prepared["task_id"], prepared["approval_id"],
                              APPROVE_START_PHRASE)["reason"] == "spec_not_found"


def test_snapshot_modificado_bloqueia_por_hash(env):
    flow = _flow(env)
    prepared = _prepare(env)
    db.execute("DROP TRIGGER execution_task_specs_no_update")
    db.execute("UPDATE execution_task_specs SET snapshot_json='{}' WHERE task_id=?",
               (prepared["task_id"],))
    assert flow.approve_start(prepared["task_id"], prepared["approval_id"],
                              APPROVE_START_PHRASE)["reason"] == "spec_hash_mismatch"


def test_run_so_cria_worktree_depois_da_aprovacao(env):
    prepared = _prepare(env)
    flow = _flow(env)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "invalid_state"
    assert not env["manager"].validate_existing(prepared["task_id"])["exists"]


def test_repo_e_executor_vem_do_registro_e_snapshot(env):
    adapter = FakeAdapter(lambda wt: (wt / "docs" / "ok.md").write_text("ok\n", encoding="utf-8"))
    flow = _flow(env, adapter)
    prepared = _run_success(env, flow)
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    assert Path(task["repository_path"]).resolve() == env["main"].resolve()
    assert adapter.requests[0].executor == "claude"
    assert "APROVAR" not in adapter.requests[0].objective


def test_prompt_interno_contem_guardrails_sem_approval_ou_paths_absolutos(env):
    adapter = FakeAdapter(lambda wt: (wt / "docs" / "prompt.md").write_text("ok\n", encoding="utf-8"))
    flow = _flow(env, adapter)
    prepared = _run_success(env, flow)
    prompt = adapter.requests[0].objective
    for text in ("não use rede", "caminhos permitidos", ".env", "credenciais",
                 "push", "merge", "rebase", "reset", "git add .", "git add -A"):
        assert text.lower() in prompt.lower()
    assert str(env["tmp"]) not in prompt and str(prepared["approval_id"]) not in prompt


@pytest.mark.parametrize("edit,reason", [
    (lambda wt: (wt / "README.md").write_text("fora\n", encoding="utf-8"),
     "path_policy_violation"),
    (lambda wt: (wt / "docs" / ".env").write_text("x\n", encoding="utf-8"),
     "sensitive_path_violation"),
])
def test_path_fora_e_arquivo_sensivel_bloqueiam_sem_commit(env, edit, reason):
    flow = _flow(env, FakeAdapter(edit))
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    out = flow.run(prepared["task_id"], RUN_PHRASE)
    assert out["reason"] == reason
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    rc, head, _ = run_git(Path(task["worktree_path"]), ["rev-parse", "HEAD"])
    assert rc == 0 and head.strip() == task["source_commit"]


def test_rename_para_fora_bloqueia(env):
    def edit(wt):
        (wt / "docs" / "base.md").rename(wt / "moved.md")
    flow = _flow(env, FakeAdapter(edit))
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "path_policy_violation"


def test_rename_vindo_de_fora_bloqueia(env):
    def edit(wt):
        (wt / "README.md").rename(wt / "docs" / "readme.md")
    flow = _flow(env, FakeAdapter(edit))
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "path_policy_violation"


def test_symlink_bloqueia(env):
    def edit(wt):
        try:
            (wt / "docs" / "link.md").symlink_to(wt / "README.md")
        except OSError:
            pytest.skip("symlink indisponível")
    flow = _flow(env, FakeAdapter(edit))
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "symlink_not_allowed"


def test_submodule_bloqueia(env):
    def edit(wt):
        head = _git(wt, "rev-parse", "HEAD").stdout.strip()
        _git(wt, "update-index", "--add", "--cacheinfo", f"160000,{head},docs/sub")
    flow = _flow(env, FakeAdapter(edit))
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "submodule_not_allowed"


def test_max_changed_files_e_diff_lines_bloqueiam(env):
    def two_files(wt):
        (wt / "docs" / "one.md").write_text("1\n", encoding="utf-8")
        (wt / "docs" / "two.md").write_text("2\n", encoding="utf-8")
    flow = _flow(env, FakeAdapter(two_files))
    prepared = _approve(env, flow, _spec(limit_max_changed_files=1))
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "max_changed_files_exceeded"

    # Nova fixture lógica no mesmo repo: encerra a task anterior para liberar admissão.
    repo.execution_tasks.update_status(prepared["task_id"], CORE, et.FAILED)
    flow2 = _flow(env, FakeAdapter(lambda wt: (wt / "docs" / "long.md").write_text(
        "a\nb\nc\n", encoding="utf-8")))
    prepared2 = _approve(env, flow2, _spec(limit_max_diff_lines=2))
    assert flow2.run(prepared2["task_id"], RUN_PHRASE)["reason"] == "max_diff_lines_exceeded"


def test_max_duration_e_testes_falhos_bloqueiam(env):
    ticks = iter([0.0, 301.0])
    flow = _flow(env, monotonic=lambda: next(ticks))
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "max_duration_exceeded"
    repo.execution_tasks.update_status(prepared["task_id"], CORE, et.FAILED)

    flow2 = _flow(env, test_profiles=FailedProfiles())
    prepared2 = _approve(env, flow2)
    assert flow2.run(prepared2["task_id"], RUN_PHRASE)["reason"] == "tests_failed"


def test_commit_lista_explicita_e_nunca_add_amplo(env):
    calls = []
    def logging_git(cwd, args, timeout=30):
        calls.append(tuple(args))
        return run_git(cwd, args, timeout=timeout)
    policy = ProgrammingChangePolicy(git_runner=logging_git)
    flow = _flow(env, change_policy=policy)
    _run_success(env, flow)
    add_calls = [args for args in calls if args and args[0] == "add"]
    assert add_calls and add_calls[-1][:2] == ("add", "--")
    assert all("." not in args and "-A" not in args and "--all" not in args for args in add_calls)
    assert not any(args and args[0] == "push" for args in calls)


def test_no_new_commit_bloqueia(env):
    flow = _flow(env, FakeAdapter())
    prepared = _approve(env, flow)
    env["monkeypatch"].setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert flow.run(prepared["task_id"], RUN_PHRASE)["reason"] == "no_new_commit"


def test_status_sanitizado(env):
    flow = _flow(env)
    prepared = _run_success(env, flow)
    out = flow.status(prepared["task_id"])
    assert set(out) == {"task_id", "project_id", "executor", "status", "spec_hash",
                        "tests", "changed_files_count", "diff_stat",
                        "evidencias_presentes", "worktree_preservada"}
    rendered = json.dumps(out)
    assert str(env["tmp"]) not in rendered and "objective" not in rendered and "prompt" not in rendered


def test_request_merge_exige_testes_commit_e_worktree_limpa(env):
    flow = _flow(env)
    prepared = _run_success(env, flow)
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    tests = env["collector"].results_dir_for(prepared["task_id"]) / "tests.txt"
    tests.write_text("status=failed", encoding="utf-8")
    assert flow.request_merge(prepared["task_id"])["reason"] == "tests_failed"
    tests.write_text("status=passed", encoding="utf-8")
    (Path(task["worktree_path"]) / "docs" / "dirty.md").write_text("dirty", encoding="utf-8")
    assert flow.request_merge(prepared["task_id"])["reason"] == "dirty_worktree"


def test_approval_merge_vincula_hash_e_e_single_use(env):
    flow = _flow(env)
    prepared = _run_success(env, flow)
    requested = flow.request_merge(prepared["task_id"])
    approval = repo.approvals.get(requested["approval_id"])
    assert approval["spec_hash"] == prepared["spec_hash"] and approval["executor"] == "claude"
    assert flow.approve_merge(prepared["task_id"], requested["approval_id"],
                              APPROVE_MERGE_PHRASE)["status"] == et.APPROVED_FOR_MERGE
    assert repo.approvals.get(requested["approval_id"])["consumed_at"]
    assert flow.approve_merge(prepared["task_id"], requested["approval_id"],
                              APPROVE_MERGE_PHRASE)["reason"] == "invalid_state"


def test_merge_revalida_hash_allowlist_e_source_primeiro(env):
    flow = _flow(env)
    prepared = _run_success(env, flow)
    request = flow.request_merge(prepared["task_id"])
    flow.approve_merge(prepared["task_id"], request["approval_id"], APPROVE_MERGE_PHRASE)
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    # Move a source: deve vencer qualquer corrupção posterior de spec.
    (env["main"] / "source.txt").write_text("move\n", encoding="utf-8")
    _git(env["main"], "add", "--", "source.txt")
    _git(env["main"], "commit", "-m", "source moved")
    db.execute("DROP TRIGGER execution_task_specs_no_update")
    db.execute("UPDATE execution_task_specs SET snapshot_json='{}' WHERE task_id=?",
               (prepared["task_id"],))
    assert flow.merge(prepared["task_id"], MERGE_PHRASE)["reason"] == "source_branch_moved"


def test_merge_revalida_spec_hash_e_allowlist_com_source_estavel(env):
    flow = _flow(env)
    first = _run_success(env, flow)
    request = flow.request_merge(first["task_id"])
    flow.approve_merge(first["task_id"], request["approval_id"], APPROVE_MERGE_PHRASE)
    db.execute("DROP TRIGGER execution_task_specs_no_update")
    db.execute("UPDATE execution_task_specs SET snapshot_json='{}' WHERE task_id=?", (first["task_id"],))
    assert flow.merge(first["task_id"], MERGE_PHRASE)["reason"] == "spec_hash_mismatch"
    repo.execution_tasks.update_status(first["task_id"], CORE, et.FAILED)

    second = _run_success(env, flow)
    request2 = flow.request_merge(second["task_id"])
    flow.approve_merge(second["task_id"], request2["approval_id"], APPROVE_MERGE_PHRASE)
    task = repo.execution_tasks.get(second["task_id"], CORE)
    worktree = Path(task["worktree_path"])
    (worktree / "outside.txt").write_text("fora\n", encoding="utf-8")
    _git(worktree, "add", "--", "outside.txt")
    _git(worktree, "commit", "-m", "tamper outside allowlist")
    assert flow.merge(second["task_id"], MERGE_PHRASE)["reason"] == "path_policy_violation"


def test_merge_sucesso_sem_push_remove_so_worktree_certa(env):
    calls = []
    real_runner = subprocess.run
    def merge_runner(argv, **kwargs):
        calls.append(tuple(argv))
        return real_runner(argv, **kwargs)
    adapter = FakeAdapter(lambda wt: (wt / "docs" / "merged.md").write_text(
        "merged\n", encoding="utf-8"))
    manager = env["manager"]
    collector = env["collector"]
    from execution.merge_service import ControlledMergeService
    merge_service = ControlledMergeService(
        worktree_manager=manager, result_collector=collector, git_runner=merge_runner,
    )
    flow = ProgrammingTaskFlow(
        registry=env["registry"], worktree_manager=manager, result_collector=collector,
        adapters={"claude": adapter, "codex": adapter}, merge_service=merge_service,
    )
    prepared = _run_success(env, flow)
    unrelated = manager.worktree_root / "unrelated-evidence"
    unrelated.mkdir(parents=True)
    request = flow.request_merge(prepared["task_id"])
    flow.approve_merge(prepared["task_id"], request["approval_id"], APPROVE_MERGE_PHRASE)
    out = flow.merge(prepared["task_id"], MERGE_PHRASE)
    assert out["status"] == et.COMPLETED
    assert not manager.validate_existing(prepared["task_id"])["exists"]
    assert unrelated.exists()
    assert not any("push" in call for call in calls)
    assert (env["main"] / "docs" / "merged.md").exists()


def test_reject_e_reject_merge_preservam_evidencias_e_sao_idempotentes(env):
    flow = _flow(env)
    first = _run_success(env, flow)
    first_task = repo.execution_tasks.get(first["task_id"], CORE)
    assert flow.reject(first["task_id"], REJECT_PHRASE)["status"] == et.REVIEW_REJECTED
    assert Path(first_task["worktree_path"]).exists() and Path(first_task["result_path"]).exists()
    repo.execution_tasks.update_status(first["task_id"], CORE, et.FAILED)

    second = _run_success(env, flow)
    requested = flow.request_merge(second["task_id"])
    flow.approve_merge(second["task_id"], requested["approval_id"], APPROVE_MERGE_PHRASE)
    second_task = repo.execution_tasks.get(second["task_id"], CORE)
    assert flow.reject_merge(second["task_id"], REJECT_MERGE_PHRASE)["status"] == et.REVIEW_REJECTED
    events = repo.task_events.count_by_task(second["task_id"])
    assert flow.reject_merge(second["task_id"], REJECT_MERGE_PHRASE)["status"] == et.REVIEW_REJECTED
    assert repo.task_events.count_by_task(second["task_id"]) == events
    assert Path(second_task["worktree_path"]).exists() and Path(second_task["result_path"]).exists()
    assert repo.approvals.get(requested["approval_id"])["consumed_at"]


def test_reject_fecha_approval_de_merge_pendente(env):
    """Rejeitar uma task não pode deixar o approval de merge órfão na fila —
    era o bug do 'approval fantasma' que poluía a Operação."""
    flow = _flow(env)
    task = _run_success(env, flow)
    requested = flow.request_merge(task["task_id"])
    assert repo.approvals.get(requested["approval_id"])["status"] == "pending"

    assert flow.reject(task["task_id"], REJECT_PHRASE)["status"] == et.REVIEW_REJECTED

    # o approval pendente foi fechado junto com a rejeição
    assert repo.approvals.get(requested["approval_id"])["status"] != "pending"
    assert repo.approvals.count_pending(CORE) == 0


def test_claim_atomico_impede_dois_runs_da_mesma_task(env):
    flow = _flow(env)
    prepared = _approve(env, flow)
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    assert flow._claim_run(task) is True
    assert flow._claim_run(task) is False


def test_uma_task_real_ativa_por_projeto_e_smoke_compativel(env):
    first = _prepare(env)
    second = prepare_file(_write_spec(env, _spec(), "other.json"), registry=env["registry"])
    assert first["status"] == et.PENDING_APPROVAL
    assert second["reason"] == "active_programming_task_exists"
    parser = smoke.build_parser()
    assert parser.parse_args(["status", "--task-id", "exec_abc"]).command == "status"
