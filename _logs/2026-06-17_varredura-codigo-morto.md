# Varredura de código morto — 17/06

## O que foi decidido

Auditoria de todos os módulos do backend (`_apps/javis-local-interface/backend/`)
procurando o que não é importado/executado por nada. Resultado e ações:

- **`memory_bridge.py`** — `save_with_embedding()`/`semantic_search()` nunca tiveram
  dado real (`_memoria/embeddings.jsonl` nunca existiu); `recall()` sempre caía no
  fallback por palavra-chave. Removidos os dois métodos mortos e o
  `EMBEDDINGS_FILE`; `recall()` agora é só keyword, sem a ilusão de busca semântica
  que nunca rodou. A busca semântica real do projeto é o `knowledge.py` (RAG com
  998 chunks indexados), que já cobre `_memoria/`.
- **`voice_elevenlabs.py`** — apagado. Zero referência em código, e ElevenLabs foi
  cancelado por decisão do Murillo (ver `_estado/proximos-passos.md`).
- **`main.py`** — apagado. CLI v0 superado pelo `server.py` (FastAPI) + frontend web;
  ninguém rodava. `README.md` atualizado para instruir `python backend/server.py`.
- **`codex_orchestrator.py` / `.ps1`** — apagados. Não estava agendado em lugar
  nenhum, e fazia `git add -A` + `git commit` automático ao concluir uma tarefa —
  violava a regra do CLAUDE.md de nunca commitar sem aprovação (já tinha sido
  evitado deliberadamente numa sessão anterior por esse motivo, ver
  `_logs/2026-06-17_orquestracao-noturna.md`). `codex_backlog.md` e
  `ARQUITETURA.md` atualizados.

## Por quê

Murillo pediu uma varredura ("doctor") pra tirar memória/código que não está sendo
usado, e qualquer projeto/script que esteja parado sem rodar.

## Alternativas consideradas

- Manter `codex_orchestrator.py` só tirando o auto-commit: descartado — Murillo
  preferiu apagar de vez.
- Manter `main.py` como CLI de emergência: descartado — Murillo preferiu apagar.

## Verificação

`python -c "import server"` limpo + `pytest tests/` → 71/71 depois de cada etapa
(antes e depois das remoções).

## Próximo passo

Nenhum follow-up de limpeza pendente. Foco volta pra Frente 3 (voz), como já
estava priorizado em `_estado/proximos-passos.md`.

**Sem commit/push — Murillo revisa e decide o que comita.**
