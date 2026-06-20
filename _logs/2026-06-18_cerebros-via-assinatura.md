# Cérebros do Javis passam a rodar 100% pela assinatura Claude — 18/06

## O que foi decidido

Murillo pediu (mensagem de voz) pra tirar o ChatGPT/OpenAI API dos "dois
cérebros do projeto" e rodar só pela assinatura do Claude. Confirmado via
pergunta direta: cérebro principal (chat/voz com tool-use) + Conclave.

## O que foi implementado

- **`claude_brain.py`**: `answer_stream()` ganhou parâmetro `system` (antes só
  `answer()` aceitava override de system prompt; agora streaming também aceita,
  necessário pros outros cérebros passarem a própria persona).
- **`llm_providers.py`** (camada compartilhada por Conclave, squads, analyzers,
  orchestrator, telegram_bridge): `call_claude`/`call_openai`/`stream_claude`
  reescritos pra rotear pelo `claude_brain` (assinatura) em vez de chamar a
  API da OpenAI ou da Anthropic por chave. `call_openai` ficou como alias de
  `call_claude` — mesmo cérebro, nome antigo preservado pros ~10 chamadores
  que ainda importam um ou outro. Fallback final: Ollama local.
  - `embed()` (embeddings semânticos pro `knowledge.py`) **não mudou** —
    continua OpenAI, porque Claude não expõe embeddings pela assinatura e não
    tem alternativa local equivalente. Não é um "cérebro" de conversa, é uma
    utilidade de busca semântica.
- **`agent.py`** (cérebro principal, tool-use de voz/chat):
  - Nova `_respond_claude_subscription()`: como o Claude Code headless não
    expõe function-calling nativo pra ferramentas arbitrárias do Jamba
    (tocar_musica, clima, abrir_app...), a decisão de ferramenta vem como
    JSON em texto puro (instruído no system prompt: `_tool_catalog()` lista
    as ferramentas, e o prompt pede `{"tool": ..., "args": {...}}` quando
    aplicável) — parseado por `_parse_tool_json()` e executado pelo mesmo
    `_exec_tool()` que os outros provedores já usavam. Loop multi-rodada
    igual ao dos outros (`max_rounds`).
  - `respond()`: cascata mudou de `OpenAI → Claude(API) → OpenRouter` pra
    `Claude (assinatura) → OpenAI → Claude(API) → OpenRouter` — assinatura é
    primária agora; os outros só entram se o Claude Code não responder.
  - `stream_text()` (chat sem tool-use): tenta `claude_brain.answer_stream()`
    primeiro, cai pra OpenAI só se a assinatura não devolver nada.

## Trade-off importante (testado, não hipotético)

Subprocess do Claude Code tem cold-start alto comparado à API:
- `agent.respond("que horas são?")` → **47.9s** (antes, instantâneo via gpt-4o).
- `Conclave().debate(...)` (3 chamadas sequenciais: Crítico→Advogado→Sintetizador)
  → **154.4s** (antes, ~3-6s via gpt-4o-mini).

Pra voz isso é perceptível — Murillo vai sentir a resposta demorar bem mais.
Não ajustei nada além do pedido (sem cache, sem paralelizar Conclave) porque
não foi pedido; registrando aqui pro caso ele queira otimizar depois.

## Verificação (real, não só leitura de código)

- `python -m py_compile agent.py llm_providers.py claude_brain.py conclave.py` — OK.
- `pytest tests/ -q` → 71 passed (suíte completa do backend, sem regressão).
- Chamada real (subprocess de verdade, não mock): `agent.respond("que horas são?")`
  → escolheu `hora_data` via JSON, executou, devolveu texto certo.
- Chamada real: `Conclave().debate(...)` → rodou Crítico/Advogado/Sintetizador
  via assinatura, devolveu síntese coerente.
- Zero chamada à API da OpenAI ou Anthropic-por-chave nos dois testes (só
  `claude_brain`/subprocess `claude` e, se precisasse, Ollama).

## Fora de escopo (não tocado)

- `embed()` (embeddings OpenAI) — sem alternativa via assinatura, mantido.
- `claude_exec.py` (motor de execução de tarefas no projeto) — já era
  assinatura, não precisou mudar.
- Outros chamadores de `llm_providers` (squads, analyzers, orchestrator,
  telegram_bridge) — herdam o novo cérebro automaticamente, sem mudança de
  código própria, porque consomem `call_claude`/`call_openai` que agora é
  uma coisa só.

**Sem commit/push — Murillo revisa e decide o que comita.**
