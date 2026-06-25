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
};

const NAV = [
  { id: "chat",    label: "Chat",    icon: ICONS.chat },
  { id: "world",   label: "World",   icon: ICONS.world },
  { id: "tarefas", label: "Tarefas", icon: ICONS.tasks },
  { id: "painel",  label: "Painel",  icon: ICONS.panel },
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
  integrations: {}, runnable: [],
  telemetry: null, online: false,
  view: "chat", q: "",
  activeAgentId: null, rpTab: "status",
  lastBrain: null, lastTools: null,
  chats: {}, // por agente: [{role, text}]
  activeProjectId: "vempassear",
  cfgTab: "memorias",
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

  // Orchestrators / Masters / Specialists
  fillAgentGroup("nav-orchestrators", state.agents.filter((a) => a.tipo === "orquestrador" && matchQ(a.nome)));
  fillAgentGroup("nav-masters", state.agents.filter((a) => (a.tags || []).includes("Master") && matchQ(a.nome)));
  fillAgentGroup("nav-specialists", state.agents.filter((a) => a.tipo === "especialista" && matchQ(a.nome)));
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
const TITLES = { chat: "Chat", world: "Javis World", tarefas: "Orquestrador de Tarefas", painel: "Painel", config: "Configurações" };
function setView(v) { state.view = v; renderSidebar(); renderCanvas(); renderRightPanel(); }
function renderCanvas() {
  const body = $("canvas-body"); body.innerHTML = "";
  if ((state.q || "").trim()) {
    $("canvas-title").textContent = `Busca: "${state.q}"`;
    return viewSearch(body);
  }
  $("canvas-title").textContent = TITLES[state.view] || "";
  ({ chat: viewChat, world: viewWorld, tarefas: viewTarefas, painel: viewPainel, config: viewConfig }[state.view] || viewChat)(body);
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
  body.appendChild(h(`
    <div class="agent-hero">
      <div class="ah-avatar">${(a.nome || "?")[0]}</div>
      <div><div class="ah-name">${a.nome || "Agente"} <span class="chip accent">${a.tipo || ""}</span></div>
      <div class="ah-role">${a.descricao || ""}</div></div>
    </div>`));

  // Habilidades
  const sk = agentSkills(a);
  const SKILL_COLORS = [
    "linear-gradient(90deg,#f59e0b,#fbbf24)",
    "linear-gradient(90deg,#8b5cf6,#a78bfa)",
    "linear-gradient(90deg,#3b82f6,#60a5fa)",
    "linear-gradient(90deg,#22c55e,#4ade80)",
    "linear-gradient(90deg,#ec4899,#f472b6)",
  ];
  const box = h(`<div class="skills-box"><h4>★ Habilidades</h4></div>`);
  sk.forEach((s, i) => {
    const p = pct(s.id);
    box.appendChild(h(`<div class="skill-row"><div class="sr-top"><span>${s.nome}</span><span class="sr-pct">${p}%</span></div><div class="skill-bar"><div class="skill-fill" style="width:${p}%;background:${SKILL_COLORS[i % SKILL_COLORS.length]}"></div></div></div>`));
  });
  body.appendChild(box);

  // Sugestões
  body.appendChild(h(`<div style="font-size:12px;color:var(--muted);margin-bottom:10px">💡 O que posso fazer por você</div>`));
  const sug = h(`<div class="cmd-suggest"></div>`);
  CMD_SUGGEST.forEach((c) => {
    const it = h(`<div class="cmd-item"><div class="ci-name">${c.name}</div><div class="ci-desc">${c.desc}</div></div>`);
    it.onclick = () => { $("chat-text").value = c.name.replace(/^[^ ]+ /, "") + ": "; $("chat-text").focus(); };
    sug.appendChild(it);
  });
  body.appendChild(sug);

  // Histórico + input
  const hist = state.chats[a.id] || [];
  const scroll = h(`<div class="chat-scroll" id="chat-scroll"></div>`);
  hist.forEach((m) => scroll.appendChild(h(`<div class="chat-msg ${m.role}">${m.text}</div>`)));
  body.appendChild(scroll);

  const input = h(`
    <div class="chat-input">
      <textarea id="chat-text" placeholder="Mensagem para ${a.nome}... (ou 🎙️ pra falar)"></textarea>
      <button class="send-btn mic-btn" id="chat-mic" title="Falar com o Javis">🎙️</button>
      <button class="send-btn" id="chat-send" title="Enviar">➤</button>
    </div>`);
  body.appendChild(input);
  const send = () => sendChat(a);
  input.querySelector("#chat-send").onclick = send;
  input.querySelector("#chat-mic").onclick = (e) => toggleVoice(a, e.currentTarget);
  input.querySelector("#chat-text").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
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
  const sel = h(`<div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap"></div>`);
  state.projects.forEach((p) => {
    const t = h(`<div class="view-tab ${p.id === state.activeProjectId ? "active" : ""}">${p.nome}</div>`);
    t.onclick = () => { state.activeProjectId = p.id; renderCanvas(); };
    sel.appendChild(t);
  });
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
function renderAll() { renderSidebar(); renderCanvas(); renderRightPanel(); }

["sb-search", "tb-search"].forEach((id) => {
  document.addEventListener("input", (e) => { if (e.target.id === id) { state.q = e.target.value; renderSidebar(); renderCanvas(); } });
});

(async function init() {
  const ok = await loadData();
  if (!ok) { $("canvas-body").innerHTML = `<div class="banner">⚠️ Sirva por HTTP: <code>python -m http.server 8080</code> e abra <code>http://localhost:8080/frontend/command-center/index.html</code>, ou rode o backend em :8000.</div>`; return; }
  renderAll();
})();
