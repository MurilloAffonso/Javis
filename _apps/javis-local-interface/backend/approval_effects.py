"""approval_effects.py — efeitos de decisões de aprovação (MODO SEGURO).

Quando a Gate 1 da pauta da Vem Passear é APROVADA, destrava a próxima etapa do
workflow (Design/Estúdio) SEM gerar criativo: marca a gate como aprovada e libera
a task de Design no Quadro (dual-write Markdown + SQLite), logando o avanço.

A task de Design JÁ EXISTE no pipeline (t2 do backlog) — então ela é LIBERADA, não
duplicada. Idempotente: re-decidir é bloqueado no endpoint (409), e aqui ainda
checamos se a gate já avançou. Rejeição só sinaliza "pauta aguardando ajuste",
sem criar nada e sem apagar nada.

NÃO chama Nova, NÃO gera criativo, NÃO toca integração externa.
"""
from __future__ import annotations

_MISSION      = "pipeline-marketing-vem-passear-jampa"
_PAUTA_TASK   = _MISSION + "-t0"   # âncora da jornada (a pauta)
_GATE_TASK    = _MISSION + "-t1"   # [Gate 1 — aprovação Murillo]
_DESIGN_TASK  = _MISSION + "-t2"   # [Design] Produzir os criativos da pauta aprovada
_DESIGN_TITLE = "[Design] Produzir os criativos da pauta aprovada"


def _journey(event_type: str, actor: str, message: str, agent_id=None, metadata=None) -> None:
    """Evento no Journey Log da pauta (t0). Nunca quebra o efeito se falhar."""
    try:
        import repositories as repo
        repo.task_events.add_event(_PAUTA_TASK, event_type, actor, message,
                                   agent_id=agent_id, metadata=metadata)
    except Exception:
        pass


def is_gate1_pauta_vp(approval: dict) -> bool:
    """Identifica a Gate 1 da pauta VP: agente nova + assunto da pauta/Gate 1."""
    subj  = (approval.get("subject") or "").lower()
    agent = (approval.get("agent") or "").lower()
    return agent == "nova" and ("pauta da semana" in subj or "gate 1" in subj)


def _log(intent: str, message: str, agent: str = "", status: str = "ok", approved=None) -> None:
    try:
        import repositories as repo
        repo.logs.add(source="system", intent=intent, agent=agent,
                      message=message, status=status, approved=approved)
    except Exception:
        pass


def on_decided(approval: dict, approved: bool, note: str = "") -> dict:
    """Roda após a decisão já estar persistida. Retorna resumo pro endpoint/UI."""
    if not is_gate1_pauta_vp(approval):
        return {"advanced": False, "reason": "não é Gate 1 da pauta VP"}
    return _advance(approval) if approved else _reject(approval)


def _advance(approval: dict) -> dict:
    import repositories as repo
    aid = approval.get("id")

    # idempotência: se a gate já avançou, não re-libera nem re-loga
    gate = next((t for t in repo.tasks.list() if t["ext_id"] == _GATE_TASK), None)
    if gate and gate.get("status") == "gate_approved":
        return {"advanced": False, "already": True, "design_task": _DESIGN_TASK,
                "message": "Gate 1 já estava aprovada; Design já liberado."}

    # 1) dual-write Markdown: marca a gate (t1) como concluída no mission_board
    try:
        import mission_board
        mission_board.set_task_done(_MISSION, _GATE_TASK, True)
    except Exception as e:
        _log("workflow_advance", f"mission_board falhou: {e}", status="error")

    # 2) SQLite: re-espelha o quadro (t1 done, t2 pending) e marca a gate como gate_approved
    try:
        import db_sync
        db_sync.sync_tasks()
    except Exception:
        pass
    repo.tasks.set_status(_GATE_TASK, "gate_approved")

    # 3) garante a task de Design liberada (pending). Ela já existe = t2; upsert
    #    é idempotente (ext_id único), então NUNCA duplica.
    repo.tasks.upsert(_DESIGN_TASK, _DESIGN_TITLE, status="pending",
                      mission=_MISSION, source=f"approval:{aid}")

    # 4) log do avanço do workflow
    _log("workflow_advance",
         f"Gate 1 aprovada (approval {aid}) → liberada a task de Design "
         f"'{_DESIGN_TITLE}' ({_DESIGN_TASK}) no workflow '{_MISSION}'",
         agent="estudio")

    # Journey Log: aprovação → avanço → desbloqueio do Design
    _journey("approval_approved", "murillo", f"Gate 1 aprovada (approval {aid})")
    _journey("workflow_advanced", "system", "Workflow avançou: gate concluída")
    _journey("design_task_unlocked", "system",
             "Task de Design liberada para produção", agent_id="estudio",
             metadata={"design_task": _DESIGN_TASK})

    return {"advanced": True, "design_task": _DESIGN_TASK, "design_title": _DESIGN_TITLE,
            "message": "Gate 1 aprovada. Produção de criativos destravada."}


def _reject(approval: dict) -> dict:
    aid = approval.get("id")
    _log("workflow_reject",
         f"Gate 1 rejeitada (approval {aid}) → pauta aguardando ajuste; "
         f"NÃO foi criada task de Design.", agent="nova", status="rejected")
    # Journey Log: rejeição → ajuste necessário
    _journey("approval_rejected", "murillo", f"Gate 1 rejeitada (approval {aid})")
    _journey("adjustment_required", "system",
             "Pauta aguardando ajuste da Nova antes de novo Gate", agent_id="nova")
    # sinal de ajuste, sem apagar nada
    try:
        import repositories as repo
        repo.memories.add(
            "Pauta da semana VP reprovada no Gate 1 — aguardando ajuste da Nova.",
            key="gate1_pauta_vp", kind="sinal")
    except Exception:
        pass
    return {"advanced": False, "rejected": True,
            "message": "Gate 1 rejeitada. Pauta aguardando ajuste."}
