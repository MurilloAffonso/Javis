"""vp_squad.py — Squad de marketing da Vem Passear (5 agentes com CONTRATO).

Implementa os 5 contratos de `_projetos/cerebro-jampa/agentes-contratos.md`
(revisão 20/06): cada agente é uma tarefa atômica com Input → Output, fronteira
explícita (O que faz / NÃO faz) e ferramentas. O "Não faz" entra no system prompt
como regra dura — é o que mata o "quem faz o quê confuso".

Roda no cérebro único (Claude pela assinatura, via claude_brain). Self-contained:
o contrato é inline e o grounding vem dos arquivos LOCAIS do projeto
(`_projetos/cerebro-jampa/`), sem depender do vault externo CEREBRO.JAMPA.
Regra Ouro: nunca inventar preço/maré/vaga — se faltar, [CONFIRMAR COM MURILLO].
"""
from __future__ import annotations
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
CJ = JAVIS_ROOT / "_projetos" / "cerebro-jampa"

# ── Os 5 agentes (contratos de agentes-contratos.md) ──────────────────────
AGENTS: dict[str, dict] = {
    "olheiro": {
        "name": "Olheiro", "icon": "🔭", "role": "Inteligência (leve)", "group": "inteligencia",
        "input":  "semana atual + pilares da linha editorial",
        "output": "3-5 referências/tendências da semana (formatos, áudios, ganchos) pra Nova",
        "faz":    "capta trends/áudios de turismo que estão bombando; aponta formatos que performam; traz inspiração (não cópia)",
        "naofaz": "copiar concorrente; criar conteúdo da marca; publicar; responder cliente",
        "tools":  "Instagram/TikTok (busca), pesquisar_redes",
        "ground": [],
    },
    "nova": {
        "name": "Nova", "icon": "🎨", "role": "Conteúdo (pauta + copy)", "group": "conteudo",
        "input":  "briefing do Murillo (maré, agenda, vagas, fotos) + referências do Olheiro",
        "output": "pauta-semana.md: 3+ posts com dia, pilar, formato, gancho, LEGENDA final + CTA + hashtags e material visual",
        "faz":    "escolhe pilares (proporção da linha editorial, máx. 2 de venda a cada 10); cria gancho 3s e formato; escreve a copy no tom caloroso/local; usa os CTAs padrão (MARÉ/COMBO/SEIXAS)",
        "naofaz": "produzir a arte; publicar; inventar preço/horário/maré; prometer vaga sem o Murillo confirmar",
        "tools":  "linha-editorial.md, Claude (assinatura)",
        "ground": ["linha-editorial.md"],
    },
    "estudio": {
        "name": "Estúdio", "icon": "🖼️", "role": "Criativos", "group": "design",
        "input":  "pauta aprovada + copy + fotos de imagens/_FOTOS-AQUI/",
        "output": "peças prontas em outputs/ (carrossel/card/Reel)",
        "faz":    "gera as artes (gerar_carrossel.py/Canva/Claude Design); adapta por formato; aplica a identidade visual da marca",
        "naofaz": "definir verba; publicar; alterar a copy aprovada",
        "tools":  "gerar_carrossel.py, gerar_card_foto.py, Canva, Claude Design",
        "ground": [],
    },
    "midas": {
        "name": "Midas", "icon": "📈", "role": "Distribuição & conversão (WhatsApp)", "group": "trafego",
        "input":  "peças + copy finais aprovadas (Gate 2); mensagens recebidas no WhatsApp",
        "output": "posts publicados/agendados + marcação do que impulsionar + RASCUNHOS de resposta de WhatsApp prontos pro Murillo enviar",
        "faz":    "agenda/publica; marca posts com potencial de anúncio e sugere segmentação; monta a resposta do WhatsApp usando os templates",
        "naofaz": "ENVIAR a resposta sozinho (o Murillo dá o envio final); inventar disponibilidade/preço; aprovar verba sozinho; criar arte/copy",
        "tools":  "Meta Business Suite, Meta Ads, templates-whatsapp.md, WhatsApp",
        "ground": ["posts/templates-whatsapp.md"],
        "extra":  "REGRA DE SEGURANÇA: toda resposta com preço, maré, vaga ou data sai como RASCUNHO pro Murillo conferir antes de enviar. Nunca dê o envio final você mesmo.",
    },
    "analista": {
        "name": "Analista", "icon": "📊", "role": "Resultado (dados)", "group": "dados",
        "input":  "métricas da semana (alcance, salvamentos, cliques no WhatsApp, reservas)",
        "output": "decisão da semana (o que repetir, o que cortar) registrada em pauta-semana.md → vira o briefing da semana seguinte",
        "faz":    "lê o desempenho de cada post; aponta os 3 que mais geraram WhatsApp/reserva; recomenda o que a Nova deve repetir/variar",
        "naofaz": "inventar número; publicar; decidir a estratégia sozinho (entrega pro Murillo decidir)",
        "tools":  "Instagram Insights, planilha simples, Claude",
        "ground": [],
    },
}

_REGRA_OURO = (
    "\n\n## REGRA OURO (inviolável)\nNunca invente preço, maré, vaga, horário, "
    "duração, ponto de embarque ou depoimento. Se o dado não estiver no contexto, "
    "escreva [CONFIRMAR COM MURILLO: <o que falta>] em vez de chutar. Responda em "
    "português do Brasil, direto e operacional — entregue o trabalho pronto."
)

_CAP = 3500  # chars por arquivo de grounding (prompt bounded)


def _read(rel: str, cap: int = _CAP) -> str:
    try:
        t = (CJ / rel).read_text(encoding="utf-8", errors="replace")
        return t[:cap] + "\n[...]" if len(t) > cap else t
    except Exception:
        return ""


def list_agents() -> list[dict]:
    """Roster pro dashboard/endpoint."""
    return [
        {"id": aid, "name": a["name"], "icon": a["icon"], "role": a["role"],
         "group": a["group"], "input": a["input"], "output": a["output"],
         "naofaz": a["naofaz"]}
        for aid, a in AGENTS.items()
    ]


def _system_prompt(agent_id: str) -> str:
    a = AGENTS[agent_id]
    sys = (
        f"Você é {a['name']} ({a['role']}) da Vem Passear Jampa — turismo em João "
        f"Pessoa/PB (piscinas naturais, catamarã, pôr do sol). Assistente operacional "
        f"de Murillo Affonso; trate-o por 'senhor'.\n\n"
        f"## SEU CONTRATO (respeite à risca)\n"
        f"- INPUT: {a['input']}\n"
        f"- OUTPUT: {a['output']}\n"
        f"- O que você FAZ: {a['faz']}\n"
        f"- O que você NÃO FAZ (NUNCA cruze esta linha): {a['naofaz']}\n"
        f"- Ferramentas: {a['tools']}\n"
    )
    if a.get("extra"):
        sys += f"\n{a['extra']}\n"
    grounds = [_read(g) for g in a.get("ground", [])]
    grounds = [g for g in grounds if g.strip()]
    if grounds:
        sys += "\n## CONHECIMENTO (fonte de verdade — use só isto)\n" + "\n\n".join(grounds)
    return sys + _REGRA_OURO


def run(agent_id: str, tarefa: str, contexto: str = "") -> dict:
    """Executa um agente do squad na assinatura (claude_brain). Retorna {agent, name, result}."""
    agent_id = (agent_id or "").strip().lower()
    if agent_id not in AGENTS:
        return {"status": "error", "message": f"Agente desconhecido: {agent_id}"}
    a = AGENTS[agent_id]
    import claude_brain
    if not claude_brain.available():
        return {"status": "error", "agent": agent_id, "name": a["name"],
                "message": "Claude (assinatura) indisponível, senhor."}
    out = claude_brain.answer(tarefa, context=contexto, system=_system_prompt(agent_id), timeout=180)
    if not (out or "").strip():
        return {"status": "error", "agent": agent_id, "name": a["name"],
                "message": "Não consegui gerar agora (cota/assinatura), senhor."}
    return {"status": "ok", "agent": agent_id, "name": a["name"], "result": out.strip()}
