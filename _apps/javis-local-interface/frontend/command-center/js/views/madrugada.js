// Modo Madrugada — R4.5. Painel READ-ONLY do preflight + kill switch.
// Deliberadamente NÃO há botão de "executar": rodar a Madrugada (execução
// desassistida de código) continua só no CLI, por princípio — um processo que
// roda código sozinho merece ser explícito, não um clique. Aqui a UI só mostra
// o estado e oferece o desarmar (a direção segura).
import { h, $, BACKEND, tryJson, withLocalAuth } from "../../app.js";

function viewMadrugada(body) {
  body.appendChild(h(`<div class="exec-view">
    <div class="exec-header">
      <div class="exec-header-left">
        <span class="exec-badge">MADRUGADA</span>
        <span class="exec-task-name">Execução desassistida de UMA task já aprovada</span>
      </div>
      <div class="exec-header-right">
        <button class="exec-clear-btn" id="mad-refresh">Atualizar</button>
      </div>
    </div>
    <div class="card-sub" id="mad-flag">Carregando status da Madrugada…</div>
    <div id="mad-panel" class="op-board"><div class="card-sub">Carregando preflight…</div></div>
    <div class="exec-hint" style="margin-top:12px">
      Rodar a Madrugada é só pelo CLI, por design:
      <code>python scripts/javes_madrugada.py run --confirm "ARMAR MADRUGADA"</code>.
      Aqui você acompanha o estado e pode <b>desarmar</b> a qualquer momento.
    </div>
  </div>`));

  $("mad-refresh").onclick = () => loadMadrugada();
  loadMadrugada();
  window._execPollTimer = setInterval(loadMadrugada, 5000);
}

async function loadMadrugada() {
  const panel = $("mad-panel");
  if (!panel) return;
  try {
    const data = await tryJson(`${BACKEND}madrugada/status`);
    renderPanel(data);
  } catch (_) {
    panel.innerHTML = `<div class="card-sub">Não consegui carregar o status da Madrugada.</div>`;
  }
}

function renderPanel(data) {
  const flag = $("mad-flag");
  const panel = $("mad-panel");
  if (!panel) return;

  const enabled = data.night_mode_enabled === true;
  const pf = data.preflight || {};
  if (flag) {
    flag.textContent = enabled
      ? "JAVIS_ENABLE_NIGHT_MODE=True — Madrugada habilitada (exige os 3 flags para rodar)."
      : "JAVIS_ENABLE_NIGHT_MODE=False — Madrugada desligada por padrão.";
  }

  panel.innerHTML = "";
  const ready = pf.status === "ready";
  const killed = pf.kill_switch_active === true;

  const rows = [
    ["Estado", ready ? "PRONTA" : "bloqueada", ready ? "ok" : "wait"],
    ["Motivo", pf.reason || "—", pf.reason ? "warn" : "ok"],
    ["Janela", pf.window || "—", "ok"],
    ["Dentro da janela", pf.inside_window ? "sim" : "não", pf.inside_window ? "ok" : "wait"],
    ["Kill switch", killed ? "ATIVO (desarmada)" : "inativo", killed ? "err" : "ok"],
    ["Tasks aprovadas", String(pf.approved_tasks ?? 0), "ok"],
    ["Task alvo", pf.task_id || "—", "ok"],
  ];

  const card = h(`<div class="op-card"><div class="op-card-title">Preflight</div></div>`);
  rows.forEach(([k, v, cls]) => {
    const row = h(`<div class="status-row"><span class="sr-label"></span><span class="sr-val badge ${cls}"><span class="dot ${cls}"></span></span></div>`);
    row.querySelector(".sr-label").textContent = k;
    row.querySelector(".sr-val").appendChild(document.createTextNode(v));
    card.appendChild(row);
  });

  const actions = h(`<div class="op-ap-actions" style="margin-top:10px"></div>`);
  if (killed) {
    addBtn(actions, "Rearmar (remover kill switch)", () => setKillSwitch(true));
  } else {
    addBtn(actions, "Desarmar a Madrugada", () => setKillSwitch(false));
  }
  card.appendChild(actions);
  panel.appendChild(card);
}

function addBtn(box, label, onClick) {
  const btn = document.createElement("button");
  btn.className = "op-btn";
  btn.textContent = label;
  btn.onclick = onClick;
  box.appendChild(btn);
}

async function setKillSwitch(armed) {
  try {
    await fetch(`${BACKEND}madrugada/kill-switch`, withLocalAuth({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ armed }),
    }));
    await loadMadrugada();
  } catch (_) {
    const panel = $("mad-panel");
    if (panel) panel.innerHTML = `<div class="card-sub">Ação de kill switch não concluída.</div>`;
  }
}

export { viewMadrugada };
