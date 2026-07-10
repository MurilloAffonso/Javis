"""Agent — cérebro com tool-use (function calling) do Jamba.

Em vez de roteamento por palavra-chave, o Claude DECIDE qual ferramenta chamar,
entende intenção (não palavra exata) e ENCADEIA ações ("abre o youtube e toca jazz").

Degrada com elegância: sem ANTHROPIC_API_KEY, retorna None e o chamador usa o fallback.
"""
from __future__ import annotations
import os
import json
import re
import time
import contextvars

import actions
import safe_config
from provider_errors import ProviderError
import provider_health
import provider_registry

# project_id da conversa em curso (R2.1). Normalizado para "javes-core" por padrão
# e propagado às ferramentas (ex.: buscar_conhecimento) via contextvar, sem
# precisar passar o argumento por todas as assinaturas dos provedores.
_DEFAULT_PROJECT_ID = "javes-core"
_PROJECT_CTX: contextvars.ContextVar[str] = contextvars.ContextVar(
    "javis_project_id", default=_DEFAULT_PROJECT_ID
)


def _normalize_project_id(project_id: str | None) -> str:
    """project_id nunca fica indefinido: vazio/None → 'javes-core'."""
    return (project_id or "").strip() or _DEFAULT_PROJECT_ID


def _current_project_id() -> str:
    return _normalize_project_id(_PROJECT_CTX.get())


# Mensagens amigáveis (nunca vazam traceback, credencial, token ou chave).
_PROVIDER_UNAVAILABLE_MSG = (
    "Provider externo indisponível. O modo local pode ser ativado com Ollama."
)

# Decisão 21/06 — Haiku 4.5 como default do tool-use (era sonnet-4-6).
# Sonnet/Opus continuam acessíveis via env JAVIS_CLAUDE_MODEL e via `pensar_profundo`.
# Razão: tool-use de comando ("toca jazz", "abre site") não precisa de capacidade
# de raciocínio pesado — só de decisão certa de qual ferramenta chamar. Haiku é
# ~5× mais leve em cota da assinatura, mantendo a precisão de tool-use.
CLAUDE_MODEL = os.environ.get("JAVIS_CLAUDE_MODEL", "claude-haiku-4-5-20251001")
OPENAI_MODEL = os.environ.get("JAVIS_OPENAI_MODEL", "gpt-4o-mini")

# Timeout (s) por chamada de LLM — evita que a cascata empilhe espera invisível
# quando um provedor está lento ou sem crédito (causa nº 1 de "travamento").
LLM_TIMEOUT = float(os.environ.get("JAVIS_LLM_TIMEOUT", "20"))


def _log(msg: str) -> None:
    """Log visível no console do servidor — para de engolir falhas em silêncio."""
    import sys
    print(f"[agent] {msg}", file=sys.stderr, flush=True)


# Tool gating — pré-filtragem das tools enviadas ao LLM por turno.
# Em vez de mandar TODAS as ~30 ferramentas em cada chamada (~1.5-2k tok), o
# command_router (regras de palavra-chave, zero LLM) detecta a intenção e
# selecionamos só as relevantes + um baseline conservador. Degradação segura: se
# o gating não souber classificar ou der erro, devolve TOOLS inteiro.

# Tools "sempre disponíveis" — raciocínio, RAG, memória, hora/data, fluxo VP,
# análise de arquivo, executor Codex. Coisas que podem ser pedidas em qualquer
# turno e cujo overhead é aceitável manter na baseline.
_BASELINE_TOOL_NAMES = {
    "buscar_conhecimento", "pensar_profundo", "consultar_especialistas",
    "hora_data", "gerar_pauta_vp", "lembrar_fato", "criar_lembrete",
    "listar_lembretes", "analisar_arquivo", "programar",
}

# Mapa intent (do command_router) → tools específicas a adicionar à baseline.
_INTENT_TOOL_NAMES: dict[str, set[str]] = {
    "clima":           {"clima"},
    "analisar_site":   {"analisar_site", "ler_pagina"},
    "tocar_musica":    {"tocar_musica", "abrir_youtube"},
    "abrir_youtube":   {"abrir_youtube", "tocar_musica"},
    "abrir_openwebui": {"abrir_openwebui", "abrir_site"},
    "abrir_vscode":    {"abrir_vscode", "abrir_app"},
    "abrir_terminal":  {"abrir_terminal", "abrir_app"},
    "abrir_navegador": {"abrir_navegador", "abrir_site", "abrir_app", "pesquisar_google"},
    "abrir_projeto":   {"abrir_projeto", "abrir_pasta"},
    "abrir_javis":     {"abrir_pasta"},
    "registrar_ideia": {"registrar_ideia", "lembrar_fato"},
    "status_sistema":  {"status_sistema"},
    # acao_perigosa / trocar_motor / conversa / desconhecido → só baseline.
}


def _gate_tools(text: str) -> list[dict]:
    """Filtra `TOOLS` para o subconjunto relevante ao texto do turno.

    Reduz ~30 → ~10-15 ferramentas. Em caso de falha do roteador ou intent
    desconhecido, devolve `TOOLS` inteiro (nunca deixa o LLM sem ferramenta
    por causa de bug do gating).
    """
    try:
        import command_router
        r = command_router.route(text or "")
        intent = r.get("intent", "")
    except Exception:
        return TOOLS
    specific = _INTENT_TOOL_NAMES.get(intent, set())
    keep = _BASELINE_TOOL_NAMES | specific
    filtered = [t for t in TOOLS if t["name"] in keep]
    if not filtered:
        return TOOLS
    _log(f"gate[{intent}] {len(filtered)}/{len(TOOLS)} tools enviadas")
    return filtered


_USAGE_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "_data", "token_usage.jsonl")


def _sanitize_telemetry_error(error: Exception | str | None) -> str | None:
    """Remove segredos conhecidos e padrões de credencial antes de persistir erros."""
    if error is None:
        return None
    text = f"{type(error).__name__}: {error}" if isinstance(error, Exception) else str(error)
    for env_name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        secret = os.environ.get(env_name, "")
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(
        r"(?i)\b(authorization|api[_-]?key)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        text,
    )
    text = re.sub(r"\b(?:sk-or-v1-|sk-)[A-Za-z0-9_-]{8,}\b", "[REDACTED]", text)
    return text[:500] or None


def _estimate_openrouter_cost(
    requested_model: str,
    input_tokens: int,
    output_tokens: int,
    reported_cost: object = None,
) -> float | None:
    """Estima USD sem tabela embutida; usa custo reportado, modelo free ou rates via env."""
    if reported_cost is not None:
        try:
            return round(float(reported_cost), 8)
        except (TypeError, ValueError):
            pass
    if requested_model.endswith(":free"):
        return 0.0
    try:
        input_rate = os.environ.get("JAVIS_OPENROUTER_INPUT_USD_PER_MILLION", "").strip()
        output_rate = os.environ.get("JAVIS_OPENROUTER_OUTPUT_USD_PER_MILLION", "").strip()
        if not input_rate or not output_rate:
            return None
        cost = (input_tokens * float(input_rate) + output_tokens * float(output_rate)) / 1_000_000
        return round(cost, 8)
    except (TypeError, ValueError):
        return None


def _log_usage(provider: str, model: str, input_tokens: int = 0, output_tokens: int = 0,
               cache_read_input_tokens: int = 0, cache_creation_input_tokens: int = 0,
               kind: str = "chat", requested_model: str | None = None,
               resolved_model: str | None = None, estimated_cost_usd: float | None = None,
               latency_ms: int | None = None, error: Exception | str | None = None,
               fallback_used: bool = False) -> None:
    """Registra o consumo de tokens em _data/token_usage.jsonl (uma linha por chamada).

    Sem isso a gente não consegue dizer "antes/depois" de nenhuma otimização —
    `server.py` retornava `usage={prompt_tokens:0,...}` hardcoded até hoje.
    Falha em silêncio se não conseguir escrever (telemetria nunca derruba o chat).
    """
    try:
        import time as _t
        os.makedirs(os.path.dirname(_USAGE_LOG_PATH), exist_ok=True)
        total_input = (input_tokens or 0) + (cache_read_input_tokens or 0) + (cache_creation_input_tokens or 0)
        rec = {
            "ts": _t.strftime("%Y-%m-%dT%H:%M:%S"),
            "provider": provider,
            "model": model,
            "requested_model": requested_model or model,
            "resolved_model": resolved_model or model,
            "kind": kind,
            "input_tokens": input_tokens or 0,
            "cache_read_input_tokens": cache_read_input_tokens or 0,
            "cache_creation_input_tokens": cache_creation_input_tokens or 0,
            "output_tokens": output_tokens or 0,
            "total_input": total_input,
            "estimated_cost_usd": estimated_cost_usd,
            "latency_ms": latency_ms,
            "error": _sanitize_telemetry_error(error),
            "fallback_used": bool(fallback_used),
        }
        with open(_USAGE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _log(f"usage[{provider}/{model}] in={total_input} (cache_read={cache_read_input_tokens or 0}) out={output_tokens or 0}")
    except Exception as e:
        _log(f"_log_usage falhou (ignorado): {e}")


def _journey(task_id: str, event_type: str, actor: str = "system", message: str = "",
             agent_id: str | None = None, metadata: dict | None = None) -> None:
    """Registra um evento no Journey Log da task. Nunca quebra o fluxo se falhar."""
    try:
        import repositories as repo
        repo.task_events.add_event(task_id, event_type, actor, message,
                                   agent_id=agent_id, metadata=metadata)
    except Exception:
        pass

SYSTEM_AGENT = """Você é Javes, assistente pessoal de Murillo Affonso.

REGRAS ABSOLUTAS — NUNCA VIOLAR:
0. RESPOSTA CURTA (padrão): máximo 5 linhas. Sem relatório longo, sem repetir contexto. Só detalhe se houver erro, risco ou decisão a tomar.
1. IDIOMA: Responda SEMPRE em português do Brasil. NUNCA em inglês, espanhol ou outro idioma.
2. TRATAMENTO: Chame o usuário de "senhor" ou "Murillo" — nunca "você" ou "user".
3. VOZ: Respostas são lidas em voz alta — seja CONCISO. Máximo 2 frases para ações. Sem markdown.
4. AÇÃO: Quando houver uma ferramenta disponível, USE-A. Não descreva o que faria — faça.
5. SEM IMPROVISO: Nunca invente dados (preços, horários, endereços). Use as ferramentas.
6. NÃO FINJA QUE FEZ: Nunca diga que "executou", "iniciou", "criou", "terminou" ou "já fez" algo se nenhuma ferramenta foi realmente chamada para isso nesta resposta. Se não há ferramenta para a tarefa, diga a verdade — o que falta, ou ofereça a ação real — em vez de afirmar que já está feito.

PERFIL DE MURILLO:
- Empreendedor, fundador da Vem Passear em Jampa (turismo em João Pessoa/PB)
- Usa o Javes para automatizar tarefas e agilizar operações
- Prefere respostas diretas e curtas
"""
# Atenção: NÃO interpolar dados que mudam por turno (hora, briefing, estado) nesta
# string. Elas estabilizam o prefixo do prompt para o **prompt caching** (Anthropic
# `cache_control:ephemeral` na rota API e cache automático do Claude CLI na rota
# da assinatura). Hora atual / estado do projeto agora entram via `_system_dynamic`.

# Ferramentas expostas ao Claude (formato Anthropic tool-use)
TOOLS = [
    {
        "name": "tocar_musica",
        "description": "Toca uma música no YouTube. Use quando o senhor pedir para tocar/colocar som ou música.",
        "input_schema": {
            "type": "object",
            "properties": {"termo": {"type": "string", "description": "O que tocar (artista, música, gênero). Vazio = lofi para relaxar."}},
            "required": [],
        },
    },
    {
        "name": "abrir_youtube",
        "description": "Abre o site do YouTube (página inicial), sem tocar nada específico.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "clima",
        "description": "Informa o clima/tempo atual de uma cidade.",
        "input_schema": {
            "type": "object",
            "properties": {"cidade": {"type": "string", "description": "Cidade. Vazio = cidade padrão do senhor."}},
            "required": [],
        },
    },
    {
        "name": "analisar_site",
        "description": "Analisa a estrutura de um site e gera um esqueleto de código HTML/CSS recriando o layout.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL do site a analisar."}},
            "required": ["url"],
        },
    },
    {
        "name": "registrar_ideia",
        "description": "Salva uma ideia/anotação do senhor em arquivo.",
        "input_schema": {
            "type": "object",
            "properties": {"texto": {"type": "string", "description": "O conteúdo da ideia a salvar."}},
            "required": ["texto"],
        },
    },
    {
        "name": "status_sistema",
        "description": "Verifica o status dos serviços do sistema (Open WebUI, Voz sandbox, etc.).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "abrir_navegador",
        "description": "Abre o navegador no Google.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "abrir_terminal",
        "description": "Abre o terminal (PowerShell) na pasta do projeto.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "abrir_vscode",
        "description": "Abre o VS Code na pasta do projeto.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "abrir_projeto",
        "description": "Abre a pasta do projeto Jamba no explorador de arquivos.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "abrir_openwebui",
        "description": "Abre o Open WebUI no navegador.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "lembrar_fato",
        "description": "Memoriza um fato sobre o senhor (preferência, rotina, projeto, gosto) para usar nas próximas conversas. Use quando ele contar algo pessoal que valha lembrar.",
        "input_schema": {
            "type": "object",
            "properties": {"fato": {"type": "string", "description": "O fato a memorizar, em uma frase."}},
            "required": ["fato"],
        },
    },
    {
        "name": "criar_lembrete",
        "description": "Cria um lembrete/timer. Informe 'minutos' (daqui a quanto tempo) OU 'iso' (horário absoluto AAAA-MM-DDTHH:MM). Use para 'me lembra de X em 10 min'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texto": {"type": "string", "description": "O que lembrar."},
                "minutos": {"type": "number", "description": "Daqui a quantos minutos."},
                "iso": {"type": "string", "description": "Horário absoluto ISO, se for hora marcada."},
            },
            "required": ["texto"],
        },
    },
    {
        "name": "listar_lembretes",
        "description": "Lista os lembretes pendentes do senhor.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "rotina_matinal",
        "description": "Resumo da manhã para o senhor: saudação, clima e lembretes pendentes.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "hora_data",
        "description": "Informa a HORA e a DATA atuais. Use para 'que horas são', 'que dia é hoje'.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "programar",
        "description": "Delega uma tarefa de EXECUÇÃO ao motor de execução (Claude Code pela assinatura): escrever/alterar código, criar arquivos, rodar comandos/testes, analisar projetos ou tarefas multi-step em QUALQUER pasta do computador. Use quando o senhor pedir para 'programar', 'criar', 'executar', 'analisar' ou 'fazer' algo — no projeto Javis ou em qualquer outra pasta. Roda em segundo plano e avisa ao terminar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tarefa": {"type": "string", "description": "Descrição clara da tarefa a executar."},
                "pasta": {"type": "string", "description": "Caminho completo da pasta onde executar (ex.: C:\\Users\\noteacer\\Documents\\MeuProjeto). Se vazio, executa na pasta do Javis."},
            },
            "required": ["tarefa"],
        },
    },
    {
        "name": "abrir_app",
        "description": "Abre QUALQUER aplicativo ou janela do Windows pelo nome (spotify, word, excel, calculadora, configurações, discord, steam, bluetooth, wifi, câmera, etc.). Use para abrir programas do PC.",
        "input_schema": {
            "type": "object",
            "properties": {"nome": {"type": "string", "description": "Nome do app/janela a abrir."}},
            "required": ["nome"],
        },
    },
    {
        "name": "abrir_pasta",
        "description": "Abre uma PASTA nomeada do PC no explorador: Documentos, Downloads, Imagens/Fotos, Vídeos, Música ou Desktop (ou um caminho completo). Use para 'abre minha pasta de documentos', 'abre os downloads', etc. NÃO confundir com abrir_projeto (pasta do Jamba).",
        "input_schema": {
            "type": "object",
            "properties": {"nome": {"type": "string", "description": "Nome da pasta (documentos, downloads, imagens, vídeos, música, desktop) ou caminho completo."}},
            "required": ["nome"],
        },
    },
    {
        "name": "abrir_site",
        "description": "Abre QUALQUER site no navegador. Use quando o senhor citar um site/endereço.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Endereço do site (ex.: github.com)."}},
            "required": ["url"],
        },
    },
    {
        "name": "pesquisar_google",
        "description": "Abre o Google no browser, pesquisa o termo e LÊ os resultados, devolvendo um resumo. Use quando o senhor quiser buscar algo na internet.",
        "input_schema": {
            "type": "object",
            "properties": {"termo": {"type": "string", "description": "O que pesquisar."}},
            "required": ["termo"],
        },
    },
    {
        "name": "ler_pagina",
        "description": "Abre uma URL no browser e lê o conteúdo da página, resumindo para o senhor. Use quando precisar ler um site específico.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Endereço completo da página (ex.: 'noticias.uol.com.br')."}},
            "required": ["url"],
        },
    },
    {
        "name": "buscar_conhecimento",
        "description": "Busca nos ARQUIVOS do senhor (notas do Obsidian, ideias, projetos, logs) para responder perguntas sobre o que ELE escreveu/anotou. Use SEMPRE que ele perguntar sobre as notas/projetos/anotações dele, ou 'o que eu anotei sobre X'.",
        "input_schema": {
            "type": "object",
            "properties": {"pergunta": {"type": "string", "description": "A pergunta ou tema a buscar nos arquivos."}},
            "required": ["pergunta"],
        },
    },
    {
        "name": "pesquisar_redes",
        "description": "Pesquisa um tema no Reddit e YouTube e retorna o que as pessoas estão falando. Use quando o senhor quiser saber a opinião/discussão sobre um assunto nas redes.",
        "input_schema": {
            "type": "object",
            "properties": {"tema": {"type": "string", "description": "O tema a pesquisar (ex.: 'turismo João Pessoa', 'Instagram marketing')."}},
            "required": ["tema"],
        },
    },
    {
        "name": "analisar_arquivo",
        "description": "Analisa um arquivo enviado pelo senhor (PDF, Excel, Word, CSV, relatório do Analytics, etc.) e extrai insights. Use quando ele mandar um arquivo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "caminho": {"type": "string", "description": "Caminho completo do arquivo."},
                "pergunta": {"type": "string", "description": "Pergunta específica sobre o arquivo (opcional)."},
            },
            "required": ["caminho"],
        },
    },
    {
        "name": "enviar_whatsapp",
        "description": "Abre o WhatsApp com a mensagem pronta para um contato. Informe 'numero' (com DDI/DDD, só dígitos) e 'mensagem'. Sem número, apenas abre o WhatsApp.",
        "input_schema": {
            "type": "object",
            "properties": {
                "numero": {"type": "string", "description": "Número com DDI+DDD, só dígitos (ex.: 5583999998888)."},
                "mensagem": {"type": "string", "description": "Texto da mensagem."},
            },
            "required": [],
        },
    },
    {
        "name": "pensar_profundo",
        "description": "Aciona o CÉREBRO DE RACIOCÍNIO (Claude Opus 4.8, o modelo mais inteligente) para pensar a fundo numa questão complexa: decisão estratégica, análise de negócio/marketing, conselho ponderado, problema que exige raciocínio cuidadoso. Use SEMPRE que o senhor pedir uma análise profunda, uma decisão importante, ou disser 'analisa a fundo', 'me ajuda a decidir', 'vale a pena', 'pensa direito nisso'. É mais lento (pensa com calma), então NÃO use para conversa casual, perguntas simples ou ações diretas (abrir app, tocar música, hora).",
        "input_schema": {
            "type": "object",
            "properties": {"questao": {"type": "string", "description": "A questão ou decisão a pensar, clara e completa (inclua o contexto que o senhor deu)."}},
            "required": ["questao"],
        },
    },
    {
        "name": "consultar_especialistas",
        "description": "Convoca o CONSELHO DE ESPECIALISTAS (Conclave: um crítico que audita falhas, um advogado que ataca o plano e um sintetizador que integra a melhor solução) para DEBATER uma questão sob múltiplos pontos de vista que se confrontam. Use APENAS quando o senhor pedir explicitamente um DEBATE ou disser 'debate', 'o que vocês acham', 'prós e contras'. Para raciocínio profundo geral, prefira pensar_profundo.",
        "input_schema": {
            "type": "object",
            "properties": {"questao": {"type": "string", "description": "A questão ou decisão a debater, redigida de forma clara e completa (inclua o contexto que o senhor deu)."}},
            "required": ["questao"],
        },
    },
    {
        "name": "gerar_pauta_vp",
        "description": "Aciona o FLUXO REAL de marketing da Vem Passear: chama a agente Nova pra montar a pauta de conteúdo da SEMANA (3 posts), salva em pauta-semana.md, registra no Quadro (Raia 1) e PARA no Gate 1 pedindo a aprovação do Murillo. Use quando o senhor pedir 'cria a pauta da semana', 'monta a pauta da Vem Passear', 'pauta de posts dessa semana' ou similar.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _compact_history(history: list[dict] | None, keep_raw: int = 2,
                     max_old_chars: int = 600) -> list[dict]:
    """Compacta o histórico: mantém os últimos `keep_raw` turnos crus e resume
    todos os anteriores em UMA mensagem `[Resumo da conversa anterior: ...]`.

    Em conversa longa (>10 turnos), o tamanho do histórico cai de ~3k tokens
    crus para ~200-300 tokens. Cada turno antigo vira `Quem: primeiros 80 chars`,
    juntados por "; ". Se o resumo passa de `max_old_chars`, ficamos com a cauda
    (mais recente) — começo da conversa raramente importa pro tool-use.
    """
    if not history:
        return []
    raw_tail = history[-keep_raw:] if keep_raw > 0 else []
    older = history[:-keep_raw] if keep_raw > 0 else history
    if not older:
        return list(raw_tail)
    bits = []
    for h in older:
        c = (h.get("content") or "").strip()
        if not c:
            continue
        quem = "Murillo" if h.get("role") == "user" else "Jamba"
        bits.append(f"{quem}: {c[:80]}")
    summary = "; ".join(bits)
    if not summary:
        return list(raw_tail)
    if len(summary) > max_old_chars:
        summary = "..." + summary[-(max_old_chars - 3):]
    summary_msg = {"role": "user",
                   "content": f"[Resumo da conversa anterior: {summary}]"}
    return [summary_msg] + list(raw_tail)


def _history_context(history: list[dict] | None, keep_raw: int = 2,
                     max_old_chars: int = 600) -> str:
    """Versão TEXTO da compactação para as rotas que injetam histórico como
    string (assinatura via `context=`, `stream_text`). Mantém o resumo + últimos
    `keep_raw` turnos crus em `Quem: ...` (capado em 400 chars cada)."""
    if not history:
        return ""
    compacted = _compact_history(history, keep_raw=keep_raw, max_old_chars=max_old_chars)
    linhas = []
    for h in compacted:
        c = (h.get("content") or "").strip()
        if not c:
            continue
        if c.startswith("[Resumo"):
            linhas.append(c)
        else:
            quem = "Murillo" if h.get("role") == "user" else "Jamba"
            linhas.append(f"{quem}: {c[:400]}")
    return "\n".join(linhas)


def _exec_tool(name: str, inp: dict, history: list[dict] | None = None) -> str:
    """Traduz a chamada de ferramenta do Claude para actions.execute e retorna a mensagem."""
    inp = inp or {}
    if name == "tocar_musica":
        termo = (inp.get("termo") or "").strip()
        text = f"toca {termo}" if termo else "toca uma música"
        return actions.execute("tocar_musica", text).get("message", "Tocando, senhor.")
    if name == "clima":
        cidade = (inp.get("cidade") or "").strip()
        text = f"clima em {cidade}" if cidade else "clima"
        return actions.execute("clima", text).get("message", "")
    if name == "analisar_site":
        url = (inp.get("url") or "").strip()
        return actions.execute("analisar_site", f"analisa o site {url}").get("message", "")
    if name == "registrar_ideia":
        return actions.execute("registrar_ideia", (inp.get("texto") or "").strip()).get("message", "")
    if name == "lembrar_fato":
        import profile
        return profile.save_fact(inp.get("fato") or "")
    if name == "criar_lembrete":
        import reminders
        return reminders.add(inp.get("texto") or "", minutos=inp.get("minutos"), iso=inp.get("iso"))
    if name == "listar_lembretes":
        import reminders
        return reminders.list_pending_text()
    if name == "rotina_matinal":
        return _rotina_matinal()
    if name == "hora_data":
        from datetime import datetime
        dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                 "agosto", "setembro", "outubro", "novembro", "dezembro"]
        n = datetime.now()
        return f"São {n.strftime('%H:%M')}, {dias[n.weekday()]}, {n.day} de {meses[n.month-1]} de {n.year}, senhor."
    if name == "programar":
        tarefa = inp.get("tarefa") or ""
        pasta = inp.get("pasta") or None
        # Motor escolhido por Murillo (botão Claude/Codex); com fallback automático.
        import brain_switch
        return brain_switch.dispatch(tarefa, pasta=pasta)
    if name == "abrir_app":
        import app_launcher
        return app_launcher.open_app(inp.get("nome") or "").get("message", "Feito, senhor.")
    if name == "abrir_pasta":
        import app_launcher
        return app_launcher.open_folder(inp.get("nome") or "").get("message", "Feito, senhor.")
    if name == "abrir_site":
        import app_launcher
        return app_launcher.open_site(inp.get("url") or "").get("message", "Feito, senhor.")
    if name == "pesquisar_google":
        import browser as _browser
        res = _browser.search_google(inp.get("termo") or "")
        return res.get("message", "Feito, senhor.")
    if name == "ler_pagina":
        import browser as _browser
        res = _browser.read_page(inp.get("url") or "")
        return res.get("message", "Feito, senhor.")
    if name == "enviar_whatsapp":
        import integrations
        return integrations.whatsapp_send(inp.get("numero") or "", inp.get("mensagem") or "").get("message", "Feito, senhor.")
    if name == "buscar_conhecimento":
        import knowledge
        ctx = knowledge.answer_context(inp.get("pergunta") or "", escopo=knowledge.scope_for_project(_current_project_id()))
        return ctx or "Não encontrei nada nos seus arquivos sobre isso, senhor."
    if name == "pesquisar_redes":
        import social_reader
        return social_reader.pesquisar_redes(inp.get("tema") or "").get("message", "Feito, senhor.")
    if name == "analisar_arquivo":
        import file_analyzer
        return file_analyzer.analyze(inp.get("caminho") or "", inp.get("pergunta") or "").get("message", "Feito, senhor.")
    if name == "pensar_profundo":
        # Cérebro de raciocínio = Claude Opus 4.8 pela ASSINATURA. É o "dois
        # níveis": gpt-4o roteia rápido aqui na frente, e delega o raciocínio
        # pesado para o Claude. Se a assinatura não responder, cai no conclave.
        import claude_brain
        questao = inp.get("questao") or ""
        ctx = _history_context(history)
        if claude_brain.available():
            resp = claude_brain.answer(questao, context=ctx)
            if resp:
                return resp
            _log("claude_brain vazio; caindo no conclave.")
        else:
            _log("Claude Code indisponível; pensar_profundo usa conclave.")
        from conclave import Conclave
        try:
            conc = Conclave().debate(questao, rounds=1)
            return conc.get("synthesis") or "Não cheguei a uma conclusão, senhor."
        except Exception as e:
            return f"Não consegui pensar a fundo agora, senhor: {e}"
    if name == "consultar_especialistas":
        # Convoca o Conclave (crítico → advogado → sintetizador) a pedido do
        # próprio cérebro principal — é assim que os especialistas entram no
        # fluxo de voz sem o senhor precisar ligar o ⚔️ debate manualmente.
        from conclave import Conclave
        try:
            conc = Conclave().debate(inp.get("questao") or "", rounds=1)
            return conc.get("synthesis") or "O conselho não chegou a uma conclusão, senhor."
        except Exception as e:
            _log(f"consultar_especialistas falhou: {e}")
            return f"Não consegui reunir o conselho agora, senhor: {e}"
    if name == "gerar_pauta_vp":
        return _fluxo_pauta_vp()
    # ações sem parâmetro
    return actions.execute(name, "").get("message", "Feito, senhor.")


def _fluxo_pauta_vp() -> str:
    """FLUXO REAL (chat → agente → arquivo → quadro → aprovação → log).

    Coração do Javis: o pedido em linguagem natural vira ação de verdade —
    a Nova gera a pauta, salva, o Quadro registra a Raia 1, e o fluxo PARA no
    Gate 1 (aprovação do Murillo). Tudo logado.
    """
    import time
    from pathlib import Path
    inicio = time.time()
    cj = Path(__file__).resolve().parents[3] / "_projetos" / "cerebro-jampa"
    pauta_task = "pipeline-marketing-vem-passear-jampa-t0"  # âncora da jornada

    # Journey Log: nascimento da task + intenção detectada
    _journey(pauta_task, "task_created", "system",
             "Pedido recebido: montar a pauta da semana da Vem Passear")
    _journey(pauta_task, "intent_detected", "system",
             "Intenção: gerar_pauta_vp (fluxo de conteúdo VP)")

    pedido = (
        "Monte a PAUTA DA SEMANA com EXATAMENTE 3 posts pro Instagram da Vem Passear, "
        "respeitando a regra de no máximo 1 de venda direta. Varie os pilares. Para cada "
        "post traga: dia e data, pilar, formato, gancho 3s, legenda no tom da marca, "
        "material visual necessário, CTA e hashtags. No fim, escreva 'Status: pauta "
        "proposta — aguardando aprovação do Murillo (Gate 1)'."
    )
    _journey(pauta_task, "agent_called", "agent", "Nova acionada para montar a pauta",
             agent_id="nova")
    try:
        import vp_squad
        r = vp_squad.run("nova", pedido)
    except Exception as e:
        return f"Não consegui acionar a Nova agora, senhor: {e}"
    if r.get("status") != "ok" or not r.get("result"):
        return r.get("message", "A Nova não devolveu a pauta agora, senhor (cota/assinatura).")

    # salva a pauta
    try:
        header = ("# Pauta da Semana — Vem Passear Jampa\n\n> Gerada pela Nova via chat do "
                  "Javis, " + time.strftime("%Y-%m-%d %H:%M") + ".\n> Raia 1 do Pipeline. "
                  "Próximo: Gate 1 (aprovação do Murillo).\n\n")
        (cj / "posts").mkdir(parents=True, exist_ok=True)
        (cj / "posts" / "pauta-semana.md").write_text(header + r["result"], encoding="utf-8")
        _journey(pauta_task, "file_generated", "agent",
                 "Arquivo pauta-semana.md gerado", agent_id="nova",
                 metadata={"arquivo": "_projetos/cerebro-jampa/posts/pauta-semana.md"})
    except Exception as e:
        return f"A Nova montou a pauta mas não consegui salvar, senhor: {e}"

    # registra no Quadro (Raia 1 concluída; Gate 1 fica pendente pro Murillo)
    quadro_ok = False
    try:
        import mission_board
        mid = "pipeline-marketing-vem-passear-jampa"
        quadro_ok = mission_board.set_task_done(mid, mid + "-t0", True)
    except Exception as e:
        _log(f"gerar_pauta_vp: quadro não atualizou: {e}")

    # persiste no SQLite: task espelhada + APROVAÇÃO pendente (Gate 1)
    try:
        import repositories as repo
        repo.tasks.set_status(pauta_task, "done")
        repo.approvals.add(
            subject="Aprovar a pauta da semana da Vem Passear (Gate 1) antes de ir pro Design",
            kind="gate", agent="nova", detail="_projetos/cerebro-jampa/posts/pauta-semana.md",
            task_id=pauta_task,  # âncora da jornada (o card "Ver jornada" mostra a timeline da pauta)
        )
        _journey(pauta_task, "approval_requested", "system",
                 "Gate 1 solicitada — aguardando aprovação do Murillo", agent_id="nova")
    except Exception as e:
        _log(f"gerar_pauta_vp: persistência SQLite falhou: {e}")

    # log do fluxo
    try:
        import logger
        logger.log(
            "frontend", "cria a pauta da semana da Vem Passear",
            {"intent": "gerar_pauta_vp", "confidence": "high", "risk_level": "low",
             "requires_approval": True},
            {"status": "ok", "message": "Nova gerou a pauta; aguardando Gate 1"},
            approved=None, duration_ms=int((time.time() - inicio) * 1000),
            extra={"agente": "nova", "arquivo": "_projetos/cerebro-jampa/posts/pauta-semana.md",
                   "quadro_atualizado": quadro_ok, "gate": "1 (aprovacao Murillo) pendente"},
        )
    except Exception as e:
        _log(f"gerar_pauta_vp: log falhou: {e}")

    return (
        "Pronto, senhor. A Nova montou a pauta da semana (3 posts) e salvei em "
        "pauta-semana.md. Registrei no Quadro — Raia 1 concluída"
        + (" ✓" if quadro_ok else "") +
        ". O fluxo PAROU no Gate 1: preciso da sua aprovação. Confira a pauta e me diga "
        "se aprovo pra produção ou ajusto algo — nada vai pro Design sem o seu OK."
    )


def _rotina_matinal() -> str:
    import reminders
    partes = []
    try:
        import integrations
        w = integrations.weather()
        if w:
            partes.append(f"Clima em {w['city']}: {w['temp']}°C, {w['desc']}.")
    except Exception:
        pass
    pend = reminders.list_pending()
    if pend:
        partes.append("Lembretes: " + "; ".join(f"{p['text']} (em {p['falta_min']} min)" for p in pend[:5]))
    else:
        partes.append("Sem lembretes pendentes.")
    return "Bom dia, senhor. " + " ".join(partes)


def _system_static() -> str:
    """Bloco FIXO do system prompt — cacheável.

    Contém o que NÃO muda por turno: regras + perfil de Murillo + fatos salvos
    do `profile`. Fica estável a ponto de a Anthropic/CLI reusar o cache deste
    prefixo entre chamadas dentro da janela de 5 min.
    """
    base = SYSTEM_AGENT
    try:
        import profile
        base = base + profile.context_block()
    except Exception:
        pass
    return base


def _system_dynamic() -> str:
    """Bloco DINÂMICO do system prompt — muda por turno (não cacheável).

    Hora atual + estado-resumo do projeto. Fica DEPOIS do bloco fixo para não
    invalidar o prefixo cacheado.
    """
    from datetime import datetime
    dias = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    n = datetime.now()
    hora = f"{n.strftime('%H:%M')}, {dias[n.weekday()]}, {n.day} de {meses[n.month-1]} de {n.year}"
    out = f"Hora atual: {hora}"
    # R3.1 — o estado interno do Javes (CURRENT_STATE.md, roadmap, fases R1..R4)
    # SÓ entra no contexto do núcleo javes-core. Projetos conectados (ex.:
    # project:cerebro-jampa) não recebem o briefing interno do núcleo.
    if _current_project_id() == _DEFAULT_PROJECT_ID:
        try:
            import briefing
            estado = briefing.estado_resumido()
            if estado:
                out += (
                    "\n\n## Estado atual do projeto Javis (use para responder o que foi "
                    "feito e o que está pendente; não invente nada fora disto):\n" + estado
                )
        except Exception:
            pass
    return out


def _system() -> str:
    """Compatibilidade: alguns chamadores ainda esperam o system inteiro como
    uma string só (OpenAI, OpenRouter, stream_text). Aqui devolvemos estático +
    dinâmico concatenados. As rotas Anthropic API/Subscription usam os blocos
    separados via `_system_static`/`_system_dynamic` para ativar o cache."""
    return _system_static() + "\n\n" + _system_dynamic()


def _respond_claude(user_text: str, history: list[dict], max_rounds: int) -> dict:
    """Tool-use via Claude (Anthropic). Levanta exceção em erro (p/ permitir fallback)."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=LLM_TIMEOUT)
    messages: list[dict] = []
    for h in _compact_history(history):
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    # Prompt caching: marca o bloco fixo (regras+perfil+fatos) e o array de tools
    # como `cache_control: ephemeral`. Bloco dinâmico (hora+briefing) vai depois,
    # sem cache. Resultado esperado: ~90% do input vira `cache_read_input_tokens`
    # a partir do 2º turno dentro de 5 min.
    system_blocks = [
        {"type": "text", "text": _system_static(), "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _system_dynamic()},
    ]
    # Gating + cache: o subconjunto filtrado vira a lista enviada, com cache
    # marker no último item. Se o gating devolveu TOOLS inteiro (fallback) ou um
    # subconjunto, o marker funciona igual — só é eficaz quando dois turnos
    # seguidos têm o mesmo intent (mesmo subconjunto).
    gated = _gate_tools(user_text)
    cached_tools = list(gated)
    if cached_tools:
        last = dict(cached_tools[-1])
        last["cache_control"] = {"type": "ephemeral"}
        cached_tools[-1] = last

    used: list[str] = []
    for _ in range(max_rounds):
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=1024,
            system=system_blocks, tools=cached_tools, messages=messages,
        )
        try:
            u = resp.usage
            _log_usage("anthropic_api", CLAUDE_MODEL,
                       input_tokens=getattr(u, "input_tokens", 0),
                       output_tokens=getattr(u, "output_tokens", 0),
                       cache_read_input_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
                       cache_creation_input_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
                       kind="tool_use")
        except Exception:
            pass
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    used.append(block.name)
                    out = _exec_tool(block.name, block.input, history)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": out or "feito"})
            messages.append({"role": "user", "content": results})
            continue
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return {"text": text.strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def _respond_openrouter(
    user_text: str,
    history: list[dict],
    max_rounds: int,
    fallback_used: bool = False,
) -> dict:
    """Tool-use via OpenRouter (gpt-oss-120b gratuito ou outros modelos)."""
    from openai import OpenAI
    # Default free trocado em 23/06: llama-3.3-70b:free estava rate-limited upstream
    # (provedor Venice) e gpt-oss-120b:free passou no teste live (PT/tool/código).
    # Catálogo free é volátil — ver _logs/2026-06-23_openrouter-teste-live.md.
    model = os.environ.get("JAVIS_OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=LLM_TIMEOUT,
    )
    oai_tools = [
        {"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in _gate_tools(user_text)
    ]
    messages: list[dict] = [{"role": "system", "content": _system()}]
    for h in _compact_history(history):
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    used: list[str] = []
    for _ in range(max_rounds):
        started = time.perf_counter()
        try:
            resp = client.chat.completions.create(model=model, messages=messages, tools=oai_tools)
        except Exception as exc:
            _log_usage(
                "openrouter", model, kind="tool_use",
                requested_model=model, resolved_model=model,
                estimated_cost_usd=0.0 if model.endswith(":free") else None,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=exc, fallback_used=fallback_used,
            )
            raise
        latency_ms = int((time.perf_counter() - started) * 1000)
        usage = getattr(resp, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        reported_cost = getattr(usage, "cost", None)
        resolved_model = getattr(resp, "model", None) or model
        _log_usage(
            "openrouter", resolved_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            kind="tool_use",
            requested_model=model,
            resolved_model=resolved_model,
            estimated_cost_usd=_estimate_openrouter_cost(
                model, input_tokens, output_tokens, reported_cost,
            ),
            latency_ms=latency_ms,
            fallback_used=fallback_used,
        )
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                used.append(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                out = _exec_tool(tc.function.name, args, history)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": out or "feito"})
            continue
        return {"text": (msg.content or "").strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def _respond_gemini(
    user_text: str,
    history: list[dict],
    max_rounds: int,
    fallback_used: bool = False,
) -> dict:
    """Tool-use via Gemini (endpoint OpenAI-compatible, tier grátis 1.500 req/dia)."""
    from openai import OpenAI
    model = os.environ.get("JAVIS_GEMINI_MODEL", "gemini-2.5-flash")
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ["GEMINI_API_KEY"],
        timeout=LLM_TIMEOUT,
    )
    oai_tools = [
        {"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in _gate_tools(user_text)
    ]
    messages: list[dict] = [{"role": "system", "content": _system()}]
    for h in _compact_history(history):
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    used: list[str] = []
    for _ in range(max_rounds):
        started = time.perf_counter()
        try:
            resp = client.chat.completions.create(model=model, messages=messages, tools=oai_tools)
        except Exception as exc:
            _log_usage(
                "gemini", model, kind="tool_use",
                requested_model=model, resolved_model=model,
                estimated_cost_usd=0.0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=exc, fallback_used=fallback_used,
            )
            raise
        latency_ms = int((time.perf_counter() - started) * 1000)
        usage = getattr(resp, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        resolved_model = getattr(resp, "model", None) or model
        _log_usage(
            "gemini", resolved_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            kind="tool_use",
            requested_model=model,
            resolved_model=resolved_model,
            estimated_cost_usd=0.0,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
        )
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                used.append(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                out = _exec_tool(tc.function.name, args, history)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": out or "feito"})
            continue
        return {"text": (msg.content or "").strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def _respond_openai(user_text: str, history: list[dict], max_rounds: int) -> dict:
    """Tool-use via OpenAI (function calling). Levanta exceção em erro."""
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=LLM_TIMEOUT, max_retries=1)
    oai_tools = [
        {"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in _gate_tools(user_text)
    ]
    messages: list[dict] = [{"role": "system", "content": _system()}]
    for h in _compact_history(history):
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    used: list[str] = []
    for _ in range(max_rounds):
        resp = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, tools=oai_tools)
        try:
            u = resp.usage
            _log_usage("openai", OPENAI_MODEL,
                       input_tokens=getattr(u, "prompt_tokens", 0) or 0,
                       output_tokens=getattr(u, "completion_tokens", 0) or 0,
                       kind="tool_use")
        except Exception:
            pass
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                used.append(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                out = _exec_tool(tc.function.name, args, history)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": out or "feito"})
            continue
        return {"text": (msg.content or "").strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def _tool_catalog(tools_subset: list[dict] | None = None) -> str:
    """Lista compacta das ferramentas pro prompt do Claude pela assinatura.

    `tools_subset` permite o tool gating injetar só as ferramentas relevantes
    pro turno. Default = todas as TOOLS (compatibilidade).
    """
    lines = []
    for t in (tools_subset if tools_subset is not None else TOOLS):
        params = ", ".join(t["input_schema"].get("properties", {}).keys())
        lines.append(f"- {t['name']}({params}): {t['description']}")
    return "\n".join(lines)


def _parse_tool_json(text: str) -> dict | None:
    """Extrai {"tool": ..., "args": {...}} de uma resposta em texto puro."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    if not text.startswith("{"):
        return None
    try:
        obj = json.loads(text)
    except Exception:
        return None
    return obj if isinstance(obj, dict) and "tool" in obj else None


def _respond_claude_subscription(user_text: str, history: list[dict], max_rounds: int) -> dict | None:
    """Tool-use via Claude Code headless (ASSINATURA, sem chave de API).

    O CLI não expõe function-calling nativo pra ferramentas arbitrárias do
    Jamba, então a decisão de ferramenta vem como JSON em texto puro
    (instruído no system prompt) e é parseada/executada aqui — mesmo
    `_exec_tool` usado pelos outros provedores. Retorna None se o Claude
    Code não estiver disponível, pro chamador cair no fallback.
    """
    import claude_brain
    if not claude_brain.available():
        return None
    # Prefixo ESTÁVEL → cache automático do Claude CLI hit. Só estático + tool
    # catalog filtrado por intent + regras (esses três blocos não mudam entre
    # turnos do MESMO intent). O dinâmico (hora + briefing) entra DEPOIS, via
    # `context`, sem invalidar o prefixo.
    gated = _gate_tools(user_text)
    system = _system_static() + (
        "\n\nFerramentas disponíveis:\n" + _tool_catalog(gated) +
        "\n\nPara usar uma ferramenta, responda SOMENTE com um JSON puro (sem "
        "texto antes/depois, sem markdown) neste formato exato:\n"
        '{"tool": "nome_da_ferramenta", "args": {"param": "valor"}}\n'
        "Se nenhuma ferramenta for necessária, responda normalmente em texto.\n\n"
        "REGRA DURA DE FERRAMENTA — não viole:\n"
        "- Se o senhor citar um ARQUIVO (caminho, .pdf, .docx, 'em Downloads', "
        "'na pasta X') → USE `analisar_arquivo`. NUNCA descreva o conteúdo de "
        "memória ou suposição: você NÃO viu o arquivo até a ferramenta rodar.\n"
        "- Se citar um SITE/URL pra ler/analisar → USE `ler_pagina` ou "
        "`analisar_site`.\n"
        "- Se pedir pra CRIAR/ALTERAR/EXECUTAR algo no projeto (código, arquivo, "
        "rodar comando) → USE `programar`. Não diga que vai pedir pra outra parte: "
        "`programar` JÁ é o pedido pro executor.\n"
        "- Se perguntar sobre as NOTAS/ANOTAÇÕES dele → USE `buscar_conhecimento`.\n"
        "- Na dúvida entre usar a ferramenta ou responder de cabeça sobre algo "
        "concreto e verificável: USE a ferramenta. Responder de memória sobre o "
        "que está num arquivo/site é FINGIR que fez — proibido."
    )
    # `dynamic` (hora + estado do projeto) entra no prompt — não no system —
    # justamente para o prefixo do system permanecer estável e ativar o cache do CLI.
    dynamic = _system_dynamic()
    base_ctx_parts = [dynamic]
    hist = _history_context(history)
    if hist:
        base_ctx_parts.append(hist)
    base_ctx = "\n\n".join(base_ctx_parts)
    transcript = ""
    used: list[str] = []
    for _ in range(max_rounds):
        ctx = f"{base_ctx}\n\n{transcript}".strip() if transcript else base_ctx
        out, usage = claude_brain.answer_with_usage(user_text, context=ctx, system=system, model=CLAUDE_MODEL)
        try:
            _log_usage("claude_subscription", CLAUDE_MODEL,
                       input_tokens=int(usage.get("input_tokens") or 0),
                       output_tokens=int(usage.get("output_tokens") or 0),
                       cache_read_input_tokens=int(usage.get("cache_read_input_tokens") or 0),
                       cache_creation_input_tokens=int(usage.get("cache_creation_input_tokens") or 0),
                       kind="tool_use")
        except Exception:
            pass
        if not out:
            return None
        call = _parse_tool_json(out)
        if not call:
            return {"text": out.strip(), "tools": used}
        name = call.get("tool", "")
        used.append(name)
        result = _exec_tool(name, call.get("args") or {}, history)
        transcript += f"\n[ferramenta {name} executada → resultado: {result}]"
    return {"text": "Executei o que era possível, senhor.", "tools": used}


# Gatilhos de raciocínio PESADO — quando o senhor pede análise a fundo/debate,
# vale o cérebro forte (Claude assinatura, que pode subir pra Opus via
# pensar_profundo) desde o início, mesmo custando os ~20s de cold-start.
# Espelham os _DEEP_HINTS de server.py (ack falado).
_HEAVY_HINTS = (
    "debate", "debat", "analisa a fundo", "analise a fundo", "análise a fundo",
    "o que voces acham", "o que vocês acham", "me ajuda a decidir",
    "me ajude a decidir", "vale a pena", "consultar o conselho",
    "consulta o conselho", "o que o conselho", "pensa direito",
    "pensa nisso", "pense nisso", "analisa direito", "prós e contras",
    "pros e contras", "pensa a fundo", "pense a fundo", "pensa profundo",
)


def _is_heavy_request(text: str) -> bool:
    """True se o pedido pede raciocínio profundo/debate → cérebro forte direto."""
    t = (text or "").lower()
    return any(h in t for h in _HEAVY_HINTS)


def _respond_ollama(user_text: str, history: list[dict]) -> dict | None:
    """Cérebro LOCAL (Ollama). RAG local (buscar via escopo) sem tocar em nuvem.
    Retorna {text, tools} ou None se o Ollama não estiver disponível."""
    import ollama_brain
    if not ollama_brain.available():
        return None
    ctx = _history_context(history)
    out = ollama_brain.answer(user_text, context=ctx, system=_system())
    # answer() nunca lança: em falha devolve texto "Ollama indisponível...".
    if not out or out.startswith("Ollama indisponível"):
        return None
    return {"text": out, "tools": []}


def _provider_for_step(step: str) -> str:
    if step.startswith("gemini"):
        return "gemini"
    if step.startswith("claude"):
        return "claude"
    if step == "anthropic":
        return "claude"
    return step


def _cloud_provider_steps(user_text: str) -> list[str]:
    steps: list[str] = []
    fast_brain = (os.environ.get("JAVIS_CHAT_FAST_BRAIN") or "gemini").strip().lower()
    use_gemini_fast = (
        fast_brain != "claude"
        and not _is_heavy_request(user_text)
        and bool(os.environ.get("GEMINI_API_KEY", "").strip())
    )
    if use_gemini_fast:
        steps.append("gemini_primary")
    steps.append("claude_subscription")
    if os.environ.get("OPENAI_API_KEY", "").strip():
        steps.append("openai")
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        steps.append("claude_api")
    if os.environ.get("GEMINI_API_KEY", "").strip() and not use_gemini_fast:
        steps.append("gemini_fallback")
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        steps.append("openrouter")
    return steps


def _provider_steps(mode: str, user_text: str) -> list[str]:
    if mode == "local":
        return provider_registry.selected_provider_ids("local", capability="chat")
    steps: list[str] = []
    if mode == "auto":
        steps.extend(provider_registry.selected_provider_ids("local", capability="chat"))
    if mode in ("cloud", "auto") and safe_config.external_adapters_enabled():
        enabled_cloud = set(provider_registry.selected_provider_ids("cloud", capability="chat"))
        steps.extend(
            step
            for step in _cloud_provider_steps(user_text)
            if _provider_for_step(step) in enabled_cloud
        )
    return steps


def _respond_provider(step: str, user_text: str, history: list[dict], max_rounds: int) -> dict | None:
    provider_id = _provider_for_step(step)
    if provider_id == "ollama":
        return _respond_ollama(user_text, history)
    if step == "gemini_primary":
        return _respond_gemini(user_text, history, max_rounds, fallback_used=False)
    if step == "gemini_fallback":
        return _respond_gemini(user_text, history, max_rounds, fallback_used=True)
    if step == "claude_subscription":
        return _respond_claude_subscription(user_text, history, max_rounds)
    if step == "claude_api":
        return _respond_claude(user_text, history, max_rounds)
    if provider_id == "openai":
        return _respond_openai(user_text, history, max_rounds)
    if provider_id == "openrouter":
        return _respond_openrouter(user_text, history, max_rounds, fallback_used=True)
    return None


def respond(
    user_text: str,
    history: list[dict] | None = None,
    max_rounds: int = 5,
    project_id: str = "",
) -> dict | None:
    """Loop de tool-use. Cascata: [Gemini rápido p/ conversa leve] → Claude
    (assinatura) → OpenAI → Claude API → Gemini → OpenRouter.
    Decisão Murillo 18/06: a assinatura é o cérebro principal. Ajuste 23/06: pra
    conversa LEVE, Gemini grátis responde primeiro (~1-2s vs ~20s do cold-start do
    Claude Code headless); pedido pesado e fallback continuam no Claude assinatura.
    Retorna {text, tools} ou None se nenhum provedor disponível."""
    history = history or []
    # project_id nunca fica indefinido: normaliza e propaga às tools (R2.1).
    _PROJECT_CTX.set(_normalize_project_id(project_id))

    try:
        import command_router
        route = command_router.route(user_text or "")
        if route.get("intent") == "status_sistema":
            res = actions.execute("status_sistema", user_text)
            return {"text": res.get("message", ""), "tools": ["status_sistema"]}
    except Exception:
        pass

    # R2.3 — provider registry + health/cooldown.
    mode = safe_config.provider_mode()
    provider_steps = _provider_steps(mode, user_text)
    if not provider_steps and mode in ("cloud", "auto") and not safe_config.external_adapters_enabled():
        return {
            "text": safe_config.disabled_message(
                "external_adapters",
                safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS,
            ),
            "tools": [],
        }

    for step in provider_steps:
        provider_id = _provider_for_step(step)
        try:
            out = _respond_provider(step, user_text, history, max_rounds)
            if out is not None:
                provider_health.record_success(provider_id)
                return out
            provider_health.record_failure(provider_id, ProviderError("unavailable", "unavailable"))
        except Exception as e:
            err = provider_health.record_failure(provider_id, e)
            _log(f"{provider_id} falhou ({err.error_type}), tentando próximo.")
            continue

    if mode == "local":
        return {
            "status": "provider_unavailable",
            "reason": "ollama_unavailable_or_model_missing",
            "text": _PROVIDER_UNAVAILABLE_MSG,
            "tools": [],
        }

    if mode in ("cloud", "auto"):
        if provider_health.is_in_cooldown("openrouter"):
            return {
                "text": _PROVIDER_UNAVAILABLE_MSG,
                "tools": [],
            }
    return None


def stream_text(user_text: str, history: list[dict]):
    """Stream raw text (sem tool-use). Claude pela assinatura, com fallback OpenAI.
    Retorna generator ou None se nenhum provedor disponível."""
    import claude_brain
    if claude_brain.available():
        ctx = _history_context(history)
        gen = claude_brain.answer_stream(user_text, context=ctx, system=_system())
        first = next(gen, None)
        if first is not None:
            def _iter_claude():
                yield first
                yield from gen
            return _iter_claude()

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=LLM_TIMEOUT, max_retries=1)
        messages: list[dict] = [{"role": "system", "content": _system()}]
        for h in _compact_history(history):
            if h.get("content"):
                messages.append({"role": h.get("role", "user"), "content": h["content"]})
        messages.append({"role": "user", "content": user_text})
        stream = client.chat.completions.create(
            model=OPENAI_MODEL, messages=messages, stream=True
        )

        def _iter():
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return _iter()
    except Exception:
        return None
