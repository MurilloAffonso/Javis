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
6. NÃO FINJA QUE FEZ: Nunca diga que "executou", "iniciou", "criou", "terminou" ou "já fez" algo se nenhuma ferramenta foi realmente chamada para isso nesta resposta. Se não há ferramenta para a tarefa, diga a verdade — o que falta, ou ofereça a ação real — em vez de afirmar que já está feito.

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


def _history_context(history: list[dict] | None, limit: int = 4) -> str:
    """Resume as últimas trocas para dar contexto ao cérebro de raciocínio."""
    if not history:
        return ""
    linhas = []
    for h in history[-limit:]:
        c = (h.get("content") or "").strip()
        if not c:
            continue
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
        # Motor escolhido por Murillo (botão Claude/Codex); com fallback automático.
        import brain_switch
        return brain_switch.dispatch(tarefa)
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

    pedido = (
        "Monte a PAUTA DA SEMANA com EXATAMENTE 3 posts pro Instagram da Vem Passear, "
        "respeitando a regra de no máximo 1 de venda direta. Varie os pilares. Para cada "
        "post traga: dia e data, pilar, formato, gancho 3s, legenda no tom da marca, "
        "material visual necessário, CTA e hashtags. No fim, escreva 'Status: pauta "
        "proposta — aguardando aprovação do Murillo (Gate 1)'."
    )
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
        repo.tasks.set_status("pipeline-marketing-vem-passear-jampa-t0", "done")
        repo.approvals.add(
            subject="Aprovar a pauta da semana da Vem Passear (Gate 1) antes de ir pro Design",
            kind="gate", agent="nova", detail="_projetos/cerebro-jampa/posts/pauta-semana.md",
        )
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


def _system() -> str:
    from datetime import datetime
    dias = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    n = datetime.now()
    hora = f"{n.strftime('%H:%M')}, {dias[n.weekday()]}, {n.day} de {meses[n.month-1]} de {n.year}"
    base = SYSTEM_AGENT.replace("{hora_atual}", hora)
    try:
        import profile
        base = base + profile.context_block()
    except Exception:
        pass
    # Injeta o ESTADO REAL do projeto: assim o cérebro sabe "o que a gente fez"
    # sem depender de acionar a ferramenta de conhecimento.
    try:
        import briefing
        estado = briefing.estado_resumido()
        if estado:
            base += (
                "\n\n## Estado atual do projeto Javis (use para responder o que foi "
                "feito e o que está pendente; não invente nada fora disto):\n" + estado
            )
    except Exception:
        pass
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
                    out = _exec_tool(block.name, block.input, history)
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
                out = _exec_tool(tc.function.name, args, history)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": out or "feito"})
            continue
        return {"text": (msg.content or "").strip(), "tools": used}
    return {"text": "Executei o que era possível, senhor.", "tools": used}


def _tool_catalog() -> str:
    """Lista compacta das ferramentas pro prompt do Claude pela assinatura."""
    lines = []
    for t in TOOLS:
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
    system = _system() + (
        "\n\nFerramentas disponíveis:\n" + _tool_catalog() +
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
    base_ctx = _history_context(history)
    transcript = ""
    used: list[str] = []
    for _ in range(max_rounds):
        ctx = f"{base_ctx}\n\n{transcript}".strip() if transcript else base_ctx
        out = claude_brain.answer(user_text, context=ctx, system=system, model=CLAUDE_MODEL)
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


def respond(user_text: str, history: list[dict] | None = None, max_rounds: int = 5) -> dict | None:
    """Loop de tool-use. Cascata: Claude (assinatura) → OpenAI → Claude API → OpenRouter.
    Decisão Murillo 18/06: a assinatura é o cérebro principal; o resto é fallback
    pra quando o Claude Code não estiver disponível, não rota padrão.
    Retorna {text, tools} ou None se nenhum provedor disponível."""
    history = history or []

    # 1) Claude pela assinatura — primário (sem custo de API)
    try:
        out = _respond_claude_subscription(user_text, history, max_rounds)
        if out is not None:
            return out
    except Exception as e:
        _log(f"Claude (assinatura) falhou, tentando próximo: {e}")

    # 2) OpenAI — só se a assinatura estiver indisponível
    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            return _respond_openai(user_text, history, max_rounds)
        except Exception as e:
            _log(f"OpenAI (tool-use) falhou, tentando próximo: {e}")

    # 3) Claude (Anthropic API) — se tiver crédito
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        try:
            return _respond_claude(user_text, history, max_rounds)
        except Exception as e:
            _log(f"Claude (tool-use) falhou, tentando próximo: {e}")

    # 4) OpenRouter — requer cartão cadastrado em openrouter.ai
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        try:
            return _respond_openrouter(user_text, history, max_rounds)
        except Exception as e:
            _log(f"OpenRouter (tool-use) falhou: {e}")
            return {"text": f"Tive um problema ao executar, senhor: {e}", "tools": []}

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
