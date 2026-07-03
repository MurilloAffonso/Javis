// World — mapa isométrico dos setores/agentes — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, state, sc, setView } from "../../app.js";

const SECTORS = ["Core", "Projetos", "Marketing", "Vendas", "Conteúdo", "Dados", "Desenvolvimento", "Operação", "Automações"];

// posições no grid isométrico (col,row) e ícone por setor
const SECTOR_CELL = {
  "Core": [2, 2], "Projetos": [2, 1], "Automações": [3, 1], "Dados": [3, 2],
  "Desenvolvimento": [3, 3], "Conteúdo": [2, 3], "Operação": [1, 3],
  "Marketing": [1, 2], "Vendas": [1, 1],
};
const SECTOR_ICON = { "Core": "🧠", "Projetos": "📦", "Marketing": "📣", "Vendas": "💰",
  "Conteúdo": "✍️", "Dados": "📊", "Desenvolvimento": "⚙️", "Operação": "🛠️", "Automações": "🤖" };

function viewWorld(body) {
  body.appendChild(h(`<div class="section-h">Javes World — mapa de setores e agentes</div>`));
  const stage = h(`<div class="iso-stage"></div>`);
  const TW = 92, TH = 46, ORIGIN_Y = 80; // espaçamento isométrico
  // ordena por profundidade (col+row) p/ empilhar corretamente
  const ordered = [...SECTORS].sort((a, b) => {
    const ca = SECTOR_CELL[a] || [2, 2], cb = SECTOR_CELL[b] || [2, 2];
    return (ca[0] + ca[1]) - (cb[0] + cb[1]);
  });
  ordered.forEach((sec) => {
    const [col, row] = SECTOR_CELL[sec] || [2, 2];
    const dx = (col - row) * TW;
    const dy = (col + row) * TH + ORIGIN_Y;
    const ags = agentsForSector(sec);
    const plat = h(`<div class="iso-plat ${ags.length ? "" : "iso-empty"}" style="left:calc(50% + ${dx}px);top:${dy}px"></div>`);
    stage.appendChild(plat);
    const avas = ags.slice(0, 4).map((a) => `<span class="iso-ava" title="${a.nome}">${(a.nome || "?")[0]}</span>`).join("");
    const executing = ags.some((a) => sc(a.status) === "run");
    const node = h(`<div class="iso-node" style="left:calc(50% + ${dx}px);top:${dy}px">
      <div class="iso-tower ${executing ? "exec" : ""}">${SECTOR_ICON[sec] || "🌐"}</div>
      <div class="iso-name">${sec}</div>
      <div class="iso-count">${ags.length} agente(s)</div>
      ${avas ? `<div class="iso-avas">${avas}</div>` : ""}
    </div>`);
    if (ags.length) { node.style.cursor = "pointer"; node.title = "Abrir chat de " + ags[0].nome; node.onclick = () => { state.activeAgentId = ags[0].id; setView("chat"); }; }
    stage.appendChild(node);
  });
  body.appendChild(stage);

  // Lista por setor (legibilidade)
  const world = h(`<div class="world"></div>`);
  SECTORS.forEach((sec) => {
    const ags = agentsForSector(sec);
    const pills = ags.map((a) => `<span class="agent-pill"><span class="dot ${sc(a.status)}"></span>${a.nome}</span>`).join("") || `<span class="card-sub">— vazio —</span>`;
    world.appendChild(h(`<div class="sector"><h4>${SECTOR_ICON[sec] || "🌐"} ${sec}</h4>${pills}</div>`));
  });
  body.appendChild(world);
}
function agentsForSector(sec) {
  const s = sec.toLowerCase();
  return state.agents.filter((a) => {
    const tags = (a.tags || []).map((t) => t.toLowerCase());
    if (s === "core") return a.tipo === "orquestrador";
    if (s === "desenvolvimento") return a.tipo === "executor" || a.projeto === "javis-dev";
    if (s === "projetos") return a.projeto === "vempassear" && a.tipo === "especialista";
    if (s === "dados") return tags.includes("dados");
    if (s === "marketing") return tags.includes("marketing");
    if (s === "vendas") return tags.includes("vendas") || tags.includes("atendimento");
    if (s === "conteúdo") return tags.includes("conteudo");
    if (s === "operação") return a.squad === "operacao";
    return false;
  });
}

export { viewWorld };
