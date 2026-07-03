# Pacote 4 — miúdos: fecha a auditoria de endpoints órfãos

**Data:** 2026-07-03

## O que foi decidido
Conectar os últimos endpoints da auditoria (pacote 4), encerrando a varredura de
órfãos. Escolha de Murillo: "pacote 4".

## Conexões
1. **Perfil** (Config › Perfil) — era "em construção". Agora `GET /profile` →
   `{facts:[str]}` → lista o que o Javes sabe sobre Murillo. `else if perfil`.
2. **Memória** (Config › Memórias) — abaixo dos KPIs, campo de busca →
   `GET /memory?q=` → `{results: <texto>}` (recall) ou decisões recentes (sem q).
   Enter busca; carrega recentes ao abrir.
3. **Causa raiz** (Tarefas) — novo card "🔍 Causa raiz": tarefa + resposta ruim →
   `POST /rootcause {task, failed_response}` → `{diagnosis, learned}` renderizado.
4. **Upload** — JÁ estava ligado (chat.js `uploadChatFile` → POST /upload multipart,
   📎 no chat). Nada a fazer.

## Verificação
- Sintaxe OK nos 13 arquivos; router intacto; deps fechadas.
- Smoke test live: `/profile` devolve fatos reais; `/memory` devolve decisões do
  Conclave. Shapes conferidos: facts=[str], results=texto, rootcause={diagnosis,learned}.

## Status da auditoria: FECHADA
Pacotes 2 (VP real), 1 (ciclo de vida), 3 (conhecimento) e 4 (miúdos) conectados.
Os endpoints que restam no server.py são internos/infra (ui/*, brain/*, voice/*,
v1/* compat OpenAI, tts, transcribe) — não são "órfãos de UI", têm uso próprio ou
não pedem botão.

## Próximo passo
1. Murillo testa (Config›Perfil, Config›Memórias, Tarefas›Causa raiz).
2. Commit.
3. Fase "operar, não construir": usar o fluxo-dinheiro da VP numa semana real.
