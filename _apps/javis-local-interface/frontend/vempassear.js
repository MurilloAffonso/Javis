// Painel Cérebro Vem Passear — consome os endpoints /vp/* do backend do Jamba.
const API = "http://localhost:8000";
const VP_PROJECT_ID = "project:cerebro-jampa";
const LOCAL_TOKEN_KEY = "javes.localToken";
const LOCAL_TOKEN_HEADER = "X-Javes-Local-Token";

// Relógio
function tickClock() {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toLocaleTimeString("pt-BR");
}
setInterval(tickClock, 1000);
tickClock();

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function brl(n) { return "R$ " + Number(n || 0).toLocaleString("pt-BR"); }

function scopedPath(path) {
  if (!path.startsWith("/vp") && !path.startsWith("/jampa")) return path;
  const url = new URL(API + path);
  url.searchParams.set("project_id", VP_PROJECT_ID);
  return url.pathname + url.search;
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  try {
    const token = (localStorage.getItem(LOCAL_TOKEN_KEY) || "").trim();
    if (token) headers[LOCAL_TOKEN_HEADER] = token;
  } catch (_) {}
  return headers;
}

async function getJSON(path) {
  const res = await fetch(API + scopedPath(path), { signal: AbortSignal.timeout(8000), headers: authHeaders() });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}
async function sendJSON(path, method, body) {
  const res = await fetch(API + scopedPath(path), {
    method,
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

function setConn(ok) {
  const dot = document.getElementById("conn-dot");
  const lbl = document.getElementById("conn-lbl");
  if (dot) dot.classList.toggle("on", ok);
  if (lbl) lbl.textContent = ok ? "conectado ao Jamba" : "servidor offline";
}

// ── Passeios ──────────────────────────────────────────────────────────
async function loadPasseios() {
  const box = document.getElementById("passeios");
  try {
    const { passeios, resumo } = await getJSON("/vp/passeios");
    setConn(true);
    document.getElementById("r-passeios").textContent = resumo.total_passeios;
    document.getElementById("r-pessoas").textContent  = resumo.total_pessoas;
    document.getElementById("r-fat").textContent      = brl(resumo.faturamento);

    if (!passeios.length) { box.innerHTML = '<div class="empty">Nenhum passeio cadastrado.</div>'; return; }
    box.innerHTML = passeios.map(p => `
      <div class="item">
        <div class="grow">
          ${esc(p.tipo)}
          <div class="meta"><span class="accent">${esc(p.data || "s/ data")}</span> · ${p.pessoas} pessoa(s) · ${brl(p.valor)}/p</div>
        </div>
        <button class="btn mini" data-del-passeio="${esc(p.id)}">✕</button>
      </div>`).join("");
  } catch { setConn(false); box.innerHTML = '<div class="empty">—</div>'; }
}

async function addPasseio() {
  const tipo    = document.getElementById("p-tipo").value;
  const data    = document.getElementById("p-data").value;
  const pessoas = parseInt(document.getElementById("p-pessoas").value || "1", 10);
  const valor   = parseFloat(document.getElementById("p-valor").value || "0");
  if (!data) { alert("Escolha a data do passeio."); return; }
  await sendJSON("/vp/passeios", "POST", { tipo, data, pessoas, valor });
  document.getElementById("p-valor").value = "";
  loadPasseios();
}

// ── Clientes / Leads ──────────────────────────────────────────────────
function renderCliente(c, fechado) {
  const responder = fechado ? "" :
    `<button class="btn mini" data-responder data-nome="${esc(c.nome)}" data-contato="${esc(c.contato || "")}" data-obs="${esc(c.obs || "")}">💬 responder</button>`;
  const acoes = fechado
    ? `<button class="btn mini" data-reabrir="${esc(c.id)}">↩</button>`
    : `<button class="btn mini" data-fechar="${esc(c.id)}">✓ fechou</button>`;
  return `
    <div class="item">
      <div class="grow">
        <span class="${fechado ? "tag-fechado" : "tag-lead"}">${esc(c.nome)}</span>
        <div class="meta">${esc(c.contato || "")}${c.obs ? " · " + esc(c.obs) : ""}</div>
      </div>
      ${responder}
      ${acoes}
      <button class="btn mini" data-del-cliente="${esc(c.id)}">✕</button>
    </div>`;
}

async function loadClientes() {
  const lBox = document.getElementById("leads");
  const fBox = document.getElementById("fechados");
  try {
    const { leads, fechados } = await getJSON("/vp/clientes");
    document.getElementById("r-leads").textContent = leads.length;
    lBox.innerHTML = leads.length    ? leads.map(c => renderCliente(c, false)).join("")    : '<div class="empty">Nenhum lead aberto.</div>';
    fBox.innerHTML = fechados.length ? fechados.map(c => renderCliente(c, true)).join("")  : '<div class="empty">Ninguém fechou ainda.</div>';
  } catch { lBox.innerHTML = '<div class="empty">—</div>'; fBox.innerHTML = '<div class="empty">—</div>'; }
}

async function addCliente() {
  const nome    = document.getElementById("c-nome").value.trim();
  const contato = document.getElementById("c-contato").value.trim();
  const obs     = document.getElementById("c-obs").value.trim();
  if (!nome) { alert("Coloque o nome do lead."); return; }
  await sendJSON("/vp/clientes", "POST", { nome, contato, obs });
  ["c-nome", "c-contato", "c-obs"].forEach(id => document.getElementById(id).value = "");
  loadClientes();
}

// ── Conteúdo (IA) ─────────────────────────────────────────────────────
let _ctTipo = "ideias";

async function gerarConteudo(tipo) {
  _ctTipo = tipo;
  const out  = document.getElementById("ct-output");
  const tema = document.getElementById("ct-tema").value.trim();
  out.classList.remove("empty");
  out.classList.add("loading");
  out.textContent = "Jamba está escrevendo…";
  document.getElementById("ct-actions").style.display = "none";
  try {
    const { texto } = await sendJSON("/vp/conteudo", "POST", { tipo, tema });
    out.classList.remove("loading");
    out.textContent = texto || "(sem resposta)";
    document.getElementById("ct-actions").style.display = "flex";
  } catch (e) {
    out.classList.remove("loading");
    out.textContent = "Falhou: " + e.message;
  }
}

// ── Biblioteca de conteúdo ────────────────────────────────────────────
const _TIPO_LBL = { ideias:"💡 Ideias", legenda:"📝 Legenda", reel:"🎬 Reel",
                    resposta:"💬 Resposta", oferta:"🔥 Oferta", stories:"📲 Stories" };

async function salvarConteudo() {
  const texto = document.getElementById("ct-output").textContent || "";
  if (!texto.trim()) return;
  await sendJSON("/vp/conteudos", "POST", { tipo: _ctTipo, texto });
  loadBiblioteca();
}

async function loadBiblioteca() {
  const box = document.getElementById("biblioteca");
  try {
    const { conteudos } = await getJSON("/vp/conteudos");
    if (!conteudos.length) { box.innerHTML = '<div class="empty">Conteúdos salvos aparecem aqui.</div>'; return; }
    box.innerHTML = conteudos.map(c => `
      <div class="item">
        <div class="grow">
          <span class="accent">${_TIPO_LBL[c.tipo] || c.tipo}</span>
          <div class="meta">${esc((c.texto || "").slice(0, 90))}…</div>
        </div>
        <button class="btn mini" data-copy-cont="${esc(c.id)}">📋</button>
        <button class="btn mini" data-del-cont="${esc(c.id)}">✕</button>
      </div>`).join("");
    box._cache = {}; conteudos.forEach(c => box._cache[c.id] = c.texto);
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

// ── Linha editorial (pauta) ───────────────────────────────────────────
async function loadPauta() {
  const box = document.getElementById("pauta");
  try {
    const { pauta } = await getJSON("/vp/pauta");
    if (!pauta.length) { box.innerHTML = '<div class="empty">Nenhuma pauta. Planeje um post.</div>'; return; }
    box.innerHTML = pauta.map(p => {
      const pub = p.status === "publicado";
      return `
      <div class="item">
        <div class="grow">
          <span class="${pub ? "tag-fechado" : "tag-lead"}">${esc(p.data || "")}</span> · ${esc(p.canal || "")}
          <div class="meta">${esc(p.ideia || "")}</div>
        </div>
        ${pub ? `<button class="btn mini" data-replan="${esc(p.id)}">↩</button>`
              : `<button class="btn mini" data-pub="${esc(p.id)}">✓ publicou</button>`}
        <button class="btn mini" data-del-pauta="${esc(p.id)}">✕</button>
      </div>`;
    }).join("");
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

async function addPauta() {
  const data  = document.getElementById("pa-data").value;
  const canal = document.getElementById("pa-canal").value.trim() || "Instagram";
  const ideia = document.getElementById("pa-ideia").value.trim();
  if (!data || !ideia) { alert("Coloque a data e a ideia do post."); return; }
  await sendJSON("/vp/pauta", "POST", { data, canal, ideia });
  document.getElementById("pa-ideia").value = "";
  loadPauta();
}

// ── Squad Jampa Jarvis ────────────────────────────────────────────────
const _AG_ICON = {};
async function loadSquad() {
  const box = document.getElementById("sq-roster");
  try {
    const { agents, ok } = await getJSON("/jampa/agents");
    if (!ok || !agents.length) { box.innerHTML = '<div class="empty">Squad indisponível (vault não encontrado).</div>'; return; }
    document.getElementById("sq-count").textContent = `· ${agents.length} agentes`;
    box.innerHTML = agents.map(a => `
      <div class="ag" title="${esc(a.papel)} — skills: ${esc((a.skills||[]).join(', '))}">
        <span class="ag-ico">${a.icon || "🤖"}</span>
        <span class="ag-nome">${esc(a.nome)}</span>
        <span class="ag-papel">${esc(a.papel)}</span>
      </div>`).join("");
    const sel = document.getElementById("sq-agente");
    sel.innerHTML = '<option value="">🧠 Orion decide (automático)</option>' +
      agents.map(a => `<option value="${esc(a.nome)}">${a.icon || "🤖"} ${esc(a.nome)} — ${esc(a.papel)}</option>`).join("");
    agents.forEach(a => _AG_ICON[a.nome] = a.icon);
  } catch { box.innerHTML = '<div class="empty">—</div>'; }
}

async function runSquad() {
  const tarefa = document.getElementById("sq-tarefa").value.trim();
  const agente = document.getElementById("sq-agente").value;
  if (!tarefa) { alert("Diga o que o squad deve fazer."); return; }
  const out = document.getElementById("sq-output");
  out.classList.remove("empty"); out.classList.add("loading");
  out.textContent = "Squad trabalhando…";
  document.getElementById("sq-actions").style.display = "none";
  try {
    const r = await sendJSON("/jampa/squad", "POST", { tarefa, agente });
    out.classList.remove("loading");
    const quem = r.agente ? `${_AG_ICON[r.agente] || "🤖"} ${r.agente}` : "Squad";
    out.textContent = `[${quem}]\n\n${r.resposta || "(sem resposta)"}`;
    document.getElementById("sq-actions").style.display = "flex";
  } catch (e) { out.classList.remove("loading"); out.textContent = "Falhou: " + e.message; }
}

async function responderLead(btn) {
  const nome = btn.dataset.nome || "", contato = btn.dataset.contato || "", obs = btn.dataset.obs || "";
  const orig = btn.textContent; btn.textContent = "✍️ gerando…"; btn.disabled = true;
  try {
    const r = await sendJSON("/jampa/responder-lead", "POST", { nome, contato, interesse: obs, obs });
    const msg = r.mensagem || "";
    const url = r.numero
      ? `https://wa.me/${r.numero}?text=${encodeURIComponent(msg)}`
      : `https://wa.me/?text=${encodeURIComponent(msg)}`;
    window.open(url, "_blank", "noopener");
  } catch (e) { alert("Falhou ao gerar resposta: " + e.message); }
  finally { btn.textContent = orig; btn.disabled = false; }
}

// ── Eventos ───────────────────────────────────────────────────────────
document.addEventListener("click", async (ev) => {
  const t = ev.target.closest("button, a");
  if (!t) return;

  if (t.id === "sq-run")      return runSquad();
  if (t.dataset.responder !== undefined) return responderLead(t);
  if (t.id === "sq-copy") {
    navigator.clipboard.writeText(document.getElementById("sq-output").textContent || "");
    t.textContent = "✓ Copiado"; setTimeout(() => t.textContent = "📋 Copiar", 1500);
    return;
  }
  if (t.dataset.tipo)         return gerarConteudo(t.dataset.tipo);
  if (t.id === "p-add")       return addPasseio();
  if (t.id === "c-add")       return addCliente();
  if (t.id === "pa-add")      return addPauta();
  if (t.id === "ct-save")     return salvarConteudo();
  if (t.id === "ct-copy") {
    navigator.clipboard.writeText(document.getElementById("ct-output").textContent || "");
    t.textContent = "✓ Copiado"; setTimeout(() => t.textContent = "📋 Copiar", 1500);
    return;
  }
  if (t.dataset.copyCont) {
    const cache = document.getElementById("biblioteca")._cache || {};
    navigator.clipboard.writeText(cache[t.dataset.copyCont] || "");
    t.textContent = "✓"; setTimeout(() => t.textContent = "📋", 1200);
    return;
  }
  if (t.dataset.delCont)    { await sendJSON(`/vp/conteudos/${t.dataset.delCont}`, "DELETE"); return loadBiblioteca(); }
  if (t.dataset.pub)        { await sendJSON(`/vp/pauta/${t.dataset.pub}`, "PATCH", { status: "publicado" }); return loadPauta(); }
  if (t.dataset.replan)     { await sendJSON(`/vp/pauta/${t.dataset.replan}`, "PATCH", { status: "planejado" }); return loadPauta(); }
  if (t.dataset.delPauta)   { await sendJSON(`/vp/pauta/${t.dataset.delPauta}`, "DELETE"); return loadPauta(); }
  if (t.dataset.delPasseio) { await sendJSON(`/vp/passeios/${t.dataset.delPasseio}`, "DELETE"); return loadPasseios(); }
  if (t.dataset.fechar)     { await sendJSON(`/vp/clientes/${t.dataset.fechar}`, "PATCH", { status: "fechado" }); return loadClientes(); }
  if (t.dataset.reabrir)    { await sendJSON(`/vp/clientes/${t.dataset.reabrir}`, "PATCH", { status: "lead" }); return loadClientes(); }
  if (t.dataset.delCliente) { await sendJSON(`/vp/clientes/${t.dataset.delCliente}`, "DELETE"); return loadClientes(); }
});

// ── Boot ──────────────────────────────────────────────────────────────
function refreshAll() { loadPasseios(); loadClientes(); loadPauta(); loadBiblioteca(); }
refreshAll();
loadSquad();
setInterval(refreshAll, 10000);
