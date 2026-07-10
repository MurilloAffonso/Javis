"""R3.1 — Correção 1: tasks/approvals sempre com escopo por project_id.

Prova que as ROTAS operacionais sem project_id caem em javes-core (nunca "todos"),
que registros legados (project_id NULL) contam como javes-core, e que o Jampa
continua isolado. Sem servidor, sem rede.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import gate  # noqa: E402
import repositories as repo  # noqa: E402
import server  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def _body(resp) -> dict:
    return json.loads(bytes(resp.body))


def _seed():
    repo.tasks.upsert("core-task", "Core task", project_id=gate.CORE_SCOPE)
    repo.tasks.upsert("jampa-task", "Jampa task", project_id=gate.CEREBRO_JAMPA_SCOPE)
    repo.approvals.add("Aprovar core", project_id=gate.CORE_SCOPE)
    repo.approvals.add("Aprovar jampa", project_id=gate.CEREBRO_JAMPA_SCOPE)


# --- GET /tasks sem project_id → só javes-core -----------------------------
def test_get_tasks_sem_project_id_retorna_so_javes_core():
    _seed()
    body = _body(asyncio.run(server.tasks_list()))
    ext_ids = [t["ext_id"] for t in body["tasks"]]
    assert ext_ids == ["core-task"]
    assert "jampa-task" not in ext_ids


def test_get_tasks_jampa_retorna_so_jampa():
    _seed()
    body = _body(asyncio.run(server.tasks_list(project_id=gate.CEREBRO_JAMPA_SCOPE)))
    assert [t["ext_id"] for t in body["tasks"]] == ["jampa-task"]


def test_task_legada_sem_project_id_conta_como_javes_core():
    repo.tasks.upsert("legacy-task", "Legacy", project_id=None)  # NULL
    body = _body(asyncio.run(server.tasks_list()))
    ext_ids = [t["ext_id"] for t in body["tasks"]]
    assert "legacy-task" in ext_ids  # legado → javes-core, não some
    # e NÃO aparece no Jampa
    jampa = _body(asyncio.run(server.tasks_list(project_id=gate.CEREBRO_JAMPA_SCOPE)))
    assert "legacy-task" not in [t["ext_id"] for t in jampa["tasks"]]


# --- GET /approvals/pending sem project_id → só javes-core -----------------
def test_get_approvals_pending_sem_project_id_so_javes_core():
    _seed()
    body = _body(asyncio.run(server.approvals_pending()))
    subjects = [a["subject"] for a in body["approvals"]]
    assert subjects == ["Aprovar core"]
    assert body["project_id"] == gate.CORE_SCOPE


def test_get_approvals_pending_jampa_so_jampa():
    _seed()
    body = _body(asyncio.run(server.approvals_pending(project_id=gate.CEREBRO_JAMPA_SCOPE)))
    assert [a["subject"] for a in body["approvals"]] == ["Aprovar jampa"]


# --- digest/events: task de outro projeto → 404 (nunca vaza) ----------------
def test_digest_task_do_jampa_nao_aparece_no_default():
    _seed()
    resp = asyncio.run(server.task_digest("jampa-task"))  # sem project_id → javes-core
    assert resp.status_code == 404
    body = _body(resp)
    assert body["reason"] == "task_not_found"


def test_events_task_do_jampa_nao_aparece_no_default():
    _seed()
    resp = asyncio.run(server.task_events("jampa-task"))  # sem project_id → javes-core
    assert resp.status_code == 404


def test_digest_task_do_jampa_ok_com_escopo_correto():
    _seed()
    resp = asyncio.run(server.task_digest("jampa-task", project_id=gate.CEREBRO_JAMPA_SCOPE))
    assert resp.status_code != 404
    assert _body(resp)["task_id"] == "jampa-task"
