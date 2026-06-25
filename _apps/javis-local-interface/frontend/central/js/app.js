// app.js — roteador por hash + telas. Agora puxa DADOS REAIS via api.js
// (com fallback automático pro mock de data.js quando o backend não responde).
import * as API from "./api.js";
import {
  kpiCard, squadNode, approvalCard, agentContract, statusDot,
  esc, setSquadsCount,
} from "./components.js";

const main = document.getElementById("view");
const crumbEl = document.getElementById("crumb");

// cache simples por carregamento (evita refetch a cada navegação)
const cache = { projetos: null, squads: {}, aprovacoes: null, status: null };

async function projetos()  { return cache.projetos  ??= await API.getProjects(); }
async function aprovacoes() { return cache.aprovacoes ??= await API.getApprovals(); }
async function squadsDe(slug) { return cache.squads[slug] ??= await API.getSquads(slug); }
async function acharProjeto(slug) { return (await projetos()).find(p => p.slug === slug); }

setSquadsCount(() => "•"); // contagem real é injetada nos cards abaixo

// chip que mostra a fonte do dado (● backend real / ○ exemplo)
const fonteChip = (f) => `<span class="chip ${f === "●" ? "ok" : ""}" style="font-size:11px">${f === "●" ? "● dados reais" : "○ exemplo"}</span>`;

// ---------- TELAS ----------

async function telaCentral() {
  setCrumb("Central");
  const [projs, aprovs] = await Promise.all([projetos(), aprovacoes()]);
  const projCards = projs.map(p => `
    <a class="card hover proj" href="#/${esc(p.slug)}">
      <div class="head"><span class="ic">${esc(p.icone)}</span>
        <div><div class="nome">${esc(p.nome)}</div>
        <div class="muted" style="font-size:12px">${esc(p.tipo)}</div></div></div>
      <div class="muted" style="font-size:12px">${statusDot(p.status)} ${esc(p.fase)} · ${esc(p.metrica.label)}: ${esc(p.metrica.value)}</div>
    </a>`).join("");

  return `
    <div class="section-title">Visão geral</div>
    <div class="grid cols-4">${API.KPIS_GLOBAIS.map(kpiCard).join("")}</div>

    <div class="section-title">Projetos plugados &nbsp; ${fonteChip(API.fonte.projetos)}</div>
    <div class="grid cols-3">${projCards}
      <div class="card hover" style="display:flex;align-items:center;justify-content:center;color:var(--faint);border-style:dashed">+ plugar projeto</div>
    </div>

    <div class="section-title">Aprovações pendentes (${aprovs.length}) &nbsp; ${fonteChip(API.fonte.aprovacoes)}</div>
    <div class="grid">${aprovs.length ? aprovs.map(approvalCard).join("")
      : `<div class="card muted">Nenhuma aprovação pendente. ✅</div>`}</div>`;
}

async function telaProjeto(slug) {
  const p = await acharProjeto(slug);
  if (!p) return `<div class="card">Projeto não encontrado.</div>`;
  setCrumb(`Projetos › <b>${esc(p.nome)}</b>`);
  const squads = await squadsDe(slug);
  const byFase = (f) => squads.filter(s => s.fase === f);

  const colFase = (f) => `<div class="fase-col"><h4>${esc(f.nome)}</h4>
    ${byFase(f.id).map(s => squadNode(s, slug)).join("") || `<div class="faint" style="font-size:12px;padding:6px">—</div>`}</div>`;

  const temFunil = p._vp; // só VP tem o funil de fases; registry mostra grade simples
  const mapa = temFunil
    ? `<div class="section-title">Mapa de squads — funil &nbsp; ${fonteChip(API.fonte.squads)}</div>
       <div class="grid" style="grid-template-columns:repeat(5,1fr)">${API.FASES.map(colFase).join("")}</div>`
    : `<div class="section-title">Squads / skills (${squads.length}) &nbsp; ${fonteChip(API.fonte.squads)}</div>
       <div class="grid cols-3">${squads.map(s => squadNode(s, slug)).join("") || "<div class='card muted'>Sem squads expostos.</div>"}</div>`;

  return `
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0 4px">
      <span style="font-size:26px">${esc(p.icone)}</span>
      <div><div style="font-weight:600;font-size:18px">${esc(p.nome)}</div>
      <div class="muted" style="font-size:12px">${statusDot(p.status)} ${esc(p.fase)} · ${squads.length} squads</div></div>
    </div>
    ${p.contexto ? `<div class="card" style="border-color:rgba(34,211,238,.25);margin-top:8px">
       <b>${esc(p.contexto.titulo)}</b> &nbsp; <span class="muted">${esc(p.contexto.sub)}</span></div>` : ""}
    ${p.kpis?.length ? `<div class="grid cols-4" style="margin-top:14px">${p.kpis.map(kpiCard).join("")}</div>` : ""}
    ${mapa}`;
}

async function telaSquad(slug, id) {
  const squads = await squadsDe(slug);
  const s = squads.find(x => x.id === id);
  const p = await acharProjeto(slug);
  if (!s) return `<div class="card">Squad não encontrado.</div>`;
  setCrumb(`Projetos › <b>${esc(p?.nome || slug)}</b> › Squads › <b>${esc(s.nome)}</b>`);
  return `
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px">
      <span style="font-size:24px">${esc(s.icone)}</span>
      <div><div style="font-weight:600;font-size:18px">${esc(s.nome)}</div>
      <div class="muted" style="font-size:12px">área: ${esc(s.area)} · responsável: ${esc(s.agente)} ${s._real ? fonteChip("●") : ""}</div></div>
      <div style="flex:1"></div>
      <button class="btn ok">Rodar agora</button>
    </div>
    ${agentContract(s)}`;
}

async function telaSquads() {
  setCrumb("Squads");
  const projs = await projetos();
  const slug = (projs.find(p => p._vp) || projs[0])?.slug;
  if (!slug) return `<div class="card">Nenhum projeto.</div>`;
  const squads = await squadsDe(slug);
  return `<div class="section-title">Squads · ${esc((await acharProjeto(slug)).nome)} &nbsp; ${fonteChip(API.fonte.squads)}</div>
    <div class="grid cols-3">${squads.map(s => squadNode(s, slug)).join("")}</div>`;
}

async function telaMetricas() {
  setCrumb("Métricas");
  return `
    <div class="section-title">Métricas que movem receita</div>
    <div class="grid cols-3">${API.METRICAS.receita.map(kpiCard).join("")}</div>
    <div class="section-title">Vaidade — fora da decisão</div>
    <div class="grid cols-3" style="opacity:.45">
      ${API.METRICAS.vaidade.map(v => `<div class="card kpi"><div class="label">${esc(v.label)}</div><div class="val">${esc(v.value)}</div></div>`).join("")}
    </div>
    <div style="margin-top:18px"><button class="btn">Abrir Ritual Semanal — Escalar / Manter / Matar</button></div>`;
}

async function telaAprovacoes() {
  setCrumb("Aprovações");
  const aprovs = await aprovacoes();
  return `<div class="section-title">Fila de aprovações (${aprovs.length}) &nbsp; ${fonteChip(API.fonte.aprovacoes)}</div>
    <div class="grid">${aprovs.length ? aprovs.map(approvalCard).join("")
      : `<div class="card muted">Nenhuma aprovação pendente. ✅</div>`}</div>`;
}

async function telaProximos() {
  setCrumb("Próximos passos");
  const col = (titulo, arr) => `<div class="col"><h4>${esc(titulo)}</h4>
    ${arr.map(t => `<div class="ktask">${esc(t.t)}<div class="s">${esc(t.squad)}</div></div>`).join("")}</div>`;
  const P = API.PROXIMOS_PASSOS;
  return `<div class="section-title">Roadmap</div>
    <div class="kanban">
      ${col("Agora", P.agora)}${col("Próximo", P.proximo)}
      ${col("Depois", P.depois)}${col("Concluído", P.concluido)}
    </div>`;
}

// ---------- ROTEADOR ----------

function setCrumb(html) { crumbEl.innerHTML = html; }

async function router() {
  const parts = location.hash.replace(/^#\//, "").split("/").filter(Boolean);
  main.innerHTML = `<div class="card muted">Carregando…</div>`;
  let html;
  try {
    if (parts.length === 0)                    html = await telaCentral();
    else if (parts[0] === "squads")            html = await telaSquads();
    else if (parts[0] === "metricas")          html = await telaMetricas();
    else if (parts[0] === "aprovacoes")        html = await telaAprovacoes();
    else if (parts[0] === "proximos")          html = await telaProximos();
    else if (parts[1] === "squad" && parts[2]) html = await telaSquad(parts[0], parts[2]);
    else                                       html = await telaProjeto(parts[0]);
  } catch (e) {
    html = `<div class="card">Erro ao carregar: ${esc(e.message)}</div>`;
  }
  main.innerHTML = html;
  main.scrollTop = 0;
  marcarNavAtivo(parts[0] || "central");
}

async function marcarNavAtivo(key) {
  const projs = cache.projetos || [];
  document.querySelectorAll(".nav-i").forEach(el => {
    el.classList.toggle("active", el.dataset.route === key
      || (el.dataset.route === "projetos" && projs.some(p => p.slug === key)));
  });
}

// status real no rodapé
async function pintarStatus() {
  const s = await API.getStatus();
  const el = document.getElementById("rail-status");
  if (el) el.innerHTML =
    `<div class="row">${statusDot(s.brain ? "online" : "offline")} cérebro · ${statusDot(s.voz ? "online" : "offline")} voz · ${statusDot(s.projetos ? "online" : "offline")} projetos</div>
     <div class="row">motor ativo: <b style="color:var(--text)">${esc(s.motor)}</b></div>`;
}

document.getElementById("toggle-rail")?.addEventListener("click", () =>
  document.querySelector(".app").classList.toggle("rail-collapsed"));

window.addEventListener("hashchange", router);
router();
pintarStatus();
