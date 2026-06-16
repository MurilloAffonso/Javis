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
import re as _re
import socket
import json
import base64
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
import history_store
from orchestrator import Orchestrator

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
HISTORY_FILE = Path(__file__).resolve().parent.parent / "logs" / "chat_history.jsonl"
HISTORY_FILE.parent.mkdir(exist_ok=True)

app = FastAPI(title="Javis v2", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

orchestrator = Orchestrator()
_history: list[dict] = []

# Padding SSE: alguns setups uvicorn/ASGI seguram os primeiros chunks pequenos
# até acumular ~alguns KB, atrasando o 'meta' em segundos (tela parada). Este
# comentário SSE grande (linha ':' — ignorada pelo cliente) estoura o buffer e
# força o flush imediato do feedback. Usado no início de todo stream.
_SSE_PADDING = ":" + (" " * 2048) + "\n\n"


@app.on_event("startup")
async def _start_integrations():
    """Liga serviços de segundo plano: Telegram e checador de lembretes."""
    try:
        import telegram_bridge
        if telegram_bridge.start_background():
            print("  Telegram: conectado [ok]")
    except Exception as e:
        print(f"  Telegram: nao iniciado ({e})")
    try:
        import reminders
        reminders.start_background()
        print("  Lembretes: checador ativo [ok]")
    except Exception as e:
        print(f"  Lembretes: nao iniciado ({e})")
    try:
        import knowledge
        knowledge.start_background_index()
        print("  Conhecimento: indexando vault em segundo plano [ok]")
    except Exception as e:
        print(f"  Conhecimento: nao iniciado ({e})")
    # Pré-aquece o cache de TTS dos acks falados — assim o 1º pedido já sai
    # instantâneo (sem o ~4s de síntese no primeiro uso após o boot).
    try:
        import threading
        def _warm_acks():
            for phrase in ("Certo, senhor.", "Deixa eu pensar nisso com calma, senhor. Um instante."):
                try:
                    _tts_ack(phrase)
                except Exception:
                    pass
        threading.Thread(target=_warm_acks, daemon=True).start()
        print("  Acks de voz: pré-aquecendo em segundo plano [ok]")
    except Exception as e:
        print(f"  Acks de voz: nao iniciado ({e})")


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


# ── Painel Vem Passear (Cérebro VP) — mesmo padrão do /painel ──────────
@app.get("/vempassear", response_class=HTMLResponse)
async def serve_vp():
    f = FRONTEND_DIR / "vempassear.html"
    if f.exists():
        return HTMLResponse(f.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Painel Vem Passear ainda não criado</h1>", status_code=404)


@app.get("/vempassear.css")
async def serve_vp_css():
    f = FRONTEND_DIR / "vempassear.css"
    return FileResponse(f, media_type="text/css") if f.exists() else JSONResponse({"error": "não criado"}, status_code=404)


@app.get("/vempassear.js")
async def serve_vp_js():
    f = FRONTEND_DIR / "vempassear.js"
    return FileResponse(f, media_type="application/javascript") if f.exists() else JSONResponse({"error": "não criado"}, status_code=404)


# ── Dados do painel VP: passeios ──
@app.get("/vp/passeios")
async def vp_passeios_list():
    import vp_store
    return JSONResponse({"passeios": vp_store.list_passeios(), "resumo": vp_store.passeios_resumo()})


class VPPasseioRequest(BaseModel):
    tipo:    str
    data:    str
    pessoas: int = 1
    valor:   float = 0.0


@app.post("/vp/passeios")
async def vp_passeios_add(req: VPPasseioRequest):
    import vp_store
    item = vp_store.add_passeio(req.tipo, req.data, req.pessoas, req.valor)
    return JSONResponse({"status": "ok", "item": item})


@app.delete("/vp/passeios/{item_id}")
async def vp_passeios_del(item_id: str):
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_passeio(item_id) else "not_found"})


# ── Dados do painel VP: clientes / leads ──
@app.get("/vp/clientes")
async def vp_clientes_list():
    import vp_store
    return JSONResponse(vp_store.list_clientes())


class VPClienteRequest(BaseModel):
    nome:    str
    contato: str = ""
    obs:     str = ""


@app.post("/vp/clientes")
async def vp_clientes_add(req: VPClienteRequest):
    import vp_store
    item = vp_store.add_cliente(req.nome, req.contato, req.obs)
    return JSONResponse({"status": "ok", "item": item})


class VPStatusRequest(BaseModel):
    status: str = "fechado"


@app.patch("/vp/clientes/{item_id}")
async def vp_clientes_status(item_id: str, req: VPStatusRequest):
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.set_status(item_id, req.status) else "not_found"})


@app.delete("/vp/clientes/{item_id}")
async def vp_clientes_del(item_id: str):
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_cliente(item_id) else "not_found"})


# ── Geração de conteúdo de marketing (usa o cérebro/OpenAI) ──
class VPConteudoRequest(BaseModel):
    tipo: str = "ideias"   # ideias | legenda | reel
    tema: str = ""


@app.post("/vp/conteudo")
async def vp_conteudo(req: VPConteudoRequest):
    texto = _gerar_conteudo_vp(req.tipo, req.tema)
    return JSONResponse({"status": "ok", "texto": texto})


# ── Biblioteca de conteúdo (salvar/reusar textos gerados) ──
class VPSalvarConteudo(BaseModel):
    tipo:  str = "ideias"
    texto: str


@app.get("/vp/conteudos")
async def vp_conteudos_list():
    import vp_store
    return JSONResponse({"conteudos": vp_store.list_conteudos()})


@app.post("/vp/conteudos")
async def vp_conteudos_add(req: VPSalvarConteudo):
    import vp_store
    if not req.texto.strip():
        return JSONResponse({"status": "vazio"}, status_code=400)
    return JSONResponse({"status": "ok", "item": vp_store.add_conteudo(req.tipo, req.texto)})


@app.delete("/vp/conteudos/{item_id}")
async def vp_conteudos_del(item_id: str):
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_conteudo(item_id) else "not_found"})


# ── Linha editorial (pauta de posts planejados) ──
@app.get("/vp/pauta")
async def vp_pauta_list():
    import vp_store
    return JSONResponse({"pauta": vp_store.list_pauta()})


class VPPautaRequest(BaseModel):
    data:  str
    canal: str = "Instagram"
    ideia: str


@app.post("/vp/pauta")
async def vp_pauta_add(req: VPPautaRequest):
    import vp_store
    return JSONResponse({"status": "ok", "item": vp_store.add_pauta(req.data, req.canal, req.ideia)})


class VPPautaStatus(BaseModel):
    status: str = "publicado"


@app.patch("/vp/pauta/{item_id}")
async def vp_pauta_status(item_id: str, req: VPPautaStatus):
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.set_pauta_status(item_id, req.status) else "not_found"})


@app.delete("/vp/pauta/{item_id}")
async def vp_pauta_del(item_id: str):
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_pauta(item_id) else "not_found"})


# ── Jampa Jarvis: squad de agentes nomeados (carrega skills do CEREBRO.JAMPA) ──
@app.get("/jampa/agents")
async def jampa_agents():
    """Roster dos agentes nomeados para o dashboard."""
    import jampa_squad
    if not jampa_squad.available():
        return JSONResponse({"agents": [], "vault": str(jampa_squad.JAMPA_VAULT), "ok": False})
    return JSONResponse({"agents": jampa_squad.list_agents(), "ok": True})


class JampaSquadRequest(BaseModel):
    tarefa:   str
    contexto: str = ""
    agente:   str = ""     # vazio = Orion escolhe (acionamento semântico)
    deep:     bool = False


@app.post("/jampa/squad")
async def jampa_squad_run(req: JampaSquadRequest):
    """Aciona o squad: Orion escolhe o agente (ou força um) e executa, aterrado."""
    import jampa_squad
    if not req.tarefa.strip():
        return JSONResponse({"status": "error", "message": "Tarefa vazia"}, status_code=400)
    if req.agente:
        resp = await run_in_threadpool(jampa_squad.run, req.agente, req.tarefa, req.contexto, req.deep)
        return JSONResponse({"status": "ok", "agente": req.agente, "resposta": resp})
    out = await run_in_threadpool(jampa_squad.orquestrar, req.tarefa, req.contexto, req.deep)
    return JSONResponse({"status": "ok", **out})


class JampaLeadRequest(BaseModel):
    nome:      str = ""
    contato:   str = ""
    interesse: str = ""
    obs:       str = ""


@app.post("/jampa/responder-lead")
async def jampa_responder_lead(req: JampaLeadRequest):
    """Fluxo-dinheiro: gera a resposta de WhatsApp pronta pro lead (aterrada)."""
    import jampa_squad
    out = await run_in_threadpool(
        jampa_squad.responder_lead, req.nome, req.contato, req.interesse, req.obs)
    return JSONResponse({"status": "ok", **out})


class JampaForjarRequest(BaseModel):
    transcricao: str
    tema:        str = ""


@app.post("/jampa/forjar-skill")
async def jampa_forjar_skill(req: JampaForjarRequest):
    """Pipeline Nero: transcrição de expert → skill .md (rascunho p/ Murillo revisar)."""
    import skill_forge
    out = await run_in_threadpool(skill_forge.forge, req.transcricao, req.tema)
    return JSONResponse(out)


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
    route = command_router.route(text)

    # Ações críticas bloqueadas imediatamente
    if route["risk_level"] == "critical":
        entry = _make_entry("blocked", text, route, {"status": "blocked"}, start)
        _save(entry)
        return JSONResponse(entry)

    # Núcleo único (threadpool evita bloquear o event loop)
    out = await run_in_threadpool(_brain, text, _get_history_messages(), req.use_conclave)
    entry = _entry_from_brain(text, out, start)
    _save(entry)
    history_store.append("user", text)
    history_store.append("assistant", out["text"])
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

    # Núcleo único — mesmo cérebro do chat
    out = await run_in_threadpool(_brain, clean, _get_history_messages(), req.use_conclave)
    entry = _entry_from_brain(clean, out, start)
    entry["source"]              = "voice"
    entry["original_transcript"] = transcript
    entry["tts"]                 = req.tts
    _save(entry)
    history_store.append("user", clean)
    history_store.append("assistant", out["text"])

    # Memória cresce com padrões de voz (vida própria)
    try:
        from agents.memory_bridge import MemoryBridge
        MemoryBridge().save_voice_command(clean, out["intent"], "main")
    except Exception:
        pass

    return JSONResponse(entry)


@app.post("/voice/stream")
async def voice_stream(req: VoiceRequest):
    """Voice com TTS incremental — começa a falar assim que a 1ª frase fica pronta (SSE)."""
    from voice_bridge import classify_voice, _strip_wake_word

    _SSE = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

    transcript = req.transcript.strip()
    if not transcript:
        def _err():
            yield f"data: {json.dumps({'type':'error','text':'Transcrição vazia'})}\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream", headers=_SSE)

    vc = classify_voice(transcript)
    if vc.get("note") == "blocked_hallucination":
        def _hall():
            yield f"data: {json.dumps({'type':'tts_text','text':'Não entendi, pode repetir?'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_hall(), media_type="text/event-stream", headers=_SSE)

    clean = _strip_wake_word(transcript) or transcript
    start = datetime.now()
    route = command_router.route(clean)

    if route["risk_level"] == "critical":
        def _crit():
            yield f"data: {json.dumps({'type':'tts_text','text':'Ação bloqueada.'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_crit(), media_type="text/event-stream", headers=_SSE)

    intent = route.get("intent", "conversa")

    def _generate():
        import agent as _agent
        full_text = ""
        # padding: força o flush imediato (orbe/feedback aparece já) — ver _SSE_PADDING
        yield _SSE_PADDING

        # FAST PATH — resposta imediata, sem LLM
        if _is_fast_path(intent, clean):
            res = actions.execute(intent, clean)
            full_text = res.get("message", "Feito, senhor.")
            yield f"data: {json.dumps({'type':'meta','intent':intent,'brain':'fast'})}\n\n"
            if req.tts:
                audio = _tts_sentence(full_text)
                if audio:
                    yield f"data: {json.dumps({'type':'audio','b64':base64.b64encode(audio).decode()})}\n\n"
                else:
                    yield f"data: {json.dumps({'type':'tts_text','text':full_text})}\n\n"
            yield f"data: {json.dumps({'type':'done','text':full_text,'intent':intent,'brain':'fast','ms':int((datetime.now()-start).total_seconds()*1000)})}\n\n"
            yield "data: [DONE]\n\n"
            _save_voice_entry(clean, full_text, intent, "fast", transcript, req.tts, start)
            return

        # PRE-ACK — fala imediatamente enquanto _brain() processa (~200ms vs 2400ms percebidos)
        # Só para intents de ação; conversa e desconhecido respondem direto.
        _NO_ACK = {"conversa", "desconhecido"}
        acked = False

        # ACK do RACIOCÍNIO PESADO — pedidos estratégicos roteiam como "conversa"
        # (caem no _NO_ACK) mas disparam pensar_profundo / Conclave (~20-30s).
        # Sem aviso, é silêncio puro e parece travamento. Detecta e avisa.
        if req.tts and _likely_council(clean):
            ack = "Deixa eu pensar nisso com calma, senhor. Um instante."
            ack_audio = _tts_ack(ack)
            if ack_audio:
                yield f"data: {json.dumps({'type':'audio','b64':base64.b64encode(ack_audio).decode(),'sentence':ack})}\n\n"
            else:
                yield f"data: {json.dumps({'type':'tts_text','text':ack})}\n\n"
            acked = True

        if req.tts and not acked and intent not in _NO_ACK:
            ack_audio = _tts_ack("Certo, senhor.")
            if ack_audio:
                yield f"data: {json.dumps({'type':'audio','b64':base64.b64encode(ack_audio).decode(),'sentence':'Certo, senhor.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type':'tts_text','text':'Certo, senhor.'})}\n\n"

        # RACIOCÍNIO PESADO EM STREAMING — pedidos profundos vão DIRETO ao Claude
        # Opus 4.8 (assinatura), falando frase a frase conforme o Opus pensa.
        # Pula o gpt-4o (sem double-LLM) e elimina o silêncio de 20-40s: o senhor
        # ouve a resposta se formando. Só para frases claramente profundas.
        if not req.use_conclave and _likely_council(clean):
            try:
                import claude_brain as _cb
                import agent as _ag
            except Exception:
                _cb = None
            if _cb and _cb.available():
                ctx = _ag._history_context(_get_history_messages())
                spoke = False
                full_text = ""
                yield f"data: {json.dumps({'type':'meta','intent':'pensar_profundo','brain':'claude'})}\n\n"
                for sentence in _accumulate_sentences(_cb.answer_stream(clean, ctx)):
                    spoke = True
                    full_text += (" " if full_text else "") + sentence
                    if req.tts:
                        audio = _tts_sentence(sentence)
                        if audio:
                            yield f"data: {json.dumps({'type':'audio','b64':base64.b64encode(audio).decode(),'sentence':sentence})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type':'tts_text','text':sentence})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type':'token','text':sentence + ' '})}\n\n"
                if spoke and full_text.strip():
                    ms = int((datetime.now() - start).total_seconds() * 1000)
                    yield f"data: {json.dumps({'type':'done','text':full_text,'intent':'pensar_profundo','brain':'claude','ms':ms})}\n\n"
                    yield "data: [DONE]\n\n"
                    _save_voice_entry(clean, full_text, "pensar_profundo", "claude", transcript, req.tts, start)
                    return
                # Streaming vazio (Claude falhou) → cai no cérebro completo abaixo.

        # CÉREBRO COMPLETO com tool-use — stream_text não passa ferramentas
        # ao GPT, que então inventa que executou sem chamar nada (falso positivo).
        # Voz usa _brain direto; TTS é feito frase a frase após a resposta.
        out = _brain(clean, _get_history_messages(), req.use_conclave)
        full_text = out["text"] or "Pronto, senhor."
        yield f"data: {json.dumps({'type':'meta','intent':out['intent'],'brain':out['brain'],'text':full_text})}\n\n"
        if req.tts:
            for sentence in _split_sentences(full_text):
                audio = _tts_sentence(sentence)
                if audio:
                    yield f"data: {json.dumps({'type':'audio','b64':base64.b64encode(audio).decode(),'sentence':sentence})}\n\n"
                else:
                    yield f"data: {json.dumps({'type':'token','text':sentence + ' '})}\n\n"
        else:
            for word in full_text.split():
                yield f"data: {json.dumps({'type':'token','text':word + ' '})}\n\n"

        ms = int((datetime.now() - start).total_seconds() * 1000)
        yield f"data: {json.dumps({'type':'done','text':full_text,'intent':intent,'brain':'main','ms':ms})}\n\n"
        yield "data: [DONE]\n\n"
        _save_voice_entry(clean, full_text, intent, "main", transcript, req.tts, start)

    return StreamingResponse(_generate(), media_type="text/event-stream", headers=_SSE)


def _save_voice_entry(clean: str, text: str, intent: str, brain: str,
                      transcript: str, tts: bool, start: datetime) -> None:
    entry = {
        "status": "ok", "text": text, "response": text,
        "intent": intent, "brain": brain, "source": "voice",
        "original_transcript": transcript, "tts": tts,
        "ms": int((datetime.now() - start).total_seconds() * 1000),
        "route": {}, "tools": [],
    }
    _save(entry)
    history_store.append("user", clean)
    history_store.append("assistant", text)


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


@app.get("/history/session")
async def history():
    return JSONResponse({"history": _history[-50:]})


@app.get("/history")
async def get_history():
    """Retorna histórico de chat persistido em disco."""
    return JSONResponse(history_store.load())


@app.delete("/history")
async def clear_history():
    """Limpa o histórico de chat."""
    history_store.clear()
    return JSONResponse({"status": "ok"})


# ── Streaming chat ────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Chat com streaming token-a-token (SSE)."""
    import json as _j

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

    intent0 = route.get("intent", "conversa")
    brain0  = "conclave" if req.use_conclave else "main"

    def _generate():
        start = datetime.now()
        # feedback imediato (orbe acende enquanto pensa)
        yield f"data: {_j.dumps({'type':'meta','intent':intent0,'brain':brain0})}\n\n"
        # padding: alguns setups ASGI/uvicorn seguram os 1ºs chunks pequenos até
        # acumular bytes. Este comentário SSE grande (linha ':' ignorada pelo
        # cliente) estoura o buffer e força o flush do 'meta' — orbe acende JÁ.
        yield _SSE_PADDING
        try:
            # 1) Atalho instantâneo — ação local óbvia, sem LLM
            if not req.use_conclave and _is_fast_path(intent0, text):
                res = actions.execute(intent0, text)
                full = res.get("message", "Feito, senhor.")
                for word in full.split(" "):
                    yield f"data: {_j.dumps({'type':'token','text':word + ' '})}\n\n"
                out = {"text": full, "intent": intent0, "brain": "main",
                       "status": res.get("status", "ok"), "tools": [intent0], "route": route}
                entry = _entry_from_brain(text, out, start)
                _save(entry)
                history_store.append("user", text)
                history_store.append("assistant", full)
                yield f"data: {_j.dumps({'type':'done','brain':'main','intent':intent0,'ms':entry['ms']})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 2) Conversa OU ação → cérebro com FERRAMENTAS (raciocínio real:
            #    busca nas notas, lembra fatos, encadeia ações), depois fake-stream.
            #    O padding acima já deu feedback instantâneo — não perdemos UX.
            out = _brain(text, _get_history_messages(), req.use_conclave)
            for word in (out["text"] or "Pronto, senhor.").split(" "):
                yield f"data: {_j.dumps({'type':'token','text':word + ' '})}\n\n"
            entry = _entry_from_brain(text, out, start)
            _save(entry)
            history_store.append("user", text)
            history_store.append("assistant", out["text"])
            yield f"data: {_j.dumps({'type':'done','brain':out['brain'],'intent':out['intent'],'ms':entry['ms']})}\n\n"
        except Exception as e:
            yield f"data: {_j.dumps({'type':'done','text':f'⚠️ Erro interno: {e}','brain':brain0,'intent':intent0,'ms':0})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Whisper transcription ─────────────────────────────────

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcrição de áudio — gpt-4o-transcribe (mais preciso que whisper-1).

    O 'prompt' envieja a transcrição para os nomes próprios do mundo do senhor
    (Jampa, Vem Passear, Murillo...), reduzindo o embolamento que estraga o
    raciocínio do cérebro. Modelo configurável via JAVIS_TRANSCRIBE_MODEL.
    """
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "OPENAI_API_KEY não configurada"}, status_code=503)
    model  = os.environ.get("JAVIS_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
    hint   = ("Jamba, Murillo, Vem Passear, Vem Passear em Jampa, Jampa, "
              "João Pessoa, Paraíba, Cadastur, piscinas naturais, Areia Vermelha, "
              "Picãozinho, Seixas, Tambaú, Cabo Branco, catamarã, Pôr do Sol do Jacaré.")
    try:
        from openai import OpenAI
        content = await file.read()
        client  = OpenAI(api_key=api_key, timeout=30)
        try:
            resp = client.audio.transcriptions.create(
                model=model,
                file=(file.filename or "audio.webm", content, file.content_type or "audio/webm"),
                language="pt",
                prompt=hint,
            )
        except Exception as e:
            # Degrada para whisper-1 se o modelo novo não estiver disponível na conta
            print(f"[transcribe] {model} falhou ({e}); usando whisper-1", flush=True)
            resp = client.audio.transcriptions.create(
                model="whisper-1",
                file=(file.filename or "audio.webm", content, file.content_type or "audio/webm"),
                language="pt",
                prompt=hint,
            )
        return JSONResponse({"text": resp.text.strip()})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── TTS ──────────────────────────────────────────────────

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Recebe um arquivo, salva temporariamente e analisa com file_analyzer."""
    import tempfile, os, shutil
    suffix = Path(file.filename or "upload").suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()
        import file_analyzer
        result = await run_in_threadpool(file_analyzer.analyze, tmp.name, "")
        result["filename"] = file.filename
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


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


# Abridores de app inequívocos → atalho instantâneo (sem gastar LLM)
FAST_PATH = {
    "abrir_navegador", "abrir_openwebui", "abrir_javis",
    "abrir_vscode", "abrir_projeto", "status_sistema",
    "hora_data", "abrir_youtube", "tocar_musica",
    "listar_lembretes", "registrar_ideia", "clima",
    # abrir_terminal removido: requires_approval=True no RISK_MAP
}

# Intenções de abrir/navegar/status: um comando real é curto e direto
# ("abre o vscode"). Se a palavra-chave aparece dentro de uma FRASE longa
# (ex.: "o nome do projeto é Vem Passear"), é quase sempre conversa — não pode
# disparar a ação e atropelar o raciocínio. tocar_musica/registrar_ideia/clima
# ficam de fora pois legitimamente vêm em frases longas ("anota que...").
_FAST_OPEN = {
    "abrir_navegador", "abrir_openwebui", "abrir_javis", "abrir_vscode",
    "abrir_projeto", "status_sistema", "hora_data", "abrir_youtube",
}


def _is_fast_path(intent: str, text: str) -> bool:
    if intent not in FAST_PATH:
        return False
    if " e " in f" {text.lower()} ":
        return False
    if _looks_like_question(text):
        return False
    # comando de abrir embutido em frase longa → provavelmente conversa
    if intent in _FAST_OPEN and len(text.split()) > 6:
        return False
    return True


# Gatilhos que quase sempre fazem o cérebro acionar o raciocínio pesado
# (pensar_profundo → Claude Opus 4.8 pela assinatura, ou o Conclave). Servem só
# para o ACK falado imediato — o senhor ouve o aviso em ~200ms em vez de 20-30s
# de silêncio. Espelham as frases descritas em pensar_profundo (agent.py).
_DEEP_HINTS = (
    "debate", "debat", "analisa a fundo", "analise a fundo", "análise a fundo",
    "o que voces acham", "o que vocês acham", "me ajuda a decidir",
    "me ajude a decidir", "vale a pena", "consultar o conselho",
    "consulta o conselho", "o que o conselho", "pensa direito",
    "pensa nisso", "pense nisso", "analisa direito", "prós e contras",
    "pros e contras", "pensa a fundo", "pense a fundo",
)


def _likely_council(text: str) -> bool:
    """Heurística leve: o pedido provavelmente acionará o raciocínio pesado?"""
    t = text.lower()
    return any(h in t for h in _DEEP_HINTS)


_SENT_SPLIT = _re.compile(r'(?<=[.!?…])\s+')


def _split_sentences(text: str) -> list[str]:
    parts = _SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _accumulate_sentences(tokens):
    """Acumula tokens de streaming e emite frases completas."""
    buf = ""
    for token in tokens:
        buf += token
        while True:
            m = _SENT_SPLIT.search(buf)
            if not m:
                break
            sentence = buf[:m.start()].strip()
            if sentence:
                yield sentence
            buf = buf[m.end():]
    if buf.strip():
        yield buf.strip()


def _tts_sentence(text: str) -> bytes | None:
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or not text.strip():
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        voice = os.environ.get("JAVIS_TTS_VOICE", "nova")
        resp = client.audio.speech.create(model="tts-1", voice=voice, input=text[:300])
        return resp.content if hasattr(resp, "content") else resp.read()
    except Exception:
        return None


_ACK_AUDIO_CACHE: dict[str, bytes] = {}


def _tts_ack(phrase: str) -> bytes | None:
    """TTS com cache em memória — pré-ack imediato após a 1ª chamada."""
    if phrase not in _ACK_AUDIO_CACHE:
        audio = _tts_sentence(phrase)
        if audio:
            _ACK_AUDIO_CACHE[phrase] = audio
    return _ACK_AUDIO_CACHE.get(phrase)


_VP_CONTEXTO = """Você é copywriter de marketing de turismo da Vem Passear Jampa,
agência certificada (Cadastur) de passeios em João Pessoa/PB. Escreva em português do
Brasil, tom animado e vendedor, pronto pra publicar. Use emojis com moderação.

CATÁLOGO REAL (preço por pessoa, compartilhado salvo indicado):
PISCINAS NATURAIS (catamarã, ~3h, sujeito à maré baixa):
- Piscinas do Seixas — R$60 (embarque Praia de Tambaú, ~3h30, ponto mais oriental das Américas)
- Piscinas de Picãozinho — R$60 (a 1,5km de Tambaú, aquário natural)
- Piscinas da Penha — R$60 (mais exclusivo, só 2 embarcações por vez)
LITORAL NORTE:
- Roteiro Clássico — R$80 (tartarugas, Dique de Cabedelo, Fortaleza, Pôr do Sol do Jacaré)
- Combo + Areia Vermelha (catamarã) — R$160 | só litoral norte — R$80
- Areia Vermelha standalone (catamarã c/ toboágua) — R$70 (banco de areia que surge na maré baixa)
- Pôr do Sol do Jacaré (catamarã, Bolero de Ravel ao vivo) — R$90 (~1h30, diário à tarde)
- Lancha privativa — a partir de R$1.590 (dia inteiro, churrasco a bordo)
LITORAL SUL:
- Roteiro Clássico (Gramame, Amor, Tambaba, Coqueirinho) — R$80
- Praia Bela — R$80 | Combo c/ Quadriciclo — R$240 individual / R$310 dupla
CITY TOUR Jampa Histórica — R$80 (~3h30, ter–dom)
INTERESTADUAIS (bate-volta) — Porto de Galinhas, Pipa, Natal — R$160 cada
PACOTES — Super Econômico 2 dias R$140 | 3 Dias Básico R$280 | 3 Dias Completo R$400
TRANSFER aeroporto/hotel 24h — consultar

Transfer incluso na maioria (Tambaú, Cabo Branco, Manaíra, Bessa). Alimentação não inclusa.

Ângulo de venda mais forte: piscinas naturais e Areia Vermelha SÓ existem na MARÉ BAIXA —
isso cria urgência REAL ("a maré tá perfeita essa semana, depois fecha"). Nas promoções do
Instagram há âncora de desconto (ex.: "de R$100 por R$60"). WhatsApp: (83) 9 9908-7830.
Sempre termine com chamada pra ação no WhatsApp."""

_VP_PEDIDOS = {
    "ideias":   "Liste 5 ideias de post para o Instagram focadas no passeio de Piscinas Naturais. Para cada uma: título curto + 1 linha de descrição.",
    "legenda":  "Escreva 1 legenda pronta para post/anúncio no Instagram do passeio de Piscinas Naturais, com preço, urgência da maré e CTA pro WhatsApp.",
    "reel":     "Escreva 1 roteiro de Reel de 15-20s para o passeio de Piscinas Naturais: descreva cena a cena (0-3s, 3-10s, 10-15s) com o texto que aparece na tela e a ação.",
    "resposta": "Escreva 3 mensagens curtas e prontas para responder no WhatsApp um lead interessado no passeio de Piscinas Naturais: (1) saudação que já apresenta o passeio e pergunta data/nº de pessoas, (2) preço com âncora de desconto e proposta de reservar, (3) fechamento pedindo Pix de sinal. Tom caloroso e direto.",
    "oferta":   "Escreva 1 anúncio de oferta-relâmpago do passeio de Piscinas Naturais usando a urgência REAL da maré baixa desta semana. Curto, com gatilho de escassez e CTA pro WhatsApp.",
    "stories":  "Escreva 3 textos curtos para Stories do Instagram sobre o passeio de Piscinas Naturais, cada um com uma chamada diferente (urgência da maré, prova social, preço). Inclua sugestão de figurinha/enquete.",
}


def _gerar_conteudo_vp(tipo: str, tema: str = "") -> str:
    """Gera conteúdo de marketing VP via OpenAI. Fallback templado se não houver API."""
    import os
    pedido = _VP_PEDIDOS.get(tipo, _VP_PEDIDOS["ideias"])
    if tema.strip():
        pedido += f" Foque no tema: {tema.strip()}."

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            model = os.environ.get("JAVIS_OPENAI_MODEL", "gpt-4o-mini")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _VP_CONTEXTO},
                    {"role": "user", "content": pedido},
                ],
                temperature=0.8,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            return f"(sem IA agora: {e})\n\n" + _vp_fallback(tipo)
    return _vp_fallback(tipo)


def _vp_fallback(tipo: str) -> str:
    if tipo == "reel":
        return ("0-3s: imagem aérea do catamarã na piscina cristalina — texto: 'A maré tá PERFEITA essa semana 🌊'\n"
                "3-10s: pessoas na água rasa, peixinhos — texto: 'Piscinas Naturais do Seixas, a 20min do centro'\n"
                "10-15s: catamarã saindo — texto: 'Maré boa só até quarta. Garante sua vaga 👇'")
    if tipo == "legenda":
        return ("🌊 MARÉ PERFEITA essa semana nas Piscinas Naturais do Seixas!\n\n"
                "Catamarã + água cristalina a 20min de João Pessoa. A partir de R$60 (de R$100).\n"
                "Agência certificada Cadastur. Vagas limitadas — chama no WhatsApp 👇")
    return ("1. Maré perfeita — \"Essa semana a maré tá na medida certa pra piscina natural\"\n"
            "2. POV chegando na piscina — \"Trocou o sofá por isso 🐠\"\n"
            "3. Quanto custa — \"Um dia desses por R$60?\"\n"
            "4. Prova social — depoimento de cliente feliz\n"
            "5. Bastidor — o catamarã saindo, clima bom")


def _brain(text: str, history: list[dict], use_conclave: bool = False) -> dict:
    """Núcleo ÚNICO de decisão do Jamba (usado por /chat, /chat/stream e /voice).

    Cascata: atalho local → conclave (se pedido) → agente tool-use → fallback Ollama.
    Retorna {text, intent, brain, status, tools, route, orch}.
    """
    route = command_router.route(text)
    intent = route.get("intent", "conversa")

    # 1) Atalho instantâneo — ação local óbvia
    if _is_fast_path(intent, text):
        res = actions.execute(intent, text)
        return {"text": res.get("message", "Feito, senhor."), "intent": intent,
                "brain": "main", "status": res.get("status", "ok"),
                "tools": [intent], "route": route, "orch": None}

    # 2) Conclave — só quando o senhor ativa o debate
    if use_conclave:
        try:
            result = orchestrator.process(text, history)
            return {"text": result.response or "Sem síntese, senhor.",
                    "intent": getattr(result, "intent", intent), "brain": "conclave",
                    "status": "llm", "tools": [], "route": route, "orch": result}
        except Exception as e:
            return {"text": f"O conclave falhou, senhor: {e}", "intent": intent,
                    "brain": "conclave", "status": "error", "tools": [], "route": route, "orch": None}

    # 3) Cérebro AGENTE (tool-use) — entende a intenção (conversa OU ação) e
    #    decide sozinho se chama uma ferramenta. Conversa também passa por aqui
    #    para PRESERVAR o raciocínio: pode buscar nas notas (buscar_conhecimento),
    #    lembrar fatos (lembrar_fato) e encadear ações, em vez de responder no
    #    vácuo. O modelo não desperdiça tool-call em bate-papo simples ("oi").
    import agent
    ag = agent.respond(text, history)
    if ag is not None:
        used = ag["tools"][0] if ag.get("tools") else intent
        return {"text": ag["text"] or "Pronto, senhor.", "intent": used,
                "brain": "main", "status": "agent", "tools": ag.get("tools", []),
                "route": route, "orch": None}

    # 4) Fallback sem Claude/OpenAI → cérebro local (Ollama)
    try:
        txt = orchestrator._main_brain(text, history)
    except Exception as e:
        txt = f"Estou sem cérebro disponível, senhor: {e}"
    return {"text": txt, "intent": intent, "brain": "main", "status": "llm",
            "tools": [], "route": route, "orch": None}


def _entry_from_brain(text: str, out: dict, start: datetime) -> dict:
    """Monta o registro padrão a partir do resultado do _brain."""
    entry = _make_entry("ok", text, out["route"],
                        {"status": out["status"], "message": out["text"]},
                        start, out.get("orch"))
    entry["response"] = out["text"]
    entry["intent"]   = out["intent"]
    entry["brain"]    = out["brain"]
    return entry


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


# ---------------------------------------------------------------------------
# OpenAI-compatible endpoint — permite que voz-sandbox use o Javis como LLM
# ---------------------------------------------------------------------------

class OAIRequest(BaseModel):
    model: str = "javis"
    messages: list[dict]
    stream: bool = False
    max_tokens: int | None = None
    temperature: float | None = None


@app.post("/v1/chat/completions")
async def openai_compat(req: OAIRequest):
    """Endpoint OpenAI-compatível para voz-sandbox e outros clientes."""
    import time, uuid
    # Extrai texto do último user message
    user_text = ""
    for m in reversed(req.messages):
        if m.get("role") == "user":
            content = m.get("content", "")
            user_text = content if isinstance(content, str) else str(content)
            break
    if not user_text:
        user_text = "olá"

    # Chamada OpenAI direta sem tools — resposta de texto limpa para o avatar
    def _llm_direct(text: str) -> str:
        import os
        from openai import OpenAI
        import agent as _agent
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        msgs = [{"role": "system", "content": _agent._system()}]
        for h in _get_history_messages():
            msgs.append(h)
        msgs.append({"role": "user", "content": text})
        r = client.chat.completions.create(
            model=os.environ.get("JAVIS_OPENAI_MODEL", "gpt-4o-mini"),
            messages=msgs,
            max_tokens=200,
        )
        return r.choices[0].message.content or "Sem resposta."

    reply = await run_in_threadpool(_llm_direct, user_text)

    history_store.append("user", user_text)
    history_store.append("assistant", reply)

    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    })


@app.get("/v1/models")
async def oai_models():
    """Lista de modelos compatível com OpenAI — necessário para clientes que fazem GET /v1/models."""
    return JSONResponse({
        "object": "list",
        "data": [{"id": "javis", "object": "model", "created": 0, "owned_by": "javis"}],
    })


# ══════════════════════════════════════════════════════════════
#  AIOS — Treino de Agentes via YouTube + Missões
# ══════════════════════════════════════════════════════════════

class TrainRequest(BaseModel):
    url: str
    agent: str = "khan"


def _extract_yt_transcript(url: str) -> dict:
    """Extrai transcrição de um vídeo YouTube via yt-dlp (bloqueante)."""
    import yt_dlp
    import re
    import requests as _req
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title   = info.get("title", "Vídeo sem título")
    channel = info.get("channel") or info.get("uploader", "")
    desc    = (info.get("description") or "").strip()[:3000]

    captions = info.get("automatic_captions") or info.get("subtitles") or {}
    lang = next((l for l in ["pt", "pt-BR", "pt-br", "en"] if l in captions), None)
    text = ""
    if lang:
        for fmt in captions[lang]:
            if fmt.get("ext") in ("json3", "vtt", "srv3"):
                try:
                    r = _req.get(fmt["url"], timeout=20)
                    if r.ok:
                        if fmt["ext"] == "json3":
                            segs = []
                            for ev in r.json().get("events", []):
                                for s in ev.get("segs", []):
                                    t = (s.get("utf8") or "").replace("\n", " ").strip()
                                    if t:
                                        segs.append(t)
                            text = " ".join(segs)
                        else:
                            raw = re.sub(r"<[^>]+>", "", r.text)
                            raw = re.sub(r"^\d{2}:\d{2}.*$", "", raw, flags=re.M)
                            raw = re.sub(r"^WEBVTT.*$", "", raw, flags=re.M)
                            text = re.sub(r"\n{2,}", "\n", raw).strip()
                        break
                except Exception:
                    continue
    if not text:
        text = desc or title

    return {"title": title, "channel": channel, "text": text}


def _save_training_doc(agent_id: str, title: str, text: str, url: str) -> str:
    import re
    from datetime import datetime as _dt
    save_dir = Path(__file__).resolve().parents[3] / "_memoria" / "treino-agentes"
    save_dir.mkdir(parents=True, exist_ok=True)
    safe  = re.sub(r"[^\w\s-]", "", title)[:50].strip().replace(" ", "_")
    fname = f"{agent_id}_{safe}_{_dt.now().strftime('%Y%m%d_%H%M')}.md"
    content = (
        f"# {title}\n"
        f"Agente: {agent_id}\nFonte: {url}\nData: {_dt.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"## Transcrição\n\n{text}\n"
    )
    (save_dir / fname).write_text(content, encoding="utf-8")
    return fname


@app.post("/train/youtube")
async def train_youtube(req: TrainRequest):
    """Extrai transcrição de um vídeo YouTube e salva na base de conhecimento do agente."""
    if not req.url.strip():
        return JSONResponse({"error": "URL obrigatória"}, status_code=400)
    try:
        from starlette.concurrency import run_in_threadpool
        info = await run_in_threadpool(_extract_yt_transcript, req.url)
        fname = await run_in_threadpool(
            _save_training_doc, req.agent, info["title"], info["text"], req.url
        )
        try:
            import knowledge, threading
            threading.Thread(target=lambda: knowledge.build_index(force=True), daemon=True).start()
        except Exception:
            pass
        return JSONResponse({
            "status": "ok",
            "title": info["title"],
            "channel": info["channel"],
            "chars": len(info["text"]),
            "file": fname,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/missions")
async def get_missions():
    """Missões ativas do orquestrador."""
    return JSONResponse({
        "missions": [
            {"id": "m1", "name": "Campanha Lançamento Q1", "pct": 89, "active": True,  "status": "running"},
            {"id": "m2", "name": "SDR Outbound EN",        "pct": 62, "active": False, "status": "running"},
            {"id": "m3", "name": "Conteúdo Julho",         "pct": 34, "active": False, "status": "pending"},
        ]
    })


if __name__ == "__main__":
    import uvicorn
    print("\n  Javis v2 — http://localhost:8000\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
