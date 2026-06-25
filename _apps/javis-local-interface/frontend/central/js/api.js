// api.js — ponte entre a Central de Comando e o backend REAL do Javis.
// Cada função busca de um endpoint e normaliza pro shape que os componentes esperam.
// Se o backend não responder (interface aberta fora do servidor), cai no mock de data.js.
import * as MOCK from "./data.js";

// quando servida pelo FastAPI (/central/), os endpoints são same-origin ("/...").
const BASE = location.origin.startsWith("http") ? "" : "http://localhost:8000";

async function getJSON(path, ms = 5000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(`${BASE}${path}`, { signal: ctrl.signal });
    if (!r.ok) throw new Error(`${path} → ${r.status}`);
    return await r.json();
  } finally { clearTimeout(t); }
}

// indica se a última leitura veio do backend (●) ou do mock (○)
export const fonte = { projetos: "?", squads: "?", aprovacoes: "?", status: "?" };

// ---- PROJETOS ----
// Junta os projetos do registry (ex.: CEREBRO.JAMPA) + a Vem Passear (squad interno).
export async function getProjects() {
  const out = [];
  // 1) registry (projetos externos plugados)
  try {
    const d = await getJSON("/projects/registry");
    for (const p of (d.projects || [])) {
      out.push({
        slug: p.slug, nome: p.nome || p.slug, icone: "🧠",
        tipo: p.empresa || "Projeto", fase: p.fase_atual ? `Fase ${p.fase_atual}` : (p.descricao_fase || "—"),
        status: p.status === "online" ? "online" : "offline",
        metrica: { label: "skills ativas", value: String(p.skills_ativas ?? "—") },
        kpis: [
          { label: "Skills ativas", value: String(p.skills_ativas ?? "—") },
          { label: "Categorias", value: String((p.skills_categorias || []).length) },
          { label: "Atualizado", value: p.fonte_da_verdade_atualizada_em || p.atualizado_em || "—" },
        ],
        _registry: true, _skills: p.skills_lista || [], _categorias: p.skills_categorias || [],
      });
    }
    fonte.projetos = "●";
  } catch { fonte.projetos = "○"; }

  // 2) Vem Passear (squad de marketing interno) — vira um "projeto" no painel
  try {
    const d = await getJSON("/vp/agents");
    if ((d.agents || []).length) {
      out.push({
        slug: "vem-passear", nome: "Vem Passear Jampa", icone: "⛵",
        tipo: "Agência de turismo", fase: "Operação", status: "online",
        metrica: { label: "squads", value: String(d.total ?? d.agents.length) },
        kpis: MOCK.PROJETOS[0]?.kpis || [],
        contexto: MOCK.PROJETOS[0]?.contexto,
        _vp: true,
      });
    }
  } catch { /* VP fica de fora se o endpoint falhar */ }

  if (!out.length) { fonte.projetos = "○"; return MOCK.PROJETOS; }
  return out;
}

// ---- SQUADS de um projeto ----
export async function getSquads(slug) {
  if (slug === "vem-passear") {
    try {
      const d = await getJSON("/vp/agents");
      fonte.squads = "●";
      return (d.agents || []).map(normalizaSquadVP);
    } catch { fonte.squads = "○"; return MOCK.SQUADS["vem-passear"] || []; }
  }
  // projetos do registry: skills viram "squads" por categoria (read-only)
  try {
    const d = await getJSON("/projects/registry");
    const p = (d.projects || []).find(x => x.slug === slug);
    if (p) { fonte.squads = "●"; return (p.skills_lista || []).map(normalizaSkill); }
  } catch { fonte.squads = "○"; }
  return [];
}

// mapeia área (group) → fase do funil
const FASE_DE = {
  inteligencia: "atrair", conteudo: "atrair", design: "operar",
  trafego: "converter", dados: "analisar",
};

function normalizaSquadVP(a) {
  return {
    id: a.id, nome: a.name, icone: a.icon || "•", area: a.group || "—",
    fase: FASE_DE[a.group] || "operar", agente: a.role || "Claude",
    faz: splitItens(a.faz), nao_faz: splitItens(a.naofaz),
    input: a.input || "—", output: a.output || "—",
    ferramentas: splitItens(a.tools, /[,;]/),
    metricas: [], rotina_diaria: "", rotina_semanal: "",
    aprovacao: "", _real: true,
  };
}

function normalizaSkill(s) {
  return {
    id: s.id, nome: s.id.replace(/-/g, " "), icone: "🧩", area: s.categoria || "—",
    fase: "operar", agente: s.papel || "—",
    faz: [], nao_faz: [], input: "—", output: "—", ferramentas: [],
    metricas: [], rotina_diaria: "", rotina_semanal: "",
    aprovacao: s.risco && s.risco !== "auto" ? `risco: ${s.risco}` : "", _real: true,
  };
}

const splitItens = (s, re = /[.;]\s*|\s•\s|·\s*/) =>
  (s ? String(s).split(re).map(x => x.trim()).filter(Boolean) : []);

// ---- APROVAÇÕES ----
export async function getApprovals() {
  try {
    const d = await getJSON("/approvals/pending");
    fonte.aprovacoes = "●";
    return (d.approvals || []).map(a => ({
      id: a.id ?? a.approval_id ?? "?",
      tipo: a.tipo || a.gate || a.kind || "Aprovação",
      projeto: a.projeto || a.project || "—",
      squad: a.squad || a.origem || "—",
      contexto: a.titulo || a.descricao || a.context || a.message || "Decisão pendente",
      previa: a.preview || a.valor || a.detalhe || "",
      tone: a.risco === "alto" ? "danger" : "warn",
    }));
  } catch { fonte.aprovacoes = "○"; return MOCK.APROVACOES; }
}

// ---- STATUS (rodapé) ----
export async function getStatus() {
  try {
    const d = await getJSON("/status");
    fonte.status = "●";
    const svc = d.services || {};
    return {
      brain: d.brain?.status === "online",
      voz: svc["Voz sandbox"]?.status === "online",
      projetos: true,
      motor: d.brain?.engine ? d.brain.engine[0].toUpperCase() + d.brain.engine.slice(1) : "—",
    };
  } catch { fonte.status = "○"; return { brain: true, voz: true, projetos: true, motor: "Claude" }; }
}

// reexporta o que ainda é só mock (KPIs globais, métricas, próximos passos)
export const KPIS_GLOBAIS = MOCK.KPIS_GLOBAIS;
export const METRICAS = MOCK.METRICAS;
export const PROXIMOS_PASSOS = MOCK.PROXIMOS_PASSOS;
export const FASES = MOCK.FASES;
