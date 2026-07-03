// ---------- Operação (Quadro/Kanban + Gates 1/2/3 + Aprovações) ----------
// Extraído de app.js em 2026-07-02. MESMO comportamento; agora módulo ES.
import { h, $, state, BACKEND, tryJson, opToast, opSend, opEsc, confirmStrong } from "../../app.js";

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
  if (!encerrada && ext) {
    const cb = h(`<button class="op-btn ok sm">✅ Concluir</button>`);
    cb.onclick = () => confirmStrong({ title: "Concluir tarefa (encerra + gera digest)", endpoint: `/tasks/${ext}/complete`, method: "POST", target: t.title || ext, before: t.status || "—", after: "completed + digest final", risk: "op", onConfirm: () => opComplete(ext) });
    actions.appendChild(cb);
  }
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

// Concluir tarefa: POST /tasks/{id}/complete → completed + digest (200) ou 409 se já encerrada.
async function opComplete(extId) {
  try {
    const res = await opSend(BACKEND + `tasks/${encodeURIComponent(extId)}/complete`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ note: "concluída no Quadro (command-center)" }) });
    if (res.status === 409) opToast("Tarefa já estava encerrada.", "info");
    else if (res.ok && res.data.ok) opToast("Tarefa concluída. Digest gerado.", "ok");
    else opToast(res.data.error || "Não consegui concluir.", "warn");
  } catch (e) { opToast("Backend offline — não concluí.", "err"); }
  opRenderBoard();
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

export { viewOperacao };

