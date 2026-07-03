/* ═══════════════════════════════════════════════════════════════════
   VOICE INFRA — Orb + Whisper + Wake Word + Voz sempre ativa + TTS
   Trazido do classic, adaptado pro Command Center.
   Extraído de app.js em 2026-07-02. MESMO comportamento; agora módulo ES.
   ═══════════════════════════════════════════════════════════════════ */
import { h, state, BACKEND, tryJson, _esc, activeAgent } from "../app.js";

let _orbInst = null;
let _whisper = null;
let _autoWhi = null;
let _wakeWord = null;
let _currentAudio = null;
const _audioQueue = [];
let _audioPlaying = false;


class VoiceOrb {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.state = "idle";
    this.color = { r: 34, g: 211, b: 238 }; // var(--accent-2)
    this.level = 0; this._level = 0; this.flash = 0;
    this.wave = new Array(64).fill(0);
    this._stopped = false;
    this._resize();
    this._onResize = () => this._resize();
    window.addEventListener("resize", this._onResize);
    this._loop();
  }
  destroy() { this._stopped = true; window.removeEventListener("resize", this._onResize); }
  _resize() {
    const r = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.w = r.width || 360; this.h = r.height || 360;
    this.canvas.width = this.w * dpr; this.canvas.height = this.h * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  setState(state) {
    this.state = state;
    const stage = document.getElementById("orb-host");
    const lblS = document.getElementById("neural-state");
    const lblP = document.getElementById("neural-pulse-lbl");
    stage?.classList.remove("thinking", "conclave");
    if (state === "thinking") { this.color = { r: 34, g: 211, b: 238 }; stage?.classList.add("thinking"); if (lblS) lblS.textContent = "PROCESSANDO"; if (lblP) lblP.textContent = "raciocinando..."; }
    else if (state === "conclave") { this.color = { r: 168, g: 85, b: 247 }; stage?.classList.add("conclave"); if (lblS) lblS.textContent = "CONCLAVE"; if (lblP) lblP.textContent = "debate interno"; }
    else if (state === "listening") { this.color = { r: 34, g: 211, b: 238 }; if (lblS) lblS.textContent = "OUVINDO"; if (lblP) lblP.textContent = "fala que eu te escuto"; }
    else if (state === "speaking") { this.color = { r: 34, g: 211, b: 238 }; if (lblS) lblS.textContent = "FALANDO"; if (lblP) lblP.textContent = "transmitindo resposta"; }
    else { this.color = { r: 34, g: 211, b: 238 }; if (lblS) lblS.textContent = "ONLINE"; if (lblP) lblP.textContent = "aguardando comando"; }
  }
  setLevel(v) { this.level = Math.min(1, Math.max(0, v)); }
  fire() { this.flash = Math.min(1, this.flash + 0.5); }
  _loop() {
    if (this._stopped) return;
    const { ctx, w, h, color } = this;
    const cx = w / 2, cy = h / 2;
    const R = Math.min(w, h) * 0.34;
    const t = Date.now() / 1000;
    ctx.clearRect(0, 0, w, h);
    this._level += (this.level - this._level) * 0.2;
    this.flash *= 0.9;
    const active = this.state !== "idle";
    const energy = (active ? 0.5 : 0.18) + this._level * 0.9 + this.flash * 0.6;
    const C = (a) => `rgba(${color.r},${color.g},${color.b},${a})`;
    const halo = ctx.createRadialGradient(cx, cy, R * 0.4, cx, cy, R * 2.0);
    halo.addColorStop(0, C(0.10 + energy * 0.10)); halo.addColorStop(1, C(0));
    ctx.fillStyle = halo; ctx.fillRect(0, 0, w, h);
    const rings = [{ rad: R * 1.55, w: 1, sp: 0.25, span: 1.1, a: 0.18 }, { rad: R * 1.34, w: 1.5, sp: -0.4, span: 2.4, a: 0.30 }, { rad: R * 1.16, w: 1, sp: 0.6, span: 0.8, a: 0.22 }];
    rings.forEach((rg) => {
      ctx.strokeStyle = C(rg.a + energy * 0.15); ctx.lineWidth = rg.w;
      ctx.beginPath(); ctx.arc(cx, cy, rg.rad, t * rg.sp, t * rg.sp + rg.span); ctx.stroke();
      const ex = cx + Math.cos(t * rg.sp + rg.span) * rg.rad;
      const ey = cy + Math.sin(t * rg.sp + rg.span) * rg.rad;
      ctx.fillStyle = C(0.6); ctx.beginPath(); ctx.arc(ex, ey, 2, 0, Math.PI * 2); ctx.fill();
    });
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-t * 0.3);
    ctx.strokeStyle = C(0.12); ctx.setLineDash([2, 8]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(0, 0, R * 1.72, 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([]); ctx.restore();
    const N = this.wave.length;
    for (let i = 0; i < N; i++) {
      const target = active || this._level > 0.02 ? (Math.sin(t * 6 + i * 0.5) * 0.5 + 0.5) * (0.3 + this._level * 2 + this.flash) : 0;
      this.wave[i] += (target - this.wave[i]) * 0.25;
    }
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {
      const idx = i % N;
      const ang = (i / N) * Math.PI * 2 - Math.PI / 2;
      const amp = R * 0.9 + this.wave[idx] * R * 0.45;
      const x = cx + Math.cos(ang) * amp; const y = cy + Math.sin(ang) * amp;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath(); ctx.strokeStyle = C(0.5 + energy * 0.3); ctx.lineWidth = 1.5; ctx.stroke();
    const corePulse = 1 + Math.sin(t * 2) * 0.06 + this._level * 0.5 + this.flash * 0.3;
    const coreR = R * 0.5 * corePulse;
    const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
    core.addColorStop(0, C(0.55 + energy * 0.3)); core.addColorStop(0.5, C(0.18)); core.addColorStop(1, C(0));
    ctx.fillStyle = core; ctx.beginPath(); ctx.arc(cx, cy, coreR, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = C(0.85); ctx.beginPath(); ctx.arc(cx, cy, R * 0.06 * corePulse, 0, Math.PI * 2); ctx.fill();
    const pc = active ? 5 : 3;
    for (let i = 0; i < pc; i++) {
      const a = t * (0.5 + i * 0.2) + i * 2.4;
      const rr = R * (1.0 + 0.25 * Math.sin(t + i));
      const px = cx + Math.cos(a) * rr; const py = cy + Math.sin(a) * rr;
      ctx.fillStyle = C(0.7); ctx.beginPath(); ctx.arc(px, py, 1.6, 0, Math.PI * 2); ctx.fill();
    }
    requestAnimationFrame(() => this._loop());
  }
}

class WhisperRecorder {
  constructor() { this.recording = false; this.mediaRec = null; this.chunks = []; this.stream = null; }
  async toggle() { this.recording ? this._stop() : await this._start(); }
  async _start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunks = [];
      this.mediaRec = new MediaRecorder(this.stream);
      this.mediaRec.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
      this.mediaRec.start(150);
      this.recording = true;
      document.getElementById("mic-btn")?.classList.add("recording");
      document.getElementById("voice-status")?.classList.add("active");
      const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "gravando...";
    } catch (e) { console.warn("Mic error:", e); }
  }
  _stop() {
    if (!this.recording || !this.mediaRec) return;
    this.recording = false;
    document.getElementById("mic-btn")?.classList.remove("recording");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "transcrevendo...";
    this.mediaRec.onstop = async () => {
      const blob = new Blob(this.chunks, { type: this.mediaRec.mimeType || "audio/webm" });
      this.stream?.getTracks().forEach((t) => t.stop());
      document.getElementById("voice-status")?.classList.remove("active");
      if (blob.size < 500) { if (vi) vi.textContent = ""; return; }
      try {
        const fd = new FormData();
        fd.append("file", blob, "audio.webm");
        const res = await fetch(BACKEND + "transcribe", { method: "POST", body: fd });
        if (res.ok) {
          const data = await res.json();
          const text = (data.text || "").trim();
          if (text) sendVoiceMessage(text);
        }
      } catch (err) { console.warn("Whisper error:", err); }
      if (vi) vi.textContent = "";
    };
    this.mediaRec.stop();
  }
}

class AutoWhisperEngine {
  constructor() {
    this.active = false; this.recording = false; this.stream = null; this.mediaRec = null;
    this.chunks = []; this.analyser = null; this.silTimer = null; this.recStart = 0;
    this.THRESHOLD = 0.035; this.SILENCE_MS = 2200; this.MIN_REC_MS = 800; this.MIN_BLOB = 4000;
  }
  async enable() {
    this.active = true;
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new AudioContext();
    const src = ctx.createMediaStreamSource(this.stream);
    this.analyser = ctx.createAnalyser(); this.analyser.fftSize = 1024;
    src.connect(this.analyser);
    const vi = document.getElementById("voice-interim");
    if (vi) vi.textContent = "calibrando microfone...";
    const noiseLevel = await this._measureNoise(1200);
    this.THRESHOLD = Math.max(0.030, noiseLevel * 3.5);
    if (vi) vi.textContent = `pronto (noise=${noiseLevel.toFixed(4)})`;
    setTimeout(() => { if (this.active && vi) vi.textContent = "aguardando voz..."; }, 1200);
    this._loop();
    document.getElementById("voice-status")?.classList.add("active");
    _orbInst?.setState("listening");
  }
  disable() {
    this.active = false; clearTimeout(this.silTimer);
    if (this.recording && this.mediaRec?.state === "recording") this.mediaRec.stop();
    this.stream?.getTracks().forEach((t) => t.stop());
    document.getElementById("voice-status")?.classList.remove("active");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "";
    _orbInst?.setLevel(0); _orbInst?.setState("idle");
  }
  async _measureNoise(durationMs) {
    return new Promise((resolve) => {
      const samples = [];
      const interval = setInterval(() => {
        const buf = new Float32Array(this.analyser.fftSize);
        this.analyser.getFloatTimeDomainData(buf);
        samples.push(Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length));
      }, 50);
      setTimeout(() => { clearInterval(interval); resolve(samples.reduce((a, b) => a + b, 0) / (samples.length || 1)); }, durationMs);
    });
  }
  _loop() {
    if (!this.active) return;
    const buf = new Float32Array(this.analyser.fftSize);
    this.analyser.getFloatTimeDomainData(buf);
    const vol = Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length);
    _orbInst?.setLevel(Math.min(1, vol * 12));
    if (vol > this.THRESHOLD && !this.recording) this._startSeg();
    else if (vol <= this.THRESHOLD && this.recording && !this.silTimer) this.silTimer = setTimeout(() => this._stopSeg(), this.SILENCE_MS);
    else if (vol > this.THRESHOLD && this.silTimer) { clearTimeout(this.silTimer); this.silTimer = null; }
    requestAnimationFrame(() => this._loop());
  }
  _startSeg() {
    this.recording = true; this.chunks = []; this.recStart = Date.now();
    this.mediaRec = new MediaRecorder(this.stream);
    this.mediaRec.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
    this.mediaRec.start(100);
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "ouvindo...";
  }
  _stopSeg() {
    this.recording = false; this.silTimer = null;
    if (!this.mediaRec || this.mediaRec.state !== "recording") return;
    const elapsed = Date.now() - this.recStart;
    this.mediaRec.onstop = async () => {
      const blob = new Blob(this.chunks, { type: this.mediaRec.mimeType || "audio/webm" });
      const vi = document.getElementById("voice-interim");
      if (elapsed < this.MIN_REC_MS || blob.size < this.MIN_BLOB) { if (this.active && vi) vi.textContent = "aguardando voz..."; return; }
      if (vi) vi.textContent = "transcrevendo...";
      try {
        const fd = new FormData(); fd.append("file", blob, "audio.webm");
        const res = await fetch(BACKEND + "transcribe", { method: "POST", body: fd });
        if (res.ok) {
          const data = await res.json();
          const text = (data.text || "").trim();
          const WHISPER_NOISE = /^(obrigado\.?|thanks\.?|thank you\.?|\.{2,}|música\.?|music\.?|legendas?\.?|subtitles?\.?|silence\.?|silêncio\.?|som de fundo\.?|background\.?|applause\.?|aplauso\.?|ruído\.?|noise\.?|beep\.?|bip\.?)$/i;
          const isNoise = !text || text.length < 4 || WHISPER_NOISE.test(text.trim()) || (text.length < 8 && /^[.,!?…\s]+$/.test(text));
          if (!isNoise) sendVoiceMessage(text);
        }
      } catch (err) { console.warn("Auto whisper error:", err); }
      if (this.active && vi) vi.textContent = "aguardando voz...";
    };
    this.mediaRec.stop();
  }
}

class WakeWordEngine {
  constructor() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.supported = !!SR; this.SR = SR;
    this.active = false; this.awoken = false; this.awokenTimer = null; this.rec = null;
    this.wakeRe = /\b(jamba|jamb[aá]|jambo|jambar|jarvis|j[aá]vis)\b/i;
  }
  toggle() {
    const vi = document.getElementById("voice-interim");
    if (!this.supported) { if (vi) vi.textContent = "wake word precisa do Chrome/Edge"; return; }
    this.active ? this.disable() : this.enable();
  }
  enable() {
    if (_autoWhi?.active) { _autoWhi.disable(); document.getElementById("voice-auto-btn")?.classList.remove("active"); }
    this.active = true;
    document.getElementById("wake-btn")?.classList.add("active");
    document.getElementById("voice-status")?.classList.add("active");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = 'diga "Javis" para ativar...';
    _orbInst?.setState("listening");
    this._build(); this._start();
  }
  disable() {
    this.active = false; clearTimeout(this.awokenTimer); this.awoken = false;
    document.getElementById("wake-btn")?.classList.remove("active");
    document.getElementById("voice-status")?.classList.remove("active");
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "";
    _orbInst?.setState("idle");
    try { this.rec?.stop(); } catch (e) {}
  }
  _build() {
    this.rec = new this.SR();
    this.rec.lang = "pt-BR"; this.rec.continuous = true; this.rec.interimResults = true;
    this.rec.onresult = (e) => this._onResult(e);
    this.rec.onend = () => { if (this.active) { try { this.rec.start(); } catch (e) {} } };
    this.rec.onerror = (e) => { if (e.error === "not-allowed") this.disable(); };
  }
  _start() { try { this.rec.start(); } catch (e) {} }
  _onResult(e) {
    let finalText = "";
    for (let i = e.resultIndex; i < e.results.length; i++) if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
    finalText = finalText.trim();
    if (!finalText) return;
    const lower = finalText.toLowerCase();
    const m = lower.match(this.wakeRe);
    const vi = document.getElementById("voice-interim");
    if (m) {
      _orbInst?.setState("listening"); _orbInst?.fire?.();
      const idx = lower.indexOf(m[0]) + m[0].length;
      const after = finalText.slice(idx).replace(/^[,.\s]+/, "").trim();
      if (after) { this._send(after); }
      else {
        this.awoken = true;
        if (vi) vi.textContent = "pode falar, senhor...";
        clearTimeout(this.awokenTimer);
        this.awokenTimer = setTimeout(() => {
          this.awoken = false;
          if (this.active && vi) vi.textContent = 'diga "Javis" para ativar...';
        }, 6000);
      }
    } else if (this.awoken) {
      this.awoken = false; clearTimeout(this.awokenTimer);
      this._send(finalText);
    }
  }
  _send(cmd) {
    if (!cmd) return;
    const vi = document.getElementById("voice-interim"); if (vi) vi.textContent = "";
    sendVoiceMessage(cmd);
    if (this.active && vi) setTimeout(() => { if (this.active && vi) vi.textContent = 'diga "Javis" para ativar...'; }, 1500);
  }
}

function appendVoiceMsg(role, text) {
  const scroll = document.getElementById("chat-scroll");
  if (!scroll) return null;
  const el = h(`<div class="chat-msg ${role}">${_esc(text)}</div>`);
  scroll.appendChild(el);
  scroll.scrollTop = scroll.scrollHeight;
  return el;
}

async function sendVoiceMessage(text) {
  if (!text) return;
  const a = activeAgent();
  state.chats[a.id] = state.chats[a.id] || [];
  state.chats[a.id].push({ role: "user", text: `🎤 ${text}` });
  appendVoiceMsg("user", `🎤 ${text}`);
  const typing = appendVoiceMsg("bot", "…");
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
  _audioQueue.length = 0; _audioPlaying = false;
  _orbInst?.setState("thinking");

  if (!state.online) { if (typing) typing.textContent = "Backend offline."; _orbInst?.setState("idle"); return; }

  try {
    const res = await fetch(BACKEND + "voice/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: text, model: "", use_conclave: state.useConclave, tts: state.useTts }),
    });
    if (!res.ok) { if (typing) typing.textContent = "Falha: " + res.status; _orbInst?.setState("idle"); return; }
    const reader = res.body.getReader(); const dec = new TextDecoder();
    let buf = "", fullText = "", done = false;
    while (!done) {
      const { done: d, value } = await reader.read();
      if (d) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n"); buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") { done = true; break; }
        let evt; try { evt = JSON.parse(raw); } catch (_) { continue; }
        if (evt.type === "audio") { enqueueAudio(evt.b64); if (evt.sentence) fullText += (fullText ? " " : "") + evt.sentence; }
        else if (evt.type === "tts_text") { speak(evt.text); fullText = evt.text; }
        else if (evt.type === "token") { fullText += evt.text; }
        else if (evt.type === "meta" && evt.text) { fullText = evt.text; }
        else if (evt.type === "done") { if (evt.text) fullText = evt.text; }
        if (typing) typing.textContent = fullText || "…";
      }
    }
    if (fullText) state.chats[a.id].push({ role: "bot", text: fullText });
    state.lastBrain = state.lastBrain || "main";
    try { state.telemetry = await tryJson(BACKEND + "ui/telemetry"); renderRightPanel(); } catch (_) {}
  } catch (e) {
    if (typing) typing.textContent = "Erro: " + e.message;
  } finally {
    if (!_audioPlaying) _orbInst?.setState("idle");
  }
}

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
  _orbInst?.setState("speaking");
  _currentAudio.onended = () => {
    URL.revokeObjectURL(url); _currentAudio = null; _audioPlaying = false;
    if (_audioQueue.length > 0) _drainAudioQueue();
    else _orbInst?.setState("idle");
  };
  _currentAudio.play().catch(() => { _audioPlaying = false; });
}

function cleanForSpeech(text) {
  return String(text || "")
    .replace(/```[\s\S]*?```/g, " ").replace(/`[^`]*`/g, " ")
    .replace(/\[[^\]]*\]\([^)]*\)/g, "").replace(/https?:\/\/\S+/g, "")
    .replace(/\[[^\]]*\.(md|txt|py|js|json)\]/gi, "").replace(/<[^>]+>/g, "")
    .replace(/[*_#>`~|]/g, "").replace(/^\s*\d+[\.\)]\s*/gm, "").replace(/^\s*[-•]\s*/gm, "")
    .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}]/gu, "")
    .replace(/\s+/g, " ").trim().substring(0, 600);
}

async function speak(text) {
  if (!text) return;
  const clean = cleanForSpeech(text);
  if (!clean) return;
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  try {
    const res = await fetch(BACKEND + "tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: clean }) });
    if (res.ok) {
      const blob = await res.blob(); const url = URL.createObjectURL(blob);
      _currentAudio = new Audio(url);
      _currentAudio.onended = () => { URL.revokeObjectURL(url); _currentAudio = null; };
      _currentAudio.play(); return;
    }
  } catch (_) {}
  if (!window.speechSynthesis) return;
  const utt = new SpeechSynthesisUtterance(clean);
  utt.lang = "pt-BR"; utt.rate = 1.0; utt.pitch = 1.0;
  _orbInst?.setState("speaking");
  utt.onboundary = (e) => { const intensity = Math.min(1, (e.charLength || 4) / 12); _orbInst?.setLevel(0.3 + intensity * 0.7); };
  utt.onend = () => { _orbInst?.setLevel(0); _orbInst?.setState("idle"); };
  window.speechSynthesis.speak(utt);
}

function initVoiceStage() {
  const canvas = document.getElementById("orb-canvas");
  if (!canvas) return;
  if (_orbInst) { _orbInst.destroy(); _orbInst = null; }
  if (_autoWhi?.active) _autoWhi.disable();
  if (_wakeWord?.active) _wakeWord.disable();
  _orbInst = new VoiceOrb(canvas);
  _whisper = _whisper || new WhisperRecorder();
  _autoWhi = _autoWhi || new AutoWhisperEngine();
  _wakeWord = _wakeWord || new WakeWordEngine();
  document.getElementById("mic-btn")?.addEventListener("click", () => _whisper.toggle());
  document.getElementById("wake-btn")?.addEventListener("click", () => _wakeWord.toggle());
  document.getElementById("voice-auto-btn")?.addEventListener("click", async () => {
    const btn = document.getElementById("voice-auto-btn");
    if (_autoWhi.active) { _autoWhi.disable(); btn?.classList.remove("active"); }
    else { if (_wakeWord.active) _wakeWord.disable(); try { await _autoWhi.enable(); btn?.classList.add("active"); } catch (e) { console.warn("auto whisper enable failed:", e); } }
  });
  const tts = document.getElementById("use-tts"); if (tts) tts.onchange = (e) => { state.useTts = e.target.checked; };
  const cc = document.getElementById("use-conclave"); if (cc) cc.onchange = (e) => { state.useConclave = e.target.checked; };
}

export { initVoiceStage };

