"""Javis v2 — FastAPI server.

Endpoints:
  GET  /              → serve frontend
  POST /chat          → orchestrator pipeline
  GET  /status        → system status
  GET  /agents        → list agents
  GET  /history       → chat history (last 50)
"""
from __future__ import annotations
import sys
import socket
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Carrega variáveis de ambiente do .env na raiz do projeto
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

import command_router
import actions
import logger
from orchestrator import Orchestrator

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
HISTORY_FILE = Path(__file__).resolve().parent.parent / "logs" / "chat_history.jsonl"
HISTORY_FILE.parent.mkdir(exist_ok=True)

app = FastAPI(title="Javis v2", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

orchestrator = Orchestrator()
_history: list[dict] = []


@app.on_event("startup")
async def _start_integrations():
    """Liga serviços de segundo plano: Telegram e checador de lembretes."""
    try:
        import telegram_bridge
        if telegram_bridge.start_background():
            print("  Telegram: conectado ✓")
    except Exception as e:
        print(f"  Telegram: não iniciado ({e})")
    try:
        import reminders
        reminders.start_background()
        print("  Lembretes: checador ativo ✓")
    except Exception as e:
        print(f"  Lembretes: não iniciado ({e})")
    try:
        import knowledge
        knowledge.start_background_index()
        print("  Conhecimento: indexando vault em segundo plano ✓")
    except Exception as e:
        print(f"  Conhecimento: não iniciado ({e})")


@app.post("/knowledge/reindex")
async def knowledge_reindex():
    """Reindexa os arquivos do vault (incremental)."""
    import knowledge
    result = await run_in_threadpool(knowledge.build_index, False)
    return JSONResponse(result)


@app.get("/knowledge/search")
async def knowledge_search(q: str = ""):
    import knowledge
    hits = await run_in_threadpool(knowledge.search, q, 5)
    return JSONResponse({"hits": hits})


@app.get("/reminders/poll")
async def reminders_poll():
    """Lembretes que venceram desde a última checagem (interface fala por TTS)."""
    try:
        import reminders
        return JSONResponse({"due": reminders.pop_due()})
    except Exception:
        return JSONResponse({"due": []})


@app.get("/reminders")
async def reminders_list():
    try:
        import reminders
        return JSONResponse({"pending": reminders.list_pending()})
    except Exception:
        return JSONResponse({"pending": []})

SERVICES = {
    "Open WebUI":  3000,
    "Ollama":      11434,
    "Voz sandbox": 12393,
}


class ChatRequest(BaseModel):
    message: str
    use_conclave: bool = False
    model: str = "llama3.2:3b"


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index = FRONTEND_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.get("/style.css")
async def serve_css():
    return FileResponse(FRONTEND_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


# ── Painel (dashboard) — arquivos criados pelo Codex ──
@app.get("/painel", response_class=HTMLResponse)
async def serve_painel():
    f = FRONTEND_DIR / "painel.html"
    if f.exists():
        return HTMLResponse(f.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Painel ainda não criado</h1>", status_code=404)


@app.get("/painel.css")
async def serve_painel_css():
    f = FRONTEND_DIR / "painel.css"
    return FileResponse(f, media_type="text/css") if f.exists() else JSONResponse({"error": "não criado"}, status_code=404)


@app.get("/painel.js")
async def serve_painel_js():
    f = FRONTEND_DIR / "painel.js"
    return FileResponse(f, media_type="application/javascript") if f.exists() else JSONResponse({"error": "não criado"}, status_code=404)


@app.get("/profile")
async def get_profile():
    """Fatos que o Jamba sabe sobre o senhor (para o painel)."""
    try:
        import profile
        return JSONResponse({"facts": profile.list_facts()})
    except Exception:
        return JSONResponse({"facts": []})


@app.get("/integrations")
async def get_integrations():
    """Quais integrações estão configuradas (para o painel)."""
    try:
        import integrations
        return JSONResponse(integrations.available())
    except Exception:
        return JSONResponse({})


@app.post("/chat")
async def chat(req: ChatRequest):
    start = datetime.now()
    text  = req.message.strip()
    if not text:
        return JSONResponse({"error": "Mensagem vazia"}, status_code=400)

    orchestrator.model = req.model

    # 1. Keyword routing para ações locais rápidas
    route = command_router.route(text)

    # 2. Ações críticas bloqueadas imediatamente
    if route["risk_level"] == "critical":
        entry = _make_entry("blocked", text, route, {"status": "blocked"}, start)
        _save(entry)
        return JSONResponse(entry)

    # 3. Orquestrador LLM (run_in_threadpool evita bloquear o event loop)
    result = await run_in_threadpool(orchestrator.process, text, _get_history_messages())

    # 4. Se orquestrador identificou ação local, executa
    action_intent = result.action_intent or route["intent"]
    action_result = {"status": "llm", "message": result.response}

    if result.requires_action and action_intent not in ("conversa", "desconhecido"):
        action_result = actions.execute(action_intent, text)
    elif route["intent"] not in ("conversa", "desconhecido") and not result.response:
        action_result = actions.execute(route["intent"], text)

    # 5. Resposta final
    response_text = (
        action_result.get("message", "")
        if action_result.get("status") in ("ok", "blocked")
        else result.response or action_result.get("message", "Sem resposta.")
    )

    entry = _make_entry("ok", text, route, action_result, start, result)
    entry["response"] = response_text
    _save(entry)

    return JSONResponse(entry)


class DebateRequest(BaseModel):
    task:    str
    agents:  list[str] = ["architect", "developer", "analyst"]
    rounds:  int = 2
    model:   str = "llama3.2:3b"


@app.post("/debate")
async def debate(req: DebateRequest):
    """Debate autônomo de squad — agentes debatem entre si sem intervenção do usuário."""
    from agents.squad import Squad
    from agents.memory_bridge import MemoryBridge

    sq = Squad(model=req.model)
    result = sq.run(req.task, req.agents, rounds=req.rounds)

    if result.get("used") and result.get("synthesis"):
        mb = MemoryBridge()
        saved = mb.save_decision(req.task, result["synthesis"], req.agents)
        result["saved_to"] = saved

    return JSONResponse(result)


@app.get("/memory")
async def memory_recall(q: str = ""):
    """Busca na memória persistente do Javis."""
    from agents.memory_bridge import MemoryBridge
    mb = MemoryBridge()
    if q:
        return JSONResponse({"results": mb.recall(q), "query": q})
    return JSONResponse({"results": mb.recent_decisions(5)})


@app.get("/status")
async def status():
    services = {}
    for name, port in SERVICES.items():
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                services[name] = {"status": "online", "port": port}
        except OSError:
            services[name] = {"status": "offline", "port": port}
    return JSONResponse({"services": services, "ts": _ts()})


@app.get("/agents")
async def agents_list():
    from agents.specialized import get_agents_info
    from agents.meta import META_AGENTS_INFO
    conclave = [
        {"id": "critico",      "name": "Conclave Crítico",      "role": "Audita lógica e falhas",   "icon": "🔴", "color": "#ef4444", "group": "conclave"},
        {"id": "advogado",     "name": "Conclave Advogado",     "role": "Ataca o plano",             "icon": "⚔️", "color": "#f97316", "group": "conclave"},
        {"id": "sintetizador", "name": "Conclave Sintetizador", "role": "Integra a melhor solução",  "icon": "✅", "color": "#22c55e", "group": "conclave"},
    ]
    return JSONResponse({
        "agents":   get_agents_info(),
        "conclave": conclave,
        "meta":     META_AGENTS_INFO,
        "total":    len(get_agents_info()) + len(conclave) + len(META_AGENTS_INFO),
    })


class VoiceRequest(BaseModel):
    transcript: str
    model:       str  = "llama3.2:3b"
    use_conclave: bool = False
    tts:         bool = True


@app.post("/voice")
async def voice_input(req: VoiceRequest):
    """Processa transcrição de voz pelo pipeline completo — wake word strip, hallucination filter, orquestrador."""
    from voice_bridge import classify_voice, _strip_wake_word

    transcript = req.transcript.strip()
    if not transcript:
        return JSONResponse({"error": "Transcrição vazia"}, status_code=400)

    # Hallucination / wake-word filter
    vc = classify_voice(transcript)
    if vc.get("note") == "blocked_hallucination":
        return JSONResponse({
            "status": "blocked",
            "response": "Não entendi, pode repetir?",
            "source": "voice",
            "tts": True,
        })

    clean = _strip_wake_word(transcript) or transcript
    start = datetime.now()
    orchestrator.model = req.model

    route = command_router.route(clean)
    if route["risk_level"] == "critical":
        entry = _make_entry("blocked", clean, route, {"status": "blocked"}, start)
        entry["source"] = "voice"
        _save(entry)
        return JSONResponse({**entry, "response": "Ação bloqueada.", "tts": True})

    action_intent = route["intent"]

    # Atalho instantâneo: abridores de app inequívocos (sem conjunção "e")
    FAST_PATH = {
        "abrir_navegador", "abrir_openwebui", "abrir_javis",
        "abrir_vscode", "abrir_terminal", "abrir_projeto", "status_sistema",
    }
    if action_intent in FAST_PATH and " e " not in f" {clean.lower()} " and not _looks_like_question(clean):
        action_result = actions.execute(action_intent, clean)
        response_text = action_result.get("message", "Feito, senhor.")
        entry = _make_entry("ok", clean, route, action_result, start)
        entry["response"] = response_text
        entry["source"] = "voice"
        entry["original_transcript"] = transcript
        entry["tts"] = req.tts
        _save(entry)
        return JSONResponse(entry)

    # Cérebro AGENTE (tool-use) — entende intenção e encadeia ações
    import agent
    ag = await run_in_threadpool(agent.respond, clean, _get_history_messages())
    if ag is not None:
        response_text = ag["text"] or "Pronto, senhor."
        action_intent = ag["tools"][0] if ag.get("tools") else action_intent
        action_result = {"status": "agent", "message": response_text}
    else:
        # Fallback sem Claude
        response_text = await run_in_threadpool(orchestrator._main_brain, clean, _get_history_messages())
        action_result = {"status": "llm", "message": response_text}

    entry = _make_entry("ok", clean, route, action_result, start)
    entry["response"]             = response_text
    entry["source"]               = "voice"
    entry["original_transcript"]  = transcript
    entry["tts"]                  = req.tts
    _save(entry)

    # Memória cresce com padrões de voz (vida própria)
    try:
        from agents.memory_bridge import MemoryBridge
        MemoryBridge().save_voice_command(clean, action_intent, "main")
    except Exception:
        pass

    return JSONResponse(entry)


class RootcauseRequest(BaseModel):
    task:            str
    failed_response: str
    agents_used:     list[str] = []
    model:           str = "llama3.2:3b"


@app.post("/rootcause")
async def rootcause(req: RootcauseRequest):
    """Rootcause diagnostica uma resposta ruim e aprende para não repetir."""
    from agents.meta import Rootcause
    rc = Rootcause(model=req.model)
    result = rc.diagnose(req.task, req.failed_response, req.agents_used)
    return JSONResponse(result)


@app.get("/history")
async def history():
    return JSONResponse({"history": _history[-50:]})


# ── Streaming chat ────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Chat com streaming token-a-token (SSE)."""
    import json as _j
    from orchestrator import SYSTEM_MAIN_BRAIN

    text = req.message.strip()
    if not text:
        return JSONResponse({"error": "Mensagem vazia"}, status_code=400)

    orchestrator.model = req.model
    route  = command_router.route(text)

    if route["risk_level"] == "critical":
        def _blocked():
            yield f"data: {_j.dumps({'type':'done','text':'Ação bloqueada.','brain':'main','status':'blocked'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_blocked(), media_type="text/event-stream",
                                  headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    intent = route.get("intent", "conversa")
    brain  = "conclave" if req.use_conclave else "main"

    # Atalho instantâneo: comandos óbvios e únicos (sem precisar do LLM)
    # Apenas abridores de app inequívocos — tudo mais vai pro agente inteligente.
    FAST_PATH = {
        "abrir_navegador", "abrir_openwebui", "abrir_javis",
        "abrir_vscode", "abrir_terminal", "abrir_projeto", "status_sistema",
    }
    if intent in FAST_PATH and " e " not in f" {text.lower()} " and not _looks_like_question(text):
        def _action():
            start = datetime.now()
            yield f"data: {_j.dumps({'type':'meta','intent':intent,'brain':'main'})}\n\n"
            result = actions.execute(intent, text)
            msg = result.get("message", "Feito.")
            entry = _make_entry("ok", text, route, result, start)
            entry["response"] = msg
            _save(entry)
            yield f"data: {_j.dumps({'type':'done','text':msg,'brain':'main','intent':intent,'ms':entry['ms']})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_action(), media_type="text/event-stream",
                                  headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    def _generate():
        from llm_providers import stream_claude
        start = datetime.now()
        yield f"data: {_j.dumps({'type':'meta','intent':intent,'brain':brain})}\n\n"

        try:
            if brain == "conclave":
                result = orchestrator.process(text, _get_history_messages())
                entry  = _make_entry("ok", text, route, {"status":"llm","message":result.response}, start, result)
                _save(entry)
                yield f"data: {_j.dumps({'type':'done','text':result.response,'brain':brain,'intent':intent,'ms':entry['ms']})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Cérebro AGENTE (tool-use): entende intenção e encadeia ações
            import agent
            ag = agent.respond(text, _get_history_messages())
            if ag is not None:
                full = ag["text"] or "Pronto, senhor."
                # fake-stream palavra a palavra para manter a sensação de digitação
                for word in full.split(" "):
                    yield f"data: {_j.dumps({'type':'token','text':word + ' '})}\n\n"
                used_intent = ag["tools"][0] if ag.get("tools") else intent
                entry = _make_entry("ok", text, route, {"status":"agent","message":full}, start)
                entry["response"] = full
                entry["intent"]   = used_intent
                _save(entry)
                yield f"data: {_j.dumps({'type':'done','brain':'main','intent':used_intent,'ms':entry['ms']})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Fallback sem Claude — streaming simples (Ollama/erro)
            messages = [{"role": "system", "content": SYSTEM_MAIN_BRAIN}]
            messages.extend(_get_history_messages()[-6:])
            messages.append({"role": "user", "content": text})
            full = ""
            for token in stream_claude(messages):
                full += token
                yield f"data: {_j.dumps({'type':'token','text':token})}\n\n"
            entry = _make_entry("ok", text, route, {"status":"llm","message":full}, start)
            entry["response"] = full
            _save(entry)
            yield f"data: {_j.dumps({'type':'done','brain':brain,'intent':intent,'ms':entry['ms']})}\n\n"
        except Exception as e:
            yield f"data: {_j.dumps({'type':'done','text':f'⚠️ Erro interno: {e}','brain':brain,'intent':intent,'ms':0})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Whisper transcription ─────────────────────────────────

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcrição de áudio via Whisper — mais preciso que Web Speech API."""
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "OPENAI_API_KEY não configurada"}, status_code=503)
    try:
        from openai import OpenAI
        content = await file.read()
        client  = OpenAI(api_key=api_key)
        resp    = client.audio.transcriptions.create(
            model="whisper-1",
            file=(file.filename or "audio.webm", content, file.content_type or "audio/webm"),
            language="pt",
        )
        return JSONResponse({"text": resp.text.strip()})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── TTS ──────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    voice: str = ""
    model: str = ""


@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    """TTS via OpenAI — voz natural (nova/alloy/shimmer...)."""
    import os
    from fastapi.responses import Response

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "OPENAI_API_KEY não configurada"}, status_code=503)

    voice = req.voice or os.environ.get("JAVIS_TTS_VOICE", "nova")
    model = req.model or os.environ.get("JAVIS_TTS_MODEL", "tts-1")
    clean = req.text[:600]

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.audio.speech.create(model=model, voice=voice, input=clean)
        audio_bytes = resp.content if hasattr(resp, "content") else resp.read()
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --- helpers ---

def _make_entry(status: str, text: str, route: dict, action: dict,
                start: datetime, orch=None) -> dict:
    return {
        "ts":             _ts(),
        "status":         status,
        "user":           text,
        "intent":         route.get("intent", "desconhecido"),
        "risk":           route.get("risk_level", "none"),
        "brain":          getattr(orch, "brain", "main") if orch else "main",
        "agents":         getattr(orch, "agents_used", []) if orch else [],
        "complexity":     getattr(orch, "complexity", "simple") if orch else "simple",
        "plan":           getattr(orch, "plan", "") if orch else "",
        "conclave":       getattr(orch, "conclave_result", {}) if orch else {},
        "squad":          getattr(orch, "squad_result", {}) if orch else {},
        "memory_context": getattr(orch, "memory_context", "") if orch else "",
        "action_status":  action.get("status", ""),
        "response":       action.get("message", ""),
        "ms":             int((datetime.now() - start).total_seconds() * 1000),
    }


_QUESTION_HINTS = (
    "o que", "que ", "qual", "quais", "como", "quando", "onde", "por que",
    "porque", "quem", "?", "me fala", "me diz", "me conta", "resume", "resumo",
    "lista", "sobre o", "sobre a", "pendente", "falta", "anotei", "anotação",
    "explica", "quanto",
)


def _looks_like_question(text: str) -> bool:
    """True se o texto parece pergunta/consulta — nunca deve ir pro atalho de ação."""
    t = f" {text.lower().strip()} "
    return any(h in t for h in _QUESTION_HINTS)


def _get_history_messages() -> list[dict]:
    msgs = []
    for h in _history[-6:]:
        msgs.append({"role": "user",      "content": h.get("user", "")})
        msgs.append({"role": "assistant", "content": h.get("response", "")})
    return msgs


def _save(entry: dict) -> None:
    _history.append(entry)
    if len(_history) > 200:
        _history.pop(0)
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    import uvicorn
    print("\n  Javis v2 — http://localhost:8000\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
