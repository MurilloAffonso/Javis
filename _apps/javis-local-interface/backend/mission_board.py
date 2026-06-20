"""
mission_board.py — Quadro de orquestramento real, derivado do backlog do
Codex (_data/codex_backlog.md) e do log de execucao. Sem dados inventados:
cada missao = uma secao do backlog; cada node = uma tarefa daquela secao.
"""
from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime

DATA_DIR  = Path(__file__).resolve().parent.parent / "_data"
BACKLOG   = DATA_DIR / "codex_backlog.md"
ORCH_LOG  = DATA_DIR / "codex_orch_log.txt"

_SECTION_RE = re.compile(r"^##\s+(.+)$")
_TASK_RE    = re.compile(r"^\s*-\s*\[( |x)\]\s*(.+)$")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _last_activity() -> str | None:
    if not ORCH_LOG.exists():
        return None
    try:
        lines = ORCH_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in reversed(lines):
            m = re.match(r"^(\d{2}:\d{2}:\d{2})\s", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def parse_backlog() -> list[dict]:
    """Le o backlog real e devolve missoes (secoes) com suas tarefas (nodes)."""
    if not BACKLOG.exists():
        return []
    missions = []
    current = None
    for raw in BACKLOG.read_text(encoding="utf-8").splitlines():
        sm = _SECTION_RE.match(raw)
        if sm:
            current = {"title": sm.group(1).strip(), "tasks": []}
            missions.append(current)
            continue
        tm = _TASK_RE.match(raw)
        if tm and current is not None:
            done = tm.group(1) == "x"
            text = tm.group(2).strip()
            current["tasks"].append({"done": done, "text": text})

    last_activity = _last_activity()
    out = []
    for m in missions:
        tasks = m["tasks"]
        if not tasks:
            continue
        total = len(tasks)
        done_n = sum(1 for t in tasks if t["done"])
        pct = round(100 * done_n / total)
        out.append({
            "id": _slug(m["title"]),
            "name": m["title"],
            "pct": pct,
            "active": 0 < done_n < total or (done_n == 0 and pct == 0),
            "status": "concluida" if pct == 100 else ("running" if done_n > 0 else "pending"),
            "tasks_done": done_n,
            "tasks_total": total,
            "last_activity": last_activity,
            "nodes": [
                {
                    "id": f"{_slug(m['title'])}-t{i}",
                    "label": t["text"][:48] + ("…" if len(t["text"]) > 48 else ""),
                    "full_text": t["text"],
                    "status": "done" if t["done"] else "pending",
                    "pct": 100 if t["done"] else 0,
                }
                for i, t in enumerate(tasks)
            ],
        })
    # marca como ativa a primeira missao que nao esta 100% concluida
    found_active = False
    for m in out:
        if m["pct"] < 100 and not found_active:
            m["active"] = True
            found_active = True
        else:
            m["active"] = False
    return out


_AREA_LABELS = {
    "vendas": "Vendas", "conteudo": "Conteúdo", "tecnico": "Técnico", "estrategia": "Estratégia",
}


def _treinamento_mission() -> dict | None:
    """Missao sintetica: esquadroes de estudo coletando material por area
    (_treinamento). Nao vem de checklist — vem da contagem real de arquivos."""
    try:
        import trend_scout
        areas = trend_scout.all_status()
    except Exception:
        return None
    if not areas:
        return None
    total_resumos_alvo = max(len(areas), 1)  # meta simbolica: 1 resumo/area = "estudado"
    done_n = sum(1 for a in areas if a["resumos"] > 0)
    pct = round(100 * done_n / total_resumos_alvo)
    nodes = [
        {
            "id": f"treinamento-{a['area']}",
            "label": f"{_AREA_LABELS.get(a['area'], a['area'])}: {a['entrada']} coletados, {a['resumos']} resumidos",
            "full_text": f"Área {a['area']} — {a['entrada']} itens em _entrada, {a['resumos']} resumos no RAG",
            "status": "done" if a["resumos"] > 0 else ("pending" if a["entrada"] == 0 else "running"),
            "pct": 100 if a["resumos"] > 0 else (50 if a["entrada"] > 0 else 0),
        }
        for a in areas
    ]
    return {
        "id": "esquadrao-de-estudo",
        "name": "Esquadrão de Estudo (_treinamento)",
        "pct": pct,
        "active": False,
        "status": "concluida" if pct == 100 else ("running" if any(a["entrada"] > 0 for a in areas) else "pending"),
        "tasks_done": done_n,
        "tasks_total": total_resumos_alvo,
        "last_activity": None,
        "nodes": nodes,
    }


def _projetos_externos_mission() -> dict | None:
    """Missao sintetica: estado dos projetos externos plugados via registry."""
    try:
        import project_registry
        projetos = project_registry.list_projects()
    except Exception:
        return None
    if not projetos:
        return None
    done_n = sum(1 for p in projetos if p.get("status") == "online")
    total = len(projetos)
    pct = round(100 * done_n / total) if total else 0
    nodes = [
        {
            "id": f"projeto-{p['slug']}",
            "label": f"{p.get('nome', p['slug'])}: fase {p.get('fase_atual', '?')}",
            "full_text": f"{p.get('nome', p['slug'])} — {p.get('skills_ativas', 0)}/{p.get('skills_total', 0)} skills ativas",
            "status": "done" if p.get("status") == "online" else "pending",
            "pct": 100 if p.get("status") == "online" else 0,
        }
        for p in projetos
    ]
    return {
        "id": "projetos-externos",
        "name": "Projetos Externos Conectados",
        "pct": pct,
        "active": False,
        "status": "running" if 0 < pct < 100 else ("concluida" if pct == 100 else "pending"),
        "tasks_done": done_n,
        "tasks_total": total,
        "last_activity": None,
        "nodes": nodes,
    }


def get_missions() -> list[dict]:
    """Quadro de orquestramento do projeto inteiro: backlog do Codex + esquadroes
    de estudo + projetos externos conectados. Tudo derivado de dado real."""
    out = parse_backlog()
    for extra in (_treinamento_mission(), _projetos_externos_mission()):
        if extra:
            out.append(extra)
    return out


def get_mission_nodes(mission_id: str) -> list[dict]:
    for m in get_missions():
        if m["id"] == mission_id:
            return m["nodes"]
    return []


_NODE_ID_RE = re.compile(r"^(.+)-t(\d+)$")


def set_task_done(mission_id: str, node_id: str, done: bool) -> bool:
    """Marca/desmarca o checkbox de uma tarefa real no backlog do Codex.

    Só funciona para missoes derivadas do backlog (cada node tem indice
    sequencial dentro da secao). Missoes sinteticas (treinamento, projetos
    externos) sao calculadas a partir de outro estado e nao tem checkbox pra
    editar — chamar aqui pra elas sempre devolve False.
    """
    m = _NODE_ID_RE.match(node_id)
    if not m or not BACKLOG.exists():
        return False
    task_idx = int(m.group(2))
    lines = BACKLOG.read_text(encoding="utf-8").splitlines()
    current_slug = None
    task_counter = -1
    for i, raw in enumerate(lines):
        sm = _SECTION_RE.match(raw)
        if sm:
            current_slug = _slug(sm.group(1).strip())
            task_counter = -1
            continue
        if _TASK_RE.match(raw) and current_slug is not None:
            task_counter += 1
            if current_slug == mission_id and task_counter == task_idx:
                mark = "x" if done else " "
                lines[i] = re.sub(r"^(\s*-\s*\[)( |x)(\])", rf"\g<1>{mark}\g<3>", raw, count=1)
                BACKLOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return True
    return False
