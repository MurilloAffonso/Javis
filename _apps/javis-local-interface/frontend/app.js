// Javis v2 — frontend app
// Connects to FastAPI server at localhost:8000

const API = "http://localhost:8000";

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
const svcOllama    = document.getElementById("svc-ollama");
const svcWebui     = document.getElementById("svc-webui");

// Brain buttons
const brains = {
  main:     document.getElementById("brain-main"),
  conclave: document.getElementById("brain-conclave"),
  memory:   document.getElementById("brain-memory"),
};

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
setInterval(checkStatus, 30000);

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

// Quick action buttons
document.querySelectorAll(".qbtn:not(#btn-debate)").forEach(btn => {
  btn.addEventListener("click", () => {
    const cmd = btn.dataset.cmd;
    if (cmd && !sendBtn.disabled) sendMessage(cmd);
  });
});

// ─── Send message ─────────────────────────────────────────
async function sendMessage(text) {
  removeWelcome();
  appendMsg("user", esc(text));
  setLoading(true);
  clearAgentActivity();

  const typing = appendTyping();

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message:      text,
        use_conclave: useConclave.checked,
        model:        modelSel.value,
      }),
    });

    typing.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendMsg("error", `⚠️ Erro ${res.status}: ${esc(err.error || res.statusText)}`);
      return;
    }

    const data = await res.json();
    handleResponse(data);

  } catch (err) {
    typing.remove();
    if (err.name === "TypeError") {
      appendMsg("error", "⚠️ Servidor offline. Inicie com: <code>python backend/server.py</code>");
    } else {
      appendMsg("error", `⚠️ ${esc(err.message)}`);
    }
  } finally {
    setLoading(false);
  }
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
}

function setBrain(name) {
  const map = { squad: "conclave" };
  const key = map[name] || name;
  Object.entries(brains).forEach(([k, el]) => {
    el.classList.toggle("active", k === key);
  });
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
  setSvc(svcOllama, "checking");
  setSvc(svcWebui,  "checking");
  try {
    const res  = await fetch(`${API}/status`, { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    const svcs = data.services || {};

    setSvc(svcOllama, svcs["Ollama"]?.status     === "online" ? "online" : "offline");
    setSvc(svcWebui,  svcs["Open WebUI"]?.status === "online" ? "online" : "offline");
  } catch {
    setSvc(svcOllama, "offline");
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
