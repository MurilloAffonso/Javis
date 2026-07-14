"""Javis v2 — FastAPI server.

Endpoints:
  GET  /              → serve frontend
  POST /chat          → orchestrator pipeline
  GET  /status        → system status
  GET  /agents        → list agents
  GET  /history       → chat history (last 50)
"""
from __future__ import annotations
import os
import sys
import re as _re
import socket
import json
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Carrega variáveis de ambiente do .env na raiz do projeto.
# Testes de hardening usam JAVIS_SKIP_DOTENV=1 para nao ler segredos locais.
if not os.environ.get("JAVIS_SKIP_DOTENV"):
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    except ImportError:
        pass

from fastapi import FastAPI, UploadFile, File, Header
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

import command_router
import actions
import logger
import history_store
import gate
import safe_config
import tts_local
from orchestrator import Orchestrator

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
HISTORY_FILE = Path(__file__).resolve().parent.parent / "logs" / "chat_history.jsonl"
HISTORY_FILE.parent.mkdir(exist_ok=True)

app = FastAPI(title="Javis v2", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=safe_config.cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _disabled_json(capability: str, flag_hint: str = "", status_code: int = 403):
    return JSONResponse(
        safe_config.disabled_response(capability, flag_hint),
        status_code=status_code,
    )


def _gate_json(payload: dict, status_code: int = 403):
    return JSONResponse(payload, status_code=status_code)


def _local_auth_gate(token: str | None, action: str) -> dict | None:
    return gate.require_local_auth(token, action)


def _vp_project_gate(
    action: str,
    project_id: str,
    external_adapters: bool = False,
    local_token: str | None = None,
    auth_required: bool = False,
) -> dict | None:
    if auth_required:
        blocked = _local_auth_gate(local_token, action)
        if blocked:
            return blocked
    blocked = gate.require_project_scope(project_id)
    if blocked:
        return blocked
    blocked = gate.require_vp_effects(action)
    if blocked:
        return blocked
    if external_adapters:
        return gate.require_external_adapters(action)
    return None

# Interface legada "Central de Comando" (/central) ARQUIVADA em UI-4B
# (movida para _arquivo/interfaces-legadas/). Mount removido.

# JAVIS Command Center (Fase 2/3) — servido em /command-center, isolado.
# Só monta se a pasta existir; não altera nenhuma rota existente.
_cc_dir = FRONTEND_DIR / "command-center"
if _cc_dir.exists():
    app.mount("/command-center", StaticFiles(directory=str(_cc_dir), html=True), name="command-center")

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
        import db_sync
        res = db_sync.bootstrap()
        print(f"  SQLite: persistência pronta {res} [ok]")
    except Exception as e:
        print(f"  SQLite: bootstrap falhou ({e})")
    try:
        import telegram_bridge
        if safe_config.telegram_enabled() and telegram_bridge.start_background():
            print("  Telegram: conectado [ok]")
        elif not safe_config.telegram_enabled():
            print("  Telegram: disabled_by_default (requires_explicit_enable)")
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
        if knowledge.start_background_index():
            print("  Conhecimento: indexando vault em segundo plano [ok]")
        else:
            print("  Conhecimento: disabled_by_default (requires_explicit_enable)")
    except Exception as e:
        print(f"  Conhecimento: nao iniciado ({e})")
    # Pré-aquece o cache de TTS dos acks falados — assim o 1º pedido já sai
    # instantâneo (sem o ~4s de síntese no primeiro uso após o boot).
    try:
        if not safe_config.external_adapters_enabled():
            print("  Acks de voz: disabled_by_default (requires_explicit_enable)")
            return
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
async def knowledge_reindex(
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Reindexa os arquivos do vault (incremental)."""
    blocked = _local_auth_gate(x_javes_local_token, "knowledge.reindex")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_external_adapters("knowledge.reindex")
    if blocked:
        return _gate_json(blocked)
    import knowledge
    result = await run_in_threadpool(knowledge.build_index, False)
    return JSONResponse(result)


@app.get("/knowledge/search")
async def knowledge_search(
    q: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "knowledge.search")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_external_adapters("knowledge.search")
    if blocked:
        return _gate_json(blocked)
    import knowledge
    hits = await run_in_threadpool(knowledge.search, q, 5)
    return JSONResponse({"hits": hits})


@app.get("/knowledge/eval")
async def knowledge_eval_endpoint(k: int = 5):
    """Avalia o RAG (recall@k / MRR) comparando híbrido × legado.
    Usa o golden set de _memoria/rag_eval_golden.json."""
    import knowledge_eval
    result = await run_in_threadpool(knowledge_eval.evaluate, None, k)
    return JSONResponse(result)


class DnaReq(BaseModel):
    text: str = ""
    fonte: str = ""
    tema: str = ""
    fonte_tipo: str = ""    # "" | "whatsapp" | "transcricao"


@app.post("/knowledge/dna")
async def knowledge_dna(
    req: DnaReq,
    approved: bool = False,
    approval_id: int | None = None,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Extrai o DNA cognitivo de um texto (transcrição, export, material),
    grava o dossiê em _memoria/dna/ e reindexa o RAG."""
    blocked = _local_auth_gate(x_javes_local_token, "knowledge.dna")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_external_adapters("knowledge.dna")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_persisted_approval(
        "knowledge.dna",
        approval_id=approval_id,
        route="/knowledge/dna",
        risk_level="high",
        reason="dna_extractor usa adaptadores externos e escreve dossie",
        approved=approved,
    )
    if blocked:
        return _gate_json(blocked)
    import dna_extractor
    result = await run_in_threadpool(
        dna_extractor.extract_and_index, req.text, req.fonte, req.tema, req.fonte_tipo)
    return JSONResponse(result)


@app.post("/knowledge/graph/build")
async def knowledge_graph_build(
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """(Re)constrói o grafo de conhecimento a partir dos dossiês de DNA."""
    blocked = _local_auth_gate(x_javes_local_token, "knowledge.graph.build")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_local_actions("knowledge.graph.build")
    if blocked:
        return _gate_json(blocked)
    import knowledge_graph
    return JSONResponse(await run_in_threadpool(knowledge_graph.build_from_dna))


@app.get("/knowledge/graph")
async def knowledge_graph_query(q: str = "", depth: int = 1):
    """Sem q → stats + conceitos centrais. Com q → vizinhança do conceito."""
    import knowledge_graph
    if not q:
        return JSONResponse(await run_in_threadpool(knowledge_graph.stats))
    return JSONResponse(await run_in_threadpool(knowledge_graph.neighbors, q, depth))


@app.post("/knowledge/ingest")
async def knowledge_ingest(
    folder: str = "",
    approved: bool = False,
    approval_id: int | None = None,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Ingestão em LOTE: processa .txt/.md de uma pasta (default _inbox/ingestao/)
    → DNA → RAG → grafo. Assíncrono; acompanhe em /knowledge/ingest/status."""
    safe_folder, blocked = gate.validate_ingest_folder(folder)
    if blocked:
        return _gate_json(blocked)
    blocked = _local_auth_gate(x_javes_local_token, "knowledge.ingest")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_external_adapters("knowledge.ingest")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_persisted_approval(
        "knowledge.ingest",
        approval_id=approval_id,
        route="/knowledge/ingest",
        risk_level="high",
        reason="ingest chama DNA em lote e reindexa conhecimento",
        metadata={"folder": str(safe_folder)},
        approved=approved,
    )
    if blocked:
        return _gate_json(blocked)
    import ingest
    return JSONResponse(ingest.start(str(safe_folder)))


@app.get("/knowledge/ingest/status")
async def knowledge_ingest_status():
    import ingest
    return JSONResponse(ingest.status())


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
    "Voz sandbox": 12393,
}


class ChatRequest(BaseModel):
    message: str
    project_id: str = ""
    session_id: str = ""
    use_conclave: bool = False
    model: str = "claude"


class ExecutionTaskCreateRequest(BaseModel):
    objective: str
    project_id: str = ""
    executor: str = "codex"
    timeout_seconds: int = 900


class ExecutionProjectRequest(BaseModel):
    project_id: str = ""


class ExecutionApprovalRequest(BaseModel):
    project_id: str = ""
    approval_id: int | None = None


class ExecutionStartRequest(BaseModel):
    project_id: str = ""
    test_commands: list[list[str]] = []


def _normalize_project_id(project_id: str | None) -> str:
    return (project_id or "").strip() or gate.CORE_SCOPE


def _resolve_session(project_id: str, session_id: str = "", create_if_missing: bool = True) -> tuple[str, str, dict | None]:
    pid = _normalize_project_id(project_id)
    sid = (session_id or "").strip()
    if sid:
        row = history_store.get_session(sid)
        if not row:
            return pid, sid, {"status": "not_found", "reason": "session_not_found"}
        if row.get("project_id") != pid:
            return pid, sid, {"status": "blocked", "reason": "project_scope_mismatch"}
        return pid, sid, None
    if not create_if_missing:
        return pid, "", None
    sid = history_store.DEFAULT_SESSION_ID
    ensured = history_store.ensure_session(pid, sid)
    if ensured.get("status") != "ok":
        return pid, sid, {"status": "blocked", "reason": "project_scope_mismatch"}
    return pid, sid, None


def _session_error_response(error: dict):
    code = 404 if error.get("status") == "not_found" else 403
    return JSONResponse(error, status_code=code)


def _execution_facade():
    from execution.execution_facade import ExecutionFacade
    return ExecutionFacade()


def _execution_response(payload: dict, ok_code: int = 200):
    status = payload.get("status", "")
    if status == "not_found":
        return JSONResponse(payload, status_code=404)
    if status in ("blocked", "failed", "timed_out", "review_rejected"):
        return JSONResponse(payload, status_code=403)
    return JSONResponse(payload, status_code=ok_code)


@app.get("/")
async def serve_index():
    # Interface oficial: Command Center. Raiz sempre redireciona pra lá.
    return RedirectResponse(url="/command-center/")


# Interface legada /classic (index.html/app.js/style.css) ARQUIVADA em UI-4D
# (movida para _arquivo/interfaces-legadas/classic/). Rotas /classic /style.css
# /app.js removidas.


# ── Painel (dashboard) — arquivos criados pelo Codex ──
# Rotas legadas /painel /painel.css /painel.js ARQUIVADAS em UI-4B
# (movidas para _arquivo/interfaces-legadas/). Rotas removidas.


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
async def vp_passeios_add(
    req: VPPasseioRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.passeios.add", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    item = vp_store.add_passeio(req.tipo, req.data, req.pessoas, req.valor)
    return JSONResponse({"status": "ok", "item": item})


@app.delete("/vp/passeios/{item_id}")
async def vp_passeios_del(
    item_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.passeios.delete", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
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
async def vp_clientes_add(
    req: VPClienteRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.clientes.add", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    item = vp_store.add_cliente(req.nome, req.contato, req.obs)
    return JSONResponse({"status": "ok", "item": item})


class VPStatusRequest(BaseModel):
    status: str = "fechado"


@app.patch("/vp/clientes/{item_id}")
async def vp_clientes_status(
    item_id: str,
    req: VPStatusRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.clientes.status", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.set_status(item_id, req.status) else "not_found"})


@app.delete("/vp/clientes/{item_id}")
async def vp_clientes_del(
    item_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.clientes.delete", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_cliente(item_id) else "not_found"})


# ── Geração de conteúdo de marketing (usa o cérebro/OpenAI) ──
class VPConteudoRequest(BaseModel):
    tipo: str = "ideias"   # ideias | legenda | reel
    tema: str = ""


@app.post("/vp/conteudo")
async def vp_conteudo(
    req: VPConteudoRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate(
        "vp.conteudo",
        project_id,
        external_adapters=True,
        local_token=x_javes_local_token,
        auth_required=True,
    )
    if blocked:
        return _gate_json(blocked)
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
async def vp_conteudos_add(
    req: VPSalvarConteudo,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.conteudos.add", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    if not req.texto.strip():
        return JSONResponse({"status": "vazio"}, status_code=400)
    return JSONResponse({"status": "ok", "item": vp_store.add_conteudo(req.tipo, req.texto)})


@app.delete("/vp/conteudos/{item_id}")
async def vp_conteudos_del(
    item_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.conteudos.delete", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_conteudo(item_id) else "not_found"})


# ── Estúdio de Conteúdo (Command Center — unificado: vempassear | javes) ──
class ConteudoReq(BaseModel):
    project: str = "vempassear"
    channel: str = ""
    title:   str = ""
    body:    str = ""
    status:  str = "rascunho"


@app.get("/conteudo")
async def conteudo_list(projeto: str = ""):
    import repositories as repo
    try:
        return JSONResponse({"itens": repo.content.list(projeto)})
    except Exception as e:
        return JSONResponse({"itens": [], "erro": str(e)})


@app.post("/conteudo")
async def conteudo_add(
    req: ConteudoReq,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "conteudo.add")
    if blocked:
        return _gate_json(blocked)
    project = (req.project or "").strip().lower()
    if project in {"vempassear", "vem-passear", "jampa", "cerebro-jampa"}:
        blocked = gate.require_project_scope(project_id)
        if blocked:
            return _gate_json(blocked)
        blocked = gate.require_vp_effects("conteudo.add")
    else:
        blocked = gate.require_local_actions("conteudo.add")
    if blocked:
        return _gate_json(blocked)
    import repositories as repo
    if not (req.title.strip() or req.body.strip()):
        return JSONResponse({"status": "vazio"}, status_code=400)
    try:
        cid = repo.content.add(req.project, req.channel, req.title, req.body, req.status)
        return JSONResponse({"status": "ok", "id": cid})
    except Exception as e:
        return JSONResponse({"status": "erro", "erro": str(e)}, status_code=500)


@app.get("/maquina/stats")
async def maquina_stats():
    """Números reais do pipeline de conhecimento (A Máquina). Tolerante a falha:
    cada métrica cai em None se a tabela/arquivo não existir, e o front mantém o valor de projeto."""
    import db
    def _c(sql, params=()):
        try:
            row = db.query_one(sql, params)
            return list(row.values())[0] if row else None
        except Exception:
            return None
    def _t(table):
        try:
            return db.count(table)
        except Exception:
            return None
    # dossiês de DNA (arquivos .json em _memoria/dna/)
    try:
        dna_dir = Path(__file__).resolve().parents[3] / "_memoria" / "dna"
        dossies = len(list(dna_dir.glob("*.json"))) if dna_dir.exists() else None
    except Exception:
        dossies = None
    chunks = _t("knowledge_chunks")
    return JSONResponse({
        "capture":       _c("SELECT COUNT(DISTINCT path) AS n FROM knowledge_chunks"),
        "chunk":         chunks,
        "rag":           chunks,
        "grafo_nos":     _t("kg_nodes"),
        "grafo_arestas": _t("kg_edges"),
        "dossies":       dossies,
        "mensagens":     _t("messages"),
        "conteudos":     _t("content"),
    })


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
async def vp_pauta_add(
    req: VPPautaRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.pauta.add", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    return JSONResponse({"status": "ok", "item": vp_store.add_pauta(req.data, req.canal, req.ideia)})


class VPPautaStatus(BaseModel):
    status: str = "publicado"


@app.patch("/vp/pauta/{item_id}")
async def vp_pauta_status(
    item_id: str,
    req: VPPautaStatus,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.pauta.status", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.set_pauta_status(item_id, req.status) else "not_found"})


@app.delete("/vp/pauta/{item_id}")
async def vp_pauta_del(
    item_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _vp_project_gate("vp.pauta.delete", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import vp_store
    return JSONResponse({"status": "ok" if vp_store.remove_pauta(item_id) else "not_found"})


# ── Registry de projetos externos conectados (Javis = orquestrador mestre) ──
@app.get("/projects/registry")
async def projects_registry():
    """Estado real (lido do disco, read-only) dos projetos externos plugados no Javis."""
    import project_registry
    return JSONResponse({"projects": project_registry.list_projects()})


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
async def jampa_squad_run(
    req: JampaSquadRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Aciona o squad: Orion escolhe o agente (ou força um) e executa, aterrado."""
    blocked = _vp_project_gate(
        "jampa.squad",
        project_id,
        external_adapters=True,
        local_token=x_javes_local_token,
        auth_required=True,
    )
    if blocked:
        return _gate_json(blocked)
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
async def jampa_responder_lead(
    req: JampaLeadRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Fluxo-dinheiro: gera a resposta de WhatsApp pronta pro lead (aterrada)."""
    blocked = _vp_project_gate(
        "jampa.responder_lead",
        project_id,
        external_adapters=True,
        local_token=x_javes_local_token,
        auth_required=True,
    )
    if blocked:
        return _gate_json(blocked)
    import jampa_squad
    out = await run_in_threadpool(
        jampa_squad.responder_lead, req.nome, req.contato, req.interesse, req.obs)
    return JSONResponse({"status": "ok", **out})


class JampaForjarRequest(BaseModel):
    transcricao: str
    tema:        str = ""


@app.post("/jampa/forjar-skill")
async def jampa_forjar_skill(
    req: JampaForjarRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Pipeline Nero: transcrição de expert → skill .md (rascunho p/ Murillo revisar)."""
    blocked = _vp_project_gate(
        "jampa.forjar_skill",
        project_id,
        external_adapters=True,
        local_token=x_javes_local_token,
        auth_required=True,
    )
    if blocked:
        return _gate_json(blocked)
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
async def chat(
    req: ChatRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    start = datetime.now()
    blocked = _local_auth_gate(x_javes_local_token, "chat")
    if blocked:
        return _gate_json(blocked)
    project_id = _normalize_project_id(req.project_id)
    blocked = gate.require_project_scope(project_id, scope=[gate.CORE_SCOPE, gate.CEREBRO_JAMPA_SCOPE])
    if blocked:
        return _gate_json(blocked)
    project_id, session_id, session_error = _resolve_session(project_id, req.session_id)
    if session_error:
        return _session_error_response(session_error)

    text  = req.message.strip()
    if not text:
        return JSONResponse({"error": "Mensagem vazia"}, status_code=400)

    orchestrator.model = req.model
    route = command_router.route(text)

    # Ações críticas bloqueadas imediatamente
    if route["risk_level"] == "critical":
        payload = gate.blocked("critical_action", action="chat")
        entry = _make_entry("blocked", text, route, payload, start)
        _save(entry)
        return JSONResponse({**entry, **payload})

    # Núcleo único (threadpool evita bloquear o event loop)
    out = await run_in_threadpool(_brain, text, _get_history_messages(project_id, session_id), req.use_conclave, project_id)
    entry = _entry_from_brain(text, out, start)
    entry["project_id"] = project_id
    entry["session_id"] = session_id
    _save(entry)
    _persist_messages(text, out, project_id=project_id, session_id=session_id)  # dual-write SQLite (não quebra se falhar)
    return JSONResponse(entry)


class DebateRequest(BaseModel):
    task:    str
    agents:  list[str] = ["architect", "developer", "analyst"]
    rounds:  int = 2
    model:   str = "claude"


@app.post("/debate")
async def debate(req: DebateRequest):
    """Debate autônomo de squad — agentes debatem entre si sem intervenção do usuário."""
    if not safe_config.external_adapters_enabled():
        return _disabled_json("external_adapters", safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS)
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


@app.get("/briefing")
async def briefing_endpoint():
    """Saudação proativa + estado do projeto para a interface receber o senhor."""
    try:
        import briefing
        return JSONResponse(briefing.briefing_dict())
    except Exception as e:
        return JSONResponse({"saudacao": "Bom dia, senhor.", "estado": "", "erro": str(e)})


@app.get("/brain/active")
async def brain_active_get():
    import brain_switch
    return JSONResponse({"engine": brain_switch.get_active()})


class BrainActiveRequest(BaseModel):
    engine: str


@app.post("/brain/active")
async def brain_active_set(
    req: BrainActiveRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "brain.active")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_local_actions("brain.active")
    if blocked:
        return _gate_json(blocked)
    import brain_switch
    try:
        engine = brain_switch.set_active(req.engine)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return JSONResponse({"engine": engine})


@app.get("/status")
async def status():
    services = {}
    for name, port in SERVICES.items():
        try:
            # 127.0.0.1 (não "localhost"): localhost resolve pra IPv6 ::1 e fica
            # esperando o timeout inteiro quando a porta está offline, deixando o
            # /status lento e estourando o timeout do cliente. Em 127.0.0.1 a
            # porta offline RECUSA na hora (sem espera).
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                services[name] = {"status": "online", "port": port}
        except OSError:
            services[name] = {"status": "offline", "port": port}
    # Cérebro = Claude pela assinatura (não é porta; é o CLI logado).
    try:
        import claude_brain
        brain_ok = claude_brain.available()
    except Exception:
        brain_ok = False
    return JSONResponse({
        "services": services,
        "brain": {"engine": "claude", "status": "online" if brain_ok else "offline"},
        "ts": _ts(),
    })


@app.get("/exec/status")
async def exec_status():
    """Estado em tempo real da execução via claude_exec (programar tool)."""
    try:
        import claude_exec
        s = claude_exec.get_status()
        return JSONResponse({
            "running": s["running"],
            "task": s["task"],
            "pasta": s["pasta"],
            "started_at": s.get("started_at"),
            "exit_code": s.get("exit_code"),
            "lines": s["lines"][-150:],
            "total_lines": len(s["lines"]),
        })
    except Exception as e:
        return JSONResponse({"running": False, "task": "", "pasta": None,
                             "started_at": None, "exit_code": None,
                             "lines": [], "total_lines": 0, "error": str(e)})


@app.get("/execution/tasks")
async def execution_tasks_list(
    project_id: str = "",
    status: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.tasks.list")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(project_id)
    blocked = gate.require_project_scope(pid, scope=[gate.CORE_SCOPE, gate.CEREBRO_JAMPA_SCOPE])
    if blocked:
        return _gate_json(blocked)
    items = _execution_facade().list_tasks(pid, status=status or None)
    return JSONResponse({
        "tasks": items,
        "total": len(items),
        "project_id": pid,
        "supervised_execution_enabled": safe_config.supervised_execution_enabled(),
    })


@app.post("/execution/tasks")
async def execution_tasks_create(
    req: ExecutionTaskCreateRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.tasks.create")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(req.project_id)
    blocked = gate.require_project_scope(pid, scope=[gate.CORE_SCOPE, gate.CEREBRO_JAMPA_SCOPE])
    if blocked:
        return _gate_json(blocked)
    try:
        out = _execution_facade().create_task(
            objective=req.objective,
            project_id=pid,
            executor=req.executor,
            timeout_seconds=req.timeout_seconds,
        )
    except Exception as exc:
        return _execution_response({"status": "blocked", "reason": str(exc)})
    return _execution_response(out, ok_code=201)


@app.get("/execution/tasks/{task_id}")
async def execution_tasks_get(
    task_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.tasks.get")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(project_id)
    return _execution_response(_execution_facade().get_task(task_id, pid))


@app.get("/execution/tasks/{task_id}/result")
async def execution_tasks_result(
    task_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.tasks.result")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(project_id)
    return _execution_response(_execution_facade().result_summary(task_id, pid))


@app.post("/execution/tasks/{task_id}/request-start-approval")
async def execution_request_start_approval(
    task_id: str,
    req: ExecutionProjectRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.start.request")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(req.project_id)
    try:
        out = _execution_facade().request_start_approval(task_id, pid)
    except Exception as exc:
        return _execution_response({"status": "blocked", "reason": str(exc)})
    return _execution_response(out)


@app.post("/execution/tasks/{task_id}/approve-start")
async def execution_approve_start(
    task_id: str,
    req: ExecutionApprovalRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.start.approve")
    if blocked:
        return _gate_json(blocked)
    if not req.approval_id:
        return _execution_response({"status": "blocked", "reason": "approval_id_required"})
    pid = _normalize_project_id(req.project_id)
    try:
        out = _execution_facade().approve_start(task_id, pid, int(req.approval_id))
    except Exception as exc:
        return _execution_response({"status": "blocked", "reason": str(exc)})
    return _execution_response(out)


@app.post("/execution/tasks/{task_id}/start")
async def execution_start(
    task_id: str,
    req: ExecutionStartRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.start")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(req.project_id)
    return _execution_response(_execution_facade().start_execution(task_id, pid, req.test_commands))


@app.post("/execution/tasks/{task_id}/request-merge-approval")
async def execution_request_merge_approval(
    task_id: str,
    req: ExecutionProjectRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.merge.request")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(req.project_id)
    try:
        out = _execution_facade().request_merge_approval(task_id, pid)
    except Exception as exc:
        return _execution_response({"status": "blocked", "reason": str(exc)})
    return _execution_response(out)


@app.post("/execution/tasks/{task_id}/approve-merge")
async def execution_approve_merge(
    task_id: str,
    req: ExecutionApprovalRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.merge.approve")
    if blocked:
        return _gate_json(blocked)
    if not req.approval_id:
        return _execution_response({"status": "blocked", "reason": "approval_id_required"})
    pid = _normalize_project_id(req.project_id)
    try:
        out = _execution_facade().approve_merge(task_id, pid, int(req.approval_id))
    except Exception as exc:
        return _execution_response({"status": "blocked", "reason": str(exc)})
    return _execution_response(out)


@app.post("/execution/tasks/{task_id}/merge")
async def execution_merge(
    task_id: str,
    req: ExecutionProjectRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.merge")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(req.project_id)
    return _execution_response(_execution_facade().perform_merge(task_id, pid))


@app.post("/execution/tasks/{task_id}/cancel")
async def execution_cancel(
    task_id: str,
    req: ExecutionProjectRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "execution.cancel")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(req.project_id)
    return _execution_response(_execution_facade().cancel_task(task_id, pid))


@app.get("/stats")
async def stats():
    """Contadores REAIS pra UI (vêm do SQLite, não de texto fixo)."""
    try:
        import repositories as repo
        return JSONResponse({
            "messages":         repo.messages.count(),
            "agents":           repo.agents.count(),
            "tasks_total":      repo.tasks.count(),
            "tasks_pending":    repo.tasks.count("pending"),
            "tasks_done":       repo.tasks.count("done"),
            "approvals_pending": repo.approvals.count_pending(),
            "projects":         repo.projects.count(),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/tasks")
async def tasks_list(status: str = "", workflow: str = "", agent: str = "", project_id: str = ""):
    """Tasks do Quadro — SQLite é a FONTE PRINCIPAL. Markdown (mission_board) é
    fallback: se o SQLite estiver vazio, sincroniza do backlog antes de responder.
    Filtros opcionais: status, workflow (=mission), agent, project_id."""
    try:
        import repositories as repo
        pid = _normalize_project_id(project_id)  # ausente → javes-core; nunca "todos"
        if repo.tasks.count() == 0:           # fallback: popula do Markdown
            import db_sync
            db_sync.sync_tasks()
        rows = repo.tasks.for_board(status=status, workflow=workflow, agent=agent, project_id=pid)
        out = []
        for r in rows:
            digest = (r.get("digest_text") or "").strip()
            out.append({
                "id": r.get("id"), "ext_id": r.get("ext_id"), "title": r.get("title"),
                "status": r.get("status"), "agent": r.get("agent_eff") or "",
                "workflow": r.get("workflow") or r.get("mission") or "",
                "project_id": r.get("project_id") or "",
                "created_at": r.get("created_at"), "updated_at": r.get("updated_at"),
                "completed_at": r.get("completed_at"), "killed_at": r.get("killed_at"),
                "has_digest": bool(digest),
            })
        return JSONResponse({"tasks": out, "total": len(out), "source": "sqlite"})
    except Exception as e:
        return JSONResponse({"error": str(e), "tasks": [], "total": 0}, status_code=500)


@app.get("/tasks/{task_id}/events")
async def task_events(task_id: str, project_id: str = ""):
    """Journey Log: timeline cronológica dos eventos de uma task (+ status/digest)."""
    try:
        import repositories as repo
        pid = _normalize_project_id(project_id)  # ausente → javes-core; nunca "todos"
        task = repo.tasks.get_task(task_id, project_id=pid)
        if not task:
            return JSONResponse({"status": "not_found", "reason": "task_not_found", "events": [], "total": 0}, status_code=404)
        evs = repo.task_events.list_by_task(task_id)
        return JSONResponse({
            "task_id": task_id, "events": evs, "total": len(evs),
            "task_status": task.get("status"),
            "completed_at": task.get("completed_at"),
            "killed_at": task.get("killed_at"),
            "digest_text": task.get("digest_text"),
        })
    except Exception as e:
        return JSONResponse({"error": str(e), "events": [], "total": 0}, status_code=500)


@app.post("/tasks/{task_id}/run-studio")
async def task_run_studio(
    task_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Roda o Estúdio (modo seguro) na task de Design: gera criativos textuais,
    registra o Journey Log e cria o Gate 2. Sem imagem, sem publicar, sem integração."""
    blocked = _vp_project_gate("tasks.run_studio", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import studio
    out = await run_in_threadpool(studio.run_studio, task_id)
    code = 200 if out.get("ok") else 409
    return JSONResponse(out, status_code=code)


@app.post("/tasks/{task_id}/prepare-distribution")
async def task_prepare_distribution(
    task_id: str,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Prepara a Distribuição (modo seguro) na task liberada: gera o pacote textual,
    registra o Journey Log e cria o Gate 3. NÃO publica, sem integração externa."""
    blocked = _vp_project_gate("tasks.prepare_distribution", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import distribution
    out = await run_in_threadpool(distribution.run_distribution, task_id)
    code = 200 if out.get("ok") else 409
    return JSONResponse(out, status_code=code)


class StatusRequest(BaseModel):
    status: str
    note: str = ""


@app.post("/tasks/{task_id}/status")
async def task_set_status(
    task_id: str,
    req: StatusRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Muda o status da task (operação do Quadro) via SQLite. completed/killed
    reusam o fluxo de conclusão/digest. Sem integração externa."""
    blocked = _vp_project_gate("tasks.status", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import task_lifecycle
    out = await run_in_threadpool(task_lifecycle.change_task_status, task_id, req.status, req.note or "")
    code = 200 if out.get("ok") else 409
    return JSONResponse(out, status_code=code)


class CompleteRequest(BaseModel):
    note: str = ""


@app.post("/tasks/{task_id}/complete")
async def task_complete(
    task_id: str,
    req: CompleteRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Encerra a entidade-tarefa (completed/killed) + gera digest. Sem LLM, sem integração externa."""
    blocked = _vp_project_gate("tasks.complete", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    import task_lifecycle
    out = await run_in_threadpool(task_lifecycle.complete_task, task_id, req.note or "")
    code = 200 if out.get("ok") else 409
    return JSONResponse(out, status_code=code)


@app.get("/tasks/{task_id}/digest")
async def task_digest(task_id: str, project_id: str = ""):
    """Digest final da task (resumo da jornada)."""
    try:
        import repositories as repo
        pid = _normalize_project_id(project_id)  # ausente → javes-core; nunca "todos"
        t = repo.tasks.get_task(task_id, project_id=pid)
        if not t:
            return JSONResponse({"status": "not_found", "reason": "task_not_found"}, status_code=404)
        return JSONResponse({
            "task_id": task_id, "status": t.get("status"),
            "completed_at": t.get("completed_at"), "killed_at": t.get("killed_at"),
            "digest_text": t.get("digest_text") or "",
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/approvals/pending")
async def approvals_pending(project_id: str = ""):
    """Aprovações pendentes (Gate humano) — do SQLite."""
    try:
        import repositories as repo
        pid = _normalize_project_id(project_id)  # ausente → javes-core; nunca "todos"
        rows = repo.approvals.pending(project_id=pid)
        return JSONResponse({"approvals": rows, "total": len(rows), "project_id": pid})
    except Exception as e:
        return JSONResponse({"error": str(e), "approvals": [], "total": 0}, status_code=500)


class DecisionRequest(BaseModel):
    decision: str            # "approved" | "rejected"
    note: str = ""


@app.post("/approvals/{approval_id}/decide")
async def approvals_decide(
    approval_id: int,
    req: DecisionRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Decide um Gate (aprovar/rejeitar). Persiste no SQLite e registra em action_logs.
    NÃO aciona integração externa, NÃO publica, NÃO envia WhatsApp — só registra a decisão."""
    blocked = _local_auth_gate(x_javes_local_token, "approvals.decide")
    if blocked:
        return _gate_json(blocked)
    import repositories as repo
    decision = (req.decision or "").strip().lower()
    if decision not in ("approved", "rejected"):
        return JSONResponse({"error": "decision deve ser 'approved' ou 'rejected'"}, status_code=400)
    ap = repo.approvals.get(approval_id)
    if not ap:
        return JSONResponse({"error": f"aprovação {approval_id} não encontrada"}, status_code=404)
    if ap.get("status") != "pending":
        return JSONResponse({"error": f"aprovação já decidida ({ap.get('status')})",
                             "approval": ap}, status_code=409)

    approved = decision == "approved"
    repo.approvals.decide(approval_id, approved, note=req.note or "", approved_by="local")
    # registra a decisão em action_logs (sem JSONL — é decisão humana, não ação de IA)
    try:
        repo.logs.add(
            source="frontend", intent="approval_decide", agent=ap.get("agent", ""),
            message=f"Gate '{ap.get('subject', '')[:80]}' → {decision}"
                    + (f" (obs: {req.note[:100]})" if req.note else ""),
            status=decision, approved=approved,
        )
    except Exception as e:
        print(f"[approvals] log falhou: {e}", flush=True)

    # Efeitos do workflow (MODO SEGURO): se for a Gate 1 da pauta VP, destrava o
    # Design. NÃO gera criativo, NÃO chama Nova, NÃO toca integração externa.
    effect = {"advanced": False}
    try:
        import approval_effects
        effect = approval_effects.on_decided(ap, approved, req.note or "")
    except Exception as e:
        print(f"[approvals] efeito do workflow falhou: {e}", flush=True)

    return JSONResponse({
        "ok": True, "id": approval_id, "status": decision,
        "approvals_pending": repo.approvals.count_pending(),
        "advanced": effect.get("advanced", False),
        "message": effect.get("message", ""),
    })


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


class AgentRunRequest(BaseModel):
    agent_id: str
    task: str
    project_id: str = ""
    approved: bool = False
    approval_id: int | None = None


@app.post("/agents/run")
async def agents_run(
    req: AgentRunRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Executa um agente com skill + RAG + cérebro forte (Claude/assinatura)."""
    blocked = _local_auth_gate(x_javes_local_token, "agents.run")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(req.project_id, scope=gate.CORE_SCOPE)
    if blocked:
        return _gate_json(blocked)
    if not safe_config.claude_exec_enabled():
        return _disabled_json("claude_exec", safe_config.JAVIS_ENABLE_CLAUDE_EXEC)
    blocked = gate.require_persisted_approval(
        "agents.run",
        approval_id=req.approval_id,
        route="/agents/run",
        project_id=req.project_id,
        risk_level="high",
        approved=req.approved,
    )
    if blocked:
        return _gate_json(blocked)
    import agent_runner
    out = await run_in_threadpool(agent_runner.run_agent, req.agent_id, req.task)
    return JSONResponse(out)


@app.get("/vp/agents")
async def vp_agents_list():
    """Squad de marketing da Vem Passear — os 5 agentes com contrato (Input/Output/Não faz)."""
    import vp_squad
    return JSONResponse({"agents": vp_squad.list_agents(), "total": len(vp_squad.AGENTS)})


class VPRunRequest(BaseModel):
    agent_id: str
    task: str
    context: str = ""


@app.post("/vp/agents/run")
async def vp_agents_run(
    req: VPRunRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Executa um agente do squad da Vem Passear (contrato como system prompt, na assinatura)."""
    blocked = _vp_project_gate("vp.agents.run", project_id, local_token=x_javes_local_token, auth_required=True)
    if blocked:
        return _gate_json(blocked)
    if not safe_config.claude_exec_enabled():
        return _disabled_json("claude_exec", safe_config.JAVIS_ENABLE_CLAUDE_EXEC)
    import vp_squad
    out = await run_in_threadpool(vp_squad.run, req.agent_id, req.task, req.context)
    return JSONResponse(out)


class VoiceRequest(BaseModel):
    transcript: str
    project_id: str = ""
    model:       str  = "claude"
    use_conclave: bool = False
    tts:         bool = True


@app.post("/voice")
async def voice_input(
    req: VoiceRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Processa transcrição de voz pelo pipeline completo — wake word strip, hallucination filter, orquestrador."""
    blocked = _local_auth_gate(x_javes_local_token, "voice")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(req.project_id, scope=gate.CORE_SCOPE)
    if blocked:
        return _gate_json(blocked)
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
        payload = gate.blocked("critical_action", action="voice")
        entry = _make_entry("blocked", clean, route, payload, start)
        entry["source"] = "voice"
        _save(entry)
        return JSONResponse({**entry, **payload, "response": "Ação bloqueada.", "tts": True})

    # Núcleo único — mesmo cérebro do chat
    out = await run_in_threadpool(_brain, clean, _get_history_messages(), req.use_conclave, req.project_id)
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
async def voice_stream(
    req: VoiceRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Voice com TTS incremental — começa a falar assim que a 1ª frase fica pronta (SSE)."""
    from voice_bridge import classify_voice, _strip_wake_word

    _SSE = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

    blocked = _local_auth_gate(x_javes_local_token, "voice.stream")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(req.project_id, scope=gate.CORE_SCOPE)
    if blocked:
        return _gate_json(blocked)

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
        return _gate_json(gate.blocked("critical_action", action="voice.stream"))

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

        # CÉREBRO PADRÃO DO CHAT = Claude pela ASSINATURA (Opus 4.8), falando frase
        # a frase conforme pensa. Decisão do Murillo (18/06): tirar a API paga do
        # OpenAI do caminho de conversa e usar a assinatura. Toda conversa/raciocínio
        # vai DIRETO ao Claude em streaming; ações com ferramenta (lembrete, abrir,
        # programar) já foram tratadas no fast-path ou caem no _brain abaixo. Se o
        # Claude estiver indisponível ou devolver vazio, cai no _brain (fallback).
        if (not req.use_conclave
                and safe_config.claude_exec_enabled()
                and (_likely_council(clean) or intent in ("conversa", "desconhecido"))):
            try:
                import claude_brain as _cb
                import agent as _ag
            except Exception:
                _cb = None
            if _cb and _cb.available():
                # Voz = Haiku + contexto enxuto (decisão Murillo 18/06). ATUALIZAÇÃO
                # 2026-07-05: com o cérebro de voz agora no OpenRouter free (rápido)
                # ficamos grounded — a persona sozinha alucinava ("rodando no Chainlit"
                # etc). Injeta: histórico + estado do projeto (se pergunta é sobre o
                # projeto) + trechos do RAG (se pergunta parece factual). Cada peça
                # entra best-effort e nunca segura a resposta.
                ctx = _ag._history_context(_get_history_messages(), keep_raw=2)
                ctx = _add_voice_grounding(clean, ctx)
                spoke = False
                full_text = ""
                # Cérebro de voz — cascata configurável por JAVIS_VOICE_BRAIN:
                #   'openrouter' → OpenRouter FREE (0.7-2s, pt-BR limpo, "senhor"). Melhor default.
                #   'ollama'     → Ollama LOCAL (grátis, ~1s).
                #   (vazio)      → Claude assinatura (~20s — lento, só se nada mais).
                # Só CONVERSA chega aqui; ações já foram pro fast-path/_brain.
                _vname = "claude"; _vstream = None
                _brain_pref = os.environ.get("JAVIS_VOICE_BRAIN", "").lower()
                if _brain_pref == "openrouter":
                    try:
                        import openrouter_voice as _ov
                        if _ov.available():
                            _vname = "openrouter"
                            _vstream = _ov.answer_stream(clean, ctx)
                    except Exception:
                        _vstream = None
                elif _brain_pref == "ollama":
                    try:
                        import ollama_brain as _ob
                        if _ob.available():
                            _vname = "ollama"
                            _vstream = _ob.answer_stream(clean, ctx, system="Você é o Javes, assistente de voz do Murillo. Responda curto e direto, em português do Brasil, tom parceiro.")
                    except Exception:
                        _vstream = None
                if _vstream is None:
                    _vstream = _cb.answer_stream(clean, ctx, model=_cb._VOICE_MODEL)
                yield f"data: {json.dumps({'type':'meta','intent':'pensar_profundo','brain':_vname})}\n\n"
                for sentence in _accumulate_sentences(_vstream):
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
        out = _brain(clean, _get_history_messages(), req.use_conclave, req.project_id)
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
    model:           str = "claude"


@app.post("/rootcause")
async def rootcause(req: RootcauseRequest):
    """Rootcause diagnostica uma resposta ruim e aprende para não repetir."""
    if not safe_config.external_adapters_enabled():
        return _disabled_json("external_adapters", safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS)
    from agents.meta import Rootcause
    rc = Rootcause(model=req.model)
    result = rc.diagnose(req.task, req.failed_response, req.agents_used)
    return JSONResponse(result)


@app.get("/history/session")
async def history(
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "history.session")
    if blocked:
        return _gate_json(blocked)
    return JSONResponse({"history": _history[-50:]})


@app.get("/history")
async def get_history(
    project_id: str = "",
    session_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Retorna histórico de chat persistido em disco."""
    blocked = _local_auth_gate(x_javes_local_token, "history.read")
    if blocked:
        return _gate_json(blocked)
    project_id, session_id, session_error = _resolve_session(project_id, session_id)
    if session_error:
        return _session_error_response(session_error)
    return JSONResponse(history_store.load(project_id, session_id))


@app.get("/history/sessions")
async def history_sessions(
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    blocked = _local_auth_gate(x_javes_local_token, "history.sessions")
    if blocked:
        return _gate_json(blocked)
    pid = _normalize_project_id(project_id)
    return JSONResponse({"project_id": pid, "sessions": history_store.list_sessions(pid)})


@app.delete("/history")
async def clear_history(
    project_id: str = "",
    session_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Limpa o histórico de chat."""
    blocked = _local_auth_gate(x_javes_local_token, "history.clear")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_local_actions("history.clear")
    if blocked:
        return _gate_json(blocked)
    project_id, session_id, session_error = _resolve_session(project_id, session_id, create_if_missing=False)
    if session_error:
        return _session_error_response(session_error)
    sid = session_id or history_store.DEFAULT_SESSION_ID
    history_store.clear(project_id, sid)
    return JSONResponse({"status": "ok", "project_id": project_id, "session_id": sid})


# ── Streaming chat ────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Chat com streaming token-a-token (SSE)."""
    import json as _j

    blocked = _local_auth_gate(x_javes_local_token, "chat.stream")
    if blocked:
        return _gate_json(blocked)
    project_id = _normalize_project_id(req.project_id)
    blocked = gate.require_project_scope(project_id, scope=[gate.CORE_SCOPE, gate.CEREBRO_JAMPA_SCOPE])
    if blocked:
        return _gate_json(blocked)
    project_id, session_id, session_error = _resolve_session(project_id, req.session_id)
    if session_error:
        return _session_error_response(session_error)

    text = req.message.strip()
    if not text:
        return JSONResponse({"error": "Mensagem vazia"}, status_code=400)

    orchestrator.model = req.model
    route  = command_router.route(text)

    if route["risk_level"] == "critical":
        return _gate_json(gate.blocked("critical_action", action="chat.stream"))

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
                _persist_messages(text, out, project_id=project_id, session_id=session_id)
                yield f"data: {_j.dumps({'type':'done','brain':'main','intent':intent0,'ms':entry['ms'],'project_id':project_id,'session_id':session_id})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 2) Conversa OU ação → cérebro com FERRAMENTAS (raciocínio real:
            #    busca nas notas, lembra fatos, encadeia ações), depois fake-stream.
            #    O padding acima já deu feedback instantâneo — não perdemos UX.
            out = _brain(text, _get_history_messages(project_id, session_id), req.use_conclave, project_id)
            for word in (out["text"] or "Pronto, senhor.").split(" "):
                yield f"data: {_j.dumps({'type':'token','text':word + ' '})}\n\n"
            entry = _entry_from_brain(text, out, start)
            _save(entry)
            _persist_messages(text, out, project_id=project_id, session_id=session_id)  # dual-write SQLite
            yield f"data: {_j.dumps({'type':'done','brain':out['brain'],'intent':out['intent'],'ms':entry['ms'],'project_id':project_id,'session_id':session_id})}\n\n"
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
    if not safe_config.external_adapters_enabled():
        return _disabled_json("external_adapters", safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS)
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
async def upload_file(
    file: UploadFile = File(...),
    approved: bool = False,
    approval_id: int | None = None,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Recebe um arquivo, salva temporariamente e analisa com file_analyzer."""
    blocked = gate.validate_upload_filename(file.filename)
    if blocked:
        return _gate_json(blocked)
    blocked = _local_auth_gate(x_javes_local_token, "upload")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_external_adapters("upload")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_persisted_approval(
        "upload",
        approval_id=approval_id,
        route="/upload",
        risk_level="high",
        reason="upload salva arquivo temporario e chama analise LLM/visao",
        metadata={"filename": file.filename or ""},
        approved=approved,
    )
    if blocked:
        return _gate_json(blocked)

    tmp_path = gate.reserve_upload_path(file.filename)
    try:
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        with tmp_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > gate.MAX_UPLOAD_BYTES:
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                    return _gate_json(gate.upload_too_large(size), status_code=413)
                out.write(chunk)
        import file_analyzer
        result = await run_in_threadpool(file_analyzer.analyze, str(tmp_path), "")
        result["filename"] = file.filename
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass


class WAAnalyzeRequest(BaseModel):
    text: str
    me:   str = ""


@app.post("/wa/analyze")
async def wa_analyze(
    req: WAAnalyzeRequest,
    project_id: str = "",
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Analisa um export de conversa do WhatsApp (local, via Claude assinatura)."""
    blocked = _local_auth_gate(x_javes_local_token, "wa.analyze")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(project_id)
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_external_adapters("wa.analyze")
    if blocked:
        return _gate_json(blocked)
    import wa_analyzer
    out = await run_in_threadpool(wa_analyzer.analyze, req.text, req.me)
    return JSONResponse(out)


class WASaveRequest(BaseModel):
    content: str


@app.post("/wa/save-voice")
async def wa_save_voice(
    req: WASaveRequest,
    project_id: str = "",
    approved: bool = False,
    approval_id: int | None = None,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Salva o material destilado como grounding do squad (voz-murillo.md)."""
    blocked = _local_auth_gate(x_javes_local_token, "wa.save_voice")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(project_id)
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_local_actions("wa.save_voice")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_vp_effects("wa.save_voice")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_persisted_approval(
        "wa.save_voice",
        approval_id=approval_id,
        route="/wa/save-voice",
        project_id=project_id,
        risk_level="high",
        reason="wa.save_voice escreve grounding no projeto conectado",
        approved=approved,
    )
    if blocked:
        return _gate_json(blocked)
    import wa_analyzer
    path = wa_analyzer.save_voice_doc(req.content)
    return JSONResponse({"status": "ok", "file": path})


class TTSRequest(BaseModel):
    text: str
    voice: str = ""
    model: str = ""


@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    """TTS — Piper local (grátis, padrão), fallback pra OpenAI (pago) se
    indisponível. Pedido com voice/model explícitos pula direto pro OpenAI
    (Piper não tem essas vozes)."""
    import os
    from fastapi.responses import Response

    clean = req.text[:600]
    provider = os.environ.get("JAVIS_TTS_PROVIDER", "piper")

    if provider == "piper" and not req.voice and not req.model:
        audio_bytes = tts_local.synthesize(clean)
        if audio_bytes:
            return Response(content=audio_bytes, media_type="audio/wav")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "OPENAI_API_KEY não configurada"}, status_code=503)

    voice = req.voice or os.environ.get("JAVIS_TTS_VOICE", "nova")
    model = req.model or os.environ.get("JAVIS_TTS_MODEL", "tts-1")

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
    "trocar_motor", "atualizar_memoria",
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
    if intent == "status_sistema":
        return True
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


# Palavras que indicam que a pergunta é sobre o PROJETO/estado (não conversa fiada).
# Se bater, injeta o estado atual + busca no RAG antes de responder por voz.
# Conservador: só injeta quando faz sentido, pra não pesar toda saudação.
_PROJECT_HINTS = (
    "projeto", "javis", "javes", "vem passear", "cérebro", "cerebro", "orquestra",
    "codex", "codigo", "código", "backend", "frontend", "agente", "squad",
    "grafo", "dna", "ingest", "rag", "conclave", "delegac", "voz do jav",
    "megabrain", "mega brain", "outlier", "hub.ai", "hub ai",
    "o que a gente", "o que voce fez", "o que você fez", "o que fizemos",
    "o que ta rodando", "o que está rodando", "como está", "como esta",
    "o que rolou", "onde estamos", "estado atual", "próximos passos",
    "roadmap", "backlog", "commit",
)


def _is_project_question(text: str) -> bool:
    t = (text or "").lower()
    return any(h in t for h in _PROJECT_HINTS)


# Vem Passear Jampa é projeto EXTERNO (fronteira do CLAUDE.md). Por padrão o Javes
# NÃO puxa contexto de VP no RAG da voz — senão "vira" a empresa (bug de identidade).
# Só quando a pergunta nomeia VP explicitamente é que o escopo vp é liberado.
_VP_RE = _re.compile(r"\b(vem\s*passear|vp|jampa)\b", _re.IGNORECASE)


def _menciona_vp(text: str) -> bool:
    return bool(_VP_RE.search(text or ""))


def _escopo_voz(pergunta: str):
    """Escopo do RAG para a voz: exclui 'vp' a menos que a pergunta cite VP.
    Retorna None (sem filtro = tudo) só quando VP é explicitamente mencionada."""
    return None if _menciona_vp(pergunta) else ["projeto", "pessoal"]


def _add_voice_grounding(pergunta: str, ctx: str) -> str:
    """Adiciona estado do projeto + trechos do RAG ao contexto de voz — só quando
    faz sentido (pergunta sobre o projeto ou factual). Nunca segura a resposta:
    cada peça é best-effort com timeout curto. Sem essa injeção, o cérebro de voz
    alucina sobre o projeto (persona sozinha inventa "Chainlit", "17 agentes" etc).
    """
    if not _is_project_question(pergunta):
        return ctx  # conversa fiada: mantém enxuto pra não pesar
    parts = [ctx] if ctx else []

    # 1) Estado do projeto (fonte-da-verdade) — o mesmo que o chat usa
    try:
        import briefing
        estado = briefing.estado_resumido()
        if estado:
            parts.append(
                "## Estado atual do projeto Javis (use isto para responder o que "
                "está rodando/pendente; NÃO invente nada fora disto):\n" + estado
            )
    except Exception:
        pass

    # 2) Trechos do RAG relevantes à pergunta (memória viva do vault).
    # Escopo: o Javes, falando como si mesmo, não puxa contexto de VP — só quando
    # a pergunta cita VP explicitamente (fronteira "por registro" do CLAUDE.md).
    try:
        import knowledge
        trechos = knowledge.answer_context(pergunta, k=3, escopo=_escopo_voz(pergunta))
        if trechos and trechos.strip():
            parts.append(
                "## Trechos relevantes do seu vault (base semântica):\n" + trechos
            )
    except Exception:
        pass

    return "\n\n".join(parts)


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
    if not safe_config.external_adapters_enabled():
        return None
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
    if not safe_config.external_adapters_enabled():
        return safe_config.disabled_message("external_adapters", safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS)
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


def _brain(
    text: str,
    history: list[dict],
    use_conclave: bool = False,
    project_id: str = gate.CORE_SCOPE,
) -> dict:
    """Núcleo ÚNICO de decisão do Jamba (usado por /chat, /chat/stream e /voice).

    Cascata: atalho local → conclave (se pedido) → agente tool-use → cérebro
    principal direto. Tudo no Claude pela assinatura; sem Ollama (decisão 19/06).
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

    try:
        from delegacao import should_delegate as _deleg_match
        if _deleg_match(text):
            resp, _ = orchestrator._run_exec(text, "", project_id=project_id)
            task = getattr(orchestrator, "_last_exec_task", {}) or {}
            return {"text": resp or "Tarefa criada e aguardando aprovação para execução.",
                    "intent": "programar", "brain": "exec",
                    "status": "pending_approval", "tools": ["execution_task"],
                    "route": route, "orch": None,
                    "task_id": task.get("task_id"),
                    "project_id": task.get("project_id", project_id),
                    "approval_id": task.get("approval_id")}
    except Exception:
        pass

    if not safe_config.external_adapters_enabled():
        return {"text": safe_config.disabled_message(
                    "external_adapters",
                    safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS),
                "intent": intent, "brain": "disabled",
                "status": "disabled_by_default", "tools": [],
                "route": route, "orch": None}

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

    # 2.5) Delegação automática Claude→Codex — se ligada (JAVIS_AUTO_CODEX) e a
    #      tarefa for execução pura (verbo inequívoco: programa, refatora, roda…),
    #      passa direto pro Codex com guardrails, sem gastar o cérebro. Claude
    #      audita depois via _audit_after_codex. Falha → cai no fluxo normal.
    try:
        from delegacao import enabled as _deleg_on, should_delegate as _deleg_match
        if _deleg_on() and _deleg_match(text):
            resp, _ = orchestrator._run_exec(text, "", project_id=project_id)
            return {"text": resp or "Codex despachado, senhor.", "intent": intent,
                    "brain": "exec", "status": "pending_approval", "tools": ["execution_task"],
                    "route": route, "orch": None}
    except Exception:
        pass  # delegação nunca deve derrubar o chat — segue pro agente

    import agent

    # 3) Cérebro AGENTE (tool-use) — caminho ÚNICO pra conversa E ação (correção
    #    19/06). Antes, "conversa"/"desconhecido" ia direto pro claude_brain.answer
    #    (cérebro de RACIOCÍNIO, persona "só penso, não ajo"): ele PROMETIA acionar
    #    a execução mas nunca chamava a ferramenta — loop de "vou pedir pra parte
    #    executora" sem nada acontecer. Agora tudo passa pelo agente, que de fato
    #    age: chama `programar` (→ executor), `buscar_conhecimento`, `pensar_profundo`
    #    (raciocínio fundo quando precisa), `lembrar_fato`, ou só conversa. O estado
    #    do projeto já entra via agent._system() (injeta briefing.estado_resumido()).
    ag = agent.respond(text, history, project_id=project_id)
    if ag is not None:
        used = ag["tools"][0] if ag.get("tools") else intent
        return {"text": ag["text"] or "Pronto, senhor.", "intent": used,
                "brain": "main", "status": "agent", "tools": ag.get("tools", []),
                "route": route, "orch": None}

    # 5) Último recurso — cérebro principal direto (Claude assinatura via
    #    orchestrator._main_brain → call_claude). Sem Ollama: se faltar, a
    #    própria call_claude devolve a mensagem clara de "sem cérebro".
    try:
        txt = orchestrator._main_brain(text, history)
    except Exception as e:
        txt = f"Estou sem cérebro disponível, senhor: {e}"
    return {"text": txt, "intent": intent, "brain": "main", "status": "llm",
            "tools": [], "route": route, "orch": None}


def _persist_messages(
    user_text: str,
    out: dict,
    project_id: str = gate.CORE_SCOPE,
    session_id: str = history_store.DEFAULT_SESSION_ID,
) -> None:
    """Dual-write das mensagens no SQLite. Nunca quebra o chat se falhar."""
    try:
        import repositories as repo
        history_store.ensure_session(project_id, session_id)
        repo.messages.add("user", user_text, source="chat", project_id=project_id, session_id=session_id)
        repo.messages.add("assistant", out.get("text", ""), brain=out.get("brain", ""),
                          intent=out.get("intent", ""), source="chat",
                          project_id=project_id, session_id=session_id)
    except Exception:
        pass


def _entry_from_brain(text: str, out: dict, start: datetime) -> dict:
    """Monta o registro padrão a partir do resultado do _brain."""
    entry = _make_entry("ok", text, out["route"],
                        {"status": out["status"], "message": out["text"]},
                        start, out.get("orch"))
    entry["response"] = out["text"]
    entry["intent"]   = out["intent"]
    entry["brain"]    = out["brain"]
    for key in ("task_id", "project_id", "approval_id"):
        if out.get(key) not in ("", None):
            entry[key] = out.get(key)
    return entry


def _get_history_messages(project_id: str | None = None, session_id: str | None = None) -> list[dict]:
    if project_id is not None or session_id is not None:
        rows = history_store.load(project_id, session_id)
        return [
            {"role": row.get("role", ""), "content": row.get("content", "")}
            for row in rows[-6:]
            if row.get("role") and row.get("content") is not None
        ]
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


# Microfone sempre-ligado (voz-sandbox/VTuber): sem isso, QUALQUER fala captada
# pelo VAD virava uma resposta falada. Portão: só processa se (a) a palavra de
# ativação apareceu nesta fala, ou (b) ainda estamos dentro da "janela de
# conversa" depois da última vez que ela apareceu — pra não exigir "Javis" antes
# de cada frase de um papo contínuo. Estado em memória (reinicia com o servidor).
_WAKE_SESSION_SECONDS = 25
_last_wake_ts: float = 0.0


@app.post("/v1/chat/completions")
async def openai_compat(req: OAIRequest):
    """Endpoint OpenAI-compatível para voz-sandbox e outros clientes."""
    global _last_wake_ts
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

    import voice_bridge as _vb
    now = time.monotonic()
    woke_now = _vb.has_wake_word(user_text)
    in_session = (now - _last_wake_ts) < _WAKE_SESSION_SECONDS
    if not (woke_now or in_session):
        # Fala captada mas não destinada ao Javis — fica em silêncio, não loga.
        return JSONResponse({
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}", "object": "chat.completion",
            "created": int(time.time()), "model": req.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": ""},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        })
    _last_wake_ts = now
    clean_text = _vb._strip_wake_word(user_text) or user_text

    if not safe_config.external_adapters_enabled():
        reply = safe_config.disabled_message(
            "external_adapters",
            safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS,
        )
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

    # Cérebro = Claude pela assinatura (decisão 18/06, tira a API paga do caminho
    # de voz também). Haiku + contexto enxuto (decisão 18/06: velocidade/leveza
    # em 1º lugar na voz). Cai pro gpt-4o-mini só se o Claude faltar.
    def _llm_direct(text: str) -> str:
        try:
            import claude_brain
            if claude_brain.available():
                ctx = ""
                try:
                    import agent as _agent
                    ctx = _agent._history_context(_get_history_messages(), limit=2)
                except Exception:
                    pass
                resp = claude_brain.answer(text, ctx, model=claude_brain._VOICE_MODEL)
                if resp and resp.strip():
                    return resp
        except Exception:
            pass
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

    reply = await run_in_threadpool(_llm_direct, clean_text)

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
    project_id: str = ""
    approved: bool = False
    approval_id: int | None = None


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
async def train_youtube(
    req: TrainRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Extrai transcrição de um vídeo YouTube e salva na base de conhecimento do agente."""
    blocked = _local_auth_gate(x_javes_local_token, "train.youtube")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(req.project_id, scope=gate.CORE_SCOPE)
    if blocked:
        return _gate_json(blocked)
    if not safe_config.external_adapters_enabled():
        return _disabled_json("external_adapters", safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS)
    blocked = gate.require_persisted_approval(
        "train.youtube",
        approval_id=req.approval_id,
        route="/train/youtube",
        project_id=req.project_id,
        risk_level="high",
        approved=req.approved,
        metadata={"agent": req.agent, "url": req.url},
    )
    if blocked:
        return _gate_json(blocked)
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


@app.get("/treinamento/status")
async def treinamento_status():
    """Estado real da pasta _treinamento/ — quanto material por área já foi
    despejado (_entrada) e quanto já foi resumido (_resumos, vai pro RAG)."""
    import trend_scout
    return JSONResponse({"areas": trend_scout.all_status()})


@app.post("/treinamento/scout/{area}")
async def treinamento_scout_area(area: str):
    """Esquadrão de estudo de uma área: busca vídeo (YouTube) + repo (GitHub)
    relevantes e joga em _treinamento/<area>/_entrada/ (sem duplicar)."""
    from starlette.concurrency import run_in_threadpool
    import trend_scout
    result = await run_in_threadpool(trend_scout.scout_area, area)
    return JSONResponse(result)


@app.post("/treinamento/scout-all")
async def treinamento_scout_all():
    """Roda o esquadrão de estudo de todas as áreas de uma vez."""
    from starlette.concurrency import run_in_threadpool
    import trend_scout
    results = await run_in_threadpool(trend_scout.scout_all)
    return JSONResponse({"results": results})


@app.post("/treinamento/resumir/{area}")
async def treinamento_resumir(area: str):
    """Resume com o Claude (assinatura) os arquivos pendentes de _entrada → _resumos
    e reindexa o RAG. Fecha o ciclo de treino sem NotebookLM manual."""
    if not safe_config.claude_exec_enabled():
        return _disabled_json("claude_exec", safe_config.JAVIS_ENABLE_CLAUDE_EXEC)
    import resumir_treino
    out = await run_in_threadpool(resumir_treino.resumir_area, area)
    return JSONResponse(out)


class PulsoRequest(BaseModel):
    topico: str


@app.post("/pulso")
async def pulso_mercado_route(req: PulsoRequest):
    """Pulso de mercado: o que estão falando sobre o tópico (Reddit/YouTube/HN/GitHub)
    sintetizado pelo Claude. Fontes grátis, sem API paga."""
    if not safe_config.external_adapters_enabled():
        return _disabled_json("external_adapters", safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS)
    import pulso_mercado
    out = await run_in_threadpool(pulso_mercado.pulso, req.topico)
    return JSONResponse(out)


@app.get("/browser/status")
async def browser_status():
    """Disponibilidade da capacidade de operar o navegador (browser-use)."""
    import browser_agent
    return JSONResponse({"available": browser_agent.available()})


def _browser_task_hash(task: str, project_id: str) -> str:
    """Hash canônico da tarefa de navegador aprovada. Normaliza espaços para
    que só diferenças reais de conteúdo invalidem o approval, e inclui o
    project_id para a aprovação nunca vazar de um projeto para outro."""
    import hashlib

    normalized = " ".join((task or "").split())
    scope = (project_id or "").strip() or gate.CORE_SCOPE
    canonical = json.dumps({"action": "browser.run", "project_id": scope, "task": normalized},
                           ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _mcp_call_hash(server_id: str, tool: str, arguments: dict | None, project_id: str) -> str:
    """Hash da chamada MCP: servidor + tool + args. Garante que trocar qualquer um
    invalida o approval. Inclui project_id pra não vazar entre escopos."""
    import hashlib

    scope = (project_id or "").strip() or gate.CORE_SCOPE
    canonical = json.dumps(
        {"action": "mcp.call", "project_id": scope, "server_id": server_id,
         "tool": tool, "arguments": arguments or {}},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class BrowserRequest(BaseModel):
    task: str
    project_id: str = ""
    approved: bool = False
    approval_id: int | None = None


@app.post("/browser/run")
async def browser_run(
    req: BrowserRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Opera o navegador (browser-use) para realizar a tarefa. Ação em site real =
    risco — o caller deve usar com aprovação. Precisa de modelo com VISÃO
    (BROWSER_USE_MODEL) + OPENROUTER_API_KEY."""
    blocked = _local_auth_gate(x_javes_local_token, "browser.run")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(req.project_id, scope=gate.CORE_SCOPE)
    if blocked:
        return _gate_json(blocked)
    if not safe_config.browser_enabled():
        return _disabled_json("browser", safe_config.JAVIS_ENABLE_BROWSER)
    # Amarra a aprovação à tarefa exata: o approval só vale para a task que o
    # humano leu e aprovou. Trocar o texto invalida o approval (spec_hash-style).
    task_hash = _browser_task_hash(req.task, req.project_id)
    blocked = gate.require_persisted_approval(
        "browser.run",
        approval_id=req.approval_id,
        route="/browser/run",
        project_id=req.project_id,
        risk_level="high",
        approved=req.approved,
        metadata={"task": req.task, "task_hash": task_hash},
        payload_hash=task_hash,
    )
    if blocked:
        return _gate_json(blocked)
    import browser_agent
    out = await browser_agent.run_task(req.task)
    return JSONResponse(out)


@app.get("/missions")
async def get_missions():
    """Missões reais: derivadas do backlog do Codex (_data/codex_backlog.md)."""
    import mission_board
    missions = mission_board.get_missions()
    return JSONResponse({"missions": [
        {k: v for k, v in m.items() if k != "nodes"} for m in missions
    ]})


@app.get("/missions/{mission_id}/nodes")
async def get_mission_nodes(mission_id: str):
    """Tarefas (nodes) de uma missão específica, pra desenhar o canvas."""
    import mission_board
    return JSONResponse({"nodes": mission_board.get_mission_nodes(mission_id)})


class TaskDoneRequest(BaseModel):
    done: bool


@app.post("/missions/{mission_id}/nodes/{node_id}/done")
async def set_mission_task_done(
    mission_id: str,
    node_id: str,
    req: TaskDoneRequest,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Marca/desmarca uma tarefa real no backlog (drag-and-drop do Quadro).
    Missões sintéticas (calculadas, sem checkbox) devolvem 404."""
    blocked = _local_auth_gate(x_javes_local_token, "missions.done")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_local_actions("missions.done")
    if blocked:
        return _gate_json(blocked)
    import mission_board
    ok = mission_board.set_task_done(mission_id, node_id, req.done)
    if not ok:
        return JSONResponse(
            {"ok": False, "message": "Tarefa não encontrada ou não editável (missão calculada)."},
            status_code=404,
        )
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# UI / Command Center — rotas READ-ONLY (Fase 3). Aditivas: agregam o que já
# existe (ui_state + telemetry_adapter), não tocam no _brain nem em nada acima.
# ---------------------------------------------------------------------------
@app.get("/ui/state")
async def ui_full_state():
    import ui_state
    return JSONResponse(ui_state.full_state())


@app.get("/ui/projects")
async def ui_projects():
    import ui_state
    return JSONResponse({"projects": ui_state.get_projects()})


@app.get("/ui/squads/{project_id}")
async def ui_squads(project_id: str):
    import ui_state
    return JSONResponse({"squads": ui_state.get_squads(project_id)})


@app.get("/ui/agents")
async def ui_agents():
    import ui_state
    return JSONResponse({"agents": ui_state.get_agents()})


@app.get("/ui/skills")
async def ui_skills():
    import ui_state
    return JSONResponse({"skills": ui_state.get_skills()})


@app.get("/ui/scripts")
async def ui_scripts():
    import ui_state
    return JSONResponse({"scripts": ui_state.get_scripts()})


@app.get("/ui/mcp")
async def ui_mcp():
    """Servidores MCP configurados que o Javis consome."""
    import mcp_client
    return JSONResponse({"servers": mcp_client.list_servers()})


@app.get("/mcp/{server_id}/tools")
async def mcp_tools(server_id: str):
    """Conecta no servidor MCP e lista as tools dele."""
    if not safe_config.mcp_enabled():
        return _disabled_json("mcp", safe_config.JAVIS_ENABLE_MCP)
    import mcp_client
    return JSONResponse(await mcp_client.list_tools(server_id))


class MCPCallRequestWithAuth(BaseModel):
    tool: str
    arguments: dict = {}
    project_id: str = ""
    approved: bool = False
    approval_id: int | None = None


@app.post("/mcp/{server_id}/call")
async def mcp_call(
    server_id: str,
    req: MCPCallRequestWithAuth,
    x_javes_local_token: str | None = Header(None, alias=gate.LOCAL_TOKEN_HEADER),
):
    """Chama uma tool de um servidor MCP. MCP = tools remotos = risco → gate completo."""
    blocked = _local_auth_gate(x_javes_local_token, "mcp.call")
    if blocked:
        return _gate_json(blocked)
    blocked = gate.require_project_scope(req.project_id, scope=gate.CORE_SCOPE)
    if blocked:
        return _gate_json(blocked)
    if not safe_config.mcp_enabled():
        return _disabled_json("mcp", safe_config.JAVIS_ENABLE_MCP)
    # Amarra a aprovação ao servidor + tool + args: o approval vale só pra exatamente
    # isso que o humano aprovou, não pra qualquer tool no servidor.
    call_hash = _mcp_call_hash(server_id, req.tool, req.arguments, req.project_id)
    blocked = gate.require_persisted_approval(
        "mcp.call",
        approval_id=req.approval_id,
        route=f"/mcp/{server_id}/call",
        project_id=req.project_id,
        risk_level="high",
        approved=req.approved,
        metadata={"server_id": server_id, "tool": req.tool, "call_hash": call_hash},
        payload_hash=call_hash,
    )
    if blocked:
        return _gate_json(blocked)
    import mcp_client
    return JSONResponse(await mcp_client.call_tool(server_id, req.tool, req.arguments))


@app.get("/ui/integrations")
async def ui_integrations():
    """Status REAL dos conectores (read-only, não dispara nada externo)."""
    import os
    try:
        import integrations
        av = integrations.available()
    except Exception:
        av = {}
    av["whatsapp"] = bool(os.environ.get("OPENWA_URL") or os.environ.get("WHATSAPP_URL"))
    av["openai"] = bool(os.environ.get("OPENAI_API_KEY"))
    av["claude_code"] = __import__("claude_exec").available()
    return JSONResponse({"integrations": av})


@app.get("/ui/project/{project_id}")
async def ui_project_manifest(project_id: str):
    import ui_state
    return JSONResponse(ui_state.get_project_manifest(project_id) or {})


@app.get("/ui/telemetry")
async def ui_telemetry():
    import telemetry_adapter
    return JSONResponse(telemetry_adapter.full())


if __name__ == "__main__":
    import uvicorn
    print("\n  Javis v2 — http://localhost:8000\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
