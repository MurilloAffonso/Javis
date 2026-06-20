# Comando de voz/texto pra trocar o motor de execução (Claude ↔ Codex) — 18/06

## O que foi decidido

Antes só dava pra trocar o motor de execução (o que roda a ferramenta
`programar`: Claude Code ou Codex) pela tela (`POST /brain/active`). Murillo quis
um comando falado/digitado. Criado o intent **`trocar_motor`** no fast-path
(sem LLM, resposta instantânea).

Contexto: o `programar` despacha tarefa de execução pro motor ativo
(`brain_switch`). Codex roda pela assinatura do ChatGPT (não gasta cota do
Claude) e em segundo plano — bom pra offload de produção pesada. Trocar por voz
deixa esse desvio prático no meio da conversa.

## Mudanças

- **`command_router.py`**: intent `trocar_motor` com gatilhos ("usa o codex",
  "muda pro claude", "troca o motor", "qual motor"...); em `RISK_MAP` (low, sem
  aprovação) e `ACTION_MAP` (`switch_brain`).
- **`actions.py`**: handler `_switch_brain` — detecta "codex"/"claude" na fala,
  chama `brain_switch.set_active`, e responde falado. Sem nome → só informa o
  motor ativo. Idempotente (avisa se já está no motor pedido).
- **`server.py`**: `trocar_motor` no `FAST_PATH` (executa instantâneo, zero token).
- **`config/commands.yaml`**: documentado `trocar_motor` + APROVEITEI pra cobrir
  3 intents que já estavam defasados no YAML (`analisar_site`, `clima`,
  `hora_data` — faltavam de antes). Consistência backend↔YAML voltou a 17/17.

## Por quê

Murillo quer poder mandar a produção pesada pro Codex (economiza cota do Claude)
sem largar a voz/teclado pra clicar num botão. O fast-path garante que o comando
não gasta LLM nenhum.

## Verificação

`pytest tests/` 71/71 · `test_intent_consistency.py` (modo __main__) verde, 17
intents idênticos backend↔YAML (antes 16 falhas: 12 pré-existentes + 4 do novo).
Roteamento testado: "usa o codex"/"muda pro claude"/"qual motor" → intent
`trocar_motor`. Execução testada: alterna claude↔codex e reporta o ativo; estado
volta ao padrão (claude) ao fim do teste.

## Próximo passo

1. Murillo testa por voz: "Javis, usa o Codex" → confirma que troca; depois pede
   pra "programar" algo e vê se roda no Codex (em segundo plano, avisa ao fim).
2. Lembrete prático: Codex não navega na internet de forma garantida — pra
   pesquisa web o caminho são as ferramentas locais (pesquisar_google, ler_pagina).

**Sem commit/push — Murillo revisa e decide o que comita.**
