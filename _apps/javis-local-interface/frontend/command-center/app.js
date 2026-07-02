/* JAVIS Command Center — estrutura inspirada no AIOS Core Platform (sem copiar
   identidade). Dados reais do backend (server.py :8000) com fallback aos JSONs.
   Chat e Tarefas conversam de verdade com o /chat (_brain). */

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
  { id: "world",   label: "World",   icon: ICONS.world },
  { id: "tarefas", label: "Tarefas", icon: ICONS.tasks },
  { id: "painel",  label: "Painel",  icon: ICONS.panel },
  { id: "treino",  label: "Treino",  icon: ICONS.train },
  { id: "rotina",  label: "Rotina",  icon: ICONS.rotina },
  { id: "vempassear", label: "Vem Passear", icon: ICONS.vp },
  { id: "acoes",   label: "Ações",   icon: ICONS.acoes },
  { id: "config",  label: "Config",  icon: ICONS.config },
];

const SECTORS = ["Core", "Projetos", "Marketing", "Vendas", "Conteúdo", "Dados", "Desenvolvimento", "Operação", "Automações"];

const CMD_SUGGEST = [
  { name: "⚡ nova-tarefa", desc: "Orquestrar uma demanda do zero" },
  { name: "📊 analisar", desc: "Analisar dados e gerar insights" },
  { name: "💡 gerar-ideias", desc: "Sugestões baseadas em contexto" },
  { name: "✍️ criar-conteúdo", desc: "Produzir copy / post / roteiro" },
];

const WORKFLOW_NODES = [
  { name: "Usuário", type: "input", status: "ok" },
  { name: "Orquestrador", type: "orquestrador", status: "ok" },
  { name: "Classificador", type: "router", status: "ok" },
  { name: "Projeto Ativo", type: "contexto", status: "ok" },
  { name: "Squad", type: "squad", status: "wait" },
  { name: "Agente", type: "agente", status: "run" },
  { name: "Tool", type: "ferramenta", status: "wait" },
  { name: "Aprovação", type: "gate", status: "warn" },
  { name: "Output", type: "output", status: "wait" },
];

const WORKFLOW_LIST = [
  { nome: "Campanha Multi-Squad", desc: "Estratégia, copywriting, design e revisão final", steps: 4 },
  { nome: "Lançamento de Produto", desc: "Pesquisa, conteúdo, design e go-to-market", steps: 5 },
  { nome: "Conteúdo Rápido", desc: "Planejamento, criação e revisão", steps: 3 },
];

const CFG_MENU = [
  { id: "categorias", t: "Categorias & Squads", d: "Organize squads em categorias" },
  { id: "memorias", t: "Memórias", d: "Knowledge por agente" },
  { id: "scripts", t: "Scripts", d: "Catálogo do backend" },
  { id: "integracoes", t: "Integrações", d: "Conectores externos" },
  { id: "mcp", t: "MCP", d: "Tools do ecossistema MCP" },
  { id: "workflows", t: "Workflows", d: "Fluxos de trabalho" },
  { id: "perfil", t: "Perfil", d: "Informações da conta" },
  { id: "apikeys", t: "API Keys", d: "Chaves dos provedores" },
  { id: "aparencia", t: "Aparência", d: "Tema e personalização" },
  { id: "sobre", t: "Sobre", d: "Informações do sistema" },
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
const TITLES = { chat: "Chat", operacao: "Operação · Quadro & Aprovações", conclave: "Conclave · Debate de Agentes", missoes: "Missões", acoes: "Central de Ações Seguras", world: "Javes World", tarefas: "Orquestrador de Tarefas", painel: "Painel", treino: "Treinamento", rotina: "Rotina · Briefing, Histórico & Lembretes", vempassear: "Projeto conectado · Vem Passear Jampa", exec: "Execução em Tempo Real", config: "Configurações" };
function setView(v) {
  if (window._execPollTimer) { clearInterval(window._execPollTimer); window._execPollTimer = null; }
  state.view = v; renderSidebar(); renderCanvas(); renderRightPanel();
}
function renderCanvas() {
  const body = $("canvas-body"); body.innerHTML = "";
  if ((state.q || "").trim()) {
    $("canvas-title").textContent = `Busca: "${state.q}"`;
    return viewSearch(body);
  }
  $("canvas-title").textContent = TITLES[state.view] || "";
  ({ chat: viewChat, operacao: viewOperacao, conclave: viewConclave, missoes: viewMissoes, acoes: viewAcoes, exec: viewExec, world: viewWorld, tarefas: viewTarefas, painel: viewPainel, treino: viewTreino, rotina: viewRotina, vempassear: viewVempassear, config: viewConfig }[state.view] || viewChat)(body);
}

function viewTreino(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:16px">Pipeline: <b>_entrada</b> (vídeos/repos/PDFs, coletados ou manuais) → resumo no <b>NotebookLM</b> → <b>_resumos</b> entra na base RAG do Javes.</div>`));
  if (!state.training.length) { body.appendChild(h(`<div class="empty-state">Sem dados de treinamento (backend offline?).</div>`)); return; }
  const grid = h(`<div class="grid cols-2"></div>`);
  state.training.forEach((a) => {
    const ent = a.entrada || 0, res = a.resumos || 0;
    const pc = ent ? Math.round((res / ent) * 100) : 0;
    const card = h(`
      <div class="card">
        <div class="card-head"><div class="card-icon">🎓</div><div><div class="card-title" style="text-transform:capitalize">${a.area}</div><div class="card-sub">${ent} entrada · ${res} resumos</div></div></div>
        <div class="skill-bar" style="margin:6px 0 4px"><div class="skill-fill" style="width:${pc}%"></div></div>
        <div class="card-sub">${pc}% resumido (no RAG)</div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn ok btn-scout">📥 Coletar (YouTube + GitHub)</button>
          <button class="btn no btn-resumir">✍️ Resumir pendentes (Claude)</button>
        </div>
        <div class="scout-out card-sub" style="margin-top:8px"></div>
      </div>`);
    card.querySelector(".btn-scout").onclick = async (e) => {
      const out = card.querySelector(".scout-out");
      e.target.disabled = true; out.textContent = "Coletando matéria-prima (consultando YouTube e GitHub)...";
      if (!state.online) { out.textContent = "Backend offline."; return; }
      try {
        const r = await tryJson(`${BACKEND}treinamento/scout/${a.area}`, { method: "POST" });
        const n = (r.results && r.results.length) || r.coletados || r.total || 0;
        out.textContent = `✅ Coleta concluída. Confira _treinamento/${a.area}/_entrada e suba no NotebookLM.`;
        try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; renderCanvas(); } catch (_) {}
      } catch (err) { out.textContent = "Falhou: " + err.message; e.target.disabled = false; }
    };
    card.querySelector(".btn-resumir").onclick = async (e) => {
      const out = card.querySelector(".scout-out");
      e.target.disabled = true; out.textContent = "Resumindo pendentes com o Claude (pode levar um pouco)...";
      if (!state.online) { out.textContent = "Backend offline."; e.target.disabled = false; return; }
      try {
        const r = await tryJson(`${BACKEND}treinamento/resumir/${a.area}`, { method: "POST" });
        if (r.error) { out.textContent = "⚠️ " + r.error; }
        else { out.textContent = `✅ ${r.resumidos} resumo(s) gerado(s) → entraram no RAG. Pendentes restantes: ${r.pendentes_restantes}.`; }
        try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; renderCanvas(); } catch (_) {}
      } catch (err) { out.textContent = "Falhou: " + err.message; e.target.disabled = false; }
    };
    grid.appendChild(card);
  });
  body.appendChild(grid);
  body.appendChild(h(`<div class="card-sub" style="margin-top:18px">💡 <b>NotebookLM</b> é o passo de resumo (manual — sem API pública): suba o material do <code>_entrada</code>, gere o resumo e cole em <code>_resumos</code>. O Javes indexa automático no RAG.</div>`));
}

function viewSearch(body) {
  const q = state.q.toLowerCase();
  const m = (t) => (t || "").toLowerCase().includes(q);
  const ag = state.agents.filter((a) => m(a.nome) || m(a.descricao) || (a.tags || []).some(m));
  const sq = state.squads.filter((s) => m(s.nome) || m(s.missao));
  const sk = state.skills.filter((s) => m(s.nome) || m(s.descricao));
  const scr = state.scripts.filter((s) => m(s.arquivo) || m(s.proposito));
  const total = ag.length + sq.length + sk.length + scr.length;
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">${total} resultado(s) para <b>${state.q}</b></div>`));
  if (!total) { body.appendChild(h(`<div class="empty-state">Nada encontrado.</div>`)); return; }

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
}

// ---------- Chat (por agente) ----------
function agentSkills(a) {
  let list = state.skills.filter((s) => s.agente && a.id && a.id.includes(s.agente));
  if (list.length < 3) list = state.skills.slice(0, 5);
  return list.slice(0, 5);
}

function viewChat(body) {
  const a = activeAgent();
  state.activeAgentId = a.id;
  const hist = state.chats[a.id] || [];

  // ===== STAGE HERO COM ORB GIGANTE CENTRAL =====
  body.appendChild(h(`
    <div class="stage stage-hero${hist.length ? " compact" : ""}" id="orb-host">
      <div class="brand-bar">JAVES</div>
      <div class="brand-sub">ORQUESTRADOR · VOZ · IA MULTIAGENTE</div>
      <div class="orb-stage" id="orb-stage"><canvas id="orb-canvas"></canvas></div>
      <div class="orb-state-lbl" id="neural-state">ONLINE</div>
      <div class="orb-pulse-lbl" id="neural-pulse-lbl">aguardando comando</div>
      <div class="voice-status" id="voice-status">
        <div class="voice-status-dot"></div>
        <span>OUVINDO</span>
        <span class="voice-interim" id="voice-interim"></span>
      </div>
      <div class="orb-controls">
        <button type="button" class="mic-btn" id="mic-btn" title="Gravar voz (Whisper)">🎤</button>
        <button type="button" class="voice-auto-btn" id="wake-btn" title='Wake word: diga "Javis"'>🎙️</button>
        <button type="button" class="voice-auto-btn" id="voice-auto-btn" title="Voz sempre ativa">👂</button>
        <label class="tts-chk" title="Falar resposta (TTS)"><input type="checkbox" id="use-tts" ${state.useTts ? "checked" : ""} /><span>🔊</span></label>
        <label class="conclave-chk" title="Ativar Conclave"><input type="checkbox" id="use-conclave" ${state.useConclave ? "checked" : ""} /><span>⚔️</span></label>
        <button type="button" class="brain-toggle" id="brain-toggle" title="Trocar motor: Claude ↔ Codex">🧠</button>
      </div>
    </div>`));

  // Brain toggle init
  (async () => {
    try {
      const b = await tryJson(BACKEND + "brain/active");
      state.lastBrain = b.engine || "claude";
      const btn = document.getElementById("brain-toggle");
      if (btn) { btn.textContent = state.lastBrain === "claude" ? "🧠 Claude" : "🤖 Codex"; btn.className = "brain-toggle" + (state.lastBrain === "codex" ? " codex-active" : ""); }
    } catch(_){}
  })();
  document.getElementById("brain-toggle").onclick = async () => {
    const next = (state.lastBrain === "claude") ? "codex" : "claude";
    try {
      await tryJson(BACKEND + "brain/active", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({engine: next}) });
      state.lastBrain = next;
      const btn = document.getElementById("brain-toggle");
      btn.textContent = next === "claude" ? "🧠 Claude" : "🤖 Codex";
      btn.className = "brain-toggle" + (next === "codex" ? " codex-active" : "");
    } catch(_){}
  };

  // Inicializa o motor de voz após o DOM estar pronto
  setTimeout(() => initVoiceStage(a), 0);

  // ===== CHAT (sempre presente, mas compacto) =====
  const chatBlock = h(`<div class="chat-block"></div>`);
  chatBlock.appendChild(h(`
    <div class="agent-hero compact">
      <div class="ah-avatar">${(a.nome || "?")[0]}</div>
      <div><div class="ah-name">${a.nome || "Agente"} <span class="chip accent">${a.tipo || ""}</span></div>
      <div class="ah-role">${a.descricao || ""}</div></div>
    </div>`));

  const scroll = h(`<div class="chat-scroll" id="chat-scroll"></div>`);
  hist.forEach((m) => scroll.appendChild(h(`<div class="chat-msg ${m.role}">${_esc(m.text)}</div>`)));
  chatBlock.appendChild(scroll);
  // Volta pro final do histórico ao retornar pra aba chat
  setTimeout(() => { scroll.scrollTop = scroll.scrollHeight; }, 0);

  const input = h(`
    <div class="chat-input">
      <label class="upload-btn" id="chat-upload-lbl" title="Anexar arquivo para análise (não publica; só analisa)">📎<input type="file" id="chat-file" hidden /></label>
      <textarea id="chat-text" placeholder="Mensagem para ${a.nome}... (ou clica no 🎤 acima)"></textarea>
      <button class="send-btn" id="chat-send" title="Enviar">➤</button>
    </div>`);
  chatBlock.appendChild(input);
  body.appendChild(chatBlock);

  const send = () => sendChat(a);
  input.querySelector("#chat-send").onclick = send;
  input.querySelector("#chat-file").onchange = (e) => { const f = e.target.files[0]; if (f) uploadChatFile(a, f); e.target.value = ""; };
  input.querySelector("#chat-text").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });

  // ===== HABILIDADES + SUGESTÕES (rodapé colapsável) =====
  const sk = agentSkills(a);
  const SKILL_COLORS = [
    "linear-gradient(90deg,#f59e0b,#fbbf24)",
    "linear-gradient(90deg,#8b5cf6,#a78bfa)",
    "linear-gradient(90deg,#3b82f6,#60a5fa)",
    "linear-gradient(90deg,#22c55e,#4ade80)",
    "linear-gradient(90deg,#ec4899,#f472b6)",
  ];
  const det = h(`<details class="chat-extras"><summary>★ Habilidades & Sugestões</summary></details>`);
  const box = h(`<div class="skills-box"><h4>Habilidades</h4></div>`);
  sk.forEach((s, i) => {
    const p = pct(s.id);
    box.appendChild(h(`<div class="skill-row"><div class="sr-top"><span>${s.nome}</span><span class="sr-pct">${p}%</span></div><div class="skill-bar"><div class="skill-fill" style="width:${p}%;background:${SKILL_COLORS[i % SKILL_COLORS.length]}"></div></div></div>`));
  });
  det.appendChild(box);
  const sug = h(`<div class="cmd-suggest"></div>`);
  CMD_SUGGEST.forEach((c) => {
    const it = h(`<div class="cmd-item"><div class="ci-name">${c.name}</div><div class="ci-desc">${c.desc}</div></div>`);
    it.onclick = () => { $("chat-text").value = c.name.replace(/^[^ ]+ /, "") + ": "; $("chat-text").focus(); };
    sug.appendChild(it);
  });
  det.appendChild(sug);
  body.appendChild(det);
}

// Conversa com STREAMING (SSE) via /chat/stream — token a token, igual à
// interface clássica. Mantém histórico, voz/tts, conclave e escape de texto.
async function sendChat(a, explicitMsg, speak) {
  const ta = $("chat-text");
  const msg = ((explicitMsg != null ? explicitMsg : (ta ? ta.value : "")) || "").trim();
  if (!msg) return;
  const hist = state.chats[a.id] = state.chats[a.id] || [];
  hist.push({ role: "user", text: msg });
  const scroll = $("chat-scroll");
  scroll.appendChild(h(`<div class="chat-msg user">${_esc(msg)}</div>`));
  if (ta && explicitMsg == null) ta.value = "";
  const bot = h(`<div class="chat-msg bot streaming"><span class="stream-cursor">▋</span></div>`);
  scroll.appendChild(bot); scroll.scrollTop = scroll.scrollHeight;

  if (!state.online) {
    bot.classList.remove("streaming");
    bot.textContent = "Backend offline — suba o server.py para conversar de verdade, senhor.";
    hist.push({ role: "bot", text: bot.textContent });
    return;
  }

  let full = "", meta = {};
  try {
    const res = await fetch(BACKEND + "chat/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, use_conclave: !!state.useConclave, model: "claude" }),
    });
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({}));
      bot.classList.remove("streaming");
      bot.textContent = "Erro " + res.status + ": " + (err.error || res.statusText || "falha");
      hist.push({ role: "bot", text: bot.textContent });
      return;
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "", done = false;
    while (!done) {
      const { done: rd, value } = await reader.read();
      if (rd) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;          // ignora padding/SSE comments
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") { done = true; break; }
        let ev; try { ev = JSON.parse(raw); } catch (_) { continue; }
        if (ev.type === "token") {
          full += ev.text;
          bot.innerHTML = _esc(full) + '<span class="stream-cursor">▋</span>';
          scroll.scrollTop = scroll.scrollHeight;
        } else if (ev.type === "meta") {
          meta = Object.assign(meta, ev);
          if (ev.brain) state.lastBrain = ev.brain;
        } else if (ev.type === "done") {
          if (ev.text) full = ev.text;
          if (ev.brain) state.lastBrain = ev.brain;
          if (ev.intent) state.lastTools = ev.intent;
          meta = Object.assign(meta, ev);
        }
      }
    }
    const finalText = full || "Sem resposta.";
    bot.classList.remove("streaming");
    bot.textContent = finalText;        // textContent = render seguro, sem cursor
    hist.push({ role: "bot", text: finalText });
    if (speak) speakText(finalText);
    try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); renderRightPanel(); } catch (_) {}
  } catch (e) {
    bot.classList.remove("streaming");
    bot.textContent = (e && e.name === "TypeError")
      ? "Servidor offline — não consegui conversar agora, senhor."
      : ("Falhou: " + (e && e.message ? e.message : e));
    hist.push({ role: "bot", text: bot.textContent });
  }
  scroll.scrollTop = scroll.scrollHeight;
}

// Upload de arquivo p/ análise (migrado da /classic). POST /upload (multipart).
// Só ANALISA (salva em temp no backend); não publica, não envia. Texto escapado.
async function uploadChatFile(a, file) {
  const scroll = $("chat-scroll");
  if (!scroll) return;
  const hist = state.chats[a.id] = state.chats[a.id] || [];
  const u = h(`<div class="chat-msg user"></div>`); u.textContent = "📎 " + file.name; scroll.appendChild(u);
  hist.push({ role: "user", text: "📎 " + file.name });
  const bot = h(`<div class="chat-msg bot streaming"><span class="stream-cursor">▋</span> analisando…</div>`);
  scroll.appendChild(bot); scroll.scrollTop = scroll.scrollHeight;
  if (!state.online) { bot.classList.remove("streaming"); bot.textContent = "Backend offline — não consegui analisar o arquivo."; return; }
  try {
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(BACKEND + "upload", { method: "POST", body: fd });
    const d = await res.json().catch(() => ({}));
    bot.classList.remove("streaming");
    const txt = (d.status === "ok") ? (d.message || "Análise concluída.") : ("Erro ao analisar: " + (d.message || res.status));
    bot.textContent = txt;
    hist.push({ role: "bot", text: txt });
  } catch (e) {
    bot.classList.remove("streaming");
    bot.textContent = (e && e.name === "TypeError") ? "Servidor offline — não consegui enviar o arquivo." : ("Falhou: " + (e && e.message ? e.message : e));
  }
  scroll.scrollTop = scroll.scrollHeight;
}

// ---------- Voz: gravar → transcrever → _brain → falar ----------
let _mediaRec = null, _chunks = [];

async function speakText(text) {
  try {
    const r = await fetch(BACKEND + "tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
    if (!r.ok) return;
    const blob = await r.blob();
    new Audio(URL.createObjectURL(blob)).play().catch(() => {});
  } catch (_) {}
}

async function toggleVoice(a, btn) {
  if (_mediaRec && _mediaRec.state === "recording") { _mediaRec.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    _chunks = [];
    _mediaRec = new MediaRecorder(stream);
    _mediaRec.ondataavailable = (e) => { if (e.data.size) _chunks.push(e.data); };
    _mediaRec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      btn.classList.remove("rec"); btn.textContent = "🎙️";
      const scroll = $("chat-scroll");
      const tmp = h(`<div class="chat-msg user">🎙️ transcrevendo…</div>`);
      scroll.appendChild(tmp); scroll.scrollTop = scroll.scrollHeight;
      try {
        const fd = new FormData();
        fd.append("file", new Blob(_chunks, { type: "audio/webm" }), "voz.webm");
        const r = await fetch(BACKEND + "transcribe", { method: "POST", body: fd });
        const out = await r.json();
        tmp.remove();
        if (out.text) sendChat(a, out.text, true);        // fala a resposta
        else scroll.appendChild(h(`<div class="chat-msg bot">Não entendi o áudio${out.error ? ": " + out.error : ""}.</div>`));
      } catch (e) { tmp.textContent = "Falha na transcrição: " + e.message; }
    };
    _mediaRec.start();
    btn.classList.add("rec"); btn.textContent = "⏺";
  } catch (e) {
    alert("Microfone indisponível: " + e.message);
  }
}

// ---------- World ----------
// posições no grid isométrico (col,row) e ícone por setor
const SECTOR_CELL = {
  "Core": [2, 2], "Projetos": [2, 1], "Automações": [3, 1], "Dados": [3, 2],
  "Desenvolvimento": [3, 3], "Conteúdo": [2, 3], "Operação": [1, 3],
  "Marketing": [1, 2], "Vendas": [1, 1],
};
const SECTOR_ICON = { "Core": "🧠", "Projetos": "📦", "Marketing": "📣", "Vendas": "💰",
  "Conteúdo": "✍️", "Dados": "📊", "Desenvolvimento": "⚙️", "Operação": "🛠️", "Automações": "🤖" };

function viewWorld(body) {
  body.appendChild(h(`<div class="section-h">Javes World — mapa de setores e agentes</div>`));
  const stage = h(`<div class="iso-stage"></div>`);
  const TW = 92, TH = 46, ORIGIN_Y = 80; // espaçamento isométrico
  // ordena por profundidade (col+row) p/ empilhar corretamente
  const ordered = [...SECTORS].sort((a, b) => {
    const ca = SECTOR_CELL[a] || [2, 2], cb = SECTOR_CELL[b] || [2, 2];
    return (ca[0] + ca[1]) - (cb[0] + cb[1]);
  });
  ordered.forEach((sec) => {
    const [col, row] = SECTOR_CELL[sec] || [2, 2];
    const dx = (col - row) * TW;
    const dy = (col + row) * TH + ORIGIN_Y;
    const ags = agentsForSector(sec);
    const plat = h(`<div class="iso-plat ${ags.length ? "" : "iso-empty"}" style="left:calc(50% + ${dx}px);top:${dy}px"></div>`);
    stage.appendChild(plat);
    const avas = ags.slice(0, 4).map((a) => `<span class="iso-ava" title="${a.nome}">${(a.nome || "?")[0]}</span>`).join("");
    const executing = ags.some((a) => sc(a.status) === "run");
    const node = h(`<div class="iso-node" style="left:calc(50% + ${dx}px);top:${dy}px">
      <div class="iso-tower ${executing ? "exec" : ""}">${SECTOR_ICON[sec] || "🌐"}</div>
      <div class="iso-name">${sec}</div>
      <div class="iso-count">${ags.length} agente(s)</div>
      ${avas ? `<div class="iso-avas">${avas}</div>` : ""}
    </div>`);
    if (ags.length) { node.style.cursor = "pointer"; node.title = "Abrir chat de " + ags[0].nome; node.onclick = () => { state.activeAgentId = ags[0].id; setView("chat"); }; }
    stage.appendChild(node);
  });
  body.appendChild(stage);

  // Lista por setor (legibilidade)
  const world = h(`<div class="world"></div>`);
  SECTORS.forEach((sec) => {
    const ags = agentsForSector(sec);
    const pills = ags.map((a) => `<span class="agent-pill"><span class="dot ${sc(a.status)}"></span>${a.nome}</span>`).join("") || `<span class="card-sub">— vazio —</span>`;
    world.appendChild(h(`<div class="sector"><h4>${SECTOR_ICON[sec] || "🌐"} ${sec}</h4>${pills}</div>`));
  });
  body.appendChild(world);
}
function agentsForSector(sec) {
  const s = sec.toLowerCase();
  return state.agents.filter((a) => {
    const tags = (a.tags || []).map((t) => t.toLowerCase());
    if (s === "core") return a.tipo === "orquestrador";
    if (s === "desenvolvimento") return a.tipo === "executor" || a.projeto === "javis-dev";
    if (s === "projetos") return a.projeto === "vempassear" && a.tipo === "especialista";
    if (s === "dados") return tags.includes("dados");
    if (s === "marketing") return tags.includes("marketing");
    if (s === "vendas") return tags.includes("vendas") || tags.includes("atendimento");
    if (s === "conteúdo") return tags.includes("conteudo");
    if (s === "operação") return a.squad === "operacao";
    return false;
  });
}

// ---------- Tarefas (Orquestrador) ----------
// ---------- Operação (Quadro/Kanban + Gates 1/2/3 + Aprovações) ----------
// Migrado da interface clássica (frontend/app.js). Usa SÓ endpoints já existentes:
// GET /tasks, POST /tasks/{ext}/status|run-studio|prepare-distribution,
// GET /tasks/{ext}/events, GET /approvals/pending, POST /approvals/{id}/decide.
// Modo seguro: nada é publicado; gates exigem aprovação humana explícita.
const OP_COLUMNS = [
  { key: "pending",   label: "Pendente",            icon: "📥", status: ["pending"],               setStatus: "pending" },
  { key: "running",   label: "Em andamento",        icon: "⚙️", status: ["running", "in_progress"], setStatus: "in_progress" },
  { key: "approved",  label: "Aprovado/Destravado", icon: "🔓", status: ["done", "gate_approved"],  setStatus: "gate_approved" },
  { key: "completed", label: "Concluído/Morto",     icon: "🪦", status: ["completed", "killed"],     setStatus: "completed" },
];
let _opFilter = "all";
let _opDrag = null;

function opColForStatus(s) {
  const col = OP_COLUMNS.find((c) => c.status.includes(s || "pending"));
  return col ? col.key : "pending";
}

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

// Confirmação FORTE reutilizável para ações de escrita. Não executa nada por si:
// só chama opts.onConfirm() depois que o usuário digita a frase exata e clica.
// Todo texto dinâmico é escapado. Cancelar sempre disponível.
function confirmStrong(opts) {
  const phrase = opts.phrase || "CONFIRMAR";
  const ov = h(`<div class="cs-overlay">
    <div class="cs-modal">
      <div class="cs-h">⚠️ Confirmação forte — esta ação altera dados</div>
      <div class="cs-action"></div>
      <div class="cs-grid">
        <div><span class="cs-k">Endpoint</span> <code>${_esc((opts.method || "POST") + " " + (opts.endpoint || ""))}</code></div>
        <div><span class="cs-k">Alvo</span> <span class="cs-target"></span></div>
        <div><span class="cs-k">Status atual</span> <span class="cs-before"></span></div>
        <div><span class="cs-k">Efeito</span> <span class="cs-after"></span></div>
        <div><span class="cs-k">Risco</span> ${acRiskBadge(opts.risk || "op")}</div>
      </div>
      <div class="cs-phrase-lbl">Para liberar, digite exatamente <b>${_esc(phrase)}</b>:</div>
      <input class="cs-input" placeholder="${_esc(phrase)}" autocomplete="off" />
      <div class="cs-actions">
        <button class="op-btn ok cs-go" disabled>Confirmar</button>
        <button class="op-btn ghost cs-cancel">Cancelar</button>
      </div>
      <div class="cs-fb"></div>
    </div>
  </div>`);
  ov.querySelector(".cs-action").textContent = opts.title || "Ação de escrita";
  ov.querySelector(".cs-target").textContent = opts.target || "—";
  ov.querySelector(".cs-before").textContent = opts.before || "—";
  ov.querySelector(".cs-after").textContent = opts.after || "—";
  const input = ov.querySelector(".cs-input");
  const go = ov.querySelector(".cs-go");
  const close = () => ov.remove();
  input.addEventListener("input", () => { go.disabled = (input.value.trim() !== phrase); });
  ov.querySelector(".cs-cancel").onclick = close;
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  go.onclick = async () => {
    if (input.value.trim() !== phrase) return;
    go.disabled = true; go.textContent = "Executando…";
    try { await opts.onConfirm(); } catch (_) {} finally { close(); }
  };
  document.body.appendChild(ov);
  setTimeout(() => input.focus(), 30);
}

function viewOperacao(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">Quadro operacional + gates da campanha (modo seguro — nada é publicado). Aprovações exigem decisão humana explícita. <b>Ações de escrita agora exigem confirmação forte.</b></div>`));
  if (!state.online) {
    body.appendChild(h(`<div class="banner">⚠️ Backend offline — conecte o servidor em <code>:8000</code> para ver tarefas e aprovações.</div>`));
    return;
  }
  body.appendChild(h(`<div class="section-h">🚦 Aprovações pendentes (gates)</div>`));
  body.appendChild(h(`<div id="op-approvals" class="op-approvals"><div class="card-sub">Carregando aprovações…</div></div>`));

  body.appendChild(h(`<div class="section-h" style="margin-top:22px">🗂️ Quadro / Kanban</div>`));
  body.appendChild(h(`<div id="op-filters" class="op-filters"></div>`));
  body.appendChild(h(`<div id="op-board" class="op-board"><div class="card-sub">Carregando tarefas…</div></div>`));

  opLoadApprovals();
  opRenderBoard();
}

async function opLoadApprovals() {
  const box = $("op-approvals");
  if (!box) return;
  let items = [];
  try { items = (await tryJson(BACKEND + "approvals/pending")).approvals || []; }
  catch (e) { box.innerHTML = `<div class="card-sub">Não consegui carregar as aprovações.</div>`; return; }
  if (!items.length) { box.innerHTML = `<div class="op-empty">Nenhuma aprovação pendente.</div>`; return; }
  box.innerHTML = "";
  items.forEach((a) => {
    const card = h(`<div class="op-ap" data-id="${opEsc(a.id)}">
      <div class="op-ap-subject">${opEsc(a.subject || "(sem assunto)")}</div>
      <div class="op-ap-meta">${a.agent ? "agente: " + opEsc(a.agent) : ""}${a.task_id ? " · tarefa: " + opEsc(a.task_id) : ""}</div>
      <input class="op-ap-note" placeholder="observação (opcional)…" />
      <div class="op-ap-actions">
        <button class="op-btn ok" data-act="approve">Aprovar</button>
        <button class="op-btn no" data-act="reject">Rejeitar</button>
        ${a.task_id ? `<button class="op-btn ghost" data-act="journey">Ver jornada</button>` : ""}
      </div>
      <div class="op-journey" data-open="0"></div>
      <div class="op-ap-fb"></div>
    </div>`);
    const askDecide = (decision) => confirmStrong({
      title: (decision === "approved" ? "Aprovar" : "Rejeitar") + " gate — decisão humana",
      endpoint: `/approvals/${a.id}/decide`, method: "POST",
      target: a.subject || ("aprovação #" + a.id), before: "pendente",
      after: decision === "approved" ? "aprovado (avança o workflow)" : "rejeitado (pede ajuste)",
      risk: "alto", phrase: "CONFIRMAR",
      onConfirm: () => opDecide(a.id, decision, card),
    });
    card.querySelector('[data-act="approve"]').onclick = () => askDecide("approved");
    card.querySelector('[data-act="reject"]').onclick = () => askDecide("rejected");
    const jb = card.querySelector('[data-act="journey"]');
    if (jb) jb.onclick = () => opJourney(a.task_id, card.querySelector(".op-journey"));
    box.appendChild(card);
  });
}

async function opDecide(id, decision, card) {
  const note = (card.querySelector(".op-ap-note")?.value || "").trim();
  const fb = card.querySelector(".op-ap-fb");
  if (fb) fb.textContent = "registrando…";
  try {
    const res = await opSend(BACKEND + `approvals/${id}/decide`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, note }),
    });
    if (res.status === 409) {
      if (fb) fb.textContent = "Essa aprovação já foi processada.";
      opToast("Gate já avançado anteriormente.", "info");
      setTimeout(opLoadApprovals, 600); opRenderBoard();
      return;
    }
    if (res.ok && res.data.ok) {
      opToast(res.data.message || (decision === "approved" ? "Aprovado." : "Rejeitado."), decision === "approved" ? "ok" : "info");
      setTimeout(opLoadApprovals, 600);
      opRenderBoard();
    } else if (fb) { fb.textContent = res.data.error || "Não rolou agora."; }
  } catch (e) { if (fb) fb.textContent = "Falhou: " + e.message; }
}

async function opRenderBoard() {
  const board = $("op-board");
  if (!board) return;
  let tasks = [];
  try {
    const qs = _opFilter !== "all" ? `?workflow=${encodeURIComponent(_opFilter)}` : "";
    tasks = (await tryJson(BACKEND + "tasks" + qs)).tasks || [];
  } catch (e) { board.innerHTML = `<div class="card-sub">Não consegui carregar as tarefas.</div>`; return; }

  const filters = $("op-filters");
  if (filters) {
    let allWf = [];
    try { allWf = [...new Set(((await tryJson(BACKEND + "tasks")).tasks || []).map((t) => t.workflow).filter(Boolean))]; } catch (_) {}
    filters.innerHTML = "";
    const mk = (id, label) => {
      const short = label.length > 22 ? label.slice(0, 22) + "…" : label;
      const b = h(`<button class="op-filter ${_opFilter === id ? "active" : ""}" title="${opEsc(label)}">${opEsc(short)}</button>`);
      b.onclick = () => { _opFilter = id; opRenderBoard(); };
      return b;
    };
    filters.appendChild(mk("all", "Todas"));
    allWf.forEach((w) => filters.appendChild(mk(w, w)));
  }

  if (!tasks.length) { board.innerHTML = `<div class="op-empty">Nenhuma tarefa no Quadro.</div>`; return; }

  board.innerHTML = "";
  OP_COLUMNS.forEach((col) => {
    const colCards = tasks.filter((t) => opColForStatus(t.status) === col.key);
    const colEl = h(`<div class="op-col" data-set-status="${col.setStatus}">
      <div class="opcol-head"><span>${col.icon} ${col.label}</span><span class="opcol-count">${colCards.length}</span></div>
      <div class="opcol-cards"></div>
    </div>`);
    const cardsHost = colEl.querySelector(".opcol-cards");
    if (!colCards.length) cardsHost.appendChild(h(`<div class="opcol-empty">—</div>`));
    colCards.forEach((t) => cardsHost.appendChild(opCard(t)));
    colEl.addEventListener("dragover", (e) => { e.preventDefault(); colEl.classList.add("drag-over"); });
    colEl.addEventListener("dragleave", () => colEl.classList.remove("drag-over"));
    colEl.addEventListener("drop", (e) => {
      e.preventDefault(); colEl.classList.remove("drag-over");
      if (_opDrag) {
        const ext = _opDrag; _opDrag = null;
        confirmStrong({ title: "Mover status no Quadro", endpoint: `/tasks/${encodeURIComponent(ext)}/status`, method: "POST", target: ext, before: "(status atual)", after: col.setStatus, risk: "op", phrase: "CONFIRMAR", onConfirm: () => opMoveStatus(ext, col.setStatus) });
      }
    });
    board.appendChild(colEl);
  });
}

function opCard(t) {
  const ext = t.ext_id || "";
  const encerrada = t.status === "completed" || t.status === "killed";
  const titleLow = (t.title || "").trim().toLowerCase();
  const liberada = t.status === "pending" || t.status === "in_progress";
  const card = h(`<div class="opcard s-${opColForStatus(t.status)}" title="${opEsc(t.title || "")}" ${encerrada ? "" : 'draggable="true"'}>
    <div class="opcard-text">${opEsc(t.title || "")}</div>
    <div class="opcard-foot"><span class="opcard-tag">${opEsc(t.agent || t.workflow || "—")}</span><span class="opcard-st">${opEsc(t.status || "")}</span></div>
    <div class="opcard-actions"></div>
    <div class="op-journey" data-open="0"></div>
  </div>`);
  const actions = card.querySelector(".opcard-actions");
  const jb = h(`<button class="op-btn ghost sm">Ver jornada</button>`);
  jb.onclick = () => opJourney(ext, card.querySelector(".op-journey"));
  actions.appendChild(jb);
  if (t.has_digest) actions.appendChild(h(`<span class="opcard-digest" title="tem digest">📄</span>`));
  if (titleLow.startsWith("[design]") && liberada) {
    const b = h(`<button class="op-btn studio sm">🎨 Rodar Estúdio</button>`);
    b.onclick = () => confirmStrong({ title: "Rodar Estúdio (Gate 2)", endpoint: `/tasks/${ext}/run-studio`, method: "POST", target: t.title || ext, before: t.status || "—", after: "gera criativos + cria Gate 2 (modo seguro)", risk: "op", phrase: "CONFIRMAR", onConfirm: () => opRunStudio(ext) });
    actions.appendChild(b);
  }
  if (titleLow.startsWith("[distribuição] preparar") && liberada) {
    const b = h(`<button class="op-btn studio sm">📤 Preparar Distribuição</button>`);
    b.onclick = () => confirmStrong({ title: "Preparar Distribuição (Gate 3)", endpoint: `/tasks/${ext}/prepare-distribution`, method: "POST", target: t.title || ext, before: t.status || "—", after: "gera pacote + cria Gate 3 (modo seguro)", risk: "op", phrase: "CONFIRMAR", onConfirm: () => opRunDistribution(ext) });
    actions.appendChild(b);
  }
  if (!encerrada) {
    card.addEventListener("dragstart", () => { _opDrag = ext; card.classList.add("dragging"); });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));
  }
  return card;
}

async function opJourney(extId, host) {
  if (!host) return;
  if (host.dataset.open === "1") { host.innerHTML = ""; host.dataset.open = "0"; return; }
  host.innerHTML = `<span class="card-sub">carregando jornada…</span>`;
  try {
    const d = await tryJson(BACKEND + `tasks/${encodeURIComponent(extId)}/events`);
    const evs = d.events || [];
    const status = d.task_status || "—";
    const encerrada = status === "completed" || status === "killed";
    const rows = evs.length
      ? evs.map((e) => `<div class="opjn-row"><span class="opjn-t">${opEsc((e.created_at || "").slice(11, 16))}</span><span class="opjn-ty">${opEsc(e.event_type || "")}</span><span class="opjn-msg">${opEsc(e.message || "")}</span></div>`).join("")
      : `<div class="card-sub">Sem eventos ainda.</div>`;
    let footer = "";
    if (encerrada && d.digest_text) footer = `<div class="opjn-digest"><b>📄 Digest</b><pre>${opEsc(d.digest_text)}</pre></div>`;
    host.innerHTML = `<div class="opjn-head">entidade: <b>${opEsc(status)}</b></div>${rows}${footer}`;
    host.dataset.open = "1";
  } catch (e) { host.innerHTML = `<span class="card-sub">Não consegui carregar a jornada.</span>`; }
}

async function opMoveStatus(extId, setStatus) {
  try {
    const res = await opSend(BACKEND + `tasks/${encodeURIComponent(extId)}/status`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: setStatus, note: "movido no Quadro (command-center)" }),
    });
    if (res.status === 409) opToast("Status já atualizado.", "info");
    else if (res.ok && res.data.ok && !res.data.unchanged) opToast(setStatus === "completed" ? "Entidade concluída. Digest gerado." : `Movido para "${setStatus}".`, "ok");
    else if (res.ok && res.data.unchanged) { /* sem mudança real */ }
    else if (!res.ok) opToast(res.data.error || "Não consegui mover.", "warn");
  } catch (e) { opToast("Backend offline — não movi.", "err"); }
  opRenderBoard();
}

async function opRunStudio(extId) {
  try {
    const res = await opSend(BACKEND + `tasks/${encodeURIComponent(extId)}/run-studio`, { method: "POST", headers: { "Content-Type": "application/json" } });
    if (res.status === 409) opToast("Essa ação já foi processada (Gate 2 já criado).", "info");
    else if (res.ok && res.data.ok) { opToast("Criativos gerados. Gate 2 aguardando aprovação.", "ok"); setTimeout(opLoadApprovals, 600); }
    else opToast(res.data.error || "Não consegui rodar o Estúdio.", "warn");
  } catch (e) { opToast("Falhou ao rodar o Estúdio.", "err"); }
  opRenderBoard();
}

async function opRunDistribution(extId) {
  try {
    const res = await opSend(BACKEND + `tasks/${encodeURIComponent(extId)}/prepare-distribution`, { method: "POST", headers: { "Content-Type": "application/json" } });
    if (res.status === 409) opToast("Essa ação já foi processada (Gate 3 já criado).", "info");
    else if (res.ok && res.data.ok) { opToast("Distribuição preparada. Gate 3 aguardando aprovação.", "ok"); setTimeout(opLoadApprovals, 600); }
    else opToast(res.data.error || "Não consegui preparar a distribuição.", "warn");
  } catch (e) { opToast("Falhou ao preparar a distribuição.", "err"); }
  opRenderBoard();
}

// ---------- Conclave (Debate de Agentes) — POST /debate ----------
// Squad multi-agente (architect/developer/analyst). Endpoint JÁ existente.
// Pode demorar (várias chamadas LLM): confirma antes, loading persistente,
// botão desabilitado durante execução, sem auto-retry, todo texto escapado.
const CV_AGENT_ICON = { architect: "🏗️", developer: "💻", analyst: "📊", qa: "🔍", jarvis_soul: "✨" };
let _cvBusy = false;

function viewConclave(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">Use quando precisar de análise com múltiplos pontos de vista antes de decidir. O Conclave aciona vários agentes e pode demorar — roda só quando você confirma.</div>`));
  body.appendChild(h(`<div class="cv-notice">⏱️ Pode levar <b>1–3 minutos</b>, pois aciona múltiplos agentes em rodadas. Pode continuar usando outras abas enquanto roda.</div>`));
  const form = h(`<div class="cv-form">
    <textarea id="cv-task" class="cv-task" placeholder="Tema ou pergunta do debate… (ex: vale a pena priorizar X ou Y?)"></textarea>
    <div class="cv-actions">
      <button class="op-btn studio" id="cv-run">⚔️ Rodar Conclave</button>
      <span class="cv-confirm" id="cv-confirm" hidden>
        <span class="card-sub">O Conclave pode demorar e acionar agentes. Continuar?</span>
        <button class="op-btn ok sm" id="cv-yes">Confirmar</button>
        <button class="op-btn ghost sm" id="cv-no">Cancelar</button>
      </span>
    </div>
  </div>`);
  body.appendChild(form);
  body.appendChild(h(`<div id="cv-result" class="cv-result"></div>`));

  const runBtn = form.querySelector("#cv-run");
  const confirmBar = form.querySelector("#cv-confirm");
  runBtn.onclick = () => {
    if (_cvBusy) return;
    const task = (form.querySelector("#cv-task").value || "").trim();
    if (!task) { $("cv-result").innerHTML = `<div class="op-empty">Escreva um tema para o debate.</div>`; return; }
    runBtn.hidden = true; confirmBar.hidden = false;
  };
  form.querySelector("#cv-no").onclick = () => { confirmBar.hidden = true; runBtn.hidden = false; };
  form.querySelector("#cv-yes").onclick = () => { confirmBar.hidden = true; runBtn.hidden = false; cvRunDebate(); };
}

async function cvRunDebate() {
  if (_cvBusy) return;
  const taskEl = $("cv-task"), runBtn = $("cv-run"), result = $("cv-result");
  const task = (taskEl ? taskEl.value : "").trim();
  if (!task) return;
  if (!state.online) { result.innerHTML = `<div class="banner">⚠️ Backend offline — suba o server.py para rodar o Conclave.</div>`; return; }
  _cvBusy = true;
  if (runBtn) { runBtn.disabled = true; runBtn.textContent = "⚔️ Rodando…"; }
  result.innerHTML = `<div class="cv-loading"><span class="stream-cursor">▋</span> Conclave em andamento… os agentes estão debatendo. Isso pode levar um tempo.</div>`;
  try {
    const res = await fetch(BACKEND + "debate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task, agents: ["architect", "developer", "analyst"], rounds: 2, model: "claude" }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      result.innerHTML = `<div class="banner">⚠️ Erro ${res.status}: ${_esc(err.error || res.statusText || "falha no debate")}</div>`;
      return;
    }
    const d = await res.json();
    cvRenderResult(d, task);
  } catch (e) {
    result.innerHTML = (e && e.name === "TypeError")
      ? `<div class="banner">⚠️ Servidor offline — não consegui rodar o Conclave agora.</div>`
      : `<div class="banner">⚠️ Falhou: ${_esc(e && e.message ? e.message : String(e))}</div>`;
  } finally {
    _cvBusy = false;
    if (runBtn) { runBtn.disabled = false; runBtn.textContent = "⚔️ Rodar Conclave"; }
  }
}

function cvRenderResult(d, task) {
  const result = $("cv-result");
  if (!result) return;
  result.innerHTML = "";
  const card = h(`<div class="cv-card">
    <div class="cv-card-h">🧭 Síntese do Conclave</div>
    <div class="cv-task-echo">tema: ${_esc(task)}</div>
    <div class="cv-synth"></div>
  </div>`);
  card.querySelector(".cv-synth").textContent = d.synthesis || "Sem síntese.";   // textContent = seguro
  result.appendChild(card);

  const rounds = Array.isArray(d.rounds) ? d.rounds : [];
  if (rounds.length) {
    const det = h(`<details class="cv-rounds"><summary>Ver rodadas do debate (${rounds.length})</summary></details>`);
    rounds.forEach((r) => {
      const label = (r.type === "analise") ? "ANÁLISE INDIVIDUAL" : "DEBATE";
      const rd = h(`<div class="cv-round"><div class="cv-round-h">Rodada ${_esc(r.round)} · ${label}</div></div>`);
      const outs = r.outputs || {};
      Object.keys(outs).forEach((agId) => {
        const ic = CV_AGENT_ICON[agId] || "🤖";
        const ag = h(`<div class="cv-agent"><div class="cv-agent-h">${ic} ${_esc(agId)}</div><div class="cv-agent-txt"></div></div>`);
        ag.querySelector(".cv-agent-txt").textContent = outs[agId] || "";
        rd.appendChild(ag);
      });
      det.appendChild(rd);
    });
    result.appendChild(det);
  }
  if (d.saved_to) result.appendChild(h(`<div class="card-sub" style="margin-top:10px">💾 Decisão salva em <code>_memoria/${_esc(d.saved_to)}</code></div>`));
}

// ---------- Missões (leitura) — GET /missions + /missions/{id}/nodes ----------
// Read-only: lista missões (backlog do Codex) e mostra os nodes/progresso.
// Sem ações de escrita (marcar node como done fica para fase futura, com confirmação).
let _miSel = null;

function viewMissoes(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">Missões reais derivadas do backlog. Somente leitura — clique numa missão para ver as tarefas (nodes) e o progresso.</div>`));
  if (!state.online) { body.appendChild(h(`<div class="banner">⚠️ Backend offline — conecte o servidor em <code>:8000</code> para ver as missões.</div>`)); return; }
  body.appendChild(h(`<div class="mi-wrap"><div id="mi-list" class="mi-list"><div class="card-sub">Carregando missões…</div></div><div id="mi-nodes" class="mi-nodes"><div class="op-empty">Selecione uma missão.</div></div></div>`));
  miLoadList();
}

async function miLoadList() {
  const list = $("mi-list");
  if (!list) return;
  let missions = [];
  try { missions = (await tryJson(BACKEND + "missions")).missions || []; }
  catch (e) { list.innerHTML = `<div class="card-sub">Não consegui carregar as missões.</div>`; return; }
  if (!missions.length) { list.innerHTML = `<div class="op-empty">Nenhuma missão no backlog.</div>`; return; }
  list.innerHTML = "";
  missions.forEach((m) => {
    const pctv = Math.max(0, Math.min(100, Number(m.pct) || 0));
    const card = h(`<div class="mi-card${m.id === _miSel ? " active" : ""}">
      <div class="mi-name"></div>
      <div class="mi-bar"><div class="mi-fill" style="width:${pctv}%"></div></div>
      <div class="mi-meta"><span>${pctv}%</span><span>${_esc((m.tasks_done ?? "?") + "/" + (m.tasks_total ?? "?"))} tarefas</span>${m.last_activity ? "<span>" + _esc(m.last_activity) + "</span>" : ""}</div>
    </div>`);
    card.querySelector(".mi-name").textContent = m.name || m.id || "(sem nome)";
    card.onclick = () => { _miSel = m.id; miLoadList(); miLoadNodes(m.id); };
    list.appendChild(card);
  });
}

async function miLoadNodes(id) {
  const host = $("mi-nodes");
  if (!host) return;
  host.innerHTML = `<div class="card-sub">Carregando tarefas…</div>`;
  let nodes = [];
  try { nodes = (await tryJson(BACKEND + `missions/${encodeURIComponent(id)}/nodes`)).nodes || []; }
  catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar as tarefas desta missão.</div>`; return; }
  if (!nodes.length) { host.innerHTML = `<div class="op-empty">Missão sem tarefas detalhadas.</div>`; return; }
  host.innerHTML = "";
  nodes.forEach((n) => {
    const pctv = Math.max(0, Math.min(100, Number(n.pct) || 0));
    const row = h(`<div class="mi-node">
      <div class="mi-node-h"><span class="mi-node-label"></span><span class="opcard-st">${_esc(n.status || "")}</span></div>
      <div class="mi-node-sub">${_esc(n.type || "")}</div>
      <div class="mi-bar"><div class="mi-fill" style="width:${pctv}%"></div></div>
    </div>`);
    row.querySelector(".mi-node-label").textContent = n.label || n.id || "(node)";
    host.appendChild(row);
  });
}

// ---------- Rotina (leitura) — Briefing + Histórico + Lembretes ----------
// Read-only: /briefing (sob demanda), /history e /reminders. Treino/scout tem
// aba própria ("Treino"); aqui só apontamos para ela, sem duplicar.
function viewRotina(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:14px">Resumo do dia do Javes — leitura. O status de treino/scout fica na aba <b>Treino</b>.</div>`));
  if (!state.online) { body.appendChild(h(`<div class="banner">⚠️ Backend offline — conecte o servidor em <code>:8000</code> para ver a rotina.</div>`)); return; }

  // Briefing (sob demanda)
  body.appendChild(h(`<div class="section-h">👋 Briefing</div>`));
  const brWrap = h(`<div class="ro-card"><button class="op-btn" id="ro-brief-btn">Carregar briefing</button><div id="ro-brief" class="ro-brief"></div></div>`);
  body.appendChild(brWrap);
  brWrap.querySelector("#ro-brief-btn").onclick = roLoadBriefing;

  // Histórico
  body.appendChild(h(`<div class="section-h" style="margin-top:20px">🕑 Histórico de conversa</div>`));
  body.appendChild(h(`<div id="ro-history" class="ro-card"><div class="card-sub">Carregando histórico…</div></div>`));

  // Lembretes
  body.appendChild(h(`<div class="section-h" style="margin-top:20px">⏰ Lembretes</div>`));
  body.appendChild(h(`<div id="ro-reminders" class="ro-card"><div class="card-sub">Carregando lembretes…</div></div>`));

  roLoadHistory();
  roLoadReminders();
}

async function roLoadBriefing() {
  const host = $("ro-brief");
  if (!host) return;
  host.textContent = "carregando…";
  try {
    const b = await tryJson(BACKEND + "briefing");
    host.textContent = b && b.saudacao ? b.saudacao : "Sem briefing agora.";   // textContent = seguro
  } catch (e) { host.textContent = "Não consegui carregar o briefing."; }
}

async function roLoadHistory() {
  const host = $("ro-history");
  if (!host) return;
  let items = [];
  try {
    const d = await tryJson(BACKEND + "history");
    items = Array.isArray(d) ? d : (d.history || d.messages || []);
  } catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar o histórico.</div>`; return; }
  if (!items.length) { host.innerHTML = `<div class="op-empty">Sem histórico ainda.</div>`; return; }
  host.innerHTML = "";
  items.slice(-30).forEach((it) => {
    const role = it.role || it.actor || "—";
    const txt = it.content || it.text || it.message || "";
    const when = it.ts || it.time || it.created_at || "";
    const row = h(`<div class="ro-hrow"><div class="ro-hmeta"><span class="ro-role">${_esc(role)}</span>${when ? "<span class='ro-when'>" + _esc(String(when)) + "</span>" : ""}</div><div class="ro-htext"></div></div>`);
    row.querySelector(".ro-htext").textContent = String(txt);
    host.appendChild(row);
  });
  host.scrollTop = host.scrollHeight;
}

async function roLoadReminders() {
  const host = $("ro-reminders");
  if (!host) return;
  let items = [];
  try { items = (await tryJson(BACKEND + "reminders")).pending || []; }
  catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar os lembretes.</div>`; return; }
  if (!items.length) { host.innerHTML = `<div class="op-empty">Nenhum lembrete pendente.</div>`; return; }
  host.innerHTML = "";
  items.forEach((r) => {
    const row = h(`<div class="ro-rem"><span class="ro-rem-txt"></span><span class="ro-rem-when">${r.falta_min != null ? "em " + _esc(String(r.falta_min)) + " min" : _esc(String(r.due || ""))}</span></div>`);
    row.querySelector(".ro-rem-txt").textContent = r.text || "(lembrete)";
    host.appendChild(row);
  });
}

// ---------- Central de Ações Seguras (governança — SEM execução real) ----------
// Catálogo estático das ações que escrevem/publicam/rodam agente/processam pesado.
// Nesta fase é AUDITORIA: classifica risco, mostra endpoint/método, e NÃO dispara
// nenhum POST/PATCH/DELETE. Botões de escrita ficam desabilitados ("Bloqueado nesta
// fase"). Só ações seguras: abrir a seção relacionada e copiar checklist (local).
const AC_RISK = {
  leitura:   { label: "Leitura",            cls: "ok" },
  leve:      { label: "Escrita leve",       cls: "run" },
  op:        { label: "Escrita operacional",cls: "warn" },
  pesado:    { label: "Pesado",             cls: "warn" },
  alto:      { label: "Alto risco",         cls: "err" },
  bloqueado: { label: "Bloqueado nesta fase",cls: "wait" },
};
const AC_GROUPS = [
  { id: "chat",     titulo: "Núcleo Javes · Chat & Voz", view: "chat" },
  { id: "operacao", titulo: "Operação · Kanban & Gates", view: "operacao", note: "🧪 Piloto de escrita segura: as ações de escrita da Operação já passam por confirmação forte (digitar CONFIRMAR). Só devem rodar em task descartável. Ações reais seguem bloqueadas nesta central." },
  { id: "missoes",  titulo: "Missões",                   view: "missoes" },
  { id: "rotina",   titulo: "Rotina · Lembretes",        view: "rotina" },
  { id: "treino",   titulo: "Treino / Scout",            view: "treino" },
  { id: "vp",       titulo: "Projeto conectado · Vem Passear Jampa", view: "vempassear" },
  { id: "upload",   titulo: "Upload",                    view: null },
  { id: "conclave", titulo: "Conclave / Agentes",        view: "conclave" },
];
const ACTIONS = [
  // Chat / Voz
  { g:"chat", nome:"Conversar (streaming)", ep:"/chat/stream", m:"POST", risk:"leve", ui:true, confirm:false, futuro:"já em uso; grava histórico" },
  { g:"chat", nome:"Transcrever voz",       ep:"/transcribe",  m:"POST", risk:"leve", ui:true, confirm:false, futuro:"validar com microfone real" },
  { g:"chat", nome:"Falar resposta (TTS)",  ep:"/tts",         m:"POST", risk:"leitura", ui:true, confirm:false, futuro:"gera áudio, sem escrita de dado" },
  // Operação
  { g:"operacao", nome:"Mover status (Kanban)",     ep:"/tasks/{id}/status",              m:"POST", risk:"op", ui:true, confirm:true, futuro:"testar com task descartável" },
  { g:"operacao", nome:"Aprovar/Rejeitar gate",     ep:"/approvals/{id}/decide",          m:"POST", risk:"alto", ui:true, confirm:true, futuro:"decisão humana; task descartável" },
  { g:"operacao", nome:"Rodar Estúdio (Gate 2)",    ep:"/tasks/{id}/run-studio",          m:"POST", risk:"op", ui:true, confirm:true, futuro:"gera criativos (modo seguro)" },
  { g:"operacao", nome:"Preparar Distribuição (G3)",ep:"/tasks/{id}/prepare-distribution",m:"POST", risk:"op", ui:true, confirm:true, futuro:"gera pacote (modo seguro)" },
  { g:"operacao", nome:"Concluir entidade",         ep:"/tasks/{id}/complete",            m:"POST", risk:"op", ui:false, confirm:true, futuro:"encerra task + digest" },
  // Missões
  { g:"missoes", nome:"Marcar node como done", ep:"/missions/{id}/nodes/{node}/done", m:"POST", risk:"op", ui:false, confirm:true, futuro:"altera backlog real" },
  // Rotina
  { g:"rotina", nome:"Criar lembrete", ep:"(sem endpoint exposto)", m:"—", risk:"bloqueado", ui:false, confirm:true, futuro:"falta endpoint de criação" },
  // Treino
  { g:"treino", nome:"Scout por área",   ep:"/treinamento/scout/{area}", m:"POST", risk:"pesado", ui:false, confirm:true, futuro:"processo pesado; aviso de tempo" },
  { g:"treino", nome:"Scout geral",      ep:"/treinamento/scout-all",    m:"POST", risk:"pesado", ui:false, confirm:true, futuro:"processo pesado" },
  { g:"treino", nome:"Resumir área",     ep:"/treinamento/resumir/{area}",m:"POST", risk:"pesado", ui:false, confirm:true, futuro:"LLM em lote" },
  { g:"treino", nome:"Treinar do YouTube",ep:"/train/youtube",           m:"POST", risk:"alto", ui:false, confirm:true, futuro:"download + processamento" },
  // Vem Passear (projeto conectado)
  { g:"vp", nome:"Cadastrar passeio",     ep:"/vp/passeios",      m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"dado do projeto conectado" },
  { g:"vp", nome:"Remover passeio",       ep:"/vp/passeios/{id}", m:"DELETE", risk:"alto", ui:false, confirm:true, futuro:"exclusão de dado real" },
  { g:"vp", nome:"Cadastrar cliente/lead",ep:"/vp/clientes",      m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"dado sensível" },
  { g:"vp", nome:"Mudar status cliente",  ep:"/vp/clientes/{id}", m:"PATCH",  risk:"op", ui:false, confirm:true, futuro:"altera lead real" },
  { g:"vp", nome:"Remover cliente",       ep:"/vp/clientes/{id}", m:"DELETE", risk:"alto", ui:false, confirm:true, futuro:"exclusão de dado real" },
  { g:"vp", nome:"Gerar conteúdo (LLM)",  ep:"/vp/conteudo",      m:"POST",   risk:"pesado", ui:false, confirm:true, futuro:"chama o cérebro/LLM" },
  { g:"vp", nome:"Salvar conteúdo",       ep:"/vp/conteudos",     m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"grava na biblioteca" },
  { g:"vp", nome:"Criar pauta",           ep:"/vp/pauta",         m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"linha editorial" },
  { g:"vp", nome:"Publicar/replanejar pauta",ep:"/vp/pauta/{id}", m:"PATCH", risk:"op", ui:false, confirm:true, futuro:"muda status de publicação" },
  { g:"vp", nome:"Remover pauta",         ep:"/vp/pauta/{id}",    m:"DELETE", risk:"alto", ui:false, confirm:true, futuro:"exclusão de dado real" },
  { g:"vp", nome:"Rodar agente VP",       ep:"/vp/agents/run",    m:"POST",   risk:"alto", ui:false, confirm:true, futuro:"execução de agente do projeto" },
  // Upload
  { g:"upload", nome:"Upload de arquivo", ep:"/upload", m:"POST", risk:"op", ui:false, confirm:true, futuro:"fase própria; validar tipo/tamanho" },
  // Conclave
  { g:"conclave", nome:"Rodar Conclave",       ep:"/debate", m:"POST", risk:"pesado", ui:true, confirm:true, futuro:"já em uso; 1–3 min" },
  { g:"conclave", nome:"Chat com Conclave",    ep:"/chat/stream (use_conclave)", m:"POST", risk:"pesado", ui:true, confirm:false, futuro:"toggle ⚔️ no Chat" },
];

function acRiskBadge(risk) { const r = AC_RISK[risk] || AC_RISK.bloqueado; return `<span class="badge ${r.cls}"><span class="dot ${r.cls}"></span>${_esc(r.label)}</span>`; }
function acChecklistText(a) {
  return `Ação: ${a.nome}\nEndpoint: ${a.m} ${a.ep}\nRisco: ${(AC_RISK[a.risk]||{}).label || a.risk}\nUI existente: ${a.ui ? "sim" : "não"}\nExige confirmação: ${a.confirm ? "sim" : "não"}\nStatus: bloqueado nesta fase (sem escrita real)\nPróxima fase: ${a.futuro}`;
}

function viewAcoes(body) {
  body.appendChild(h(`<div class="vp-boundary">🛡️ <b>Central de Ações Seguras.</b> Mapa das ações que alteram dados, disparam agentes ou executam processos. Nesta fase a central <b>organiza riscos e prepara aprovações</b> — <b>nenhuma escrita real é executada daqui</b>.</div>`));
  // Resumo por categoria
  const counts = {};
  ACTIONS.forEach((a) => { counts[a.risk] = (counts[a.risk] || 0) + 1; });
  const summary = h(`<div class="ac-summary"></div>`);
  ["leitura","leve","op","pesado","alto","bloqueado"].forEach((k) => {
    if (!counts[k]) return;
    const r = AC_RISK[k];
    summary.appendChild(h(`<div class="ac-sum ${r.cls}"><div class="ac-sum-n">${counts[k]}</div><div class="ac-sum-l">${_esc(r.label)}</div></div>`));
  });
  body.appendChild(summary);
  // Grupos
  AC_GROUPS.forEach((grp) => {
    const items = ACTIONS.filter((a) => a.g === grp.id);
    if (!items.length) return;
    const head = h(`<div class="ac-group-h"><span>${_esc(grp.titulo)}</span></div>`);
    if (grp.view) {
      const open = h(`<button class="op-btn ghost sm">Abrir seção</button>`);
      open.onclick = () => setView(grp.view);
      head.appendChild(open);
    }
    body.appendChild(head);
    if (grp.note) { const n = h(`<div class="ac-note"></div>`); n.textContent = grp.note; body.appendChild(n); }
    items.forEach((a) => {
      const card = h(`<div class="ac-card">
        <div class="ac-card-top"><span class="ac-name"></span>${acRiskBadge(a.risk)}</div>
        <div class="ac-ep"><code>${_esc(a.m)} ${_esc(a.ep)}</code></div>
        <div class="ac-flags">UI existente: <b>${a.ui ? "sim" : "não"}</b> · confirmação: <b>${a.confirm ? "sim" : "não"}</b> · <span class="ac-status">bloqueado nesta fase</span></div>
        <div class="ac-next">Próxima fase: <span class="ac-next-v"></span></div>
        <div class="ac-actions">
          <button class="op-btn sm" disabled title="Ativação em fase própria, com confirmação forte">Executar (bloqueado nesta fase)</button>
          <button class="op-btn ghost sm ac-copy">Copiar checklist</button>
        </div>
      </div>`);
      card.querySelector(".ac-name").textContent = a.nome;
      card.querySelector(".ac-next-v").textContent = a.futuro;
      card.querySelector(".ac-copy").onclick = async (e) => {
        try { await navigator.clipboard.writeText(acChecklistText(a)); e.target.textContent = "Copiado ✓"; setTimeout(() => { e.target.textContent = "Copiar checklist"; }, 1500); }
        catch (_) { e.target.textContent = "Copie manualmente"; }
      };
      body.appendChild(card);
    });
  });
}

// ---------- Vem Passear Jampa (projeto conectado — LEITURA) ----------
// Fronteira: projeto EXTERNO do Cérebro Jampa, consultado pelo Javes por registro.
// NÃO mistura contexto com o núcleo. 100% leitura nesta fase: nenhum POST/PATCH/
// DELETE, nenhuma execução de agente, nenhum envio/publicação. Tudo escapado.
let _vpTab = "resumo";
const VP_TABS = [
  { id: "resumo",      label: "Resumo" },
  { id: "atendimento", label: "Atendimento" },
  { id: "funil",       label: "Funil" },
  { id: "reservas",    label: "Reservas" },
  { id: "voucher",     label: "Voucher" },
  { id: "agenda",      label: "Agenda" },
  { id: "posvenda",    label: "Pós-venda" },
  { id: "marketing",   label: "Marketing" },
  { id: "resultados",  label: "Resultados" },
  { id: "gates",       label: "Gates" },
  { id: "passeios",  label: "Passeios · legado" },
  { id: "clientes",  label: "Clientes · legado" },
  { id: "conteudos", label: "Conteúdos · legado" },
  { id: "pauta",     label: "Pauta · legado" },
  { id: "agentes",   label: "Agentes" },
];
const vpBRL = (v) => { const n = Number(v); return isNaN(n) ? _esc(String(v ?? "—")) : "R$ " + n.toFixed(2).replace(".", ","); };
const vpMask = (s) => { const t = String(s || "").trim(); if (!t) return ""; if (t.length <= 4) return "••"; return t.slice(0, 2) + "•••" + t.slice(-2); };

const VP_DISPATCH = {
  resumo: vpResumo, atendimento: vpAtendimento, funil: vpFunil, reservas: vpReservas,
  voucher: vpVoucherTab, agenda: vpAgenda, posvenda: vpPosVenda, marketing: vpMarketing,
  resultados: vpResultados, gates: vpGates,
  passeios: vpPasseios, clientes: vpClientes, conteudos: vpConteudos, pauta: vpPauta, agentes: vpAgentes,
};
const VP_ONLINE_ONLY = new Set(["passeios", "clientes", "conteudos", "pauta", "agentes"]);

function viewVempassear(body) {
  body.appendChild(h(`<div class="vp-boundary">🔗 <b>Projeto conectado via Cérebro Jampa.</b> O Javes consulta e organiza este projeto <b>por registro</b>, sem misturar contexto automaticamente com o núcleo. Contexto externo · somente leitura nesta fase.</div>`));
  if (!state.online) body.appendChild(h(`<div class="banner">⚠️ Backend offline — as telas operacionais (Resumo, Atendimento, Funil, Reservas, Voucher, Agenda, Pós-venda, Marketing, Resultados, Gates) seguem com dados sintéticos. Passeios/Clientes/Conteúdos/Pauta/Agentes (legado) precisam do servidor em <code>:8000</code>.</div>`));
  const chips = h(`<div class="vp-chips"></div>`);
  VP_TABS.forEach((t) => {
    const c = h(`<button class="vp-chip${t.id === _vpTab ? " active" : ""}">${_esc(t.label)}</button>`);
    c.onclick = () => { _vpTab = t.id; renderCanvas(); };
    chips.appendChild(c);
  });
  body.appendChild(chips);
  body.appendChild(h(`<div id="vp-content" class="vp-content"><div class="card-sub">Carregando…</div></div>`));
  if (VP_ONLINE_ONLY.has(_vpTab) && !state.online) { $("vp-content").innerHTML = `<div class="banner">⚠️ Esta aba (legado) precisa do backend em <code>:8000</code>.</div>`; return; }
  (VP_DISPATCH[_vpTab] || vpResumo)();
}

async function vpResumo() {
  const host = $("vp-content"); if (!host) return;
  let resumo = {};
  if (state.online) { try { resumo = (await tryJson(BACKEND + "vp/passeios")).resumo || {}; } catch (_) {} }
  host.innerHTML = `
    <div class="vp-card">
      <div class="vp-row"><span class="vp-k">Nome</span><span class="vp-v">Vem Passear Jampa</span></div>
      <div class="vp-row"><span class="vp-k">Projeto externo</span><span class="vp-v">Cérebro Jampa</span></div>
      <div class="vp-row"><span class="vp-k">Relação</span><span class="vp-v">conectado ao Javes por registro</span></div>
      <div class="vp-row"><span class="vp-k">Estado</span><span class="vp-v"><span class="badge ${state.online ? "ok" : "wait"}"><span class="dot ${state.online ? "ok" : "wait"}"></span>${state.online ? "online" : "offline"}</span></span></div>
    </div>
    <div class="section-h" style="margin-top:16px">Resumo operacional (projeto conectado)</div>
    <div class="vp-stats">
      <div class="vp-stat"><div class="vp-stat-n">${_esc(String(resumo.total_passeios ?? 0))}</div><div class="vp-stat-l">passeios</div></div>
      <div class="vp-stat"><div class="vp-stat-n">${_esc(String(resumo.total_pessoas ?? 0))}</div><div class="vp-stat-l">pessoas</div></div>
      <div class="vp-stat"><div class="vp-stat-n">${vpBRL(resumo.faturamento ?? 0)}</div><div class="vp-stat-l">faturamento</div></div>
    </div>`;

  // ---- Dashboard do dia (sintético + leads reais em leitura quando online) ----
  await vpSyncRealLeads();
  if (_vpTab !== "resumo" || !$("vp-content")) return;
  const leadsHoje = AT_LEADS.filter((l) => l.status === "Lead novo").length + _vpRealLeads.length;
  const reservasPendentes = AT_LEADS.filter((l) => ["Proposta enviada", "Aguardando reserva"].includes(l.status)).length;
  const vouchersPendentes = AT_LEADS.filter((l) => l.status === "Reserva paga").length;
  const passeiosHoje = AT_LEADS.filter((l) => l.reserva.data === VP_HOJE).length;
  const saldosAReceber = AT_LEADS.reduce((s, l) => s + (l.reserva.saldo || 0), 0);
  const posVendaPendente = AT_LEADS.filter((l) => ["Voucher gerado", "Passeio realizado"].includes(l.status)).length;
  const tarefasUrgentes = AT_LEADS.filter((l) => l.prioridade === "alta").length;
  const conteudosPendentes = AT_MKT.filter((c) => c.status !== "Publicado").length;

  const dashCards = [
    ["👥", "Leads de hoje", leadsHoje], ["📝", "Reservas pendentes", reservasPendentes],
    ["🎫", "Vouchers pendentes", vouchersPendentes], ["🗓️", "Passeios de hoje", passeiosHoje],
    ["💰", "Saldos a receber", vpBRL(saldosAReceber)], ["⭐", "Pós-venda pendente", posVendaPendente],
    ["🔥", "Tarefas urgentes", tarefasUrgentes], ["✍️", "Conteúdos pendentes", conteudosPendentes],
  ];
  host.insertAdjacentHTML("beforeend", `<div class="section-h" style="margin-top:20px">📅 Dashboard do dia <span class="card-sub">(dados sintéticos)</span></div>`);
  const grid = h(`<div class="at-dash-grid"></div>`);
  dashCards.forEach(([ic, label, val]) => grid.appendChild(h(`<div class="at-dash-card"><div class="at-dash-ic">${ic}</div><div class="at-dash-n">${_esc(String(val))}</div><div class="at-dash-l">${_esc(label)}</div></div>`)));
  host.appendChild(grid);

  host.insertAdjacentHTML("beforeend", `<div class="section-h" style="margin-top:18px">🚨 Prioridade do dia</div>`);
  const alerts = h(`<div class="at-dash-alerts"></div>`);
  ["Confirmar reservas sem voucher.", "Conferir passageiros/manifesto.", "Pedir avaliações dos passeios realizados."].forEach((a) => alerts.appendChild(h(`<div class="at-dash-alert">⚠️ ${_esc(a)}</div>`)));
  host.appendChild(alerts);

  const btns = h(`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px"></div>`);
  const bNovo = h(`<button class="op-btn studio">➕ Novo atendimento</button>`);
  bNovo.onclick = () => vpVisualModal("➕ Novo atendimento", `<p style="font-size:13px;color:var(--text)">Abriria um novo card de lead na coluna "Lead novo" do Funil.</p>`, { warn: "Fase visual — sem gravação real." });
  const bAgenda = h(`<button class="op-btn ghost">📅 Ver agenda</button>`);
  bAgenda.onclick = () => { _vpTab = "agenda"; renderCanvas(); };
  const bReservas = h(`<button class="op-btn ghost">📋 Ver reservas</button>`);
  bReservas.onclick = () => { _vpTab = "reservas"; renderCanvas(); };
  btns.append(bNovo, bAgenda, bReservas);
  host.appendChild(btns);
}

async function vpPasseios() {
  const host = $("vp-content"); if (!host) return;
  host.innerHTML = "";
  const form = h(`<div class="vp-form">
    <div class="vp-form-h">➕ Cadastrar passeio <span class="card-sub">(escrita no projeto conectado — exige confirmação forte)</span></div>
    <div class="vp-form-row">
      <input id="vps-tipo" class="cs-input vp-in" placeholder="tipo/nome do passeio" />
      <input id="vps-data" class="cs-input vp-in" placeholder="data (ex: 2026-07-10)" />
    </div>
    <div class="vp-form-row">
      <input id="vps-pessoas" class="cs-input vp-in" type="number" min="1" placeholder="pessoas" value="1" />
      <input id="vps-valor" class="cs-input vp-in" type="number" min="0" step="0.01" placeholder="valor/p" value="0" />
    </div>
    <div style="text-align:right;margin-top:8px"><button class="op-btn studio" id="vps-add">➕ Cadastrar passeio</button></div>
  </div>`);
  host.appendChild(form);
  form.querySelector("#vps-add").onclick = () => {
    const tipo = ($("vps-tipo").value || "").trim(), data = ($("vps-data").value || "").trim();
    const pessoas = parseInt($("vps-pessoas").value || "1", 10) || 1, valor = parseFloat($("vps-valor").value || "0") || 0;
    if (!tipo) { opToast("Informe o tipo do passeio.", "warn"); return; }
    confirmStrong({ title: "Cadastrar passeio (Vem Passear · projeto conectado)", endpoint: "/vp/passeios", method: "POST", target: tipo, before: "—", after: `${data || "s/data"} · ${pessoas}p · ${vpBRL(valor)}`, risk: "leve", phrase: "CONFIRMAR", onConfirm: () => vpCreatePasseio(tipo, data, pessoas, valor) });
  };
  const listHost = h(`<div id="vp-pas-list"></div>`); host.appendChild(listHost);
  let passeios = [];
  try { passeios = (await tryJson(BACKEND + "vp/passeios")).passeios || []; }
  catch (e) { listHost.innerHTML = `<div class="card-sub">Não consegui carregar os passeios.</div>`; return; }
  if (!passeios.length) { listHost.innerHTML = `<div class="op-empty">Nenhum passeio cadastrado.</div>`; return; }
  passeios.forEach((p) => {
    const card = h(`<div class="vp-item"><div class="vp-item-h"></div><div class="vp-item-meta"><span class="accent">${_esc(p.data || "s/ data")}</span> · ${_esc(String(p.pessoas ?? "?"))} pessoa(s) · ${vpBRL(p.valor)}/p</div></div>`);
    card.querySelector(".vp-item-h").textContent = p.tipo || "(passeio)";
    listHost.appendChild(card);
  });
}

async function vpCreatePasseio(tipo, data, pessoas, valor) {
  try {
    const res = await opSend(BACKEND + "vp/passeios", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tipo, data, pessoas, valor }) });
    if (res.ok && res.data.status === "ok") { opToast("Passeio cadastrado.", "ok"); vpPasseios(); }
    else opToast(res.data.message || ("Falha (" + res.status + ")"), "warn");
  } catch (e) { opToast("Backend offline — não cadastrei.", "err"); }
}

async function vpClientes() {
  const host = $("vp-content"); if (!host) return;
  host.innerHTML = "";
  const form = h(`<div class="vp-form">
    <div class="vp-form-h">➕ Cadastrar cliente/lead <span class="card-sub">(dado sensível — exige confirmação forte)</span></div>
    <div class="vp-form-row">
      <input id="vpcl-nome" class="cs-input vp-in" placeholder="nome" />
      <input id="vpcl-contato" class="cs-input vp-in" placeholder="contato (use teste)" />
    </div>
    <textarea id="vpcl-obs" class="cv-task" placeholder="observação (opcional)…"></textarea>
    <div style="text-align:right;margin-top:8px"><button class="op-btn studio" id="vpcl-add">➕ Cadastrar cliente</button></div>
  </div>`);
  host.appendChild(form);
  form.querySelector("#vpcl-add").onclick = () => {
    const nome = ($("vpcl-nome").value || "").trim(), contato = ($("vpcl-contato").value || "").trim(), obs = ($("vpcl-obs").value || "").trim();
    if (!nome) { opToast("Informe o nome.", "warn"); return; }
    confirmStrong({ title: "Cadastrar cliente (Vem Passear · projeto conectado)", endpoint: "/vp/clientes", method: "POST", target: nome, before: "—", after: "cria lead" + (contato ? " · " + vpMask(contato) : ""), risk: "leve", phrase: "CONFIRMAR", onConfirm: () => vpCreateCliente(nome, contato, obs) });
  };
  const listHost = h(`<div id="vp-cli-list"></div>`); host.appendChild(listHost);
  let d = {};
  try { d = await tryJson(BACKEND + "vp/clientes"); }
  catch (e) { listHost.innerHTML = `<div class="card-sub">Não consegui carregar os clientes.</div>`; return; }
  const leads = d.leads || [], fechados = d.fechados || [];
  if (!leads.length && !fechados.length) { listHost.innerHTML = `<div class="op-empty">Nenhum cliente/lead ainda.</div>`; return; }
  const block = (titulo, arr, tagClass) => {
    listHost.appendChild(h(`<div class="section-h">${_esc(titulo)} (${arr.length})</div>`));
    if (!arr.length) { listHost.appendChild(h(`<div class="op-empty">—</div>`)); return; }
    arr.forEach((c) => {
      const row = h(`<div class="vp-item"><div class="vp-item-h"><span class="vp-tag ${tagClass}"></span></div><div class="vp-item-meta">${_esc(vpMask(c.contato))}${c.obs ? " · " + _esc(c.obs) : ""}</div></div>`);
      row.querySelector(".vp-tag").textContent = c.nome || "(cliente)";
      listHost.appendChild(row);
    });
  };
  block("Leads abertos", leads, "lead");
  block("Fechados", fechados, "fechado");
}

async function vpCreateCliente(nome, contato, obs) {
  try {
    const res = await opSend(BACKEND + "vp/clientes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome, contato, obs }) });
    if (res.ok && res.data.status === "ok") { opToast("Cliente cadastrado.", "ok"); vpClientes(); }
    else opToast(res.data.message || ("Falha (" + res.status + ")"), "warn");
  } catch (e) { opToast("Backend offline — não cadastrei.", "err"); }
}

async function vpConteudos() {
  const host = $("vp-content"); if (!host) return;
  host.innerHTML = "";
  // Salvar conteúdo manual (escrita — confirmação forte). NÃO gera via LLM.
  const form = h(`<div class="vp-form">
    <div class="vp-form-h">➕ Salvar conteúdo <span class="card-sub">(texto manual; não gera via LLM — exige confirmação forte)</span></div>
    <div class="vp-form-row"><input id="vpc-tipo" class="cs-input vp-in" placeholder="tipo (ex: legenda)" value="ideias" /></div>
    <textarea id="vpc-texto" class="cv-task" placeholder="texto do conteúdo…"></textarea>
    <div style="text-align:right;margin-top:8px"><button class="op-btn studio" id="vpc-add">➕ Salvar conteúdo</button></div>
  </div>`);
  host.appendChild(form);
  form.querySelector("#vpc-add").onclick = () => {
    const tipo = ($("vpc-tipo").value || "ideias").trim(), texto = ($("vpc-texto").value || "").trim();
    if (!texto) { opToast("Escreva o texto do conteúdo.", "warn"); return; }
    confirmStrong({ title: "Salvar conteúdo (Vem Passear · projeto conectado)", endpoint: "/vp/conteudos", method: "POST", target: tipo, before: "—", after: "salva conteúdo: " + texto.slice(0, 40), risk: "leve", phrase: "CONFIRMAR", onConfirm: () => vpCreateConteudo(tipo, texto) });
  };
  const listHost = h(`<div id="vp-cont-list"></div>`); host.appendChild(listHost);
  let conteudos = [];
  try { conteudos = (await tryJson(BACKEND + "vp/conteudos")).conteudos || []; }
  catch (e) { listHost.innerHTML = `<div class="card-sub">Não consegui carregar os conteúdos.</div>`; return; }
  if (!conteudos.length) { listHost.innerHTML = `<div class="op-empty">Nenhum conteúdo salvo.</div>`; return; }
  conteudos.forEach((c) => {
    const card = h(`<div class="vp-item"><div class="vp-item-h"><span class="accent">${_esc(c.tipo || "conteúdo")}</span></div><div class="vp-item-body"></div></div>`);
    card.querySelector(".vp-item-body").textContent = (c.texto || "").slice(0, 400);
    listHost.appendChild(card);
  });
}

async function vpCreateConteudo(tipo, texto) {
  try {
    const res = await opSend(BACKEND + "vp/conteudos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tipo, texto }) });
    if (res.ok && res.data.status === "ok") { opToast("Conteúdo salvo.", "ok"); vpConteudos(); }
    else opToast(res.data.message || ("Falha (" + res.status + ")"), "warn");
  } catch (e) { opToast("Backend offline — não salvei.", "err"); }
}

async function vpPauta() {
  const host = $("vp-content"); if (!host) return;
  host.innerHTML = "";
  // Form de criação (escrita — protegida por confirmação forte). Projeto conectado.
  const form = h(`<div class="vp-form">
    <div class="vp-form-h">➕ Nova pauta <span class="card-sub">(escrita no projeto conectado — exige confirmação forte)</span></div>
    <div class="vp-form-row">
      <input id="vpp-data" class="cs-input vp-in" placeholder="data (ex: 2026-07-05)" />
      <input id="vpp-canal" class="cs-input vp-in" placeholder="canal (ex: Instagram)" value="Instagram" />
    </div>
    <textarea id="vpp-ideia" class="cv-task" placeholder="ideia do post…"></textarea>
    <div style="text-align:right;margin-top:8px"><button class="op-btn studio" id="vpp-add">➕ Criar pauta</button></div>
  </div>`);
  host.appendChild(form);
  form.querySelector("#vpp-add").onclick = () => {
    const data = ($("vpp-data").value || "").trim(), canal = ($("vpp-canal").value || "Instagram").trim(), ideia = ($("vpp-ideia").value || "").trim();
    if (!ideia) { opToast("Escreva a ideia da pauta.", "warn"); return; }
    confirmStrong({ title: "Criar pauta (Vem Passear · projeto conectado)", endpoint: "/vp/pauta", method: "POST", target: (data || "s/data") + " · " + canal, before: "—", after: "cria nova pauta: " + ideia.slice(0, 40), risk: "leve", phrase: "CONFIRMAR", onConfirm: () => vpCreatePauta(data, canal, ideia) });
  };
  const listHost = h(`<div id="vp-pauta-list"></div>`); host.appendChild(listHost);
  let pauta = [];
  try { pauta = (await tryJson(BACKEND + "vp/pauta")).pauta || []; }
  catch (e) { listHost.innerHTML = `<div class="card-sub">Não consegui carregar a pauta.</div>`; return; }
  if (!pauta.length) { listHost.innerHTML = `<div class="op-empty">Nenhuma pauta planejada.</div>`; return; }
  pauta.forEach((p) => {
    const pub = p.status === "publicado";
    const card = h(`<div class="vp-item"><div class="vp-item-h"><span class="vp-tag ${pub ? "fechado" : "lead"}">${_esc(p.data || "")}</span> · ${_esc(p.canal || "")} <span class="opcard-st">${_esc(p.status || "")}</span></div><div class="vp-item-body"></div></div>`);
    card.querySelector(".vp-item-body").textContent = p.ideia || "";
    listHost.appendChild(card);
  });
}

async function vpCreatePauta(data, canal, ideia) {
  try {
    const res = await opSend(BACKEND + "vp/pauta", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ data, canal, ideia }) });
    if (res.ok && (res.data.status === "ok")) { opToast("Pauta criada.", "ok"); vpPauta(); }
    else opToast(res.data.message || ("Falha (" + res.status + ")"), "warn");
  } catch (e) { opToast("Backend offline — não criei a pauta.", "err"); }
}

async function vpAgentes() {
  const host = $("vp-content"); if (!host) return;
  let agents = [];
  try { agents = (await tryJson(BACKEND + "vp/agents")).agents || []; }
  catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar os agentes.</div>`; return; }
  if (!agents.length) { host.innerHTML = `<div class="op-empty">Nenhum agente VP.</div>`; return; }
  host.innerHTML = `<div class="card-sub" style="margin-bottom:10px">Squad de marketing da Vem Passear (leitura). Execução de agente fica para fase futura, com confirmação.</div>`;
  agents.forEach((a) => {
    const ic = a.icon || "🤖";
    const card = h(`<div class="vp-item"><div class="vp-item-h">${ic} <span class="vp-agent-nome"></span></div><div class="vp-item-meta"></div></div>`);
    card.querySelector(".vp-agent-nome").textContent = a.nome || "(agente)";
    card.querySelector(".vp-item-meta").textContent = a.papel || "";
    host.appendChild(card);
  });
}

// ---------- Atendimento (VP · MVP1 — 3 colunas, visual/frontend-only) ----------
// Dados sintéticos só pra visual. Nenhuma escrita real: nem em disco, nem em backend.
// Resolve: briefing incompleto, lead perdido no WhatsApp, proposta confusa,
// reserva sem controle, voucher manual. IA aparece só como copiloto discreto.
const AT_FUNNEL = ["Lead novo", "Em atendimento", "Proposta enviada", "Aguardando reserva", "Reserva paga", "Voucher gerado", "Passeio realizado", "Pós-venda"];
const VP_HOJE = "2026-07-03"; // referência sintética de "hoje" pra Dashboard/Agenda
const VP_CONTATO = "(24) 99999-0000 · contato@vempassearjampa.com.br";
const VP_INSTRUCOES = "Chegar 15 min antes no ponto de encontro. Levar documento com foto e protetor solar.";
const VP_POLITICA_CANCEL = "Cancelamento com até 48h de antecedência: reembolso de 80% do sinal. Depois disso, sem reembolso.";

const AT_LEADS = [
  {
    id: "l1", cliente: "Marina Silva", telefone: "24991230001", status: "Em atendimento", passeio: "Escuna · Ilha Grande",
    ultimaMsg: "Quanto fica pra 4 adultos e 2 crianças?", prioridade: "alta",
    proximaAcao: "Confirmar horário e enviar proposta com valor.",
    chat: [
      { from: "cliente", texto: "Oi, vocês têm horário pra sábado?" },
      { from: "agente", texto: "Temos sim! Saída às 9h ou 14h." },
      { from: "cliente", texto: "Quanto fica pra 4 adultos e 2 crianças?" },
    ],
    sugestao: "Oi Marina! Pra 4 adultos e 2 crianças no passeio de Escuna sai R$ 720 (criança até 8 anos tem 50% off). Posso reservar às 9h de sábado?",
    reserva: { passeio: "Escuna · Ilha Grande", pessoas: 4, criancas: 2, hotel: "Recanto do Sol · Centro", data: "2026-07-06", horario: "09:00", valorTotal: 720, sinal: 200, saldo: 520, pagamento: "Pix (parcial)", parceiro: "Escuna Vitória", obs: "Pediu confirmação por WhatsApp." },
  },
  {
    id: "l2", cliente: "Rafael & Bia", telefone: "24991230002", status: "Lead novo", passeio: "Trilha Pico do Papagaio",
    ultimaMsg: "Vi o story, ainda tem vaga pra sexta?", prioridade: "media",
    proximaAcao: "Perguntar nº de pessoas e experiência com trilha.",
    chat: [{ from: "cliente", texto: "Vi o story, ainda tem vaga pra sexta?" }],
    sugestao: "Oi! Temos vaga sim pra sexta. É pra quantas pessoas e vocês já têm experiência com trilha?",
    reserva: { passeio: "Trilha Pico do Papagaio", pessoas: 2, criancas: 0, hotel: "—", data: "2026-07-04", horario: "07:00", valorTotal: 260, sinal: 0, saldo: 260, pagamento: "—", parceiro: "Guia Zé Trilheiro", obs: "Ainda sem briefing completo." },
  },
  {
    id: "l3", cliente: "Fernanda Costa", telefone: "24991230003", status: "Proposta enviada", passeio: "Passeio de Lancha · Praias",
    ultimaMsg: "Vou ver com meu marido e te aviso.", prioridade: "media",
    proximaAcao: "Fazer follow-up amanhã à noite.",
    chat: [
      { from: "cliente", texto: "Manda a proposta pra 6 pessoas?" },
      { from: "agente", texto: "Proposta enviada: R$ 1.380 pra 6 adultos, saída 10h." },
      { from: "cliente", texto: "Vou ver com meu marido e te aviso." },
    ],
    sugestao: "Oi Fernanda, ficou alguma dúvida sobre a proposta? Posso segurar o horário das 10h até amanhã à noite.",
    reserva: { passeio: "Lancha · Praias", pessoas: 6, criancas: 0, hotel: "Pousada Mar Azul", data: "2026-07-09", horario: "10:00", valorTotal: 1380, sinal: 0, saldo: 1380, pagamento: "—", parceiro: "Lancha Netuno", obs: "Aguardando decisão do casal." },
  },
  {
    id: "l4", cliente: "Grupo Amigos RJ (8p)", telefone: "24991230004", status: "Aguardando reserva", passeio: "Bike + Praia",
    ultimaMsg: "Fechado! Só falta o sinal.", prioridade: "alta",
    proximaAcao: "Cobrar sinal até quinta-feira.",
    chat: [
      { from: "cliente", texto: "Fechado! Só falta o sinal." },
      { from: "agente", texto: "Show! Te mando a chave Pix do sinal agora." },
    ],
    sugestao: "Perfeito! Segue a chave Pix pra sinal de R$ 150. Assim que cair eu confirmo a reserva e mando o voucher.",
    reserva: { passeio: "Bike + Praia", pessoas: 8, criancas: 0, hotel: "Hostel Vista Mar", data: "2026-07-12", horario: "08:30", valorTotal: 960, sinal: 150, saldo: 810, pagamento: "Pix (sinal pendente)", parceiro: "Bike Tour Jampa", obs: "Cobrar sinal até quinta." },
  },
  {
    id: "l5", cliente: "Casal Andrade", telefone: "24991230005", status: "Reserva paga", passeio: "City Tour Histórico",
    ultimaMsg: "Pagamento feito, obrigada!", prioridade: "baixa",
    proximaAcao: "Gerar voucher e enviar.",
    chat: [{ from: "cliente", texto: "Pagamento feito, obrigada!" }, { from: "agente", texto: "Recebido! Já vou gerar o voucher de vocês." }],
    sugestao: "Ótimo, pagamento confirmado! Posso gerar o voucher do City Tour pra amanhã às 9h?",
    reserva: { passeio: "City Tour Histórico", pessoas: 2, criancas: 0, hotel: "Hotel Costa Verde", data: VP_HOJE, horario: "09:00", valorTotal: 340, sinal: 340, saldo: 0, pagamento: "Pago integral", parceiro: "Guia Local Centro", obs: "Pronto pra gerar voucher." },
  },
  {
    id: "l6", cliente: "Beatriz Lima", telefone: "24991230006", status: "Voucher gerado", passeio: "Mergulho · Naufrágio",
    ultimaMsg: "Chegou o voucher, obrigada 🙏", prioridade: "baixa",
    proximaAcao: "Confirmar presença 1 dia antes.",
    avaliacao: "pendente",
    chat: [{ from: "agente", texto: "Voucher enviado no seu e-mail e WhatsApp." }, { from: "cliente", texto: "Chegou o voucher, obrigada 🙏" }],
    sugestao: "De nada! Qualquer dúvida antes do passeio de amanhã é só chamar por aqui.",
    reserva: { passeio: "Mergulho · Naufrágio", pessoas: 1, criancas: 0, hotel: "Pousada do Mar", data: "2026-07-02", horario: "08:00", valorTotal: 280, sinal: 280, saldo: 0, pagamento: "Pago integral", parceiro: "Dive Jampa", obs: "Voucher #VP-0342 enviado." },
  },
  {
    id: "l7", cliente: "Grupo Excursão SP (12p)", telefone: "24991230007", status: "Passeio realizado", passeio: "Trilha + Cachoeira",
    ultimaMsg: "Foi incrível, valeu demais!", prioridade: "baixa",
    proximaAcao: "Pedir avaliação no Google.",
    avaliacao: "pendente",
    chat: [{ from: "cliente", texto: "Foi incrível, valeu demais!" }],
    sugestao: "Que alegria saber! Se puder deixar uma avaliação rápida no Google, ajuda demais a gente. 🙏",
    reserva: { passeio: "Trilha + Cachoeira", pessoas: 12, criancas: 1, hotel: "Camping Verde Vale", data: "2026-06-30", horario: "08:00", valorTotal: 1440, sinal: 1440, saldo: 0, pagamento: "Pago integral", parceiro: "Guia Zé Trilheiro", obs: "Passeio concluído sem intercorrências." },
  },
  {
    id: "l8", cliente: "Paulo Nunes", telefone: "24991230008", status: "Perdido", passeio: "Passeio de Lancha · Praias",
    ultimaMsg: "Vou fechar com outra agência, valor ficou alto.", prioridade: "baixa",
    proximaAcao: "Registrar motivo e reengajar em campanha futura.",
    chat: [{ from: "cliente", texto: "Vou fechar com outra agência, valor ficou alto." }],
    sugestao: "Entendo, Paulo. Se quiser, posso te avisar quando tivermos uma condição especial nesse passeio.",
    reserva: { passeio: "Lancha · Praias", pessoas: 3, criancas: 0, hotel: "—", data: "—", horario: "—", valorTotal: 690, sinal: 0, saldo: 690, pagamento: "—", parceiro: "Lancha Netuno", obs: "Perdido por preço." },
  },
];

// Leads REAIS (leitura via GET /vp/clientes, mesmo endpoint da aba legado).
// Só leitura: nenhum botão escreve; telefone sempre mascarado na tela.
let _vpRealLeads = [];
async function vpSyncRealLeads() {
  if (!state.online) { _vpRealLeads = []; return; }
  try {
    const d = await tryJson(BACKEND + "vp/clientes");
    _vpRealLeads = (d.leads || []).map((c, i) => ({
      id: "real-" + i, real: true,
      cliente: c.nome || "(cliente)", telefone: c.contato || "",
      status: "Lead novo", passeio: "—", prioridade: "media",
      ultimaMsg: c.obs || "sem observação registrada",
      proximaAcao: "Completar briefing (passeio, data, pessoas).",
      chat: [],
      sugestao: `Oi ${(c.nome || "").split(" ")[0] || ""}! Aqui é da Vem Passear Jampa 😊 Qual passeio você tem interesse e pra qual data?`.replace("  ", " "),
      reserva: { passeio: "—", pessoas: "—", criancas: "—", hotel: "—", data: "—", horario: "—", valorTotal: 0, sinal: 0, saldo: 0, pagamento: "—", parceiro: "—", obs: c.obs || "—" },
    }));
  } catch (_) { _vpRealLeads = []; }
}
const atLeads = () => AT_LEADS.concat(_vpRealLeads);

let _atLeadId = AT_LEADS[0].id;
const atLead = (id) => atLeads().find((l) => l.id === id) || AT_LEADS[0];
const atPrioClass = { alta: "err", media: "warn", baixa: "ok" };
const atFunnelIdx = (status) => { const i = AT_FUNNEL.indexOf(status); return i < 0 ? 0 : i; };

async function vpAtendimento() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = "";
  const note = state.online
    ? "Atendimento — demo sintética + leads reais em leitura (marcados com 🔗). Escrita real desligada nesta fase."
    : "Atendimento — visual, dados sintéticos. Escrita real desligada nesta fase.";
  host.appendChild(h(`<div class="card-sub" style="margin-bottom:12px">${_esc(note)}</div>`));
  await vpSyncRealLeads();
  if (_vpTab !== "atendimento" || !$("vp-content")) return; // usuário trocou de aba durante o fetch

  const wrap = h(`<div class="at-cols"></div>`);
  wrap.appendChild(atColLeft());
  wrap.appendChild(atColCenter());
  wrap.appendChild(atColRight());
  host.appendChild(wrap);
}

function atColLeft() {
  const col = h(`<div class="at-col at-col-left"><div class="at-col-h">Leads / Conversas</div><div class="at-lead-list"></div></div>`);
  const list = col.querySelector(".at-lead-list");
  atLeads().forEach((l) => {
    const active = l.id === _atLeadId;
    const it = h(`<div class="at-lead-item${active ? " active" : ""}">
      <div class="at-lead-top"><span class="at-lead-nome"></span><span class="badge ${atPrioClass[l.prioridade] || "wait"}">●</span></div>
      <div class="at-lead-status"></div>
      <div class="at-lead-passeio"></div>
      <div class="at-lead-msg"></div>
    </div>`);
    it.querySelector(".at-lead-nome").textContent = (l.real ? "🔗 " : "") + l.cliente;
    it.querySelector(".at-lead-status").textContent = l.status + (l.real ? " · leitura real" : "");
    it.querySelector(".at-lead-passeio").textContent = "🎯 " + l.passeio;
    it.querySelector(".at-lead-msg").textContent = "💬 " + l.ultimaMsg;
    it.onclick = () => { _atLeadId = l.id; vpAtendimento(); };
    list.appendChild(it);
  });
  return col;
}

const AT_BRIEFING_FIELDS = [["passeio", "Passeio"], ["data", "Data"], ["horario", "Horário"], ["pessoas", "Pessoas"], ["criancas", "Crianças"], ["hotel", "Hotel/Bairro"], ["pagamento", "Forma de pagamento"], ["sinal", "Reserva/Sinal"], ["saldo", "Saldo"], ["parceiro", "Parceiro"], ["obs", "Observações"]];
const AT_BRIEFING_ESSENCIAIS = ["data", "pessoas", "hotel"];
const atIsMissing = (v) => v === undefined || v === null || v === "" || v === "—";

function atColCenter() {
  const l = atLead(_atLeadId);
  const r = l.reserva;
  const col = h(`<div class="at-col at-col-center"></div>`);
  if (l.status === "Perdido") {
    col.appendChild(h(`<div class="at-funnel"><span class="at-funnel-step lost">✖ Lead perdido</span></div>`));
  } else {
    const idx = atFunnelIdx(l.status);
    const funnel = h(`<div class="at-funnel"></div>`);
    AT_FUNNEL.forEach((step, i) => {
      funnel.appendChild(h(`<span class="at-funnel-step${i === idx ? " current" : ""}${i < idx ? " done" : ""}">${_esc(step)}</span>`));
    });
    col.appendChild(funnel);
  }

  const missingEssenciais = AT_BRIEFING_ESSENCIAIS.filter((k) => atIsMissing(r[k]));
  if (missingEssenciais.length) col.appendChild(h(`<div class="at-alert">⚠️ Briefing incompleto — confirme data, pessoas e local de busca antes de gerar voucher.</div>`));

  const det = h(`<details class="at-briefing"><summary>📋 Checklist do briefing</summary><div class="at-briefing-grid"></div></details>`);
  const bg = det.querySelector(".at-briefing-grid");
  AT_BRIEFING_FIELDS.forEach(([k, label]) => {
    const ok = !atIsMissing(r[k]);
    bg.appendChild(h(`<span class="at-check ${ok ? "ok" : "pend"}">${ok ? "✅" : "⬜"} ${_esc(label)}</span>`));
  });
  col.appendChild(det);

  col.appendChild(h(`<div class="at-col-h">Conversa · ${_esc(l.cliente)}</div>`));
  const chat = h(`<div class="at-chat"></div>`);
  if (!l.chat.length) chat.appendChild(h(`<div class="op-empty">Sem histórico de conversa ainda.</div>`));
  l.chat.forEach((m) => chat.appendChild(h(`<div class="at-msg ${m.from === "agente" ? "agente" : "cliente"}">${_esc(m.texto)}</div>`)));
  col.appendChild(chat);

  const ai = h(`<div class="at-ai-box">
    <div class="at-ai-h">✨ Sugestão da IA</div>
    <div class="at-ai-text"></div>
    <div class="at-ai-actions">
      <button class="op-btn ok at-copy-btn">📋 Copiar sugestão</button>
      <button class="op-btn ghost" disabled title="em breve">✏️ Reescrever <span class="chip">em breve</span></button>
    </div>
  </div>`);
  ai.querySelector(".at-ai-text").textContent = l.sugestao;
  ai.querySelector(".at-copy-btn").onclick = async (e) => {
    try { await navigator.clipboard.writeText(l.sugestao); opToast("Sugestão copiada.", "ok"); }
    catch (_) { opToast("Não consegui copiar (permissão do navegador).", "warn"); }
  };
  col.appendChild(ai);
  return col;
}

function atField(k, v) {
  return `<div class="at-f"><span class="at-f-k">${_esc(k)}</span><span class="at-f-v">${_esc(String(v ?? "—"))}</span></div>`;
}

function atColRight() {
  const l = atLead(_atLeadId);
  const r = l.reserva;
  const col = h(`<div class="at-col at-col-right"><div class="at-col-h">CRM rápido · Reserva</div></div>`);
  const box = h(`<div class="at-crm"></div>`);
  box.innerHTML = [
    atField("Passeio", r.passeio), atField("Pessoas", r.pessoas), atField("Crianças", r.criancas),
    atField("Hotel/Bairro", r.hotel), atField("Data", r.data), atField("Horário", r.horario),
    atField("Valor total", vpBRL(r.valorTotal)), atField("Reserva/Sinal", vpBRL(r.sinal)), atField("Saldo", vpBRL(r.saldo)),
    atField("Pagamento", r.pagamento), atField("Parceiro", r.parceiro), atField("Observações", r.obs),
  ].join("");
  col.appendChild(box);
  const btn = h(`<button class="op-btn studio at-voucher-btn">🎫 Gerar reserva/voucher</button>`);
  btn.onclick = () => vpVoucherModal(l);
  col.appendChild(btn);
  return col;
}

// ---------- Modal genérico "fase visual" — nenhuma chamada escreve nada real ----------
function vpVisualModal(title, bodyHtml, opts) {
  opts = opts || {};
  const ov = h(`<div class="cs-overlay">
    <div class="cs-modal vp-modal">
      <div class="cs-h"></div>
      <div class="vp-modal-warn"></div>
      <div class="vp-modal-body"></div>
      <div class="cs-actions"></div>
    </div>
  </div>`);
  ov.querySelector(".cs-h").textContent = title;
  if (opts.warn) ov.querySelector(".vp-modal-warn").innerHTML = `<div class="banner">⚠️ ${_esc(opts.warn)}</div>`;
  ov.querySelector(".vp-modal-body").innerHTML = bodyHtml || "";
  const actions = ov.querySelector(".cs-actions");
  (opts.extraActions || []).forEach((a) => {
    const b = h(`<button class="op-btn ok"></button>`); b.textContent = a.label; b.onclick = a.onClick;
    actions.appendChild(b);
  });
  const closeBtn = h(`<button class="op-btn ghost">Fechar</button>`);
  const close = () => ov.remove();
  closeBtn.onclick = close;
  actions.appendChild(closeBtn);
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  document.body.appendChild(ov);
  return ov;
}

function vpCopyResumo(lead) {
  const r = lead.reserva;
  const txt = `Vem Passear Jampa — Resumo\nCliente: ${lead.cliente}\nPasseio: ${r.passeio}\nData/Horário: ${r.data} · ${r.horario}\nPessoas: ${r.pessoas} (crianças: ${r.criancas})\nLocal de busca: ${r.hotel}\nValor total: ${vpBRL(r.valorTotal)} · Sinal: ${vpBRL(r.sinal)} · Saldo: ${vpBRL(r.saldo)}\nParceiro: ${r.parceiro}\nObs: ${r.obs}`;
  navigator.clipboard.writeText(txt).then(() => opToast("Resumo copiado.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
}

// Voucher visual — prévia apenas, não é emitido nem enviado de verdade.
function vpVoucherModal(lead) {
  const r = lead.reserva;
  const pago = (r.valorTotal || 0) - (r.saldo || 0);
  const body = `
    <div class="voucher-card">
      <div class="voucher-h"><div class="voucher-logo">🌊</div><div><div class="voucher-brand">Vem Passear Jampa</div><div class="voucher-sub">Voucher de passeio · prévia</div></div></div>
      <div class="at-crm">
        ${atField("Cliente", lead.cliente)}${atField("Passeio", r.passeio)}
        ${atField("Data", r.data)}${atField("Horário", r.horario)}
        ${atField("Local de saída/busca", r.hotel)}${atField("Parceiro", r.parceiro)}
        ${atField("Valor pago", vpBRL(pago))}${atField("Saldo", vpBRL(r.saldo))}
      </div>
      <div class="voucher-block"><b>Instruções</b><p>${_esc(VP_INSTRUCOES)}</p></div>
      <div class="voucher-block"><b>Política de cancelamento</b><p>${_esc(VP_POLITICA_CANCEL)}</p></div>
      <div class="voucher-block"><b>Contato</b><p>${_esc(VP_CONTATO)}</p></div>
    </div>`;
  vpVisualModal("🎫 Gerar voucher", body, {
    warn: "Fase visual — prévia do voucher, não emitida nem enviada.",
    extraActions: [{ label: "📋 Copiar resumo", onClick: () => vpCopyResumo(lead) }],
  });
}

// ---------- Funil de Vendas (Kanban visual — sem drag real) ----------
async function vpFunil() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Funil de vendas · demo sintética${state.online ? " + leads reais em leitura (🔗)" : ""}. Sem drag-and-drop nesta fase.</div>`;
  await vpSyncRealLeads();
  if (_vpTab !== "funil" || !$("vp-content")) return;
  const all = atLeads();
  const board = h(`<div class="fk-board"></div>`);
  const cols = AT_FUNNEL.concat(["Perdido"]);
  cols.forEach((col) => {
    const leads = all.filter((l) => l.status === col);
    const colEl = h(`<div class="fk-col"><div class="fk-col-h">${_esc(col)} <span class="ti-count">${leads.length}</span></div><div class="fk-cards"></div></div>`);
    const cardsBox = colEl.querySelector(".fk-cards");
    leads.forEach((l) => {
      const r = l.reserva;
      const card = h(`<div class="fk-card">
        <div class="fk-card-nome">${l.real ? "🔗 " : ""}${_esc(l.cliente)}${l.real ? ` <span class="chip">leitura real</span>` : ""}</div>
        <div class="fk-card-meta">🎯 ${_esc(l.passeio)}</div>
        <div class="fk-card-meta">👥 ${_esc(String(r.pessoas))}p · 📅 ${_esc(r.data)} · 💰 ${vpBRL(r.valorTotal)}</div>
        <div class="fk-card-next">➡ ${_esc(l.proximaAcao || "—")}</div>
        <div class="fk-card-actions"></div>
      </div>`);
      const actions = card.querySelector(".fk-card-actions");
      const bVer = h(`<button class="op-btn ghost sm">Ver atendimento</button>`);
      bVer.onclick = () => { _atLeadId = l.id; _vpTab = "atendimento"; renderCanvas(); };
      actions.appendChild(bVer);
      const bNext = h(`<button class="op-btn studio sm">Próxima etapa</button>`);
      bNext.onclick = () => vpVisualModal("➡ Próxima etapa", `<p style="font-size:13px">Moveria <b>${_esc(l.cliente)}</b> pra próxima etapa do funil.</p>`, { warn: "Fase visual — sem gravação real." });
      actions.appendChild(bNext);
      if (l.sugestao) {
        const bCopy = h(`<button class="op-btn ok sm">Copiar resposta</button>`);
        bCopy.onclick = () => navigator.clipboard.writeText(l.sugestao).then(() => opToast("Resposta copiada.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
        actions.appendChild(bCopy);
      }
      if (col === "Passeio realizado" || col === "Pós-venda") {
        const bPos = h(`<button class="op-btn ghost sm">Marcar pós-venda</button>`);
        bPos.onclick = () => vpVisualModal("⭐ Marcar pós-venda", `<p style="font-size:13px">Marcaria <b>${_esc(l.cliente)}</b> como pós-venda em andamento.</p>`, { warn: "Fase visual — sem gravação real." });
        actions.appendChild(bPos);
      }
      cardsBox.appendChild(card);
    });
    if (!leads.length) cardsBox.appendChild(h(`<div class="op-empty">—</div>`));
    board.appendChild(colEl);
  });
  host.appendChild(board);
}

// ---------- Reservas & Vouchers (tabela visual) ----------
function vpReservas() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Reservas · dados sintéticos, telefone mascarado. Nenhuma escrita real nesta fase.</div>`;
  const wrap = h(`<div class="vp-table-wrap"></div>`);
  const table = h(`<table class="vp-table"><thead><tr>
    <th>Cliente</th><th>Telefone</th><th>Passeio</th><th>Data</th><th>Horário</th><th>Pessoas</th><th>Crianças</th>
    <th>Valor total</th><th>Sinal</th><th>Saldo</th><th>Pagamento</th><th>Hotel/Bairro</th><th>Parceiro</th><th>Status</th><th>Ações</th>
  </tr></thead><tbody></tbody></table>`);
  const tbody = table.querySelector("tbody");
  AT_LEADS.forEach((l) => {
    const r = l.reserva;
    const tr = h(`<tr>
      <td>${_esc(l.cliente)}</td><td>${_esc(vpMask(l.telefone))}</td><td>${_esc(r.passeio)}</td><td>${_esc(r.data)}</td><td>${_esc(r.horario)}</td>
      <td>${_esc(String(r.pessoas))}</td><td>${_esc(String(r.criancas))}</td><td>${vpBRL(r.valorTotal)}</td><td>${vpBRL(r.sinal)}</td><td>${vpBRL(r.saldo)}</td>
      <td>${_esc(r.pagamento)}</td><td>${_esc(r.hotel)}</td><td>${_esc(r.parceiro)}</td><td><span class="vp-tag ${l.status === "Perdido" ? "lead" : "fechado"}">${_esc(l.status)}</span></td>
      <td class="vp-table-actions"></td>
    </tr>`);
    const actions = tr.querySelector(".vp-table-actions");
    const bDet = h(`<button class="op-btn ghost sm">Ver detalhes</button>`);
    bDet.onclick = () => vpVisualModal(`📋 ${l.cliente}`, [
      atField("Passeio", r.passeio), atField("Data", r.data), atField("Horário", r.horario), atField("Pessoas", r.pessoas), atField("Crianças", r.criancas),
      atField("Hotel/Bairro", r.hotel), atField("Valor total", vpBRL(r.valorTotal)), atField("Sinal", vpBRL(r.sinal)), atField("Saldo", vpBRL(r.saldo)),
      atField("Pagamento", r.pagamento), atField("Parceiro", r.parceiro), atField("Observações", r.obs),
    ].join(""), { extraActions: [{ label: "📋 Copiar resumo", onClick: () => vpCopyResumo(l) }] });
    const bVoucher = h(`<button class="op-btn studio sm">Gerar voucher</button>`);
    bVoucher.onclick = () => vpVoucherModal(l);
    const bCopy = h(`<button class="op-btn ok sm">Copiar resumo</button>`);
    bCopy.onclick = () => vpCopyResumo(l);
    const bPag = h(`<button class="op-btn ghost sm">Confirmar pagamento</button>`);
    bPag.onclick = () => vpVisualModal("💳 Confirmar pagamento", `<p style="font-size:13px">Confirmaria o pagamento de <b>${_esc(l.cliente)}</b>.</p>`, { warn: "Fase visual — sem gravação real." });
    actions.append(bDet, bVoucher, bCopy, bPag);
    tbody.appendChild(tr);
  });
  wrap.appendChild(table);
  host.appendChild(wrap);
}

// ---------- Voucher (galeria de pendências/emitidos) ----------
function vpVoucherTab() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Vouchers · prévia visual. Nenhum voucher é emitido ou enviado de verdade nesta fase.</div>`;
  const pendentes = AT_LEADS.filter((l) => l.status === "Reserva paga");
  const emitidos = AT_LEADS.filter((l) => ["Voucher gerado", "Passeio realizado", "Pós-venda"].includes(l.status));
  const block = (titulo, arr, tagClass) => {
    host.insertAdjacentHTML("beforeend", `<div class="section-h">${_esc(titulo)} (${arr.length})</div>`);
    if (!arr.length) { host.insertAdjacentHTML("beforeend", `<div class="op-empty">—</div>`); return; }
    arr.forEach((l) => {
      const card = h(`<div class="vp-item"><div class="vp-item-h"><span class="vp-tag ${tagClass}"></span></div><div class="vp-item-meta"></div><div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap"></div></div>`);
      card.querySelector(".vp-tag").textContent = l.cliente;
      card.querySelector(".vp-item-meta").textContent = `${l.reserva.passeio} · ${l.reserva.data} ${l.reserva.horario}`;
      const acts = card.querySelector("div:last-child");
      const bGen = h(`<button class="op-btn studio sm">🎫 ${tagClass === "lead" ? "Gerar voucher" : "Ver voucher"}</button>`);
      bGen.onclick = () => vpVoucherModal(l);
      acts.appendChild(bGen);
      host.appendChild(card);
    });
  };
  block("Vouchers pendentes", pendentes, "lead");
  block("Vouchers emitidos", emitidos, "fechado");
}

// ---------- Agenda / Manifesto ----------
let _agView = "hoje", _agPasseio = "all", _agParceiro = "all";
function vpAgenda() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = "";
  const toggles = h(`<div class="vp-chips" style="margin-bottom:10px"></div>`);
  ["hoje", "semana"].forEach((v) => {
    const c = h(`<button class="vp-chip${_agView === v ? " active" : ""}">${v === "hoje" ? "Hoje" : "Semana"}</button>`);
    c.onclick = () => { _agView = v; vpAgenda(); };
    toggles.appendChild(c);
  });
  host.appendChild(toggles);

  const passeios = ["all", ...new Set(AT_LEADS.map((l) => l.reserva.passeio))];
  const parceiros = ["all", ...new Set(AT_LEADS.map((l) => l.reserva.parceiro))];
  const filtros = h(`<div class="vp-form-row" style="margin-bottom:12px"></div>`);
  const selP = h(`<select class="cs-input vp-in"></select>`);
  passeios.forEach((p) => selP.appendChild(h(`<option value="${_esc(p)}">${p === "all" ? "Todos os passeios" : _esc(p)}</option>`)));
  selP.value = _agPasseio; selP.onchange = () => { _agPasseio = selP.value; vpAgenda(); };
  const selPa = h(`<select class="cs-input vp-in"></select>`);
  parceiros.forEach((p) => selPa.appendChild(h(`<option value="${_esc(p)}">${p === "all" ? "Todos os parceiros" : _esc(p)}</option>`)));
  selPa.value = _agParceiro; selPa.onchange = () => { _agParceiro = selPa.value; vpAgenda(); };
  filtros.append(selP, selPa);
  host.appendChild(filtros);

  let rows = AT_LEADS.filter((l) => l.status !== "Perdido" && l.reserva.data !== "—");
  if (_agView === "hoje") rows = rows.filter((l) => l.reserva.data === VP_HOJE);
  if (_agPasseio !== "all") rows = rows.filter((l) => l.reserva.passeio === _agPasseio);
  if (_agParceiro !== "all") rows = rows.filter((l) => l.reserva.parceiro === _agParceiro);
  rows = rows.slice().sort((a, b) => (a.reserva.data + a.reserva.horario).localeCompare(b.reserva.data + b.reserva.horario));

  host.insertAdjacentHTML("beforeend", `<div class="section-h">📋 Manifesto (${rows.length})</div>`);
  if (!rows.length) host.insertAdjacentHTML("beforeend", `<div class="op-empty">Nenhum passeio nesse filtro.</div>`);
  rows.forEach((l) => {
    const r = l.reserva;
    host.appendChild(h(`<div class="vp-item">
      <div class="vp-item-h">${_esc(r.horario)} · ${_esc(r.passeio)} <span class="accent">${_esc(r.data)}</span></div>
      <div class="vp-item-meta">${_esc(l.cliente)} · ${_esc(String(r.pessoas))}p · busca: ${_esc(r.hotel)} · pago: ${vpBRL(r.valorTotal - r.saldo)} · saldo: ${vpBRL(r.saldo)} · parceiro: ${_esc(r.parceiro)}</div>
      <div class="vp-item-body">${_esc(r.obs || "")}</div>
    </div>`));
  });

  const btns = h(`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px"></div>`);
  const bPdf = h(`<button class="op-btn ghost" disabled title="em breve">📄 Gerar manifesto PDF <span class="chip">em breve</span></button>`);
  const bCopy = h(`<button class="op-btn ok">📋 Copiar manifesto</button>`);
  bCopy.onclick = () => {
    const txt = rows.map((l) => `${l.reserva.horario} · ${l.reserva.passeio} · ${l.cliente} · ${l.reserva.pessoas}p · busca: ${l.reserva.hotel} · saldo: ${vpBRL(l.reserva.saldo)}`).join("\n");
    navigator.clipboard.writeText(txt || "Sem itens no filtro atual.").then(() => opToast("Manifesto copiado.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
  };
  const bEnviar = h(`<button class="op-btn ghost" disabled title="em breve">📤 Enviar parceiro <span class="chip">em breve</span></button>`);
  const bSaldos = h(`<button class="op-btn studio">💰 Conferir saldos</button>`);
  bSaldos.onclick = () => {
    const total = rows.reduce((s, l) => s + (l.reserva.saldo || 0), 0);
    vpVisualModal("💰 Saldos a receber", `<p style="font-size:13px">Total de saldo a receber no filtro atual: <b>${vpBRL(total)}</b> (${rows.length} reserva(s)).</p>`);
  };
  btns.append(bPdf, bCopy, bEnviar, bSaldos);
  host.appendChild(btns);
}

// ---------- Pós-venda ----------
const _atPosVendaSolicitado = new Set(); // estado só em memória — reseta ao recarregar
function vpPosVenda() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Pós-venda · mensagens sugeridas, cópia manual. Nada é enviado automaticamente.</div>`;
  const leads = AT_LEADS.filter((l) => l.avaliacao);
  if (!leads.length) { host.insertAdjacentHTML("beforeend", `<div class="op-empty">Nenhum passeio aguardando pós-venda.</div>`); return; }
  leads.forEach((l) => {
    const solicitado = _atPosVendaSolicitado.has(l.id);
    const msg = `Oi ${l.cliente.split(" ")[0]}! Que bom que você curtiu o passeio de ${l.reserva.passeio} 😊 Poderia deixar uma avaliação rápida pra gente? Ajuda muito!`;
    const card = h(`<div class="vp-item">
      <div class="vp-item-h">${_esc(l.passeio)} <span class="vp-tag ${solicitado ? "fechado" : "lead"}">${solicitado ? "solicitado" : "pendente"}</span></div>
      <div class="vp-item-meta">${_esc(l.cliente)} · ${_esc(l.reserva.data)}</div>
      <div class="vp-item-body"></div>
      <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap"></div>
    </div>`);
    card.querySelector(".vp-item-body").textContent = msg;
    const acts = card.querySelector("div:last-child");
    const bCopy = h(`<button class="op-btn ok sm">📋 Copiar pedido de avaliação</button>`);
    bCopy.onclick = () => navigator.clipboard.writeText(msg).then(() => opToast("Mensagem copiada.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
    const bMark = h(`<button class="op-btn ${solicitado ? "ghost" : "studio"} sm">${solicitado ? "✔ Solicitado" : "Marcar como solicitado"}</button>`);
    bMark.onclick = () => { if (solicitado) _atPosVendaSolicitado.delete(l.id); else _atPosVendaSolicitado.add(l.id); vpPosVenda(); };
    const bGoogle = h(`<button class="op-btn ghost sm" disabled title="em breve">🔗 Link Google <span class="chip">em breve</span></button>`);
    acts.append(bCopy, bMark, bGoogle);
    host.appendChild(card);
  });
}

// ---------- Marketing (apoio — kanban visual estático) ----------
const AT_MKT = [
  { id: "m1", tema: "Bastidores da Escuna", passeio: "Escuna · Ilha Grande", formato: "Reels", status: "Ideias", risco: false, legenda: "" },
  { id: "m2", tema: "Trilha ao amanhecer", passeio: "Trilha Pico do Papagaio", formato: "Carrossel", status: "Pauta", risco: false, legenda: "" },
  { id: "m3", tema: "Promoção fim de semana", passeio: "Bike + Praia", formato: "Story", status: "Roteiro/Legenda", risco: true, legenda: "🚲🌊 Bike + praia com condição especial esse fim de semana! Vagas limitadas, chama no direct." },
  { id: "m4", tema: "Depoimento cliente", passeio: "City Tour Histórico", formato: "Reels", status: "Criativo", risco: false, legenda: "" },
  { id: "m5", tema: "Mergulho no naufrágio", passeio: "Mergulho · Naufrágio", formato: "Post", status: "Aprovação", risco: true, legenda: "🤿 Maré boa essa semana pro passeio de mergulho no naufrágio! Poucas vagas." },
  { id: "m6", tema: "Recapitulando a temporada", passeio: "Vários", formato: "Carrossel", status: "Publicado", risco: false, legenda: "" },
];
const VP_MKT_COLS = ["Ideias", "Pauta", "Roteiro/Legenda", "Criativo", "Aprovação", "Publicado"];
function vpMarketing() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = `<div class="banner">💡 Marketing é apoio. Fluxo operacional de vendas/reservas vem primeiro.</div>`;
  const top = h(`<div style="margin:10px 0"></div>`);
  const bIdeia = h(`<button class="op-btn ghost" disabled title="em breve">💡 Gerar ideia <span class="chip">em breve</span></button>`);
  top.appendChild(bIdeia);
  host.appendChild(top);

  const board = h(`<div class="fk-board"></div>`);
  VP_MKT_COLS.forEach((col) => {
    const cards = AT_MKT.filter((c) => c.status === col);
    const colEl = h(`<div class="fk-col"><div class="fk-col-h">${_esc(col)} <span class="ti-count">${cards.length}</span></div><div class="fk-cards"></div></div>`);
    const box = colEl.querySelector(".fk-cards");
    cards.forEach((c) => {
      const card = h(`<div class="fk-card">
        <div class="fk-card-nome">${_esc(c.tema)}</div>
        <div class="fk-card-meta">🎯 ${_esc(c.passeio)} · ${_esc(c.formato)}</div>
        ${c.risco ? `<div class="fk-card-meta"><span class="badge warn">⚠️ sensível (maré/preço/vaga)</span></div>` : ""}
        <div class="fk-card-actions"></div>
      </div>`);
      const acts = card.querySelector(".fk-card-actions");
      if (c.legenda) {
        const bCopy = h(`<button class="op-btn ok sm">Copiar legenda</button>`);
        bCopy.onclick = () => navigator.clipboard.writeText(c.legenda).then(() => opToast("Legenda copiada.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
        acts.appendChild(bCopy);
      }
      if (col === "Aprovação") {
        const bOk = h(`<button class="op-btn ok sm">Aprovar</button>`);
        bOk.onclick = () => vpVisualModal("✅ Aprovar pauta", `<p style="font-size:13px">Aprovaria <b>${_esc(c.tema)}</b> pra seguir pra Publicado.</p>`, { warn: "Fase visual — sem gravação real." });
        const bNo = h(`<button class="op-btn no sm">Reprovar</button>`);
        bNo.onclick = () => vpVisualModal("❌ Reprovar pauta", `<p style="font-size:13px">Reprovaria <b>${_esc(c.tema)}</b> e voltaria pro roteiro.</p>`, { warn: "Fase visual — sem gravação real." });
        acts.append(bOk, bNo);
      }
      box.appendChild(card);
    });
    if (!cards.length) box.appendChild(h(`<div class="op-empty">—</div>`));
    board.appendChild(colEl);
  });
  host.appendChild(board);
}

// ---------- Resultados (dummy) ----------
function vpResultados() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Resultados · números sintéticos, só pra visual.</div>`;
  const cards = [
    ["Leads", "38"], ["Reservas", "21"], ["Receita", vpBRL(18420)], ["Ticket médio", vpBRL(877)],
    ["Conversão", "55%"], ["Passeio mais vendido", "Escuna · Ilha Grande"], ["Origem do lead", "Instagram 46%"],
    ["Avaliações Google", "4.8 ★ (126)"], ["Clientes perdidos", "4"], ["ROAS", "—"],
  ];
  const grid = h(`<div class="at-dash-grid"></div>`);
  cards.forEach(([label, val]) => grid.appendChild(h(`<div class="at-dash-card"><div class="at-dash-n">${_esc(val)}</div><div class="at-dash-l">${_esc(label)}</div></div>`)));
  host.appendChild(grid);
  host.insertAdjacentHTML("beforeend", `<div class="section-h" style="margin-top:18px">🧠 Leitura da IA <span class="card-sub">(resumo gerencial dummy)</span></div>`);
  host.insertAdjacentHTML("beforeend", `<div class="vp-card"><div class="vp-row"><span class="vp-v">Semana com conversão estável (55%), puxada por Escuna e City Tour. Instagram segue como maior origem de lead.</span></div><div class="vp-row"><span class="vp-k">Alerta</span><span class="vp-v">4 leads perdidos por preço — considerar condição especial em baixa demanda.</span></div><div class="vp-row"><span class="vp-k">Foco da semana</span><span class="vp-v">Reduzir tempo de resposta no WhatsApp e cobrar sinal pendente do grupo Bike + Praia.</span></div></div>`);
}

// ---------- Gates / Aprovações (visual) ----------
const AT_GATES = [
  { acao: "Gerar voucher", risco: "médio" }, { acao: "Enviar mensagem ao cliente", risco: "leve" },
  { acao: "Alterar valor da reserva", risco: "alto" }, { acao: "Confirmar pagamento", risco: "médio" },
  { acao: "Alterar status de reserva", risco: "médio" }, { acao: "Enviar pós-venda", risco: "leve" },
  { acao: "Aprovar pauta", risco: "leve" }, { acao: "Publicar conteúdo", risco: "alto" },
  { acao: "Rodar agente", risco: "alto" }, { acao: "Apagar dado", risco: "crítico" },
];
const AT_RISK_CLASS = { leve: "ok", médio: "warn", alto: "err", crítico: "err" };
function vpGates() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="banner">⚠️ Todas as ações abaixo exigem confirmação humana. Nesta fase, nenhum botão executa algo real.</div>`;
  AT_GATES.forEach((g) => {
    const row = h(`<div class="vp-item">
      <div class="vp-item-h">${_esc(g.acao)} <span class="badge ${AT_RISK_CLASS[g.risco] || "wait"}">risco ${_esc(g.risco)}</span></div>
      <div class="vp-item-meta">status: pendente de confirmação</div>
      <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap"></div>
    </div>`);
    const acts = row.querySelector("div:last-child");
    const bOk = h(`<button class="op-btn ok sm">Aprovar</button>`);
    bOk.onclick = () => vpVisualModal("✅ " + g.acao, `<p style="font-size:13px">Aprovaria a ação <b>${_esc(g.acao)}</b>.</p>`, { warn: "Sem execução real nesta fase." });
    const bNo = h(`<button class="op-btn no sm">Reprovar</button>`);
    bNo.onclick = () => vpVisualModal("❌ " + g.acao, `<p style="font-size:13px">Reprovaria a ação <b>${_esc(g.acao)}</b>.</p>`, { warn: "Sem execução real nesta fase." });
    acts.append(bOk, bNo);
    host.appendChild(row);
  });
}

function viewTarefas(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:16px">Visualização em tempo real do fluxo de execução</div>`));
  const dem = h(`<div class="demanda"><textarea id="dem-text" placeholder="Descreva o que você precisa..."></textarea><div style="text-align:right"><button class="btn ok" id="dem-run">⚡ Executar</button></div></div>`);
  body.appendChild(dem);
  dem.querySelector("#dem-run").onclick = async () => {
    const t = $("dem-text").value.trim(); if (!t) return;
    const log = h(`<div class="card" style="margin-bottom:16px"><div class="card-sub">Enviando ao orquestrador...</div></div>`);
    body.insertBefore(log, body.children[2]);
    if (!state.online) { log.querySelector(".card-sub").textContent = "Backend offline."; return; }
    try {
      const out = await tryJson(BACKEND + "chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: t, model: "claude-3-5-sonnet" }) });
      log.innerHTML = `<div class="meta-row"><span class="k">Intent</span><span class="v">${out.intent}</span></div><div class="meta-row"><span class="k">Brain</span><span class="v">${out.brain}</span></div><div class="card-desc" style="margin-top:10px">${out.response || ""}</div>`;
      try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); renderRightPanel(); } catch (_) {}
    } catch (e) { log.querySelector(".card-sub").textContent = "Falhou: " + e.message; }
  };

  // Rodar agente especialista (execução real via /agents/run — Claude assinatura)
  if (state.runnable.length) {
    body.appendChild(h(`<div class="section-h">Rodar agente especialista</div>`));
    const opts = state.runnable.map((a) => `<option value="${a.id}">${a.name || a.id}</option>`).join("");
    const rb = h(`<div class="demanda" style="max-width:640px">
      <select id="ag-sel" style="width:100%;background:var(--bg-2);border:1px solid var(--border);color:var(--text);padding:9px;border-radius:8px;margin-bottom:8px">${opts}</select>
      <textarea id="ag-task" placeholder="Tarefa para o agente..."></textarea>
      <div style="text-align:right"><button class="btn ok" id="ag-run">▶ Rodar agente</button></div>
    </div>`);
    body.appendChild(rb);
    rb.querySelector("#ag-run").onclick = async () => {
      const agent_id = $("ag-sel").value, task = $("ag-task").value.trim();
      if (!task) return;
      const out = h(`<div class="card" style="max-width:640px;margin-bottom:18px"><div class="card-sub">Executando ${agent_id}... (pode levar alguns segundos)</div></div>`);
      rb.after(out);
      if (!state.online) { out.querySelector(".card-sub").textContent = "Backend offline."; return; }
      try {
        const r = await tryJson(BACKEND + "agents/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent_id, task }) });
        out.innerHTML = `<div class="card-title" style="font-size:14px">${agent_id}</div><div class="card-desc" style="margin-top:8px;white-space:pre-wrap">${(r.message || r.response || JSON.stringify(r)).slice(0, 1200)}</div>`;
      } catch (e) { out.querySelector(".card-sub").textContent = "Falhou: " + e.message; }
    };
  }

  // Pulso de mercado (last30days) — o que estão falando, fontes grátis
  body.appendChild(h(`<div class="section-h">📡 Pulso de mercado</div>`));
  const pulso = h(`<div class="demanda" style="max-width:640px">
    <div class="card-sub" style="margin-bottom:8px">O que estão falando sobre um tópico agora (Reddit, YouTube, HackerNews, GitHub) → o Claude sintetiza com implicações pro negócio. Grátis.</div>
    <textarea id="pulso-topico" placeholder="Ex: turismo João Pessoa, passeio de barco, tendências Reels viagem"></textarea>
    <div style="text-align:right"><button class="btn ok" id="pulso-run">📡 Captar pulso</button></div>
  </div>`);
  body.appendChild(pulso);
  pulso.querySelector("#pulso-run").onclick = async () => {
    const t = $("pulso-topico").value.trim(); if (!t) return;
    const out = h(`<div class="card" style="max-width:640px;margin-bottom:18px"><div class="card-sub">Captando o pulso (consultando redes/fóruns + síntese)...</div></div>`);
    pulso.after(out);
    if (!state.online) { out.querySelector(".card-sub").textContent = "Backend offline."; return; }
    try {
      const r = await tryJson(BACKEND + "pulso", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ topico: t }) });
      out.innerHTML = `<div class="card-sub" style="margin-bottom:6px">📡 ${t} · ${r.fontes || 0} fonte(s)</div><div class="card-desc" style="white-space:pre-wrap">${(r.brief || r.message || "").slice(0, 2000)}</div>`;
    } catch (e) { out.querySelector(".card-sub").textContent = "Falhou: " + e.message; }
  };

  // Operar navegador (browser-use) — experimental, precisa modelo com visão
  body.appendChild(h(`<div class="section-h">🌐 Operar navegador (experimental)</div>`));
  const nav = h(`<div class="demanda" style="max-width:640px">
    <div class="card-sub" style="margin-bottom:8px">O Javes abre o Chrome e age como humano (ler/postar/preencher). Precisa de modelo com VISÃO em <code>BROWSER_USE_MODEL</code>. Comece com tarefa de LEITURA.</div>
    <textarea id="nav-task" placeholder="Ex: abra https://example.com e me diga o título da página"></textarea>
    <div style="text-align:right"><button class="btn ok" id="nav-run">🌐 Operar</button></div>
  </div>`);
  body.appendChild(nav);
  nav.querySelector("#nav-run").onclick = async () => {
    const t = $("nav-task").value.trim(); if (!t) return;
    const out = h(`<div class="card" style="max-width:640px;margin-bottom:18px"><div class="card-sub">Operando o navegador... (pode levar ~1 min)</div></div>`);
    nav.after(out);
    if (!state.online) { out.querySelector(".card-sub").textContent = "Backend offline."; return; }
    try {
      const r = await tryJson(BACKEND + "browser/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task: t }) });
      out.innerHTML = `<div class="card-desc" style="white-space:pre-wrap">${(r.result || r.message || JSON.stringify(r)).slice(0, 1500)}</div>`;
    } catch (e) { out.querySelector(".card-sub").textContent = "Falhou: " + e.message; }
  };

  // Workflows (lista)
  body.appendChild(h(`<div class="section-h">Workflows</div>`));
  WORKFLOW_LIST.forEach((w) => {
    body.appendChild(h(`<div class="wf-card"><div class="wf-main"><div class="wf-name">${w.nome}</div><div class="wf-desc">${w.desc}</div><div class="wf-meta">${w.steps} steps · demo</div></div><button class="btn ok" disabled title="Workflow de exemplo — ativação em fase futura">▶ Executar (em breve)</button></div>`));
  });

  // Grafo (demo)
  body.appendChild(h(`<div class="section-h" style="margin-top:20px">Fluxo (exemplo)</div>`));
  const flow = h(`<div class="flow"></div>`);
  WORKFLOW_NODES.forEach((n, i) => {
    flow.appendChild(h(`<div class="flow-node s-${sc(n.status)}"><div class="fn-type">${n.type}</div><div class="fn-name">${n.name}</div><span class="badge ${sc(n.status)}"><span class="dot ${sc(n.status)}"></span>${n.status}</span></div>`));
    if (i < WORKFLOW_NODES.length - 1) flow.appendChild(h(`<div class="flow-arrow">→</div>`));
  });
  body.appendChild(flow);
}

// ---------- Painel (dashboards) ----------
function viewPainel(body) {
  const sel = h(`<div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap;align-items:center"></div>`);
  state.projects.forEach((p) => {
    const t = h(`<div class="view-tab ${p.id === state.activeProjectId ? "active" : ""}">${p.nome}</div>`);
    t.onclick = () => { state.activeProjectId = p.id; renderCanvas(); };
    sel.appendChild(t);
  });
  // botão de sincronizar — útil quando o senhor edita o Cérebro Jampa
  const sync = h(`<button class="btn no" style="margin-left:auto" id="sync-rag">🔄 Sincronizar conhecimento</button>`);
  sync.onclick = async () => {
    sync.disabled = true; const orig = sync.textContent; sync.textContent = "Sincronizando…";
    if (!state.online) { sync.textContent = "Backend offline"; setTimeout(() => { sync.textContent = orig; sync.disabled = false; }, 2500); return; }
    try {
      const r = await tryJson(BACKEND + "knowledge/reindex", { method: "POST" });
      sync.textContent = `✓ ${(r && (r.arquivos_reindexados || r.status)) || "ok"}`;
    } catch (e) { sync.textContent = "Falhou"; }
    setTimeout(() => { sync.textContent = orig; sync.disabled = false; }, 4000);
  };
  sel.appendChild(sync);
  body.appendChild(sel);

  const man = state.manifests[state.activeProjectId];
  if (!man || !man.dashboards) { body.appendChild(h(`<div class="empty-state">Sem manifesto detalhado para <b>${projName(state.activeProjectId)}</b>.<br/>Dashboards completos disponíveis para Vem Passear Jampa.</div>`)); return; }
  const funil = man.dashboards.funil_vendas;
  if (funil) {
    body.appendChild(h(`<div class="section-h">${funil.titulo}</div>`));
    const f = h(`<div class="funnel" style="margin-bottom:24px"></div>`);
    (funil.etapas || []).forEach((e, i) => {
      const w = 100 - i * (60 / Math.max(1, funil.etapas.length));
      f.appendChild(h(`<div class="funnel-step"><div class="funnel-label">${e}</div><div class="funnel-bar" style="width:${w}%">—</div></div>`));
    });
    body.appendChild(f);
  }
  body.appendChild(h(`<div class="section-h">Indicadores</div>`));
  const grid = h(`<div class="grid cols-4"></div>`);
  Object.entries(man.dashboards).forEach(([key, d]) => {
    if (key === "funil_vendas") return;
    const val = d.total ?? d.valor ?? d.nota_media ?? d.nps;
    const empty = val === null || val === undefined;
    grid.appendChild(h(`<div class="kpi"><div class="kpi-label">${d.titulo || key}</div><div class="kpi-value ${empty ? "empty" : ""}">${empty ? "sem dados" : val}</div><div class="kpi-foot">${d.status || ""}</div></div>`));
  });
  body.appendChild(grid);
}

// ---------- Config ----------
function viewConfig(body) {
  const wrap = h(`<div class="cfg-wrap"></div>`);
  const menu = h(`<div></div>`);
  CFG_MENU.forEach((c) => {
    const it = h(`<div class="cfg-item ${c.id === state.cfgTab ? "active" : ""}"><div><div class="cfg-t">${c.t}</div><div class="cfg-d">${c.d}</div></div></div>`);
    it.onclick = () => { state.cfgTab = c.id; renderCanvas(); };
    menu.appendChild(it);
  });
  const panel = h(`<div></div>`);
  cfgPanel(panel);
  wrap.appendChild(menu); wrap.appendChild(panel);
  body.appendChild(wrap);
}

function cfgPanel(panel) {
  if (state.cfgTab === "memorias") {
    panel.appendChild(h(`<div class="section-h">Memórias — Knowledge por Agente</div>`));
    const total = state.skills.length;
    const grid = h(`<div class="grid cols-3" style="margin-bottom:18px"></div>`);
    [["Squads", state.squads.length], ["Agentes", state.agents.length], ["Skills/Arquivos", total]].forEach(([k, v]) =>
      grid.appendChild(h(`<div class="kpi"><div class="kpi-label">${k}</div><div class="kpi-value">${v}</div></div>`)));
    panel.appendChild(grid);
    panel.appendChild(h(`<div class="card-sub">Cada agente pode ter sua própria base de knowledge (skills, referências, contexto). As ${total} skills reais já estão indexadas em <code>_skills/</code>.</div>`));
  } else if (state.cfgTab === "scripts") {
    panel.appendChild(h(`<div class="section-h">Scripts do backend (${state.scripts.length})</div>`));
    const grid = h(`<div class="grid cols-2"></div>`);
    state.scripts.forEach((s) => {
      grid.appendChild(h(`<div class="card" style="padding:14px"><div class="card-title" style="font-size:13.5px">${s.arquivo}</div><div class="card-desc" style="margin:6px 0">${s.proposito || "—"}</div><div class="chips"><span class="chip">${s.funcoes} fn</span><span class="chip">${s.classes} cls</span></div></div>`));
    });
    panel.appendChild(grid);
  } else if (state.cfgTab === "mcp") {
    panel.appendChild(h(`<div class="section-h">MCP — tools que o Javes consome</div>`));
    if (!state.mcp.length) { panel.appendChild(h(`<div class="card-sub">Nenhum servidor MCP configurado (data/mcp_servers.json).</div>`)); }
    state.mcp.forEach((s) => {
      const card = h(`<div class="card" style="margin-bottom:10px"><div class="card-head"><div class="card-icon">🔌</div><div><div class="card-title">${s.id}</div><div class="card-sub">${s.descricao || s.command}</div></div><button class="btn no" style="margin-left:auto" id="mcp-${s.id}">Listar tools</button></div><div class="mcp-out card-sub" style="margin-top:8px"></div></div>`);
      card.querySelector(`#mcp-${s.id}`).onclick = async (e) => {
        const out = card.querySelector(".mcp-out"); e.target.disabled = true; out.textContent = "Conectando ao servidor MCP...";
        try {
          const r = await tryJson(`${BACKEND}mcp/${s.id}/tools`);
          if (r.error) out.textContent = "⚠️ " + r.error;
          else out.innerHTML = (r.tools || []).map((t) => `<div>🔧 <b>${t.name}</b> — ${t.description || ""}</div>`).join("") || "Sem tools.";
        } catch (err) { out.textContent = "Falhou: " + err.message; } finally { e.target.disabled = false; }
      };
      panel.appendChild(card);
    });
    panel.appendChild(h(`<div class="card-sub" style="margin-top:10px">Adicione servidores em <code>data/mcp_servers.json</code> (stdio: command + args). O Javes lista e chama as tools deles.</div>`));
  } else if (state.cfgTab === "integracoes") {
    panel.appendChild(h(`<div class="section-h">Integrações / Conectores</div>`));
    const labels = { youtube: "YouTube", google: "Google", canva: "Canva", spotify: "Spotify",
      openweather: "OpenWeather", telegram: "Telegram", elevenlabs: "ElevenLabs",
      whatsapp: "WhatsApp (OpenWA)", openai: "OpenAI (voz/transcrição)", claude_code: "Claude Code (execução)" };
    const ents = Object.entries(state.integrations);
    if (!ents.length) { panel.appendChild(h(`<div class="card-sub">Sem dados (backend offline?).</div>`)); }
    ents.forEach(([k, on]) => {
      panel.appendChild(h(`<div class="status-row"><span class="sr-label">${labels[k] || k}</span><span class="sr-val badge ${on ? "ok" : "wait"}"><span class="dot ${on ? "ok" : "wait"}"></span>${on ? "conectado" : "configurar"}</span></div>`));
    });
    panel.appendChild(h(`<div class="card-sub" style="margin-top:12px">Conectores "configurar" precisam de chave/URL no <code>.env</code>. WhatsApp/Meta não enviam nada sem sua autorização.</div>`));
  } else if (state.cfgTab === "categorias") {
    panel.appendChild(h(`<div class="section-h">Categorias & Squads</div>`));
    state.projects.forEach((p) => {
      const n = state.squads.filter((s) => s.projeto === p.id).length;
      panel.appendChild(h(`<div class="status-row"><span class="sr-label">${p.nome}</span><span class="sr-val">${n} squad(s)</span></div>`));
    });
  } else if (state.cfgTab === "apikeys") {
    panel.appendChild(h(`<div class="section-h">API Keys</div>`));
    (tele().status).forEach((s) => panel.appendChild(h(`<div class="status-row"><span class="sr-label">${s.label}</span><span class="sr-val badge ${s.cls}"><span class="dot ${s.cls}"></span>${s.val}</span></div>`)));
  } else if (state.cfgTab === "sobre") {
    panel.appendChild(h(`<div class="card"><div class="card-title">Javes Core Platform</div><div class="card-desc">v1.0.0 · Backend Python (FastAPI) + Chainlit + Command Center. Inspirado na lógica AIOS, sem copiar identidade.</div></div>`));
  } else {
    const c = CFG_MENU.find((x) => x.id === state.cfgTab);
    panel.appendChild(h(`<div class="empty-state"><b>${c.t}</b><br/>${c.d} — em construção.</div>`));
  }
}

// ---------- Painel direito (Atividade) ----------
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
/* ═══════════════════════════════════════════════════════════════════
   VOICE INFRA — Orb + Whisper + Wake Word + Voz sempre ativa + TTS
   Trazido do classic, adaptado pro Command Center.
   ═══════════════════════════════════════════════════════════════════ */

let _orbInst = null;
let _whisper = null;
let _autoWhi = null;
let _wakeWord = null;
let _currentAudio = null;
const _audioQueue = [];
let _audioPlaying = false;

function _esc(s) { return String(s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

class VoiceOrb {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.state = "idle";
    this.color = { r: 34, g: 211, b: 238 }; // var(--accent-2)
    this.level = 0; this._level = 0; this.flash = 0;
    this.wave = new Array(64).fill(0);
    this._stopped = false;
    this._resize();
    this._onResize = () => this._resize();
    window.addEventListener("resize", this._onResize);
    this._loop();
  }
  destroy() { this._stopped = true; window.removeEventListener("resize", this._onResize); }
  _resize() {
    const r = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.w = r.width || 360; this.h = r.height || 360;
    this.canvas.width = this.w * dpr; this.canvas.height = this.h * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  setState(state) {
    this.state = state;
    const stage = document.getElementById("orb-host");
    const lblS = document.getElementById("neural-state");
    const lblP = document.getElementById("neural-pulse-lbl");
    stage?.classList.remove("thinking", "conclave");
    if (state === "thinking") { this.color = { r: 34, g: 211, b: 238 }; stage?.classList.add("thinking"); if (lblS) lblS.textContent = "PROCESSANDO"; if (lblP) lblP.textContent = "raciocinando..."; }
    else if (state === "conclave") { this.color = { r: 168, g: 85, b: 247 }; stage?.classList.add("conclave"); if (lblS) lblS.textContent = "CONCLAVE"; if (lblP) lblP.textContent = "debate interno"; }
    else if (state === "listening") { this.color = { r: 34, g: 211, b: 238 }; if (lblS) lblS.textContent = "OUVINDO"; if (lblP) lblP.textContent = "fala que eu te escuto"; }
    else if (state === "speaking") { this.color = { r: 34, g: 211, b: 238 }; if (lblS) lblS.textContent = "FALANDO"; if (lblP) lblP.textContent = "transmitindo resposta"; }
    else { this.color = { r: 34, g: 211, b: 238 }; if (lblS) lblS.textContent = "ONLINE"; if (lblP) lblP.textContent = "aguardando comando"; }
  }
  setLevel(v) { this.level = Math.min(1, Math.max(0, v)); }
  fire() { this.flash = Math.min(1, this.flash + 0.5); }
  _loop() {
    if (this._stopped) return;
    const { ctx, w, h, color } = this;
    const cx = w / 2, cy = h / 2;
    const R = Math.min(w, h) * 0.34;
    const t = Date.now() / 1000;
    ctx.clearRect(0, 0, w, h);
    this._level += (this.level - this._level) * 0.2;
    this.flash *= 0.9;
    const active = this.state !== "idle";
    const energy = (active ? 0.5 : 0.18) + this._level * 0.9 + this.flash * 0.6;
    const C = (a) => `rgba(${color.r},${color.g},${color.b},${a})`;
    const halo = ctx.createRadialGradient(cx, cy, R * 0.4, cx, cy, R * 2.0);
    halo.addColorStop(0, C(0.10 + energy * 0.10)); halo.addColorStop(1, C(0));
    ctx.fillStyle = halo; ctx.fillRect(0, 0, w, h);
    const rings = [{ rad: R * 1.55, w: 1, sp: 0.25, span: 1.1, a: 0.18 }, { rad: R * 1.34, w: 1.5, sp: -0.4, span: 2.4, a: 0.30 }, { rad: R * 1.16, w: 1, sp: 0.6, span: 0.8, a: 0.22 }];
    rings.forEach((rg) => {
      ctx.strokeStyle = C(rg.a + energy * 0.15); ctx.lineWidth = rg.w;
      ctx.beginPath(); ctx.arc(cx, cy, rg.rad, t * rg.sp, t * rg.sp + rg.span); ctx.stroke();
      const ex = cx + Math.cos(t * rg.sp + rg.span) * rg.rad;
      const ey = cy + Math.sin(t * rg.sp + rg.span) * rg.rad;
      ctx.fillStyle = C(0.6); ctx.beginPath(); ctx.arc(ex, ey, 2, 0, Math.PI * 2); ctx.fill();
    });
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-t * 0.3);
    ctx.strokeStyle = C(0.12); ctx.setLineDash([2, 8]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(0, 0, R * 1.72, 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([]); ctx.restore();
    const N = this.wave.length;
    for (let i = 0; i < N; i++) {
      const target = active || this._level > 0.02 ? (Math.sin(t * 6 + i * 0.5) * 0.5 + 0.5) * (0.3 + this._level * 2 + this.flash) : 0;
      this.wave[i] += (target - this.wave[i]) * 0.25;
    }
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {
      const idx = i % N;
      const ang = (i / N) * Math.PI * 2 - Math.PI / 2;
      const amp = R * 0.9 + this.wave[idx] * R * 0.45;
      const x = cx + Math.cos(ang) * amp; const y = cy + Math.sin(ang) * amp;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath(); ctx.strokeStyle = C(0.5 + energy * 0.3); ctx.lineWidth = 1.5; ctx.stroke();
    const corePulse = 1 + Math.sin(t * 2) * 0.06 + this._level * 0.5 + this.flash * 0.3;
    const coreR = R * 0.5 * corePulse;
    const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
    core.addColorStop(0, C(0.55 + energy * 0.3)); core.addColorStop(0.5, C(0.18)); core.addColorStop(1, C(0));
    ctx.fillStyle = core; ctx.beginPath(); ctx.arc(cx, cy, coreR, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = C(0.85); ctx.beginPath(); ctx.arc(cx, cy, R * 0.06 * corePulse, 0, Math.PI * 2); ctx.fill();
    const pc = active ? 5 : 3;
    for (let i = 0; i < pc; i++) {
      const a = t * (0.5 + i * 0.2) + i * 2.4;
      const rr = R * (1.0 + 0.25 * Math.sin(t + i));
      const px = cx + Math.cos(a) * rr; const py = cy + Math.sin(a) * rr;
      ctx.fillStyle = C(0.7); ctx.beginPath(); ctx.arc(px, py, 1.6, 0, Math.PI * 2); ctx.fill();
    }
    requestAnimationFrame(() => this._loop());
  }
}

class WhisperRecorder {
  constructor() { this.recording = false; this.mediaRec = null; this.chunks = []; this.stream = null; }
  async toggle() { this.recording ? this._stop() : await this._start(); }
  async _start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunks = [];
      this.mediaRec = new MediaRecorder(this.stream);
      this.mediaRec.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
      this.mediaRec.start(150);
      this.recording = true;
      document.getElementById("mic-btn")?.classList.add("recording");
      document.getElementById("voice-status")?.classList.add("active");
      const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "gravando...";
    } catch (e) { console.warn("Mic error:", e); }
  }
  _stop() {
    if (!this.recording || !this.mediaRec) return;
    this.recording = false;
    document.getElementById("mic-btn")?.classList.remove("recording");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "transcrevendo...";
    this.mediaRec.onstop = async () => {
      const blob = new Blob(this.chunks, { type: this.mediaRec.mimeType || "audio/webm" });
      this.stream?.getTracks().forEach((t) => t.stop());
      document.getElementById("voice-status")?.classList.remove("active");
      if (blob.size < 500) { if (vi) vi.textContent = ""; return; }
      try {
        const fd = new FormData();
        fd.append("file", blob, "audio.webm");
        const res = await fetch(BACKEND + "transcribe", { method: "POST", body: fd });
        if (res.ok) {
          const data = await res.json();
          const text = (data.text || "").trim();
          if (text) sendVoiceMessage(text);
        }
      } catch (err) { console.warn("Whisper error:", err); }
      if (vi) vi.textContent = "";
    };
    this.mediaRec.stop();
  }
}

class AutoWhisperEngine {
  constructor() {
    this.active = false; this.recording = false; this.stream = null; this.mediaRec = null;
    this.chunks = []; this.analyser = null; this.silTimer = null; this.recStart = 0;
    this.THRESHOLD = 0.035; this.SILENCE_MS = 2200; this.MIN_REC_MS = 800; this.MIN_BLOB = 4000;
  }
  async enable() {
    this.active = true;
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new AudioContext();
    const src = ctx.createMediaStreamSource(this.stream);
    this.analyser = ctx.createAnalyser(); this.analyser.fftSize = 1024;
    src.connect(this.analyser);
    const vi = document.getElementById("voice-interim");
    if (vi) vi.textContent = "calibrando microfone...";
    const noiseLevel = await this._measureNoise(1200);
    this.THRESHOLD = Math.max(0.030, noiseLevel * 3.5);
    if (vi) vi.textContent = `pronto (noise=${noiseLevel.toFixed(4)})`;
    setTimeout(() => { if (this.active && vi) vi.textContent = "aguardando voz..."; }, 1200);
    this._loop();
    document.getElementById("voice-status")?.classList.add("active");
    _orbInst?.setState("listening");
  }
  disable() {
    this.active = false; clearTimeout(this.silTimer);
    if (this.recording && this.mediaRec?.state === "recording") this.mediaRec.stop();
    this.stream?.getTracks().forEach((t) => t.stop());
    document.getElementById("voice-status")?.classList.remove("active");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "";
    _orbInst?.setLevel(0); _orbInst?.setState("idle");
  }
  async _measureNoise(durationMs) {
    return new Promise((resolve) => {
      const samples = [];
      const interval = setInterval(() => {
        const buf = new Float32Array(this.analyser.fftSize);
        this.analyser.getFloatTimeDomainData(buf);
        samples.push(Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length));
      }, 50);
      setTimeout(() => { clearInterval(interval); resolve(samples.reduce((a, b) => a + b, 0) / (samples.length || 1)); }, durationMs);
    });
  }
  _loop() {
    if (!this.active) return;
    const buf = new Float32Array(this.analyser.fftSize);
    this.analyser.getFloatTimeDomainData(buf);
    const vol = Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length);
    _orbInst?.setLevel(Math.min(1, vol * 12));
    if (vol > this.THRESHOLD && !this.recording) this._startSeg();
    else if (vol <= this.THRESHOLD && this.recording && !this.silTimer) this.silTimer = setTimeout(() => this._stopSeg(), this.SILENCE_MS);
    else if (vol > this.THRESHOLD && this.silTimer) { clearTimeout(this.silTimer); this.silTimer = null; }
    requestAnimationFrame(() => this._loop());
  }
  _startSeg() {
    this.recording = true; this.chunks = []; this.recStart = Date.now();
    this.mediaRec = new MediaRecorder(this.stream);
    this.mediaRec.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
    this.mediaRec.start(100);
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "ouvindo...";
  }
  _stopSeg() {
    this.recording = false; this.silTimer = null;
    if (!this.mediaRec || this.mediaRec.state !== "recording") return;
    const elapsed = Date.now() - this.recStart;
    this.mediaRec.onstop = async () => {
      const blob = new Blob(this.chunks, { type: this.mediaRec.mimeType || "audio/webm" });
      const vi = document.getElementById("voice-interim");
      if (elapsed < this.MIN_REC_MS || blob.size < this.MIN_BLOB) { if (this.active && vi) vi.textContent = "aguardando voz..."; return; }
      if (vi) vi.textContent = "transcrevendo...";
      try {
        const fd = new FormData(); fd.append("file", blob, "audio.webm");
        const res = await fetch(BACKEND + "transcribe", { method: "POST", body: fd });
        if (res.ok) {
          const data = await res.json();
          const text = (data.text || "").trim();
          const WHISPER_NOISE = /^(obrigado\.?|thanks\.?|thank you\.?|\.{2,}|música\.?|music\.?|legendas?\.?|subtitles?\.?|silence\.?|silêncio\.?|som de fundo\.?|background\.?|applause\.?|aplauso\.?|ruído\.?|noise\.?|beep\.?|bip\.?)$/i;
          const isNoise = !text || text.length < 4 || WHISPER_NOISE.test(text.trim()) || (text.length < 8 && /^[.,!?…\s]+$/.test(text));
          if (!isNoise) sendVoiceMessage(text);
        }
      } catch (err) { console.warn("Auto whisper error:", err); }
      if (this.active && vi) vi.textContent = "aguardando voz...";
    };
    this.mediaRec.stop();
  }
}

class WakeWordEngine {
  constructor() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.supported = !!SR; this.SR = SR;
    this.active = false; this.awoken = false; this.awokenTimer = null; this.rec = null;
    this.wakeRe = /\b(jamba|jamb[aá]|jambo|jambar|jarvis|j[aá]vis)\b/i;
  }
  toggle() {
    const vi = document.getElementById("voice-interim");
    if (!this.supported) { if (vi) vi.textContent = "wake word precisa do Chrome/Edge"; return; }
    this.active ? this.disable() : this.enable();
  }
  enable() {
    if (_autoWhi?.active) { _autoWhi.disable(); document.getElementById("voice-auto-btn")?.classList.remove("active"); }
    this.active = true;
    document.getElementById("wake-btn")?.classList.add("active");
    document.getElementById("voice-status")?.classList.add("active");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = 'diga "Javis" para ativar...';
    _orbInst?.setState("listening");
    this._build(); this._start();
  }
  disable() {
    this.active = false; clearTimeout(this.awokenTimer); this.awoken = false;
    document.getElementById("wake-btn")?.classList.remove("active");
    document.getElementById("voice-status")?.classList.remove("active");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "";
    _orbInst?.setState("idle");
    try { this.rec?.stop(); } catch (e) {}
  }
  _build() {
    this.rec = new this.SR();
    this.rec.lang = "pt-BR"; this.rec.continuous = true; this.rec.interimResults = true;
    this.rec.onresult = (e) => this._onResult(e);
    this.rec.onend = () => { if (this.active) { try { this.rec.start(); } catch (e) {} } };
    this.rec.onerror = (e) => { if (e.error === "not-allowed") this.disable(); };
  }
  _start() { try { this.rec.start(); } catch (e) {} }
  _onResult(e) {
    let finalText = "";
    for (let i = e.resultIndex; i < e.results.length; i++) if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
    finalText = finalText.trim();
    if (!finalText) return;
    const lower = finalText.toLowerCase();
    const m = lower.match(this.wakeRe);
    const vi = document.getElementById("voice-interim");
    if (m) {
      _orbInst?.setState("listening"); _orbInst?.fire?.();
      const idx = lower.indexOf(m[0]) + m[0].length;
      const after = finalText.slice(idx).replace(/^[,.\s]+/, "").trim();
      if (after) { this._send(after); }
      else {
        this.awoken = true;
        if (vi) vi.textContent = "pode falar, senhor...";
        clearTimeout(this.awokenTimer);
        this.awokenTimer = setTimeout(() => {
          this.awoken = false;
          if (this.active && vi) vi.textContent = 'diga "Javis" para ativar...';
        }, 6000);
      }
    } else if (this.awoken) {
      this.awoken = false; clearTimeout(this.awokenTimer);
      this._send(finalText);
    }
  }
  _send(cmd) {
    if (!cmd) return;
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "";
    sendVoiceMessage(cmd);
    if (this.active && vi) setTimeout(() => { if (this.active && vi) vi.textContent = 'diga "Javis" para ativar...'; }, 1500);
  }
}

function appendVoiceMsg(role, text) {
  const scroll = document.getElementById("chat-scroll");
  if (!scroll) return null;
  const el = h(`<div class="chat-msg ${role}">${_esc(text)}</div>`);
  scroll.appendChild(el);
  scroll.scrollTop = scroll.scrollHeight;
  return el;
}

async function sendVoiceMessage(text) {
  if (!text) return;
  const a = activeAgent();
  state.chats[a.id] = state.chats[a.id] || [];
  state.chats[a.id].push({ role: "user", text: `🎤 ${text}` });
  appendVoiceMsg("user", `🎤 ${text}`);
  const typing = appendVoiceMsg("bot", "…");
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
  _audioQueue.length = 0; _audioPlaying = false;
  _orbInst?.setState("thinking");

  if (!state.online) { if (typing) typing.textContent = "Backend offline."; _orbInst?.setState("idle"); return; }

  try {
    const res = await fetch(BACKEND + "voice/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: text, model: "", use_conclave: state.useConclave, tts: state.useTts }),
    });
    if (!res.ok) { if (typing) typing.textContent = "Falha: " + res.status; _orbInst?.setState("idle"); return; }
    const reader = res.body.getReader(); const dec = new TextDecoder();
    let buf = "", fullText = "", done = false;
    while (!done) {
      const { done: d, value } = await reader.read();
      if (d) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n"); buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") { done = true; break; }
        let evt; try { evt = JSON.parse(raw); } catch (_) { continue; }
        if (evt.type === "audio") { enqueueAudio(evt.b64); if (evt.sentence) fullText += (fullText ? " " : "") + evt.sentence; }
        else if (evt.type === "tts_text") { speak(evt.text); fullText = evt.text; }
        else if (evt.type === "token") { fullText += evt.text; }
        else if (evt.type === "meta" && evt.text) { fullText = evt.text; }
        else if (evt.type === "done") { if (evt.text) fullText = evt.text; }
        if (typing) typing.textContent = fullText || "…";
      }
    }
    if (fullText) state.chats[a.id].push({ role: "bot", text: fullText });
    state.lastBrain = state.lastBrain || "main";
    try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); renderRightPanel(); } catch (_) {}
  } catch (e) {
    if (typing) typing.textContent = "Erro: " + e.message;
  } finally {
    if (!_audioPlaying) _orbInst?.setState("idle");
  }
}

function enqueueAudio(b64) {
  const bytes = atob(b64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const blob = new Blob([arr], { type: "audio/mpeg" });
  _audioQueue.push(URL.createObjectURL(blob));
  _drainAudioQueue();
}

function _drainAudioQueue() {
  if (_audioPlaying || _audioQueue.length === 0) return;
  _audioPlaying = true;
  const url = _audioQueue.shift();
  _currentAudio = new Audio(url);
  _orbInst?.setState("speaking");
  _currentAudio.onended = () => {
    URL.revokeObjectURL(url); _currentAudio = null; _audioPlaying = false;
    if (_audioQueue.length > 0) _drainAudioQueue();
    else _orbInst?.setState("idle");
  };
  _currentAudio.play().catch(() => { _audioPlaying = false; });
}

function cleanForSpeech(text) {
  return String(text || "")
    .replace(/```[\s\S]*?```/g, " ").replace(/`[^`]*`/g, " ")
    .replace(/\[[^\]]*\]\([^)]*\)/g, "").replace(/https?:\/\/\S+/g, "")
    .replace(/\[[^\]]*\.(md|txt|py|js|json)\]/gi, "").replace(/<[^>]+>/g, "")
    .replace(/[*_#>`~|]/g, "").replace(/^\s*\d+[\.\)]\s*/gm, "").replace(/^\s*[-•]\s*/gm, "")
    .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}]/gu, "")
    .replace(/\s+/g, " ").trim().substring(0, 600);
}

async function speak(text) {
  if (!text) return;
  const clean = cleanForSpeech(text);
  if (!clean) return;
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  try {
    const res = await fetch(BACKEND + "tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: clean }) });
    if (res.ok) {
      const blob = await res.blob(); const url = URL.createObjectURL(blob);
      _currentAudio = new Audio(url);
      _currentAudio.onended = () => { URL.revokeObjectURL(url); _currentAudio = null; };
      _currentAudio.play(); return;
    }
  } catch (_) {}
  if (!window.speechSynthesis) return;
  const utt = new SpeechSynthesisUtterance(clean);
  utt.lang = "pt-BR"; utt.rate = 1.0; utt.pitch = 1.0;
  _orbInst?.setState("speaking");
  utt.onboundary = (e) => { const intensity = Math.min(1, (e.charLength || 4) / 12); _orbInst?.setLevel(0.3 + intensity * 0.7); };
  utt.onend = () => { _orbInst?.setLevel(0); _orbInst?.setState("idle"); };
  window.speechSynthesis.speak(utt);
}

function initVoiceStage() {
  const canvas = document.getElementById("orb-canvas");
  if (!canvas) return;
  if (_orbInst) { _orbInst.destroy(); _orbInst = null; }
  if (_autoWhi?.active) _autoWhi.disable();
  if (_wakeWord?.active) _wakeWord.disable();
  _orbInst = new VoiceOrb(canvas);
  _whisper = _whisper || new WhisperRecorder();
  _autoWhi = _autoWhi || new AutoWhisperEngine();
  _wakeWord = _wakeWord || new WakeWordEngine();
  document.getElementById("mic-btn")?.addEventListener("click", () => _whisper.toggle());
  document.getElementById("wake-btn")?.addEventListener("click", () => _wakeWord.toggle());
  document.getElementById("voice-auto-btn")?.addEventListener("click", async () => {
    const btn = document.getElementById("voice-auto-btn");
    if (_autoWhi.active) { _autoWhi.disable(); btn?.classList.remove("active"); }
    else { if (_wakeWord.active) _wakeWord.disable(); try { await _autoWhi.enable(); btn?.classList.add("active"); } catch (e) { console.warn("auto whisper enable failed:", e); } }
  });
  const tts = document.getElementById("use-tts"); if (tts) tts.onchange = (e) => { state.useTts = e.target.checked; };
  const cc = document.getElementById("use-conclave"); if (cc) cc.onchange = (e) => { state.useConclave = e.target.checked; };
}

function viewExec(body) {
  let lastCount = 0;
  const wrap = h(`<div class="exec-view">
    <div class="exec-header">
      <div class="exec-header-left">
        <span id="exec-badge" class="exec-badge">OCIOSO</span>
        <span id="exec-task" class="exec-task-name">—</span>
      </div>
      <div class="exec-header-right">
        <span id="exec-elapsed" class="exec-elapsed"></span>
        <button class="exec-clear-btn" id="exec-clear">Limpar log</button>
      </div>
    </div>
    <div id="exec-term" class="exec-terminal"><div class="exec-hint">Aguardando execução... Peça ao Javes para "programar", "analisar" ou "criar" algo e acompanhe aqui em tempo real.</div></div>
  </div>`);
  body.appendChild(wrap);

  const badge = document.getElementById("exec-badge");
  const taskEl = document.getElementById("exec-task");
  const elapsedEl = document.getElementById("exec-elapsed");
  const term = document.getElementById("exec-term");
  document.getElementById("exec-clear").onclick = () => { term.innerHTML = ""; lastCount = 0; };

  async function poll() {
    try {
      const s = await tryJson(BACKEND + "exec/status");
      const running = s.running;
      badge.textContent = running ? "RODANDO" : (s.exit_code === 0 ? "CONCLUÍDO" : s.exit_code !== null ? "ERRO" : "OCIOSO");
      badge.className = "exec-badge" + (running ? " exec-running" : s.exit_code === 0 ? " exec-done" : s.exit_code !== null ? " exec-err" : "");
      taskEl.textContent = s.task || "—";
      if (s.started_at && running) {
        const sec = Math.round(Date.now() / 1000 - s.started_at);
        elapsedEl.textContent = sec >= 60 ? `${Math.floor(sec/60)}m ${sec%60}s` : `${sec}s`;
      } else { elapsedEl.textContent = ""; }
      const lines = s.lines || [];
      if (lines.length > lastCount) {
        if (lastCount === 0) term.innerHTML = "";
        lines.slice(lastCount).forEach((ln) => {
          const el = document.createElement("div");
          el.className = "exec-line" + (ln.startsWith("[") ? " exec-line-meta" : "");
          el.textContent = ln || " ";
          term.appendChild(el);
        });
        lastCount = lines.length;
        term.scrollTop = term.scrollHeight;
      }
    } catch (_) {}
  }

  poll();
  window._execPollTimer = setInterval(poll, 1500);
}

function renderAll() { renderSidebar(); renderCanvas(); renderRightPanel(); }

["sb-search", "tb-search"].forEach((id) => {
  document.addEventListener("input", (e) => { if (e.target.id === id) { state.q = e.target.value; renderSidebar(); renderCanvas(); } });
});

(async function init() {
  const ok = await loadData();
  if (!ok) { $("canvas-body").innerHTML = `<div class="banner">⚠️ Sirva por HTTP: <code>python -m http.server 8080</code> e abra <code>http://localhost:8080/frontend/command-center/index.html</code>, ou rode o backend em :8000.</div>`; return; }
  renderAll();
})();
