// Tarefas — orquestrador de demandas — extraído de app.js em 2026-07-03; módulo ES.
// 2026-07-03: seções demo (Workflows/Fluxo de exemplo) removidas — minimalismo.
// Ficam as 4 ferramentas reais: demanda, agente, pulso, navegador.
import { h, $, state, BACKEND, tryJson, renderRightPanel } from "../../app.js";

function viewTarefas(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:16px">Ferramentas de execução — demanda ao orquestrador, agente especialista, pulso de mercado e navegador.</div>`));
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
}

export { viewTarefas };
