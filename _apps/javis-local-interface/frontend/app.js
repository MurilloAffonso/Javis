// Javis v2 — frontend app
// Connects to the FastAPI server na MESMA origem da página (127.0.0.1 ou
// localhost — o que o senhor abriu). Fixar "localhost" quebrava quando a página
// vinha de 127.0.0.1: o localhost resolvia pra IPv6 (::1), onde o servidor não
// escuta, e TODO fetch dava timeout (status sempre "offline").
const API = window.location.origin;

// ─── DOM refs ────────────────────────────────────────────
const chatLog      = document.getElementById("chat-log");
const form         = document.getElementById("form");
const inputEl      = document.getElementById("input");
const modelSel     = document.getElementById("model-sel");
const useConclave  = document.getElementById("use-conclave");
const sendBtn      = document.querySelector(".send-btn");
const planBox      = document.getElementById("plan-box");
const conclaveWrap = document.getElementById("conclave-wrap");
const squadWrap    = document.getElementById("squad-wrap");
const squadRounds  = document.getElementById("squad-rounds");
const svcClaude    = document.getElementById("svc-claude");
const svcWebui     = document.getElementById("svc-webui");
const micBtn       = document.getElementById("mic-btn");
const useTts       = document.getElementById("use-tts");
const voiceStatus  = document.getElementById("voice-status");
const voiceInterim = document.getElementById("voice-interim");

// Brain cards (new layout)
const brainCards = {
  main:     document.getElementById("bc-main"),
  conclave: document.getElementById("bc-conclave"),
  memory:   document.getElementById("bc-memory"),
};

// Stat elements
const statCount    = document.getElementById("stat-count");
const statBrainLbl = document.getElementById("stat-brain-lbl");
const statSession  = document.getElementById("stat-session");
const sysMsEl      = document.getElementById("sys-ms");
const sysCountEl   = document.getElementById("sys-count");
const sysBrainEl   = document.getElementById("sys-brain");
const sysUptimeEl  = document.getElementById("sys-uptime");
const sysIntentEl  = document.getElementById("sys-intent");

let _msgCount = 0;
const _sessionStart = Date.now();

// Conclave text areas
const ct = {
  critico:      document.getElementById("ct-critico"),
  advogado:     document.getElementById("ct-advogado"),
  sintetizador: document.getElementById("ct-sintetizador"),
};

// Agent cards
const agentCards = {};
document.querySelectorAll(".ag-card[data-id]").forEach(card => {
  agentCards[card.dataset.id] = card;
});

// ─── Init ────────────────────────────────────────────────
checkStatus();
refreshStats();
loadApprovals();
setInterval(checkStatus, 30000);
setInterval(refreshStats, 30000);
setInterval(loadApprovals, 30000);
setInterval(_tickSession, 1000);
setInterval(pollReminders, 15000);
loadChatHistory().then(loadBriefing);
loadEngine();

// Contadores REAIS do topo (vêm do SQLite via /stats, não mais fixos).
async function refreshStats() {
  try {
    const r = await fetch(`${API}/stats`, { signal: AbortSignal.timeout(4000) });
    const s = await r.json();
    const msgs = document.getElementById('stat-count');
    const ags  = document.getElementById('stat-agents');
    if (msgs && typeof s.messages === 'number') msgs.textContent = s.messages;
    if (ags  && typeof s.agents   === 'number') ags.textContent  = s.agents;
  } catch { /* mantém o valor atual se /stats falhar */ }
}

// ─── Gate humano: aprovações pendentes no painel de Atividade ──────────────
async function loadApprovals() {
  const box  = document.getElementById('approvals-box');
  const list = document.getElementById('approvals-list');
  const cnt  = document.getElementById('approvals-count');
  if (!box || !list) return;
  let items = [];
  try {
    const r = await fetch(`${API}/approvals/pending`, { signal: AbortSignal.timeout(4000) });
    const d = await r.json();
    items = d.approvals || [];
  } catch { return; /* mantém o que está */ }
  if (!items.length) { box.hidden = true; list.innerHTML = ''; return; }
  box.hidden = false;
  if (cnt) cnt.textContent = items.length;
  list.innerHTML = items.map(_approvalCard).join('');
}

function _approvalCard(a) {
  const task = a.task_id ? `<div class="ap-task">tarefa: ${esc(a.task_id)}</div>` : '';
  const journeyBtn = a.task_id
    ? `<button class="ap-journey-btn" onclick="viewJourney('${esc(a.task_id)}', 'ap-journey-${a.id}')">Ver jornada</button>` : '';
  return `<div class="ap-card" id="ap-${a.id}">
    <div class="ap-subject">${esc(a.subject || '')}</div>
    <div class="ap-meta">${a.agent ? 'agente: ' + esc(a.agent) : ''}</div>
    ${task}
    ${journeyBtn}
    <div class="ap-journey" id="ap-journey-${a.id}" data-open="0"></div>
    <input class="ap-note" id="ap-note-${a.id}" placeholder="observação (opcional)…" />
    <div class="ap-actions">
      <button class="ap-btn ap-approve" onclick="decideApproval(${a.id}, 'approved')">Aprovar</button>
      <button class="ap-btn ap-reject"  onclick="decideApproval(${a.id}, 'rejected')">Rejeitar</button>
    </div>
    <div class="ap-feedback" id="ap-fb-${a.id}"></div>
  </div>`;
}

// Journey Log: timeline simples da task (horário · ator · evento · mensagem).
// hostId = id do container onde a jornada é renderizada (serve aprovação E Quadro).
async function viewJourney(taskId, hostId) {
  const host = document.getElementById(hostId);
  if (!host) return;
  if (host.dataset.open === '1') { host.innerHTML = ''; host.dataset.open = '0'; return; } // toggle fecha
  host.innerHTML = '<span class="ap-spin">carregando jornada…</span>';
  try {
    const r = await fetch(`${API}/tasks/${encodeURIComponent(taskId)}/events`, { signal: AbortSignal.timeout(5000) });
    const d = await r.json();
    const evs = d.events || [];
    const status = d.task_status || '—';
    const encerrada = status === 'completed' || status === 'killed';
    const timeline = evs.length
      ? '<div class="jn-list">' + evs.map(_journeyRow).join('') + '</div>'
      : '<div class="jn-empty">Sem eventos registrados nesta tarefa ainda.</div>';
    const head = `<div class="jn-status">entidade: <b class="jn-st-${encerrada ? 'dead' : 'live'}">${esc(status)}</b></div>`;
    let footer;
    if (encerrada && d.digest_text) {
      footer = `<div class="jn-digest"><div class="jn-digest-h">📄 Digest da entidade</div><pre class="jn-digest-b">${esc(d.digest_text)}</pre></div>`;
    } else if (!encerrada) {
      footer = `<button class="jn-complete-btn" onclick="completeTask('${esc(taskId)}', '${esc(hostId)}')">Concluir entidade</button>`;
    } else {
      footer = '';
    }
    host.innerHTML = head + timeline + footer;
    host.dataset.open = '1';
  } catch (e) {
    host.innerHTML = `<span class="ap-warn">Não consegui carregar a jornada: ${esc(String(e))}</span>`;
  }
}

// Encerra a entidade-tarefa (completed/killed) e re-renderiza mostrando o digest.
async function completeTask(taskId, hostId) {
  try {
    const r = await fetch(`${API}/tasks/${encodeURIComponent(taskId)}/complete`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: '' }), signal: AbortSignal.timeout(8000),
    });
    const d = await r.json();
    if (d.ok) { showToast('Entidade concluída. Digest gerado.', 'success'); refreshStats(); }
    else      { showToast(d.error || 'Não consegui concluir.', 'warning'); }
  } catch (e) {
    showToast('Falhou ao concluir: ' + e, 'error');
  }
  const host = document.getElementById(hostId);
  if (host) host.dataset.open = '0';   // força re-render (mostra o digest)
  viewJourney(taskId, hostId);
  if (document.getElementById('view-quadro')?.classList.contains('active')) setTimeout(renderQuadro, 600);
}

function _journeyRow(e) {
  const hora = (e.created_at || '').slice(11, 16);  // HH:MM
  const ator = esc(e.actor || '') + (e.agent_id ? '·' + esc(e.agent_id) : '');
  return `<div class="jn-row">
    <span class="jn-time">${esc(hora)}</span>
    <span class="jn-type">${esc(e.event_type || '')}</span>
    <span class="jn-actor">${ator}</span>
    <span class="jn-msg">${esc(e.message || '')}</span>
  </div>`;
}

async function decideApproval(id, decision) {
  const card = document.getElementById(`ap-${id}`);
  const fb   = document.getElementById(`ap-fb-${id}`);
  const note = (document.getElementById(`ap-note-${id}`)?.value || '').trim();
  if (fb) fb.innerHTML = '<span class="ap-spin">registrando…</span>';
  try {
    const r = await fetch(`${API}/approvals/${id}/decide`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, note }),
      signal: AbortSignal.timeout(8000),
    });
    const d = await r.json();
    if (r.ok && d.ok) {
      if (card) {
        card.classList.add(decision === 'approved' ? 'ap-done-ok' : 'ap-done-no');
        const extra = d.message ? `<div class="ap-effect">${esc(d.message)}</div>` : '';
        card.innerHTML = `<div class="ap-resolved">${decision === 'approved' ? '✓ Aprovado' : '✕ Rejeitado'}${note ? ' — ' + esc(note) : ''}</div>${extra}`;
      }
      refreshStats();                      // approvals_pending / contadores
      setTimeout(loadApprovals, 1800);     // recarrega a lista (some o resolvido)
      // se o Quadro estiver aberto, reflete a nova task liberada
      if (d.advanced && document.getElementById('view-quadro')?.classList.contains('active')) {
        renderQuadro();
      }
      // feedback: usa a mensagem do workflow se houver (ex.: "Produção destravada")
      showToast(d.message || (decision === 'approved' ? 'Aprovado, senhor.' : 'Rejeitado, senhor.'),
                decision === 'approved' ? 'success' : 'info');
    } else {
      if (fb) fb.innerHTML = `<span class="ap-warn">${esc(d.error || 'Não rolou agora.')}</span>`;
    }
  } catch (e) {
    if (fb) fb.innerHTML = `<span class="ap-warn">Falhou: ${esc(String(e))}</span>`;
  }
}

// Motor de execução (Claude assinatura x Codex assinatura): botão manual,
// pra trocar quando a cota de um acabar (server.py: GET/POST /brain/active).
const ENGINE_DESC = {
  claude: 'Quem programa quando você pede "programa X": assinatura do Claude.',
  codex:  'Quem programa quando você pede "programa X": assinatura do Codex (OpenAI).',
};

async function loadEngine() {
  try {
    const r = await fetch(`${API}/brain/active`);
    if (!r.ok) return;
    const d = await r.json();
    _setEngineUI(d.engine);
  } catch (e) { console.warn('Engine:', e); }
}

function _setEngineUI(engine) {
  document.querySelectorAll('.engine-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.engine === engine);
  });
  const desc = document.getElementById('engine-desc');
  if (desc) desc.textContent = ENGINE_DESC[engine] || '';
}

document.getElementById('engine-toggle')?.addEventListener('click', async e => {
  const btn = e.target.closest('.engine-btn');
  if (!btn) return;
  const engine = btn.dataset.engine;
  try {
    const r = await fetch(`${API}/brain/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine }),
    });
    const d = await r.json();
    if (r.ok) _setEngineUI(d.engine);
  } catch (e) { console.warn('Engine switch:', e); }
});

// Saudação proativa: ao abrir, o Javis recebe o senhor sabendo o que foi feito.
async function loadBriefing() {
  try {
    const r = await fetch(`${API}/briefing`);
    if (!r.ok) return;
    const b = await r.json();
    if (!b.saudacao) return;
    const div = appendMsg("assistant", `<span class="briefing-greet">👋 ${esc(b.saudacao)}</span>`);
    if (div) div.classList.add("msg-briefing");
  } catch (e) { console.warn("Briefing:", e); }
}

async function loadChatHistory() {
  try {
    const r = await fetch(`${API}/history`);
    if (!r.ok) return;
    const hist = await r.json();
    const recent = hist.slice(-30);
    for (const h of recent) {
      if (h.role === "user") appendMsg("user", esc(h.content));
      else if (h.role === "assistant") appendMsg("assistant", renderMarkdown(h.content));
    }
  } catch (e) { console.warn("Histórico:", e); }
}

// Lembretes vencidos → Jamba avisa (mostra no chat + fala)
async function pollReminders() {
  try {
    const res = await fetch(`${API}/reminders/poll`);
    if (!res.ok) return;
    const data = await res.json();
    for (const r of (data.due || [])) {
      const msg = `⏰ Lembrete, senhor: ${r.text}`;
      removeWelcome();
      appendMsg("assistant", esc(msg), { brain: "memory", intent: "lembrete" });
      neuralBrain?.setState("thinking");
      neuralBrain?.fire?.();
      if (useTts?.checked) speak(msg);
      setTimeout(() => { if (!sendBtn.disabled) neuralBrain?.setState("idle"); }, 2500);
    }
  } catch (_) {}
}

// Brain card clicks
Object.entries(brainCards).forEach(([key, el]) => {
  el?.addEventListener("click", () => {
    setBrain(key);
    if (key === "conclave") useConclave.checked = true;
    else                    useConclave.checked = false;
  });
});

document.getElementById("conclave-toggle").addEventListener("click", () => {
  conclaveWrap.classList.toggle("open");
});
document.getElementById("squad-toggle")?.addEventListener("click", () => {
  squadWrap.classList.toggle("open");
});

// Debate autônomo
document.getElementById("btn-debate")?.addEventListener("click", () => {
  const task = inputEl.value.trim();
  if (!task) {
    inputEl.focus();
    inputEl.placeholder = "Digite a tarefa para o debate autônomo...";
    return;
  }
  inputEl.value = "";
  runAutonomousDebate(task);
});

// ─── Form submit ─────────────────────────────────────────
form.addEventListener("submit", e => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text || sendBtn.disabled) return;
  inputEl.value = "";
  sendMessage(text);
});

// File upload handler
const fileInput = document.getElementById("file-input");
if (fileInput) {
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;
    fileInput.value = "";
    removeWelcome();
    appendMsg("user", `📎 <strong>${file.name}</strong> enviado para análise`);
    const typingEl = appendTyping("analisando arquivo...");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/upload`, { method: "POST", body: fd });
      const data = await res.json();
      typingEl.remove();
      if (data.status === "ok") {
        appendMsg("assistant", renderMarkdown(data.message), { brain: "file-analyzer" });
      } else {
        appendMsg("assistant", `Erro ao analisar arquivo: ${data.message}`);
      }
    } catch (err) {
      typingEl.remove();
      appendMsg("assistant", `Erro ao enviar arquivo: ${err.message}`);
    }
  });
}

// Quick action buttons
document.querySelectorAll(".qbtn:not(#btn-debate)").forEach(btn => {
  btn.addEventListener("click", () => {
    const cmd = btn.dataset.cmd;
    if (!cmd || sendBtn.disabled) return;
    // Comando incompleto (termina com espaço) → preenche o campo e aguarda a URL
    if (cmd.endsWith(" ")) {
      inputEl.value = cmd;
      inputEl.focus();
      inputEl.placeholder = "cole a URL do site aqui...";
    } else {
      sendMessage(cmd);
    }
  });
});

// ─── Streaming message ────────────────────────────────────
async function sendMessage(text) {
  removeWelcome();
  appendMsg("user", esc(text));
  setLoading(true);
  clearAgentActivity();

  const streamDiv = _appendStreamMsg();
  let fullText = "";
  let meta = {};

  try {
    const res = await fetch(`${API}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message:      text,
        use_conclave: useConclave.checked,
        model:        modelSel.value,
      }),
    });

    if (!res.ok) {
      streamDiv.remove();
      const err = await res.json().catch(() => ({}));
      appendMsg("error", `⚠️ Erro ${res.status}: ${esc(err.error || res.statusText)}`);
      return;
    }

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") break;
        try {
          const ev = JSON.parse(raw);
          if (ev.type === "token") {
            fullText += ev.text;
            neuralBrain?.fire(1);   // cada token dispara um neurônio
            streamDiv.querySelector(".msg-bubble").innerHTML =
              renderMarkdown(fullText) + '<span class="stream-cursor">▋</span>';
            chatLog.scrollTop = chatLog.scrollHeight;
          } else if (ev.type === "meta") {
            meta = ev;
            if (ev.brain)  setBrain(ev.brain);
            if (ev.intent && sysIntentEl) sysIntentEl.textContent = ev.intent;
          } else if (ev.type === "done") {
            if (ev.text) fullText = ev.text;
            if (ev.brain)  { setBrain(ev.brain); meta.brain = ev.brain; }
            if (ev.intent) meta.intent = ev.intent;
            if (ev.ms)     { meta.ms = ev.ms; if (sysMsEl) sysMsEl.textContent = ev.ms + "ms"; reservoir?.push(ev.ms); }
          }
        } catch (_) {}
      }
    }

    // Finaliza a bolha
    streamDiv.querySelector(".msg-bubble").innerHTML = renderMarkdown(fullText || "Sem resposta.");
    streamDiv.classList.remove("streaming");
    if (meta.intent || meta.brain) {
      const md = document.createElement("div");
      md.className = "msg-meta";
      if (meta.intent) md.innerHTML += `<span class="tag">${esc(meta.intent)}</span>`;
      if (meta.brain)  md.innerHTML += `<span class="tag">🧠 ${esc(meta.brain)}</span>`;
      if (meta.ms)     md.innerHTML += `<span>${meta.ms}ms</span>`;
      streamDiv.appendChild(md);
    }
    _msgCount++;
    if (statCount) statCount.textContent  = _msgCount;
    if (sysCountEl) sysCountEl.textContent = _msgCount;

    if (useTts?.checked && fullText) speak(fullText);

  } catch (err) {
    streamDiv.remove();
    if (err.name === "TypeError") {
      appendMsg("error", "⚠️ Servidor offline. Inicie com: <code>python backend/server.py</code>");
    } else {
      appendMsg("error", `⚠️ ${esc(err.message)}`);
    }
  } finally {
    setLoading(false);
  }
}

function _appendStreamMsg() {
  const div    = document.createElement("div");
  div.className = "msg assistant streaming";
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = '<span class="stream-cursor">▋</span>';
  div.appendChild(bubble);
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

// ─── Debate autônomo (Squad) ───────────────────────────────
async function runAutonomousDebate(task) {
  removeWelcome();
  appendMsg("user", `🤝 Debate autônomo: ${esc(task)}`);
  setLoading(true);
  clearAgentActivity();

  const typing = appendTyping("squad debatendo...");

  try {
    const res = await fetch(`${API}/debate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task,
        agents: ["architect", "developer", "analyst", "qa"],
        rounds: 2,
        model:  modelSel.value,
      }),
    });

    typing.remove();

    if (!res.ok) {
      appendMsg("error", `⚠️ Erro no debate: ${res.statusText}`);
      return;
    }

    const data = await res.json();

    appendMsg("assistant", renderMarkdown(data.synthesis || "Sem síntese."), {
      intent: "debate autônomo",
      brain: "squad",
    });

    if (data.rounds?.length) {
      renderSquadRounds(data.rounds);
      squadWrap.classList.remove("hidden");
      squadWrap.classList.add("open");
    }

    if (data.saved_to) {
      appendMsg("assistant",
        `💾 Decisão salva em <code>_memoria/${esc(data.saved_to)}</code>`,
        {}
      );
    }

    setBrain("conclave");
    highlightAgents(data.agents || []);

  } catch (err) {
    typing.remove();
    appendMsg("error", `⚠️ ${esc(err.message)}`);
  } finally {
    setLoading(false);
  }
}

// ─── Handle API response ──────────────────────────────────
function handleResponse(data) {
  const response  = data.response || data.message || "Sem resposta.";
  const brain     = data.brain || "main";
  const agents    = data.agents || [];
  const plan      = data.plan || "";
  const conclave  = data.conclave || {};
  const squad     = data.squad || {};
  const isBlocked = data.status === "blocked";

  appendMsg(
    isBlocked ? "blocked" : "assistant",
    renderMarkdown(response),
    { intent: data.intent, brain, ms: data.ms }
  );

  setBrain(brain);

  // Update stats
  _msgCount++;
  if (statCount)  statCount.textContent  = _msgCount;
  if (sysCountEl) sysCountEl.textContent = _msgCount;
  if (data.ms != null) {
    if (sysMsEl) sysMsEl.textContent = data.ms + "ms";
    reservoir?.push(data.ms);
  }
  if (data.intent && sysIntentEl) {
    sysIntentEl.textContent = data.intent;
  }

  if (agents.length) highlightAgents(agents);
  if (plan)          planBox.textContent = plan;

  if (conclave.used) {
    updateConclave(conclave);
    conclaveWrap.classList.remove("hidden");
    conclaveWrap.classList.add("open");
  }

  if (squad.used) {
    renderSquadRounds(squad.rounds || []);
    squadWrap.classList.remove("hidden");
    squadWrap.classList.add("open");
  }
}

// ─── Squad rounds renderer ────────────────────────────────
function renderSquadRounds(rounds) {
  squadRounds.innerHTML = "";

  const agentIcons = {
    architect: "🏗️", developer: "💻", analyst: "📊",
    qa: "🔍", jarvis_soul: "✨",
  };

  rounds.forEach(r => {
    const div = document.createElement("div");
    div.className = "squad-round";

    const label = r.type === "analise" ? "ANÁLISE INDIVIDUAL" : `DEBATE — RODADA ${r.round}`;
    div.innerHTML = `<div class="squad-round-hdr">RODADA ${r.round} · ${label}</div>`;

    const outputs = document.createElement("div");
    outputs.className = "squad-agent-outputs";

    for (const [agentId, txt] of Object.entries(r.outputs || {})) {
      const agDiv = document.createElement("div");
      agDiv.className = "squad-agent";
      const icon = agentIcons[agentId] || "🤖";
      agDiv.innerHTML = `
        <div class="squad-agent-name">${icon} ${agentId.toUpperCase()}</div>
        <div class="squad-agent-txt">${esc(txt).replace(/\n/g, "<br>")}</div>
      `;
      outputs.appendChild(agDiv);
    }

    div.appendChild(outputs);
    squadRounds.appendChild(div);
  });
}

// ─── UI helpers ───────────────────────────────────────────
function appendMsg(role, html, meta = {}) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = html;
  div.appendChild(bubble);

  if (meta && (meta.intent || meta.brain || meta.ms != null)) {
    const metaDiv = document.createElement("div");
    metaDiv.className = "msg-meta";
    if (meta.intent) metaDiv.innerHTML += `<span class="tag">${esc(meta.intent)}</span>`;
    if (meta.brain)  metaDiv.innerHTML += `<span class="tag">🧠 ${esc(meta.brain)}</span>`;
    if (meta.ms != null) metaDiv.innerHTML += `<span>${meta.ms}ms</span>`;
    div.appendChild(metaDiv);
  }

  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

function appendTyping(label = "pensando...") {
  const div = document.createElement("div");
  div.className = "typing-indicator";
  div.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div><span>${esc(label)}</span>`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

function removeWelcome() {
  const wb = chatLog.querySelector(".welcome-block");
  if (wb) wb.remove();
}

function setLoading(on) {
  sendBtn.disabled = on;
  inputEl.disabled = on;
  // Orbe reage: pensa enquanto carrega; ao terminar volta a ouvir (se voz ativa) ou idle
  if (on) {
    neuralBrain?.setState(useConclave?.checked ? "conclave" : "thinking");
  } else if (typeof autoWhi !== "undefined" && autoWhi?.active) {
    neuralBrain?.setState("listening");
  } else {
    neuralBrain?.setState("idle");
  }
}

function setBrain(name) {
  const map = { squad: "conclave" };
  const key = map[name] || name;
  Object.entries(brainCards).forEach(([k, el]) => {
    el?.classList.toggle("active", k === key);
  });
  const label = { main: "MAIN", conclave: "CONCLAVE", memory: "MEMORY" }[key] || key.toUpperCase();
  if (statBrainLbl) statBrainLbl.textContent = label;
  if (sysBrainEl)   sysBrainEl.textContent   = label;
  // Reflete o cérebro ativo na cor dos neurônios enquanto processa
  if (sendBtn.disabled) {
    neuralBrain?.setState(key === "conclave" ? "conclave" : "thinking");
  }
}

function highlightAgents(ids) {
  clearAgentActivity();
  ids.forEach(id => {
    if (agentCards[id]) agentCards[id].classList.add("active");
  });
  setTimeout(clearAgentActivity, 5000);
}

function clearAgentActivity() {
  Object.values(agentCards).forEach(c => c.classList.remove("active"));
}

function updateConclave(c) {
  if (c.critico)   ct.critico.textContent   = c.critico;
  if (c.advogado)  ct.advogado.textContent  = c.advogado;
  if (c.synthesis) ct.sintetizador.textContent = c.synthesis;
}

// ─── Status check ─────────────────────────────────────────
async function checkStatus() {
  setSvc(svcClaude, "checking");
  setSvc(svcWebui,  "checking");
  try {
    const res  = await fetch(`${API}/status`, { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    const svcs = data.services || {};

    setSvc(svcClaude, data.brain?.status         === "online" ? "online" : "offline");
    setSvc(svcWebui,  svcs["Open WebUI"]?.status === "online" ? "online" : "offline");
  } catch {
    setSvc(svcClaude, "offline");
    setSvc(svcWebui,  "offline");
  }
}

function setSvc(el, state) {
  el.className = "svc";
  if (state === "offline")  el.classList.add("offline");
  if (state === "checking") el.classList.add("checking");
}

// ─── Markdown renderer ────────────────────────────────────
function renderMarkdown(raw) {
  const blocks = [];
  const withPH = raw.replace(/```[\w]*\n?([\s\S]*?)```/g, (_, code) => {
    blocks.push(code.trim());
    return `\x00BLOCK${blocks.length - 1}\x00`;
  });

  let out = esc(withPH)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^#{1,3}\s+(.+)$/gm, "<strong>$1</strong>")
    .replace(/^\s*[-*]\s+(.+)$/gm, "• $1")
    .replace(/\n/g, "<br>");

  blocks.forEach((code, i) => {
    out = out.replace(`\x00BLOCK${i}\x00`, `<pre><code>${esc(code)}</code></pre>`);
  });
  return out;
}

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Update brain card name when model changes
modelSel?.addEventListener("change", () => {
  const nameEl = document.getElementById("bc-main-name");
  if (nameEl) nameEl.textContent = modelSel.value;
});

// ─── Session Timer ───────────────────────────────────────
function _tickSession() {
  const s = Math.floor((Date.now() - _sessionStart) / 1000);
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  const t = `${mm}:${ss}`;
  if (statSession)  statSession.textContent  = t;
  if (sysUptimeEl)  sysUptimeEl.textContent  = t;
}

// ─── Reservoir Chart ──────────────────────────────────────
class ReservoirChart {
  constructor(canvas) {
    this.ctx  = canvas.getContext("2d");
    this.w    = canvas.width;
    this.h    = canvas.height;
    this.data = new Array(32).fill(0);
    this.peak = 0;
    this._draw();
  }

  push(ms) {
    this.data.push(ms);
    if (this.data.length > 32) this.data.shift();
    if (ms > this.peak) this.peak = ms;
    const avg = Math.round(this.data.reduce((a, b) => a + b, 0) / this.data.filter(v => v > 0).length || 1);
    const resAvg  = document.getElementById("res-avg");
    const resPeak = document.getElementById("res-peak");
    if (resAvg)  resAvg.textContent  = `avg ${avg}ms`;
    if (resPeak) resPeak.textContent = `pico ${this.peak}ms`;
    this._draw();
  }

  _draw() {
    const { ctx, w, h, data } = this;
    const max = Math.max(500, ...data) * 1.15;
    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = "rgba(34,34,58,0.9)";
    ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) {
      const y = (h / 4) * i;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Bars
    const bw = w / data.length;
    data.forEach((v, i) => {
      if (!v) return;
      const bh  = (v / max) * (h - 2);
      const x   = i * bw;
      const y   = h - bh;
      const alpha = 0.3 + (i / data.length) * 0.7;
      const grad = ctx.createLinearGradient(0, y, 0, h);
      grad.addColorStop(0, `rgba(0,229,255,${alpha})`);
      grad.addColorStop(1, `rgba(0,229,255,${alpha * 0.15})`);
      ctx.fillStyle = grad;
      ctx.fillRect(x + 1, y, Math.max(bw - 2, 1), bh);
    });

    // Trend line
    const pts = data.map((v, i) => [i * bw + bw / 2, h - (v / max) * (h - 2)]);
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0,229,255,0.55)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([]);
    pts.forEach(([x, y], i) => i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y));
    ctx.stroke();
  }
}

const _resCanvas = document.getElementById("reservoir-canvas");
const reservoir  = _resCanvas ? new ReservoirChart(_resCanvas) : null;

// ─── Voice Orb — orbe circular tecnológico (cérebro de voz JAMBA) ───
class VoiceOrb {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx    = canvas.getContext("2d");
    this.state  = "idle";              // idle | thinking | conclave | listening
    this.color  = { r: 0, g: 229, b: 255 };
    this.level  = 0;                   // 0..1 amplitude do microfone
    this._level = 0;                   // suavizado
    this.flash  = 0;                   // brilho extra a cada token
    this.wave   = new Array(64).fill(0);
    this._resize();
    window.addEventListener("resize", () => this._resize());
    this._loop();
  }

  _resize() {
    const r = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.w = r.width || 360;  this.h = r.height || 360;
    this.canvas.width  = this.w * dpr;
    this.canvas.height = this.h * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  setState(state) {
    this.state = state;
    const stage = document.getElementById("orb-stage")?.closest(".stage");
    const lblS  = document.getElementById("neural-state");
    const lblP  = document.getElementById("neural-pulse-lbl");
    stage?.classList.remove("thinking", "conclave");
    if (state === "thinking") {
      this.color = { r: 0, g: 229, b: 255 };
      stage?.classList.add("thinking");
      if (lblS) lblS.textContent = "PROCESSANDO";
      if (lblP) lblP.textContent = "raciocinando...";
    } else if (state === "conclave") {
      this.color = { r: 168, g: 85, b: 247 };
      stage?.classList.add("conclave");
      if (lblS) lblS.textContent = "CONCLAVE";
      if (lblP) lblP.textContent = "debate interno";
    } else if (state === "listening") {
      this.color = { r: 0, g: 229, b: 255 };
      if (lblS) lblS.textContent = "OUVINDO";
      if (lblP) lblP.textContent = "fala que eu te escuto";
    } else {
      this.color = { r: 0, g: 229, b: 255 };
      if (lblS) lblS.textContent = "ONLINE";
      if (lblP) lblP.textContent = "aguardando comando";
    }
  }

  // nível de áudio do microfone (0..1) — deixa o orbe reativo à voz
  setLevel(v) { this.level = Math.min(1, Math.max(0, v)); }

  // brilho pontual a cada token gerado
  fire() { this.flash = Math.min(1, this.flash + 0.5); }

  _loop() {
    const { ctx, w, h, color } = this;
    const cx = w / 2, cy = h / 2;
    const R  = Math.min(w, h) * 0.34;     // raio base
    const t  = Date.now() / 1000;
    ctx.clearRect(0, 0, w, h);

    // suaviza nível e flash
    this._level += (this.level - this._level) * 0.2;
    this.flash  *= 0.9;
    const active = this.state !== "idle";
    const energy = (active ? 0.5 : 0.18) + this._level * 0.9 + this.flash * 0.6;
    const C = (a) => `rgba(${color.r},${color.g},${color.b},${a})`;

    // halo externo
    const halo = ctx.createRadialGradient(cx, cy, R * 0.4, cx, cy, R * 2.0);
    halo.addColorStop(0, C(0.10 + energy * 0.10));
    halo.addColorStop(1, C(0));
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, w, h);

    // anéis rotativos (arcos)
    const rings = [
      { rad: R * 1.55, w: 1,   sp: 0.25, span: 1.1, a: 0.18 },
      { rad: R * 1.34, w: 1.5, sp: -0.4, span: 2.4, a: 0.30 },
      { rad: R * 1.16, w: 1,   sp: 0.6,  span: 0.8, a: 0.22 },
    ];
    rings.forEach((rg, i) => {
      ctx.strokeStyle = C(rg.a + energy * 0.15);
      ctx.lineWidth = rg.w;
      ctx.beginPath();
      ctx.arc(cx, cy, rg.rad, t * rg.sp, t * rg.sp + rg.span);
      ctx.stroke();
      // ponto na ponta do arco
      const ex = cx + Math.cos(t * rg.sp + rg.span) * rg.rad;
      const ey = cy + Math.sin(t * rg.sp + rg.span) * rg.rad;
      ctx.fillStyle = C(0.6);
      ctx.beginPath(); ctx.arc(ex, ey, 2, 0, Math.PI * 2); ctx.fill();
    });

    // anel pontilhado (tracejado) girando
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-t * 0.3);
    ctx.strokeStyle = C(0.12);
    ctx.setLineDash([2, 8]);
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(0, 0, R * 1.72, 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // onda de áudio circular (waveform reativa)
    const N = this.wave.length;
    for (let i = 0; i < N; i++) {
      const target = active || this._level > 0.02
        ? (Math.sin(t * 6 + i * 0.5) * 0.5 + 0.5) * (0.3 + this._level * 2 + this.flash)
        : 0;
      this.wave[i] += (target - this.wave[i]) * 0.25;
    }
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {
      const idx = i % N;
      const ang = (i / N) * Math.PI * 2 - Math.PI / 2;
      const amp = R * 0.9 + this.wave[idx] * R * 0.45;
      const x = cx + Math.cos(ang) * amp;
      const y = cy + Math.sin(ang) * amp;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = C(0.5 + energy * 0.3);
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // núcleo pulsante
    const corePulse = 1 + Math.sin(t * 2) * 0.06 + this._level * 0.5 + this.flash * 0.3;
    const coreR = R * 0.5 * corePulse;
    const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
    core.addColorStop(0,   C(0.55 + energy * 0.3));
    core.addColorStop(0.5, C(0.18));
    core.addColorStop(1,   C(0));
    ctx.fillStyle = core;
    ctx.beginPath(); ctx.arc(cx, cy, coreR, 0, Math.PI * 2); ctx.fill();

    // brilho central sólido
    ctx.fillStyle = C(0.85);
    ctx.beginPath(); ctx.arc(cx, cy, R * 0.06 * corePulse, 0, Math.PI * 2); ctx.fill();

    // partículas orbitando
    const pc = active ? 5 : 3;
    for (let i = 0; i < pc; i++) {
      const a = t * (0.5 + i * 0.2) + i * 2.4;
      const rr = R * (1.0 + 0.25 * Math.sin(t + i));
      const px = cx + Math.cos(a) * rr;
      const py = cy + Math.sin(a) * rr;
      ctx.fillStyle = C(0.7);
      ctx.beginPath(); ctx.arc(px, py, 1.6, 0, Math.PI * 2); ctx.fill();
    }

    requestAnimationFrame(() => this._loop());
  }
}

const _orbCanvas = document.getElementById("orb-canvas");
const neuralBrain = _orbCanvas ? new VoiceOrb(_orbCanvas) : null;

// ─── Voice Engine ─────────────────────────────────────────

class VoiceEngine {
  constructor() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.supported   = !!SR;
    this.recording   = false;
    this.autoMode    = false;
    this._manualStop = false;

    if (!this.supported) {
      if (micBtn) { micBtn.title = "Voz não suportada neste navegador"; micBtn.style.opacity = "0.35"; }
      const autoBtn = document.getElementById("voice-auto-btn");
      if (autoBtn) { autoBtn.title = "Voz não suportada"; autoBtn.style.opacity = "0.35"; }
      return;
    }

    this._buildRec(SR);
  }

  _buildRec(SR) {
    this.rec = new (SR || window.SpeechRecognition || window.webkitSpeechRecognition)();
    this.rec.lang = "pt-BR";
    this.rec.continuous = true;
    this.rec.interimResults = true;

    this.rec.onstart = () => {
      this.recording = true;
      micBtn?.classList.add("recording");
      voiceStatus?.classList.add("active");
    };

    this.rec.onresult = (e) => {
      let interim = "";
      let final   = "";
      for (const result of e.results) {
        if (result.isFinal) final   += result[0].transcript;
        else                 interim += result[0].transcript;
      }
      const display = this._stripWake(final || interim);
      inputEl.value = display;
      if (voiceInterim) voiceInterim.textContent = display;

      // Auto-envia assim que há resultado final — sem precisar clicar
      if (final.trim() && !sendBtn.disabled) {
        const toSend = this._stripWake(final.trim());
        if (toSend) {
          inputEl.value = "";
          if (voiceInterim) voiceInterim.textContent = "";
          sendVoiceMessage(toSend);
        }
      }
    };

    this.rec.onend = () => {
      this.recording = false;
      micBtn?.classList.remove("recording");
      if (!this.autoMode) voiceStatus?.classList.remove("active");
      if (voiceInterim) voiceInterim.textContent = "";

      const text = inputEl.value.trim();
      if (text && !sendBtn.disabled) {
        inputEl.value = "";
        sendVoiceMessage(text);
      }

      // Reinicia automaticamente se modo sempre-ativa estiver ligado
      if (this.autoMode && !this._manualStop) {
        setTimeout(() => {
          if (this.autoMode) {
            this._buildRec();
            try { this.rec.start(); } catch (e) {}
          }
        }, 500);
      }
    };

    this.rec.onerror = (e) => {
      this.recording = false;
      micBtn?.classList.remove("recording");
      voiceStatus?.classList.remove("active");
      if (e.error !== "no-speech" && e.error !== "aborted") {
        console.warn("Voice error:", e.error);
      }
    };
  }

  _stripWake(text) {
    return text.replace(/^(jamba|jambo|jambá|javis|jarvis|j[aá]vis)[,.]?\s*/i, "").trim() || text;
  }

  toggle() {
    if (!this.supported) return;
    if (this.recording) {
      this._manualStop = true;
      this.rec.stop();
    } else {
      this._manualStop = false;
      this._buildRec();
      try { this.rec.start(); } catch (e) { console.warn("Mic start failed:", e); }
    }
  }

  toggleAutoMode() {
    if (!this.supported) return;
    this.autoMode = !this.autoMode;
    const btn = document.getElementById("voice-auto-btn");
    if (this.autoMode) {
      this._manualStop = false;
      btn?.classList.add("active");
      voiceStatus?.classList.add("active");
      if (!this.recording) {
        this._buildRec();
        try { this.rec.start(); } catch (e) { console.warn("Auto voice start failed:", e); }
      }
    } else {
      this._manualStop = true;
      btn?.classList.remove("active");
      voiceStatus?.classList.remove("active");
      if (this.recording) this.rec.stop();
    }
  }
}

// ─── Whisper Recorder (push-to-talk via Whisper API) ─────
class WhisperRecorder {
  constructor() {
    this.recording   = false;
    this.mediaRec    = null;
    this.chunks      = [];
    this.stream      = null;
  }

  async toggle() {
    if (this.recording) {
      this._stop();
    } else {
      await this._start();
    }
  }

  async _start() {
    try {
      this.stream  = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunks  = [];
      this.mediaRec = new MediaRecorder(this.stream);
      this.mediaRec.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
      this.mediaRec.start(150);
      this.recording = true;
      micBtn?.classList.add("recording");
      voiceStatus?.classList.add("active");
      if (voiceInterim) voiceInterim.textContent = "gravando...";
    } catch (e) {
      console.warn("Mic error:", e);
    }
  }

  _stop() {
    if (!this.recording || !this.mediaRec) return;
    this.recording = false;
    micBtn?.classList.remove("recording");
    if (voiceInterim) voiceInterim.textContent = "transcrevendo...";

    this.mediaRec.onstop = async () => {
      const blob = new Blob(this.chunks, { type: this.mediaRec.mimeType || "audio/webm" });
      this.stream?.getTracks().forEach(t => t.stop());
      voiceStatus?.classList.remove("active");
      if (blob.size < 500) { if (voiceInterim) voiceInterim.textContent = ""; return; }
      try {
        const fd  = new FormData();
        fd.append("file", blob, "audio.webm");
        const res = await fetch(`${API}/transcribe`, { method: "POST", body: fd });
        if (res.ok) {
          const data = await res.json();
          const text = data.text?.trim();
          if (text && !sendBtn.disabled) sendVoiceMessage(text);
        }
      } catch (err) { console.warn("Whisper error:", err); }
      if (voiceInterim) voiceInterim.textContent = "";
    };
    this.mediaRec.stop();
  }
}

// ─── Auto Whisper Engine (always-on com VAD calibrado) ───
class AutoWhisperEngine {
  constructor() {
    this.active      = false;
    this.recording   = false;
    this.stream      = null;
    this.mediaRec    = null;
    this.chunks      = [];
    this.analyser    = null;
    this.silTimer    = null;
    this.recStart    = 0;
    this.THRESHOLD   = 0.035;   // calibrado dinamicamente no enable()
    this.SILENCE_MS  = 2200;
    this.MIN_REC_MS  = 800;     // ignora gravações muito curtas (ruído pontual)
    this.MIN_BLOB    = 4000;    // bytes mínimos para enviar ao Whisper
  }

  async enable() {
    this.active = true;
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx   = new AudioContext();
    const src   = ctx.createMediaStreamSource(this.stream);
    this.analyser = ctx.createAnalyser();
    this.analyser.fftSize = 1024;
    src.connect(this.analyser);

    // Calibração: mede ruído ambiente por 1.2s e define threshold dinâmico
    if (voiceInterim) voiceInterim.textContent = "calibrando microfone...";
    const noiseLevel = await this._measureNoise(1200);
    this.THRESHOLD = Math.max(0.030, noiseLevel * 3.5);
    if (voiceInterim) voiceInterim.textContent = `pronto (noise=${noiseLevel.toFixed(4)})`;
    setTimeout(() => {
      if (this.active && voiceInterim) voiceInterim.textContent = "aguardando voz...";
    }, 1200);

    this._loop();
    voiceStatus?.classList.add("active");
    neuralBrain?.setState("listening");
  }

  disable() {
    this.active = false;
    clearTimeout(this.silTimer);
    if (this.recording && this.mediaRec?.state === "recording") this.mediaRec.stop();
    this.stream?.getTracks().forEach(t => t.stop());
    voiceStatus?.classList.remove("active");
    if (voiceInterim) voiceInterim.textContent = "";
    neuralBrain?.setLevel(0);
    if (!sendBtn.disabled) neuralBrain?.setState("idle");
  }

  async _measureNoise(durationMs) {
    return new Promise(resolve => {
      const samples = [];
      const interval = setInterval(() => {
        const buf = new Float32Array(this.analyser.fftSize);
        this.analyser.getFloatTimeDomainData(buf);
        samples.push(Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length));
      }, 50);
      setTimeout(() => {
        clearInterval(interval);
        const avg = samples.reduce((a, b) => a + b, 0) / (samples.length || 1);
        resolve(avg);
      }, durationMs);
    });
  }

  _loop() {
    if (!this.active) return;
    const buf = new Float32Array(this.analyser.fftSize);
    this.analyser.getFloatTimeDomainData(buf);
    const vol = Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length);

    // Alimenta o orbe com o nível de voz — reage em tempo real
    neuralBrain?.setLevel(Math.min(1, vol * 12));

    if (vol > this.THRESHOLD && !this.recording) {
      this._startSeg();
    } else if (vol <= this.THRESHOLD && this.recording && !this.silTimer) {
      this.silTimer = setTimeout(() => this._stopSeg(), this.SILENCE_MS);
    } else if (vol > this.THRESHOLD && this.silTimer) {
      clearTimeout(this.silTimer); this.silTimer = null;
    }
    requestAnimationFrame(() => this._loop());
  }

  _startSeg() {
    this.recording = true;
    this.chunks    = [];
    this.recStart  = Date.now();
    this.mediaRec  = new MediaRecorder(this.stream);
    this.mediaRec.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
    this.mediaRec.start(100);
    if (voiceInterim) voiceInterim.textContent = "ouvindo...";
  }

  _stopSeg() {
    this.recording = false;
    this.silTimer  = null;
    if (!this.mediaRec || this.mediaRec.state !== "recording") return;

    const elapsed = Date.now() - this.recStart;

    this.mediaRec.onstop = async () => {
      const blob = new Blob(this.chunks, { type: this.mediaRec.mimeType || "audio/webm" });

      // Descarta ruído curto ou blob muito pequeno
      if (elapsed < this.MIN_REC_MS || blob.size < this.MIN_BLOB) {
        if (this.active && voiceInterim) voiceInterim.textContent = "aguardando voz...";
        return;
      }

      if (voiceInterim) voiceInterim.textContent = "transcrevendo...";
      try {
        const fd  = new FormData();
        fd.append("file", blob, "audio.webm");
        const res = await fetch(`${API}/transcribe`, { method: "POST", body: fd });
        if (res.ok) {
          const data = await res.json();
          const text = data.text?.trim();
          // Filtra respostas de ruído (Whisper às vezes retorna "Obrigado." ou "..." para silêncio)
          const WHISPER_NOISE = /^(obrigado\.?|thanks\.?|thank you\.?|\.{2,}|música\.?|music\.?|legendas?\.?|subtitles?\.?|silence\.?|silêncio\.?|som de fundo\.?|background\.?|applause\.?|aplauso\.?|ruído\.?|noise\.?|beep\.?|bip\.?)$/i;
          const isNoise = !text
            || text.length < 4
            || WHISPER_NOISE.test(text.trim())
            || (text.length < 8 && /^[.,!?…\s]+$/.test(text));
          if (!isNoise && !sendBtn.disabled) sendVoiceMessage(text);
        }
      } catch (err) { console.warn("Auto whisper error:", err); }
      if (this.active && voiceInterim) voiceInterim.textContent = "aguardando voz...";
    };
    this.mediaRec.stop();
  }
}

// ─── Wake Word Engine — "Jamba" ativa por voz (hands-free) ───
class WakeWordEngine {
  constructor() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.supported = !!SR;
    this.SR = SR;
    this.active = false;
    this.awoken = false;
    this.awokenTimer = null;
    this.rec = null;
    this.wakeRe = /\b(jamba|jamb[aá]|jambo|jambar|jarvis|j[aá]vis)\b/i;
  }

  toggle() {
    if (!this.supported) {
      if (voiceInterim) voiceInterim.textContent = "wake word precisa do Chrome/Edge";
      return;
    }
    this.active ? this.disable() : this.enable();
  }

  enable() {
    // mutuamente exclusivo com o modo always-on (👂) — ambos usam o microfone
    if (typeof autoWhi !== "undefined" && autoWhi?.active) {
      autoWhi.disable();
      document.getElementById("voice-auto-btn")?.classList.remove("active");
    }
    this.active = true;
    document.getElementById("wake-btn")?.classList.add("active");
    voiceStatus?.classList.add("active");
    if (voiceInterim) voiceInterim.textContent = 'diga "Jamba" para ativar...';
    neuralBrain?.setState("listening");
    this._build();
    this._start();
  }

  disable() {
    this.active = false;
    clearTimeout(this.awokenTimer);
    this.awoken = false;
    document.getElementById("wake-btn")?.classList.remove("active");
    voiceStatus?.classList.remove("active");
    if (voiceInterim) voiceInterim.textContent = "";
    if (!sendBtn.disabled) neuralBrain?.setState("idle");
    try { this.rec?.stop(); } catch (e) {}
  }

  _build() {
    this.rec = new this.SR();
    this.rec.lang = "pt-BR";
    this.rec.continuous = true;
    this.rec.interimResults = true;
    this.rec.onresult = (e) => this._onResult(e);
    this.rec.onend = () => { if (this.active) { try { this.rec.start(); } catch (e) {} } };
    this.rec.onerror = (e) => { if (e.error === "not-allowed") this.disable(); };
  }

  _start() { try { this.rec.start(); } catch (e) {} }

  _onResult(e) {
    // só o que foi finalizado agora (resultIndex evita reprocessar tudo)
    let finalText = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
    }
    finalText = finalText.trim();
    if (!finalText) return;

    const lower = finalText.toLowerCase();
    const m = lower.match(this.wakeRe);

    if (m) {
      neuralBrain?.setState("listening");
      neuralBrain?.fire?.();
      const idx = lower.indexOf(m[0]) + m[0].length;
      const after = finalText.slice(idx).replace(/^[,.\s]+/, "").trim();
      if (after) {
        this._send(after);                 // "Jamba, toca jazz" → envia "toca jazz"
      } else {
        this.awoken = true;                // só "Jamba" → janela de 6s pro comando
        if (voiceInterim) voiceInterim.textContent = "pode falar, senhor...";
        clearTimeout(this.awokenTimer);
        this.awokenTimer = setTimeout(() => {
          this.awoken = false;
          if (this.active && voiceInterim) voiceInterim.textContent = 'diga "Jamba" para ativar...';
        }, 6000);
      }
    } else if (this.awoken) {
      this.awoken = false;
      clearTimeout(this.awokenTimer);
      this._send(finalText);               // comando logo após o "Jamba"
    }
  }

  _send(cmd) {
    if (!cmd || sendBtn.disabled) return;
    if (voiceInterim) voiceInterim.textContent = "";
    sendVoiceMessage(cmd);
    if (this.active && voiceInterim) {
      setTimeout(() => {
        if (this.active && !sendBtn.disabled && voiceInterim)
          voiceInterim.textContent = 'diga "Jamba" para ativar...';
      }, 1500);
    }
  }
}

const whisper   = new WhisperRecorder();
const autoWhi   = new AutoWhisperEngine();
const voice     = new VoiceEngine();
const wakeWord  = new WakeWordEngine();

micBtn?.addEventListener("click", () => whisper.toggle());
document.getElementById("wake-btn")?.addEventListener("click", () => wakeWord.toggle());

document.getElementById("voice-auto-btn")?.addEventListener("click", async () => {
  const btn = document.getElementById("voice-auto-btn");
  if (autoWhi.active) {
    autoWhi.disable();
    btn?.classList.remove("active");
  } else {
    // mutuamente exclusivo com o wake word (🎙️) — ambos usam o microfone
    if (typeof wakeWord !== "undefined" && wakeWord?.active) wakeWord.disable();
    try {
      await autoWhi.enable();
      btn?.classList.add("active");
    } catch (e) {
      console.warn("Auto whisper enable failed:", e);
      voice.toggleAutoMode();
    }
  }
});

// ─── Send via voice ───────────────────────────────────────

async function sendVoiceMessage(text) {
  removeWelcome();
  appendMsg("user", `🎤 ${esc(text)}`);
  setLoading(true);
  clearAgentActivity();

  // Para áudio anterior
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
  _audioQueue.length = 0;
  _audioPlaying = false;

  const typing = appendTyping("processando voz...");
  let fullText = "";
  let msgDiv = null;

  try {
    const res = await fetch(`${API}/voice/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transcript:   text,
        model:        modelSel?.value || "",
        use_conclave: useConclave?.checked || false,
        tts:          useTts?.checked ?? true,
      }),
    });

    typing.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendMsg("error", `⚠️ Erro ${res.status}: ${esc(err.error || res.statusText)}`);
      return;
    }

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") break;
        let evt;
        try { evt = JSON.parse(raw); } catch (_) { continue; }

        if (evt.type === "audio") {
          enqueueAudio(evt.b64);
          if (evt.sentence) fullText += (fullText ? " " : "") + evt.sentence;
        } else if (evt.type === "tts_text") {
          speak(evt.text);
          fullText = evt.text;
        } else if (evt.type === "token") {
          fullText += evt.text;
        } else if (evt.type === "meta" && evt.text) {
          fullText = evt.text;
        } else if (evt.type === "done") {
          if (evt.text) fullText = evt.text;
          if (!msgDiv) {
            msgDiv = appendMsg("assistant", renderMarkdown(fullText),
                               { intent: evt.intent, brain: evt.brain, ms: evt.ms });
          }
          setBrain(evt.brain || "main");
          _msgCount++;
          if (statCount)  statCount.textContent  = _msgCount;
          if (sysCountEl) sysCountEl.textContent = _msgCount;
          if (evt.ms != null && sysMsEl) sysMsEl.textContent = evt.ms + "ms";
          if (evt.intent && sysIntentEl) sysIntentEl.textContent = evt.intent;
        }
      }
    }

    if (!msgDiv && fullText) {
      appendMsg("assistant", renderMarkdown(fullText));
    }

  } catch (err) {
    typing?.remove();
    if (err.name === "TypeError") {
      appendMsg("error", "⚠️ Servidor offline.");
    } else {
      appendMsg("error", `⚠️ ${esc(err.message)}`);
    }
  } finally {
    setLoading(false);
  }
}

let _currentAudio = null;

// Fila de áudio — reproduz chunks em ordem sem gaps
const _audioQueue = [];
let _audioPlaying = false;

function enqueueAudio(b64) {
  const bytes = atob(b64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const blob = new Blob([arr], { type: "audio/mpeg" });
  _audioQueue.push(URL.createObjectURL(blob));
  _drainAudioQueue();
}

function _drainAudioQueue() {
  if (_audioPlaying || _audioQueue.length === 0) return;
  _audioPlaying = true;
  const url = _audioQueue.shift();
  _currentAudio = new Audio(url);
  neuralBrain?.setState("speaking");
  _currentAudio.onended = () => {
    URL.revokeObjectURL(url);
    _currentAudio = null;
    _audioPlaying = false;
    if (_audioQueue.length > 0) {
      _drainAudioQueue();
    } else {
      if (!sendBtn?.disabled) neuralBrain?.setState("idle");
    }
  };
  _currentAudio.play().catch(() => { _audioPlaying = false; });
}

function cleanForSpeech(text) {
  return String(text || "")
    .replace(/```[\s\S]*?```/g, " ")              // blocos de código
    .replace(/`[^`]*`/g, " ")                      // código inline
    .replace(/\[[^\]]*\]\([^)]*\)/g, "")           // links markdown [txt](url)
    .replace(/https?:\/\/\S+/g, "")                // URLs cruas
    .replace(/\[[^\]]*\.(md|txt|py|js|json)\]/gi, "") // marcadores de arquivo do RAG
    .replace(/<[^>]+>/g, "")                        // HTML
    .replace(/[*_#>`~|]/g, "")                      // símbolos markdown
    .replace(/^\s*\d+[\.\)]\s*/gm, "")             // "1." "2)" de listas
    .replace(/^\s*[-•]\s*/gm, "")                   // bullets
    .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}]/gu, "") // emojis/setas
    .replace(/\s+/g, " ")                           // espaços/quebras múltiplas
    .trim()
    .substring(0, 600);
}

async function speak(text) {
  if (!text) return;
  const clean = cleanForSpeech(text);
  if (!clean) return;

  // Para áudio anterior se ainda estiver tocando
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  try {
    const res = await fetch(`${API}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: clean }),
    });
    if (res.ok) {
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      _currentAudio = new Audio(url);
      _currentAudio.onended = () => { URL.revokeObjectURL(url); _currentAudio = null; };
      _currentAudio.play();
      return;
    }
  } catch (_) {}

  // Fallback — Web Speech API (voz do navegador)
  if (!window.speechSynthesis) return;
  const utt   = new SpeechSynthesisUtterance(clean);
  utt.lang    = "pt-BR";
  utt.rate    = 1.0;
  utt.pitch   = 1.0;

  neuralBrain?.setState("speaking");
  utt.onboundary = (e) => {
    const intensity = Math.min(1, (e.charLength || 4) / 12);
    neuralBrain?.setLevel(0.3 + intensity * 0.7);
  };
  utt.onend = () => {
    neuralBrain?.setLevel(0);
    if (!sendBtn?.disabled) neuralBrain?.setState("idle");
  };

  window.speechSynthesis.speak(utt);
}

/* ═══════════════════════════════════════════════════════════
   JAVIS AIOS — View Router & Multi-View Logic
═══════════════════════════════════════════════════════════ */

const VIEW_TITLES = { chat:'Orquestrador', agents:'Agentes', mente:'Mente', workflows:'Workflows', room:'Sala dos Agentes', quadro:'Quadro', fluxovp:'Fluxo Vem Passear', timevp:'Time Vem Passear', projects:'Projetos', train:'SDR Academy', integrations:'Integrações' };

function switchView(viewId) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.sb-item[data-view]').forEach(b => b.classList.remove('active'));
  const view = document.getElementById('view-' + viewId);
  if (view) view.classList.add('active');
  const btn = document.querySelector(`.sb-item[data-view="${viewId}"]`);
  if (btn) btn.classList.add('active');
  const titleEl = document.getElementById('topbar-view-title');
  if (titleEl) titleEl.textContent = VIEW_TITLES[viewId] || viewId;
  if (viewId === 'agents' && !document.getElementById('gallery-grid').children.length) renderAgentGallery();
  if (viewId === 'mente') renderOrgChart();
  if (viewId === 'workflows') initWorkflowCanvas();
  if (viewId === 'integrations' && !document.getElementById('integrations-grid').children.length) renderIntegrations();
  if (viewId === 'room') initAgentRoom(); else stopAgentRoom();
  if (viewId === 'projects' && !document.getElementById('projects-grid').children.length) renderProjects();
  if (viewId === 'quadro') renderQuadro();
  if (viewId === 'fluxovp') renderPipelineVP();
  if (viewId === 'timevp') renderVPSquad();
  if (viewId === 'train') renderTrainAreas();
}

// ─── Time Vem Passear: os 5 agentes com contrato (do backend /vp/agents) ────
let VP_AGENTS = [];

async function renderVPSquad() {
  const host = document.getElementById('tvp-grid');
  if (!host) return;
  host.innerHTML = '<div class="tvp-loading">Carregando o time…</div>';
  try {
    const res = await fetch(`${API}/vp/agents`, { signal: AbortSignal.timeout(5000) });
    const data = await res.json();
    VP_AGENTS = data.agents || [];
  } catch {
    host.innerHTML = '<div class="tvp-loading">Não consegui carregar o time, senhor (servidor offline?).</div>';
    return;
  }
  host.innerHTML = VP_AGENTS.map(_vpCard).join('');
}

function _vpCard(a) {
  return `<div class="tvp-card" id="tvp-${a.id}">
    <div class="tvp-head">
      <span class="tvp-emoji">${a.icon || '🤖'}</span>
      <div>
        <div class="tvp-name">${esc(a.name)}</div>
        <div class="tvp-role">${esc(a.role || '')}</div>
      </div>
    </div>
    <div class="tvp-contract">
      <div class="tvp-row"><span class="tvp-lbl">Entra</span><span>${esc(a.input || '')}</span></div>
      <div class="tvp-row"><span class="tvp-lbl">Sai</span><span>${esc(a.output || '')}</span></div>
      <div class="tvp-row tvp-naofaz"><span class="tvp-lbl">Não faz</span><span>${esc(a.naofaz || '')}</span></div>
    </div>
    <textarea class="tvp-task" id="tvp-task-${a.id}" rows="2" placeholder="O que o senhor quer que ${esc(a.name)} faça?"></textarea>
    <button class="tvp-run" onclick="runVPAgent('${a.id}')">Acionar ${esc(a.name)}</button>
    <div class="tvp-result" id="tvp-result-${a.id}"></div>
  </div>`;
}

async function runVPAgent(id) {
  const task = (document.getElementById(`tvp-task-${id}`)?.value || '').trim();
  const out  = document.getElementById(`tvp-result-${id}`);
  if (!task) { if (out) out.innerHTML = '<span class="tvp-warn">Escreva a tarefa primeiro, senhor.</span>'; return; }
  if (out) out.innerHTML = '<span class="tvp-spin">Trabalhando na assinatura… (pode levar ~40s)</span>';
  try {
    const res = await fetch(`${API}/vp/agents/run`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: id, task }),
      signal: AbortSignal.timeout(240000),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      out.innerHTML = `<div class="tvp-out">${renderMarkdown(data.result || '')}</div>`;
    } else {
      out.innerHTML = `<span class="tvp-warn">${esc(data.message || 'Não rolou agora, senhor.')}</span>`;
    }
  } catch (e) {
    out.innerHTML = `<span class="tvp-warn">Demorou demais ou falhou, senhor: ${esc(String(e))}</span>`;
  }
}

// ─── Fluxo Vem Passear: pipeline de marketing em raias (estilo Monday) ──────
// Espelha _projetos/cerebro-jampa/fluxograma-vem-passear.md. Cada raia é uma
// função (briefing→conteúdo→copy→design→tráfego→distribuição), com gate [G]
// (sua aprovação) ou conferência [C] quando o trabalho não pode pular adiante
// sem aval. A faixa de baixo é o loop de aprendizado que volta pro briefing.
const PIPELINE_VP = {
  lanes: [
    { id:'briefing', label:'Briefing', owner:'Você + dados', color:'#f59e0b',
      cards:['Maré da semana', 'Agenda de saídas', 'Vagas reais', 'Fotos novas', 'Combos OK'] },
    { id:'conteudo', label:'Conteúdo / Pauta', owner:'Nova', color:'#3b82f6',
      cards:['10-15 pautas', 'Pilar de cada', 'Objetivo: alcance/venda', 'Formato'],
      gate:{ t:'G', txt:'Você aprova a pauta' } },
    { id:'copy', label:'Roteiro & Copy', owner:'Nova + Midas', color:'#06b6d4',
      cards:['Gancho 3s', 'Roteiro por cena', 'Legenda + CTA', 'Palavra-chave WhatsApp'],
      gate:{ t:'C', txt:'Info sensível: maré/preço/vaga conferida' } },
    { id:'design', label:'Produção Visual', owner:'Design', color:'#ef4444',
      cards:['Carrossel (Canva)', 'Reel (CapCut)', 'gerar_carrossel.py', 'Nome-padrão de arquivo'],
      gate:{ t:'C', txt:'Marca / Design System' } },
    { id:'trafego', label:'Tráfego / Conversão', owner:'Midas', color:'#8b5cf6',
      cards:['CTA WhatsApp', 'Segmentação', 'Marcar p/ impulsionar'],
      gate:{ t:'G', txt:'Você aprova o FINAL (checklist)' } },
    { id:'distribuicao', label:'Distribuição', owner:'Você / Javis', color:'#22c55e',
      cards:['Agendar (Meta Suite)', 'Reel/Story no momento real', 'Registrar publicação'] },
  ],
  loop: { label:'Aprendizado ↺', owner:'Midas mede · você valida',
          txt:'retenção 3s · salvamentos · cliques no WhatsApp · reservas → vira o briefing da próxima semana' },
};

function _fvpLane(lane) {
  const cards = lane.cards.map(c => `<div class="fvp-card">${esc(c)}</div>`).join('');
  const gate = lane.gate
    ? `<div class="fvp-gate-row fvp-gate-${lane.gate.t.toLowerCase()}">
         <span class="fvp-gate fvp-${lane.gate.t.toLowerCase()}">${lane.gate.t}</span>
         <span class="fvp-gate-txt">${esc(lane.gate.txt)}</span>
       </div>`
    : '';
  return `<div class="fvp-lane" style="--lane:${lane.color}">
    <div class="fvp-lane-head">
      <span class="fvp-lane-name">${esc(lane.label)}</span>
      <span class="fvp-lane-owner">${esc(lane.owner)}</span>
    </div>
    <div class="fvp-cards">${cards}</div>
    ${gate}
  </div>`;
}

function renderPipelineVP() {
  const host = document.getElementById('fvp-board');
  if (!host) return;
  const lanes = PIPELINE_VP.lanes.map(_fvpLane).join('<div class="fvp-arrow">▶</div>');
  const loop = PIPELINE_VP.loop;
  host.innerHTML = `
    <div class="fvp-lanes">${lanes}</div>
    <div class="fvp-loop">
      <span class="fvp-loop-label">${esc(loop.label)}</span>
      <span class="fvp-loop-owner">${esc(loop.owner)}</span>
      <span class="fvp-loop-txt">${esc(loop.txt)}</span>
    </div>`;
}

// ─── Mente: organograma dos 17 agentes da "mente", por fase ──────────
// AIOS Master no topo → Produto / Construção / Qualidade / Conclave,
// com Jarvis Soul · Squad Creator · Rootcause numa faixa "meta" no topo.
//
// Dentro de cada fase, `flow` é uma sequência de "estágios": estágios com 1
// agente só viram setas de handover real entre eles (PO→PM→Scrum); estágios
// com vários agentes ficam empilhados sem seta (trabalham em paralelo, ex.:
// UX/DevOps/Data Engineer sob o Developer, ou Crítico+Advogado debatendo
// antes do Sintetizador) — mesma lógica do board de squads que inspirou isso
// (handover sólido = sequência obrigatória; sem seta = alternativas/paralelo).
const MENTE_TREE = {
  root: 'aios_master',
  groups: [
    { id:'produto',    label:'Produto',    flow: [['po'], ['pm'], ['scrum']] },
    { id:'construcao', label:'Construção', flow: [['architect'], ['developer'], ['ux_designer', 'devops', 'data_engineer']] },
    { id:'qualidade',  label:'Qualidade',  flow: [['qa', 'analyst']] },
    { id:'conclave',   label:'Conclave',   flow: [['critico', 'advogado'], ['sintetizador']] },
  ],
  meta: ['jarvis_soul', 'squad_creator', 'rootcause'],
};

function _agentById(id) { return AGENTS.find(a => a.id === id); }

function _orgCard(a, opts = {}) {
  if (!a) return '';
  const nome = opts.stripConclave ? a.name.replace(/^Conclave\s+/, '') : a.name;
  return `
    <div class="org-card oc-${a.phase}" onclick="openAgentChat('${a.id}')" title="Abrir chat com ${esc(a.name)}">
      <div class="oc-top">
        <span class="oc-emoji">${a.emoji}</span>
        <span class="oc-status oc-${a.status}" title="${a.status}"></span>
      </div>
      <div class="oc-name">${esc(nome)}</div>
      <div class="oc-role">${esc(a.tag || '')}</div>
    </div>`;
}

function _orgGroup(g) {
  const stages = g.flow.map(stage => {
    const cards = stage.map(id => _orgCard(_agentById(id), { stripConclave: g.id === 'conclave' })).join('');
    return `<div class="of-stage${stage.length > 1 ? ' of-parallel' : ''}">${cards}</div>`;
  });
  const flowHtml = stages.join('<div class="of-arrow" title="handover">▶</div>');
  return `<li>
    <div class="org-group og-${g.id}">${g.label}</div>
    <div class="org-flow">${flowHtml}</div>
  </li>`;
}

function renderOrgChart() {
  const host = document.getElementById('org-chart');
  if (!host) return;
  if (!AGENTS.length) { loadAgents().then(renderOrgChart); return; }
  const root = _orgCard(_agentById(MENTE_TREE.root));
  const band = MENTE_TREE.meta.map(id => _orgCard(_agentById(id))).join('');
  const groups = MENTE_TREE.groups.map(_orgGroup).join('');
  host.innerHTML = `
    <div class="org-meta-band"><span class="omb-label">META</span>${band}</div>
    <ul class="org-root"><li>
      ${root}
      <ul>${groups}</ul>
    </li></ul>`;
}

async function renderTrainAreas() {
  const grid = document.getElementById('train-areas-grid');
  if (!grid) return;
  const AREA_LABELS = {
    vendas: { icon: '🎯', label: 'Vendas' },
    conteudo: { icon: '🎨', label: 'Conteúdo' },
    tecnico: { icon: '⚙️', label: 'Técnico' },
    estrategia: { icon: '🧭', label: 'Estratégia' },
  };
  let areas = [];
  try {
    const r = await fetch('/treinamento/status');
    const j = await r.json();
    areas = j.areas || [];
  } catch { /* backend offline */ }
  grid.innerHTML = areas.map(a => {
    const meta = AREA_LABELS[a.area] || { icon: '📁', label: a.area };
    return `
      <div class="ta-card" id="ta-card-${a.area}">
        <div class="ta-icon">${meta.icon}</div>
        <div class="ta-name">${meta.label}</div>
        <div class="ta-stats">
          <span><b>${a.entrada}</b> em entrada</span>
          <span><b>${a.resumos}</b> resumidos</span>
        </div>
        <button class="ta-scout-btn" onclick="scoutArea('${a.area}')">🔍 buscar tendência</button>
      </div>
    `;
  }).join('') || `<div class="train-empty">_treinamento/ ainda sem áreas.</div>`;
}

async function scoutArea(area) {
  const card = document.getElementById(`ta-card-${area}`);
  const btn = card ? card.querySelector('.ta-scout-btn') : null;
  if (btn) { btn.disabled = true; btn.textContent = '⏳ buscando...'; }
  try {
    const r = await fetch(`/treinamento/scout/${area}`, { method: 'POST' });
    const j = await r.json();
    if (btn) btn.textContent = j.novos > 0 ? `✓ +${j.novos} novos` : '— nada novo';
  } catch {
    if (btn) btn.textContent = '✗ erro';
  }
  await renderTrainAreas();
}

async function scoutAllAreas() {
  const btn = document.getElementById('ta-scout-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ esquadrões em campo...'; }
  try {
    await fetch('/treinamento/scout-all', { method: 'POST' });
  } catch { /* ignore */ }
  if (btn) { btn.disabled = false; btn.textContent = '🔍 Esquadrões: buscar tudo'; }
  await renderTrainAreas();
}

document.querySelectorAll('.sb-item[data-view]').forEach(btn => {
  btn.addEventListener('click', () => switchView(btn.dataset.view));
});

/* ─── AGENT DATA ─────────────────────────────────────────── */
// Roster de orquestração = os 17 agentes da "mente" (servidos por GET /agents).
// O array de vendas foi preservado abaixo (não usado na UI) caso volte a fazer sentido.
const _LEGACY_SALES_AGENTS = [
  { id:'orion',   name:'Orion',   role:'@master',     emoji:'🧬', squad:'ops',      status:'online',  desc:'Orquestra todos os agentes e decisões estratégicas do sistema.', skills:['Orquestração','Decisão','Priorização'], ints:['slack','gmail','notion'] },
  { id:'titan',   name:'Titan',   role:'@cro',        emoji:'👑', squad:'ops',      status:'online',  desc:'Orquestra todo o time de vendas, garantindo alinhamento e resultados.', skills:['Liderança','Vendas','KPIs'], ints:['slack','gmail','notion'] },
  { id:'khan',    name:'Khan',    role:'@bdr-global', emoji:'📞', squad:'vendas',   status:'online',  desc:'Gerencia outbound global, prospecção e qualificação de leads.', skills:['Prospecção','Cold Call','Qualificação'], ints:['whatsapp','gmail','sheets'] },
  { id:'phantom', name:'Phantom', role:'@closer',     emoji:'🎯', squad:'vendas',   status:'online',  desc:'Conduz negociações e fecha contratos de alto valor.', skills:['Fechamento','Negociação','Follow-up'], ints:['whatsapp','gmail'] },
  { id:'blade',   name:'Blade',   role:'@bdr-en',     emoji:'⚔️', squad:'vendas',   status:'online',  desc:'Prospecção em inglês para mercados internacionais.', skills:['Outbound EN','LinkedIn','Email'], ints:['gmail','linkedin'] },
  { id:'vera',    name:'Vera',    role:'@cmo',        emoji:'📢', squad:'criativo', status:'idle',    desc:'Impulsiona presença da marca, estratégias e campanhas criativas.', skills:['Marketing','Conteúdo','Branding'], ints:['instagram','gmail'] },
];

// Metadados de apresentação (o backend não tem fase nem status visual).
const PHASE_LABEL = { produto:'Produto', construcao:'Construção', qualidade:'Qualidade', conclave:'Conclave', meta:'Meta' };
const AGENT_PRESENTATION = {
  aios_master:   { phase:'meta',       status:'online', tag:'Orquestrador' },
  po:            { phase:'produto',    status:'online', tag:'Produto' },
  pm:            { phase:'produto',    status:'online', tag:'Projeto' },
  scrum:         { phase:'produto',    status:'idle',   tag:'Processo' },
  architect:     { phase:'construcao', status:'online', tag:'Arquitetura' },
  developer:     { phase:'construcao', status:'online', tag:'Código' },
  ux_designer:   { phase:'construcao', status:'idle',   tag:'UX' },
  devops:        { phase:'construcao', status:'idle',   tag:'Infra' },
  data_engineer: { phase:'construcao', status:'idle',   tag:'Dados' },
  qa:            { phase:'qualidade',  status:'online', tag:'Qualidade' },
  analyst:       { phase:'qualidade',  status:'idle',   tag:'Análise' },
  critico:       { phase:'conclave',   status:'online', tag:'Crítico' },
  advogado:      { phase:'conclave',   status:'idle',   tag:'Advogado' },
  sintetizador:  { phase:'conclave',   status:'online', tag:'Síntese' },
  jarvis_soul:   { phase:'meta',       status:'online', tag:'Alma' },
  squad_creator: { phase:'meta',       status:'idle',   tag:'Squads' },
  rootcause:     { phase:'meta',       status:'idle',   tag:'Diagnóstico' },
};

// Fallback local caso GET /agents falhe (mesmos dados do backend).
const MIND_AGENTS_FALLBACK = [
  { id:'aios_master',   name:'AIOS Master',           role:'Coordena a squad e decide quem executa', emoji:'🧬', color:'#00e5ff' },
  { id:'po',            name:'Product Owner',         role:'Priorização e visão de produto',         emoji:'🎯', color:'#8b5cf6' },
  { id:'pm',            name:'Project Manager',       role:'Planejamento, etapas e prazos',          emoji:'📋', color:'#3b82f6' },
  { id:'scrum',         name:'Scrum Master',          role:'Gestão de tarefas e impedimentos',       emoji:'⚙️', color:'#6366f1' },
  { id:'architect',     name:'Architect',             role:'Design de sistemas e estrutura',         emoji:'🏗️', color:'#00e5ff' },
  { id:'developer',     name:'Developer',             role:'Programação e implementação',            emoji:'💻', color:'#00e5ff' },
  { id:'ux_designer',   name:'UX Designer',           role:'Interfaces, UX e usabilidade',           emoji:'🎨', color:'#ec4899' },
  { id:'devops',        name:'DevOps',                role:'Deploy, infraestrutura e operação',      emoji:'🚀', color:'#f97316' },
  { id:'data_engineer', name:'Data Engineer',         role:'Banco de dados, pipelines e dados',      emoji:'🗄️', color:'#14b8a6' },
  { id:'qa',            name:'QA Tester',             role:'Testes, qualidade e validação',          emoji:'🔍', color:'#22c55e' },
  { id:'analyst',       name:'Analyst',               role:'Pesquisa, análise e estratégia',         emoji:'📊', color:'#a855f7' },
  { id:'critico',       name:'Conclave Crítico',      role:'Audita lógica e falhas',                 emoji:'🔴', color:'#ef4444' },
  { id:'advogado',      name:'Conclave Advogado',     role:'Ataca o plano e expõe riscos',           emoji:'⚔️', color:'#f97316' },
  { id:'sintetizador',  name:'Conclave Sintetizador', role:'Integra a melhor solução',               emoji:'✅', color:'#22c55e' },
  { id:'jarvis_soul',   name:'Jarvis Soul',           role:'Identidade, tom e personalidade',        emoji:'✨', color:'#f59e0b' },
  { id:'squad_creator', name:'Squad Creator',         role:'Monta squads dinamicamente',             emoji:'⚡', color:'#f59e0b' },
  { id:'rootcause',     name:'Rootcause',             role:'Diagnóstico de falhas e aprendizado',    emoji:'🔬', color:'#ef4444' },
];

let AGENTS = [];

function _mergePresentation(a) {
  const p = AGENT_PRESENTATION[a.id] || {};
  return {
    id: a.id, name: a.name, role: a.role,
    emoji: a.emoji || a.icon || '🤖', color: a.color,
    phase: p.phase || 'meta', status: p.status || 'idle', tag: p.tag || '',
  };
}

// Fonte única: puxa os 17 do backend (/agents). Cai no fallback local se falhar.
async function loadAgents() {
  try {
    const r = await fetch(`${API}/agents`);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const data = await r.json();
    const flat = [...(data.agents || []), ...(data.conclave || []), ...(data.meta || [])];
    if (!flat.length) throw new Error('lista vazia');
    AGENTS = flat.map(_mergePresentation);
  } catch (e) {
    console.warn('Agents → fallback local:', e);
    AGENTS = MIND_AGENTS_FALLBACK.map(_mergePresentation);
  }
  return AGENTS;
}

/* ─── AGENT GALLERY ──────────────────────────────────────── */
let _activeFilter = 'all';

function renderAgentGallery(filter) {
  filter = filter || _activeFilter;
  _activeFilter = filter;
  const grid = document.getElementById('gallery-grid');
  if (!grid) return;
  if (!AGENTS.length) { loadAgents().then(() => renderAgentGallery(filter)); return; }
  const list = filter === 'all' ? AGENTS : AGENTS.filter(a => a.phase === filter);
  if (!list.length) {
    grid.innerHTML = `<div class="gallery-empty">Nenhum agente nesta fase ainda.</div>`;
    renderActivityFeed();
    return;
  }
  grid.innerHTML = list.map(a => `
    <div class="gallery-card gc-${a.phase}" onclick="openAgentChat('${a.id}')">
      <div class="gc-header">
        <div class="gc-avatar">${a.emoji}</div>
        <div class="gc-info"><div class="gc-name">${esc(a.name)}</div><div class="gc-role">${esc(a.tag || '')}</div></div>
        <div class="gc-status-dot ${a.status}"></div>
      </div>
      <div class="gc-desc">${esc(a.role)}</div>
      <div class="gc-footer">
        <span class="gc-phase-tag og-${a.phase}">${esc(PHASE_LABEL[a.phase] || a.phase)}</span>
        <button class="gc-convocar-btn" onclick="event.stopPropagation(); convocarAgente('${a.id}')">Convocar</button>
      </div>
    </div>
  `).join('');
  renderActivityFeed();
}

async function openAgentChat(agentId) {
  const a = _agentById(agentId);
  if (!a) return;
  const task = window.prompt(`Tarefa para ${a.name}:`, '');
  if (!task || !task.trim()) return;

  switchView('chat');
  removeWelcome();
  appendMsg('user', esc(`@${a.name}: ${task}`));
  const typing = appendTyping(`${a.name} pensando...`);
  setLoading(true);

  try {
    const r = await fetch(`${API}/agents/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agentId, task }),
    });
    const data = await r.json();
    typing.remove();
    if (!r.ok || data.status !== 'ok') {
      appendMsg('error', `⚠️ ${esc(data.message || 'Falha ao executar o agente.')}`);
    } else {
      appendMsg('assistant', renderMarkdown(data.result || 'Sem resposta.'), { brain: data.brain });
    }
  } catch (e) {
    typing.remove();
    appendMsg('error', `⚠️ Erro ao chamar ${esc(a.name)}: ${esc(e.message)}`);
  } finally {
    setLoading(false);
  }
}

function convocarAgente(agentId) {
  const a = _agentById(agentId);
  if (!a) return;
  switchView('chat');
  const inp = document.getElementById('input');
  if (inp) { inp.value = `@${a.name} `; inp.focus(); }
}

document.addEventListener('click', e => {
  const btn = e.target.closest('.filter-btn');
  if (!btn) return;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderAgentGallery(btn.dataset.filter);
});

function renderActivityFeed() {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;
  const items = [
    { agent:'AIOS Master',           text:'Montou a squad para a tarefa de interface',  time:'2m atrás' },
    { agent:'Architect',             text:'Definiu a estrutura da ponte de briefing',   time:'10m atrás' },
    { agent:'Developer',             text:'Implementou a aba Mente no frontend',        time:'18m atrás' },
    { agent:'QA Tester',             text:'Validou a galeria: 17 agentes, zero erro',   time:'25m atrás' },
    { agent:'Conclave Sintetizador', text:'Integrou a decisão sobre o roster da mente', time:'40m atrás' },
  ];
  feed.innerHTML = items.map(i => `
    <div class="activity-item">
      <div class="ai-agent">${i.agent}</div>
      <div class="ai-text">${i.text}</div>
      <div class="ai-time">${i.time}</div>
    </div>
  `).join('');
}

/* ─── WORKFLOW CANVAS — quadro de orquestramento real (backlog do Codex) ─── */
let MISSIONS = [];
let WF_NODES = [];
let WF_EDGES = [];

async function fetchMissionNodes(missionId) {
  try {
    const r = await fetch(`${API}/missions/${missionId}/nodes`);
    if (!r.ok) return [];
    const data = await r.json();
    const nodes = data.nodes || [];
    return nodes.map((n, i) => ({
      ...n,
      type: i === 0 ? 'orchestrator' : (n.status === 'done' ? 'review' : 'copy'),
      x: 60 + i * 190,
      y: 150 + ((i % 3) - 1) * 80,
    }));
  } catch { return []; }
}

async function fetchMissions() {
  try {
    const r = await fetch(`${API}/missions`);
    if (!r.ok) return;
    const data = await r.json();
    if (data.missions) MISSIONS = data.missions;
  } catch { /* backend offline — sem missões pra mostrar */ }
}

let _selectedMissionId = null;

// ─── Quadro: board estilo Plane sobre as missões reais (/missions) ──────
// Cada node de missão vira um card; colunas = status do node (pending/running/done).
// Arrastar entre Pendente/Concluído grava de volta no checkbox real do backlog
// (POST /missions/{id}/nodes/{id}/done). "Em andamento" é sempre calculado —
// não tem checkbox pra editar, então não aceita drop nem é arrastável.
// Quadro agora lê do SQLite (GET /tasks). 4 colunas; cada status mapeia numa coluna.
const QUADRO_COLUMNS = [
  { key:'pending',   label:'Pendente',            icon:'📥', status:['pending'],               setStatus:'pending' },
  { key:'running',   label:'Em andamento',        icon:'⚙️', status:['running','in_progress'], setStatus:'in_progress' },
  { key:'approved',  label:'Aprovado/Destravado', icon:'🔓', status:['done','gate_approved'],  setStatus:'gate_approved' },
  { key:'completed', label:'Concluído/Morto',     icon:'🪦', status:['completed','killed'],     setStatus:'completed' },
];
let _quadroFilter = 'all';      // 'all' ou um workflow (mission slug)

function setQuadroFilter(id) {
  _quadroFilter = id;
  renderQuadro();
}

function _qColForStatus(status) {
  const s = status || 'pending';
  const col = QUADRO_COLUMNS.find(c => c.status.includes(s));
  return col ? col.key : 'pending';
}

async function renderQuadro() {
  const board = document.getElementById('quadro-board');
  if (!board) return;
  board.innerHTML = '<div class="quadro-empty">Carregando tarefas…</div>';

  // FONTE PRINCIPAL: SQLite via GET /tasks (com fallback Markdown no backend).
  let tasks = [];
  try {
    const qs = _quadroFilter !== 'all' ? `?workflow=${encodeURIComponent(_quadroFilter)}` : '';
    const r = await fetch(`${API}/tasks${qs}`, { signal: AbortSignal.timeout(6000) });
    tasks = (await r.json()).tasks || [];
  } catch {
    board.innerHTML = '<div class="quadro-empty">Não consegui carregar as tarefas (backend offline?).</div>';
    return;
  }

  // Filtros por workflow (a partir dos próprios dados — sem depender de /missions).
  const filters = document.getElementById('quadro-filters');
  if (filters) {
    // pra montar as chips, busca a lista completa (sem filtro) uma vez
    let allWf = [];
    try {
      const ra = await fetch(`${API}/tasks`, { signal: AbortSignal.timeout(6000) });
      allWf = [...new Set(((await ra.json()).tasks || []).map(t => t.workflow).filter(Boolean))];
    } catch { allWf = []; }
    filters.innerHTML =
      `<button class="qfilter ${_quadroFilter==='all'?'active':''}" onclick="setQuadroFilter('all')">Todas</button>` +
      allWf.map(w => `<button class="qfilter ${_quadroFilter===w?'active':''}" onclick="setQuadroFilter('${esc(w)}')" title="${esc(w)}">${esc(w.length>22?w.slice(0,22)+'…':w)}</button>`).join('');
  }

  if (!tasks.length) {
    board.innerHTML = '<div class="quadro-empty">Nenhuma tarefa — o SQLite está vazio e o backlog do Codex também.</div>';
    return;
  }

  board.innerHTML = QUADRO_COLUMNS.map(col => {
    const colCards = tasks.filter(t => _qColForStatus(t.status) === col.key);
    return `
      <div class="quadro-col q-col-${col.key}" data-col="${col.key}" data-set-status="${col.setStatus}"
           ondragover="quadroDragOver(event)" ondragleave="quadroDragLeave(event)" ondrop="quadroDrop(event)">
        <div class="qcol-head">
          <span class="qcol-title">${col.icon} ${col.label}</span>
          <span class="qcol-count">${colCards.length}</span>
        </div>
        <div class="qcol-cards">
          ${colCards.map(_quadroCard).join('') || '<div class="qcol-empty">—</div>'}
        </div>
      </div>
    `;
  }).join('');
}

function _quadroCard(t) {
  const ext = esc(t.ext_id || '');
  const hostId = `qj-${(t.ext_id || '').replace(/[^a-zA-Z0-9_-]/g, '_')}`;
  const encerrada = t.status === 'completed' || t.status === 'killed';
  const digest = t.has_digest ? '<span class="qcard-digest" title="tem digest">📄 digest</span>' : '';
  const journeyBtn = `<button class="qcard-jbtn" onclick="viewJourney('${ext}', '${hostId}')">Ver jornada</button>`;
  // encerradas não são arrastáveis (não dá pra reabrir pelo Quadro)
  const drag = encerrada ? '' : `draggable="true" ondragstart="quadroDragStart(event)" ondragend="quadroDragEnd(event)"`;
  return `<div class="qcard q-${_qColForStatus(t.status)}" title="${esc(t.title || '')}" data-ext-id="${ext}" ${drag}>
    <div class="qcard-text">${esc(t.title || '')}</div>
    <div class="qcard-foot">
      <span class="qcard-tag">${esc(t.agent || t.workflow || '—')}</span>
      <span class="qcard-st">${esc(t.status || '')}</span>
    </div>
    <div class="qcard-actions">${journeyBtn}${digest}</div>
    <div class="ap-journey" id="${hostId}" data-open="0"></div>
  </div>`;
}

// ─── Drag-and-drop do Quadro: mover card grava status no SQLite ───────────
let _quadroDrag = null; // { extId }

function quadroDragStart(ev) {
  const el = ev.currentTarget;
  _quadroDrag = { extId: el.dataset.extId };
  el.classList.add('dragging');
  ev.dataTransfer.effectAllowed = 'move';
}

function quadroDragEnd(ev) {
  ev.currentTarget.classList.remove('dragging');
}

function quadroDragOver(ev) {
  ev.preventDefault();
  ev.currentTarget.classList.add('drag-over');
}

function quadroDragLeave(ev) {
  ev.currentTarget.classList.remove('drag-over');
}

async function quadroDrop(ev) {
  ev.preventDefault();
  const col = ev.currentTarget;
  col.classList.remove('drag-over');
  const drag = _quadroDrag;
  _quadroDrag = null;
  if (!drag || !drag.extId) return;
  const setStatus = col.dataset.setStatus;   // status-alvo da coluna
  if (!setStatus) return;
  try {
    const r = await fetch(`${API}/tasks/${encodeURIComponent(drag.extId)}/status`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: setStatus, note: 'movido no Quadro' }),
      signal: AbortSignal.timeout(8000),
    });
    const d = await r.json().catch(() => ({}));
    if (r.ok && d.ok) {
      if (d.unchanged) { /* sem mudança */ }
      else if (setStatus === 'completed') showToast('Entidade concluída. Digest gerado.', 'success');
      else showToast(`Movido para "${setStatus}".`, 'success');
      refreshStats();
    } else {
      showToast(d.error || 'Não consegui mover essa tarefa.', 'warning');
    }
  } catch {
    showToast('Backend offline — não consegui mover.', 'error');
  }
  renderQuadro();
}

function renderMissionsList() {
  const list = document.getElementById('missions-list');
  if (!list) return;
  list.innerHTML = MISSIONS.length ? MISSIONS.map(m => `
    <div class="mission-item ${m.id === _selectedMissionId ? 'active' : ''}" data-mid="${m.id}" onclick="selectMission('${m.id}')">
      <div class="mi-name">${m.name}</div>
      <div class="mi-progress-row">
        <div class="mi-bar"><div class="mi-bar-fill" style="width:${m.pct}%"></div></div>
        <span class="mi-pct">${m.pct}%</span>
      </div>
      <div class="mi-meta">${m.tasks_done}/${m.tasks_total} tarefas${m.last_activity ? ' · ' + m.last_activity : ''}</div>
    </div>
  `).join('') : `<div class="mi-empty">Nenhuma missão no backlog do Codex.</div>`;
}

async function renderCanvasForMission(mission) {
  const titleEl = document.getElementById('wf-canvas-title');
  if (titleEl) titleEl.textContent = mission ? mission.name : 'Sem missão ativa';
  const statusEl = document.querySelector('.wf-canvas-status');
  if (statusEl) statusEl.textContent = mission ? (mission.status === 'concluida' ? 'Concluída' : mission.status === 'running' ? 'Em execução' : 'Pendente') : '—';

  WF_NODES = mission ? await fetchMissionNodes(mission.id) : [];
  WF_EDGES = WF_NODES.slice(0, -1).map((n, i) => [n.id, WF_NODES[i + 1].id]);

  const canvas = document.getElementById('workflow-canvas');
  if (!canvas) return;
  canvas.querySelectorAll('.wf-node').forEach(n => n.remove());
  WF_NODES.forEach(node => {
    const div = document.createElement('div');
    div.className = `wf-node type-${node.type} status-${node.status}`;
    div.id = 'wfn-' + node.id;
    div.style.cssText = `left:${node.x}px;top:${node.y}px`;
    div.innerHTML = `<div class="wf-node-label">${node.label}</div><div class="wf-node-type">${node.type}</div><div class="wf-node-bar"><div class="wf-node-bar-fill" style="width:${node.pct}%"></div></div>`;
    div.addEventListener('click', () => showTaskDetail(node));
    canvas.appendChild(div);
  });
  requestAnimationFrame(() => drawWfEdges());
}

async function initWorkflowCanvas() {
  await fetchMissions();
  if (!_selectedMissionId || !MISSIONS.some(m => m.id === _selectedMissionId)) {
    const active = MISSIONS.find(m => m.active) || MISSIONS[0];
    _selectedMissionId = active ? active.id : null;
  }
  renderMissionsList();
  await renderCanvasForMission(MISSIONS.find(m => m.id === _selectedMissionId));
}

function selectMission(mid) {
  _selectedMissionId = mid;
  renderMissionsList();
  renderCanvasForMission(MISSIONS.find(m => m.id === mid));
}

function drawWfEdges() {
  const svg = document.getElementById('wf-connections');
  const canvas = document.getElementById('workflow-canvas');
  if (!svg || !canvas) return;
  svg.innerHTML = '';
  const cr = canvas.getBoundingClientRect();
  WF_EDGES.forEach(([fId, tId]) => {
    const fEl = document.getElementById('wfn-' + fId);
    const tEl = document.getElementById('wfn-' + tId);
    if (!fEl || !tEl) return;
    const fr = fEl.getBoundingClientRect();
    const tr = tEl.getBoundingClientRect();
    const x1 = fr.right - cr.left, y1 = (fr.top+fr.bottom)/2 - cr.top;
    const x2 = tr.left  - cr.left, y2 = (tr.top+tr.bottom)/2  - cr.top;
    const mx = (x1+x2)/2;
    const path = document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d', `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`);
    path.setAttribute('stroke', 'rgba(124,58,237,0.4)');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-dasharray', '5 3');
    svg.appendChild(path);
  });
}

function showTaskDetail(node) {
  const panel = document.getElementById('tdp-content');
  if (!panel) return;
  const subtaskMap = {
    orchestrator: ['Análise de contexto','Delegação de tasks','Monitoramento'],
    copy:         ['Pesquisa de referências','Rascunho inicial','Revisão de tom'],
    review:       ['Checklist de qualidade','Aprovação humana','Feedback loop'],
    publish:      ['Agendamento','Publicação final','Report de alcance'],
    research:     ['Coleta de dados','Análise','Síntese'],
  };
  const tasks = subtaskMap[node.type] || [];
  const done = Math.floor((node.pct/100)*tasks.length);
  panel.innerHTML = `
    <div class="tdp-task-name">${node.label}</div>
    <div class="tdp-progress-big">${node.pct}%</div>
    <div class="tdp-section-label">Subtarefas</div>
    <div class="tdp-subtasks">${tasks.map((t,i)=>`<div class="tdp-subtask ${i<done?'done':''}"><span>${i<done?'✅':'○'}</span><span>${t}</span></div>`).join('')}</div>
    <div class="tdp-section-label" style="margin-top:12px">Contexto</div>
    <div class="tdp-context">Agente: <strong>${node.label}</strong><br>Tipo: ${node.type}<br>Status: ${node.status}</div>
  `;
}

/* ─── TRAINING VIEW ─────────────────────────────────────── */
const _trainingQueue = [];

document.addEventListener('click', async e => {
  if (e.target.id !== 'train-add-btn') return;
  const urlInp = document.getElementById('train-url');
  const agSel  = document.getElementById('train-agent-sel');
  const url    = (urlInp?.value || '').trim();
  if (!url) return;
  const agent = agSel?.value || 'khan';

  const idx = _trainingQueue.length;
  _trainingQueue.push({ url, title: 'Extraindo transcrição...', agent, progress: 5, status: 'studying' });
  if (urlInp) urlInp.value = '';
  renderTrainingQueue();

  const fakeId = setInterval(() => {
    const item = _trainingQueue[idx];
    if (!item || item.progress >= 85) { clearInterval(fakeId); return; }
    item.progress = Math.min(85, item.progress + Math.random() * 5 + 2);
    const bar = document.getElementById('ti-bar-' + idx);
    if (bar) bar.style.width = item.progress + '%';
  }, 400);

  try {
    const res  = await fetch('/train/youtube', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, agent }),
    });
    clearInterval(fakeId);
    const data = await res.json();
    const item = _trainingQueue[idx];
    if (data.error) {
      item.title = '❌ ' + data.error;
      item.status = 'error';
      item.progress = 0;
    } else {
      item.title    = data.title || item.title;
      item.status   = 'done';
      item.progress = 100;
      item.chars    = data.chars;
      showToast(`✅ ${item.agent} absorveu: ${item.title}`, 'success');
    }
    renderTrainingQueue();
  } catch (err) {
    clearInterval(fakeId);
    const item = _trainingQueue[idx];
    if (item) { item.title = '❌ Erro de conexão'; item.status = 'error'; item.progress = 0; }
    renderTrainingQueue();
  }
});

function renderTrainingQueue() {
  const el = document.getElementById('train-queue');
  if (!el) return;
  if (!_trainingQueue.length) {
    el.innerHTML='<div class="train-empty">Nenhum vídeo em treinamento ainda.</div>';
    renderTrainStats();
    return;
  }
  el.innerHTML = _trainingQueue.map((item,i) => `
    <div class="train-item">
      <div class="ti-icon">🎓</div>
      <div class="ti-info">
        <div class="ti-title">${item.title}${item.chars ? ' <small style="color:var(--text-dim);font-weight:400">· '+Math.round(item.chars/1000)+'k chars</small>' : ''}</div>
        <div class="ti-agent">Agente: ${item.agent}</div>
        <div class="ti-progress"><div class="ti-progress-fill" id="ti-bar-${i}" style="width:${item.progress}%"></div></div>
      </div>
      <div class="ti-status ${item.status}" id="ti-st-${i}">${item.status==='done'?'✅ Absorvido':item.status==='error'?'Erro':'📚 Estudando'}</div>
    </div>
  `).join('');
  renderTrainStats();
}

function renderTrainStats() {
  const doneItems = _trainingQueue.filter(item => item.status === 'done');
  const totalVideos = doneItems.length;
  const totalChars = doneItems.reduce((sum, item) => sum + (item.chars || 0), 0);
  const trainedAgents = new Set(doneItems.map(item => item.agent).filter(Boolean)).size;

  const totalEl = document.getElementById('ts-total');
  const charsEl = document.getElementById('ts-chars');
  const agentsEl = document.getElementById('ts-agents');

  if (totalEl) totalEl.textContent = totalVideos;
  if (charsEl) charsEl.textContent = Math.round(totalChars / 1000) + 'k';
  if (agentsEl) agentsEl.textContent = trainedAgents;
}

/* ─── INTEGRATIONS ───────────────────────────────────────── */
const INTEGRATIONS_DATA = [
  { id:'gmail',     name:'Gmail',         icon:'📧', status:'disconnected', desc:'Envio e recebimento de emails' },
  { id:'whatsapp',  name:'WhatsApp',      icon:'💬', status:'disconnected', desc:'Mensagens via WhatsApp Business' },
  { id:'slack',     name:'Slack',         icon:'💼', status:'disconnected', desc:'Notificações e alertas de equipe' },
  { id:'notion',    name:'Notion',        icon:'📓', status:'disconnected', desc:'Documentação e conhecimento' },
  { id:'sheets',    name:'Google Sheets', icon:'📊', status:'disconnected', desc:'Planilhas e relatórios de dados' },
  { id:'instagram', name:'Instagram',     icon:'📸', status:'disconnected', desc:'Gestão de conteúdo e DMs' },
  { id:'linkedin',  name:'LinkedIn',      icon:'🔗', status:'disconnected', desc:'Prospecção B2B e conexões' },
  { id:'evolution', name:'Evolution API', icon:'⚡', status:'disconnected', desc:'WhatsApp automatizado via API' },
];

/* ─── TOAST SYSTEM ─────────────────────────────────────────── */
function showToast(msg, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  requestAnimationFrame(() => { requestAnimationFrame(() => t.classList.add('show')); });
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 300);
  }, duration);
}

/* ─── KEYBOARD SHORTCUTS ────────────────────────────────────── */
document.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement !== inputEl && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    switchView('chat');
    inputEl && inputEl.focus();
  }
  if (e.key === 'Escape' && document.activeElement === inputEl) {
    inputEl.blur();
  }
});

function renderIntegrations() {
  const grid = document.getElementById('integrations-grid');
  if (!grid) return;
  grid.innerHTML = INTEGRATIONS_DATA.map(i => `
    <div class="integration-card ${i.status}" onclick="toggleIntegration('${i.id}')">
      <div class="ic-icon">${i.icon}</div>
      <div class="ic-name">${i.name}</div>
      <div class="ic-desc">${i.desc}</div>
      <span class="ic-status ${i.status}">${i.status==='connected'?'✓ Conectado':'Conectar'}</span>
    </div>
  `).join('');
}

function toggleIntegration(id) {
  const item = INTEGRATIONS_DATA.find(i => i.id===id);
  if (!item) return;
  item.status = item.status==='connected' ? 'disconnected' : 'connected';
  renderIntegrations();
}

/* ═══════════════════════════════════════════════════════════
   SALA DOS AGENTES — animated room with character sprites
   ═══════════════════════════════════════════════════════════ */
const ROOM_AGENTS = [
  { id:'orion',   name:'Orion',   emoji:'🧬', hx:50, hy:30 },
  { id:'titan',   name:'Titan',   emoji:'👑', hx:22, hy:48 },
  { id:'khan',    name:'Khan',    emoji:'📞', hx:38, hy:66 },
  { id:'phantom', name:'Phantom', emoji:'🎯', hx:62, hy:66 },
  { id:'blade',   name:'Blade',   emoji:'⚔️', hx:78, hy:48 },
  { id:'vera',    name:'Vera',    emoji:'📢', hx:15, hy:74 },
  { id:'dara',    name:'Dara',    emoji:'📊', hx:85, hy:74 },
  { id:'recap',   name:'Recap',   emoji:'🔄', hx:50, hy:82 },
];
const ROOM_TASKS = [
  'analisando lead novo', 'escrevendo follow-up', 'revisando copy', 'fechando contrato',
  'pesquisando concorrente', 'gerando relatório', 'qualificando prospect', 'criando reel',
  'atualizando CRM', 'preparando proposta', 'estudando vídeo de vendas', 'agendando reunião',
];
let _roomTimers = [];
let _roomInited = false;

function initAgentRoom() {
  const floor = document.getElementById('room-floor');
  if (!floor) return;
  if (_roomInited) { _roomTick(); return; }
  _roomInited = true;

  // build desks + agents
  ROOM_AGENTS.forEach(a => {
    const desk = document.createElement('div');
    desk.className = 'room-desk';
    desk.style.left = a.hx + '%';
    desk.style.top  = a.hy + '%';
    floor.appendChild(desk);

    const el = document.createElement('div');
    el.className = 'room-agent';
    el.id = 'ra-' + a.id;
    el.style.left = a.hx + '%';
    el.style.top  = a.hy + '%';
    el.innerHTML = `
      <span class="room-agent-status-dot idle"></span>
      <div class="room-bubble" id="rb-${a.id}"></div>
      <div class="room-agent-body">${a.emoji}</div>
      <div class="room-agent-name">${a.name}</div>`;
    el.onclick = () => roomPoke(a);
    floor.appendChild(el);
  });

  _roomTick();
  _roomTimers.push(setInterval(_roomTick, 3200));
}

function stopAgentRoom() {
  _roomTimers.forEach(clearInterval);
  _roomTimers = [];
}

function _roomTick() {
  // randomly assign work to ~half the agents each tick
  let working = 0, idle = 0;
  ROOM_AGENTS.forEach(a => {
    const el = document.getElementById('ra-' + a.id);
    if (!el) return;
    const dot = el.querySelector('.room-agent-status-dot');
    const roll = Math.random();
    if (roll < 0.55) {
      // working
      el.classList.add('working');
      dot.className = 'room-agent-status-dot working';
      working++;
      if (Math.random() < 0.5) roomBubble(a, ROOM_TASKS[Math.floor(Math.random()*ROOM_TASKS.length)]);
    } else if (roll < 0.9) {
      // idle — wander a bit
      el.classList.remove('working');
      dot.className = 'room-agent-status-dot idle';
      idle++;
      if (Math.random() < 0.4) {
        el.style.left = Math.max(8, Math.min(92, a.hx + (Math.random()*16 - 8))) + '%';
        el.style.top  = Math.max(20, Math.min(86, a.hy + (Math.random()*12 - 6))) + '%';
      } else {
        el.style.left = a.hx + '%'; el.style.top = a.hy + '%';
      }
    } else {
      el.classList.remove('working');
      el.classList.add('offline');
      dot.className = 'room-agent-status-dot offline';
    }
    if (roll >= 0.55) el.classList.remove('offline');
  });
  const w = document.getElementById('rstat-working'); if (w) w.textContent = working;
  const i = document.getElementById('rstat-idle');    if (i) i.textContent = idle;
  const t = document.getElementById('rstat-tasks');   if (t) t.textContent = working;
}

function roomBubble(a, text) {
  const b = document.getElementById('rb-' + a.id);
  if (!b) return;
  b.textContent = text;
  b.classList.add('show');
  setTimeout(() => b.classList.remove('show'), 2600);
  roomLog(a.name, text);
}

function roomPoke(a) {
  roomBubble(a, 'pronto pra trabalhar, senhor!');
  const el = document.getElementById('ra-' + a.id);
  if (el) { el.classList.add('working'); el.querySelector('.room-agent-status-dot').className = 'room-agent-status-dot working'; }
}

function roomLog(agent, text) {
  const log = document.getElementById('room-log');
  if (!log) return;
  const now = new Date().toLocaleTimeString('pt-BR', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  const line = document.createElement('div');
  line.className = 'rl-line';
  line.innerHTML = `<span class="rl-time">${now}</span><span class="rl-agent">${agent}</span> · ${text}`;
  log.insertBefore(line, log.firstChild);
  while (log.children.length > 30) log.removeChild(log.lastChild);
}

/* ═══════════════════════════════════════════════════════════
   PROJETOS — Javis as master orchestrator of all projects
   ═══════════════════════════════════════════════════════════ */
const PROJECTS_DATA = [
  {
    id:'vempassear', icon:'🌊', name:'Vem Passear Jampa', tag:'Turismo · João Pessoa',
    desc:'Squad de turismo: vendas de passeios, conteúdo, leads e atendimento no WhatsApp.',
    agents:10, status:'online', statusLabel:'Ativo', grad:'linear-gradient(90deg,#0ea5e9,#06b6d4)',
    open:'/vempassear', squadEndpoint:'/jampa/agents',
  },
  {
    id:'cerebro-jampa', icon:'🧠', name:'Cérebro Jampa', tag:'Orquestração comercial',
    desc:'Squad mestre Jampa Jarvis: Orion orquestra Hunter, Atlas, LNS, Nero, Nova e mais.',
    agents:10, status:'online', statusLabel:'Ativo', grad:'linear-gradient(90deg,#7c3aed,#a855f7)',
    open:'/vempassear', squadEndpoint:'/jampa/agents',
    registrySlug:'cerebro-jampa', external:true,
  },
  {
    id:'javis-core', icon:'⚡', name:'Javis Core', tag:'Orquestrador mestre',
    desc:'O cérebro central. Coordena todos os projetos, voz, código (Claude + Codex) e memória.',
    agents:12, status:'online', statusLabel:'Você está aqui', grad:'linear-gradient(90deg,#f59e0b,#ef4444)',
    open:'/', squadEndpoint:'/agents',
  },
  {
    id:'futuro', icon:'➕', name:'Novo Projeto', tag:'Slot livre',
    desc:'Plugue um novo projeto aqui. Javis cria o squad e orquestra automaticamente.',
    agents:0, status:'planned', statusLabel:'Planejado', grad:'linear-gradient(90deg,#475569,#334155)',
    open:null, squadEndpoint:null,
  },
];

let _registryCache = null;

async function _fetchRegistry() {
  if (_registryCache) return _registryCache;
  try {
    const r = await fetch('/projects/registry');
    const j = await r.json();
    _registryCache = {};
    (j.projects || []).forEach(p => { _registryCache[p.slug] = p; });
  } catch (e) {
    _registryCache = {};
  }
  return _registryCache;
}

function renderProjects() {
  const grid = document.getElementById('projects-grid');
  if (!grid) return;
  const totalTasks = PROJECTS_DATA.reduce((sum, p) => sum + (typeof p.tasks === 'number' ? p.tasks : 3), 0);
  const analyticsHtml = `
    <div class="analytics-bar" id="analytics-bar">
      <div class="ab-card">
        <div class="ab-val" id="ab-total-tasks">${totalTasks}</div>
        <div class="ab-lbl">tarefas ativas</div>
      </div>
      <div class="ab-card">
        <div class="ab-val online" id="ab-agents-online">5</div>
        <div class="ab-lbl">agentes online</div>
      </div>
      <div class="ab-card">
        <div class="ab-val" id="ab-completions">14</div>
        <div class="ab-lbl">completadas hoje</div>
      </div>
      <div class="ab-card">
        <div class="ab-val" id="ab-efficiency">87%</div>
        <div class="ab-lbl">eficiência</div>
      </div>
      <div class="ab-chart-wrap">
        <canvas id="ab-chart" width="200" height="60"></canvas>
        <div class="ab-chart-lbl">Atividade 7 dias</div>
      </div>
    </div>
  `;
  const existingAnalytics = document.getElementById('analytics-bar');
  if (existingAnalytics) {
    existingAnalytics.outerHTML = analyticsHtml;
  } else {
    grid.insertAdjacentHTML('beforebegin', analyticsHtml);
  }
  grid.innerHTML = PROJECTS_DATA.map(p => `
    <div class="project-card" style="--accent-grad:${p.grad}" id="pc-${p.id}">
      <div class="pc-head">
        <div class="pc-icon">${p.icon}</div>
        <div><div class="pc-name">${p.name}</div><div class="pc-tag">${p.tag}</div></div>
        ${p.external ? '<span class="pc-ext-badge" title="Projeto externo conectado por registry — Javis não absorve, só orquestra">🔗 externo</span>' : ''}
      </div>
      <div class="pc-desc">${p.desc}</div>
      <div class="pc-meta">
        <div class="pc-stat"><b>${p.agents}</b>agentes</div>
        <div class="pc-stat"><span class="pc-status ${p.status}">${p.status==='online'?'●':'○'} ${p.statusLabel}</span></div>
      </div>
      <div class="pc-extra" id="pc-extra-${p.id}"></div>
      <div class="pc-actions">
        <button class="pc-btn" ${p.open?`onclick="window.location.href='${p.open}'"`:'disabled'}>${p.open?'Abrir':'Em breve'}</button>
        <button class="pc-btn" ${p.squadEndpoint?`onclick="orquestrarProjeto('${p.id}')"`:'disabled'}>Orquestrar</button>
      </div>
    </div>
  `).join('');
  _drawAnalyticsChart();
  _hydrateRegistryCards();
}

async function _hydrateRegistryCards() {
  const reg = await _fetchRegistry();
  PROJECTS_DATA.filter(p => p.registrySlug).forEach(p => {
    const data = reg[p.registrySlug];
    const slot = document.getElementById(`pc-extra-${p.id}`);
    if (!slot) return;
    if (!data || data.status !== 'online') {
      slot.innerHTML = `<div class="pc-extra-row pc-extra-warn">⚠ projeto externo offline (caminho não encontrado)</div>`;
      return;
    }
    slot.innerHTML = `
      <div class="pc-extra-row"><span>fase</span><b>${data.fase_atual} · ${data.descricao_fase}</b></div>
      <div class="pc-extra-row"><span>skills ativas</span><b>${data.skills_ativas}/${data.skills_total}</b></div>
      <div class="pc-extra-row"><span>fonte-da-verdade</span><b>${data.fonte_da_verdade_atualizada_em || '—'}</b></div>
    `;
  });
}

function _drawAnalyticsChart() {
  const canvas = document.getElementById('ab-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const points = Array.from({ length: 7 }, () => Math.floor(Math.random() * 10) + 3);
  const min = Math.min(...points);
  const max = Math.max(...points);
  const pad = 5;
  const range = max - min || 1;
  const step = (canvas.width - pad * 2) / (points.length - 1);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath();
  points.forEach((value, i) => {
    const x = pad + i * step;
    const y = canvas.height - pad - ((value - min) / range) * (canvas.height - pad * 2);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = '#7c3aed';
  ctx.lineWidth = 1.5;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();
}

function orquestrarProjeto(id) {
  const p = PROJECTS_DATA.find(x => x.id===id);
  if (!p) return;
  switchView('chat');
  const inp = document.getElementById('input');
  if (inp) { inp.value = `Orquestrar projeto ${p.name}: `; inp.focus(); }
}
