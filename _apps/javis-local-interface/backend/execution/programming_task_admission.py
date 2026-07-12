"""Admissão R4.4A: valida, persiste snapshot e solicita o primeiro gate."""
from __future__ import annotations

from pathlib import Path

import db
import repositories as repo
import safe_config

from .execution_facade import ExecutionFacade
from .programming_task_spec import load_and_validate
from .project_execution_registry import ProjectExecutionRegistry


def validate_file(path: str | Path, *, registry: ProjectExecutionRegistry | None = None) -> dict:
    return load_and_validate(path, registry).public_payload()


def prepare_file(path: str | Path, *, registry: ProjectExecutionRegistry | None = None) -> dict:
    registry = registry or ProjectExecutionRegistry()
    spec = load_and_validate(path, registry)
    if not safe_config.real_programming_tasks_enabled():
        return {"status": "blocked", "reason": "real_programming_tasks_disabled"}
    db.init_db()
    project = registry.require(spec.data["project_id"])
    if repo.execution_task_specs.active_for_project(project.project_id):
        return {"status": "blocked", "reason": "active_programming_task_exists",
                "project_id": project.project_id}
    facade = ExecutionFacade(repository_path=project.repository_path,
                             source_branch=project.source_branch)
    created = facade.create_task(
        objective=spec.data["objective"], project_id=project.project_id,
        executor=spec.data["executor"],
        timeout_seconds=spec.data["limits"]["max_duration_seconds"],
    )
    if created.get("status") == "blocked":
        return created
    task_id = created["task_id"]
    repo.execution_task_specs.add(
        task_id=task_id, project_id=project.project_id, spec_hash=spec.spec_hash,
        schema_version=spec.data["schema_version"], snapshot_json=spec.canonical_json,
    )
    approval = facade.request_start_approval(
        task_id, project.project_id, executor=spec.data["executor"], spec_hash=spec.spec_hash,
    )
    return {"status": approval["status"], "task_id": task_id,
            "approval_id": approval["approval_id"], "project_id": project.project_id,
            "executor": spec.data["executor"], "spec_hash": spec.spec_hash}
