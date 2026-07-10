"""R4.2A — os dois gates de aprovação (execution.start / execution.merge).

Nenhum agente é executado e nenhum merge é feito. Aprovações são single-use e
amarradas a task_id + project_id.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution import execution_approvals as ea  # noqa: E402

CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def _mk_task(project_id: str = CORE, status: str = "draft", approval_id=None) -> str:
    tid = et.new_task_id()
    repo.execution_tasks.create(
        task_id=tid, project_id=project_id, executor="codex", objective="obj",
        repository_path="/repo", source_branch="main",
        work_branch=f"javes/exec/{tid}", worktree_path=f"/wt/{tid}", status=status,
    )
    if approval_id is not None:
        repo.execution_tasks.set_approval(tid, project_id, approval_id)
    return tid


def _approved_approval(action: str, task_id: str, project_id: str) -> int:
    aid = repo.approvals.add(subject="x", kind="execution_gate", task_id=task_id,
                             project_id=project_id, action=action, risk_level="high")
    repo.approvals.decide(aid, True)
    return aid


# ── Gate 1: execução ────────────────────────────────────────────────────────
def test_fluxo_feliz_execucao():
    tid = _mk_task()
    req = ea.request_execution_start(tid, CORE)
    assert req["status"] == et.PENDING_APPROVAL
    repo.approvals.decide(req["approval_id"], True)
    out = ea.approve_execution_start(tid, CORE, req["approval_id"])
    assert out["status"] == et.APPROVED
    task = repo.execution_tasks.get(tid, CORE)
    assert task["status"] == et.APPROVED and task["approval_id"] == req["approval_id"]
    # aprovação consumida
    assert repo.approvals.get(req["approval_id"])["consumed_at"] is not None


def test_approval_de_outro_project_recusado():
    tid = _mk_task(project_id=CORE, status="pending_approval")
    # aprovação amarrada a JAMPA, não a CORE
    aid = _approved_approval(ea.ACTION_START, tid, JAMPA)
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_execution_start(tid, CORE, aid)
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.PENDING_APPROVAL


def test_approval_de_outra_task_recusado():
    tid = _mk_task(status="pending_approval")
    outra = _mk_task(status="pending_approval")
    aid = _approved_approval(ea.ACTION_START, outra, CORE)  # amarrada a 'outra'
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_execution_start(tid, CORE, aid)
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.PENDING_APPROVAL


def test_single_use_nao_reutiliza():
    tid = _mk_task(status="pending_approval")
    aid = _approved_approval(ea.ACTION_START, tid, CORE)
    ea.approve_execution_start(tid, CORE, aid)  # consome
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_execution_start(tid, CORE, aid)  # segundo uso


def test_estado_nao_muda_sem_approval():
    tid = _mk_task(status="pending_approval")
    # aprovação ainda pendente (não decidida) → negada, estado intacto
    pend = repo.approvals.add(subject="x", kind="execution_gate", task_id=tid,
                              project_id=CORE, action=ea.ACTION_START)
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_execution_start(tid, CORE, pend)
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.PENDING_APPROVAL
    # approval_id inexistente → negada
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_execution_start(tid, CORE, 999999)
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.PENDING_APPROVAL


# ── Gate 2: merge ───────────────────────────────────────────────────────────
def test_fluxo_feliz_merge_sem_mergear():
    start_aid = _approved_approval(ea.ACTION_START, "placeholder", CORE)  # id qualquer
    tid = _mk_task(status="awaiting_review", approval_id=start_aid)
    req = ea.request_merge(tid, CORE)
    assert req["status"] == et.AWAITING_REVIEW  # não mergeou
    repo.approvals.decide(req["merge_approval_id"], True)
    out = ea.approve_merge(tid, CORE, req["merge_approval_id"])
    assert out["status"] == et.APPROVED_FOR_MERGE
    task = repo.execution_tasks.get(tid, CORE)
    assert task["status"] == et.APPROVED_FOR_MERGE
    assert task["merge_approval_id"] == req["merge_approval_id"]


def test_execucao_e_merge_usam_approvals_diferentes():
    start_aid = _approved_approval(ea.ACTION_START, "t", CORE)
    tid = _mk_task(status="awaiting_review", approval_id=start_aid)
    # reusar a aprovação de execução como merge → recusado
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_merge(tid, CORE, start_aid)
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.AWAITING_REVIEW


def test_merge_com_acao_errada_recusado():
    tid = _mk_task(status="awaiting_review", approval_id=111)
    # aprovação com ação execution.start (não merge) → recusada no gate de merge
    aid = _approved_approval(ea.ACTION_START, tid, CORE)
    with pytest.raises(ea.ApprovalDenied):
        ea.approve_merge(tid, CORE, aid)
    assert repo.execution_tasks.get(tid, CORE)["status"] == et.AWAITING_REVIEW
