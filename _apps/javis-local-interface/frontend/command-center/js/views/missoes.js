// Missões — backlog e nodes (leitura) — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, $, state, BACKEND, tryJson, _esc, pct } from "../../app.js";

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

export { viewMissoes };
