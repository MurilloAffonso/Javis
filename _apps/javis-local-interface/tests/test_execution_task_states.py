"""R4.1 — máquina de estados do execution_task (sem executar agentes)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution import execution_task as et  # noqa: E402


# ── identidade ─────────────────────────────────────────────────────────────
def test_new_task_id_valido():
    tid = et.new_task_id()
    assert et.validate_task_id(tid) == tid


@pytest.mark.parametrize("bad", ["", "exec_", "exec_XYZ", "abc_123", "exec_123", "exec_" + "g" * 8])
def test_task_id_invalido(bad):
    with pytest.raises(et.ValidationError):
        et.validate_task_id(bad)


def test_executor_validado():
    assert et.validate_executor("codex") == "codex"
    assert et.validate_executor("CLAUDE") == "claude"
    with pytest.raises(et.ValidationError):
        et.validate_executor("gpt")


def test_project_id_default_e_explicito():
    assert et.normalize_project_id("") == "javes-core"
    assert et.normalize_project_id(None) == "javes-core"
    assert et.normalize_project_id("project:cerebro-jampa") == "project:cerebro-jampa"


def test_branch_derivada_e_master_bloqueado():
    tid = et.new_task_id()
    assert et.branch_for(tid) == f"javes/exec/{tid}"
    for bad in ("master", "main"):
        with pytest.raises(et.ValidationError):
            et.validate_work_branch(bad)


# ── transições ─────────────────────────────────────────────────────────────
def test_draft_para_pending_approval():
    assert et.validate_transition(et.DRAFT, et.PENDING_APPROVAL) == et.PENDING_APPROVAL


def test_approved_exige_approval_id():
    with pytest.raises(et.ApprovalRequired):
        et.validate_transition(et.PENDING_APPROVAL, et.APPROVED)
    assert et.validate_transition(et.PENDING_APPROVAL, et.APPROVED, approval_id=7) == et.APPROVED


def test_approved_for_merge_exige_merge_approval_id():
    with pytest.raises(et.ApprovalRequired):
        et.validate_transition(et.AWAITING_REVIEW, et.APPROVED_FOR_MERGE)
    assert et.validate_transition(
        et.AWAITING_REVIEW, et.APPROVED_FOR_MERGE, merge_approval_id=9
    ) == et.APPROVED_FOR_MERGE


def test_merged_so_vem_de_approved_for_merge():
    assert et.validate_transition(et.APPROVED_FOR_MERGE, et.MERGED) == et.MERGED
    with pytest.raises(et.InvalidTransition):
        et.validate_transition(et.RUNNING, et.MERGED)


def test_completed_so_vem_de_merged():
    assert et.validate_transition(et.MERGED, et.COMPLETED) == et.COMPLETED
    with pytest.raises(et.InvalidTransition):
        et.validate_transition(et.RUNNING, et.COMPLETED)


def test_transicao_invalida_falha():
    with pytest.raises(et.InvalidTransition):
        et.validate_transition(et.DRAFT, et.RUNNING)


def test_estado_terminal_nao_avanca():
    with pytest.raises(et.InvalidTransition):
        et.validate_transition(et.COMPLETED, et.RUNNING)
    with pytest.raises(et.InvalidTransition):
        et.validate_transition(et.CANCELED, et.PENDING_APPROVAL)


def test_idempotencia_mesmo_estado():
    assert et.validate_transition(et.RUNNING, et.RUNNING) == et.RUNNING
    assert et.validate_transition(et.COMPLETED, et.COMPLETED) == et.COMPLETED
