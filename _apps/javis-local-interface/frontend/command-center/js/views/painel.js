// Painel — visão do projeto ativo — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, state, BACKEND, tryJson, projName, renderCanvas } from "../../app.js";

function viewPainel(body) {
  const sel = h(`<div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap;align-items:center"></div>`);
  state.projects.forEach((p) => {
    const t = h(`<div class="view-tab ${p.id === state.activeProjectId ? "active" : ""}">${p.nome}</div>`);
    t.onclick = () => { state.activeProjectId = p.id; renderCanvas(); };
    sel.appendChild(t);
  });
  // botão de sincronizar — útil quando o senhor edita o Cérebro Jampa
  const sync = h(`<button class="btn no" style="margin-left:auto" id="sync-rag">🔄 Sincronizar conhecimento</button>`);
  sync.onclick = async () => {
    sync.disabled = true; const orig = sync.textContent; sync.textContent = "Sincronizando…";
    if (!state.online) { sync.textContent = "Backend offline"; setTimeout(() => { sync.textContent = orig; sync.disabled = false; }, 2500); return; }
    try {
      const r = await tryJson(BACKEND + "knowledge/reindex", { method: "POST" });
      sync.textContent = `✓ ${(r && (r.arquivos_reindexados || r.status)) || "ok"}`;
    } catch (e) { sync.textContent = "Falhou"; }
    setTimeout(() => { sync.textContent = orig; sync.disabled = false; }, 4000);
  };
  sel.appendChild(sync);
  body.appendChild(sel);

  const man = state.manifests[state.activeProjectId];
  if (!man || !man.dashboards) { body.appendChild(h(`<div class="empty-state">Sem manifesto detalhado para <b>${projName(state.activeProjectId)}</b>.<br/>Dashboards completos disponíveis para Vem Passear Jampa.</div>`)); return; }
  const funil = man.dashboards.funil_vendas;
  if (funil) {
    body.appendChild(h(`<div class="section-h">${funil.titulo}</div>`));
    const f = h(`<div class="funnel" style="margin-bottom:24px"></div>`);
    (funil.etapas || []).forEach((e, i) => {
      const w = 100 - i * (60 / Math.max(1, funil.etapas.length));
      f.appendChild(h(`<div class="funnel-step"><div class="funnel-label">${e}</div><div class="funnel-bar" style="width:${w}%">—</div></div>`));
    });
    body.appendChild(f);
  }
  body.appendChild(h(`<div class="section-h">Indicadores</div>`));
  const grid = h(`<div class="grid cols-4"></div>`);
  Object.entries(man.dashboards).forEach(([key, d]) => {
    if (key === "funil_vendas") return;
    const val = d.total ?? d.valor ?? d.nota_media ?? d.nps;
    const empty = val === null || val === undefined;
    grid.appendChild(h(`<div class="kpi"><div class="kpi-label">${d.titulo || key}</div><div class="kpi-value ${empty ? "empty" : ""}">${empty ? "sem dados" : val}</div><div class="kpi-foot">${d.status || ""}</div></div>`));
  });
  body.appendChild(grid);
}

export { viewPainel };
