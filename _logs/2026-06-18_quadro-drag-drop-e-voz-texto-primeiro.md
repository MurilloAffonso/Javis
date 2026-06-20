# Quadro: arrastar muda status real + voz silenciosa por padrão — 18/06

## O que foi decidido

Murillo pediu "todos" os dois próximos passos do Quadro estilo Plane: (1)
arrastar card pra mudar status grava de volta, (2) botão de gravação. Fiz as
duas, e a segunda já existia em boa parte — só faltava um ajuste pontual.

## 1. Drag-and-drop grava no backlog real

- **`backend/mission_board.py`**: nova `set_task_done(mission_id, node_id, done)`
  — localiza a tarefa pelo índice sequencial dentro da seção (`{slug}-t{i}`) e
  reescreve o checkbox `[ ]`/`[x]` na linha exata do `codex_backlog.md`.
  Devolve `False` se a missão for sintética (treinamento/projetos externos —
  calculadas, sem checkbox pra editar).
- **`backend/server.py`**: `POST /missions/{mission_id}/nodes/{node_id}/done`
  — chama `set_task_done`, 404 se não editável.
- **`frontend/app.js`**: cards do Quadro ficam `draggable` (exceto status
  `running`, que é sempre calculado — não tem checkbox, não aceita drop).
  `quadroDragStart/DragOver/DragLeave/Drop` — ao soltar em Pendente/Concluído,
  chama o endpoint novo e atualiza o card local; soltar em "Em andamento" dá
  toast explicando que essa coluna é calculada.
- **`frontend/style.css`**: `.dragging`, `.drag-over`.

### Verificação (real, sem deixar rastro)
- Testei via curl direto: missão sintética → 404 confirmado. Missão real → fiz
  um round-trip (done→pending→done) na tarefa `conte-do-vem-passear-jampa-t0` e
  confirmei no `git diff` que essa linha específica voltou exatamente ao
  original.
- **Achado no caminho**: o `git diff` mostrou MUITAS outras tarefas mudando de
  `[ ]` pra `[x]` ao mesmo tempo — investiguei antes de seguir (regra
  anti-fabricação: verificar antes de concluir). Não era bug meu: o
  **orquestrador Codex autônomo estava rodando em paralelo** nesse exato
  momento (`codex_orch_log.txt`: "Tarefa marcada como [x] no backlog... Commit
  feito"), terminando tarefas reais e comitando por conta própria. Coincidência
  de timing com meu teste, não interferência.
- Repeti o teste de drag-and-drop **na UI real** (Playwright, chamando os
  handlers JS direto no DOM): card foi pra Pendente, voltou pra Concluído,
  confirmado visualmente e no `git diff` (zero rastro extra).

## 2. Botão de gravação — ajuste de voz

O botão de gravação (🎤 `mic-btn` → `WhisperRecorder`) **já existia e já fazia**
exatamente o que Murillo descreveu: grava → transcreve (`/transcribe`) → entra
na conversa automaticamente (`sendVoiceMessage`). Não precisava construir nada
novo aí.

O que faltava: Murillo disse "comando de voz ele não vai responder por áudio,
só se eu mandar" — mas o checkbox 🔊 (`use-tts`) vinha **marcado por padrão**,
então toda resposta (de voz ou texto) saía falada sem pedir. Mudei o default
pra **desmarcado** (`index.html`, linha do `use-tts`). Resposta volta a ser só
texto, a menos que o Murillo marque a caixinha.

Os 3 botões de voz (mic/wake/sempre-ativo) continuam visíveis — não escondi
nenhum, decisão mais segura/reversível (duas perguntas sobre isso ficaram sem
resposta antes; optei pelo caminho que não reduz nada do que já existe).

## Verificação

- `node --check app.js` / `python -c "import ast..."` nos 2 arquivos Python.
- Rota nova confirmada no `/openapi.json`.
- Round-trips reais via curl e via Playwright (sem deixar diff órfão).
- Checkbox de TTS confirmado `false` por padrão no DOM renderizado.
- Console do browser: só o 404 do favicon (pré-existente).

## Próximo passo

- Se Murillo quiser, dar opção de revisar o texto transcrito antes de enviar
  (hoje envia direto) — fica pra quando ele decidir essa preferência.

**Sem commit/push — Murillo revisa e decide o que comita.**
