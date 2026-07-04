// Ingestão — despeje material → DNA → grafo cresce. Tela didática do "cérebro".
// Reusa endpoints: POST /knowledge/ingest (lote async) + status, POST /knowledge/dna
// (avulso), POST /knowledge/graph/build, GET /knowledge/graph (stats + conceitos).
import { h, $, state, BACKEND, tryJson, _esc, opToast } from "../../app.js";

let _poll = null;

function ensureStyles() {
  if ($("ing-styles")) return;
  const s = document.createElement("style");
  s.id = "ing-styles";
  s.textContent = `
  .ing-intro { background:var(--accent-soft); border:1px solid var(--accent-dim,var(--border-2));
    border-radius:var(--radius-sm); padding:12px 15px; font-size:13px; color:var(--text);
    line-height:1.55; margin-bottom:18px; }
  .ing-grid { display:grid; grid-template-columns:1fr 340px; gap:16px; align-items:start; }
  @media (max-width:980px){ .ing-grid { grid-template-columns:1fr; } }
  .ing-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:16px; margin-bottom:16px; }
  .ing-h { font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted-2);
    margin-bottom:12px; display:flex; align-items:center; gap:8px; }
  .ing-h .n { margin-left:auto; color:var(--accent); font-weight:700; font-variant-numeric:tabular-nums; }
  .ing-steps { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }
  .ing-step { flex:1; min-width:150px; background:var(--bg-2); border:1px solid var(--border);
    border-radius:10px; padding:11px 13px; }
  .ing-step b { color:var(--accent); }
  .ing-step .t { font-size:13px; font-weight:600; margin-bottom:3px; }
  .ing-step .d { font-size:11.5px; color:var(--muted); }
  .ing-kpis { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:6px; }
  .ing-kpi { flex:1; min-width:90px; background:var(--bg-2); border:1px solid var(--border);
    border-radius:10px; padding:12px; text-align:center; }
  .ing-kpi .n { font-size:24px; font-weight:800; color:var(--accent); font-variant-numeric:tabular-nums; line-height:1; }
  .ing-kpi .l { font-size:10px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted-2); margin-top:7px; }
  .ing-btn { border:1px solid var(--border-2); background:var(--card-hover); color:var(--text);
    padding:9px 14px; border-radius:10px; font-size:13px; font-weight:600; cursor:pointer;
    transition:border-color .15s, background .15s; }
  .ing-btn:hover { border-color:var(--accent); }
  .ing-btn.primary { background:linear-gradient(135deg,var(--accent),var(--accent-2)); border-color:transparent; color:#1a0f06; }
  .ing-btn:disabled { opacity:.55; cursor:default; }
  .ing-row { display:flex; gap:9px; flex-wrap:wrap; align-items:center; margin-top:4px; }
  .ing-textarea { width:100%; box-sizing:border-box; min-height:120px; resize:vertical; background:var(--bg);
    color:var(--text); border:1px solid var(--border); border-radius:10px; padding:11px 13px;
    font-size:13px; font-family:var(--font); line-height:1.5; outline:none; }
  .ing-textarea:focus { border-color:var(--accent); }
  .ing-prog { height:8px; border-radius:5px; background:var(--border); overflow:hidden; margin:10px 0 6px; }
  .ing-prog i { display:block; height:100%; background:linear-gradient(90deg,var(--accent-dim,var(--accent)),var(--accent)); width:0%; transition:width .4s; }
  .ing-prog-lbl { font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }
  .ing-concept { display:flex; align-items:center; gap:9px; padding:8px 0; border-top:1px solid var(--border); }
  .ing-concept:first-child { border-top:none; }
  .ing-concept .grau { font-size:11px; font-weight:700; color:var(--accent); background:var(--accent-soft);
    border-radius:6px; padding:1px 7px; min-width:30px; text-align:center; flex:0 0 auto; }
  .ing-concept .lbl { font-size:12.5px; color:var(--text); line-height:1.35; }
  .ing-concept .typ { font-size:10px; color:var(--muted-2); }
  .ing-hint { font-size:11.5px; color:var(--muted); margin-top:6px; line-height:1.5; }
  code.ing-path { background:var(--bg-2); border:1px solid var(--border); border-radius:5px; padding:1px 6px; font-size:11.5px; color:var(--accent); }
  `;
  document.head.appendChild(s);
}

export function viewIngestao(body) {
  ensureStyles();

  const root = h(`<div>
    <div class="ing-intro">🧠 <b>Ingestão — o cérebro do Javis.</b> Despeje material (WhatsApp, transcrições,
      resumos de mentores, notas) e ele vira <b>dossiê de DNA</b> → entra no <b>RAG</b> → alimenta o <b>grafo</b>.
      O salto de inteligência vem do <b>volume</b>: quanto mais você alimenta, mais o Javis pensa e fala como você.</div>

    <div class="ing-steps">
      <div class="ing-step"><div class="t"><b>1.</b> Despejar</div><div class="d">Jogue arquivos .txt/.md em <code class="ing-path">_inbox/ingestao/</code></div></div>
      <div class="ing-step"><div class="t"><b>2.</b> Processar</div><div class="d">O Javis extrai o DNA de cada um (assíncrono)</div></div>
      <div class="ing-step"><div class="t"><b>3.</b> Ver crescer</div><div class="d">O grafo ganha nós e conexões novas</div></div>
    </div>

    <div class="ing-grid">
      <div class="ing-col-left"></div>
      <div class="ing-col-right"></div>
    </div>
  </div>`);
  body.appendChild(root);

  root.querySelector(".ing-col-left").appendChild(buildLote());
  root.querySelector(".ing-col-left").appendChild(buildAvulso());
  root.querySelector(".ing-col-right").appendChild(buildGrafo());

  refreshGrafo();
  // Se uma ingestão já estava rodando (voltou pra tela), retoma o acompanhamento.
  atualizarStatus();
}

// ---------- Lote (pasta _inbox/ingestao) ----------
function buildLote() {
  const card = h(`<div class="ing-card">
    <div class="ing-h">📥 Ingestão em lote</div>
    <div class="ing-hint">Processa tudo que estiver em <code class="ing-path">_inbox/ingestao/</code>.
      Roda em segundo plano — pode levar minutos com muitos arquivos (~20-40s cada).</div>
    <div class="ing-prog"><i id="ing-prog-bar"></i></div>
    <div class="ing-prog-lbl" id="ing-prog-lbl">Pronto para processar.</div>
    <div class="ing-row">
      <button class="ing-btn primary" id="ing-run">▶ Processar pasta</button>
      <button class="ing-btn" id="ing-rebuild">🕸️ Reconstruir grafo</button>
    </div>
  </div>`);
  card.querySelector("#ing-run").onclick = dispararLote;
  card.querySelector("#ing-rebuild").onclick = reconstruirGrafo;
  return card;
}

async function dispararLote() {
  if (!state.online) { opToast("Precisa do backend em :8000.", "warn"); return; }
  const btn = $("ing-run"); if (btn) { btn.disabled = true; btn.textContent = "Iniciando…"; }
  try {
    const r = await tryJson(BACKEND + "knowledge/ingest", { method: "POST" });
    if (r.status === "vazio") {
      opToast("Pasta vazia. Jogue arquivos .txt/.md em _inbox/ingestao/ primeiro.", "warn");
      if (btn) { btn.disabled = false; btn.textContent = "▶ Processar pasta"; }
      return;
    }
    if (r.status === "ja_rodando") { opToast("Já tem uma ingestão rodando.", "info"); }
    else { opToast(`Ingestão iniciada: ${r.total} arquivo(s).`, "ok"); }
    iniciarPolling();
  } catch (e) {
    opToast("Falha ao iniciar a ingestão.", "err");
    if (btn) { btn.disabled = false; btn.textContent = "▶ Processar pasta"; }
  }
}

function iniciarPolling() {
  if (_poll) clearInterval(_poll);
  _poll = setInterval(atualizarStatus, 2500);
}

async function atualizarStatus() {
  if (!state.online || !$("ing-prog-bar")) { if (_poll) { clearInterval(_poll); _poll = null; } return; }
  let s;
  try { s = await tryJson(BACKEND + "knowledge/ingest/status"); } catch (_) { return; }
  const bar = $("ing-prog-bar"), lbl = $("ing-prog-lbl"), btn = $("ing-run");
  if (!bar || !lbl) return;
  const pct = s.total ? Math.round((s.processed / s.total) * 100) : 0;
  if (s.running) {
    bar.style.width = pct + "%";
    lbl.textContent = `Processando ${s.processed}/${s.total} — ${s.current || "…"}`;
    if (btn) { btn.disabled = true; btn.textContent = "Processando…"; }
  } else {
    if (_poll) { clearInterval(_poll); _poll = null; }
    if (btn) { btn.disabled = false; btn.textContent = "▶ Processar pasta"; }
    if (s.processed > 0 && s.done_ts) {
      bar.style.width = "100%";
      lbl.textContent = `✓ Concluído: ${s.ok} dossiê(s) · ${s.erros} erro(s). Grafo atualizado.`;
      refreshGrafo();
    }
  }
}

async function reconstruirGrafo() {
  if (!state.online) { opToast("Precisa do backend.", "warn"); return; }
  const btn = $("ing-rebuild"); if (btn) { btn.disabled = true; btn.textContent = "Reconstruindo…"; }
  try {
    await tryJson(BACKEND + "knowledge/graph/build", { method: "POST" });
    opToast("Grafo reconstruído.", "ok");
    refreshGrafo();
  } catch (_) { opToast("Falha ao reconstruir.", "err"); }
  finally { if (btn) { btn.disabled = false; btn.textContent = "🕸️ Reconstruir grafo"; } }
}

// ---------- Avulso (colar texto → DNA) ----------
function buildAvulso() {
  const card = h(`<div class="ing-card">
    <div class="ing-h">✍️ Material avulso</div>
    <div class="ing-hint" style="margin-bottom:10px">Cole um texto denso (nota, transcrição, resumo) e extraia o DNA na hora.</div>
    <textarea class="ing-textarea" id="ing-avulso" placeholder="Cole aqui o material..."></textarea>
    <div class="ing-row"><button class="ing-btn primary" id="ing-extrair">🧬 Extrair DNA</button></div>
  </div>`);
  card.querySelector("#ing-extrair").onclick = extrairAvulso;
  return card;
}

async function extrairAvulso() {
  if (!state.online) { opToast("Precisa do backend.", "warn"); return; }
  const ta = $("ing-avulso"); const texto = (ta ? ta.value : "").trim();
  if (texto.length < 40) { opToast("Cole um material com mais conteúdo (mín. ~40 caracteres).", "warn"); return; }
  const btn = $("ing-extrair"); if (btn) { btn.disabled = true; btn.textContent = "Extraindo… (~30s)"; }
  try {
    const r = await tryJson(BACKEND + "knowledge/dna", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: texto, fonte: "avulso", tema: "" }),
    });
    if (r.status === "ok") {
      opToast(`DNA extraído (fidelidade ${r.fidelidade ?? "—"}). Reconstruindo grafo…`, "ok");
      if (ta) ta.value = "";
      await reconstruirGrafo();
    } else {
      opToast("Não consegui extrair: " + (r.message || "erro"), "warn");
    }
  } catch (_) { opToast("Falha na extração.", "err"); }
  finally { if (btn) { btn.disabled = false; btn.textContent = "🧬 Extrair DNA"; } }
}

// ---------- Grafo (coluna direita) ----------
function buildGrafo() {
  const card = h(`<div class="ing-card">
    <div class="ing-h">🕸️ Grafo de conhecimento <span class="n" id="ing-g-nodes">—</span></div>
    <div class="ing-kpis">
      <div class="ing-kpi"><div class="n" id="ing-k-nodes">—</div><div class="l">Nós</div></div>
      <div class="ing-kpi"><div class="n" id="ing-k-edges">—</div><div class="l">Arestas</div></div>
    </div>
    <div class="ing-h" style="margin-top:16px">Conceitos centrais</div>
    <div id="ing-concepts"><div class="ing-hint">Carregando…</div></div>
  </div>`);
  return card;
}

async function refreshGrafo() {
  if (!state.online) { const c = $("ing-concepts"); if (c) c.innerHTML = `<div class="ing-hint">Backend offline.</div>`; return; }
  let g;
  try { g = await tryJson(BACKEND + "knowledge/graph"); } catch (_) { return; }
  const fmt = (n) => (n == null ? "—" : Number(n).toLocaleString("pt-BR"));
  const setTxt = (id, v) => { const el = $(id); if (el) el.textContent = v; };
  setTxt("ing-g-nodes", fmt(g.nodes) + " nós");
  setTxt("ing-k-nodes", fmt(g.nodes));
  setTxt("ing-k-edges", fmt(g.edges));
  const box = $("ing-concepts"); if (!box) return;
  const top = (g.top || []).slice(0, 10);
  if (!top.length) { box.innerHTML = `<div class="ing-hint">Grafo vazio. Alimente material para os conceitos surgirem.</div>`; return; }
  box.innerHTML = "";
  top.forEach((c) => {
    const row = h(`<div class="ing-concept"><span class="grau"></span><div><div class="lbl"></div><div class="typ"></div></div></div>`);
    row.querySelector(".grau").textContent = c.grau ?? "·";
    row.querySelector(".lbl").textContent = (c.label || "").slice(0, 90);
    row.querySelector(".typ").textContent = (c.type || "").replace(/_/g, " ");
    box.appendChild(row);
  });
}

export default viewIngestao;
