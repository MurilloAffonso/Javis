// Chat — conversa com os agentes (texto, upload, voz). Extraído de app.js em
// 2026-07-02. MESMO comportamento; agora módulo ES.
import { h, $, state, BACKEND, tryJson, _esc, activeAgent, pct } from "../../app.js";
import { initVoiceStage } from "../voice.js";

const CMD_SUGGEST = [
  { name: "⚡ nova-tarefa", desc: "Orquestrar uma demanda do zero" },
  { name: "📊 analisar", desc: "Analisar dados e gerar insights" },
  { name: "💡 gerar-ideias", desc: "Sugestões baseadas em contexto" },
  { name: "✍️ criar-conteúdo", desc: "Produzir copy / post / roteiro" },
];
function agentSkills(a) {
  let list = state.skills.filter((s) => s.agente && a.id && a.id.includes(s.agente));
  if (list.length < 3) list = state.skills.slice(0, 5);
  return list.slice(0, 5);
}

function viewChat(body) {
  const a = activeAgent();
  state.activeAgentId = a.id;
  const hist = state.chats[a.id] || [];

  // ===== STAGE HERO COM ORB GIGANTE CENTRAL =====
  body.appendChild(h(`
    <div class="stage stage-hero${hist.length ? " compact" : ""}" id="orb-host">
      <div class="brand-bar">JAVES</div>
      <div class="brand-sub">ORQUESTRADOR · VOZ · IA MULTIAGENTE</div>
      <div class="orb-stage" id="orb-stage"><canvas id="orb-canvas"></canvas></div>
      <div class="orb-state-lbl" id="neural-state">ONLINE</div>
      <div class="orb-pulse-lbl" id="neural-pulse-lbl">aguardando comando</div>
      <div class="voice-status" id="voice-status">
        <div class="voice-status-dot"></div>
        <span>OUVINDO</span>
        <span class="voice-interim" id="voice-interim"></span>
      </div>
      <div class="orb-controls">
        <button type="button" class="mic-btn" id="mic-btn" title="Gravar voz (Whisper)">🎤</button>
        <button type="button" class="voice-auto-btn" id="wake-btn" title='Wake word: diga "Javis"'>🎙️</button>
        <button type="button" class="voice-auto-btn" id="voice-auto-btn" title="Voz sempre ativa">👂</button>
        <label class="tts-chk" title="Falar resposta (TTS)"><input type="checkbox" id="use-tts" ${state.useTts ? "checked" : ""} /><span>🔊</span></label>
        <label class="conclave-chk" title="Ativar Conclave"><input type="checkbox" id="use-conclave" ${state.useConclave ? "checked" : ""} /><span>⚔️</span></label>
        <button type="button" class="brain-toggle" id="brain-toggle" title="Trocar motor: Claude ↔ Codex">🧠</button>
      </div>
    </div>`));

  // Brain toggle init
  (async () => {
    try {
      const b = await tryJson(BACKEND + "brain/active");
      state.lastBrain = b.engine || "claude";
      const btn = document.getElementById("brain-toggle");
      if (btn) { btn.textContent = state.lastBrain === "claude" ? "🧠 Claude" : "🤖 Codex"; btn.className = "brain-toggle" + (state.lastBrain === "codex" ? " codex-active" : ""); }
    } catch(_){}
  })();
  document.getElementById("brain-toggle").onclick = async () => {
    const next = (state.lastBrain === "claude") ? "codex" : "claude";
    try {
      await tryJson(BACKEND + "brain/active", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({engine: next}) });
      state.lastBrain = next;
      const btn = document.getElementById("brain-toggle");
      btn.textContent = next === "claude" ? "🧠 Claude" : "🤖 Codex";
      btn.className = "brain-toggle" + (next === "codex" ? " codex-active" : "");
    } catch(_){}
  };

  // Inicializa o motor de voz após o DOM estar pronto
  setTimeout(() => initVoiceStage(a), 0);

  // ===== CHAT (sempre presente, mas compacto) =====
  const chatBlock = h(`<div class="chat-block"></div>`);
  chatBlock.appendChild(h(`
    <div class="agent-hero compact">
      <div class="ah-avatar">${(a.nome || "?")[0]}</div>
      <div><div class="ah-name">${a.nome || "Agente"} <span class="chip accent">${a.tipo || ""}</span></div>
      <div class="ah-role">${a.descricao || ""}</div></div>
    </div>`));

  const scroll = h(`<div class="chat-scroll" id="chat-scroll"></div>`);
  hist.forEach((m) => scroll.appendChild(h(`<div class="chat-msg ${m.role}">${_esc(m.text)}</div>`)));
  chatBlock.appendChild(scroll);
  // Volta pro final do histórico ao retornar pra aba chat
  setTimeout(() => { scroll.scrollTop = scroll.scrollHeight; }, 0);

  const input = h(`
    <div class="chat-input">
      <label class="upload-btn" id="chat-upload-lbl" title="Anexar arquivo para análise (não publica; só analisa)">📎<input type="file" id="chat-file" hidden /></label>
      <textarea id="chat-text" placeholder="Mensagem para ${a.nome}... (ou clica no 🎤 acima)"></textarea>
      <button class="send-btn" id="chat-send" title="Enviar">➤</button>
    </div>`);
  chatBlock.appendChild(input);
  body.appendChild(chatBlock);

  const send = () => sendChat(a);
  input.querySelector("#chat-send").onclick = send;
  input.querySelector("#chat-file").onchange = (e) => { const f = e.target.files[0]; if (f) uploadChatFile(a, f); e.target.value = ""; };
  input.querySelector("#chat-text").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });

  // ===== HABILIDADES + SUGESTÕES (rodapé colapsável) =====
  const sk = agentSkills(a);
  const SKILL_COLORS = [
    "linear-gradient(90deg,#f59e0b,#fbbf24)",
    "linear-gradient(90deg,#8b5cf6,#a78bfa)",
    "linear-gradient(90deg,#3b82f6,#60a5fa)",
    "linear-gradient(90deg,#22c55e,#4ade80)",
    "linear-gradient(90deg,#ec4899,#f472b6)",
  ];
  const det = h(`<details class="chat-extras"><summary>★ Habilidades & Sugestões</summary></details>`);
  const box = h(`<div class="skills-box"><h4>Habilidades</h4></div>`);
  sk.forEach((s, i) => {
    const p = pct(s.id);
    box.appendChild(h(`<div class="skill-row"><div class="sr-top"><span>${s.nome}</span><span class="sr-pct">${p}%</span></div><div class="skill-bar"><div class="skill-fill" style="width:${p}%;background:${SKILL_COLORS[i % SKILL_COLORS.length]}"></div></div></div>`));
  });
  det.appendChild(box);
  const sug = h(`<div class="cmd-suggest"></div>`);
  CMD_SUGGEST.forEach((c) => {
    const it = h(`<div class="cmd-item"><div class="ci-name">${c.name}</div><div class="ci-desc">${c.desc}</div></div>`);
    it.onclick = () => { $("chat-text").value = c.name.replace(/^[^ ]+ /, "") + ": "; $("chat-text").focus(); };
    sug.appendChild(it);
  });
  det.appendChild(sug);
  body.appendChild(det);
}

// Conversa com STREAMING (SSE) via /chat/stream — token a token, igual à
// interface clássica. Mantém histórico, voz/tts, conclave e escape de texto.
async function sendChat(a, explicitMsg, speak) {
  const ta = $("chat-text");
  const msg = ((explicitMsg != null ? explicitMsg : (ta ? ta.value : "")) || "").trim();
  if (!msg) return;
  const hist = state.chats[a.id] = state.chats[a.id] || [];
  hist.push({ role: "user", text: msg });
  const scroll = $("chat-scroll");
  scroll.appendChild(h(`<div class="chat-msg user">${_esc(msg)}</div>`));
  if (ta && explicitMsg == null) ta.value = "";
  const bot = h(`<div class="chat-msg bot streaming"><span class="stream-cursor">▋</span></div>`);
  scroll.appendChild(bot); scroll.scrollTop = scroll.scrollHeight;

  if (!state.online) {
    bot.classList.remove("streaming");
    bot.textContent = "Backend offline — suba o server.py para conversar de verdade, senhor.";
    hist.push({ role: "bot", text: bot.textContent });
    return;
  }

  let full = "", meta = {};
  try {
    const res = await fetch(BACKEND + "chat/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, use_conclave: !!state.useConclave, model: "claude" }),
    });
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({}));
      bot.classList.remove("streaming");
      bot.textContent = "Erro " + res.status + ": " + (err.error || res.statusText || "falha");
      hist.push({ role: "bot", text: bot.textContent });
      return;
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "", done = false;
    while (!done) {
      const { done: rd, value } = await reader.read();
      if (rd) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;          // ignora padding/SSE comments
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") { done = true; break; }
        let ev; try { ev = JSON.parse(raw); } catch (_) { continue; }
        if (ev.type === "token") {
          full += ev.text;
          bot.innerHTML = _esc(full) + '<span class="stream-cursor">▋</span>';
          scroll.scrollTop = scroll.scrollHeight;
        } else if (ev.type === "meta") {
          meta = Object.assign(meta, ev);
          if (ev.brain) state.lastBrain = ev.brain;
        } else if (ev.type === "done") {
          if (ev.text) full = ev.text;
          if (ev.brain) state.lastBrain = ev.brain;
          if (ev.intent) state.lastTools = ev.intent;
          meta = Object.assign(meta, ev);
        }
      }
    }
    const finalText = full || "Sem resposta.";
    bot.classList.remove("streaming");
    bot.textContent = finalText;        // textContent = render seguro, sem cursor
    hist.push({ role: "bot", text: finalText });
    if (speak) speakText(finalText);
    try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); renderRightPanel(); } catch (_) {}
  } catch (e) {
    bot.classList.remove("streaming");
    bot.textContent = (e && e.name === "TypeError")
      ? "Servidor offline — não consegui conversar agora, senhor."
      : ("Falhou: " + (e && e.message ? e.message : e));
    hist.push({ role: "bot", text: bot.textContent });
  }
  scroll.scrollTop = scroll.scrollHeight;
}

// Upload de arquivo p/ análise (migrado da /classic). POST /upload (multipart).
// Só ANALISA (salva em temp no backend); não publica, não envia. Texto escapado.
async function uploadChatFile(a, file) {
  const scroll = $("chat-scroll");
  if (!scroll) return;
  const hist = state.chats[a.id] = state.chats[a.id] || [];
  const u = h(`<div class="chat-msg user"></div>`); u.textContent = "📎 " + file.name; scroll.appendChild(u);
  hist.push({ role: "user", text: "📎 " + file.name });
  const bot = h(`<div class="chat-msg bot streaming"><span class="stream-cursor">▋</span> analisando…</div>`);
  scroll.appendChild(bot); scroll.scrollTop = scroll.scrollHeight;
  if (!state.online) { bot.classList.remove("streaming"); bot.textContent = "Backend offline — não consegui analisar o arquivo."; return; }
  try {
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(BACKEND + "upload", { method: "POST", body: fd });
    const d = await res.json().catch(() => ({}));
    bot.classList.remove("streaming");
    const txt = (d.status === "ok") ? (d.message || "Análise concluída.") : ("Erro ao analisar: " + (d.message || res.status));
    bot.textContent = txt;
    hist.push({ role: "bot", text: txt });
  } catch (e) {
    bot.classList.remove("streaming");
    bot.textContent = (e && e.name === "TypeError") ? "Servidor offline — não consegui enviar o arquivo." : ("Falhou: " + (e && e.message ? e.message : e));
  }
  scroll.scrollTop = scroll.scrollHeight;
}

// ---------- Voz: gravar → transcrever → _brain → falar ----------
let _mediaRec = null, _chunks = [];

async function speakText(text) {
  try {
    const r = await fetch(BACKEND + "tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
    if (!r.ok) return;
    const blob = await r.blob();
    new Audio(URL.createObjectURL(blob)).play().catch(() => {});
  } catch (_) {}
}

async function toggleVoice(a, btn) {
  if (_mediaRec && _mediaRec.state === "recording") { _mediaRec.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    _chunks = [];
    _mediaRec = new MediaRecorder(stream);
    _mediaRec.ondataavailable = (e) => { if (e.data.size) _chunks.push(e.data); };
    _mediaRec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      btn.classList.remove("rec"); btn.textContent = "🎙️";
      const scroll = $("chat-scroll");
      const tmp = h(`<div class="chat-msg user">🎙️ transcrevendo…</div>`);
      scroll.appendChild(tmp); scroll.scrollTop = scroll.scrollHeight;
      try {
        const fd = new FormData();
        fd.append("file", new Blob(_chunks, { type: "audio/webm" }), "voz.webm");
        const r = await fetch(BACKEND + "transcribe", { method: "POST", body: fd });
        const out = await r.json();
        tmp.remove();
        if (out.text) sendChat(a, out.text, true);        // fala a resposta
        else scroll.appendChild(h(`<div class="chat-msg bot">Não entendi o áudio${out.error ? ": " + out.error : ""}.</div>`));
      } catch (e) { tmp.textContent = "Falha na transcrição: " + e.message; }
    };
    _mediaRec.start();
    btn.classList.add("rec"); btn.textContent = "⏺";
  } catch (e) {
    alert("Microfone indisponível: " + e.message);
  }
}

export { viewChat };

// ---------- World ----------
