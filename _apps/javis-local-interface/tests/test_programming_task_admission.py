"""R4.4A — admissão segura, sem agente, rede, worktree ou merge."""
from __future__ import annotations

import copy
import json
import sqlite3
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
from execution import execution_approvals as ea  # noqa: E402
from execution.programming_task_admission import prepare_file, validate_file  # noqa: E402
from execution.programming_task_spec import SpecValidationError, load_and_validate  # noqa: E402
from execution.project_execution_registry import ProjectExecutionRegistry  # noqa: E402


def valid_spec() -> dict:
    return {
        "schema_version": 1,
        "project_id": "javes-core",
        "title": "Atualiza documentação segura",
        "objective": "Atualizar uma seção documental sem alterar código de execução.",
        "executor": "claude",
        "allowed_paths": ["docs/"],
        "test_profile": "docs_only",
        "limits": {"max_duration_seconds": 300, "max_changed_files": 5,
                   "max_diff_lines": 300},
    }


@pytest.fixture()
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.delenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", raising=False)
    monkeypatch.delenv("JAVIS_ENABLE_SUPERVISED_EXEC", raising=False)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    registry = ProjectExecutionRegistry(tmp_path / "repo")
    return tmp_path, registry


def write_spec(tmp_path: Path, data: dict, name: str = "spec.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def rejected(tmp_path: Path, registry: ProjectExecutionRegistry, data: dict) -> str:
    with pytest.raises(SpecValidationError) as error:
        load_and_validate(write_spec(tmp_path, data), registry)
    return error.value.reason


def test_validate_spec_valida_e_retorna_json_sanitizado(isolated):
    tmp_path, registry = isolated
    out = validate_file(write_spec(tmp_path, valid_spec()), registry=registry)
    assert out["status"] == "valid"
    assert out["project_id"] == "javes-core" and out["executor"] == "claude"
    assert len(out["spec_hash"]) == 64
    assert "objective" not in out and str(tmp_path) not in json.dumps(out)


def test_campos_desconhecidos_e_comandos_shell_bloqueiam(isolated):
    tmp_path, registry = isolated
    for field in ("extra", "commands", "shell", "environment", "repository_path"):
        data = valid_spec()
        data[field] = ["rm", "-rf"]
        assert rejected(tmp_path, registry, data) == "unknown_or_missing_fields"


def test_project_executor_e_profile_fora_da_allowlist_bloqueiam(isolated):
    tmp_path, registry = isolated
    cases = [("project_id", "outro", "project_not_allowed"),
             ("executor", "bash", "executor_not_allowed"),
             ("test_profile", "pytest --network", "test_profile_not_allowed")]
    for field, value, reason in cases:
        data = valid_spec()
        data[field] = value
        assert rejected(tmp_path, registry, data) == reason


@pytest.mark.parametrize("path", [
    "C:/Windows", "C:\\Windows", "//server/share", "../docs", "docs/../../fora",
    ".git/", ".env", ".env.local", "dados.sqlite", "cache.db", "_data/",
    "javis-worktrees/", "node_modules/", ".venv/", "__pycache__/", "api-credentials.json",
])
def test_paths_inseguros_bloqueiam(isolated, path):
    tmp_path, registry = isolated
    data = valid_spec()
    data["allowed_paths"] = [path]
    assert rejected(tmp_path, registry, data).startswith("allowed_path")


def test_symlink_que_escapa_do_repo_bloqueia(isolated):
    tmp_path, registry = isolated
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink indisponível neste Windows")
    data = valid_spec()
    data["allowed_paths"] = ["link/"]
    assert rejected(tmp_path, registry, data) == "allowed_path_escape"


def test_limites_acima_da_politica_bloqueiam(isolated):
    tmp_path, registry = isolated
    for field, value in (("max_duration_seconds", 301), ("max_changed_files", 6),
                         ("max_diff_lines", 301)):
        data = valid_spec()
        data["limits"][field] = value
        assert rejected(tmp_path, registry, data) == f"{field}_exceeds_policy"


def test_hash_deterministico_e_alteracao_muda_hash(isolated):
    tmp_path, registry = isolated
    first = load_and_validate(write_spec(tmp_path, valid_spec(), "one.json"), registry)
    reordered = dict(reversed(list(valid_spec().items())))
    second = load_and_validate(write_spec(tmp_path, reordered, "two.json"), registry)
    changed = valid_spec()
    changed["objective"] += " Mudança."
    third = load_and_validate(write_spec(tmp_path, changed, "three.json"), registry)
    assert first.spec_hash == second.spec_hash
    assert first.spec_hash != third.spec_hash


def test_validate_e_prepare_desabilitado_nao_persistem(isolated):
    tmp_path, registry = isolated
    path = write_spec(tmp_path, valid_spec())
    assert validate_file(path, registry=registry)["status"] == "valid"
    assert not db.DB_PATH.exists()
    assert prepare_file(path, registry=registry) == {
        "status": "blocked", "reason": "real_programming_tasks_disabled"
    }
    assert not db.DB_PATH.exists()


def test_prepare_habilitado_cria_task_snapshot_e_approval_vinculado(isolated, monkeypatch):
    tmp_path, registry = isolated
    monkeypatch.setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    path = write_spec(tmp_path, valid_spec())
    expected = load_and_validate(path, registry)
    out = prepare_file(path, registry=registry)
    assert out["status"] == "pending_approval"
    assert set(out) == {"status", "task_id", "approval_id", "project_id", "executor", "spec_hash"}
    assert out["spec_hash"] == expected.spec_hash
    task = repo.execution_tasks.get(out["task_id"], "javes-core")
    approval = repo.approvals.get(out["approval_id"])
    snapshot = repo.execution_task_specs.get(out["task_id"], "javes-core")
    assert task["status"] == "pending_approval" and task["worktree_path"] == ""
    assert approval["action"] == ea.ACTION_START
    assert approval["task_id"] == out["task_id"] and approval["project_id"] == "javes-core"
    assert approval["executor"] == "claude" and approval["spec_hash"] == expected.spec_hash
    assert snapshot["spec_hash"] == expected.spec_hash
    assert json.loads(snapshot["snapshot_json"])["objective"] == valid_spec()["objective"]
    assert not (tmp_path / "javis-worktrees").exists()


def test_uma_task_real_ativa_por_projeto_sem_bloquear_smoke(isolated, monkeypatch):
    tmp_path, registry = isolated
    monkeypatch.setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    path = write_spec(tmp_path, valid_spec())
    first = prepare_file(path, registry=registry)
    second = prepare_file(path, registry=registry)
    assert first["status"] == "pending_approval"
    assert second["reason"] == "active_programming_task_exists"
    smoke_task = repo.execution_tasks.create(
        task_id="exec_smoke44a", project_id="javes-core", executor="claude",
        objective="smoke isolado", repository_path="/repo", source_branch="master",
        work_branch="javes/exec/exec_smoke44a", worktree_path="", status="draft",
    )
    assert smoke_task == "exec_smoke44a"
    assert repo.execution_task_specs.get(smoke_task, "javes-core") is None


def test_leituras_nao_vazam_outro_project_id(isolated, monkeypatch):
    tmp_path, registry = isolated
    monkeypatch.setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    out = prepare_file(write_spec(tmp_path, valid_spec()), registry=registry)
    assert repo.execution_tasks.get(out["task_id"], "outro") is None
    assert repo.execution_task_specs.get(out["task_id"], "outro") is None


def test_approval_com_spec_hash_alterado_nao_pode_ser_usado(isolated, monkeypatch):
    tmp_path, registry = isolated
    monkeypatch.setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    out = prepare_file(write_spec(tmp_path, valid_spec()), registry=registry)
    repo.approvals.decide(out["approval_id"], True)
    db.execute("UPDATE approvals SET spec_hash='0' WHERE id=?", (out["approval_id"],))
    with pytest.raises(ea.ApprovalDenied, match="spec_snapshot_mismatch"):
        ea.approve_execution_start(out["task_id"], "javes-core", out["approval_id"])
    assert repo.execution_tasks.get(out["task_id"], "javes-core")["status"] == "pending_approval"


def test_snapshot_e_imutavel_e_hash_ausente_invalida_approval(isolated, monkeypatch):
    tmp_path, registry = isolated
    monkeypatch.setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    out = prepare_file(write_spec(tmp_path, valid_spec()), registry=registry)
    with pytest.raises(sqlite3.IntegrityError, match="execution_task_spec_immutable"):
        db.execute(
            "UPDATE execution_task_specs SET snapshot_json='{}' WHERE task_id=? AND project_id=?",
            (out["task_id"], "javes-core"),
        )
    repo.approvals.decide(out["approval_id"], True)
    db.execute("UPDATE approvals SET spec_hash='' WHERE id=?", (out["approval_id"],))
    with pytest.raises(ea.ApprovalDenied, match="spec_snapshot_mismatch"):
        ea.approve_execution_start(out["task_id"], "javes-core", out["approval_id"])


def test_smoke_cli_existente_continua_comandos_compatíveis():
    parser = smoke.build_parser()
    assert parser.parse_args(["status", "--task-id", "exec_abc"]).command == "status"
