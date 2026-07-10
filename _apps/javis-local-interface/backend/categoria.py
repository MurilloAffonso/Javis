"""categoria.py — classificação determinística de escopo do conhecimento.

Cada chunk do RAG é rotulado, SEM modelo e SEM latência, em uma de três
categorias de escopo:

  • pessoal — o DNA cognitivo do Murillo (quem ele é: voz, método, valores).
  • projeto — conhecimento operacional DO Javis (o resto interno).
  • vp / externo — projetos externos plugados POR REGISTRO (Cérebro Jampa /
    Vem Passear Jampa). A fronteira vem do `project_registry`, não de hardcode.

O sinal é o PATH do chunk — que já carrega a fronteira: `knowledge_hybrid._relpath`
prefixa vaults externos com `[NomeDoVault] ...`, enquanto arquivos do Javis ficam
com caminho relativo puro. Isso casa com a regra do CLAUDE.md: projetos externos
só entram "por registro", com fronteira clara.

Determinístico e testável: `de_path(path) -> str`.
"""
from __future__ import annotations

import re
from pathlib import Path

# Prefixos (relativos à raiz do Javis) que contam como PESSOAL. Uma linha de
# ajuste: hoje só o DNA cognitivo do Murillo. Comparado em minúsculas, com '/'.
PESSOAL_PREFIXES: tuple[str, ...] = ("_memoria/dna/",)
VP_PREFIXES: tuple[str, ...] = (
    "_projetos/cerebro-jampa/",
    "_projetos/vem-passear/",
    "_projetos/vempassear/",
)

# Categoria default para o que é interno do Javis e não é pessoal.
DEFAULT = "projeto"

# Categoria para prefixo externo `[vault]` sem correspondência no registro.
EXTERNO_DESCONHECIDO = "externo"

_EXT_RE = re.compile(r"^\[(.+?)\]")


def _registry_map() -> dict[str, str]:
    """{nome_da_pasta_do_vault -> categoria} lido do project_registry (fonte da
    verdade da fronteira). cerebro-jampa -> 'vp'. Falha silenciosa = mapa vazio."""
    m: dict[str, str] = {}
    try:
        import project_registry as pr
        for slug, cfg in getattr(pr, "REGISTRY", {}).items():
            if not isinstance(cfg, dict):
                continue
            p = cfg.get("path")
            nome = Path(p).name if p else slug
            m[nome] = cfg.get("categoria", slug)
    except Exception:
        pass
    return m


def de_path(path: str) -> str:
    """Classifica um chunk pelo seu path. Puro e determinístico.

    >>> de_path("[CEREBRO.JAMPA] docs/fonte.md")   # externo, por registro
    'vp'
    >>> de_path("_memoria/dna/thiago-finch.md")     # DNA cognitivo do Murillo
    'pessoal'
    >>> de_path("_projetos/javis.md")               # interno do Javis
    'projeto'
    """
    if not path:
        return DEFAULT
    raw = path.strip()
    m = _EXT_RE.match(raw)
    if m:
        vault = m.group(1).strip()
        return _registry_map().get(vault, EXTERNO_DESCONHECIDO)
    low = raw.replace("\\", "/").lstrip("/").lower()
    for pre in PESSOAL_PREFIXES:
        if low.startswith(pre):
            return "pessoal"
    for pre in VP_PREFIXES:
        if low.startswith(pre):
            return "vp"
    return DEFAULT
