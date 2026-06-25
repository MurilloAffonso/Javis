# Progresso do loop noturno — 2026-06-25

Relatório para Murillo ler ao acordar. Cada iteração registra o que foi feito,
resultado dos testes e estado dos serviços.

---

## Iteração 1 — ~01:4x — Ingestão de scripts
- Catalogados **44 scripts** do backend (propósito via docstring) → `data/ui/scripts_registry.json`.
- Adaptador `ui_state.get_scripts()` + rota read-only `GET /ui/scripts`.
- Nova aba **Scripts** no Config do Command Center (44 cards com propósito/funções/classes).
- Serviços: 8000 (backend+command-center) OK, 8001 (chat) OK.
- **Testes: 142 passed.** ✅
- Sem git, sem deleção, tudo aditivo.

## Iteração 2 — Comando de voz (pedido do Murillo)
- Botão 🎙️ no chat do Command Center: grava áudio (MediaRecorder) → `POST /transcribe`
  (OpenAI, chave presente) → `POST /chat` (o `_brain`, que orquestra todos os projetos)
  → resposta **falada** com `POST /tts` (Piper local, grátis — testado, retorna WAV 58KB).
- `sendChat()` refatorado p/ aceitar texto explícito + flag de fala; `speakText()` + `toggleVoice()`.
- UI verificada (botão aparece, sem erros de JS além de favicon).
- **Testes: 142 passed.** ✅
- Loop passa a ser CONTÍNUO (terminou um, entra outro), sem horário fixo.

## Iteração 3 — itens 3,4,5,6 (lote)
- **3 Telemetria rica:** `telemetry_adapter._last_brain()` lê o `brain` da última resposta
  no SQLite (messages); `/ui/telemetry` agora traz `brain` no `last`. Command Center
  mostra **Brain** e **Tools** na aba Métricas (tools captados da conversa ao vivo).
- **4 Aprovações automáticas:** `app_ui.py` — ações com `requires_approval` (risco médio)
  criam um Gate real (`repo.approvals.add`) em vez de executar; aparece no painel direito
  do Command Center pra decidir. Crítico continua bloqueado.
- **5 World interativo:** torre do setor **pulsa** quando há agente executando; **clicar**
  no setor abre o chat do 1º agente.
- **6 Agente clicável:** sidebar/World → abre o Chat do agente (já estava no fluxo).
- Verificação: console **0 erros**, **142 testes passed**, serviços 8000/8001 no ar.

## Iteração 4 — itens 7,8,9,10,11 (lote) — FILA COMPLETA
- **7 Dashboards reais VP:** `ui_state.vp_metrics()` computa de `_data/vp_*.json` →
  manifesto da VP agora traz reservas 1, passeios 1, receita R$3, criativos 2 (dados reais).
- **8 Busca global:** digitar no topo/sidebar mostra `viewSearch` no canvas com
  Agentes/Squads/Skills/Scripts; clicar num agente abre o chat dele.
- **9 Projeto externo real:** `get_projects()` enriquece Cerebro Jampa via `project_registry`
  → card mostra **status "online"** real (path do repo existe).
- **10 Doc:** `COMMAND_CENTER.md` (arquitetura, telas, como rodar, segurança, endpoints).
- **11 Polimento:** consolidado dos ciclos anteriores; **0 erros de console**.
- Verificação: **142 testes passed**, serviços 8000/8001 no ar, Cerebro Jampa online.

>>> BACKLOG 100% CONCLUÍDO. A partir daqui o loop entra em MODO VERIFICAÇÃO:
a cada ciclo faz health-check + testes e mantém os serviços de pé, sem inventar risco.

### Resumo p/ Murillo (manhã)
Tudo pronto e no ar: Command Center completo (Chat+voz, World isométrico, Tarefas,
Painel com KPIs reais, Config com Scripts/Memórias, Atividade com aprovações reais,
busca global). Backend e chat no venv 3.11. Teste o 🎙️ em http://localhost:8000/command-center/.

## Sessão da manhã (Murillo acordado) — itens extras 2,3,4
- **4 Launcher:** `iniciar-javis.bat` + `backend/_run_server.py` — sobe backend + chat
  e abre o Command Center com 1 clique (tudo no venv 3.11).
- **3 Integrações:** rota `/ui/integrations` (status REAL: youtube/telegram/openai/
  claude_code conectados; google/canva/spotify/whatsapp a configurar) + aba **Integrações**
  no Config. Não dispara nada externo.
- **2 Agentes executores reais:** na view Tarefas, selector de agente especialista
  (architect/developer/qa/...) + tarefa → `POST /agents/run` (executa no Claude por
  assinatura, com skill+RAG) e mostra o resultado.
- Verificação: **142 testes passed**, 0 erros de console, serviços no ar.
