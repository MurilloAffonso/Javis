"""
project_registry.py — Javis como orquestrador mestre de projetos externos.

Le (somente leitura, nunca escreve) o manifesto e as skills de projetos
conectados que vivem FORA do repo do Javis. O Javis nao absorve esses
projetos — ele aponta para eles (modelo registry/pointer).

Projeto conectado hoje: CEREBRO.JAMPA (Vem Passear em Jampa), repo
standalone maduro em Documents\\CEREBRO.CLAUDE\\CEREBRO.JAMPA.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

REGISTRY = {
    "cerebro-jampa": {
        "path": Path(r"C:\Users\noteacer\Documents\CEREBRO.CLAUDE\CEREBRO.JAMPA"),
        "manifest_file": "project-manifest.json",
        "skills_manifest": "skills/manifest.json",
        "fonte_da_verdade": "FONTE-DA-VERDADE.md",
        "categoria": "vp",   # escopo do RAG (categoria.py): Vem Passear Jampa = externo por registro
    },
}


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_project(slug: str) -> dict | None:
    """Le o estado atual do projeto externo a partir do disco. Sem cache —
    sempre reflete o que esta no repo deles agora."""
    cfg = REGISTRY.get(slug)
    if not cfg:
        return None
    root = cfg["path"]
    if not root.exists():
        return {"slug": slug, "status": "offline", "erro": f"caminho nao encontrado: {root}"}

    manifest = _read_json(root / cfg["manifest_file"]) or {}
    skills_manifest = _read_json(root / cfg["skills_manifest"]) or {}
    skills = skills_manifest.get("skills", [])
    ativas = [s for s in skills if s.get("status") == "ativo"]

    fonte = root / cfg["fonte_da_verdade"]
    fonte_mtime = None
    if fonte.exists():
        fonte_mtime = datetime.fromtimestamp(fonte.stat().st_mtime).strftime("%Y-%m-%d")

    return {
        "slug": slug,
        "status": "online",
        "nome": manifest.get("projeto", slug),
        "empresa": manifest.get("empresa", ""),
        "fase_atual": manifest.get("fase_atual", "?"),
        "descricao_fase": manifest.get("descricao_fase", ""),
        "atualizado_em": manifest.get("atualizado_em", ""),
        "fonte_da_verdade_atualizada_em": fonte_mtime,
        "modelo_ia": manifest.get("modelo_ia", {}),
        "skills_total": len(skills),
        "skills_ativas": len(ativas),
        "skills_categorias": sorted({s.get("categoria") for s in ativas if s.get("categoria")}),
        "skills_lista": [
            {"id": s["id"], "categoria": s.get("categoria"), "papel": s.get("papel"), "risco": s.get("risco")}
            for s in ativas
        ],
        "validacao": manifest.get("validacao", {}),
        "contato_responsavel": manifest.get("contato_responsavel", {}),
        "path": str(root),
    }


def list_projects() -> list[dict]:
    out = []
    for slug in REGISTRY:
        p = get_project(slug)
        if p:
            out.append(p)
    return out
