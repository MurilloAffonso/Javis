"""task_lifecycle.py — conclusão/morte da entidade-tarefa + AI Digest.

Fecha o ciclo de vida: nascimento → eventos → aprovação → avanço → CONCLUSÃO/MORTE
→ DIGEST. O digest é montado por TEMPLATE LOCAL a partir do que já temos (task +
Journey Log + aprovações) — SEM chamar LLM/API (sem gastar cota). Idempotente:
task já encerrada não é re-concluída nem re-loga.
"""
from __future__ import annotations
from datetime import datetime


def _parse(ts: str | None):
    if not ts:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts[:19], fmt)
        except Exception:
            pass
    return None


def _human_delta(a, b) -> str:
    if not a or not b:
        return "tempo indeterminado"
    secs = max(0, int((b - a).total_seconds()))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}min"
    if secs < 86400:
        return f"{secs // 3600}h{(secs % 3600) // 60}min"
    return f"{secs // 86400}d"


def generate_task_digest(task_id: str) -> str:
    """Resumo em texto da jornada da task — template local, sem LLM."""
    import repositories as repo
    task = repo.tasks.get_task(task_id) or {}
    events = repo.task_events.list_by_task(task_id)
    aps = repo.approvals.by_task(task_id)

    title = task.get("title") or task_id
    status = task.get("status") or "?"
    tipos = [e["event_type"] for e in events]

    quem = sorted({(e.get("agent_id") or e.get("actor") or "").strip()
                   for e in events if (e.get("agent_id") or e.get("actor"))})
    quem = [q for q in quem if q] or ["system"]

    if any(a.get("status") == "approved" for a in aps):
        aprov = "aprovada (Gate humano)"
    elif any(a.get("status") == "rejected" for a in aps):
        aprov = "rejeitada — exigiu ajuste"
    else:
        aprov = "sem aprovação registrada"

    ini = _parse(events[0]["created_at"] if events else task.get("created_at"))
    fim = _parse(task.get("completed_at") or task.get("killed_at")
                 or (events[-1]["created_at"] if events else None))
    dur = _human_delta(ini, fim)

    riscos = []
    if any(a.get("status") == "rejected" for a in aps):
        riscos.append("houve rejeição no Gate (retrabalho)")
    if "approval_requested" in tipos and not ({"approval_approved", "approval_rejected"} & set(tipos)):
        riscos.append("aprovação ficou pendente")
    riscos_txt = "; ".join(riscos) or "nenhum gargalo evidente"

    if "design_task_unlocked" in tipos:
        prox = "produzir os criativos (Design/Estúdio)"
    elif status in ("completed", "killed"):
        prox = "tarefa encerrada — nada pendente"
    elif "approval_requested" in tipos:
        prox = "aguardar/decidir o Gate"
    else:
        prox = "seguir o pipeline"

    feito = []
    if "file_generated" in tipos:
        feito.append("conteúdo/arquivo gerado")
    if "approval_approved" in tipos:
        feito.append("Gate aprovado")
    if "design_task_unlocked" in tipos:
        feito.append("produção destravada")
    feito_txt = ", ".join(feito) or "fluxo iniciado"

    return (
        f"# Digest — {title}\n"
        f"- Status: {status} | duração: {dur}\n"
        f"- O que foi feito: {feito_txt}\n"
        f"- Quem participou: {', '.join(quem)}\n"
        f"- Principais eventos: {' → '.join(tipos) if tipos else '—'}\n"
        f"- Aprovação: {aprov}\n"
        f"- Gargalos/perigos: {riscos_txt}\n"
        f"- Próximo passo recomendado: {prox}"
    )


def complete_task(task_id: str, note: str = "", actor: str = "murillo") -> dict:
    """Encerra a entidade: completed/killed + eventos + digest + log. Idempotente."""
    import repositories as repo
    task = repo.tasks.get_task(task_id)
    if not task:
        return {"ok": False, "error": f"task '{task_id}' não encontrada"}
    if task.get("status") in ("completed", "killed"):
        return {"ok": False, "error": "task já encerrada", "status": task["status"],
                "digest_text": task.get("digest_text", "")}

    # 1) marca completed/killed
    repo.tasks.complete_task(task_id, actor=actor, note=note)
    # 2) eventos de conclusão e morte da entidade
    repo.task_events.add_event(task_id, "task_completed", actor,
                               note or "Tarefa concluída",
                               metadata={"note": note} if note else None)
    repo.task_events.add_event(task_id, "entity_killed", "system",
                               "Entidade encerrada (ciclo de vida completo)")
    # 3) digest (template local, sem LLM) — lê os eventos já com a conclusão
    digest = generate_task_digest(task_id)
    repo.tasks.update_digest(task_id, digest)
    repo.task_events.add_event(task_id, "ai_digest_created", "system",
                               "Digest da entidade gerado")
    # 4) action_logs
    try:
        repo.logs.add(source="frontend", intent="task_complete", agent="",
                      message=f"Task {task_id} concluída/encerrada"
                              + (f" (obs: {note[:80]})" if note else ""),
                      status="completed", approved=None)
    except Exception:
        pass

    t = repo.tasks.get_task(task_id)
    return {"ok": True, "status": t["status"], "completed_at": t.get("completed_at"),
            "killed_at": t.get("killed_at"), "digest_text": digest}
