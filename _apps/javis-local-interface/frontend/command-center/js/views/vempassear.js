// Vem Passear — view do projeto conectado. Extraído de app.js em 2026-07-02.
// MESMO comportamento; agora é um módulo ES que importa os helpers do núcleo.
import { _esc, h, $, state, BACKEND, tryJson, withProjectId, renderCanvas, opToast, opSend, confirmStrong } from "../../app.js";

// Fronteira: projeto EXTERNO do Cérebro Jampa, consultado pelo Javes por registro.
// NÃO mistura contexto com o núcleo. Escritas reais existem desde 2026-07-03
// (lead, funil, sugestão do squad, rodar agente) e TODAS passam por confirmação
// forte (confirmStrong). Nenhum envio/publicação automático. Tudo escapado.
let _vpTab = "resumo";
const vpUrl = (path) => withProjectId(BACKEND + path.replace(/^\/+/, ""));
const VP_TABS = [
  { id: "resumo",      label: "Resumo" },
  { id: "atendimento", label: "Atendimento" },
  { id: "funil",       label: "Funil" },
  { id: "reservas",    label: "Reservas" },
  { id: "voucher",     label: "Voucher" },
  { id: "agenda",      label: "Agenda" },
  { id: "posvenda",    label: "Pós-venda" },
  { id: "marketing",   label: "Marketing" },
  { id: "resultados",  label: "Resultados" },
  { id: "gates",       label: "Gates" },
  { id: "agentes",     label: "Agentes" },
];
// Abas "· legado" (Passeios/Clientes/Conteúdos/Pauta) removidas em 2026-07-03 —
// minimalismo. Forms de escrita correspondentes: ver _arquitetura/catalogo-acoes-risco.md.
const vpBRL = (v) => { const n = Number(v); return isNaN(n) ? _esc(String(v ?? "—")) : "R$ " + n.toFixed(2).replace(".", ","); };
const vpMask = (s) => { const t = String(s || "").trim(); if (!t) return ""; if (t.length <= 4) return "••"; return t.slice(0, 2) + "•••" + t.slice(-2); };

const VP_DISPATCH = {
  resumo: vpResumo, atendimento: vpAtendimento, funil: vpFunil, reservas: vpReservas,
  voucher: vpVoucherTab, agenda: vpAgenda, posvenda: vpPosVenda, marketing: vpMarketing,
  resultados: vpResultados, gates: vpGates, agentes: vpAgentes,
};
const VP_ONLINE_ONLY = new Set(["agentes"]);

function viewVempassear(body) {
  body.appendChild(h(`<div class="vp-boundary">🔗 <b>Projeto conectado via Cérebro Jampa.</b> O Javes consulta e organiza este projeto <b>por registro</b>, sem misturar contexto automaticamente com o núcleo. Escritas reais (lead, funil, agente) sempre passam por <b>confirmação forte</b>.</div>`));
  if (!state.online) body.appendChild(h(`<div class="banner">⚠️ Backend offline — as telas operacionais seguem com dados sintéticos. A aba Agentes precisa do servidor em <code>:8000</code>.</div>`));
  const chips = h(`<div class="vp-chips"></div>`);
  VP_TABS.forEach((t) => {
    const c = h(`<button class="vp-chip${t.id === _vpTab ? " active" : ""}">${_esc(t.label)}</button>`);
    c.onclick = () => { _vpTab = t.id; renderCanvas(); };
    chips.appendChild(c);
  });
  body.appendChild(chips);
  body.appendChild(h(`<div id="vp-content" class="vp-content"><div class="card-sub">Carregando…</div></div>`));
  if (VP_ONLINE_ONLY.has(_vpTab) && !state.online) { $("vp-content").innerHTML = `<div class="banner">⚠️ Esta aba precisa do backend em <code>:8000</code>.</div>`; return; }
  (VP_DISPATCH[_vpTab] || vpResumo)();
}

async function vpResumo() {
  const host = $("vp-content"); if (!host) return;
  let resumo = {};
  if (state.online) { try { resumo = (await tryJson(vpUrl("vp/passeios"))).resumo || {}; } catch (_) {} }
  host.innerHTML = `
    <div class="vp-card">
      <div class="vp-row"><span class="vp-k">Nome</span><span class="vp-v">Vem Passear Jampa</span></div>
      <div class="vp-row"><span class="vp-k">Projeto externo</span><span class="vp-v">Cérebro Jampa</span></div>
      <div class="vp-row"><span class="vp-k">Relação</span><span class="vp-v">conectado ao Javes por registro</span></div>
      <div class="vp-row"><span class="vp-k">Estado</span><span class="vp-v"><span class="badge ${state.online ? "ok" : "wait"}"><span class="dot ${state.online ? "ok" : "wait"}"></span>${state.online ? "online" : "offline"}</span></span></div>
    </div>
    <div class="section-h" style="margin-top:16px">Resumo operacional (projeto conectado)</div>
    <div class="vp-stats">
      <div class="vp-stat"><div class="vp-stat-n">${_esc(String(resumo.total_passeios ?? 0))}</div><div class="vp-stat-l">passeios</div></div>
      <div class="vp-stat"><div class="vp-stat-n">${_esc(String(resumo.total_pessoas ?? 0))}</div><div class="vp-stat-l">pessoas</div></div>
      <div class="vp-stat"><div class="vp-stat-n">${vpBRL(resumo.faturamento ?? 0)}</div><div class="vp-stat-l">faturamento</div></div>
    </div>`;

  // ---- Dashboard do dia (sintético + leads reais em leitura quando online) ----
  await vpSyncRealLeads();
  if (_vpTab !== "resumo" || !$("vp-content")) return;
  const leadsHoje = AT_LEADS.filter((l) => l.status === "Lead novo").length + _vpRealLeads.length;
  const reservasPendentes = AT_LEADS.filter((l) => ["Proposta enviada", "Aguardando reserva"].includes(l.status)).length;
  const vouchersPendentes = AT_LEADS.filter((l) => l.status === "Reserva paga").length;
  const passeiosHoje = AT_LEADS.filter((l) => l.reserva.data === VP_HOJE).length;
  const saldosAReceber = AT_LEADS.reduce((s, l) => s + (l.reserva.saldo || 0), 0);
  const posVendaPendente = AT_LEADS.filter((l) => ["Voucher gerado", "Passeio realizado"].includes(l.status)).length;
  const tarefasUrgentes = AT_LEADS.filter((l) => l.prioridade === "alta").length;
  const conteudosPendentes = AT_MKT.filter((c) => c.status !== "Publicado").length;

  const dashCards = [
    ["👥", "Leads de hoje", leadsHoje], ["📝", "Reservas pendentes", reservasPendentes],
    ["🎫", "Vouchers pendentes", vouchersPendentes], ["🗓️", "Passeios de hoje", passeiosHoje],
    ["💰", "Saldos a receber", vpBRL(saldosAReceber)], ["⭐", "Pós-venda pendente", posVendaPendente],
    ["🔥", "Tarefas urgentes", tarefasUrgentes], ["✍️", "Conteúdos pendentes", conteudosPendentes],
  ];
  host.insertAdjacentHTML("beforeend", `<div class="section-h" style="margin-top:20px">📅 Dashboard do dia <span class="card-sub">(dados sintéticos)</span></div>`);
  const grid = h(`<div class="at-dash-grid"></div>`);
  dashCards.forEach(([ic, label, val]) => grid.appendChild(h(`<div class="at-dash-card"><div class="at-dash-ic">${ic}</div><div class="at-dash-n">${_esc(String(val))}</div><div class="at-dash-l">${_esc(label)}</div></div>`)));
  host.appendChild(grid);

  host.insertAdjacentHTML("beforeend", `<div class="section-h" style="margin-top:18px">🚨 Prioridade do dia</div>`);
  const alerts = h(`<div class="at-dash-alerts"></div>`);
  ["Confirmar reservas sem voucher.", "Conferir passageiros/manifesto.", "Pedir avaliações dos passeios realizados."].forEach((a) => alerts.appendChild(h(`<div class="at-dash-alert">⚠️ ${_esc(a)}</div>`)));
  host.appendChild(alerts);

  const btns = h(`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px"></div>`);
  const bNovo = h(`<button class="op-btn studio">➕ Novo atendimento</button>`);
  bNovo.onclick = () => vpNovoAtendimento();
  const bAgenda = h(`<button class="op-btn ghost">📅 Ver agenda</button>`);
  bAgenda.onclick = () => { _vpTab = "agenda"; renderCanvas(); };
  const bReservas = h(`<button class="op-btn ghost">📋 Ver reservas</button>`);
  bReservas.onclick = () => { _vpTab = "reservas"; renderCanvas(); };
  btns.append(bNovo, bAgenda, bReservas);
  host.appendChild(btns);
}

// Novo atendimento REAL: cria lead via POST /vp/clientes (escrita no projeto
// conectado — exige confirmação forte). Aparece no Funil/Atendimento como 🔗.
function vpNovoAtendimento() {
  if (!state.online) { opToast("Backend offline — não dá pra cadastrar agora.", "err"); return; }
  const ov = vpVisualModal("➕ Novo atendimento (lead real)", `
    <div class="vp-form-row">
      <input id="vpna-nome" class="cs-input vp-in" placeholder="nome do cliente" />
      <input id="vpna-contato" class="cs-input vp-in" placeholder="contato (WhatsApp)" />
    </div>
    <textarea id="vpna-obs" class="cv-task" placeholder="interesse/observação (ex: Escuna sábado, 4 adultos)…"></textarea>`,
    { extraActions: [{ label: "➕ Cadastrar lead", onClick: () => {
      const nome = ($("vpna-nome").value || "").trim();
      const contato = ($("vpna-contato").value || "").trim();
      const obs = ($("vpna-obs").value || "").trim();
      if (!nome) { opToast("Informe o nome.", "warn"); return; }
      confirmStrong({
        title: "Cadastrar lead (Vem Passear · projeto conectado)",
        endpoint: "/vp/clientes", method: "POST", target: nome,
        before: "—", after: "cria lead real" + (contato ? " · " + vpMask(contato) : ""),
        risk: "leve", phrase: "CONFIRMAR",
        onConfirm: async () => {
          try {
            const res = await opSend(vpUrl("vp/clientes"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome, contato, obs }) });
            if (res.ok && res.data.status === "ok") { opToast("Lead cadastrado. 🔗", "ok"); ov.remove(); renderCanvas(); }
            else opToast(res.data.message || ("Falha (" + res.status + ")"), "warn");
          } catch (e) { opToast("Backend offline — não cadastrei.", "err"); }
        },
      });
    } }] });
}

async function vpAgentes() {
  const host = $("vp-content"); if (!host) return;
  let agents = [];
  try { agents = (await tryJson(vpUrl("vp/agents"))).agents || []; }
  catch (e) { host.innerHTML = `<div class="card-sub">Não consegui carregar os agentes.</div>`; return; }
  if (!agents.length) { host.innerHTML = `<div class="op-empty">Nenhum agente VP.</div>`; return; }
  host.innerHTML = `<div class="card-sub" style="margin-bottom:10px">Squad da Vem Passear. Execução real via <code>/vp/agents/run</code> — sempre com confirmação forte.</div>`;
  agents.forEach((a) => {
    const ic = a.icon || "🤖";
    const card = h(`<div class="vp-item">
      <div class="vp-item-h">${ic} <span class="vp-agent-nome"></span></div>
      <div class="vp-item-meta"></div>
      ${a.metrica ? `<div class="vp-item-meta" style="margin-top:2px">🎯 <b>Métrica:</b> ${_esc(a.metrica)}</div>` : ""}
      <div class="vp-agent-run" style="margin-top:8px">
        <textarea class="cv-task vp-agent-task" placeholder="tarefa para este agente…" style="min-height:52px"></textarea>
        <div style="text-align:right;margin-top:6px"><button class="op-btn studio sm vp-agent-go">▶ Rodar agente</button></div>
        <div class="vp-agent-out card-sub" style="white-space:pre-wrap"></div>
      </div>
    </div>`);
    card.querySelector(".vp-agent-nome").textContent = a.name || a.nome || "(agente)";
    card.querySelector(".vp-item-meta").textContent = a.role || a.papel || "";
    const go = card.querySelector(".vp-agent-go"), out = card.querySelector(".vp-agent-out");
    go.onclick = () => {
      const task = (card.querySelector(".vp-agent-task").value || "").trim();
      if (!task) { opToast("Escreva a tarefa do agente.", "warn"); return; }
      confirmStrong({
        title: "Rodar agente VP (execução real)",
        endpoint: "/vp/agents/run", method: "POST", target: (a.name || a.id),
        before: "—", after: "executa: " + task.slice(0, 60), risk: "alto", phrase: "CONFIRMAR",
        onConfirm: async () => {
          go.disabled = true; out.textContent = "⏳ Executando (pode levar um pouco)…";
          try {
            const r = await tryJson(vpUrl("vp/agents/run"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent_id: a.id, task }) });
            out.textContent = r.status === "ok" ? (r.result || "(sem saída)") : ("⚠️ " + (r.message || "falhou"));
          } catch (e) { out.textContent = "Falhou: " + e.message; }
          go.disabled = false;
        },
      });
    };
    host.appendChild(card);
  });
}

// ---------- Atendimento (VP · MVP1 — 3 colunas, visual/frontend-only) ----------
// Dados sintéticos só pra visual. Nenhuma escrita real: nem em disco, nem em backend.
// Resolve: briefing incompleto, lead perdido no WhatsApp, proposta confusa,
// reserva sem controle, voucher manual. IA aparece só como copiloto discreto.
const AT_FUNNEL = ["Lead novo", "Em atendimento", "Proposta enviada", "Aguardando reserva", "Reserva paga", "Voucher gerado", "Passeio realizado", "Pós-venda"];
const VP_HOJE = "2026-07-03"; // referência sintética de "hoje" pra Dashboard/Agenda
const VP_CONTATO = "(24) 99999-0000 · contato@vempassearjampa.com.br";
const VP_INSTRUCOES = "Chegar 15 min antes no ponto de encontro. Levar documento com foto e protetor solar.";
const VP_POLITICA_CANCEL = "Cancelamento com até 48h de antecedência: reembolso de 80% do sinal. Depois disso, sem reembolso.";

const AT_LEADS = [
  {
    id: "l1", cliente: "Marina Silva", telefone: "24991230001", status: "Em atendimento", passeio: "Escuna · Ilha Grande",
    ultimaMsg: "Quanto fica pra 4 adultos e 2 crianças?", prioridade: "alta",
    proximaAcao: "Confirmar horário e enviar proposta com valor.",
    chat: [
      { from: "cliente", texto: "Oi, vocês têm horário pra sábado?" },
      { from: "agente", texto: "Temos sim! Saída às 9h ou 14h." },
      { from: "cliente", texto: "Quanto fica pra 4 adultos e 2 crianças?" },
    ],
    sugestao: "Oi Marina! Pra 4 adultos e 2 crianças no passeio de Escuna sai R$ 720 (criança até 8 anos tem 50% off). Posso reservar às 9h de sábado?",
    reserva: { passeio: "Escuna · Ilha Grande", pessoas: 4, criancas: 2, hotel: "Recanto do Sol · Centro", data: "2026-07-06", horario: "09:00", valorTotal: 720, sinal: 200, saldo: 520, pagamento: "Pix (parcial)", parceiro: "Escuna Vitória", obs: "Pediu confirmação por WhatsApp." },
  },
  {
    id: "l2", cliente: "Rafael & Bia", telefone: "24991230002", status: "Lead novo", passeio: "Trilha Pico do Papagaio",
    ultimaMsg: "Vi o story, ainda tem vaga pra sexta?", prioridade: "media",
    proximaAcao: "Perguntar nº de pessoas e experiência com trilha.",
    chat: [{ from: "cliente", texto: "Vi o story, ainda tem vaga pra sexta?" }],
    sugestao: "Oi! Temos vaga sim pra sexta. É pra quantas pessoas e vocês já têm experiência com trilha?",
    reserva: { passeio: "Trilha Pico do Papagaio", pessoas: 2, criancas: 0, hotel: "—", data: "2026-07-04", horario: "07:00", valorTotal: 260, sinal: 0, saldo: 260, pagamento: "—", parceiro: "Guia Zé Trilheiro", obs: "Ainda sem briefing completo." },
  },
  {
    id: "l3", cliente: "Fernanda Costa", telefone: "24991230003", status: "Proposta enviada", passeio: "Passeio de Lancha · Praias",
    ultimaMsg: "Vou ver com meu marido e te aviso.", prioridade: "media",
    proximaAcao: "Fazer follow-up amanhã à noite.",
    chat: [
      { from: "cliente", texto: "Manda a proposta pra 6 pessoas?" },
      { from: "agente", texto: "Proposta enviada: R$ 1.380 pra 6 adultos, saída 10h." },
      { from: "cliente", texto: "Vou ver com meu marido e te aviso." },
    ],
    sugestao: "Oi Fernanda, ficou alguma dúvida sobre a proposta? Posso segurar o horário das 10h até amanhã à noite.",
    reserva: { passeio: "Lancha · Praias", pessoas: 6, criancas: 0, hotel: "Pousada Mar Azul", data: "2026-07-09", horario: "10:00", valorTotal: 1380, sinal: 0, saldo: 1380, pagamento: "—", parceiro: "Lancha Netuno", obs: "Aguardando decisão do casal." },
  },
  {
    id: "l4", cliente: "Grupo Amigos RJ (8p)", telefone: "24991230004", status: "Aguardando reserva", passeio: "Bike + Praia",
    ultimaMsg: "Fechado! Só falta o sinal.", prioridade: "alta",
    proximaAcao: "Cobrar sinal até quinta-feira.",
    chat: [
      { from: "cliente", texto: "Fechado! Só falta o sinal." },
      { from: "agente", texto: "Show! Te mando a chave Pix do sinal agora." },
    ],
    sugestao: "Perfeito! Segue a chave Pix pra sinal de R$ 150. Assim que cair eu confirmo a reserva e mando o voucher.",
    reserva: { passeio: "Bike + Praia", pessoas: 8, criancas: 0, hotel: "Hostel Vista Mar", data: "2026-07-12", horario: "08:30", valorTotal: 960, sinal: 150, saldo: 810, pagamento: "Pix (sinal pendente)", parceiro: "Bike Tour Jampa", obs: "Cobrar sinal até quinta." },
  },
  {
    id: "l5", cliente: "Casal Andrade", telefone: "24991230005", status: "Reserva paga", passeio: "City Tour Histórico",
    ultimaMsg: "Pagamento feito, obrigada!", prioridade: "baixa",
    proximaAcao: "Gerar voucher e enviar.",
    chat: [{ from: "cliente", texto: "Pagamento feito, obrigada!" }, { from: "agente", texto: "Recebido! Já vou gerar o voucher de vocês." }],
    sugestao: "Ótimo, pagamento confirmado! Posso gerar o voucher do City Tour pra amanhã às 9h?",
    reserva: { passeio: "City Tour Histórico", pessoas: 2, criancas: 0, hotel: "Hotel Costa Verde", data: VP_HOJE, horario: "09:00", valorTotal: 340, sinal: 340, saldo: 0, pagamento: "Pago integral", parceiro: "Guia Local Centro", obs: "Pronto pra gerar voucher." },
  },
  {
    id: "l6", cliente: "Beatriz Lima", telefone: "24991230006", status: "Voucher gerado", passeio: "Mergulho · Naufrágio",
    ultimaMsg: "Chegou o voucher, obrigada 🙏", prioridade: "baixa",
    proximaAcao: "Confirmar presença 1 dia antes.",
    avaliacao: "pendente",
    chat: [{ from: "agente", texto: "Voucher enviado no seu e-mail e WhatsApp." }, { from: "cliente", texto: "Chegou o voucher, obrigada 🙏" }],
    sugestao: "De nada! Qualquer dúvida antes do passeio de amanhã é só chamar por aqui.",
    reserva: { passeio: "Mergulho · Naufrágio", pessoas: 1, criancas: 0, hotel: "Pousada do Mar", data: "2026-07-02", horario: "08:00", valorTotal: 280, sinal: 280, saldo: 0, pagamento: "Pago integral", parceiro: "Dive Jampa", obs: "Voucher #VP-0342 enviado." },
  },
  {
    id: "l7", cliente: "Grupo Excursão SP (12p)", telefone: "24991230007", status: "Passeio realizado", passeio: "Trilha + Cachoeira",
    ultimaMsg: "Foi incrível, valeu demais!", prioridade: "baixa",
    proximaAcao: "Pedir avaliação no Google.",
    avaliacao: "pendente",
    chat: [{ from: "cliente", texto: "Foi incrível, valeu demais!" }],
    sugestao: "Que alegria saber! Se puder deixar uma avaliação rápida no Google, ajuda demais a gente. 🙏",
    reserva: { passeio: "Trilha + Cachoeira", pessoas: 12, criancas: 1, hotel: "Camping Verde Vale", data: "2026-06-30", horario: "08:00", valorTotal: 1440, sinal: 1440, saldo: 0, pagamento: "Pago integral", parceiro: "Guia Zé Trilheiro", obs: "Passeio concluído sem intercorrências." },
  },
  {
    id: "l8", cliente: "Paulo Nunes", telefone: "24991230008", status: "Perdido", passeio: "Passeio de Lancha · Praias",
    ultimaMsg: "Vou fechar com outra agência, valor ficou alto.", prioridade: "baixa",
    proximaAcao: "Registrar motivo e reengajar em campanha futura.",
    chat: [{ from: "cliente", texto: "Vou fechar com outra agência, valor ficou alto." }],
    sugestao: "Entendo, Paulo. Se quiser, posso te avisar quando tivermos uma condição especial nesse passeio.",
    reserva: { passeio: "Lancha · Praias", pessoas: 3, criancas: 0, hotel: "—", data: "—", horario: "—", valorTotal: 690, sinal: 0, saldo: 690, pagamento: "—", parceiro: "Lancha Netuno", obs: "Perdido por preço." },
  },
];

// Leads REAIS (leitura via GET /vp/clientes, mesmo endpoint da aba legado).
// Só leitura: nenhum botão escreve; telefone sempre mascarado na tela.
let _vpRealLeads = [];
async function vpSyncRealLeads() {
  if (!state.online) { _vpRealLeads = []; return; }
  try {
    const d = await tryJson(vpUrl("vp/clientes"));
    _vpRealLeads = (d.leads || []).map((c, i) => ({
      id: "real-" + i, real: true, backendId: c.id || null,
      cliente: c.nome || "(cliente)", telefone: c.contato || "",
      status: AT_FUNNEL.includes(c.status) ? c.status : "Lead novo", passeio: "—", prioridade: "media",
      ultimaMsg: c.obs || "sem observação registrada",
      proximaAcao: "Completar briefing (passeio, data, pessoas).",
      chat: [],
      sugestao: `Oi ${(c.nome || "").split(" ")[0] || ""}! Aqui é da Vem Passear Jampa 😊 Qual passeio você tem interesse e pra qual data?`.replace("  ", " "),
      reserva: { passeio: "—", pessoas: "—", criancas: "—", hotel: "—", data: "—", horario: "—", valorTotal: 0, sinal: 0, saldo: 0, pagamento: "—", parceiro: "—", obs: c.obs || "—" },
    }));
  } catch (_) { _vpRealLeads = []; }
}
const atLeads = () => AT_LEADS.concat(_vpRealLeads);

let _atLeadId = AT_LEADS[0].id;
const atLead = (id) => atLeads().find((l) => l.id === id) || AT_LEADS[0];
const atPrioClass = { alta: "err", media: "warn", baixa: "ok" };
const atFunnelIdx = (status) => { const i = AT_FUNNEL.indexOf(status); return i < 0 ? 0 : i; };

async function vpAtendimento() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = "";
  const note = state.online
    ? "Atendimento — demo sintética + leads reais (🔗). Sugestão da IA pode ser gerada de verdade pelo squad; nada é enviado ao cliente daqui."
    : "Atendimento — visual, dados sintéticos. Backend offline: geração real indisponível.";
  host.appendChild(h(`<div class="card-sub" style="margin-bottom:12px">${_esc(note)}</div>`));
  await vpSyncRealLeads();
  if (_vpTab !== "atendimento" || !$("vp-content")) return; // usuário trocou de aba durante o fetch

  const wrap = h(`<div class="at-cols"></div>`);
  wrap.appendChild(atColLeft());
  wrap.appendChild(atColCenter());
  wrap.appendChild(atColRight());
  host.appendChild(wrap);
}

function atColLeft() {
  const col = h(`<div class="at-col at-col-left"><div class="at-col-h">Leads / Conversas</div><div class="at-lead-list"></div></div>`);
  const list = col.querySelector(".at-lead-list");
  atLeads().forEach((l) => {
    const active = l.id === _atLeadId;
    const it = h(`<div class="at-lead-item${active ? " active" : ""}">
      <div class="at-lead-top"><span class="at-lead-nome"></span><span class="badge ${atPrioClass[l.prioridade] || "wait"}">●</span></div>
      <div class="at-lead-status"></div>
      <div class="at-lead-passeio"></div>
      <div class="at-lead-msg"></div>
    </div>`);
    it.querySelector(".at-lead-nome").textContent = (l.real ? "🔗 " : "") + l.cliente;
    it.querySelector(".at-lead-status").textContent = l.status + (l.real ? " · leitura real" : "");
    it.querySelector(".at-lead-passeio").textContent = "🎯 " + l.passeio;
    it.querySelector(".at-lead-msg").textContent = "💬 " + l.ultimaMsg;
    it.onclick = () => { _atLeadId = l.id; vpAtendimento(); };
    list.appendChild(it);
  });
  return col;
}

const AT_BRIEFING_FIELDS = [["passeio", "Passeio"], ["data", "Data"], ["horario", "Horário"], ["pessoas", "Pessoas"], ["criancas", "Crianças"], ["hotel", "Hotel/Bairro"], ["pagamento", "Forma de pagamento"], ["sinal", "Reserva/Sinal"], ["saldo", "Saldo"], ["parceiro", "Parceiro"], ["obs", "Observações"]];
const AT_BRIEFING_ESSENCIAIS = ["data", "pessoas", "hotel"];
const atIsMissing = (v) => v === undefined || v === null || v === "" || v === "—";

function atColCenter() {
  const l = atLead(_atLeadId);
  const r = l.reserva;
  const col = h(`<div class="at-col at-col-center"></div>`);
  if (l.status === "Perdido") {
    col.appendChild(h(`<div class="at-funnel"><span class="at-funnel-step lost">✖ Lead perdido</span></div>`));
  } else {
    const idx = atFunnelIdx(l.status);
    const funnel = h(`<div class="at-funnel"></div>`);
    AT_FUNNEL.forEach((step, i) => {
      funnel.appendChild(h(`<span class="at-funnel-step${i === idx ? " current" : ""}${i < idx ? " done" : ""}">${_esc(step)}</span>`));
    });
    col.appendChild(funnel);
  }

  const missingEssenciais = AT_BRIEFING_ESSENCIAIS.filter((k) => atIsMissing(r[k]));
  if (missingEssenciais.length) col.appendChild(h(`<div class="at-alert">⚠️ Briefing incompleto — confirme data, pessoas e local de busca antes de gerar voucher.</div>`));

  const det = h(`<details class="at-briefing"><summary>📋 Checklist do briefing</summary><div class="at-briefing-grid"></div></details>`);
  const bg = det.querySelector(".at-briefing-grid");
  AT_BRIEFING_FIELDS.forEach(([k, label]) => {
    const ok = !atIsMissing(r[k]);
    bg.appendChild(h(`<span class="at-check ${ok ? "ok" : "pend"}">${ok ? "✅" : "⬜"} ${_esc(label)}</span>`));
  });
  col.appendChild(det);

  col.appendChild(h(`<div class="at-col-h">Conversa · ${_esc(l.cliente)}</div>`));
  const chat = h(`<div class="at-chat"></div>`);
  if (!l.chat.length) chat.appendChild(h(`<div class="op-empty">Sem histórico de conversa ainda.</div>`));
  l.chat.forEach((m) => chat.appendChild(h(`<div class="at-msg ${m.from === "agente" ? "agente" : "cliente"}">${_esc(m.texto)}</div>`)));
  col.appendChild(chat);

  const ai = h(`<div class="at-ai-box">
    <div class="at-ai-h">✨ Sugestão da IA</div>
    <div class="at-ai-text"></div>
    <div class="at-ai-actions">
      <button class="op-btn ok at-copy-btn">📋 Copiar sugestão</button>
      <button class="op-btn studio at-gen-btn" title="Gera resposta real via POST /jampa/responder-lead (squad Hunter+LNS)">✨ Gerar com o squad</button>
    </div>
  </div>`);
  ai.querySelector(".at-ai-text").textContent = l.sugestao;
  // Copiar copia o texto EXIBIDO (modelo pronto ou gerado pelo squad).
  ai.querySelector(".at-copy-btn").onclick = async () => {
    try { await navigator.clipboard.writeText(ai.querySelector(".at-ai-text").textContent); opToast("Sugestão copiada.", "ok"); }
    catch (_) { opToast("Não consegui copiar (permissão do navegador).", "warn"); }
  };
  // Resposta REAL do squad (leitura+geração; nada é enviado ao cliente daqui).
  const genBtn = ai.querySelector(".at-gen-btn");
  genBtn.onclick = async () => {
    if (!state.online) { opToast("Backend offline — squad indisponível.", "err"); return; }
    genBtn.disabled = true; genBtn.textContent = "⏳ Gerando…";
    const box = ai.querySelector(".at-ai-text");
    try {
      const r = await tryJson(vpUrl("jampa/responder-lead"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome: l.cliente, contato: l.telefone, interesse: l.passeio !== "—" ? l.passeio : "", obs: l.ultimaMsg || "" }) });
      if (r.mensagem) { box.textContent = r.mensagem; opToast("Resposta gerada pelo squad. Revise antes de enviar.", "ok"); }
      else opToast("O squad não devolveu mensagem.", "warn");
    } catch (e) { opToast("Falhou ao gerar: " + e.message, "err"); }
    genBtn.disabled = false; genBtn.textContent = "✨ Gerar com o squad";
  };
  col.appendChild(ai);
  return col;
}

function atField(k, v) {
  return `<div class="at-f"><span class="at-f-k">${_esc(k)}</span><span class="at-f-v">${_esc(String(v ?? "—"))}</span></div>`;
}

function atColRight() {
  const l = atLead(_atLeadId);
  const r = l.reserva;
  const col = h(`<div class="at-col at-col-right"><div class="at-col-h">CRM rápido · Reserva</div></div>`);
  const box = h(`<div class="at-crm"></div>`);
  box.innerHTML = [
    atField("Passeio", r.passeio), atField("Pessoas", r.pessoas), atField("Crianças", r.criancas),
    atField("Hotel/Bairro", r.hotel), atField("Data", r.data), atField("Horário", r.horario),
    atField("Valor total", vpBRL(r.valorTotal)), atField("Reserva/Sinal", vpBRL(r.sinal)), atField("Saldo", vpBRL(r.saldo)),
    atField("Pagamento", r.pagamento), atField("Parceiro", r.parceiro), atField("Observações", r.obs),
  ].join("");
  col.appendChild(box);
  const btn = h(`<button class="op-btn studio at-voucher-btn">🎫 Gerar reserva/voucher</button>`);
  btn.onclick = () => vpVoucherModal(l);
  col.appendChild(btn);
  return col;
}

// ---------- Modal genérico "fase visual" — nenhuma chamada escreve nada real ----------
function vpVisualModal(title, bodyHtml, opts) {
  opts = opts || {};
  const ov = h(`<div class="cs-overlay">
    <div class="cs-modal vp-modal">
      <div class="cs-h"></div>
      <div class="vp-modal-warn"></div>
      <div class="vp-modal-body"></div>
      <div class="cs-actions"></div>
    </div>
  </div>`);
  ov.querySelector(".cs-h").textContent = title;
  if (opts.warn) ov.querySelector(".vp-modal-warn").innerHTML = `<div class="banner">⚠️ ${_esc(opts.warn)}</div>`;
  ov.querySelector(".vp-modal-body").innerHTML = bodyHtml || "";
  const actions = ov.querySelector(".cs-actions");
  (opts.extraActions || []).forEach((a) => {
    const b = h(`<button class="op-btn ok"></button>`); b.textContent = a.label; b.onclick = a.onClick;
    actions.appendChild(b);
  });
  const closeBtn = h(`<button class="op-btn ghost">Fechar</button>`);
  const close = () => ov.remove();
  closeBtn.onclick = close;
  actions.appendChild(closeBtn);
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  document.body.appendChild(ov);
  return ov;
}

function vpCopyResumo(lead) {
  const r = lead.reserva;
  const txt = `Vem Passear Jampa — Resumo\nCliente: ${lead.cliente}\nPasseio: ${r.passeio}\nData/Horário: ${r.data} · ${r.horario}\nPessoas: ${r.pessoas} (crianças: ${r.criancas})\nLocal de busca: ${r.hotel}\nValor total: ${vpBRL(r.valorTotal)} · Sinal: ${vpBRL(r.sinal)} · Saldo: ${vpBRL(r.saldo)}\nParceiro: ${r.parceiro}\nObs: ${r.obs}`;
  navigator.clipboard.writeText(txt).then(() => opToast("Resumo copiado.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
}

// Voucher visual — prévia apenas, não é emitido nem enviado de verdade.
function vpVoucherModal(lead) {
  const r = lead.reserva;
  const pago = (r.valorTotal || 0) - (r.saldo || 0);
  const body = `
    <div class="voucher-card">
      <div class="voucher-h"><div class="voucher-logo">🌊</div><div><div class="voucher-brand">Vem Passear Jampa</div><div class="voucher-sub">Voucher de passeio · prévia</div></div></div>
      <div class="at-crm">
        ${atField("Cliente", lead.cliente)}${atField("Passeio", r.passeio)}
        ${atField("Data", r.data)}${atField("Horário", r.horario)}
        ${atField("Local de saída/busca", r.hotel)}${atField("Parceiro", r.parceiro)}
        ${atField("Valor pago", vpBRL(pago))}${atField("Saldo", vpBRL(r.saldo))}
      </div>
      <div class="voucher-block"><b>Instruções</b><p>${_esc(VP_INSTRUCOES)}</p></div>
      <div class="voucher-block"><b>Política de cancelamento</b><p>${_esc(VP_POLITICA_CANCEL)}</p></div>
      <div class="voucher-block"><b>Contato</b><p>${_esc(VP_CONTATO)}</p></div>
    </div>`;
  vpVisualModal("🎫 Gerar voucher", body, {
    warn: "Fase visual — prévia do voucher, não emitida nem enviada.",
    extraActions: [{ label: "📋 Copiar resumo", onClick: () => vpCopyResumo(lead) }],
  });
}

// ---------- Funil de Vendas (Kanban visual — sem drag real) ----------
async function vpFunil() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Funil de vendas · demo sintética${state.online ? " + leads reais em leitura (🔗)" : ""}. Sem drag-and-drop nesta fase.</div>`;
  await vpSyncRealLeads();
  if (_vpTab !== "funil" || !$("vp-content")) return;
  const all = atLeads();
  const board = h(`<div class="fk-board"></div>`);
  const cols = AT_FUNNEL.concat(["Perdido"]);
  cols.forEach((col) => {
    const leads = all.filter((l) => l.status === col);
    const colEl = h(`<div class="fk-col"><div class="fk-col-h">${_esc(col)} <span class="ti-count">${leads.length}</span></div><div class="fk-cards"></div></div>`);
    const cardsBox = colEl.querySelector(".fk-cards");
    leads.forEach((l) => {
      const r = l.reserva;
      const card = h(`<div class="fk-card">
        <div class="fk-card-nome">${l.real ? "🔗 " : ""}${_esc(l.cliente)}${l.real ? ` <span class="chip">leitura real</span>` : ""}</div>
        <div class="fk-card-meta">🎯 ${_esc(l.passeio)}</div>
        <div class="fk-card-meta">👥 ${_esc(String(r.pessoas))}p · 📅 ${_esc(r.data)} · 💰 ${vpBRL(r.valorTotal)}</div>
        <div class="fk-card-next">➡ ${_esc(l.proximaAcao || "—")}</div>
        <div class="fk-card-actions"></div>
      </div>`);
      const actions = card.querySelector(".fk-card-actions");
      const bVer = h(`<button class="op-btn ghost sm">Ver atendimento</button>`);
      bVer.onclick = () => { _atLeadId = l.id; _vpTab = "atendimento"; renderCanvas(); };
      actions.appendChild(bVer);
      const bNext = h(`<button class="op-btn studio sm">Próxima etapa</button>`);
      if (l.real && l.backendId) {
        // Lead REAL: grava a etapa via PATCH /vp/clientes/{id} (confirmação forte).
        const prox = AT_FUNNEL[Math.min(atFunnelIdx(l.status) + 1, AT_FUNNEL.length - 1)];
        bNext.onclick = () => confirmStrong({
          title: "Mover lead no funil (Vem Passear · projeto conectado)",
          endpoint: `/vp/clientes/${l.backendId}`, method: "PATCH", target: l.cliente,
          before: l.status, after: prox, risk: "op", phrase: "CONFIRMAR",
          onConfirm: async () => {
            try {
              const res = await opSend(vpUrl(`vp/clientes/${encodeURIComponent(l.backendId)}`), { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: prox }) });
              if (res.ok && res.data.status === "ok") { opToast(`${l.cliente} → ${prox}.`, "ok"); vpFunil(); }
              else opToast(res.data.status === "not_found" ? "Lead não encontrado no backend." : "Falha (" + res.status + ")", "warn");
            } catch (e) { opToast("Backend offline — não movi.", "err"); }
          },
        });
      } else {
        bNext.onclick = () => vpVisualModal("➡ Próxima etapa", `<p style="font-size:13px">Moveria <b>${_esc(l.cliente)}</b> pra próxima etapa do funil.</p>`, { warn: "Lead de demonstração — sem gravação real." });
      }
      actions.appendChild(bNext);
      if (l.sugestao) {
        const bCopy = h(`<button class="op-btn ok sm">Copiar resposta</button>`);
        bCopy.onclick = () => navigator.clipboard.writeText(l.sugestao).then(() => opToast("Resposta copiada.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
        actions.appendChild(bCopy);
      }
      if (col === "Passeio realizado" || col === "Pós-venda") {
        const bPos = h(`<button class="op-btn ghost sm">Marcar pós-venda</button>`);
        bPos.onclick = () => vpVisualModal("⭐ Marcar pós-venda", `<p style="font-size:13px">Marcaria <b>${_esc(l.cliente)}</b> como pós-venda em andamento.</p>`, { warn: "Fase visual — sem gravação real." });
        actions.appendChild(bPos);
      }
      cardsBox.appendChild(card);
    });
    if (!leads.length) cardsBox.appendChild(h(`<div class="op-empty">—</div>`));
    board.appendChild(colEl);
  });
  host.appendChild(board);
}

// ---------- Reservas & Vouchers (tabela visual) ----------
function vpReservas() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Reservas · dados sintéticos, telefone mascarado. Nenhuma escrita real nesta fase.</div>`;
  const wrap = h(`<div class="vp-table-wrap"></div>`);
  const table = h(`<table class="vp-table"><thead><tr>
    <th>Cliente</th><th>Telefone</th><th>Passeio</th><th>Data</th><th>Horário</th><th>Pessoas</th><th>Crianças</th>
    <th>Valor total</th><th>Sinal</th><th>Saldo</th><th>Pagamento</th><th>Hotel/Bairro</th><th>Parceiro</th><th>Status</th><th>Ações</th>
  </tr></thead><tbody></tbody></table>`);
  const tbody = table.querySelector("tbody");
  AT_LEADS.forEach((l) => {
    const r = l.reserva;
    const tr = h(`<tr>
      <td>${_esc(l.cliente)}</td><td>${_esc(vpMask(l.telefone))}</td><td>${_esc(r.passeio)}</td><td>${_esc(r.data)}</td><td>${_esc(r.horario)}</td>
      <td>${_esc(String(r.pessoas))}</td><td>${_esc(String(r.criancas))}</td><td>${vpBRL(r.valorTotal)}</td><td>${vpBRL(r.sinal)}</td><td>${vpBRL(r.saldo)}</td>
      <td>${_esc(r.pagamento)}</td><td>${_esc(r.hotel)}</td><td>${_esc(r.parceiro)}</td><td><span class="vp-tag ${l.status === "Perdido" ? "lead" : "fechado"}">${_esc(l.status)}</span></td>
      <td class="vp-table-actions"></td>
    </tr>`);
    const actions = tr.querySelector(".vp-table-actions");
    const bDet = h(`<button class="op-btn ghost sm">Ver detalhes</button>`);
    bDet.onclick = () => vpVisualModal(`📋 ${l.cliente}`, [
      atField("Passeio", r.passeio), atField("Data", r.data), atField("Horário", r.horario), atField("Pessoas", r.pessoas), atField("Crianças", r.criancas),
      atField("Hotel/Bairro", r.hotel), atField("Valor total", vpBRL(r.valorTotal)), atField("Sinal", vpBRL(r.sinal)), atField("Saldo", vpBRL(r.saldo)),
      atField("Pagamento", r.pagamento), atField("Parceiro", r.parceiro), atField("Observações", r.obs),
    ].join(""), { extraActions: [{ label: "📋 Copiar resumo", onClick: () => vpCopyResumo(l) }] });
    const bVoucher = h(`<button class="op-btn studio sm">Gerar voucher</button>`);
    bVoucher.onclick = () => vpVoucherModal(l);
    const bCopy = h(`<button class="op-btn ok sm">Copiar resumo</button>`);
    bCopy.onclick = () => vpCopyResumo(l);
    const bPag = h(`<button class="op-btn ghost sm">Confirmar pagamento</button>`);
    bPag.onclick = () => vpVisualModal("💳 Confirmar pagamento", `<p style="font-size:13px">Confirmaria o pagamento de <b>${_esc(l.cliente)}</b>.</p>`, { warn: "Fase visual — sem gravação real." });
    actions.append(bDet, bVoucher, bCopy, bPag);
    tbody.appendChild(tr);
  });
  wrap.appendChild(table);
  host.appendChild(wrap);
}

// ---------- Voucher (galeria de pendências/emitidos) ----------
function vpVoucherTab() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Vouchers · prévia visual. Nenhum voucher é emitido ou enviado de verdade nesta fase.</div>`;
  const pendentes = AT_LEADS.filter((l) => l.status === "Reserva paga");
  const emitidos = AT_LEADS.filter((l) => ["Voucher gerado", "Passeio realizado", "Pós-venda"].includes(l.status));
  const block = (titulo, arr, tagClass) => {
    host.insertAdjacentHTML("beforeend", `<div class="section-h">${_esc(titulo)} (${arr.length})</div>`);
    if (!arr.length) { host.insertAdjacentHTML("beforeend", `<div class="op-empty">—</div>`); return; }
    arr.forEach((l) => {
      const card = h(`<div class="vp-item"><div class="vp-item-h"><span class="vp-tag ${tagClass}"></span></div><div class="vp-item-meta"></div><div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap"></div></div>`);
      card.querySelector(".vp-tag").textContent = l.cliente;
      card.querySelector(".vp-item-meta").textContent = `${l.reserva.passeio} · ${l.reserva.data} ${l.reserva.horario}`;
      const acts = card.querySelector("div:last-child");
      const bGen = h(`<button class="op-btn studio sm">🎫 ${tagClass === "lead" ? "Gerar voucher" : "Ver voucher"}</button>`);
      bGen.onclick = () => vpVoucherModal(l);
      acts.appendChild(bGen);
      host.appendChild(card);
    });
  };
  block("Vouchers pendentes", pendentes, "lead");
  block("Vouchers emitidos", emitidos, "fechado");
}

// ---------- Agenda / Manifesto ----------
let _agView = "hoje", _agPasseio = "all", _agParceiro = "all";
function vpAgenda() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = "";
  const toggles = h(`<div class="vp-chips" style="margin-bottom:10px"></div>`);
  ["hoje", "semana"].forEach((v) => {
    const c = h(`<button class="vp-chip${_agView === v ? " active" : ""}">${v === "hoje" ? "Hoje" : "Semana"}</button>`);
    c.onclick = () => { _agView = v; vpAgenda(); };
    toggles.appendChild(c);
  });
  host.appendChild(toggles);

  const passeios = ["all", ...new Set(AT_LEADS.map((l) => l.reserva.passeio))];
  const parceiros = ["all", ...new Set(AT_LEADS.map((l) => l.reserva.parceiro))];
  const filtros = h(`<div class="vp-form-row" style="margin-bottom:12px"></div>`);
  const selP = h(`<select class="cs-input vp-in"></select>`);
  passeios.forEach((p) => selP.appendChild(h(`<option value="${_esc(p)}">${p === "all" ? "Todos os passeios" : _esc(p)}</option>`)));
  selP.value = _agPasseio; selP.onchange = () => { _agPasseio = selP.value; vpAgenda(); };
  const selPa = h(`<select class="cs-input vp-in"></select>`);
  parceiros.forEach((p) => selPa.appendChild(h(`<option value="${_esc(p)}">${p === "all" ? "Todos os parceiros" : _esc(p)}</option>`)));
  selPa.value = _agParceiro; selPa.onchange = () => { _agParceiro = selPa.value; vpAgenda(); };
  filtros.append(selP, selPa);
  host.appendChild(filtros);

  let rows = AT_LEADS.filter((l) => l.status !== "Perdido" && l.reserva.data !== "—");
  if (_agView === "hoje") rows = rows.filter((l) => l.reserva.data === VP_HOJE);
  if (_agPasseio !== "all") rows = rows.filter((l) => l.reserva.passeio === _agPasseio);
  if (_agParceiro !== "all") rows = rows.filter((l) => l.reserva.parceiro === _agParceiro);
  rows = rows.slice().sort((a, b) => (a.reserva.data + a.reserva.horario).localeCompare(b.reserva.data + b.reserva.horario));

  host.insertAdjacentHTML("beforeend", `<div class="section-h">📋 Manifesto (${rows.length})</div>`);
  if (!rows.length) host.insertAdjacentHTML("beforeend", `<div class="op-empty">Nenhum passeio nesse filtro.</div>`);
  rows.forEach((l) => {
    const r = l.reserva;
    host.appendChild(h(`<div class="vp-item">
      <div class="vp-item-h">${_esc(r.horario)} · ${_esc(r.passeio)} <span class="accent">${_esc(r.data)}</span></div>
      <div class="vp-item-meta">${_esc(l.cliente)} · ${_esc(String(r.pessoas))}p · busca: ${_esc(r.hotel)} · pago: ${vpBRL(r.valorTotal - r.saldo)} · saldo: ${vpBRL(r.saldo)} · parceiro: ${_esc(r.parceiro)}</div>
      <div class="vp-item-body">${_esc(r.obs || "")}</div>
    </div>`));
  });

  const btns = h(`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px"></div>`);
  const bPdf = h(`<button class="op-btn ghost" disabled title="em breve">📄 Gerar manifesto PDF <span class="chip">em breve</span></button>`);
  const bCopy = h(`<button class="op-btn ok">📋 Copiar manifesto</button>`);
  bCopy.onclick = () => {
    const txt = rows.map((l) => `${l.reserva.horario} · ${l.reserva.passeio} · ${l.cliente} · ${l.reserva.pessoas}p · busca: ${l.reserva.hotel} · saldo: ${vpBRL(l.reserva.saldo)}`).join("\n");
    navigator.clipboard.writeText(txt || "Sem itens no filtro atual.").then(() => opToast("Manifesto copiado.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
  };
  const bEnviar = h(`<button class="op-btn ghost" disabled title="em breve">📤 Enviar parceiro <span class="chip">em breve</span></button>`);
  const bSaldos = h(`<button class="op-btn studio">💰 Conferir saldos</button>`);
  bSaldos.onclick = () => {
    const total = rows.reduce((s, l) => s + (l.reserva.saldo || 0), 0);
    vpVisualModal("💰 Saldos a receber", `<p style="font-size:13px">Total de saldo a receber no filtro atual: <b>${vpBRL(total)}</b> (${rows.length} reserva(s)).</p>`);
  };
  btns.append(bPdf, bCopy, bEnviar, bSaldos);
  host.appendChild(btns);
}

// ---------- Pós-venda ----------
const _atPosVendaSolicitado = new Set(); // estado só em memória — reseta ao recarregar
function vpPosVenda() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Pós-venda · mensagens sugeridas, cópia manual. Nada é enviado automaticamente.</div>`;
  const leads = AT_LEADS.filter((l) => l.avaliacao);
  if (!leads.length) { host.insertAdjacentHTML("beforeend", `<div class="op-empty">Nenhum passeio aguardando pós-venda.</div>`); return; }
  leads.forEach((l) => {
    const solicitado = _atPosVendaSolicitado.has(l.id);
    const msg = `Oi ${l.cliente.split(" ")[0]}! Que bom que você curtiu o passeio de ${l.reserva.passeio} 😊 Poderia deixar uma avaliação rápida pra gente? Ajuda muito!`;
    const card = h(`<div class="vp-item">
      <div class="vp-item-h">${_esc(l.passeio)} <span class="vp-tag ${solicitado ? "fechado" : "lead"}">${solicitado ? "solicitado" : "pendente"}</span></div>
      <div class="vp-item-meta">${_esc(l.cliente)} · ${_esc(l.reserva.data)}</div>
      <div class="vp-item-body"></div>
      <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap"></div>
    </div>`);
    card.querySelector(".vp-item-body").textContent = msg;
    const acts = card.querySelector("div:last-child");
    const bCopy = h(`<button class="op-btn ok sm">📋 Copiar pedido de avaliação</button>`);
    bCopy.onclick = () => navigator.clipboard.writeText(msg).then(() => opToast("Mensagem copiada.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
    const bMark = h(`<button class="op-btn ${solicitado ? "ghost" : "studio"} sm">${solicitado ? "✔ Solicitado" : "Marcar como solicitado"}</button>`);
    bMark.onclick = () => { if (solicitado) _atPosVendaSolicitado.delete(l.id); else _atPosVendaSolicitado.add(l.id); vpPosVenda(); };
    const bGoogle = h(`<button class="op-btn ghost sm" disabled title="em breve">🔗 Link Google <span class="chip">em breve</span></button>`);
    acts.append(bCopy, bMark, bGoogle);
    host.appendChild(card);
  });
}

// ---------- Marketing (apoio — kanban visual estático) ----------
const AT_MKT = [
  { id: "m1", tema: "Bastidores da Escuna", passeio: "Escuna · Ilha Grande", formato: "Reels", status: "Ideias", risco: false, legenda: "" },
  { id: "m2", tema: "Trilha ao amanhecer", passeio: "Trilha Pico do Papagaio", formato: "Carrossel", status: "Pauta", risco: false, legenda: "" },
  { id: "m3", tema: "Promoção fim de semana", passeio: "Bike + Praia", formato: "Story", status: "Roteiro/Legenda", risco: true, legenda: "🚲🌊 Bike + praia com condição especial esse fim de semana! Vagas limitadas, chama no direct." },
  { id: "m4", tema: "Depoimento cliente", passeio: "City Tour Histórico", formato: "Reels", status: "Criativo", risco: false, legenda: "" },
  { id: "m5", tema: "Mergulho no naufrágio", passeio: "Mergulho · Naufrágio", formato: "Post", status: "Aprovação", risco: true, legenda: "🤿 Maré boa essa semana pro passeio de mergulho no naufrágio! Poucas vagas." },
  { id: "m6", tema: "Recapitulando a temporada", passeio: "Vários", formato: "Carrossel", status: "Publicado", risco: false, legenda: "" },
];
const VP_MKT_COLS = ["Ideias", "Pauta", "Roteiro/Legenda", "Criativo", "Aprovação", "Publicado"];
function vpMarketing() {
  const host = $("vp-content"); if (!host) return;
  host.classList.add("at-wide");
  host.innerHTML = `<div class="banner">💡 Marketing é apoio. Fluxo operacional de vendas/reservas vem primeiro.</div>`;
  const top = h(`<div style="margin:10px 0"></div>`);
  const bIdeia = h(`<button class="op-btn ghost" disabled title="em breve">💡 Gerar ideia <span class="chip">em breve</span></button>`);
  top.appendChild(bIdeia);
  host.appendChild(top);

  const board = h(`<div class="fk-board"></div>`);
  VP_MKT_COLS.forEach((col) => {
    const cards = AT_MKT.filter((c) => c.status === col);
    const colEl = h(`<div class="fk-col"><div class="fk-col-h">${_esc(col)} <span class="ti-count">${cards.length}</span></div><div class="fk-cards"></div></div>`);
    const box = colEl.querySelector(".fk-cards");
    cards.forEach((c) => {
      const card = h(`<div class="fk-card">
        <div class="fk-card-nome">${_esc(c.tema)}</div>
        <div class="fk-card-meta">🎯 ${_esc(c.passeio)} · ${_esc(c.formato)}</div>
        ${c.risco ? `<div class="fk-card-meta"><span class="badge warn">⚠️ sensível (maré/preço/vaga)</span></div>` : ""}
        <div class="fk-card-actions"></div>
      </div>`);
      const acts = card.querySelector(".fk-card-actions");
      if (c.legenda) {
        const bCopy = h(`<button class="op-btn ok sm">Copiar legenda</button>`);
        bCopy.onclick = () => navigator.clipboard.writeText(c.legenda).then(() => opToast("Legenda copiada.", "ok")).catch(() => opToast("Não consegui copiar.", "warn"));
        acts.appendChild(bCopy);
      }
      if (col === "Aprovação") {
        const bOk = h(`<button class="op-btn ok sm">Aprovar</button>`);
        bOk.onclick = () => vpVisualModal("✅ Aprovar pauta", `<p style="font-size:13px">Aprovaria <b>${_esc(c.tema)}</b> pra seguir pra Publicado.</p>`, { warn: "Fase visual — sem gravação real." });
        const bNo = h(`<button class="op-btn no sm">Reprovar</button>`);
        bNo.onclick = () => vpVisualModal("❌ Reprovar pauta", `<p style="font-size:13px">Reprovaria <b>${_esc(c.tema)}</b> e voltaria pro roteiro.</p>`, { warn: "Fase visual — sem gravação real." });
        acts.append(bOk, bNo);
      }
      box.appendChild(card);
    });
    if (!cards.length) box.appendChild(h(`<div class="op-empty">—</div>`));
    board.appendChild(colEl);
  });
  host.appendChild(board);

  // ---------- Conteúdo vindo do Estúdio (GET /conteudo?projeto=vempassear) ----------
  // Conecta o Estúdio de Conteúdo à VP: o que você cria/publica lá aparece aqui.
  const secao = h(`<div style="margin-top:24px">
    <div class="section-h">✍️ Conteúdo do Estúdio</div>
    <div class="card-sub" style="margin:-4px 0 10px">Posts criados na aba <b>Conteúdo</b> para a Vem Passear aparecem aqui.</div>
    <div id="vp-estudio-list"><div class="op-empty">Carregando…</div></div>
  </div>`);
  host.appendChild(secao);
  if (state.online) {
    tryJson(vpUrl("conteudo?projeto=vempassear")).then((d) => {
      const list = $("vp-estudio-list"); if (!list) return;
      const itens = d.itens || [];
      if (!itens.length) { list.innerHTML = `<div class="op-empty">Nenhum conteúdo ainda. Crie na aba <b>Conteúdo</b>. 👈</div>`; return; }
      list.innerHTML = "";
      const grid = h(`<div class="fk-cards" style="max-width:660px"></div>`);
      const STA = { rascunho: ["Rascunho", "wait"], agendado: ["Agendado", "warn"], publicado: ["Publicado", "ok"] };
      itens.forEach((it) => {
        const [lbl, cls] = STA[it.status] || STA.rascunho;
        const card = h(`<div class="fk-card"><div class="fk-card-nome"></div><div class="fk-card-meta"><span class="vp-canal"></span> · <span class="badge ${cls}"><span class="dot ${cls}"></span>${lbl}</span></div></div>`);
        card.querySelector(".fk-card-nome").textContent = it.title || "(sem título)";
        card.querySelector(".vp-canal").textContent = it.channel || "—";
        grid.appendChild(card);
      });
      list.appendChild(grid);
    }).catch(() => { const l = $("vp-estudio-list"); if (l) l.innerHTML = `<div class="op-empty">Não consegui carregar agora.</div>`; });
  } else {
    const l = $("vp-estudio-list"); if (l) l.innerHTML = `<div class="op-empty">Backend offline — sem conteúdo do Estúdio.</div>`;
  }
}

// ---------- Resultados (dummy) ----------
function vpResultados() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="card-sub" style="margin-bottom:12px">Resultados · números sintéticos, só pra visual.</div>`;
  const cards = [
    ["Leads", "38"], ["Reservas", "21"], ["Receita", vpBRL(18420)], ["Ticket médio", vpBRL(877)],
    ["Conversão", "55%"], ["Passeio mais vendido", "Escuna · Ilha Grande"], ["Origem do lead", "Instagram 46%"],
    ["Avaliações Google", "4.8 ★ (126)"], ["Clientes perdidos", "4"], ["ROAS", "—"],
  ];
  const grid = h(`<div class="at-dash-grid"></div>`);
  cards.forEach(([label, val]) => grid.appendChild(h(`<div class="at-dash-card"><div class="at-dash-n">${_esc(val)}</div><div class="at-dash-l">${_esc(label)}</div></div>`)));
  host.appendChild(grid);
  host.insertAdjacentHTML("beforeend", `<div class="section-h" style="margin-top:18px">🧠 Leitura da IA <span class="card-sub">(resumo gerencial dummy)</span></div>`);
  host.insertAdjacentHTML("beforeend", `<div class="vp-card"><div class="vp-row"><span class="vp-v">Semana com conversão estável (55%), puxada por Escuna e City Tour. Instagram segue como maior origem de lead.</span></div><div class="vp-row"><span class="vp-k">Alerta</span><span class="vp-v">4 leads perdidos por preço — considerar condição especial em baixa demanda.</span></div><div class="vp-row"><span class="vp-k">Foco da semana</span><span class="vp-v">Reduzir tempo de resposta no WhatsApp e cobrar sinal pendente do grupo Bike + Praia.</span></div></div>`);
}

// ---------- Gates / Aprovações (visual) ----------
const AT_GATES = [
  { acao: "Gerar voucher", risco: "médio" }, { acao: "Enviar mensagem ao cliente", risco: "leve" },
  { acao: "Alterar valor da reserva", risco: "alto" }, { acao: "Confirmar pagamento", risco: "médio" },
  { acao: "Alterar status de reserva", risco: "médio" }, { acao: "Enviar pós-venda", risco: "leve" },
  { acao: "Aprovar pauta", risco: "leve" }, { acao: "Publicar conteúdo", risco: "alto" },
  { acao: "Rodar agente", risco: "alto" }, { acao: "Apagar dado", risco: "crítico" },
];
const AT_RISK_CLASS = { leve: "ok", médio: "warn", alto: "err", crítico: "err" };
function vpGates() {
  const host = $("vp-content"); if (!host) return;
  host.classList.remove("at-wide");
  host.innerHTML = `<div class="banner">⚠️ Todas as ações abaixo exigem confirmação humana. Nesta fase, nenhum botão executa algo real.</div>`;
  AT_GATES.forEach((g) => {
    const row = h(`<div class="vp-item">
      <div class="vp-item-h">${_esc(g.acao)} <span class="badge ${AT_RISK_CLASS[g.risco] || "wait"}">risco ${_esc(g.risco)}</span></div>
      <div class="vp-item-meta">status: pendente de confirmação</div>
      <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap"></div>
    </div>`);
    const acts = row.querySelector("div:last-child");
    const bOk = h(`<button class="op-btn ok sm">Aprovar</button>`);
    bOk.onclick = () => vpVisualModal("✅ " + g.acao, `<p style="font-size:13px">Aprovaria a ação <b>${_esc(g.acao)}</b>.</p>`, { warn: "Sem execução real nesta fase." });
    const bNo = h(`<button class="op-btn no sm">Reprovar</button>`);
    bNo.onclick = () => vpVisualModal("❌ " + g.acao, `<p style="font-size:13px">Reprovaria a ação <b>${_esc(g.acao)}</b>.</p>`, { warn: "Sem execução real nesta fase." });
    acts.append(bOk, bNo);
    host.appendChild(row);
  });
}

export { viewVempassear };
