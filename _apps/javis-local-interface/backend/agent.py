"""Agent — cérebro com tool-use (function calling) do Jamba.

Em vez de roteamento por palavra-chave, o Claude DECIDE qual ferramenta chamar,
entende intenção (não palavra exata) e ENCADEIA ações ("abre o youtube e toca jazz").

Degrada com elegância: sem ANTHROPIC_API_KEY, retorna None e o chamador usa o fallback.
"""
from __future__ import annotations
import os
import json

import actions

CLAUDE_MODEL = os.environ.get("JAVIS_CLAUDE_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.environ.get("JAVIS_OPENAI_MODEL", "gpt-4o-mini")

# Timeout (s) por chamada de LLM — evita que a cascata empilhe espera invisível
# quando um provedor está lento ou sem crédito (causa nº 1 de "travamento").
LLM_TIMEOUT = float(os.environ.get("JAVIS_LLM_TIMEOUT", "20"))


def _log(msg: str) -> None:
    """Log visível no console do servidor — para de engolir falhas em silêncio."""
    import sys
    print(f"[agent] {msg}", file=sys.stderr, flush=True)

SYSTEM_AGENT = """Você é Jamba, assistente pessoal de Murillo Affonso.

REGRAS ABSOLUTAS — NUNCA VIOLAR:
1. IDIOMA: Responda SEMPRE em português do Brasil. NUNCA em inglês, espanhol ou outro idioma.
2. TRATAMENTO: Chame o usuário de "senhor" ou "Murillo" — nunca "você" ou "user".
3. VOZ: Respostas são lidas em voz alta — seja CONCISO. Máximo 2 frases para ações. Sem markdown.
4. AÇÃO: Quando houver uma ferramenta disponível, USE-A. Não descreva o que faria — faça.
5. SEM IMPROVISO: Nunca invente dados (preços, horários, endereços). Use as ferramentas.

PERFIL DE MURILLO:
- Empreendedor, fundador da Vem Passear em Jampa (turismo em João Pessoa/PB)
- Usa o Jamba para automatizar tarefas e agilizar operações
- Prefere respostas diretas e curtas

Hora atual: {hora_atual}
"""

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
        "description": "Verifica o status dos serviços do sistema (Ollama, Open WebUI, etc.).",
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
        "description": "Delega uma tarefa de EXECUÇÃO ao motor de execução (Claude Code pela assinatura): escrever/alterar código, criar arquivos, rodar comandos/testes ou tarefas multi-step dentro do projeto. Use quando o senhor pedir para 'programar', 'criar', 'executar' ou 'fazer' algo no projeto. Roda em segundo plano e avisa ao terminar.",
        "input_schema": {
            "type": "object",
            "properties": {"tarefa": {"type": "string", "description": "Descrição clara da tarefa a executar."}},
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
]


def _exec_tool(name: str, inp: dict) -> str:
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
        # Execução pela ASSINATURA do Claude (Claude Code headless); Codex como reserva.
        import claude_exec
        if claude_exec.available():
            return claude_exec.dispatch(tarefa)
        import code_agent
        return code_agent.dispatch(tarefa)
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
        ctx = knowledge.answer_context(inp.get("pergunta") or "")
        return ctx or "Não encontrei nada nos seus arquivos sobre isso, senhor."
    # ações sem parâmetro
    return actions.execute(name, "").get("message", "Feito, senhor.")


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


def _system() -> str:
    from datetime import datetime
    dias = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    n = datetime.now()
    hora = f"{n.strftime('%H:%M')}, {dias[n.weekday()]}, {n.day} de {meses[n.month-1]} de {n.year}"
    base = SYSTEM_AGENT.replace("{hora_atual}", hora)
    try:
        import profile
        return base + profile.context_block()
    except Exception:
        return base


def _respond_claude(user_text: str, history: list[dict], max_rounds: int) -> dict:
    """Tool-use via Claude (Anthropic). Levanta exceção em erro (p/ permitir fallback)."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=LLM_TIMEOUT)
    messages: list[dict] = []
    for h in history[-6:]:
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    used: list[str] = []
    for _ in range(max_rounds):
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=1024,
            system=_system(), tools=TOOLS, messages=messages,
        )
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    used.append(block.name)
                    out = _exec_tool(block.name, block.input)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": out or "feito"})
            messages.append({"role": "user", "content": results})
            continue
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return {"text": text.strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def _respond_openrouter(user_text: str, history: list[dict], max_rounds: int) -> dict:
    """Tool-use via OpenRouter (Llama 3.3 70B gratuito ou outros modelos)."""
    from openai import OpenAI
    model = os.environ.get("JAVIS_OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=LLM_TIMEOUT,
    )
    oai_tools = [
        {"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in TOOLS
    ]
    messages: list[dict] = [{"role": "system", "content": _system()}]
    for h in history[-6:]:
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    used: list[str] = []
    for _ in range(max_rounds):
        resp = client.chat.completions.create(model=model, messages=messages, tools=oai_tools)
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
                out = _exec_tool(tc.function.name, args)
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
        for t in TOOLS
    ]
    messages: list[dict] = [{"role": "system", "content": _system()}]
    for h in history[-6:]:
        if h.get("content"):
            messages.append({"role": h.get("role", "user"), "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    used: list[str] = []
    for _ in range(max_rounds):
        resp = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, tools=oai_tools)
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
                out = _exec_tool(tc.function.name, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": out or "feito"})
            continue
        return {"text": (msg.content or "").strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def respond(user_text: str, history: list[dict] | None = None, max_rounds: int = 5) -> dict | None:
    """Loop de tool-use. Cascata: OpenAI → Claude → OpenRouter.
    Retorna {text, tools} ou None se nenhum provedor disponível."""
    history = history or []

    # 1) OpenAI — primário (rápido, estável)
    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            return _respond_openai(user_text, history, max_rounds)
        except Exception as e:
            _log(f"OpenAI (tool-use) falhou, tentando próximo: {e}")

    # 2) Claude (Anthropic) — se tiver crédito
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        try:
            return _respond_claude(user_text, history, max_rounds)
        except Exception as e:
            _log(f"Claude (tool-use) falhou, tentando próximo: {e}")

    # 3) OpenRouter — requer cartão cadastrado em openrouter.ai
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        try:
            return _respond_openrouter(user_text, history, max_rounds)
        except Exception as e:
            _log(f"OpenRouter (tool-use) falhou: {e}")
            return {"text": f"Tive um problema ao executar, senhor: {e}", "tools": []}

    return None


def stream_text(user_text: str, history: list[dict]):
    """Stream raw text tokens via OpenAI (sem tool-use). Retorna generator ou None se indisponível."""
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=LLM_TIMEOUT, max_retries=1)
        messages: list[dict] = [{"role": "system", "content": _system()}]
        for h in (history or [])[-6:]:
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
