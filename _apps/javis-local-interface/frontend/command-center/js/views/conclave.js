// Conclave — debate multi-agente — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, $, state, BACKEND, _esc } from "../../app.js";

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

export { viewConclave };
