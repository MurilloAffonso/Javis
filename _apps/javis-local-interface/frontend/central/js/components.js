// components.js — componentes reutilizáveis (funções puras que retornam HTML string).
// Cada um é usado em mais de uma tela. Sem dependências externas.

export const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// statusDot(status) → bolinha de status. status: online | warn | offline
export const statusDot = (status = "online") => `<span class="dot ${esc(status)}"></span>`;

// trendBadge(n) → variação % com seta. n>0 sobe, n<0 desce, 0 neutro.
export function trendBadge(n) {
  if (n === 0 || n == null) return `<span class="trend flat">—</span>`;
  const up = n > 0;
  const cls = up ? "up" : (n < 0 ? "down" : "flat"); // queda de CAC/custo também é "bom" (verde) por padrão
  const arrow = up ? "▲" : "▼";
  return `<span class="trend ${cls}">${arrow} ${Math.abs(n)}%</span>`;
}

// sparkline(arr) → mini gráfico SVG a partir de um array de números.
export function sparkline(data = [], color = "var(--accent)") {
  if (!data.length) return "";
  const w = 120, h = 26, max = Math.max(...data), min = Math.min(...data);
  const rng = max - min || 1;
  const pts = data.map((v, i) =>
    `${(i / (data.length - 1)) * w},${h - ((v - min) / rng) * h}`).join(" ");
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" width="100%">
    <polyline fill="none" stroke="${color}" stroke-width="2" points="${pts}"/>
  </svg>`;
}

// kpiCard({label,value,trend,spark}) → cartão de métrica.
export function kpiCard({ label, value, trend, spark, tone }) {
  const color = tone === "ok" ? "var(--ok)" : tone === "warn" ? "var(--warn)" : "var(--accent)";
  return `<div class="card kpi">
    <div class="label">${esc(label)}</div>
    <div class="val">${esc(value)}</div>
    ${trend !== undefined ? trendBadge(trend) : ""}
    ${spark ? sparkline(spark, color) : ""}
  </div>`;
}

// projectCard(p) → cartão de projeto (clicável, vai pra #/<slug>).
export function projectCard(p) {
  return `<a class="card hover proj" href="#/${esc(p.slug)}">
    <div class="head">
      <span class="ic">${esc(p.icone)}</span>
      <div><div class="nome">${esc(p.nome)}</div>
      <div class="muted" style="font-size:12px">${esc(p.tipo)}</div></div>
    </div>
    <div class="muted" style="font-size:12px">${statusDot("online")} ${esc(p.fase)} · ${esc(SQUADS_COUNT(p.slug))} squads</div>
    <div class="mono" style="font-size:13px">${esc(p.metrica.label)}: <b>${esc(p.metrica.value)}</b></div>
  </a>`;
}
let SQUADS_COUNT = () => "—"; // injetado pelo app
export const setSquadsCount = (fn) => { SQUADS_COUNT = fn; };

// squadNode(s, slug) → nó de squad clicável no mapa.
export function squadNode(s, slug) {
  const m = s.metricas?.[0];
  return `<a class="snode" href="#/${esc(slug)}/squad/${esc(s.id)}" style="border-left-color:${esc(corArea(s.area))}">
    <div class="t">${esc(s.icone)} ${esc(s.nome)} ${statusDot("online")}</div>
    ${m ? `<div class="m">${esc(m.label)}: ${esc(m.value)} ${trendBadge(m.trend)}</div>` : ""}
  </a>`;
}

// approvalCard(a) → cartão de aprovação com ações.
export function approvalCard(a) {
  return `<div class="card appr">
    <span class="chip ${esc(a.tone || "warn")}">${esc(a.tipo)}</span>
    <div class="body">
      <div><b>${esc(a.contexto)}</b></div>
      <div class="muted" style="font-size:12px">${esc(a.squad)} · ${esc(a.projeto)} · <span class="mono">${esc(a.previa)}</span></div>
    </div>
    <div class="actions">
      <button class="btn ok">Aprovar</button>
      <button class="btn">Ajustar</button>
      <button class="btn ghost">Recusar</button>
    </div>
  </div>`;
}

// agentContract(s) → o Squad Contract completo (tela de detalhe).
export function agentContract(s) {
  const li = (arr) => arr.map(x => `<li>${esc(x)}</li>`).join("");
  return `<div class="card">
    <div class="contract">
      <div>
        <div class="field"><div class="k">Faz</div><ul>${li(s.faz)}</ul></div>
        <div class="field"><div class="k">Não faz (delega)</div><ul>${li(s.nao_faz)}</ul></div>
        <div class="field"><div class="k">Ferramentas</div>
          ${s.ferramentas.map(f => `<span class="chip">${esc(f)}</span>`).join(" ")}</div>
        <div class="field"><div class="k">Responsável</div><div>${esc(s.agente)}</div></div>
      </div>
      <div>
        <div class="field"><div class="k">Input ←</div><div>${esc(s.input)}</div></div>
        <div class="field"><div class="k">Output →</div><div>${esc(s.output)}</div></div>
        <div class="field"><div class="k">Métricas</div>
          <div class="grid cols-3" style="gap:8px">${s.metricas.map(kpiCard).join("")}</div></div>
        <div class="field"><div class="k">Rotina diária</div><div class="muted">${esc(s.rotina_diaria)}</div></div>
        <div class="field"><div class="k">Rotina semanal</div><div class="muted">${esc(s.rotina_semanal)}</div></div>
      </div>
    </div>
    <div class="approval-banner">⚠ Aprovação humana: ${esc(s.aprovacao)}</div>
  </div>`;
}

// corArea — cor do acento por área (espelha COR_AREA do data.js sem import circular).
function corArea(area) {
  return ({
    conteudo: "var(--ai)", trafego: "var(--accent)", operacao: "var(--ok)",
    retencao: "var(--warn)", dados: "var(--ai)", oferta: "var(--accent)",
    inteligencia: "var(--ok)",
  })[area] || "var(--accent)";
}
