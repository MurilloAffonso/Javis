"""execution_task — modelo e máquina de estados do executor supervisionado (R4.1).

Sem executar agentes: só define os estados, transições válidas e validações de
identidade (task_id, executor, project_id, branch). O consumo do approval
persistido entra na R4.2 — aqui apenas exigimos a PRESENÇA dos ids de aprovação.
"""
from __future__ import annotations

import re
import secrets

DEFAULT_PROJECT_ID = "javes-core"
VALID_EXECUTORS = ("codex", "claude")
DEFAULT_TIMEOUT_SECONDS = 900

_TASK_ID_RE = re.compile(r"^exec_[a-f0-9]{8,64}$")
_BRANCH_RE = re.compile(r"^javes/exec/exec_[a-f0-9]{8,64}$")

# ── Estados ────────────────────────────────────────────────────────────────
DRAFT = "draft"
PENDING_APPROVAL = "pending_approval"
APPROVED = "approved"
PREPARING_WORKSPACE = "preparing_workspace"
RUNNING = "running"
TESTING = "testing"
AWAITING_REVIEW = "awaiting_review"
APPROVED_FOR_MERGE = "approved_for_merge"
MERGED = "merged"
COMPLETED = "completed"
BLOCKED = "blocked"
FAILED = "failed"
TIMED_OUT = "timed_out"
CANCELED = "canceled"
REVIEW_REJECTED = "review_rejected"

TERMINAL_STATES = frozenset({COMPLETED, BLOCKED, FAILED, TIMED_OUT, CANCELED, REVIEW_REJECTED})

ALL_STATES = frozenset({
    DRAFT, PENDING_APPROVAL, APPROVED, PREPARING_WORKSPACE, RUNNING, TESTING,
    AWAITING_REVIEW, APPROVED_FOR_MERGE, MERGED, COMPLETED,
    BLOCKED, FAILED, TIMED_OUT, CANCELED, REVIEW_REJECTED,
})

# Transições permitidas (grafo direcionado, só pra frente). Qualquer estado não
# terminal pode ser abortado para blocked/canceled; falhas de execução para failed.
_ALLOWED: dict[str, frozenset[str]] = {
    DRAFT:               frozenset({PENDING_APPROVAL, BLOCKED, CANCELED}),
    PENDING_APPROVAL:    frozenset({APPROVED, BLOCKED, CANCELED}),
    APPROVED:            frozenset({PREPARING_WORKSPACE, BLOCKED, CANCELED, FAILED}),
    PREPARING_WORKSPACE: frozenset({RUNNING, BLOCKED, CANCELED, FAILED}),
    RUNNING:             frozenset({TESTING, FAILED, TIMED_OUT, CANCELED}),
    TESTING:             frozenset({AWAITING_REVIEW, FAILED, TIMED_OUT, CANCELED}),
    AWAITING_REVIEW:     frozenset({APPROVED_FOR_MERGE, REVIEW_REJECTED, CANCELED}),
    APPROVED_FOR_MERGE:  frozenset({MERGED, REVIEW_REJECTED, FAILED, CANCELED}),
    MERGED:              frozenset({COMPLETED, FAILED}),
    # terminais → sem saída
    COMPLETED: frozenset(),
    BLOCKED: frozenset(),
    FAILED: frozenset(),
    TIMED_OUT: frozenset(),
    CANCELED: frozenset(),
    REVIEW_REJECTED: frozenset(),
}


class ExecutionError(Exception):
    """Erro base do domínio de execução."""


class InvalidTransition(ExecutionError):
    def __init__(self, current: str, target: str, detail: str = ""):
        self.current = current
        self.target = target
        msg = f"transição inválida: {current} -> {target}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


class ApprovalRequired(ExecutionError):
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"transição exige {field} presente")


class ValidationError(ExecutionError):
    pass


# ── Validações de identidade ──────────────────────────────────────────────
def new_task_id() -> str:
    """Gera um task_id seguro: exec_<16 hex>."""
    return f"exec_{secrets.token_hex(8)}"


def validate_task_id(task_id: str | None) -> str:
    tid = (task_id or "").strip()
    if not _TASK_ID_RE.match(tid):
        raise ValidationError("task_id inválido (esperado ^exec_[a-f0-9]{8,64}$)")
    return tid


def validate_executor(executor: str | None) -> str:
    ex = (executor or "").strip().lower()
    if ex not in VALID_EXECUTORS:
        raise ValidationError(f"executor inválido (esperado um de {VALID_EXECUTORS})")
    return ex


def normalize_project_id(project_id: str | None = None) -> str:
    """Vazio/None → javes-core. Nunca '' como 'todos'."""
    return (project_id or "").strip() or DEFAULT_PROJECT_ID


def branch_for(task_id: str) -> str:
    """Nome de branch seguro derivado do task_id (nunca do input do usuário)."""
    tid = validate_task_id(task_id)
    branch = f"javes/exec/{tid}"
    if not _BRANCH_RE.match(branch):  # defensivo
        raise ValidationError("branch derivada inválida")
    return branch


def validate_work_branch(branch: str | None) -> str:
    b = (branch or "").strip()
    if b in ("master", "main"):
        raise ValidationError("work_branch não pode ser master/main")
    if not _BRANCH_RE.match(b):
        raise ValidationError("work_branch inválida (esperado ^javes/exec/exec_[a-f0-9]{8,64}$)")
    return b


# ── Máquina de estados ────────────────────────────────────────────────────
def validate_transition(
    current: str,
    target: str,
    *,
    approval_id: int | None = None,
    merge_approval_id: int | None = None,
) -> str:
    """Valida uma transição. Retorna o target se válido; lança se inválido.

    - idempotência SÓ quando current == target;
    - estados terminais não avançam;
    - approved exige approval_id; approved_for_merge exige merge_approval_id;
    - merged só vem de approved_for_merge; completed só vem de merged
      (garantido pelo grafo _ALLOWED).
    """
    if current not in ALL_STATES:
        raise ValidationError(f"estado atual desconhecido: {current!r}")
    if target not in ALL_STATES:
        raise ValidationError(f"estado alvo desconhecido: {target!r}")

    # idempotência: mesmo estado é no-op permitido
    if current == target:
        return target

    if current in TERMINAL_STATES:
        raise InvalidTransition(current, target, "estado terminal não avança")

    if target not in _ALLOWED.get(current, frozenset()):
        raise InvalidTransition(current, target)

    if target == APPROVED and not approval_id:
        raise ApprovalRequired("approval_id")
    if target == APPROVED_FOR_MERGE and not merge_approval_id:
        raise ApprovalRequired("merge_approval_id")

    return target
