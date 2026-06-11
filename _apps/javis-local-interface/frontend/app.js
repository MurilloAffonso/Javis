// Javis Local Interface — frontend v0
// Simula o Command Router em JS para feedback imediato (sem servidor).
// Para executar ações reais, use o CLI: python backend/main.py

const RULES = [
  ["acao_perigosa",  ["apaga","apagar","deleta","deletar","formata","rm -rf","del /f","git push","instala","instalar","remove","remover"]],
  ["abrir_youtube",  ["youtube"]],
  ["tocar_musica",   ["toca ","música","musica","playlist","play ","lofi","som relaxante"]],
  ["abrir_openwebui",["open webui","openwebui","webui","localhost:3000"]],
  ["abrir_vscode",   ["vscode","vs code","visual studio","editor de código","editor de codigo"]],
  ["abrir_terminal", ["terminal","powershell","cmd","prompt de comando"]],
  ["abrir_navegador",["navegador","chrome","firefox","edge","browser"]],
  ["abrir_javis",    ["pasta do javis","pasta javis","abre o javis","abrir javis"]],
  ["registrar_ideia",["anota","anotar","captura ideia","registra ideia","ideia:","tive uma ideia"]],
  ["status_sistema", ["status","tá funcionando","ta funcionando","check sistema","como estão os serviços"]],
];

const RISK = {
  acao_perigosa:"critical", abrir_terminal:"medium",
  abrir_navegador:"low", abrir_youtube:"low", tocar_musica:"low",
  abrir_openwebui:"low", abrir_vscode:"low", abrir_javis:"low",
  registrar_ideia:"low", status_sistema:"low",
  conversa:"none", desconhecido:"none",
};

const ICON = { critical:"🔴", medium:"🟡", low:"🟢", none:"⚪" };

const MESSAGES = {
  acao_perigosa:  () => ({ cls:"blocked", text:"⛔ Ação bloqueada — risk_level: critical. Comando destrutivo detectado." }),
  abrir_youtube:  () => ({ cls:"ok",  text:"✅ Abrindo YouTube...", url:"https://www.youtube.com" }),
  tocar_musica:   () => ({ cls:"ok",  text:"✅ Buscando música no YouTube...", url:"https://www.youtube.com/results?search_query=lofi+beats+para+trabalhar" }),
  abrir_openwebui:() => ({ cls:"ok",  text:"✅ Abrindo Open WebUI...", url:"http://localhost:3000" }),
  abrir_navegador:() => ({ cls:"ok",  text:"✅ Abrindo navegador...", url:"https://www.google.com" }),
  abrir_vscode:   () => ({ cls:"warn",text:"🟡 Para abrir o VS Code, use o CLI: python backend/main.py" }),
  abrir_terminal: () => ({ cls:"warn",text:"🟡 Abrir terminal requer aprovação. Use o CLI: python backend/main.py" }),
  abrir_javis:    () => ({ cls:"warn",text:"🟡 Para abrir a pasta, use o CLI: python backend/main.py" }),
  registrar_ideia:() => ({ cls:"warn",text:"🟡 Registro de ideias requer o CLI: python backend/main.py" }),
  status_sistema: () => ({ cls:"system",text:"ℹ️ Verificando serviços...\n   Open WebUI (3000) — verifique em http://localhost:3000\n   Ollama (11434) — verifique com: ollama list\n   Voz (12393) — verifique em http://localhost:12393" }),
  conversa:       () => ({ cls:"llm",text:"💬 Encaminhando ao Open WebUI → http://localhost:3000", url:"http://localhost:3000" }),
  desconhecido:   () => ({ cls:"llm",text:"💬 Sem ação reconhecida → http://localhost:3000", url:"http://localhost:3000" }),
};

function classify(text) {
  const t = text.toLowerCase();
  for (const [intent, kws] of RULES) {
    for (const kw of kws) { if (t.includes(kw)) return intent; }
  }
  const hints = ["como","o que","me explica","quem","quando","por que","qual","você","voce","ajuda","preciso"];
  if (hints.some(h => t.includes(h))) return "conversa";
  if (t.split(" ").length <= 3) return "desconhecido";
  return "conversa";
}

function route(text) {
  const intent = classify(text);
  const risk = RISK[intent] || "none";
  return { intent, risk, icon: ICON[risk] };
}

const log  = document.getElementById("log");
const form = document.getElementById("form");
const inp  = document.getElementById("input");

function addEntry(cls, html) {
  const div = document.createElement("div");
  div.className = `entry ${cls}`;
  div.innerHTML = html;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function handleText(text) {
  if (!text.trim()) return;
  addEntry("user", `<strong>Você:</strong> ${esc(text)}`);

  const { intent, risk, icon } = route(text);
  const meta = `<div class="meta">${icon} intent: <code>${intent}</code>  risk: ${risk}</div>`;

  const handler = MESSAGES[intent] || MESSAGES["desconhecido"];
  const { cls, text: msg, url } = handler();

  const lines = msg.split("\n").map(l => esc(l)).join("<br>");
  addEntry(cls, lines + meta);

  if (url && risk !== "critical") {
    setTimeout(() => window.open(url, "_blank"), 300);
  }
}

form.addEventListener("submit", e => {
  e.preventDefault();
  const text = inp.value.trim();
  if (!text) return;
  inp.value = "";
  handleText(text);
});

document.querySelectorAll(".quick").forEach(btn => {
  btn.addEventListener("click", () => handleText(btn.dataset.cmd));
});

function esc(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
