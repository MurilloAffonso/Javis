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

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

    # 3. Orquestrador LLM
    result = orchestrator.process(text, _get_history_messages())

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
