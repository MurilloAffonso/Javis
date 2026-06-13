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
setInterval(checkStatus, 30000);
setInterval(_tickSession, 1000);
setInterval(pollReminders, 15000);

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

  const typing = appendTyping("processando voz...");

  try {
    const res = await fetch(`${API}/voice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transcript:   text,
        model:        modelSel.value,
        use_conclave: useConclave.checked,
        tts:          useTts?.checked ?? true,
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

    if (data.tts && (useTts?.checked ?? true)) {
      speak(data.response || "");
    }

  } catch (err) {
    typing.remove();
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
