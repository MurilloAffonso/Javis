"""skill_forge.py — pipeline "Nero": transcrição de expert → SKILL.md (rascunho).

O mecanismo-assinatura do vídeo: absorve o conteúdo de um expert (ou do próprio
Murillo) e converte o FRAMEWORK MENTAL numa skill acionável, no padrão do
CEREBRO.JAMPA. Emite um Score de Fidelidade (quão fiel capturou o framework).

Governança: IA rascunha, Murillo aprova. A skill sai como RASCUNHO numa pasta
local do Javis (não grava direto no vault, não toca o git do CEREBRO.JAMPA).
Murillo revisa e move pra skills/ quando aprovar.
"""
from __future__ import annotations
import os
import re
import unicodedata
from datetime import date
from pathlib import Path

# Saída dos rascunhos (dentro do Javis — não escreve no vault por padrão).
FORGE_OUT = Path(os.environ.get(
    "JAMPA_FORGE_OUT",
    str(Path(__file__).resolve().parent.parent / "_data" / "skills_forjadas"),
))

_SYSTEM = """\
Você é o pipeline Nero do Jampa Jarvis: extrai o FRAMEWORK MENTAL de um conteúdo
de especialista e o converte numa SKILL acionável para um agente de IA, no padrão
do CEREBRO.JAMPA (vault da Vem Passear em Jampa).

Não resuma o conteúdo — extraia o MÉTODO acionável (passos, gatilhos, regras) que
um agente possa EXECUTAR. Português do Brasil.

Formato EXATO da resposta:
FIDELIDADE: <0-100>
---
---
name: <slug-kebab-case>
description: <1 linha do que a skill faz>
version: "1.0"
status: rascunho
origem: skill_forge
atualizado: "<AAAA-MM-DD>"
---

# Skill: <Nome>

## IDENTIDADE
<o papel/quando usar>

## O Que Faz
- <itens>

## O Que NÃO Faz
- <itens>

## PROCESSO
<passos numerados acionáveis>

## REGRAS INVIOLÁVEIS
<regras>
"""


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "skill-forjada"


def forge(transcricao: str, tema: str = "") -> dict:
    """Forja uma skill a partir da transcrição. Retorna {status, score, nome, path, skill_md}."""
    transcricao = (transcricao or "").strip()
    if not transcricao:
        return {"status": "error", "message": "Transcrição vazia."}
    user = (f"Tema/foco: {tema}\n\n" if tema else "") + f"Conteúdo do expert:\n{transcricao[:14000]}"
    from llm_providers import call_openai
    try:
        raw = call_openai(
            [{"role": "system", "content": _SYSTEM.replace("<AAAA-MM-DD>", date.today().isoformat())},
             {"role": "user", "content": user}],
            temperature=0.3,
        )
    except Exception as e:
        return {"status": "error", "message": f"Falha ao forjar: {e}"}

    # separa FIDELIDADE: NN  do corpo
    score = None
    m = re.search(r"FIDELIDADE:\s*(\d{1,3})", raw)
    if m:
        score = min(100, int(m.group(1)))
    skill_md = re.sub(r"^.*?---\s*", "", raw, count=1, flags=re.DOTALL).strip() if "---" in raw else raw.strip()

    # nome a partir do frontmatter name:
    nm = re.search(r"name:\s*([a-z0-9\-]+)", skill_md)
    nome = nm.group(1) if nm else _slug(tema or "skill-forjada")

    FORGE_OUT.mkdir(parents=True, exist_ok=True)
    path = FORGE_OUT / f"{nome}.md"
    try:
        path.write_text(skill_md, encoding="utf-8")
    except Exception as e:
        return {"status": "error", "message": f"Forjada mas não salvou: {e}", "skill_md": skill_md}

    return {
        "status": "ok",
        "score": score,
        "nome": nome,
        "path": str(path),
        "skill_md": skill_md,
        "revisar": (score is None or score < 75),
    }
