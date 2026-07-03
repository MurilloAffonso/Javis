# Minimalismo da interface — 4 cortes no command-center

**Data:** 2026-07-03 (logo após a modularização completa)

## O que foi decidido
Enxugar a interface removendo o que era decorativo/bloqueado, mantendo tudo que tem
backend real. Critério: **decorativo/fake sai, funcional fica.** Aprovado por Murillo
(os 4 cortes; fusões Exec/Rotina ficaram pra segunda rodada, se ainda parecer cheio).

## Cortes executados
1. **World (menu)** — tela decorativa (mapa isométrico), zero chamadas ao backend.
   Arquivo movido pra `_arquivo/command-center-views/world.js` (git mv, histórico
   preservado — regra do projeto: não deletar).
2. **Ações (menu)** — catálogo estático com todos os botões desabilitados. Movido pra
   `_arquivo/command-center-views/acoes.js`. O conteúdo (mapa endpoint × risco ×
   confirmação) virou doc: **`_arquitetura/catalogo-acoes-risco.md`** — vai guiar a
   fase de conexão de endpoints.
3. **Demos da tela Tarefas** — seções "Workflows" (botões "em breve") e "Fluxo
   (exemplo)" (grafo hardcoded) removidas; `WORKFLOW_NODES/LIST` deletados. Ficaram as
   4 ferramentas reais: demanda (/chat), agente (/agents/run), pulso (/pulso),
   navegador (/browser/run). Subtítulo atualizado.
4. **Abas legado da VP** — 4 chips (Passeios/Clientes/Conteúdos/Pauta · legado) e as 8
   funções `vp*`/`vpCreate*` correspondentes removidas (~163 linhas). Aba Agentes
   ficou. Imports `opSend`/`confirmStrong` limpos (sem uso restante na VP).

## Bônus
- **Bug corrigido:** `tarefas.js` chamava `renderRightPanel()` sem importar
  (ReferenceError engolido por catch silencioso desde a extração). Agora o núcleo
  exporta `renderRightPanel` e a Tarefas importa.

## Resultado
- Menu: 13 → **11 itens** (sem World e Ações).
- VP: 15 → **11 chips**.
- Tarefas: metade da tela era demo; agora só ferramenta real.
- vempassear.js: 874 → 711 → ~715 linhas; tarefas.js: 116 → ~85.

## Próximo passo
1. Murillo testa (menu, Tarefas, VP) e aprova.
2. Commit (aguardando aprovação).
3. Fase seguinte: conectar endpoints órfãos usando `_arquitetura/catalogo-acoes-risco.md`
   como guia de risco/confirmação.
