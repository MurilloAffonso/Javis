// Execução supervisionada — R4.2C2. Sem streams brutos, sem paths internos.
import { h, $, BACKEND, CORE_PROJECT_ID, tryJson, withLocalAuth, opEsc } from "../../app.js";

// Iniciado vazio de propósito: ler CORE_PROJECT_ID aqui, no topo do módulo,
// dispara TDZ na dependência circular com app.js (app.js importa esta view antes
// de terminar de definir suas consts). Resolvido dentro de viewExec.
let _execProjectId = "";
let _supervisedEnabled = false;

function viewExec(body) {
  _execProjectId = _execProjectId || CORE_PROJECT_ID;
  body.appendChild(h(`<div class="exec-view">
    <div class="exec-header">
      <div class="exec-header-left">
        <span class="exec-badge">SUPERVISIONADO</span>
        <span class="exec-task-name">Execução segura por task_id + project_id</span>
      </div>
      <div class="exec-header-right">
        <select id="exec-project" class="op-input">
          <option value="javes-core">javes-core</option>
          <option value="project:cerebro-jampa">project:cerebro-jampa</option>
        </select>
        <button class="exec-clear-btn" id="exec-refresh">Atualizar</button>
      </div>
    </div>
    <div class="card-sub" id="exec-flag">Carregando status do executor…</div>
    <div id="exec-list" class="op-board"><div class="card-sub">Carregando tasks…</div></div>
    <div id="exec-result" class="exec-terminal"><div class="exec-hint">Selecione “Ver resumo” para carregar diff/testes sanitizados.</div></div>
  </div>`));

  $("exec-project").onchange = (ev) => {
    _execProjectId = ev.target.value || CORE_PROJECT_ID;
    loadExecutionTasks();
  };
  $("exec-refresh").onclick = () => loadExecutionTasks();
  loadExecutionTasks();
  window._execPollTimer = setInterval(loadExecutionTasks, 5000);
}

async function loadExecutionTasks() {
  const list = $("exec-list");
  if (!list) return;
  try {
    const data = await tryJson(`${BACKEND}execution/tasks?project_id=${encodeURIComponent(_execProjectId)}`);
    _supervisedEnabled = data.supervised_execution_enabled === true;
    const flag = $("exec-flag");
    if (flag) {
      flag.textContent = _supervisedEnabled
        ? "JAVIS_ENABLE_SUPERVISED_EXEC=True — execução manual habilitada."
        : "JAVIS_ENABLE_SUPERVISED_EXEC=False — botão Executar permanece desabilitado.";
    }
    renderTasks(data.tasks || []);
  } catch (_) {
    list.innerHTML = `<div class="card-sub">Não consegui carregar execution_tasks.</div>`;
  }
}

function renderTasks(tasks) {
  const list = $("exec-list");
  if (!list) return;
  list.innerHTML = "";
  if (!tasks.length) {
    list.appendChild(h(`<div class="op-empty">Nenhuma execution_task neste projeto.</div>`));
    return;
  }
  tasks.forEach((task) => {
    const card = h(`<div class="op-card">
      <div class="op-card-title"></div>
      <div class="op-card-meta"></div>
      <div class="op-card-meta"></div>
      <div class="op-card-meta"></div>
      <div class="op-ap-actions"></div>
    </div>`);
    const metas = card.querySelectorAll(".op-card-meta");
    card.querySelector(".op-card-title").textContent = shortId(task.task_id);
    metas[0].textContent = `${task.project_id} · ${task.executor} · ${task.status}`;
    metas[1].textContent = `testes: ${task.tests_status || "not_run"} · arquivos: ${task.changed_files_count || 0}`;
    metas[2].textContent = `exec approval: ${task.execution_approval} · merge approval: ${task.merge_approval} · risco: ${task.risk || "high"}`;
    renderActions(card.querySelector(".op-ap-actions"), task);
    list.appendChild(card);
  });
}

function renderActions(box, task) {
  const actions = new Set(task.actions || []);
  if (actions.has("request_start_approval")) {
    addButton(box, "Solicitar execução", () => postAction(task, "request-start-approval"));
  }
  if (actions.has("open_approval")) {
    addButton(box, "Abrir aprovação", () => setViewHint(`Aprovação de execução: ${task.approval_id || "pendente"}`));
  }
  if (actions.has("start")) {
    addButton(box, "Executar", () => postAction(task, "start", { test_commands: [] }), !_supervisedEnabled);
  }
  if (actions.has("view_result")) {
    addButton(box, "Ver resumo", () => loadResult(task));
  }
  if (actions.has("request_merge_approval")) {
    addButton(box, "Solicitar aprovação de merge", () => postAction(task, "request-merge-approval"));
  }
  if (actions.has("perform_merge")) {
    addButton(box, "Fazer merge local", () => postAction(task, "merge"));
  }
  if (actions.has("cancel")) {
    addButton(box, "Cancelar", () => postAction(task, "cancel"));
  }
}

function addButton(box, label, onClick, disabled = false) {
  const btn = document.createElement("button");
  btn.className = "op-btn";
  btn.textContent = label;
  btn.disabled = disabled;
  btn.onclick = onClick;
  box.appendChild(btn);
}

async function postAction(task, action, extra = {}) {
  const body = { project_id: task.project_id, ...extra };
  try {
    const out = await fetch(`${BACKEND}execution/tasks/${encodeURIComponent(task.task_id)}/${action}`, withLocalAuth({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })).then((r) => r.json());
    setViewHint(JSON.stringify(out, null, 2));
    await loadExecutionTasks();
  } catch (_) {
    setViewHint("Ação não concluída.");
  }
}

async function loadResult(task) {
  try {
    const out = await tryJson(`${BACKEND}execution/tasks/${encodeURIComponent(task.task_id)}/result?project_id=${encodeURIComponent(task.project_id)}`);
    const result = $("exec-result");
    result.innerHTML = "";
    const pre = document.createElement("pre");
    pre.textContent = [
      "Resumo sanitizado",
      JSON.stringify(out.summary || {}, null, 2),
      "",
      "Testes",
      out.tests || "(sem relatório)",
      "",
      "Diff sanitizado",
      out.diff || "(sem diff)",
    ].join("\n");
    result.appendChild(pre);
  } catch (_) {
    setViewHint("Resultado não disponível.");
  }
}

function setViewHint(text) {
  const result = $("exec-result");
  if (!result) return;
  result.innerHTML = "";
  const pre = document.createElement("pre");
  pre.textContent = text;
  result.appendChild(pre);
}

function shortId(taskId) {
  const safe = opEsc(taskId || "—");
  return safe.length > 18 ? `${safe.slice(0, 13)}…${safe.slice(-4)}` : safe;
}

export { viewExec };
