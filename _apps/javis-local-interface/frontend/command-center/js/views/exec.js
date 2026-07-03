// Execução — telemetria em tempo real — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, BACKEND, tryJson } from "../../app.js";

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

export { viewExec };
