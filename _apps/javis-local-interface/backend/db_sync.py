"""db_sync.py — espelha os dados vivos (Markdown/JSON/rosters) no SQLite.

Não é fonte de verdade: lê o que já existe (mission_board, rosters de agentes) e
faz upsert no banco pra ficar CONSULTÁVEL. Idempotente. Chamado no boot do server.
Se qualquer parte falhar, engole o erro — o sistema segue nos arquivos.
"""
from __future__ import annotations


def seed_projects() -> None:
    import repositories as repo
    try:
        repo.projects.upsert("javis", "Javis", "Assistente pessoal e operacional do Murillo")
        repo.projects.upsert("vem-passear-jampa", "Vem Passear Jampa",
                             "Operação de marketing/turismo em João Pessoa")
    except Exception:
        pass


def seed_agents() -> None:
    import repositories as repo
    # Squad da Vem Passear (com contrato)
    try:
        import vp_squad
        for a in vp_squad.list_agents():
            repo.agents.upsert(a["id"], a["name"], a.get("role", ""), "vp",
                               a.get("input", ""), a.get("output", ""), a.get("naofaz", ""))
    except Exception:
        pass
    # Agentes da "mente" (software)
    try:
        from agents.specialized import get_agents_info
        for a in get_agents_info():
            repo.agents.upsert(a["id"], a.get("name", a["id"]), a.get("role", ""), "mente")
    except Exception:
        pass


def sync_tasks() -> int:
    """Espelha as tarefas do Quadro (mission_board) na tabela tasks. Retorna nº sincronizado."""
    import repositories as repo
    n = 0
    try:
        import mission_board
        for m in mission_board.get_missions():
            for node in m.get("nodes", []):
                repo.tasks.upsert(
                    ext_id=node.get("id", ""),
                    title=node.get("label", "")[:300],
                    status=node.get("status", "pending"),
                    mission=m.get("id", ""),
                    source="backlog",
                )
                n += 1
    except Exception:
        pass
    return n


def seed_workflows() -> None:
    import repositories as repo
    try:
        repo.workflows.upsert("pipeline-marketing-vp", "Pipeline Marketing — Vem Passear",
                              "vem-passear-jampa")
    except Exception:
        pass


def bootstrap() -> dict:
    """Roda tudo no boot. Retorna um resumo de contagens (pra log/diagnóstico)."""
    import db
    db.init_db()
    seed_projects()
    seed_agents()
    seed_workflows()
    n = sync_tasks()
    import repositories as repo
    return {
        "tasks_sync": n,
        "agents": repo.agents.count(),
        "projects": repo.projects.count(),
        "workflows": repo.workflows.count(),
    }
