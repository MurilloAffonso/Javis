import sys
import time
from pathlib import Path

# server.py faz imports de irmãos ("import agent", "import actions" etc.)
# assumindo que backend/ está no sys.path — verdade quando se roda
# `python backend/server.py` direto, mas falso ao importar como pacote
# (backend.server) a partir da raiz do projeto, como o Chainlit faz aqui.
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

import chainlit as cl
from chainlit.input_widget import Select, Switch
from backend.server import _brain  # O seu motor único de decisão (NÃO alterado)
import command_router            # classificação de intenção + risk_level
import file_analyzer             # análise de arquivos (PDF/Office/img)
import ui_state                  # adaptador read-only de projetos/squads/agentes

# Avatares: arquivos estáticos em public/avatars/<nome_normalizado>.<ext>
# (javis, conclave_ai, claude_code_exec, obsidian_rag). Sem API Python nesta versão.

# --- MODOS OPERACIONAIS -----------------------------------------------------
# Cada modo SÓ injeta contexto adicional no texto e/ou liga o conclave.
# Nunca altera _brain(): a execução continua passando pela whitelist + risk_level.
MODOS = [
    "Conversa",
    "Análise de Arquivo",
    "Transformar Referência em Base",
    "Criar Squad",
    "Executar Tarefa",
    "Conclave",
    "Somente Leitura",
]

_PREAMBULOS = {
    "Análise de Arquivo": "[modo: análise de arquivo] Foque em ler e resumir o material fornecido.",
    "Transformar Referência em Base": "[modo: referência→base] Extraia o conteúdo e estruture como base de conhecimento reutilizável.",
    "Criar Squad": "[modo: criar squad] Ajude a desenhar um squad: missão, agentes, inputs, outputs, ferramentas e o que exige aprovação humana.",
    "Executar Tarefa": "[modo: executar tarefa] Trate como tarefa de execução; use a ferramenta de execução quando fizer sentido.",
    "Somente Leitura": "[modo: somente leitura] NÃO execute nenhuma ação no sistema. Apenas responda, analise e sugira.",
}


def _est_tokens(texto: str) -> int:
    """Estimativa simples (~4 chars/token). Heurística, não cobrança real."""
    return max(0, len(texto or "") // 4)


def _telemetria_md(out: dict, est_in: int, est_out: int, elapsed: float,
                   projeto: str, modo: str) -> str:
    route = out.get("route", {}) or {}
    tools = out.get("tools", []) or []
    return (
        "📊 **Telemetria da execução**\n\n"
        f"- Projeto ativo: `{projeto}` · Modo: `{modo}`\n"
        f"- Intent: `{out.get('intent', '?')}` · Brain: `{out.get('brain', '?')}` · Status: `{out.get('status', '?')}`\n"
        f"- Risk level: `{route.get('risk_level', 'none')}` · Aprovação exigida: `{route.get('requires_approval', False)}` · Confiança: `{route.get('confidence', '?')}`\n"
        f"- Tools acionadas: `{', '.join(tools) if tools else 'nenhuma'}`\n"
        f"- Tokens estimados: entrada `{est_in}` · saída `{est_out}` · total `{est_in + est_out}`\n"
        f"- Tempo de execução: `{elapsed:.2f}s`"
    )


@cl.on_chat_start
async def start():
    # --- PAINEL LATERAL DE CONTROLE ---
    await cl.ChatSettings(
        [
            Select(
                id="projeto_ativo",
                label="🗂️ Projeto Ativo",
                values=ui_state.project_options(),
                initial_index=0,
            ),
            Select(
                id="modo_operacao",
                label="🛠️ Modo de Operação",
                values=MODOS,
                initial_index=0,
            ),
            Switch(id="use_conclave", label="🔥 Ativar Conclave (Debate de Agentes)", initial=False),
            Select(
                id="modelo_llm",
                label="🧠 Cérebro Principal (Modelo)",
                values=["claude-3-5-sonnet", "gpt-4o", "ollama-local"],
                initial_index=0,
            ),
        ]
    ).send()

    # Defaults da sessão
    cl.user_session.set("projeto_ativo", ui_state.project_options()[0])
    cl.user_session.set("modo_operacao", MODOS[0])
    cl.user_session.set("use_conclave", False)
    cl.user_session.set("history", [])

    await cl.Message(
        content=(
            "**Sistemas Inicializados, Senhor.**\n"
            "Central de Comando online. Use o painel lateral (⚙️) para escolher "
            "**Projeto Ativo** e **Modo de Operação**."
        ),
        author="Javis"
    ).send()


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("projeto_ativo", settings.get("projeto_ativo", "Geral"))
    cl.user_session.set("modo_operacao", settings.get("modo_operacao", "Conversa"))
    cl.user_session.set("use_conclave", settings.get("use_conclave", False))
    cl.user_session.set("modelo_llm", settings.get("modelo_llm", "claude-3-5-sonnet"))

    await cl.Message(
        content=(
            f"⚙️ Configurações atualizadas, senhor.\n"
            f"- Projeto: **{settings.get('projeto_ativo')}**\n"
            f"- Modo: **{settings.get('modo_operacao')}**\n"
            f"- Conclave: **{settings.get('use_conclave')}**"
        ),
        author="Javis"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history") or []
    projeto = cl.user_session.get("projeto_ativo", "Geral")
    modo = cl.user_session.get("modo_operacao", "Conversa")

    # --- RECEBIMENTO DE ARQUIVOS (clipe de papel) ---
    if message.elements:
        for element in message.elements:
            async with cl.Step(name=f"📎 Análise de arquivo: {element.name}") as file_step:
                resultado = await cl.make_async(file_analyzer.analyze)(element.path, message.content)
                file_step.output = resultado.get("message", "Não consegui analisar o arquivo, senhor.")
            await cl.Message(
                content=resultado.get("message", "Não consegui analisar o arquivo, senhor."),
                author="Javis"
            ).send()
        if not message.content.strip():
            return

    texto = message.content

    # --- GATE DE SEGURANÇA: ação crítica bloqueada antes de qualquer execução ---
    # (espelha o server.py /chat; respeita a whitelist + risk_level existentes)
    route = command_router.route(texto)
    if route.get("risk_level") == "critical":
        async with cl.Step(name="🛑 Aprovação humana necessária") as gate:
            gate.output = (
                f"Ação classificada como **crítica** (`{route.get('intent')}`) e BLOQUEADA, senhor. "
                "Por segurança, não executo isto automaticamente."
            )
        await cl.Message(
            content="🛑 Ação bloqueada por segurança (risco crítico). Preciso de confirmação explícita e fora do modo automático, senhor.",
            author="Javis"
        ).send()
        return

    # --- GATE DE APROVAÇÃO: risco médio / requires_approval vira aprovação real ---
    # Cria um Gate no backend (aparece no painel direito do Command Center) em vez
    # de executar direto. Aprovado lá → o senhor reexecuta a ação com segurança.
    if route.get("requires_approval"):
        aid = None
        try:
            import repositories as repo
            aid = repo.approvals.add(subject=texto[:120], kind="gate",
                                     agent="javis-core", detail=f"intent={route.get('intent')} risco={route.get('risk_level')}")
        except Exception:
            pass
        async with cl.Step(name="⏳ Aprovação humana necessária") as g:
            g.output = (f"Ação `{route.get('intent')}` (risco {route.get('risk_level')}) "
                        f"registrada como aprovação pendente{(' #' + str(aid)) if aid else ''}.")
        await cl.Message(
            content=(f"Isto precisa da sua aprovação, senhor. Registrei o gate"
                     f"{(' #' + str(aid)) if aid else ''} — aprove no **Command Center** (painel direito) e eu sigo."),
            author="Javis"
        ).send()
        return

    # --- CONTEXTO ADICIONAL por projeto + modo (não toca no _brain) ---
    preambulo = _PREAMBULOS.get(modo, "")
    contexto = f"[projeto ativo: {projeto}]"
    if preambulo:
        contexto += f" {preambulo}"
    texto_para_brain = f"{contexto}\n\n{texto}" if contexto else texto

    # Modo Conclave força o debate; senão respeita o switch lateral.
    ativar_debate = (modo == "Conclave") or cl.user_session.get("use_conclave", False)

    # --- ROTEAMENTO + EXECUÇÃO (núcleo único) ---
    inicio = time.perf_counter()
    async with cl.Step(name="🧭 Orquestrador Central: roteando comando...") as root_step:
        root_step.input = texto
        out = await cl.make_async(_brain)(
            text=texto_para_brain,
            history=history,
            use_conclave=ativar_debate,
        )
        intent = out.get("intent", "conversa")
        brain_used = out.get("brain", "main")
        status = out.get("status", "ok")
        tools = out.get("tools", []) or []
        root_step.output = f"Intent: `{intent}` · Canal: `{brain_used}` · Status: `{status}`"
    elapsed = time.perf_counter() - inicio

    # --- STEPS por capacidade acionada ---
    if brain_used == "conclave":
        async with cl.Step(name="⚖️ Conclave: debate de agentes") as s:
            s.output = "Crítico × Advogado × Sintetizador deliberaram para chegar à síntese."

    for tool in tools:
        if "programar" in tool or "claude_exec" in tool or "exec" in tool:
            async with cl.Step(name="⚡ Execução: Claude Code (assinatura)") as s:
                s.output = "Tarefa multi-step executada headless via assinatura, dentro da whitelist."
        elif "conhecimento" in tool or "knowledge" in tool:
            async with cl.Step(name="📚 Busca de conhecimento (Obsidian RAG)") as s:
                s.output = "Notas do Obsidian e base do projeto consultadas."
        else:
            async with cl.Step(name=f"🔧 Capacidade: {tool}") as s:
                s.output = f"Ferramenta `{tool}` acionada."

    # --- Autor (avatar) conforme o cérebro vencedor ---
    autor_final = "Javis"
    if brain_used == "conclave":
        autor_final = "Conclave AI"
    elif status == "agent" and any(("programar" in t or "exec" in t) for t in tools):
        autor_final = "Claude Code Exec"

    resposta_final = out.get("text", "Pronto, senhor.")
    await cl.Message(content=resposta_final, author=autor_final).send()

    # --- TELEMETRIA VISUAL ao final ---
    est_in = _est_tokens(texto_para_brain) + sum(_est_tokens(m.get("content", "")) for m in history)
    est_out = _est_tokens(resposta_final)
    async with cl.Step(name="📊 Telemetria") as tel:
        tel.output = _telemetria_md(out, est_in, est_out, elapsed, projeto, modo)

    # --- Histórico ---
    history.append({"role": "user", "content": texto})
    history.append({"role": "assistant", "content": resposta_final})
    cl.user_session.set("history", history)
