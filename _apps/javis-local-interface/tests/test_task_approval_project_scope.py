from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import gate  # noqa: E402
import repositories as repo  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def test_task_de_um_projeto_nao_e_consultada_por_outro():
    repo.tasks.upsert("core-task", "Core task", project_id=gate.CORE_SCOPE)
    repo.tasks.upsert("jampa-task", "Jampa task", project_id=gate.CEREBRO_JAMPA_SCOPE)

    assert repo.tasks.get_task("core-task", project_id=gate.CORE_SCOPE)["title"] == "Core task"
    assert repo.tasks.get_task("jampa-task", project_id=gate.CORE_SCOPE) is None
    assert repo.tasks.get_task("core-task", project_id=gate.CEREBRO_JAMPA_SCOPE) is None


def test_board_filtra_tasks_por_project_id():
    repo.tasks.upsert("core-task", "Core task", project_id=gate.CORE_SCOPE)
    repo.tasks.upsert("jampa-task", "Jampa task", project_id=gate.CEREBRO_JAMPA_SCOPE)

    core = repo.tasks.for_board(project_id=gate.CORE_SCOPE)
    jampa = repo.tasks.for_board(project_id=gate.CEREBRO_JAMPA_SCOPE)

    assert [row["ext_id"] for row in core] == ["core-task"]
    assert [row["ext_id"] for row in jampa] == ["jampa-task"]


def test_approval_de_um_projeto_nao_aparece_no_outro():
    core_id = repo.approvals.add("Aprovar core", project_id=gate.CORE_SCOPE)
    jampa_id = repo.approvals.add("Aprovar jampa", project_id=gate.CEREBRO_JAMPA_SCOPE)

    core = repo.approvals.pending(project_id=gate.CORE_SCOPE)
    jampa = repo.approvals.pending(project_id=gate.CEREBRO_JAMPA_SCOPE)

    assert [row["id"] for row in core] == [core_id]
    assert [row["id"] for row in jampa] == [jampa_id]
    assert repo.approvals.count_pending(project_id=gate.CORE_SCOPE) == 1
    assert repo.approvals.count_pending(project_id=gate.CEREBRO_JAMPA_SCOPE) == 1


def test_approval_por_task_respeita_project_id():
    repo.approvals.add("Core gate", task_id="same-task", project_id=gate.CORE_SCOPE)
    repo.approvals.add("Jampa gate", task_id="same-task", project_id=gate.CEREBRO_JAMPA_SCOPE)

    assert [row["subject"] for row in repo.approvals.by_task("same-task", project_id=gate.CORE_SCOPE)] == ["Core gate"]
    assert [row["subject"] for row in repo.approvals.by_task("same-task", project_id=gate.CEREBRO_JAMPA_SCOPE)] == ["Jampa gate"]
