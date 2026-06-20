# Cérebro do chat = Claude assinatura (fora a API paga do OpenAI) — 18/06

## O que foi decidido

Tirar o gpt-4o-mini (API paga do OpenAI) do caminho de **conversa/raciocínio** e
botar o **Claude pela assinatura do Murillo** (Opus 4.8, `claude_brain.py`) como
cérebro padrão do chat. Confirmado por ele na interface.

Antes: só perguntas com gatilho de debate (`_likely_council`) iam pro Claude; todo
o resto caía no gpt-4o-mini via `agent.respond` (RAG + tool-use → 4-14s no teste
real do Murillo).

## Por que NÃO usar o Codex (que ele tinha cogitado)

O "Codex" do projeto (`code_agent.py`) é `codex exec` — subprocesso batch pra
tarefas de código que duram minutos, sem streaming. Como cérebro de chat abriria
um processo por resposta (10-40s, sem falar frase a frase). Pioraria a latência.
O Claude-assinatura já existe, **faz streaming na voz** e roda pela assinatura
(não gasta API paga) — exatamente o objetivo.

## Mudanças (server.py)

1. **Voz** (`/voice` stream, ~linha 692): o gate que mandava só pedidos "profundos"
   pro Claude streaming agora inclui `intent in ("conversa","desconhecido")`. Toda
   conversa de voz vai pro Claude Opus em streaming (frase a frase). Cai no `_brain`
   se o Claude vier vazio.
2. **Texto** (`_brain()`, passo 3 novo): para `intent` conversa/desconhecido, tenta
   `claude_brain.answer()` com histórico + estado do projeto (briefing) como
   contexto, `brain: "claude"`. Fallback pro agente tool-use (gpt-4o-mini) se o
   Claude faltar/vazio.

Ações que EXECUTAM (lembrete, abrir, programar) não mudaram: seguem no fast-path
ou no agente tool-use (passo 4). O `programar` continua no `brain_switch` (Claude
x Codex), feature separada.

## Trade-offs honestos

- **Não conserta os 13s sozinho.** Tira a API paga, mas boa parte da demora era o
  RAG + tool-use rodando todo turno. O Claude headless tem custo de spawn do
  subprocesso (~1-3s) + tempo do Opus. Pode ficar parecido ou um pouco mais lento
  em respostas curtas — mas é a assinatura e faz streaming. Latência de verdade é
  conserto separado (cortar RAG/tool-use desnecessário no papo simples).
- **Conversa via Claude não busca nas notas (RAG) hoje** — injeta histórico +
  estado do projeto, mas não o `knowledge.py`. Se faltar embasamento nas notas, dá
  pra ligar o RAG no contexto do Claude depois.

## Verificação

`python -c "import server"` OK · `pytest tests/` 71/71 · `claude_brain.available()`
True (Opus 4.8 / fallback sonnet). Teste ao vivo pelo Murillo pendente: falar e ver
se as respostas vêm marcadas `🧠 claude` (não `main`) e como fica a sensação de
velocidade.

## Próximo passo

1. Murillo testa ao vivo: respostas marcadas `claude`? Mais rápido/igual/lento?
2. Se quiser cortar os 13s de verdade: revisar RAG + tool-use no papo simples.

**Sem commit/push — Murillo revisa e decide o que comita.**
