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
};

const NAV = [
  { id: "chat",    label: "Chat",    icon: ICONS.chat },
  { id: "exec",    label: "Execução", icon: ICONS.exec },
  { id: "world",   label: "World",   icon: ICONS.world },
  { id: "tarefas", label: "Tarefas", icon: ICONS.tasks },
  { id: "painel",  label: "Painel",  icon: ICONS.panel },
  { id: "treino",  label: "Treino",  icon: ICONS.train },
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
const TITLES = { chat: "Chat", exec: "Execução em Tempo Real", world: "Javis World", tarefas: "Orquestrador de Tarefas", painel: "Painel", treino: "Treinamento", config: "Configurações" };
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
  ({ chat: viewChat, exec: viewExec, world: viewWorld, tarefas: viewTarefas, painel: viewPainel, treino: viewTreino, config: viewConfig }[state.view] || viewChat)(body);
}

function viewTreino(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:16px">Pipeline: <b>_entrada</b> (vídeos/repos/PDFs, coletados ou manuais) → resumo no <b>NotebookLM</b> → <b>_resumos</b> entra na base RAG do Javis.</div>`));
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
  body.appendChild(h(`<div class="card-sub" style="margin-top:18px">💡 <b>NotebookLM</b> é o passo de resumo (manual — sem API pública): suba o material do <code>_entrada</code>, gere o resumo e cole em <code>_resumos</code>. O Javis indexa automático no RAG.</div>`));
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
      <div class="brand-bar">JAVIS</div>
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
  hist.forEach((m) => scroll.appendChild(h(`<div class="chat-msg ${m.role}">${m.text}</div>`)));
  chatBlock.appendChild(scroll);

  const input = h(`
    <div class="chat-input">
      <textarea id="chat-text" placeholder="Mensagem para ${a.nome}... (ou clica no 🎤 acima)"></textarea>
      <button class="send-btn" id="chat-send" title="Enviar">➤</button>
    </div>`);
  chatBlock.appendChild(input);
  body.appendChild(chatBlock);

  const send = () => sendChat(a);
  input.querySelector("#chat-send").onclick = send;
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

async function sendChat(a, explicitMsg, speak) {
  const ta = $("chat-text");
  const msg = ((explicitMsg != null ? explicitMsg : (ta ? ta.value : "")) || "").trim();
  if (!msg) return;
  const hist = state.chats[a.id] = state.chats[a.id] || [];
  hist.push({ role: "user", text: msg });
  const scroll = $("chat-scroll");
  scroll.appendChild(h(`<div class="chat-msg user">${msg}</div>`));
  if (ta && explicitMsg == null) ta.value = "";
  const thinking = h(`<div class="chat-msg bot">…</div>`);
  scroll.appendChild(thinking); scroll.scrollTop = scroll.scrollHeight;

  if (!state.online) { thinking.textContent = "Backend offline — suba o server.py para conversar de verdade, senhor."; hist.push({ role: "bot", text: thinking.textContent }); return; }
  try {
    const out = await tryJson(BACKEND + "chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, model: "claude-3-5-sonnet" }),
    });
    const resp = out.response || out.message || "Pronto, senhor.";
    thinking.textContent = resp;
    hist.push({ role: "bot", text: resp });
    state.lastBrain = out.brain || state.lastBrain;
    state.lastTools = (out.tools && out.tools.length) ? out.tools.join(", ") : (out.intent || state.lastTools);
    if (speak) speakText(resp);
    try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); renderRightPanel(); } catch (_) {}
  } catch (e) {
    thinking.textContent = "Falhou: " + e.message;
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
  body.appendChild(h(`<div class="section-h">Javis World — mapa de setores e agentes</div>`));
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
    <div class="card-sub" style="margin-bottom:8px">O Javis abre o Chrome e age como humano (ler/postar/preencher). Precisa de modelo com VISÃO em <code>BROWSER_USE_MODEL</code>. Comece com tarefa de LEITURA.</div>
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
    body.appendChild(h(`<div class="wf-card"><div class="wf-main"><div class="wf-name">${w.nome}</div><div class="wf-desc">${w.desc}</div><div class="wf-meta">${w.steps} steps · trigger manual · active</div></div><button class="btn ok">▶ Executar</button></div>`));
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
    panel.appendChild(h(`<div class="section-h">MCP — tools que o Javis consome</div>`));
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
    panel.appendChild(h(`<div class="card-sub" style="margin-top:10px">Adicione servidores em <code>data/mcp_servers.json</code> (stdio: command + args). O Javis lista e chama as tools deles.</div>`));
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
    panel.appendChild(h(`<div class="card"><div class="card-title">JAVIS Core Platform</div><div class="card-desc">v1.0.0 · Backend Python (FastAPI) + Chainlit + Command Center. Inspirado na lógica AIOS, sem copiar identidade.</div></div>`));
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
    <div id="exec-term" class="exec-terminal"><div class="exec-hint">Aguardando execução... Peça ao Javis para "programar", "analisar" ou "criar" algo e acompanhe aqui em tempo real.</div></div>
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
