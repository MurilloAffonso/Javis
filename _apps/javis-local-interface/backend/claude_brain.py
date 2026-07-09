"""claude_brain.py — cérebro de RACIOCÍNIO do Jamba via ASSINATURA do Claude.

Diferente do claude_exec.py (que EXECUTA tarefas no projeto: cria/edita arquivos,
roda comandos), este módulo usa o Claude Code headless apenas para PENSAR:
decisões estratégicas, análises a fundo, conselhos. Roda pela ASSINATURA do
Murillo (Opus 4.8 por padrão), sem gastar crédito da API Anthropic.

Arquitetura "dois níveis" (decisão Murillo 18/06: só Claude por assinatura,
sem API paga da OpenAI/Anthropic):
  Voz/papo/ações rápidas → Claude Haiku pela assinatura (`_VOICE_MODEL`)
  Raciocínio pesado      → Claude Opus 4.8 pela assinatura  ← ESTE módulo

`llm_providers.py` (camada compartilhada por Conclave, squads, analyzers etc.)
chama este módulo como cérebro ÚNICO. Sem Ollama (decisão 19/06): se a
assinatura faltar/zerar, o sistema diz isso na cara, não cai em fallback local.

É SÍNCRONO: o cérebro principal precisa da resposta para falar. Bounded por
timeout para não travar a voz se o subprocesso demorar demais.

CRÍTICO: o subprocesso roda com ANTHROPIC_API_KEY REMOVIDA do ambiente, senão o
Claude Code tentaria a API (sem crédito) em vez da assinatura — igual ao
claude_exec.py.
"""
from __future__ import annotations
import os
import json as _json
import shutil
import subprocess
import threading
from pathlib import Path

import safe_config

JAVIS_ROOT = Path(__file__).resolve().parents[3]

# Opus 4.8 = mais novo e capaz. Trocável pelo .env (alias 'opus'/'sonnet' ou ID).
_MODEL    = os.environ.get("JAVIS_CLAUDE_BRAIN_MODEL", "claude-opus-4-8")
# Se o modelo escolhido não estiver disponível na assinatura, cai no sonnet.
_FALLBACK = os.environ.get("JAVIS_CLAUDE_BRAIN_FALLBACK", "sonnet")
# Voz = prioridade velocidade/leveza (decisão Murillo 18/06): Haiku é o modelo
# mais rápido e mais barato em cota da assinatura. Opus fica só pro raciocínio
# pesado (texto/conclave), que não tem pressa de resposta falada.
_VOICE_MODEL = os.environ.get("JAVIS_CLAUDE_VOICE_MODEL", "claude-haiku-4-5-20251001")
# Raciocínio é mais rápido que execução; teto generoso mas não infinito.
_TIMEOUT  = int(os.environ.get("JAVIS_CLAUDE_BRAIN_TIMEOUT", "120"))

_CLAUDE_BIN: str | None = shutil.which("claude")

_SYSTEM = (
    "Você é o cérebro de RACIOCÍNIO do Jamba, assistente pessoal de Murillo "
    "Affonso — fundador da Vem Passear em Jampa (turismo em João Pessoa/PB). "
    "Pense com profundidade e devolva uma resposta DIRETA e CONCISA em português "
    "do Brasil. A resposta será LIDA EM VOZ ALTA: no máximo 4-5 frases, sem "
    "markdown, sem listas longas. Trate-o por 'senhor'. Não use ferramentas nem "
    "edite arquivos — apenas raciocine e responda. "
    "NUNCA afirme que executou, iniciou, criou ou terminou uma tarefa: você só "
    "pensa e responde, não age. Se algo precisa ser FEITO, diga que vai pedir a "
    "ação ou o que falta — não finja que já está pronto."
)


def available() -> bool:
    return safe_config.claude_exec_enabled() and _CLAUDE_BIN is not None


def _env() -> dict:
    """Ambiente do subprocesso SEM ANTHROPIC_API_KEY → força login por assinatura."""
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def answer(question: str, context: str = "", system: str | None = None, timeout: int | None = None,
           model: str | None = None, add_dirs: list[str] | None = None) -> str:
    """Raciocina sobre a pergunta com o Claude (assinatura) e retorna o texto.

    Retorna "" se o Claude Code não estiver disponível, para o chamador cair no
    fallback (ex.: conclave OpenAI).

    `system`   — sobrescreve o system prompt (por padrão usa o de voz, curto).
                 Os agentes (ex.: Architect) passam a própria persona+skill aqui.
    `timeout`  — sobrescreve o teto de tempo (agentes de design podem precisar mais).
    `model`    — sobrescreve o modelo (ex.: voz usa Haiku, mais rápido/leve).
    `add_dirs` — pastas extras que o Claude pode LER (ex.: Downloads p/ analisar
                 um arquivo fora do projeto). Read continua liberado; Bash/Edit/
                 Write seguem bloqueados — então é leitura segura, não escrita.
    """
    question = (question or "").strip()
    if not question:
        return "Sobre o que devo pensar, senhor?"
    if not available():
        return ""
    prompt = question if not context.strip() else f"Contexto: {context.strip()}\n\nPergunta: {question}"
    cmd = [
        _CLAUDE_BIN, "-p", prompt,
        "--model", model or _MODEL,
        "--fallback-model", _FALLBACK,
        "--output-format", "text",
        "--permission-mode", "default",
        # Raciocínio puro: bloqueia ações para não tentar mexer no projeto.
        "--disallowedTools", "Bash", "Edit", "Write",
        "--append-system-prompt", system or _SYSTEM,
    ]
    for d in (add_dirs or []):
        cmd += ["--add-dir", d]
    try:
        proc = subprocess.run(
            cmd, cwd=str(JAVIS_ROOT), env=_env(),
            # stdin fechado: sem isso o claude espera 3s por stdin (latência morta).
            stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout or _TIMEOUT,
        )
        out = (proc.stdout or "").strip()
        if not out:
            err = (proc.stderr or "").strip()
            return f"Pensei mas não consegui formular, senhor.{(' (' + err[-200:] + ')') if err else ''}"
        return out
    except subprocess.TimeoutExpired:
        return f"Levei mais que o tempo disponível pensando nisso, senhor. Pode reformular ou simplificar?"
    except Exception:
        return ""


def answer_with_usage(question: str, context: str = "", system: str | None = None, timeout: int | None = None,
                      model: str | None = None, add_dirs: list[str] | None = None) -> tuple[str, dict]:
    """Igual a answer(), mas devolve (texto, usage_dict) — usa --output-format json
    para o Claude Code retornar `usage` (input/output/cache_*tokens) na resposta.

    Usado para TELEMETRIA de tokens da rota da assinatura. Se algo falhar na
    parsing, usage volta vazio ({}); o texto continua sendo retornado normalmente.
    """
    question = (question or "").strip()
    if not question:
        return ("Sobre o que devo pensar, senhor?", {})
    if not available():
        return ("", {})
    prompt = question if not context.strip() else f"Contexto: {context.strip()}\n\nPergunta: {question}"
    cmd = [
        _CLAUDE_BIN, "-p", prompt,
        "--model", model or _MODEL,
        "--fallback-model", _FALLBACK,
        "--output-format", "json",
        "--permission-mode", "default",
        "--disallowedTools", "Bash", "Edit", "Write",
        "--append-system-prompt", system or _SYSTEM,
    ]
    for d in (add_dirs or []):
        cmd += ["--add-dir", d]
    try:
        proc = subprocess.run(
            cmd, cwd=str(JAVIS_ROOT), env=_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout or _TIMEOUT,
        )
        raw = (proc.stdout or "").strip()
        if not raw:
            return ("", {})
        try:
            obj = _json.loads(raw)
        except Exception:
            return (raw, {})
        text = (obj.get("result") or "").strip()
        usage = obj.get("usage") or {}
        return (text, usage)
    except subprocess.TimeoutExpired:
        return ("Levei mais que o tempo disponível pensando nisso, senhor. Pode reformular ou simplificar?", {})
    except Exception:
        return ("", {})


def answer_stream(question: str, context: str = "", model: str | None = None, system: str | None = None):
    """Igual a answer(), mas GERA o texto em pedaços conforme o modelo produz —
    para a voz começar a falar frase a frase em vez de esperar o bloco todo.

    Yields str (deltas de texto). Não emite nada se o Claude Code estiver
    indisponível — o chamador deve checar e cair no fallback.

    `model`  — sobrescreve o modelo padrão (voz usa Haiku via `_VOICE_MODEL`).
    `system` — sobrescreve o system prompt (outros cérebros passam o próprio).
    """
    question = (question or "").strip()
    if not question or not available():
        return
    prompt = question if not context.strip() else f"Contexto: {context.strip()}\n\nPergunta: {question}"
    cmd = [
        _CLAUDE_BIN, "-p", prompt,
        "--model", model or _MODEL,
        "--fallback-model", _FALLBACK,
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--verbose",
        "--permission-mode", "default",
        "--disallowedTools", "Bash", "Edit", "Write",
        "--append-system-prompt", system or _SYSTEM,
    ]
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(JAVIS_ROOT), env=_env(),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True,
            encoding="utf-8", errors="replace", bufsize=1,
        )
    except Exception:
        return
    # Watchdog: mata o processo se passar do timeout (não trava a voz).
    killer = threading.Timer(_TIMEOUT, proc.kill)
    killer.start()
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = _json.loads(line)
            except Exception:
                continue
            if obj.get("type") != "stream_event":
                continue
            ev = obj.get("event") or {}
            if ev.get("type") == "content_block_delta":
                d = ev.get("delta") or {}
                if d.get("type") == "text_delta" and d.get("text"):
                    yield d["text"]
    finally:
        killer.cancel()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
