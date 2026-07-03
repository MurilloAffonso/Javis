# Modularização do frontend — Fatias 2–4: COMPLETA

**Data:** 2026-07-03 (continuação de `2026-07-02_modularizacao-frontend-fatia1.md`)

## Resultado final
`app.js` do command-center: **2.901 → 364 linhas (−87%)**. As 13 telas agora vivem em
módulos ES próprios; o `app.js` restante é só núcleo: constantes (ICONS/NAV), `state`,
helpers (`$`, `h`, `_esc`, `opEsc`, `sc`, `pct`, `tryJson`, `loadData`, `tele`),
op-helpers compartilhados (`opSend`, `opToast`, `confirmStrong`), sidebar, right panel,
`viewSearch`, router (`setView`/`renderCanvas`) e `init()`.

## Mapa de módulos
```
command-center/
├── app.js                    364L  núcleo + router + sidebar + rightpanel
├── js/
│   ├── voice.js              448L  infra de voz (Orb/Whisper/WakeWord/TTS) → exporta initVoiceStage
│   └── views/
│       ├── vempassear.js     874L  (fatia 1 — 02/07)
│       ├── operacao.js       236L  (fatia 2 — 02/07)
│       ├── chat.js           273L  (fatia 3 — 02/07; importa initVoiceStage)
│       ├── acoes.js          117L  ┐
│       ├── tarefas.js        116L  │
│       ├── conclave.js       103L  │
│       ├── config.js          92L  │ fatia 4 — 03/07
│       ├── rotina.js          75L  │ (10 telas numa tacada,
│       ├── world.js           70L  │  corte por âncoras de texto
│       ├── missoes.js         58L  │  via script Node, não por
│       ├── exec.js            58L  │  número de linha)
│       ├── treino.js          51L  │
│       └── painel.js          49L  ┘
```

## Decisões técnicas
- Constantes usadas por UMA tela foram junto com ela: `SECTORS`→world,
  `WORKFLOW_NODES/LIST`→tarefas, `CFG_MENU`→config, `CMD_SUGGEST`→chat.
- Compartilhados ficaram no núcleo e são exportados: `_esc, h, $, state, BACKEND,
  tryJson, renderCanvas, setView, opToast, opSend, opEsc, confirmStrong, activeAgent,
  pct, sc, projName, tele`.
- Fatia 4 usou script Node com âncoras de texto (regex em conteúdo de linha) em vez de
  `sed` por número — o display do ctx_shell omitia linhas e tornava cortes numéricos
  arriscados. Script falha alto se âncora não bater exatamente 1x.
- Scripts em `scratchpad/split_views.js` e `verify_split.js` (temporários, fora do repo).

## Verificação
- `node --check` OK nos 15 arquivos (import/export removidos p/ check standalone).
- Zero definições/chamadas residuais no app.js; router com as 13 telas via import.
- Sem código module-level dependente do núcleo (sem risco TDZ).
- Fatias 1–3 testadas no navegador por Murillo (aprovadas); fatia 4 aguardando teste.

## Próximo passo
1. Murillo testa as 13 telas no navegador (hard refresh).
2. Commit da modularização (aguardando aprovação — NADA staged ainda).
3. Objetivo real destravado: conectar os ~50 endpoints do backend que a UI não usa
   (tela por tela, agora que cada uma é um arquivo pequeno).
