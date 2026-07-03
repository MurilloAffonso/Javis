// Ações — auditoria do catálogo de ações seguras — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, _esc, setView } from "../../app.js";

// Catálogo estático das ações que escrevem/publicam/rodam agente/processam pesado.
// Nesta fase é AUDITORIA: classifica risco, mostra endpoint/método, e NÃO dispara
// nenhum POST/PATCH/DELETE. Botões de escrita ficam desabilitados ("Bloqueado nesta
// fase"). Só ações seguras: abrir a seção relacionada e copiar checklist (local).
const AC_RISK = {
  leitura:   { label: "Leitura",            cls: "ok" },
  leve:      { label: "Escrita leve",       cls: "run" },
  op:        { label: "Escrita operacional",cls: "warn" },
  pesado:    { label: "Pesado",             cls: "warn" },
  alto:      { label: "Alto risco",         cls: "err" },
  bloqueado: { label: "Bloqueado nesta fase",cls: "wait" },
};
const AC_GROUPS = [
  { id: "chat",     titulo: "Núcleo Javes · Chat & Voz", view: "chat" },
  { id: "operacao", titulo: "Operação · Kanban & Gates", view: "operacao", note: "🧪 Piloto de escrita segura: as ações de escrita da Operação já passam por confirmação forte (digitar CONFIRMAR). Só devem rodar em task descartável. Ações reais seguem bloqueadas nesta central." },
  { id: "missoes",  titulo: "Missões",                   view: "missoes" },
  { id: "rotina",   titulo: "Rotina · Lembretes",        view: "rotina" },
  { id: "treino",   titulo: "Treino / Scout",            view: "treino" },
  { id: "vp",       titulo: "Projeto conectado · Vem Passear Jampa", view: "vempassear" },
  { id: "upload",   titulo: "Upload",                    view: null },
  { id: "conclave", titulo: "Conclave / Agentes",        view: "conclave" },
];
const ACTIONS = [
  // Chat / Voz
  { g:"chat", nome:"Conversar (streaming)", ep:"/chat/stream", m:"POST", risk:"leve", ui:true, confirm:false, futuro:"já em uso; grava histórico" },
  { g:"chat", nome:"Transcrever voz",       ep:"/transcribe",  m:"POST", risk:"leve", ui:true, confirm:false, futuro:"validar com microfone real" },
  { g:"chat", nome:"Falar resposta (TTS)",  ep:"/tts",         m:"POST", risk:"leitura", ui:true, confirm:false, futuro:"gera áudio, sem escrita de dado" },
  // Operação
  { g:"operacao", nome:"Mover status (Kanban)",     ep:"/tasks/{id}/status",              m:"POST", risk:"op", ui:true, confirm:true, futuro:"testar com task descartável" },
  { g:"operacao", nome:"Aprovar/Rejeitar gate",     ep:"/approvals/{id}/decide",          m:"POST", risk:"alto", ui:true, confirm:true, futuro:"decisão humana; task descartável" },
  { g:"operacao", nome:"Rodar Estúdio (Gate 2)",    ep:"/tasks/{id}/run-studio",          m:"POST", risk:"op", ui:true, confirm:true, futuro:"gera criativos (modo seguro)" },
  { g:"operacao", nome:"Preparar Distribuição (G3)",ep:"/tasks/{id}/prepare-distribution",m:"POST", risk:"op", ui:true, confirm:true, futuro:"gera pacote (modo seguro)" },
  { g:"operacao", nome:"Concluir entidade",         ep:"/tasks/{id}/complete",            m:"POST", risk:"op", ui:false, confirm:true, futuro:"encerra task + digest" },
  // Missões
  { g:"missoes", nome:"Marcar node como done", ep:"/missions/{id}/nodes/{node}/done", m:"POST", risk:"op", ui:false, confirm:true, futuro:"altera backlog real" },
  // Rotina
  { g:"rotina", nome:"Criar lembrete", ep:"(sem endpoint exposto)", m:"—", risk:"bloqueado", ui:false, confirm:true, futuro:"falta endpoint de criação" },
  // Treino
  { g:"treino", nome:"Scout por área",   ep:"/treinamento/scout/{area}", m:"POST", risk:"pesado", ui:false, confirm:true, futuro:"processo pesado; aviso de tempo" },
  { g:"treino", nome:"Scout geral",      ep:"/treinamento/scout-all",    m:"POST", risk:"pesado", ui:false, confirm:true, futuro:"processo pesado" },
  { g:"treino", nome:"Resumir área",     ep:"/treinamento/resumir/{area}",m:"POST", risk:"pesado", ui:false, confirm:true, futuro:"LLM em lote" },
  { g:"treino", nome:"Treinar do YouTube",ep:"/train/youtube",           m:"POST", risk:"alto", ui:false, confirm:true, futuro:"download + processamento" },
  // Vem Passear (projeto conectado)
  { g:"vp", nome:"Cadastrar passeio",     ep:"/vp/passeios",      m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"dado do projeto conectado" },
  { g:"vp", nome:"Remover passeio",       ep:"/vp/passeios/{id}", m:"DELETE", risk:"alto", ui:false, confirm:true, futuro:"exclusão de dado real" },
  { g:"vp", nome:"Cadastrar cliente/lead",ep:"/vp/clientes",      m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"dado sensível" },
  { g:"vp", nome:"Mudar status cliente",  ep:"/vp/clientes/{id}", m:"PATCH",  risk:"op", ui:false, confirm:true, futuro:"altera lead real" },
  { g:"vp", nome:"Remover cliente",       ep:"/vp/clientes/{id}", m:"DELETE", risk:"alto", ui:false, confirm:true, futuro:"exclusão de dado real" },
  { g:"vp", nome:"Gerar conteúdo (LLM)",  ep:"/vp/conteudo",      m:"POST",   risk:"pesado", ui:false, confirm:true, futuro:"chama o cérebro/LLM" },
  { g:"vp", nome:"Salvar conteúdo",       ep:"/vp/conteudos",     m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"grava na biblioteca" },
  { g:"vp", nome:"Criar pauta",           ep:"/vp/pauta",         m:"POST",   risk:"leve", ui:false, confirm:true, futuro:"linha editorial" },
  { g:"vp", nome:"Publicar/replanejar pauta",ep:"/vp/pauta/{id}", m:"PATCH", risk:"op", ui:false, confirm:true, futuro:"muda status de publicação" },
  { g:"vp", nome:"Remover pauta",         ep:"/vp/pauta/{id}",    m:"DELETE", risk:"alto", ui:false, confirm:true, futuro:"exclusão de dado real" },
  { g:"vp", nome:"Rodar agente VP",       ep:"/vp/agents/run",    m:"POST",   risk:"alto", ui:false, confirm:true, futuro:"execução de agente do projeto" },
  // Upload
  { g:"upload", nome:"Upload de arquivo", ep:"/upload", m:"POST", risk:"op", ui:false, confirm:true, futuro:"fase própria; validar tipo/tamanho" },
  // Conclave
  { g:"conclave", nome:"Rodar Conclave",       ep:"/debate", m:"POST", risk:"pesado", ui:true, confirm:true, futuro:"já em uso; 1–3 min" },
  { g:"conclave", nome:"Chat com Conclave",    ep:"/chat/stream (use_conclave)", m:"POST", risk:"pesado", ui:true, confirm:false, futuro:"toggle ⚔️ no Chat" },
];

function acRiskBadge(risk) { const r = AC_RISK[risk] || AC_RISK.bloqueado; return `<span class="badge ${r.cls}"><span class="dot ${r.cls}"></span>${_esc(r.label)}</span>`; }
function acChecklistText(a) {
  return `Ação: ${a.nome}\nEndpoint: ${a.m} ${a.ep}\nRisco: ${(AC_RISK[a.risk]||{}).label || a.risk}\nUI existente: ${a.ui ? "sim" : "não"}\nExige confirmação: ${a.confirm ? "sim" : "não"}\nStatus: bloqueado nesta fase (sem escrita real)\nPróxima fase: ${a.futuro}`;
}

function viewAcoes(body) {
  body.appendChild(h(`<div class="vp-boundary">🛡️ <b>Central de Ações Seguras.</b> Mapa das ações que alteram dados, disparam agentes ou executam processos. Nesta fase a central <b>organiza riscos e prepara aprovações</b> — <b>nenhuma escrita real é executada daqui</b>.</div>`));
  // Resumo por categoria
  const counts = {};
  ACTIONS.forEach((a) => { counts[a.risk] = (counts[a.risk] || 0) + 1; });
  const summary = h(`<div class="ac-summary"></div>`);
  ["leitura","leve","op","pesado","alto","bloqueado"].forEach((k) => {
    if (!counts[k]) return;
    const r = AC_RISK[k];
    summary.appendChild(h(`<div class="ac-sum ${r.cls}"><div class="ac-sum-n">${counts[k]}</div><div class="ac-sum-l">${_esc(r.label)}</div></div>`));
  });
  body.appendChild(summary);
  // Grupos
  AC_GROUPS.forEach((grp) => {
    const items = ACTIONS.filter((a) => a.g === grp.id);
    if (!items.length) return;
    const head = h(`<div class="ac-group-h"><span>${_esc(grp.titulo)}</span></div>`);
    if (grp.view) {
      const open = h(`<button class="op-btn ghost sm">Abrir seção</button>`);
      open.onclick = () => setView(grp.view);
      head.appendChild(open);
    }
    body.appendChild(head);
    if (grp.note) { const n = h(`<div class="ac-note"></div>`); n.textContent = grp.note; body.appendChild(n); }
    items.forEach((a) => {
      const card = h(`<div class="ac-card">
        <div class="ac-card-top"><span class="ac-name"></span>${acRiskBadge(a.risk)}</div>
        <div class="ac-ep"><code>${_esc(a.m)} ${_esc(a.ep)}</code></div>
        <div class="ac-flags">UI existente: <b>${a.ui ? "sim" : "não"}</b> · confirmação: <b>${a.confirm ? "sim" : "não"}</b> · <span class="ac-status">bloqueado nesta fase</span></div>
        <div class="ac-next">Próxima fase: <span class="ac-next-v"></span></div>
        <div class="ac-actions">
          <button class="op-btn sm" disabled title="Ativação em fase própria, com confirmação forte">Executar (bloqueado nesta fase)</button>
          <button class="op-btn ghost sm ac-copy">Copiar checklist</button>
        </div>
      </div>`);
      card.querySelector(".ac-name").textContent = a.nome;
      card.querySelector(".ac-next-v").textContent = a.futuro;
      card.querySelector(".ac-copy").onclick = async (e) => {
        try { await navigator.clipboard.writeText(acChecklistText(a)); e.target.textContent = "Copiado ✓"; setTimeout(() => { e.target.textContent = "Copiar checklist"; }, 1500); }
        catch (_) { e.target.textContent = "Copie manualmente"; }
      };
      body.appendChild(card);
    });
  });
}

export { viewAcoes };
