"""ui_state.py — adaptador READ-ONLY de estado para a interface (Chainlit + Command Center).

Le os registries em data/ui/ e os manifestos em data/projects/ e entrega uma
forma unica para a UI. NUNCA escreve, NUNCA chama _brain nem executa nada — so
agrega o que ja existe (JSONs + modulos do backend). Seguro de importar a partir
do venv do Chainlit (3.11) ou do server.py (3.14).

Degrada com elegancia: se um arquivo faltar, retorna lista/dict vazio em vez de
quebrar a interface.
"""
from __future__ import annotations
import json
from pathlib import Path

# backend/ui_state.py -> sobe 1 nivel (app root) -> data/
_DATA = Path(__file__).resolve().parents[1] / "data"
_UI = _DATA / "ui"
_PROJ = _DATA / "projects"
# Skills reais espalhadas: _skills/ na raiz do Javis + skills forjadas no app.
_SKILLS_DIR = Path(__file__).resolve().parents[3] / "_skills"
_FORJADAS_DIR = Path(__file__).resolve().parents[1] / "_data" / "skills_forjadas"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


# --- Projetos ---------------------------------------------------------------

def get_projects() -> list[dict]:
    projs = _load(_UI / "project_registry.json", {}).get("projects", [])
    # Enriquece projetos EXTERNOS com o status real do pointer (project_registry.py)
    try:
        import project_registry as pr
        for p in projs:
            if p.get("tipo") == "externo":
                ext = pr.get_project(p.get("id"))
                if ext:
                    p["status"] = ext.get("status", p.get("status"))
                    p["_externo"] = {"fase": ext.get("fase_atual"), "skills_ativas": ext.get("skills_ativas"),
                                     "atualizado": ext.get("fonte_da_verdade_atualizada_em")}
    except Exception:
        pass
    return projs


def get_project(project_id: str) -> dict | None:
    for p in get_projects():
        if p.get("id") == project_id:
            return p
    return None


_VP_DATA = Path(__file__).resolve().parents[1] / "_data"


def vp_metrics() -> dict:
    """KPIs REAIS da Vem Passear a partir de _data/vp_*.json (read-only)."""
    clientes = _load(_VP_DATA / "vp_clientes.json", [])
    passeios = _load(_VP_DATA / "vp_passeios.json", [])
    conteudos = _load(_VP_DATA / "vp_conteudos.json", [])
    pauta = _load(_VP_DATA / "vp_pauta.json", [])
    clientes = clientes if isinstance(clientes, list) else []
    passeios = passeios if isinstance(passeios, list) else []
    receita = 0.0
    for p in passeios:
        try:
            receita += float(p.get("valor") or 0)
        except Exception:
            pass
    funil = {}
    for c in clientes:
        st = (c.get("status") or "novo")
        funil[st] = funil.get(st, 0) + 1
    return {
        "leads": len(clientes),
        "reservas": len(passeios),
        "passeios_vendidos": len(passeios),
        "receita": round(receita, 2),
        "criativos": len(conteudos) if isinstance(conteudos, list) else 0,
        "pauta": len(pauta) if isinstance(pauta, list) else 0,
        "funil_por_status": funil,
    }


def get_project_manifest(project_id: str) -> dict | None:
    """Manifesto detalhado (dashboards etc.), se existir em data/projects/.
    Para a Vem Passear, injeta os KPIs REAIS computados de _data/vp_*.json."""
    man = _load(_PROJ / f"{project_id}.json", None)
    if man and project_id == "vempassear" and isinstance(man.get("dashboards"), dict):
        m = vp_metrics()
        d = man["dashboards"]
        mapping = {"leads": "leads", "reservas": "reservas",
                   "passeios_vendidos": "passeios_vendidos", "receita": "receita",
                   "criativos": "criativos"}
        for dash_key, mkey in mapping.items():
            if dash_key in d and m.get(mkey) is not None:
                d[dash_key]["total"] = m[mkey]
                d[dash_key]["status"] = "real"
        man["_kpis_reais"] = m
    return man


def project_options() -> list[str]:
    """Nomes para o Select de Projeto Ativo (com fallback)."""
    nomes = [p["nome"] for p in get_projects() if p.get("nome")]
    return nomes or ["Geral"]


def project_id_by_name(nome: str) -> str:
    for p in get_projects():
        if p.get("nome") == nome:
            return p.get("id", "geral")
    return "geral"


# --- Squads -----------------------------------------------------------------

def get_squads(project_id: str | None = None) -> list[dict]:
    squads = _load(_UI / "squad_registry.json", {}).get("squads", [])
    if project_id:
        return [s for s in squads if s.get("projeto") == project_id]
    return squads


# --- Agentes ----------------------------------------------------------------

def get_agents(project_id: str | None = None) -> list[dict]:
    agents = _load(_UI / "agent_registry.json", {}).get("agents", [])
    if project_id:
        return [a for a in agents if a.get("projeto") == project_id]
    return agents


# --- Skills (parse READ-ONLY dos .md reais) ---------------------------------

def _parse_frontmatter(text: str) -> dict:
    """Lê frontmatter YAML simples (linhas 'chave: valor') entre os dois '---'."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    meta = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _section_text(text: str, header: str) -> str:
    """Primeiro parágrafo abaixo de um '## header'."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower() == f"## {header}".lower():
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    return lines[j].strip()
    return ""


def _parse_skill(path: Path, categoria: str) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"id": path.stem, "nome": path.stem, "descricao": "", "categoria": categoria,
                "status": "?", "agente": None, "arquivo": path.name}
    fm = _parse_frontmatter(text)
    nome = fm.get("name") or _first_heading(text) or path.stem
    # tira prefixo "Skill: " de títulos
    nome = nome.replace("Skill:", "").strip() or path.stem
    desc = fm.get("description") or _section_text(text, "Objetivo") or _section_text(text, "IDENTIDADE")
    return {
        "id": path.stem,
        "nome": nome,
        "descricao": (desc or "")[:240],
        "categoria": categoria,
        "status": fm.get("status", "ativa"),
        "agente": fm.get("agente"),
        "arquivo": path.name,
    }


def get_scripts() -> list[dict]:
    """Catálogo dos scripts Python do backend (ingerido por docstring)."""
    return _load(_UI / "scripts_registry.json", {}).get("scripts", [])


def get_skills() -> list[dict]:
    """Catálogo de skills reais: _skills/*.md (agente/processo) + skills forjadas."""
    out: list[dict] = []
    if _SKILLS_DIR.exists():
        for p in sorted(_SKILLS_DIR.glob("*.md")):
            if p.stem.startswith("_"):  # pula _index.md
                continue
            cat = "Agente" if p.stem.startswith("agente-") else "Processo"
            out.append(_parse_skill(p, cat))
    if _FORJADAS_DIR.exists():
        for p in sorted(_FORJADAS_DIR.glob("*.md")):
            out.append(_parse_skill(p, "Forjada"))
    return out


# --- Estado agregado (para o Command Center) --------------------------------

def full_state() -> dict:
    return {
        "projects": get_projects(),
        "squads": get_squads(),
        "agents": get_agents(),
        "skills": get_skills(),
    }
