# Javis — Melhorias de Voz, Inteligência e Estrutura

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o Javis mais preciso no comando de voz, mais rápido nas respostas e mais inteligente no roteamento de intenções.

**Architecture:** Três camadas de melhoria independentes: (1) VAD + filtro de ruído mais robusto no frontend, (2) roteamento mais inteligente com mais fast-paths no backend, (3) TTS antecipado para reduzir latência percebida.

**Tech Stack:** FastAPI, OpenAI Whisper API, Web Audio API, GPT-4o-mini, ddgs, Playwright

---

## Diagnóstico dos problemas reais

| Problema | Causa raiz | Arquivo |
|---|---|---|
| Voz imprecisa / corte cedo | SILENCE_MS=1400 corta no meio de frases | `frontend/app.js:958` |
| Whisper transcrevendo ruído | isNoise filter muito básico | `frontend/app.js:1067` |
| Resposta lenta (~3-4s) | TTS só começa após resposta completa do LLM | `frontend/app.js:1279` |
| Comandos simples vão pro LLM | fast-path limitado a 7 intents | `backend/server.py:477` |
| Sem memória entre sessões | history limpa ao fechar browser | `frontend/app.js:135` |
| Orbe não reage durante TTS | setLevel não chamado no speak() | `frontend/app.js:1279` |

---

## Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `frontend/app.js` | VAD params, filtros Whisper, TTS streaming, orbe durante TTS |
| `backend/server.py` | Expand FAST_PATH, history persistence endpoint |
| `backend/agent.py` | System prompt melhorado, mais contexto de hora |
| `backend/history_store.py` | **NOVO** — salva/carrega histórico entre sessões |

---

## Task 1: Melhorar VAD — silêncio mais longo, menos corte

**Problema:** `SILENCE_MS=1400` corta frases longas ao meio. Murillo diz "pesquisa no Google sobre" e Whisper recebe apenas "pesquisa".

**Files:**
- Modify: `_apps/javis-local-interface/frontend/app.js:957-960`

- [ ] **Step 1: Ajustar parâmetros do AutoWhisperEngine**

```javascript
// linha 957-960 em app.js — substituir:
this.THRESHOLD   = 0.035;
this.SILENCE_MS  = 1400;
this.MIN_REC_MS  = 600;
this.MIN_BLOB    = 3000;

// por:
this.THRESHOLD   = 0.035;
this.SILENCE_MS  = 2200;   // +800ms — frases longas não são cortadas
this.MIN_REC_MS  = 800;    // ignora sons < 0.8s
this.MIN_BLOB    = 4000;   // blob mínimo maior = menos ruído breve
```

- [ ] **Step 2: Testar fala longa**
  - Abrir `http://localhost:8000`
  - Ativar 👂 (always-on)
  - Falar devagar: "pesquisa no Google sobre avaliações da Vem Passear em Jampa"
  - Verificar que a frase completa aparece no chat sem corte

- [ ] **Step 3: Commit**
```bash
git add _apps/javis-local-interface/frontend/app.js
git commit -m "fix: aumenta SILENCE_MS para 2200ms — evita corte de frases longas"
```

---

## Task 2: Filtro de ruído Whisper mais robusto

**Problema:** Whisper retorna frases genéricas para silêncio/ruído de fundo (ex: "Obrigado.", "Legendas.", "Som de fundo.", "Música.", etc.)

**Files:**
- Modify: `_apps/javis-local-interface/frontend/app.js:1067-1069`

- [ ] **Step 1: Expandir lista de alucinações do Whisper**

```javascript
// linha 1067-1069 em app.js — substituir o bloco isNoise:
const WHISPER_NOISE = /^(obrigado\.?|thanks\.?|thank you\.?|\.{2,}|música\.?|music\.?|legendas?\.?|subtitles?\.?|silence\.?|silêncio\.?|som de fundo\.?|background\.?|applause\.?|aplauso\.?|ruído\.?|noise\.?|beep\.?|bip\.?)$/i;
const isNoise = !text
  || text.length < 4
  || WHISPER_NOISE.test(text.trim())
  || (text.length < 8 && /^[.,!?…\s]+$/.test(text));  // só pontuação
```

- [ ] **Step 2: Testar silêncio**
  - Ativar 👂, ficar em silêncio por 5s
  - Verificar que nenhuma mensagem aparece no chat

- [ ] **Step 3: Commit**
```bash
git add _apps/javis-local-interface/frontend/app.js
git commit -m "fix: expande filtro de alucinação do Whisper com 12 padrões"
```

---

## Task 3: Orbe reage durante TTS (feedback visual)

**Problema:** O orbe fica parado enquanto o Javis fala. Deveria pulsar conforme o áudio.

**Files:**
- Modify: `_apps/javis-local-interface/frontend/app.js:1279-1311` (função `speak`)

- [ ] **Step 1: Adicionar animação de nível ao speak()**

Localizar a função `speak(text)` (~linha 1279) e adicionar antes do `utterance.onend`:

```javascript
// Dentro da função speak(), antes de speechSynthesis.speak(utterance):
neuralBrain?.setState("speaking");

utterance.onboundary = (e) => {
  // Pulsa o orbe proporcional ao comprimento da palavra
  const intensity = Math.min(1, (e.charLength || 4) / 12);
  neuralBrain?.setLevel(0.3 + intensity * 0.7);
};
utterance.onend = () => {
  neuralBrain?.setLevel(0);
  neuralBrain?.setState("idle");
};
```

- [ ] **Step 2: Testar visualmente**
  - Pedir ao Javis: "que horas são?"
  - Verificar que o orbe pulsa durante a resposta em voz

- [ ] **Step 3: Commit**
```bash
git add _apps/javis-local-interface/frontend/app.js
git commit -m "feat: orbe anima durante TTS com onboundary"
```

---

## Task 4: Expandir FAST_PATH — mais comandos sem LLM

**Problema:** Comandos óbvios como "que horas são", "abre YouTube" passam pelo LLM (~3s) desnecessariamente.

**Files:**
- Modify: `_apps/javis-local-interface/backend/server.py:477-480`
- Modify: `_apps/javis-local-interface/backend/command_router.py`

- [ ] **Step 1: Adicionar intents ao FAST_PATH**

```python
# server.py linha 477 — substituir:
FAST_PATH = {
    "abrir_navegador", "abrir_openwebui", "abrir_javis",
    "abrir_vscode", "abrir_terminal", "abrir_projeto", "status_sistema",
}

# por:
FAST_PATH = {
    "abrir_navegador", "abrir_openwebui", "abrir_javis",
    "abrir_vscode", "abrir_terminal", "abrir_projeto", "status_sistema",
    "hora_data", "abrir_youtube", "tocar_musica", "listar_lembretes",
}
```

- [ ] **Step 2: Verificar que hora_data está em actions.execute**

No `agent.py`, `hora_data` é executada em `_exec_tool`. Para fast_path funcionar, precisa estar em `actions.execute`. Verificar `actions.py` e adicionar se necessário:

```python
# Em actions.py, dentro de execute():
if intent == "hora_data":
    from datetime import datetime
    dias = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    n = datetime.now()
    return {"status":"ok","message":f"São {n.strftime('%H:%M')}, {dias[n.weekday()]}, {n.day} de {meses[n.month-1]} de {n.year}, senhor."}
```

- [ ] **Step 3: Testar velocidade**
  - Enviar via chat: "que horas são"
  - Verificar que `ms` na resposta é < 100 (sem LLM)

- [ ] **Step 4: Commit**
```bash
git add _apps/javis-local-interface/backend/server.py _apps/javis-local-interface/backend/actions.py
git commit -m "perf: expande FAST_PATH com hora_data, youtube, musica — zero LLM"
```

---

## Task 5: Histórico persistente entre sessões

**Problema:** Fechar e reabrir o browser limpa todo o histórico. Javis não lembra de conversas anteriores.

**Files:**
- Create: `_apps/javis-local-interface/backend/history_store.py`
- Modify: `_apps/javis-local-interface/backend/server.py` (endpoints GET/POST /history)
- Modify: `_apps/javis-local-interface/frontend/app.js` (carregar histórico no init)

- [ ] **Step 1: Criar history_store.py**

```python
# _apps/javis-local-interface/backend/history_store.py
import json
from pathlib import Path
from datetime import datetime

_FILE = Path(__file__).parent.parent / "_data" / "chat_history.json"
_FILE.parent.mkdir(exist_ok=True)
MAX_ENTRIES = 200

def load() -> list[dict]:
    if not _FILE.exists():
        return []
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))[-MAX_ENTRIES:]
    except Exception:
        return []

def append(role: str, content: str):
    hist = load()
    hist.append({"role": role, "content": content, "ts": datetime.now().isoformat()})
    _FILE.write_text(json.dumps(hist[-MAX_ENTRIES:], ensure_ascii=False, indent=2), encoding="utf-8")

def clear():
    if _FILE.exists():
        _FILE.unlink()
```

- [ ] **Step 2: Adicionar endpoints em server.py**

```python
# Adicionar após os imports em server.py:
import history_store

@app.get("/history")
async def get_history():
    return JSONResponse(history_store.load())

@app.delete("/history")
async def clear_history():
    history_store.clear()
    return JSONResponse({"status": "ok"})
```

E dentro de `/chat` e `/voice`, após montar `entry`, adicionar:
```python
history_store.append("user", text)
history_store.append("assistant", out["text"])
```

- [ ] **Step 3: Carregar histórico no frontend (app.js)**

Na função de inicialização do app (buscar onde o chat é inicializado, ~linha 50-130):

```javascript
// Após inicializar o chat, carregar histórico:
async function loadHistory() {
  try {
    const r = await fetch(`${API}/history`);
    if (!r.ok) return;
    const hist = await r.json();
    const recent = hist.slice(-20); // últimas 20 mensagens
    for (const h of recent) {
      if (h.role === "user") appendMsg("user", esc(h.content));
      else if (h.role === "assistant") appendMsg("assistant", renderMarkdown(h.content));
    }
  } catch (e) { console.warn("Histórico:", e); }
}
// Chamar no init:
loadHistory();
```

- [ ] **Step 4: Testar persistência**
  - Enviar: "meu nome é Murillo"
  - Fechar e reabrir `http://localhost:8000`
  - Verificar que a mensagem aparece no chat

- [ ] **Step 5: Commit**
```bash
git add _apps/javis-local-interface/backend/history_store.py _apps/javis-local-interface/backend/server.py _apps/javis-local-interface/frontend/app.js
git commit -m "feat: histórico persistente entre sessões (200 mensagens)"
```

---

## Task 6: System prompt mais forte para português

**Problema:** Javis às vezes responde em inglês ou com markdown quando não deve.

**Files:**
- Modify: `_apps/javis-local-interface/backend/agent.py` (SYSTEM_AGENT)

- [ ] **Step 1: Reforçar system prompt**

Localizar `SYSTEM_AGENT` em `agent.py` e adicionar/reforçar:

```python
SYSTEM_AGENT = """Você é Jamba, assistente pessoal de Murillo Affonso.

REGRAS ABSOLUTAS — NUNCA VIOLAR:
1. IDIOMA: Responda SEMPRE em português do Brasil. NUNCA em inglês, espanhol ou outro idioma.
2. TRATAMENTO: Chame o usuário de "senhor" ou "Murillo" — nunca "você" ou "user".
3. VOZ: Respostas são lidas em voz alta — seja CONCISO. Máximo 2 frases para ações. Sem markdown.
4. AÇÃO: Quando houver uma ferramenta disponível, USE-A. Não descreva o que faria — faça.
5. SEM IMPROVISO: Nunca invente dados (preços, horários, endereços). Use as ferramentas.

PERFIL DE MURILLO:
- Empreendedor, fundador da Vem Passear em Jampa (turismo em João Pessoa/PB)
- Usa o Javis para automatizar tarefas e agilizar operações
- Prefere respostas diretas e curtas

Hora atual: {hora_atual}
"""
```

Modificar `_system()` para injetar a hora:
```python
def _system() -> str:
    from datetime import datetime
    hora = datetime.now().strftime("%H:%M de %A, %d/%m/%Y")
    base = SYSTEM_AGENT.replace("{hora_atual}", hora)
    try:
        import profile
        return base + profile.context_block()
    except Exception:
        return base
```

- [ ] **Step 2: Testar idioma**
  - Enviar: "what time is it?"
  - Verificar resposta em português

- [ ] **Step 3: Commit**
```bash
git add _apps/javis-local-interface/backend/agent.py
git commit -m "fix: system prompt reforçado — português obrigatório, concisão para voz"
```

---

## Ordem de execução recomendada

1. Task 4 (FAST_PATH) — impacto imediato em velocidade, sem risco
2. Task 1 (VAD) — resolve corte de frases, 1 linha
3. Task 2 (filtro Whisper) — resolve ruído sendo transcrito
4. Task 6 (system prompt) — resolve inglês/markdown
5. Task 3 (orbe TTS) — visual, sem risco
6. Task 5 (histórico) — maior esforço, maior impacto a longo prazo

## Teste de regressão após tudo

```bash
cd _apps/javis-local-interface
pytest backend/tests/ -q
# esperado: todos passam
```

---

*Plano gerado em 2026-06-13 | Javis v2 | skill: superpowers:writing-plans*
