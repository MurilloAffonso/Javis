"""jampa_squad.py — runtime de agentes nomeados (o "Jampa Jarvis").

Carrega as skills do vault CEREBRO.JAMPA (frameworks em markdown) como agentes
NOMEADOS no estilo do vídeo (Orion, Hunter, Atlas, LNS, Nova, ...), aterrados na
FONTE-DA-VERDADE do Vem Passear, rodando no cérebro forte (gpt-4o / Opus) —
NÃO no Ollama dos agentes genéricos de software.

Governança (decidido: AUTÔNOMO COM TRAVAS):
- Regra Ouro: todo dado de preço/roteiro/fato vem do _conhecimento/. O agente
  nunca inventa; se faltar, marca [CONFIRMAR COM MURILLO].
- Vault é lido READ-ONLY (não modifica a governança do Jampa).
"""
from __future__ import annotations
import os
import re
from pathlib import Path

# Caminho do vault CEREBRO.JAMPA (configurável). Read-only.
JAMPA_VAULT = Path(os.environ.get(
    "JAMPA_VAULT",
    r"C:\Users\noteacer\Documents\CEREBRO.CLAUDE\CEREBRO.JAMPA",
))
SKILLS_DIR = JAMPA_VAULT / "skills"
CONHECIMENTO_DIR = JAMPA_VAULT / "_conhecimento"

# Roster: nome Jarvis → papel + skills do Jampa que o compõem.
ROSTER: dict[str, dict] = {
    "Orion":   {"role": "Orquestrador mestre", "icon": "🧠", "group": "orquestracao",
                "skills": ["orquestrador-projeto-turismo"]},
    "Hunter":  {"role": "Estrategista comercial", "icon": "🎯", "group": "vendas",
                "skills": ["agente-comercial-jampa", "qualificacao-lead"]},
    "Atlas":   {"role": "Pesquisa e espionagem", "icon": "🔭", "group": "pesquisa",
                "skills": ["radar-concorrentes-social", "captura-referencias-visuais"]},
    "LNS":     {"role": "Nutrição e follow-up", "icon": "💧", "group": "vendas",
                "skills": ["follow-up-comercial", "agente-atendimento-pre-passeio"]},
    "Nero":    {"role": "Objeções e forja de skills", "icon": "🛡️", "group": "vendas",
                "skills": ["objecoes-turismo-jampa"]},
    "Nova":    {"role": "Diretora criativa", "icon": "🎨", "group": "criativo",
                "skills": ["copywriter-vendas", "social-media-editorial-turismo"]},
    "Midas":   {"role": "Tráfego e performance", "icon": "📈", "group": "trafego",
                "skills": ["painel-kpi-vempassear"]},
    "Umba":    {"role": "UX e experiência", "icon": "📐", "group": "produto",
                "skills": ["ux-ui-mobile-first"]},
    "Dex":     {"role": "Desenvolvimento de site", "icon": "💻", "group": "produto",
                "skills": ["programador-de-site", "estrategista-de-site"]},
    "Hex":     {"role": "Proposta e precificação", "icon": "💰", "group": "produto",
                "skills": ["proposta-passeio"]},
}

# Arquivos do _conhecimento que aterram TODA geração (Regra Ouro). Capados.
_CORE_GROUNDING = [
    "empresa.md", "passeios.md", "base-operacional-comercial.md",
    "tom-de-voz.md", "scripts-atendimento-whatsapp.md", "provas-de-confianca.md",
]
_CAP_PER_FILE = 2200  # chars por arquivo, pra manter o prompt bounded

_REGRA_OURO = (
    "\n\n## REGRA OURO (INVIOLÁVEL)\n"
    "Nunca invente preço, roteiro, duração, ponto de embarque, depoimento ou parceria. "
    "Use SOMENTE os dados do CONHECIMENTO abaixo. Se o dado não estiver lá, escreva "
    "[CONFIRMAR COM MURILLO: <o que falta>] em vez de chutar. WhatsApp oficial: "
    "+55 83 99908-7830. Responda em português do Brasil."
)

_grounding_cache: str | None = None


def _read(path: Path, cap: int = 0) -> str:
    try:
        t = path.read_text(encoding="utf-8", errors="replace")
        return t[:cap] + "\n[...]" if cap and len(t) > cap else t
    except Exception:
        return ""


def _grounding() -> str:
    """Bloco de conhecimento (catálogo/empresa/tom/scripts) — cacheado."""
    global _grounding_cache
    if _grounding_cache is not None:
        return _grounding_cache
    partes = ["## CONHECIMENTO (fonte de verdade — Vem Passear em Jampa)"]
    for fn in _CORE_GROUNDING:
        txt = _read(CONHECIMENTO_DIR / fn, _CAP_PER_FILE)
        if txt.strip():
            partes.append(f"\n### {fn}\n{txt}")
    _grounding_cache = "\n".join(partes) + _REGRA_OURO
    return _grounding_cache


def _skill_body(skill_id: str) -> str:
    """Corpo da SKILL.md (sem o frontmatter YAML)."""
    raw = _read(SKILLS_DIR / skill_id / "SKILL.md")
    if not raw:
        return ""
    # remove frontmatter --- ... ---
    return re.sub(r"^---.*?---\s*", "", raw, count=1, flags=re.DOTALL).strip()


def available() -> bool:
    return SKILLS_DIR.exists()


def list_agents() -> list[dict]:
    """Roster para o dashboard."""
    out = []
    for nome, info in ROSTER.items():
        skills_ok = [s for s in info["skills"] if (SKILLS_DIR / s / "SKILL.md").exists()]
        out.append({
            "nome": nome, "papel": info["role"], "icon": info["icon"],
            "grupo": info["group"], "skills": skills_ok,
            "ativo": bool(skills_ok),
        })
    return out


def _system_prompt(nome: str) -> str:
    info = ROSTER[nome]
    corpos = [_skill_body(s) for s in info["skills"]]
    corpos = [c for c in corpos if c]
    header = (
        f"Você é {nome}, agente {info['role']} do Jampa Jarvis (assistente operacional "
        f"de Murillo Affonso, fundador da Vem Passear em Jampa). Aja de forma DIRETA e "
        f"OPERACIONAL: entregue o trabalho pronto, não diga 'faça isso'. "
        f"Trate-o por 'senhor'.\n\n"
        f"## SEU FRAMEWORK (skill)\n" + "\n\n---\n\n".join(corpos)
    )
    return header + "\n\n" + _grounding()


def run(nome: str, tarefa: str, contexto: str = "", deep: bool = False) -> str:
    """Executa um agente nomeado. deep=True usa Opus (assinatura); senão gpt-4o."""
    if nome not in ROSTER:
        return f"Agente desconhecido: {nome}"
    sys = _system_prompt(nome)
    user = f"{contexto}\n\nTarefa: {tarefa}".strip() if contexto else tarefa
    if deep:
        import claude_brain
        if claude_brain.available():
            # claude_brain usa system próprio; injetamos o framework no contexto.
            return claude_brain.answer(user, context=sys)
    from llm_providers import call_openai
    try:
        return call_openai(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.5,
        )
    except Exception as e:
        return f"[{nome} indisponível: {e}]"


def _escolher_agente(tarefa: str) -> str:
    """Orion classifica qual agente nomeado deve atender a tarefa."""
    from llm_providers import call_openai
    roster_txt = "\n".join(f"- {n}: {i['role']}" for n, i in ROSTER.items())
    prompt = (
        "Você é Orion, orquestrador do Jampa Jarvis. Escolha QUAL agente atende a "
        f"tarefa. Responda SÓ com o nome do agente, nada mais.\n\nAgentes:\n{roster_txt}\n\n"
        f"Tarefa: {tarefa}"
    )
    try:
        r = call_openai([{"role": "user", "content": prompt}], temperature=0).strip()
        for nome in ROSTER:
            if nome.lower() in r.lower():
                return nome
    except Exception:
        pass
    return "Hunter"  # default comercial


def orquestrar(tarefa: str, contexto: str = "", deep: bool = False) -> dict:
    """Orion escolhe o agente e o executa (acionamento semântico, Fase 1)."""
    nome = _escolher_agente(tarefa)
    resposta = run(nome, tarefa, contexto, deep=deep)
    return {"agente": nome, "papel": ROSTER[nome]["role"], "resposta": resposta}


def responder_lead(nome_lead: str = "", contato: str = "", interesse: str = "",
                   obs: str = "") -> dict:
    """Fluxo-dinheiro: Hunter+LNS geram a resposta de WhatsApp pronta pro lead.

    Aterrada no catálogo/scripts. Retorna {mensagem, numero} — o ENVIO é do Murillo
    (abre o wa.me com a mensagem pronta).
    """
    ctx_partes = []
    if nome_lead: ctx_partes.append(f"Nome do lead: {nome_lead}")
    if interesse: ctx_partes.append(f"Interesse: {interesse}")
    if obs:       ctx_partes.append(f"Observações: {obs}")
    contexto = "\n".join(ctx_partes)
    tarefa = (
        "Escreva UMA mensagem de WhatsApp pronta para enviar a este lead que chegou "
        "(provavelmente pelo anúncio das Piscinas Naturais). Siga esta lógica de "
        "qualificação (discovery) — qualifique ANTES de despejar proposta:\n"
        "1) Cumprimente pelo nome e confirme, em uma frase, o interesse que ele demonstrou.\n"
        "2) Dê o preço correto do catálogo e use a urgência real da maré (se souber).\n"
        "3) TERMINE com no máximo 2 perguntas naturais para preencher o que falta para "
        "fechar: data desejada, número de pessoas (adultos/crianças) e local de busca/hotel. "
        "Pergunte como quem quer ajudar a organizar o passeio, NUNCA como interrogatório.\n"
        "Regra de ouro do discovery: se faltar dado essencial (data, pessoas, local), a "
        "mensagem DEVE terminar puxando esse dado — não invente proposta detalhada no vácuo. "
        "Tom caloroso e local da Vem Passear. Sem markdown, pronta pra colar."
    )
    msg = run("LNS", tarefa, contexto)
    num = "".join(c for c in (contato or "") if c.isdigit())
    return {"mensagem": (msg or "").strip(), "numero": num}
