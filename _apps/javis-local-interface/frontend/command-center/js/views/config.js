// Config — painéis de configuração — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, state, BACKEND, tryJson, tele, renderCanvas } from "../../app.js";

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
    // Memória persistente do Javes (decisões/aprendizados do Conclave) — GET /memory
    panel.appendChild(h(`<div class="section-h" style="margin-top:18px">🧠 Memória do Javes (decisões & aprendizados)</div>`));
    const mrow = h(`<div class="demanda" style="max-width:640px">
      <input id="mem-q" class="cs-input" style="width:100%;margin-bottom:8px" placeholder="buscar na memória… (vazio = decisões recentes)" />
      <div style="text-align:right"><button class="btn ok" id="mem-go">🔎 Buscar</button></div>
      <div class="mem-out card-sub" style="margin-top:8px;white-space:pre-wrap"></div>
    </div>`);
    panel.appendChild(mrow);
    const runMem = async () => {
      const q = (mrow.querySelector("#mem-q").value || "").trim();
      const out = mrow.querySelector(".mem-out"); out.textContent = "buscando…";
      try { const d = await tryJson(BACKEND + "memory" + (q ? "?q=" + encodeURIComponent(q) : "")); out.textContent = (d.results || "").trim() || "Nada na memória ainda."; }
      catch (e) { out.textContent = "Não consegui buscar na memória (backend offline?)."; }
    };
    mrow.querySelector("#mem-go").onclick = runMem;
    mrow.querySelector("#mem-q").addEventListener("keydown", (e) => { if (e.key === "Enter") runMem(); });
    runMem();
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
  } else if (state.cfgTab === "perfil") {
    panel.appendChild(h(`<div class="section-h">Perfil — o que o Javes sabe sobre você</div>`));
    const box = h(`<div id="cfg-perfil"><div class="card-sub">Carregando fatos…</div></div>`);
    panel.appendChild(box);
    tryJson(BACKEND + "profile").then((d) => {
      if (state.cfgTab !== "perfil") return;
      const facts = d.facts || [];
      if (!facts.length) { box.innerHTML = `<div class="op-empty">Nenhum fato registrado ainda. O Javes aprende sobre você conversando.</div>`; return; }
      box.innerHTML = "";
      facts.forEach((f) => { const row = h(`<div class="status-row"><span class="sr-label"></span></div>`); row.querySelector(".sr-label").textContent = "• " + f; box.appendChild(row); });
    }).catch(() => { box.innerHTML = `<div class="card-sub">Não consegui carregar o perfil (backend offline?).</div>`; });
  } else if (state.cfgTab === "sobre") {
    panel.appendChild(h(`<div class="card"><div class="card-title">Javes Core Platform</div><div class="card-desc">v1.0.0 · Backend Python (FastAPI) + Chainlit + Command Center. Inspirado na lógica AIOS, sem copiar identidade.</div></div>`));
  } else {
    const c = CFG_MENU.find((x) => x.id === state.cfgTab);
    panel.appendChild(h(`<div class="empty-state"><b>${c.t}</b><br/>${c.d} — em construção.</div>`));
  }
}

export { viewConfig };
