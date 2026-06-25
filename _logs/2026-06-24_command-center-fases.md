# Decisão: Interface do Javis = Chainlit + Command Center (não Dify)

Data: 2026-06-24

## O que foi decidido
- **Não migrar para Dify.** Manter o Javis em Python.
- **Chat operacional** = Chainlit (`app_ui.py`), rodando em **venv isolado Python 3.11** (`.venv_chainlit/`), porta 8001.
- **Command Center** = frontend estático (`frontend/command-center/`), servido pelo `server.py` em `/command-center`, porta 8000.
- **`server.py` também roda no venv 3.11** (não no Python 3.14 global).

## Por quê
- Python 3.14 (global da máquina) é incompatível com `anyio.to_thread.run_sync` usado
  por Starlette/FastAPI em `StaticFiles` (FileResponse `os.stat`) e `run_in_threadpool` →
  `anyio.NoEventLoopError`. Travava o Chainlit (tela branca) e travaria o `server.py`.
  Solução: rodar tudo no venv 3.11, onde a stack funciona.
- Dify acrescentaria um orquestrador externo; o `_brain()` já é um orquestrador testado.
  Chainlit consome o `_brain()` por import direto, sem reescrever nada.

## Como ficou (aditivo, sem refatorar)
- Fase 1: `app_ui.py` (projeto ativo, modos, telemetria, gate de crítico) + `backend/ui_state.py`
  + JSONs em `data/ui/` e `data/projects/`. `_brain()` e `server.py` intocados.
- Fase 2: `frontend/command-center/` (index/styles/app.js), 3 colunas, dados dos JSONs.
- Fase 3: rotas READ-ONLY `/ui/*` no fim do `server.py` + `backend/telemetry_adapter.py`
  (lê o log JSONL do `logger.py`) + mount `/command-center`. `app.js` consome o backend
  com fallback para os JSONs locais.

## Como rodar
```
cd _apps/javis-local-interface
# Backend + Command Center (venv 3.11):
./.venv_chainlit/Scripts/python.exe backend/server.py        # :8000
# Chat (venv 3.11):
./.venv_chainlit/Scripts/python.exe -m chainlit run app_ui.py -w --port 8001
```
- Command Center: http://localhost:8000/command-center/
- Chat: http://localhost:8001

## Próximos passos
- Ligar aprovações reais (`/approvals/pending` + `/approvals/decide`) ao painel direito.
- Expor `brain`/`tools` no log para a telemetria (hoje o logger não grava esses campos).
- Unificar config (projeto/modo/modelo) entre Chat e Command Center.
