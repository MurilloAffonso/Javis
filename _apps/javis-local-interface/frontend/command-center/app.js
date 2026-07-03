/* JAVIS Command Center — estrutura inspirada no AIOS Core Platform (sem copiar
   identidade). Dados reais do backend (server.py :8000) com fallback aos JSONs.
   Chat e Tarefas conversam de verdade com o /chat (_brain). */

// --- Módulos de tela (extraídos de app.js; migração incremental p/ ES Modules) ---
import { viewVempassear } from "./js/views/vempassear.js";
import { viewOperacao } from "./js/views/operacao.js";
import { viewChat } from "./js/views/chat.js";
import { viewTreino } from "./js/views/treino.js";
import { viewConclave } from "./js/views/conclave.js";
import { viewMissoes } from "./js/views/missoes.js";
import { viewRotina } from "./js/views/rotina.js";
import { viewTarefas } from "./js/views/tarefas.js";
import { viewPainel } from "./js/views/painel.js";
import { viewConfig } from "./js/views/config.js";
import { viewExec } from "./js/views/exec.js";
// Helpers do núcleo que as telas-módulo consomem (live bindings):
export { _esc, h, $, state, BACKEND, tryJson, renderCanvas, renderRightPanel, setView, opToast, opSend, opEsc, confirmStrong, activeAgent, pct, sc, projName, tele };

const DATA_BASE = "../../data/";
const BACKEND = (location.port === "8000") ? "/" : "http://localhost:8000/";

const ICONS = {
  chat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  world: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></svg>',
  tasks: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  panel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>',
  config: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
  train: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1 3 2 6 2s6-1 6-2v-5"/></svg>',
  exec: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
  board: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="12" rx="1"/><rect x="17" y="3" width="4" height="15" rx="1"/></svg>',
  conclave: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9a2 2 0 0 1-2 2H6l-4 3V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-3h-6a2 2 0 0 1-2-2v-1"/></svg>',
  missoes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/></svg>',
  rotina: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
  vp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12s3-4 9-4 9 4 9 4M3 17s3-3 9-3 9 3 9 3"/><circle cx="12" cy="6" r="2"/></svg>',
  acoes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>',
};

const NAV = [
  { id: "chat",    label: "Chat",    icon: ICONS.chat },
  { id: "operacao",label: "Operação", icon: ICONS.board },
  { id: "conclave",label: "Conclave", icon: ICONS.conclave },
  { id: "missoes", label: "Missões", icon: ICONS.missoes },
  { id: "exec",    label: "Execução", icon: ICONS.exec },
  { id: "tarefas", label: "Tarefas", icon: ICONS.tasks },
  { id: "painel",  label: "Painel",  icon: ICONS.panel },
  { id: "treino",  label: "Treino",  icon: ICONS.train },
  { id: "rotina",  label: "Rotina",  icon: ICONS.rotina },
  { id: "vempassear", label: "Vem Passear", icon: ICONS.vp },
  { id: "config",  label: "Config",  icon: ICONS.config },
];


const STATUS_CLASS = { ativo:"ok", ativa:"ok", online:"ok", concluido:"ok", executando:"run", run:"run", aguardando:"wait", wait:"wait", externo:"externo", warn:"warn", erro:"err", err:"err" };
const sc = (s) => STATUS_CLASS[(s || "").toLowerCase()] || "wait";
const pct = (id) => 70 + ([...String(id)].reduce((a, c) => a + c.charCodeAt(0), 0) % 27); // 70..96 estável

const state = {
  projects: [], squads: [], agents: [], skills: [], scripts: [], manifests: {}, approvals: [],
  integrations: {}, runnable: [], training: [], mcp: [],
  telemetry: null, online: false,
  view: "chat", q: "",
  activeAgentId: null, rpTab: "status",
  lastBrain: null, lastTools: null,
  chats: {}, // por agente: [{role, text}]
  activeProjectId: "vempassear",
  cfgTab: "memorias",
  useTts: false, useConclave: false,
};

const $ = (id) => document.getElementById(id);
const h = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };

// ---------- Dados ----------
async function tryJson(url, opts) { const r = await fetch(url, opts); if (!r.ok) throw new Error(r.status); return r.json(); }

async function loadData() {
  try {
    const st = await tryJson(BACKEND + "ui/state");
    state.projects = st.projects || []; state.squads = st.squads || [];
    state.agents = st.agents || []; state.skills = st.skills || []; state.online = true;
    try { state.manifests.vempassear = await tryJson(BACKEND + "ui/project/vempassear"); } catch (_) {}
    try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); } catch (_) {}
    try { state.approvals = (await tryJson(BACKEND + "approvals/pending")).approvals || []; } catch (_) {}
    try { state.scripts = (await tryJson(BACKEND + "ui/scripts")).scripts || []; } catch (_) {}
    try { state.integrations = (await tryJson(BACKEND + "ui/integrations")).integrations || {}; } catch (_) {}
    try { state.runnable = (await tryJson(BACKEND + "agents")).agents || []; } catch (_) {}
    try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; } catch (_) {}
    try { state.mcp = (await tryJson(BACKEND + "ui/mcp")).servers || []; } catch (_) {}
    return true;
  } catch (_) {}
  try {
    const [p, s, a, k] = await Promise.all([
      tryJson(DATA_BASE + "ui/project_registry.json"),
      tryJson(DATA_BASE + "ui/squad_registry.json"),
      tryJson(DATA_BASE + "ui/agent_registry.json"),
      tryJson(DATA_BASE + "ui/skill_registry.json").catch(() => ({ skills: [] })),
    ]);
    state.projects = p.projects || []; state.squads = s.squads || [];
    state.agents = a.agents || []; state.skills = k.skills || []; state.online = false;
    try { state.scripts = (await tryJson(DATA_BASE + "ui/scripts_registry.json")).scripts || []; } catch (_) {}
    try { state.manifests.vempassear = await tryJson(DATA_BASE + "projects/vempassear.json"); } catch (_) {}
    return true;
  } catch (e) { return false; }
}

function tele() {
  if (state.telemetry) {
    const m = state.telemetry.metrics || {}, last = m.last || {};
    return {
      status: state.telemetry.status || [],
      logs: (state.telemetry.events || []).map((e) => ({ t: e.t || "", txt: `<b>${e.intent || e.source || "evento"}</b> ${e.message || ""}` })),
      metrics: { intent: last.intent || "—", brain: state.lastBrain || last.brain || "—", tools: state.lastTools || "—",
        risk: last.risk_level || "—", approval: String(last.requires_approval ?? "—"),
        tokens_in: m.tokens_in || 0, tokens_out: m.tokens_out || 0, total: m.tokens_total || 0, calls: m.calls || 0, tempo: (m.avg_latency_ms || 0) + "ms" },
    };
  }
  return { status: [{ label: "Backend", val: "offline", cls: "wait" }], logs: [],
    metrics: { intent: "—", brain: "—", tools: "—", risk: "—", approval: "—", tokens_in: 0, tokens_out: 0, total: 0, calls: 0, tempo: "—" } };
}

const projName = (id) => (state.projects.find((p) => p.id === id) || {}).nome || id;
const activeAgent = () => state.agents.find((a) => a.id === state.activeAgentId) || state.agents.find((a) => a.tipo === "orquestrador") || state.agents[0] || {};

// ---------- Sidebar ----------
function matchQ(txt) { return !state.q || (txt || "").toLowerCase().includes(state.q.toLowerCase()); }

function renderSidebar() {
  // Menu
  $("nav-menu").innerHTML = "";
  NAV.forEach((n) => {
    const el = h(`<div class="nav-tile ${n.id === state.view ? "active" : ""}">${n.icon}<span>${n.label}</span></div>`);
    el.onclick = () => setView(n.id);
    $("nav-menu").appendChild(el);
  });

  // Squads agrupados por projeto (categoria)
  const box = $("nav-squads"); box.innerHTML = "";
  const byProj = {};
  state.squads.filter((s) => matchQ(s.nome)).forEach((s) => { (byProj[s.projeto] = byProj[s.projeto] || []).push(s); });
  Object.entries(byProj).forEach(([pid, squads]) => {
    box.appendChild(h(`<div class="tree-head">${projName(pid)}<span class="tg-count">${squads.length}</span></div>`));
    squads.forEach((s) => {
      const it = h(`<div class="tree-item"><span class="dot ${s.executavel ? "ok" : "wait"}"></span>${s.nome}<span class="ti-count">${(s.agentes || []).length}</span></div>`);
      it.onclick = () => { state.activeProjectId = pid; setView("painel"); };
      box.appendChild(it);
    });
  });

  // Agentes agrupados por PROJETO (Javis Core / Javis Dev / Vem Passear)
  fillAgentGroup("nav-orchestrators", state.agents.filter((a) => a.projeto === "geral" && matchQ(a.nome)));
  fillAgentGroup("nav-masters", state.agents.filter((a) => a.projeto === "javis-dev" && matchQ(a.nome)));
  fillAgentGroup("nav-specialists", state.agents.filter((a) => a.projeto === "vempassear" && matchQ(a.nome)));
}

function fillAgentGroup(boxId, list) {
  const box = $(boxId); box.innerHTML = "";
  if (!list.length) { box.appendChild(h(`<div class="li-sub" style="padding:6px 10px">—</div>`)); return; }
  list.forEach((a) => {
    const it = h(`<div class="list-item ${a.id === state.activeAgentId ? "active" : ""}"><span class="dot ${sc(a.status)}"></span><div class="li-main"><div class="li-name">${a.nome}</div><div class="li-sub">${(a.tags || []).join(" · ") || a.tipo}</div></div></div>`);
    it.onclick = () => { state.activeAgentId = a.id; setView("chat"); };
    box.appendChild(it);
  });
}

// ---------- Tabs / view ----------
const TITLES = { chat: "Chat", operacao: "Operação · Quadro & Aprovações", conclave: "Conclave · Debate de Agentes", missoes: "Missões", tarefas: "Orquestrador de Tarefas", painel: "Painel", treino: "Treinamento", rotina: "Rotina · Briefing, Histórico & Lembretes", vempassear: "Projeto conectado · Vem Passear Jampa", exec: "Execução em Tempo Real", config: "Configurações" };
function setView(v) {
  if (window._execPollTimer) { clearInterval(window._execPollTimer); window._execPollTimer = null; }
  state.view = v; renderSidebar(); renderCanvas(); renderRightPanel();
}
function renderCanvas() {
  // Operação da agência não expõe painel técnico (tokens/LLM/logs do Javes)
  document.querySelector(".app")?.classList.toggle("vp-mode", state.view === "vempassear");
  const body = $("canvas-body"); body.innerHTML = "";
  if ((state.q || "").trim()) {
    $("canvas-title").textContent = `Busca: "${state.q}"`;
    return viewSearch(body);
  }
  $("canvas-title").textContent = TITLES[state.view] || "";
  ({ chat: viewChat, operacao: viewOperacao, conclave: viewConclave, missoes: viewMissoes, exec: viewExec, tarefas: viewTarefas, painel: viewPainel, treino: viewTreino, rotina: viewRotina, vempassear: viewVempassear, config: viewConfig }[state.view] || viewChat)(body);
}

function viewSearch(body) {
  const q = state.q.toLowerCase();
  const m = (t) => (t || "").toLowerCase().includes(q);
  const ag = state.agents.filter((a) => m(a.nome) || m(a.descricao) || (a.tags || []).some(m));
  const sq = state.squads.filter((s) => m(s.nome) || m(s.missao));
  const sk = state.skills.filter((s) => m(s.nome) || m(s.descricao));
  const scr = state.scripts.filter((s) => m(s.arquivo) || m(s.proposito));
  const total = ag.length + sq.length + sk.length + scr.length;
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">${total} resultado(s) local(is) para <b>${_esc(state.q)}</b></div>`));
  if (!total) body.appendChild(h(`<div class="card-sub">Nenhum agente/squad/skill/script bate. Buscando na base de conhecimento…</div>`));

  if (ag.length) {
    body.appendChild(h(`<div class="section-h">Agentes (${ag.length})</div>`));
    const g = h(`<div class="grid cols-3" style="margin-bottom:18px"></div>`);
    ag.forEach((a) => {
      const c = h(`<div class="card" style="cursor:pointer"><div class="card-head"><div class="card-icon">${(a.nome || "?")[0]}</div><div><div class="card-title">${a.nome}</div><div class="card-sub">${a.tipo}</div></div></div><div class="card-desc">${a.descricao || ""}</div></div>`);
      c.onclick = () => { state.q = ""; $("tb-search").value = ""; $("sb-search").value = ""; state.activeAgentId = a.id; setView("chat"); };
      g.appendChild(c);
    });
    body.appendChild(g);
  }
  const lists = [["Squads", sq, (s) => `${s.nome} — ${s.missao || ""}`], ["Skills", sk, (s) => `${s.nome} (${s.categoria})`], ["Scripts", scr, (s) => `${s.arquivo} — ${s.proposito || ""}`]];
  lists.forEach(([title, arr, fmt]) => {
    if (!arr.length) return;
    body.appendChild(h(`<div class="section-h">${title} (${arr.length})</div>`));
    const box = h(`<div style="margin-bottom:18px"></div>`);
    arr.forEach((x) => box.appendChild(h(`<div class="status-row"><span class="sr-label">${fmt(x)}</span></div>`)));
    body.appendChild(box);
  });

  // Busca semântica no RAG (GET /knowledge/search) — assíncrona, memórias/vaults.
  const ragQ = state.q;
  body.appendChild(h(`<div class="section-h">🔎 Base de conhecimento (RAG)</div>`));
  const ragBox = h(`<div id="rag-box"><div class="card-sub">Buscando na base semântica… (pode demorar na 1ª vez — indexando)</div></div>`);
  body.appendChild(ragBox);
  if (!state.online) { ragBox.innerHTML = `<div class="card-sub">Backend offline — RAG indisponível.</div>`; return; }
  tryJson(BACKEND + "knowledge/search?q=" + encodeURIComponent(ragQ)).then((d) => {
    if (state.q !== ragQ || !document.getElementById("rag-box")) return; // usuário mudou a busca
    const hits = (d.hits || []).filter((x) => (x.score || 0) > 0.2);
    if (!hits.length) { ragBox.innerHTML = `<div class="op-empty">Nada relevante na base para essa busca.</div>`; return; }
    ragBox.innerHTML = "";
    hits.forEach((hit) => {
      const card = h(`<div class="card" style="margin-bottom:10px"><div class="card-sub" style="margin-bottom:4px">📄 <b class="rag-path"></b> · ${Math.round((hit.score || 0) * 100)}% relevante</div><div class="card-desc rag-chunk" style="white-space:pre-wrap"></div></div>`);
      card.querySelector(".rag-path").textContent = hit.path || "(fonte)";
      card.querySelector(".rag-chunk").textContent = (hit.chunk || "").slice(0, 600);
      ragBox.appendChild(card);
    });
  }).catch(() => { if (document.getElementById("rag-box")) ragBox.innerHTML = `<div class="card-sub">Não consegui buscar na base agora.</div>`; });
}

// ---------- Chat (por agente) ----------
// Escape seguro para qualquer texto vindo do backend antes de ir pro HTML.
const opEsc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// fetch que NÃO lança em status de erro — devolve {status, ok, data} pra tratar 409 etc.
async function opSend(url, opts) {
  const r = await fetch(url, opts);
  let data = {};
  try { data = await r.json(); } catch (_) {}
  return { status: r.status, ok: r.ok, data };
}

function opToast(msg, kind) {
  let host = $("op-toast");
  if (!host) { host = h(`<div id="op-toast" class="op-toast"></div>`); document.body.appendChild(host); }
  const t = h(`<div class="op-toast-item ${kind || "info"}">${opEsc(msg)}</div>`);
  host.appendChild(t);
  setTimeout(() => t.classList.add("show"), 10);
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 250); }, 3200);
}

// Confirmação reutilizável para ações de escrita: mostra endpoint/alvo/efeito/risco
// e executa opts.onConfirm() com UM clique em Confirmar. (2026-07-03: removida a
// digitação da frase — decisão de UX do Murillo.) Cancelar sempre disponível.
// opts.phrase é aceito e ignorado (compatibilidade com chamadas antigas).
const CS_RISK = {
  leitura: { label: "Leitura", cls: "ok" }, leve: { label: "Escrita leve", cls: "run" },
  op: { label: "Escrita operacional", cls: "warn" }, pesado: { label: "Pesado", cls: "warn" },
  alto: { label: "Alto risco", cls: "err" },
};
function confirmStrong(opts) {
  const risk = CS_RISK[opts.risk] || CS_RISK.op;
  const ov = h(`<div class="cs-overlay">
    <div class="cs-modal">
      <div class="cs-h">⚠️ Confirmar — esta ação altera dados</div>
      <div class="cs-action"></div>
      <div class="cs-grid">
        <div><span class="cs-k">Endpoint</span> <code>${_esc((opts.method || "POST") + " " + (opts.endpoint || ""))}</code></div>
        <div><span class="cs-k">Alvo</span> <span class="cs-target"></span></div>
        <div><span class="cs-k">Status atual</span> <span class="cs-before"></span></div>
        <div><span class="cs-k">Efeito</span> <span class="cs-after"></span></div>
        <div><span class="cs-k">Risco</span> <span class="badge ${risk.cls}"><span class="dot ${risk.cls}"></span>${_esc(risk.label)}</span></div>
      </div>
      <div class="cs-actions">
        <button class="op-btn ok cs-go">✔ Confirmar</button>
        <button class="op-btn ghost cs-cancel">Cancelar</button>
      </div>
      <div class="cs-fb"></div>
    </div>
  </div>`);
  ov.querySelector(".cs-action").textContent = opts.title || "Ação de escrita";
  ov.querySelector(".cs-target").textContent = opts.target || "—";
  ov.querySelector(".cs-before").textContent = opts.before || "—";
  ov.querySelector(".cs-after").textContent = opts.after || "—";
  const go = ov.querySelector(".cs-go");
  const close = () => ov.remove();
  ov.querySelector(".cs-cancel").onclick = close;
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  go.onclick = async () => {
    go.disabled = true; go.textContent = "Executando…";
    try { await opts.onConfirm(); } catch (_) {} finally { close(); }
  };
  document.body.appendChild(ov);
  setTimeout(() => go.focus(), 30);
}

// ---------- Conclave (Debate de Agentes) — POST /debate ----------
function renderRightPanel() {
  const tabs = [{ id: "status", label: "Status" }, { id: "historico", label: "Histórico" }, { id: "metricas", label: "Métricas" }];
  $("rp-tabs").innerHTML = "";
  tabs.forEach((t) => { const el = h(`<div class="rp-tab ${t.id === state.rpTab ? "active" : ""}">${t.label}</div>`); el.onclick = () => { state.rpTab = t.id; renderRightPanel(); }; $("rp-tabs").appendChild(el); });
  const body = $("rp-body"); body.innerHTML = "";
  ({ status: rpStatus, historico: rpHist, metricas: rpMet }[state.rpTab] || rpStatus)(body);
}

function rpStatus(body) {
  const T = tele();
  // Agente selecionado
  if (state.view === "chat") {
    const a = activeAgent();
    body.appendChild(h(`<div class="section-h">Agente Selecionado</div>`));
    body.appendChild(h(`<div class="agent-sel"><div class="as-av">${(a.nome || "?")[0]}</div><div><div style="font-weight:600">${a.nome || ""}</div><div class="card-sub">${a.tipo || ""} ${(a.tags || []).length ? "· " + a.tags.join(" ") : ""}</div></div></div>`));
  }
  body.appendChild(h(`<div class="status-row"><span class="sr-label">Fonte</span><span class="sr-val badge ${state.online ? "ok" : "wait"}"><span class="dot ${state.online ? "ok" : "wait"}"></span>${state.online ? "backend ao vivo" : "mock"}</span></div>`));
  body.appendChild(h(`<div class="section-h" style="margin-top:14px">Status LLM</div>`));
  T.status.forEach((s) => body.appendChild(h(`<div class="status-row"><span class="sr-label">${s.label}</span><span class="sr-val badge ${s.cls}"><span class="dot ${s.cls}"></span>${s.val}</span></div>`)));
  // Uso de tokens
  body.appendChild(h(`<div class="section-h" style="margin-top:14px">Uso de Tokens</div>`));
  const g = h(`<div class="grid" style="grid-template-columns:1fr 1fr;gap:8px"></div>`);
  [["Input", T.metrics.tokens_in], ["Output", T.metrics.tokens_out], ["Total", T.metrics.total], ["Chamadas", T.metrics.calls]].forEach(([k, v]) => g.appendChild(h(`<div class="kpi"><div class="kpi-label">${k}</div><div class="kpi-value" style="font-size:18px">${v}</div></div>`)));
  body.appendChild(g);
  // Aprovações
  body.appendChild(h(`<div class="section-h" style="margin-top:14px">Aprovações pendentes</div>`));
  const aps = state.online ? state.approvals : [];
  if (!aps.length) { body.appendChild(h(`<div class="card-sub">Nenhuma aprovação pendente.</div>`)); }
  aps.forEach((a) => {
    const ap = h(`<div class="approval"><div class="ap-title">${a.subject || "—"}</div><div class="card-sub">#${a.id} · ${a.kind || "gate"}${a.agent ? " · " + a.agent : ""}</div><div class="ap-actions"><button class="btn ok">Aprovar</button><button class="btn no">Recusar</button></div></div>`);
    const [ok, no] = ap.querySelectorAll("button");
    ok.onclick = () => decideApproval(a, "approved", ap); no.onclick = () => decideApproval(a, "rejected", ap);
    body.appendChild(ap);
  });
}

async function decideApproval(a, decision, el) {
  const act = el.querySelector(".ap-actions"); act.innerHTML = `<span class="card-sub">Enviando...</span>`;
  try {
    const out = await tryJson(`${BACKEND}approvals/${a.id}/decide`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, note: "via Command Center" }) });
    if (!out.ok) throw new Error(out.error || "erro");
    try { state.approvals = (await tryJson(`${BACKEND}approvals/pending`)).approvals || []; } catch (_) {}
    renderRightPanel();
  } catch (e) { act.innerHTML = `<span class="card-sub" style="color:var(--err)">Falhou: ${e.message}</span>`; }
}

function rpHist(body) {
  body.appendChild(h(`<div class="section-h">Eventos recentes</div>`));
  const logs = tele().logs;
  if (!logs.length) { body.appendChild(h(`<div class="card-sub">Sem eventos.</div>`)); return; }
  logs.forEach((l) => body.appendChild(h(`<div class="log-item"><span class="lt">${l.t}</span> · ${l.txt}</div>`)));
}

function rpMet(body) {
  const m = tele().metrics;
  body.appendChild(h(`<div class="section-h">Última execução</div>`));
  [["Intent", m.intent], ["Brain", m.brain], ["Tools", m.tools], ["Risk", m.risk], ["Aprovação", m.approval], ["Tempo médio", m.tempo]].forEach(([k, v]) =>
    body.appendChild(h(`<div class="status-row"><span class="sr-label">${k}</span><span class="sr-val">${v}</span></div>`)));
  body.appendChild(h(`<div class="section-h" style="margin-top:14px">Tokens</div>`));
  const g = h(`<div class="grid" style="grid-template-columns:1fr 1fr;gap:8px"></div>`);
  [["Input", m.tokens_in], ["Output", m.tokens_out], ["Total", m.total], ["Chamadas", m.calls]].forEach(([k, v]) => g.appendChild(h(`<div class="kpi"><div class="kpi-label">${k}</div><div class="kpi-value" style="font-size:18px">${v}</div></div>`)));
  body.appendChild(g);
}

// ---------- Bootstrap ----------
// Escape HTML genérico do núcleo (exportado; vivia no bloco de voz antes da modularização).
function _esc(s) { return String(s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

function renderAll() { renderSidebar(); renderCanvas(); renderRightPanel(); }

["sb-search", "tb-search"].forEach((id) => {
  document.addEventListener("input", (e) => { if (e.target.id === id) { state.q = e.target.value; renderSidebar(); renderCanvas(); } });
});

(async function init() {
  const ok = await loadData();
  if (!ok) { $("canvas-body").innerHTML = `<div class="banner">⚠️ Sirva por HTTP: <code>python -m http.server 8080</code> e abra <code>http://localhost:8080/frontend/command-center/index.html</code>, ou rode o backend em :8000.</div>`; return; }
  renderAll();
})();
