"""Registro confiável de repositórios elegíveis para execução supervisionada."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


JAVIS_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class ProjectExecution:
    project_id: str
    repository_path: Path
    source_branch: str


class ProjectExecutionRegistry:
    def __init__(self, javis_root: str | Path | None = None):
        root = Path(javis_root or JAVIS_ROOT).resolve()
        self._projects = {"javes-core": ProjectExecution("javes-core", root, "master")}

    def get(self, project_id: str) -> ProjectExecution | None:
        return self._projects.get((project_id or "").strip())

    def require(self, project_id: str) -> ProjectExecution:
        project = self.get(project_id)
        if project is None:
            raise ValueError("project_not_allowed")
        return project
