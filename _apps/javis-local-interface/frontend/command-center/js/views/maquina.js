// A Máquina — pipeline de conhecimento do Javis em grafo (DAG esquerda→direita).
// Nós = etapas; arestas SVG curvas por trás; fluxo principal com tracejado animado.
// CSS próprio, injetado de forma idempotente (não toca no styles.css global).
import { h } from "../../app.js";

// ---------- Definição do grafo ----------
// Cada nó: posição em % (centro), título, ícone, métrica (número grande), unidade,
// e um "extra" opcional: sparkline (barras) ou gauge (anel).
const NODES = [
  { key: "capture",    left: 9,  top: 28, icon: "📡", title: "Capture",       metric: "6",          unit: "fontes · captura contínua" },
  { key: "classify",   left: 25, top: 20, icon: "🧭", title: "Classify",      metric: "0.45–1.0",   unit: "confiança do roteador", gauge: 72 },
  { key: "embed",      left: 41, top: 30, icon: "🧬", title: "Embed",         metric: "1536",       unit: "dims · text-embedding-3" },
  { key: "insights",   left: 57, top: 18, icon: "💡", title: "Insights",      metric: "142",        unit: "insights únicos", spark: [30, 55, 40, 70, 52, 88, 64] },
  { key: "grafo",      left: 72, top: 27, icon: "🕸️", title: "Grafo",         metric: "100",        unit: "nós · 1.690 arestas", spark: [40, 60, 50, 80, 66, 92, 74] },
  { key: "agente",     left: 89, top: 46, icon: "🤖", title: "Agente vivo",   metric: "1.688 +142", unit: "o clone que conversa", hero: true },
  { key: "guard",      left: 9,  top: 64, icon: "🛡️", title: "Guard",         metric: "6",          unit: "bloqueios" },
  { key: "route",      left: 27, top: 56, icon: "🔀", title: "Route + Bucket", metric: "248",       unit: "itens roteados" },
  { key: "chunk",      left: 43, top: 68, icon: "🧩", title: "Chunk",         metric: "248",        unit: "blocos" },
  { key: "rag",        left: 58, top: 56, icon: "🔎", title: "RAG Index",     metric: "7.247",      unit: "vetores · FTS5 + cosine · RRF", spark: [50, 68, 44, 82, 60, 90, 78] },
  { key: "identity",   left: 60, top: 82, icon: "🪪", title: "Identity · Voz", metric: "5",         unit: "dossiês · 10 dimensões DNA" },
  { key: "checkpoint", left: 75, top: 74, icon: "💾", title: "Checkpoint",    metric: "142",        unit: "salvos" },
  { key: "dossie",     left: 85, top: 62, icon: "📄", title: "Dossiê",        metric: "1.688",      unit: "tokens" },
];

// Arestas: hot = fluxo principal (animado/quente); as demais são frias.
const EDGES = [
  // fluxo principal (quente, animado)
  { from: "capture", to: "classify", hot: true },
  { from: "classify", to: "embed", hot: true },
  { from: "embed", to: "insights", hot: true },
  { from: "insights", to: "grafo", hot: true },
  { from: "grafo", to: "agente", hot: true },
  // ramais frios
  { from: "capture", to: "guard" },
  { from: "classify", to: "route" },
  { from: "route", to: "chunk" },
  { from: "chunk", to: "rag" },
  { from: "rag", to: "identity" },
  { from: "identity", to: "checkpoint" },
  { from: "checkpoint", to: "dossie" },
  { from: "dossie", to: "agente" },
  { from: "embed", to: "rag" },
];

// ---------- CSS (injetado uma única vez) ----------
function ensureStyles() {
  if (document.getElementById("maquina-styles")) return;
  const style = document.createElement("style");
  style.id = "maquina-styles";
  style.textContent = `
  .mq-wrap {
    position: relative; height: 640px; min-height: 640px; overflow: hidden;
    border-radius: 14px; border: 1px solid var(--border);
    background-color: var(--bg);
    background-image:
      radial-gradient(var(--border) 1px, transparent 1px),
      radial-gradient(var(--border) 1px, transparent 1px);
    background-size: 26px 26px, 26px 26px;
    background-position: 0 0, 13px 13px;
    font-family: var(--font);
  }
  /* leve brilho quente no canto do agente vivo */
  .mq-wrap::after {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(420px 320px at 88% 46%, var(--accent-soft), transparent 70%);
  }

  .mq-edges { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none; }
  .mq-edge-cold { fill: none; stroke: var(--border-2); stroke-width: 1.5; opacity: .8; }
  .mq-edge-hot  { fill: none; stroke: var(--accent); stroke-width: 2.2; opacity: .95;
    stroke-dasharray: 7 9; filter: drop-shadow(0 0 4px var(--accent-soft));
    animation: mq-dash 1.1s linear infinite; }
  @keyframes mq-dash { to { stroke-dashoffset: -32; } }

  /* Cabeçalho e métricas (overlay no topo) */
  .mq-head {
    position: absolute; top: 0; left: 0; right: 0; z-index: 3;
    display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;
    padding: 14px 18px; pointer-events: none;
    background: linear-gradient(var(--bg), transparent);
  }
  .mq-head-title { font-size: 15px; font-weight: 700; color: var(--text); letter-spacing: .2px; }
  .mq-head-title b { color: var(--accent); font-weight: 700; }
  .mq-head-sub { font-size: 11.5px; color: var(--muted); margin-top: 3px; max-width: 460px; line-height: 1.45; }
  .mq-head-metrics { text-align: right; font-size: 11.5px; color: var(--muted-2); white-space: nowrap; }
  .mq-head-metrics b { color: var(--accent-2); font-variant-numeric: tabular-nums; }

  /* Nós */
  .mq-node {
    position: absolute; z-index: 2; width: 150px; transform: translate(-50%, -50%);
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-sm);
    padding: 9px 11px 10px; box-shadow: 0 6px 18px rgba(0,0,0,.35);
    transition: border-color .18s, transform .18s, box-shadow .18s;
  }
  .mq-node:hover { border-color: var(--border-2); background: var(--card-hover);
    transform: translate(-50%, -50%) translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,.45); }
  .mq-node-head { display: flex; align-items: center; gap: 7px; margin-bottom: 6px; }
  .mq-ico { font-size: 14px; line-height: 1; filter: saturate(1.1); }
  .mq-title { font-size: 11.5px; font-weight: 600; color: var(--muted); letter-spacing: .3px; text-transform: uppercase; }
  .mq-metric { font-size: 23px; font-weight: 800; color: var(--text); line-height: 1.05;
    font-variant-numeric: tabular-nums; letter-spacing: -.3px; }
  .mq-unit { font-size: 10px; color: var(--muted-2); margin-top: 3px; line-height: 1.3; }

  /* Nó HERO (agente vivo) */
  .mq-node.hero {
    width: 172px; border: 1.5px solid var(--accent);
    background: linear-gradient(180deg, var(--card-hover), var(--card));
    box-shadow: 0 0 0 1px var(--accent-soft), 0 10px 30px rgba(0,0,0,.5), 0 0 26px var(--accent-soft);
    animation: mq-pulse 2.6s ease-in-out infinite;
  }
  .mq-node.hero .mq-title { color: var(--accent-2); }
  .mq-node.hero .mq-metric { color: var(--accent-2); font-size: 25px; }
  @keyframes mq-pulse {
    0%, 100% { box-shadow: 0 0 0 1px var(--accent-soft), 0 10px 30px rgba(0,0,0,.5), 0 0 20px var(--accent-soft); }
    50%      { box-shadow: 0 0 0 1px var(--accent-soft), 0 10px 30px rgba(0,0,0,.5), 0 0 34px var(--accent-soft); }
  }

  /* Sparkline */
  .mq-spark { display: flex; align-items: flex-end; gap: 2px; height: 20px; margin-top: 7px; }
  .mq-spark i { flex: 1; background: linear-gradient(var(--accent-2), var(--accent)); border-radius: 2px 2px 0 0; opacity: .85; }

  /* Gauge (anel) */
  .mq-gauge { position: absolute; top: 9px; right: 10px; width: 34px; height: 34px; border-radius: 50%;
    display: grid; place-items: center;
    background: conic-gradient(var(--accent) calc(var(--g) * 1%), var(--border-2) 0); }
  .mq-gauge::before { content: ""; position: absolute; inset: 4px; border-radius: 50%; background: var(--card); }
  .mq-gauge span { position: relative; font-size: 9.5px; font-weight: 700; color: var(--accent-2); font-variant-numeric: tabular-nums; }

  /* Mini console de log */
  .mq-console {
    position: absolute; left: 14px; bottom: 12px; z-index: 3; max-width: 340px;
    background: rgba(10, 9, 8, .72); border: 1px solid var(--border); border-radius: var(--radius-sm);
    padding: 8px 11px; font-size: 10.5px; line-height: 1.7; color: var(--muted);
    font-variant-numeric: tabular-nums; backdrop-filter: blur(2px);
  }
  .mq-console b { color: var(--accent-2); }
  .mq-console .mq-dot { color: var(--ok); }

  @media (prefers-reduced-motion: reduce) {
    .mq-edge-hot { animation: none; }
    .mq-node.hero { animation: none; }
  }
  `;
  document.head.appendChild(style);
}

// ---------- Helpers de render ----------
function sparkHtml(vals) {
  return `<div class="mq-spark">${vals.map((v) => `<i style="height:${Math.max(8, Math.min(100, v))}%"></i>`).join("")}</div>`;
}

function nodeHtml(n) {
  const gauge = n.gauge != null ? `<div class="mq-gauge" style="--g:${n.gauge}"><span>${n.gauge}%</span></div>` : "";
  const spark = n.spark ? sparkHtml(n.spark) : "";
  return `<div class="mq-node ${n.hero ? "hero" : ""}" id="mq-${n.key}" style="left:${n.left}%;top:${n.top}%">
    ${gauge}
    <div class="mq-node-head"><span class="mq-ico">${n.icon}</span><span class="mq-title">${n.title}</span></div>
    <div class="mq-metric">${n.metric}</div>
    <div class="mq-unit">${n.unit}</div>
    ${spark}
  </div>`;
}

// ---------- View ----------
export function viewMaquina(body) {
  ensureStyles();

  const wrap = h(`<div class="mq-wrap"></div>`);

  // Cabeçalho + métricas (topo direito)
  wrap.appendChild(h(`<div class="mq-head">
    <div>
      <div class="mq-head-title">A Máquina — <b>pipeline de conhecimento</b> · 13 etapas</div>
      <div class="mq-head-sub">Da captura de fontes ao clone que conversa: cada nó é uma etapa e o fluxo quente é o caminho vivo do conhecimento.</div>
    </div>
    <div class="mq-head-metrics"><b>6</b> estágios · <b>248</b> chunks · <b>142</b> insights · <b>1</b> agente</div>
  </div>`));

  // SVG das arestas (atrás dos nós). Um <path> por aresta, atualizado no draw().
  const SVGNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(SVGNS, "svg");
  svg.setAttribute("class", "mq-edges");
  const paths = EDGES.map((e) => {
    const p = document.createElementNS(SVGNS, "path");
    p.setAttribute("class", e.hot ? "mq-edge-hot" : "mq-edge-cold");
    svg.appendChild(p);
    return p;
  });
  wrap.appendChild(svg);

  // Nós
  NODES.forEach((n) => wrap.appendChild(h(nodeHtml(n))));

  // Mini console de log
  wrap.appendChild(h(`<div class="mq-console">
    <div><span class="mq-dot">●</span> capture: <b>6</b> fontes sincronizadas</div>
    <div><span class="mq-dot">●</span> classify: confiança média <b>0.72</b></div>
    <div><span class="mq-dot">●</span> embed → rag: <b>248</b> blocos · <b>7.247</b> vetores</div>
    <div><span class="mq-dot">●</span> agente vivo: dossiê <b>1.688</b> tokens (<b>+142</b>)</div>
  </div>`));

  body.appendChild(wrap);

  // ---------- Desenho das arestas (após o DOM montar) ----------
  const centerOf = (key, wrapRect) => {
    const el = wrap.querySelector("#mq-" + key);
    const r = el.getBoundingClientRect();
    return { x: r.left - wrapRect.left + r.width / 2, y: r.top - wrapRect.top + r.height / 2 };
  };

  const draw = () => {
    const wr = wrap.getBoundingClientRect();
    if (!wr.width) return;
    svg.setAttribute("width", wr.width);
    svg.setAttribute("height", wr.height);
    svg.setAttribute("viewBox", `0 0 ${wr.width} ${wr.height}`);
    EDGES.forEach((e, i) => {
      const a = centerOf(e.from, wr);
      const b = centerOf(e.to, wr);
      // Bézier cúbica com controles horizontais → curvas suaves estilo DAG.
      const dx = Math.max(40, Math.abs(b.x - a.x) * 0.5);
      paths[i].setAttribute("d", `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`);
    });
  };

  // Desenha no próximo frame (garante que os nós já têm layout) e re-desenha no resize.
  requestAnimationFrame(() => requestAnimationFrame(draw));
  const onResize = () => draw();
  window.addEventListener("resize", onResize);
  // Auto-limpeza: quando o container sai do DOM (troca de view), remove o listener.
  const mo = new MutationObserver(() => {
    if (!document.body.contains(wrap)) {
      window.removeEventListener("resize", onResize);
      mo.disconnect();
    }
  });
  mo.observe(document.body, { childList: true, subtree: true });
}

export default viewMaquina;
