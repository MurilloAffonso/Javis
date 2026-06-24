// app.js — roteador por hash + telas. Liga os componentes aos dados mock.
import {
  KPIS_GLOBAIS, PROJETOS, SQUADS, APROVACOES, PROXIMOS_PASSOS, METRICAS, FASES,
} from "./data.js";
import {
  kpiCard, projectCard, squadNode, approvalCard, agentContract, statusDot,
  trendBadge, esc, setSquadsCount,
} from "./components.js";

setSquadsCount((slug) => (SQUADS[slug] || []).length);

const main = document.getElementById("view");
const crumbEl = document.getElementById("crumb");
const projeto = (slug) => PROJETOS.find(p => p.slug === slug);
const squadsDe = (slug) => SQUADS[slug] || [];

// ---------- TELAS ----------

function telaCentral() {
  setCrumb("Central");
  return `
    <div class="section-title">Visão geral</div>
    <div class="grid cols-4">${KPIS_GLOBAIS.map(kpiCard).join("")}</div>

    <div class="section-title">Projetos plugados</div>
    <div class="grid cols-3">
      ${PROJETOS.map(projectCard).join("")}
      <div class="card hover" style="display:flex;align-items:center;justify-content:center;color:var(--faint);border-style:dashed">+ plugar projeto</div>
    </div>

    <div class="section-title">Aprovações pendentes (${APROVACOES.length})</div>
    <div class="grid">${APROVACOES.map(approvalCard).join("")}</div>`;
}

function telaProjeto(slug) {
  const p = projeto(slug);
  if (!p) return `<div class="card">Projeto não encontrado.</div>`;
  setCrumb(`Projetos › <b>${esc(p.nome)}</b>`);
  const squads = squadsDe(slug);
  const byFase = (f) => squads.filter(s => s.fase === f);
  const transversais = squads.filter(s => s.fase === "transversal");

  const colFase = (f) => `<div class="fase-col"><h4>${esc(f.nome)}</h4>
    ${byFase(f.id).map(s => squadNode(s, slug)).join("") || `<div class="faint" style="font-size:12px;padding:6px">—</div>`}</div>`;

  return `
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0 4px">
      <span style="font-size:26px">${esc(p.icone)}</span>
      <div><div style="font-weight:600;font-size:18px">${esc(p.nome)}</div>
      <div class="muted" style="font-size:12px">${statusDot("online")} ${esc(p.fase)} · ${squads.length} squads</div></div>
    </div>

    ${p.contexto ? `<div class="card" style="border-color:rgba(34,211,238,.25);margin-top:8px">
       <b>${esc(p.contexto.titulo)}</b> &nbsp; <span class="muted">${esc(p.contexto.sub)}</span></div>` : ""}

    <div class="grid cols-4" style="margin-top:14px">${p.kpis.map(kpiCard).join("")}</div>

    <div class="section-title">Mapa de squads — funil</div>
    <div class="grid" style="grid-template-columns:repeat(5,1fr)">${FASES.map(colFase).join("")}</div>

    <div class="section-title">Transversais</div>
    <div class="transv">${transversais.map(s => squadNode(s, slug)).join("")}</div>`;
}

function telaSquad(slug, id) {
  const s = squadsDe(slug).find(x => x.id === id);
  const p = projeto(slug);
  if (!s) return `<div class="card">Squad não encontrado.</div>`;
  setCrumb(`Projetos › <b>${esc(p.nome)}</b> › Squads › <b>${esc(s.nome)}</b>`);
  return `
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px">
      <span style="font-size:24px">${esc(s.icone)}</span>
      <div><div style="font-weight:600;font-size:18px">${esc(s.nome)}</div>
      <div class="muted" style="font-size:12px">área: ${esc(s.area)} · responsável: ${esc(s.agente)}</div></div>
      <div style="flex:1"></div>
      <button class="btn ok">Rodar agora</button>
    </div>
    ${agentContract(s)}`;
}

function telaSquads() {
  setCrumb("Squads");
  const slug = PROJETOS[0].slug;
  return `<div class="section-title">Squads · ${esc(projeto(slug).nome)}</div>
    <div class="grid cols-3">${squadsDe(slug).map(s => squadNode(s, slug)).join("")}</div>`;
}

function telaMetricas() {
  setCrumb("Métricas");
  return `
    <div class="section-title">Métricas que movem receita</div>
    <div class="grid cols-3">${METRICAS.receita.map(kpiCard).join("")}</div>
    <div class="section-title">Vaidade — fora da decisão</div>
    <div class="grid cols-3" style="opacity:.45">
      ${METRICAS.vaidade.map(v => `<div class="card kpi"><div class="label">${esc(v.label)}</div><div class="val">${esc(v.value)}</div></div>`).join("")}
    </div>
    <div style="margin-top:18px"><button class="btn">Abrir Ritual Semanal — Escalar / Manter / Matar</button></div>`;
}

function telaAprovacoes() {
  setCrumb("Aprovações");
  return `<div class="section-title">Fila de aprovações (${APROVACOES.length})</div>
    <div class="grid">${APROVACOES.map(approvalCard).join("")}</div>`;
}

function telaProximos() {
  setCrumb("Próximos passos");
  const col = (titulo, arr) => `<div class="col"><h4>${esc(titulo)}</h4>
    ${arr.map(t => `<div class="ktask">${esc(t.t)}<div class="s">${esc(t.squad)}</div></div>`).join("")}</div>`;
  return `<div class="section-title">Roadmap</div>
    <div class="kanban">
      ${col("Agora", PROXIMOS_PASSOS.agora)}
      ${col("Próximo", PROXIMOS_PASSOS.proximo)}
      ${col("Depois", PROXIMOS_PASSOS.depois)}
      ${col("Concluído", PROXIMOS_PASSOS.concluido)}
    </div>`;
}

// ---------- ROTEADOR ----------

function setCrumb(html) { crumbEl.innerHTML = html; }

function router() {
  const hash = location.hash.replace(/^#\//, "") || "";
  const parts = hash.split("/").filter(Boolean);
  let html;
  if (parts.length === 0)                         html = telaCentral();
  else if (parts[0] === "squads")                 html = telaSquads();
  else if (parts[0] === "metricas")               html = telaMetricas();
  else if (parts[0] === "aprovacoes")             html = telaAprovacoes();
  else if (parts[0] === "proximos")               html = telaProximos();
  else if (parts[1] === "squad" && parts[2])      html = telaSquad(parts[0], parts[2]);
  else                                            html = telaProjeto(parts[0]); // #/<slug>
  main.innerHTML = html;
  main.scrollTop = 0;
  marcarNavAtivo(parts[0] || "central");
}

function marcarNavAtivo(key) {
  document.querySelectorAll(".nav-i").forEach(el => {
    el.classList.toggle("active", el.dataset.route === key
      || (key && el.dataset.route === "projetos" && PROJETOS.some(p => p.slug === key)));
  });
}

// rail recolhível
document.getElementById("toggle-rail")?.addEventListener("click", () => {
  document.querySelector(".app").classList.toggle("rail-collapsed");
});

window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", router);
router();
