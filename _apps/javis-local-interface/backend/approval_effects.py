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
# Gate 2 → Distribuição (modo seguro, prepara pacote; publicação é depois do Gate 3)
_DIST_TASK    = "vp-distribuicao-preparar"
_DIST_TITLE   = "[Distribuição] Preparar pacote de publicação da pauta aprovada"


def _journey(task_id: str, event_type: str, actor: str, message: str, agent_id=None, metadata=None) -> None:
    """Evento no Journey Log de `task_id`. Nunca quebra o efeito se falhar."""
    try:
        import repositories as repo
        repo.task_events.add_event(task_id, event_type, actor, message,
                                   agent_id=agent_id, metadata=metadata)
    except Exception:
        pass


def is_gate1_pauta_vp(approval: dict) -> bool:
    """Identifica a Gate 1 da pauta VP: agente nova + assunto da pauta/Gate 1."""
    subj  = (approval.get("subject") or "").lower()
    agent = (approval.get("agent") or "").lower()
    return agent == "nova" and ("pauta da semana" in subj or "gate 1" in subj)


def is_gate2_criativos(approval: dict) -> bool:
    """Identifica a Gate 2 dos criativos: agente estudio + assunto de criativos."""
    subj  = (approval.get("subject") or "").lower()
    agent = (approval.get("agent") or "").lower()
    return agent == "estudio" and "criativos da semana" in subj


def is_gate3_distribuicao(approval: dict) -> bool:
    """Identifica a Gate 3 da distribuição: agente midas + assunto de distribuição."""
    subj  = (approval.get("subject") or "").lower()
    agent = (approval.get("agent") or "").lower()
    return agent in ("midas", "distribuicao") and "distribuição antes de publicar" in subj


def _log(intent: str, message: str, agent: str = "", status: str = "ok", approved=None) -> None:
    try:
        import repositories as repo
        repo.logs.add(source="system", intent=intent, agent=agent,
                      message=message, status=status, approved=approved)
    except Exception:
        pass


def on_decided(approval: dict, approved: bool, note: str = "") -> dict:
    """Roda após a decisão já estar persistida. Retorna resumo pro endpoint/UI."""
    if is_gate1_pauta_vp(approval):
        return _advance(approval) if approved else _reject(approval)
    if is_gate2_criativos(approval):
        return _advance_gate2(approval) if approved else _reject_gate2(approval)
    if is_gate3_distribuicao(approval):
        return _advance_gate3(approval) if approved else _reject_gate3(approval)
    return {"advanced": False, "reason": "aprovação sem efeito de workflow"}


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
    _journey(_PAUTA_TASK, "approval_approved", "murillo", f"Gate 1 aprovada (approval {aid})")
    _journey(_PAUTA_TASK, "workflow_advanced", "system", "Workflow avançou: gate concluída")
    _journey(_PAUTA_TASK, "design_task_unlocked", "system",
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
    _journey(_PAUTA_TASK, "approval_rejected", "murillo", f"Gate 1 rejeitada (approval {aid})")
    _journey(_PAUTA_TASK, "adjustment_required", "system",
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


# ── Gate 2 (criativos) → Distribuição ────────────────────────────────────
def _advance_gate2(approval: dict) -> dict:
    """Gate 2 aprovada → libera/cria a task de Distribuição (modo seguro)."""
    import repositories as repo
    aid = approval.get("id")
    design_task = approval.get("task_id") or _DESIGN_TASK  # jornada do Gate 2 = task de Design

    # idempotência: se a task de Distribuição já existe, não re-cria nem re-loga
    if repo.tasks.get_task(_DIST_TASK):
        return {"advanced": False, "already": True, "distribution_task": _DIST_TASK,
                "message": "Gate 2 já avançou; Distribuição já liberada."}

    # criativos aprovados → Design fica gate_approved
    repo.tasks.set_status(design_task, "gate_approved")
    # cria a task de Distribuição (só no SQLite; é a fonte principal do Quadro)
    repo.tasks.upsert(_DIST_TASK, _DIST_TITLE, status="pending", mission=_MISSION,
                      source=f"approval:{aid}", agent="midas", project_id="vem-passear-jampa")

    _log("workflow_advance",
         f"Gate 2 aprovada (approval {aid}) → liberada a task de Distribuição "
         f"'{_DIST_TITLE}' ({_DIST_TASK})", agent="midas")
    _journey(design_task, "approval_approved", "murillo", f"Gate 2 aprovada (approval {aid})")
    _journey(design_task, "workflow_advanced", "system", "Workflow avançou: criativos aprovados")
    _journey(design_task, "distribution_task_unlocked", "system",
             "Task de Distribuição liberada para preparação", agent_id="midas",
             metadata={"distribution_task": _DIST_TASK})

    return {"advanced": True, "distribution_task": _DIST_TASK, "distribution_title": _DIST_TITLE,
            "message": "Gate 2 aprovada. Distribuição destravada (sem publicar)."}


def _reject_gate2(approval: dict) -> dict:
    """Gate 2 rejeitada → NÃO cria Distribuição; mantém Design disponível pra ajuste."""
    import repositories as repo
    aid = approval.get("id")
    design_task = approval.get("task_id") or _DESIGN_TASK
    _log("workflow_reject",
         f"Gate 2 rejeitada (approval {aid}) → criativos aguardando ajuste; "
         f"NÃO foi criada Distribuição.", agent="estudio", status="rejected")
    _journey(design_task, "approval_rejected", "murillo", f"Gate 2 rejeitada (approval {aid})")
    _journey(design_task, "adjustment_required", "system",
             "Criativos aguardando ajuste do Estúdio antes de novo Gate", agent_id="estudio")
    # mantém o Design disponível pra ajuste (reabre pra rodar o Estúdio de novo)
    try:
        repo.tasks.set_status(design_task, "pending")
        repo.memories.add(
            "Criativos da semana VP reprovados no Gate 2 — aguardando ajuste do Estúdio.",
            key="gate2_criativos_vp", kind="sinal")
    except Exception:
        pass
    return {"advanced": False, "rejected": True,
            "message": "Gate 2 rejeitada. Criativos aguardando ajuste."}


# ── Gate 3 (distribuição) → pacote manual + fim da campanha ───────────────
def _advance_gate3(approval: dict) -> dict:
    """Gate 3 aprovada → gera o pacote de publicação MANUAL e fecha a campanha
    (conclui a task de Distribuição via lifecycle/digest). NÃO publica nada."""
    import repositories as repo
    import distribution, task_lifecycle
    aid = approval.get("id")
    dist_task = approval.get("task_id") or _DIST_TASK

    # idempotência: se a task já está encerrada, não refaz
    t = repo.tasks.get_task(dist_task)
    if t and t.get("status") in ("completed", "killed"):
        return {"advanced": False, "already": True,
                "message": "Gate 3 já aprovada; campanha já concluída."}

    # 1) Journey: aprovação
    _journey(dist_task, "approval_approved", "murillo", f"Gate 3 aprovada (approval {aid})")
    # 2) gera o pacote final de publicação MANUAL
    arquivo = distribution.gerar_pacote_publicacao_manual_vp(dist_task)
    _journey(dist_task, "file_generated", "agent",
             "pacote-publicacao-semana.md gerado (publicação MANUAL)", agent_id="midas",
             metadata={"arquivo": "_projetos/cerebro-jampa/posts/pacote-publicacao-semana.md"})
    _journey(dist_task, "manual_publication_package_created", "system",
             "Pacote de publicação manual pronto — nenhuma integração externa acionada",
             agent_id="midas")
    _log("workflow_advance",
         f"Gate 3 aprovada (approval {aid}) → pacote manual gerado; campanha concluída.",
         agent="midas")
    # 3) fecha a campanha: conclui a task de Distribuição (reusa lifecycle/digest)
    #    → entity_killed + ai_digest_created + digest via complete_task.
    res = task_lifecycle.complete_task(dist_task, note="Campanha concluída (Gate 3)", actor="murillo")

    return {"advanced": True, "completed": True, "arquivo": arquivo,
            "digest_text": res.get("digest_text", ""),
            "message": "Pacote manual de publicação gerado. Campanha concluída com digest."}


def _reject_gate3(approval: dict) -> dict:
    """Gate 3 rejeitada → NÃO gera pacote; mantém Distribuição disponível pra ajuste."""
    import repositories as repo
    aid = approval.get("id")
    dist_task = approval.get("task_id") or _DIST_TASK
    _log("workflow_reject",
         f"Gate 3 rejeitada (approval {aid}) → distribuição aguardando ajuste; "
         f"NÃO foi gerado pacote final.", agent="midas", status="rejected")
    _journey(dist_task, "approval_rejected", "murillo", f"Gate 3 rejeitada (approval {aid})")
    _journey(dist_task, "adjustment_required", "system",
             "Distribuição aguardando ajuste do Midas antes de novo Gate", agent_id="midas")
    try:
        repo.tasks.set_status(dist_task, "pending")
        repo.memories.add(
            "Distribuição da semana VP reprovada no Gate 3 — aguardando ajuste do Midas.",
            key="gate3_distribuicao_vp", kind="sinal")
    except Exception:
        pass
    return {"advanced": False, "rejected": True,
            "message": "Gate 3 rejeitada. Distribuição aguardando ajuste."}
