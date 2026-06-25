"""resumir_treino.py — fecha o ciclo de Treino SEM NotebookLM manual.

Lê os arquivos de `_treinamento/<area>/_entrada` que ainda NÃO têm resumo e
resume cada um com o Claude (assinatura, via claude_brain), gravando em
`_resumos/` com o MESMO nome. Depois reindexa o RAG (knowledge.build_index).

Read+write SÓ dentro de `_treinamento/`. Nada externo, nada destrutivo (só cria
arquivos novos em _resumos; nunca apaga nem sobrescreve _entrada).
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime

TREINO_DIR = Path(__file__).resolve().parents[3] / "_treinamento"

_SYS = (
    "Você resume material de estudo para Murillo. Contexto do negócio: Vem Passear "
    "Jampa (turismo receptivo em João Pessoa) e o assistente pessoal Javis. "
    "Seja objetivo e prático, em português do Brasil:\n"
    "1) Resumo em 3-5 linhas;\n"
    "2) 3-5 aprendizados aplicáveis ao negócio;\n"
    "3) 1-2 ações concretas.\n"
    "Sem enrolação."
)


def _pending(area: str) -> list[Path]:
    ent = TREINO_DIR / area / "_entrada"
    res = TREINO_DIR / area / "_resumos"
    if not ent.is_dir():
        return []
    done = {f.name for f in res.glob("*.md")} if res.is_dir() else set()
    return [f for f in sorted(ent.glob("*.md")) if f.name not in done]


def resumir_area(area: str, limite: int = 5) -> dict:
    """Resume até `limite` arquivos pendentes da área. Retorna o relatório."""
    import claude_brain
    if not claude_brain.available():
        return {"area": area, "error": "Claude (assinatura) indisponível", "resumidos": 0}

    res_dir = TREINO_DIR / area / "_resumos"
    res_dir.mkdir(parents=True, exist_ok=True)
    pendentes = _pending(area)
    alvo = pendentes[:max(1, limite)]
    feitos = []

    for f in alvo:
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        resumo = claude_brain.answer(
            f"Resuma este material de estudo (área: {area}):\n\n{txt[:6000]}",
            system=_SYS, timeout=180,
        )
        if not resumo or not resumo.strip():
            continue
        out = (
            f"# Resumo: {f.stem}\n\n"
            f"Área: {area}\n"
            f"Resumido em: {datetime.now():%Y-%m-%d} (Javis / Claude assinatura)\n"
            f"Origem: _entrada/{f.name}\n\n"
            f"{resumo.strip()}\n"
        )
        (res_dir / f.name).write_text(out, encoding="utf-8")
        feitos.append(f.name)

    # Reindexa o RAG pra os resumos entrarem na base (best effort)
    if feitos:
        try:
            import knowledge
            knowledge.build_index(force=True)
        except Exception:
            pass

    return {
        "area": area,
        "resumidos": len(feitos),
        "arquivos": feitos,
        "pendentes_restantes": len(_pending(area)),
    }
