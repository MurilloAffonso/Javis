// Treino — status de treinamento por área — extraído de app.js em 2026-07-03. MESMO comportamento; módulo ES.
import { h, state, BACKEND, tryJson, withProjectId, renderCanvas } from "../../app.js";

function viewTreino(body) {
  body.appendChild(h(`<div class="card-sub" style="margin-bottom:16px">Pipeline: <b>_entrada</b> (vídeos/repos/PDFs, coletados ou manuais) → resumo no <b>NotebookLM</b> → <b>_resumos</b> entra na base RAG do Javes.</div>`));

  // Treinar direto de um vídeo do YouTube (transcrição → doc → reindexa o RAG).
  body.appendChild(h(`<div class="section-h">📺 Treinar de um vídeo do YouTube</div>`));
  const yt = h(`<div class="demanda" style="max-width:640px">
    <div class="card-sub" style="margin-bottom:8px">Cola a URL: o Javes extrai a transcrição, salva como material de treino e reindexa o RAG na hora.</div>
    <input id="yt-url" class="cs-input" style="width:100%;margin-bottom:8px" placeholder="https://youtube.com/watch?v=…" />
    <div style="text-align:right"><button class="btn ok" id="yt-run">📺 Treinar do vídeo</button></div>
    <div class="yt-out card-sub" style="margin-top:8px"></div>
  </div>`);
  body.appendChild(yt);
  yt.querySelector("#yt-run").onclick = async () => {
    const url = (yt.querySelector("#yt-url").value || "").trim();
    const out = yt.querySelector(".yt-out");
    if (!url) { out.textContent = "Cola a URL do vídeo primeiro."; return; }
    if (!state.online) { out.textContent = "Backend offline."; return; }
    const btn = yt.querySelector("#yt-run"); btn.disabled = true; out.textContent = "Extraindo transcrição e indexando (pode levar ~30s)…";
    try {
      const r = await tryJson(BACKEND + "train/youtube", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
      if (r.error) out.textContent = "⚠️ " + r.error;
      else out.textContent = `✅ "${r.title}" (${r.channel || "canal"}) · ${r.chars} chars → ${r.file}. Reindexando o RAG.`;
    } catch (e) { out.textContent = "Falhou: " + e.message; }
    btn.disabled = false;
  };

  // Analisar export de conversa do WhatsApp → estilo/vendas/leads perdidos + voz-murillo.md
  body.appendChild(h(`<div class="section-h" style="margin-top:20px">📱 Analisar conversas do WhatsApp</div>`));
  const wa = h(`<div class="demanda" style="max-width:760px">
    <div class="card-sub" style="margin-bottom:8px">Exporte uma conversa no WhatsApp (⋮ → Mais → <b>Exportar conversa</b> → <b>Sem mídia</b>) e cole o texto aqui. O Javes analisa seu estilo, onde os leads travam/somem, e destila uma "voz do Murillo" que vira treino do squad. <b>Local — nada é enviado.</b></div>
    <input id="wa-me" class="cs-input" style="width:100%;margin-bottom:8px" placeholder="seu nome como aparece no WhatsApp (opcional, ex: Murillo)" />
    <textarea id="wa-text" placeholder="cole aqui o conteúdo do .txt exportado…" style="min-height:120px"></textarea>
    <div style="text-align:right;margin-top:6px"><button class="btn ok" id="wa-run">📱 Analisar conversa</button></div>
    <div class="wa-out" style="margin-top:10px"></div>
  </div>`);
  body.appendChild(wa);
  wa.querySelector("#wa-run").onclick = async () => {
    const text = (wa.querySelector("#wa-text").value || "").trim();
    const me = (wa.querySelector("#wa-me").value || "").trim();
    const out = wa.querySelector(".wa-out");
    if (text.length < 40) { out.textContent = "Cole o texto da conversa exportada primeiro."; return; }
    if (!state.online) { out.textContent = "Backend offline."; return; }
    const btn = wa.querySelector("#wa-run"); btn.disabled = true;
    out.innerHTML = `<div class="card-sub">Analisando (pode levar ~1 min — lendo a conversa inteira)…</div>`;
    try {
      const r = await tryJson(withProjectId(BACKEND + "wa/analyze"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text, me }) });
      out.innerHTML = "";
      if (r.error && !r.analysis) { const b = h(`<div class="banner"></div>`); b.textContent = "⚠️ " + r.error; out.appendChild(b); btn.disabled = false; return; }
      if (r.stats && r.stats.total) out.appendChild(h(`<div class="card-sub" style="margin-bottom:8px">${r.stats.total} mensagens · ${r.stats.periodo || "—"} · você: ${r.stats.minhas_msgs || 0} · pico ${r.stats.hora_pico != null ? r.stats.hora_pico + "h" : "—"}</div>`));
      const box = h(`<div class="card" style="white-space:pre-wrap"></div>`); box.textContent = r.analysis || ""; out.appendChild(box);
      const saveRow = h(`<div style="text-align:right;margin-top:8px"><button class="btn no" id="wa-save">💾 Salvar como treino (voz-murillo.md)</button> <span class="wa-save-fb card-sub"></span></div>`);
      out.appendChild(saveRow);
      saveRow.querySelector("#wa-save").onclick = async (e) => {
        e.target.disabled = true;
        try { const s = await tryJson(withProjectId(BACKEND + "wa/save-voice"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: r.analysis }) }); saveRow.querySelector(".wa-save-fb").textContent = "✓ salvo em " + (s.file || "voz-murillo.md"); }
        catch (err) { saveRow.querySelector(".wa-save-fb").textContent = "falhou: " + err.message; e.target.disabled = false; }
      };
    } catch (e) { const d = h(`<div class="card-sub"></div>`); d.textContent = "Falhou: " + e.message; out.innerHTML = ""; out.appendChild(d); }
    btn.disabled = false;
  };

  body.appendChild(h(`<div class="section-h" style="margin-top:20px">🎓 Áreas de treino</div>`));
  if (!state.training.length) { body.appendChild(h(`<div class="empty-state">Sem dados de treinamento (backend offline?).</div>`)); return; }
  const grid = h(`<div class="grid cols-2"></div>`);
  state.training.forEach((a) => {
    const ent = a.entrada || 0, res = a.resumos || 0;
    const pc = ent ? Math.round((res / ent) * 100) : 0;
    const card = h(`
      <div class="card">
        <div class="card-head"><div class="card-icon">🎓</div><div><div class="card-title" style="text-transform:capitalize">${a.area}</div><div class="card-sub">${ent} entrada · ${res} resumos</div></div></div>
        <div class="skill-bar" style="margin:6px 0 4px"><div class="skill-fill" style="width:${pc}%"></div></div>
        <div class="card-sub">${pc}% resumido (no RAG)</div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn ok btn-scout">📥 Coletar (YouTube + GitHub)</button>
          <button class="btn no btn-resumir">✍️ Resumir pendentes (Claude)</button>
        </div>
        <div class="scout-out card-sub" style="margin-top:8px"></div>
      </div>`);
    card.querySelector(".btn-scout").onclick = async (e) => {
      const out = card.querySelector(".scout-out");
      e.target.disabled = true; out.textContent = "Coletando matéria-prima (consultando YouTube e GitHub)...";
      if (!state.online) { out.textContent = "Backend offline."; return; }
      try {
        const r = await tryJson(`${BACKEND}treinamento/scout/${a.area}`, { method: "POST" });
        const n = (r.results && r.results.length) || r.coletados || r.total || 0;
        out.textContent = `✅ Coleta concluída. Confira _treinamento/${a.area}/_entrada e suba no NotebookLM.`;
        try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; renderCanvas(); } catch (_) {}
      } catch (err) { out.textContent = "Falhou: " + err.message; e.target.disabled = false; }
    };
    card.querySelector(".btn-resumir").onclick = async (e) => {
      const out = card.querySelector(".scout-out");
      e.target.disabled = true; out.textContent = "Resumindo pendentes com o Claude (pode levar um pouco)...";
      if (!state.online) { out.textContent = "Backend offline."; e.target.disabled = false; return; }
      try {
        const r = await tryJson(`${BACKEND}treinamento/resumir/${a.area}`, { method: "POST" });
        if (r.error) { out.textContent = "⚠️ " + r.error; }
        else { out.textContent = `✅ ${r.resumidos} resumo(s) gerado(s) → entraram no RAG. Pendentes restantes: ${r.pendentes_restantes}.`; }
        try { state.training = (await tryJson(BACKEND + "treinamento/status")).areas || []; renderCanvas(); } catch (_) {}
      } catch (err) { out.textContent = "Falhou: " + err.message; e.target.disabled = false; }
    };
    grid.appendChild(card);
  });
  body.appendChild(grid);
  body.appendChild(h(`<div class="card-sub" style="margin-top:18px">💡 <b>NotebookLM</b> é o passo de resumo (manual — sem API pública): suba o material do <code>_entrada</code>, gere o resumo e cole em <code>_resumos</code>. O Javes indexa automático no RAG.</div>`));
}

export { viewTreino };
