"""execution_approvals — os DOIS gates de aprovação do executor (R4.2A).

Gate 1 (execution.start): pending_approval → approved.
Gate 2 (execution.merge):  awaiting_review  → approved_for_merge.

Nenhum agente é executado e NENHUM merge é feito aqui — o Gate 2 apenas registra
a aprovação e preenche merge_approval_id (o merge real é R4.2B).

Invariantes de segurança:
- aprovação é SINGLE-USE (consome via repo.approvals.consume);
- a aprovação precisa estar amarrada à MESMA task e ao MESMO project_id da
  execution_task (action + task_id + project_id conferem);
- execução e merge usam aprovações DIFERENTES (ação distinta e id distinto);
- o estado NÃO muda sem aprovação válida.
"""
from __future__ import annotations

from . import execution_task as et

ACTION_START = "execution.start"
ACTION_MERGE = "execution.merge"


class ApprovalDenied(et.ExecutionError):
    """Aprovação ausente, inválida, já consumida, ou de outra task/projeto."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"aprovação negada: {reason}")


def _repo():
    import repositories as repo
    return repo


def _journey(task_id: str, event_type: str, message: str, metadata: dict | None = None) -> None:
    try:
        _repo().task_events.add_event(task_id, event_type, "murillo", message,
                                      metadata=metadata)
    except Exception:
        pass


def _log(intent: str, message: str, approved: bool) -> None:
    try:
        _repo().logs.add(source="execution", intent=intent, agent="",
                         message=message, status="approved" if approved else "denied",
                         approved=approved)
    except Exception:
        pass


def _load_task(task_id: str, project_id: str) -> dict:
    tid = et.validate_task_id(task_id)
    pid = et.normalize_project_id(project_id)
    task = _repo().execution_tasks.get(tid, pid)
    if not task:
        raise ApprovalDenied("execution_task inexistente para task_id+project_id")
    return task


def _approval_bound(approval: dict | None, action: str, task_id: str, project_id: str) -> bool:
    """Aprovação válida (approved, não consumida, não expirada, ação e projeto
    conferem) E amarrada exatamente a esta task."""
    repo = _repo()
    if not repo.approvals.valid_for_action(approval, action, route="", project_id=project_id):
        return False
    return (approval.get("task_id") or "") == task_id


# ── Gate 1: execução ────────────────────────────────────────────────────────
def request_execution_start(task_id: str, project_id: str) -> dict:
    """draft → pending_approval, criando a aprovação (pending) de execution.start."""
    repo = _repo()
    task = _load_task(task_id, project_id)
    tid, pid = task["task_id"], task["project_id"]

    et.validate_transition(task["status"], et.PENDING_APPROVAL)

    approval_id = repo.approvals.add(
        subject=f"Executar tarefa {tid} ({task.get('executor', '?')})",
        kind="execution_gate", task_id=tid, project_id=pid,
        action=ACTION_START, risk_level="high", requested_by="execution",
        reason="human_approval_required_execution_start",
    )
    repo.execution_tasks.update_status(tid, pid, et.PENDING_APPROVAL)
    _journey(tid, "execution_approval_requested",
             f"Aprovação de execução solicitada (approval {approval_id})",
             {"action": ACTION_START, "approval_id": approval_id})
    return {"task_id": tid, "project_id": pid, "approval_id": approval_id,
            "status": et.PENDING_APPROVAL}


def approve_execution_start(task_id: str, project_id: str, approval_id: int) -> dict:
    """pending_approval → approved SOMENTE com aprovação válida e single-use."""
    repo = _repo()
    task = _load_task(task_id, project_id)
    tid, pid = task["task_id"], task["project_id"]

    approval = repo.approvals.get(approval_id)
    if not _approval_bound(approval, ACTION_START, tid, pid):
        _log(ACTION_START, f"execução {tid}: aprovação {approval_id} inválida", False)
        raise ApprovalDenied("aprovação de execução inválida/não-amarrada")

    # single-use: consumir; se já consumida (corrida), nega sem mudar estado
    if repo.approvals.consume(approval_id) < 1:
        _log(ACTION_START, f"execução {tid}: aprovação {approval_id} já consumida", False)
        raise ApprovalDenied("aprovação já consumida")

    et.validate_transition(task["status"], et.APPROVED, approval_id=approval_id)
    repo.execution_tasks.set_approval(tid, pid, approval_id)
    repo.execution_tasks.update_status(tid, pid, et.APPROVED)
    _journey(tid, "execution_approved",
             f"Execução aprovada (approval {approval_id})", {"approval_id": approval_id})
    _log(ACTION_START, f"execução {tid}: aprovada via approval {approval_id}", True)
    return {"task_id": tid, "project_id": pid, "approval_id": approval_id,
            "status": et.APPROVED}


# ── Gate 2: merge ───────────────────────────────────────────────────────────
def request_merge(task_id: str, project_id: str) -> dict:
    """Cria a aprovação (pending) de execution.merge para uma task em review.
    NÃO faz merge. A task permanece em awaiting_review."""
    repo = _repo()
    task = _load_task(task_id, project_id)
    tid, pid = task["task_id"], task["project_id"]
    if task["status"] != et.AWAITING_REVIEW:
        raise ApprovalDenied("merge só pode ser solicitado em awaiting_review")

    approval_id = repo.approvals.add(
        subject=f"Mergear tarefa {tid}",
        kind="execution_gate", task_id=tid, project_id=pid,
        action=ACTION_MERGE, risk_level="high", requested_by="execution",
        reason="human_approval_required_execution_merge",
    )
    _journey(tid, "merge_approval_requested",
             f"Aprovação de merge solicitada (approval {approval_id})",
             {"action": ACTION_MERGE, "approval_id": approval_id})
    return {"task_id": tid, "project_id": pid, "merge_approval_id": approval_id,
            "status": et.AWAITING_REVIEW}


def approve_merge(task_id: str, project_id: str, merge_approval_id: int) -> dict:
    """awaiting_review → approved_for_merge SOMENTE com aprovação de merge válida.
    NÃO executa o merge (isso é R4.2C1). Exige aprovação DIFERENTE da de execução."""
    repo = _repo()
    task = _load_task(task_id, project_id)
    tid, pid = task["task_id"], task["project_id"]

    # execução e merge usam aprovações diferentes
    if task.get("approval_id") and int(merge_approval_id) == int(task["approval_id"]):
        _log(ACTION_MERGE, f"merge {tid}: reuso da aprovação de execução negado", False)
        raise ApprovalDenied("aprovação de merge não pode ser a mesma da execução")

    approval = repo.approvals.get(merge_approval_id)
    if not _approval_bound(approval, ACTION_MERGE, tid, pid):
        _log(ACTION_MERGE, f"merge {tid}: aprovação {merge_approval_id} inválida", False)
        raise ApprovalDenied("aprovação de merge inválida/não-amarrada")

    if repo.approvals.consume(merge_approval_id) < 1:
        _log(ACTION_MERGE, f"merge {tid}: aprovação {merge_approval_id} já consumida", False)
        raise ApprovalDenied("aprovação de merge já consumida")

    et.validate_transition(task["status"], et.APPROVED_FOR_MERGE,
                           merge_approval_id=merge_approval_id)
    repo.execution_tasks.set_merge_approval(tid, pid, merge_approval_id)
    repo.execution_tasks.update_status(tid, pid, et.APPROVED_FOR_MERGE)
    _journey(tid, "merge_approved",
             f"Merge aprovado (approval {merge_approval_id}) — merge real é R4.2C1",
             {"merge_approval_id": merge_approval_id})
    _log(ACTION_MERGE, f"merge {tid}: aprovado via approval {merge_approval_id} (sem merge)", True)
    return {"task_id": tid, "project_id": pid, "merge_approval_id": merge_approval_id,
            "status": et.APPROVED_FOR_MERGE}
