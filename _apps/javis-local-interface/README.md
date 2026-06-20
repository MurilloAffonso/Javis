# Javis Local Interface — v0

Interface de execução local do Javis. Classifica intenções por palavra-chave e executa
ações seguras no computador de Murillo, sem precisar de LLM para ações rotineiras.

## Iniciar (servidor + interface web)

```powershell
cd _apps/javis-local-interface
python backend/server.py
```

Abra `frontend/index.html` no navegador (ou sirva a pasta), com o backend em `http://127.0.0.1:8000`.

## Estrutura

```
javis-local-interface/
├── backend/
│   ├── command_router.py  — classifica intenção (sem LLM)
│   ├── actions.py         — executa ações locais
│   ├── logger.py          — JSONL em logs/actions.jsonl
│   └── server.py          — API FastAPI (servidor real, usado pela interface web)
├── frontend/
│   ├── index.html         — UI estática
│   ├── style.css
│   └── app.js
├── config/
│   └── commands.yaml      — documentação de intents
└── logs/
    └── actions.jsonl      — histórico de execuções
```

## Segurança

- Ações destrutivas são **bloqueadas** pelo Command Router (risk_level: critical)
- Ações que pedem `requires_approval: true` exigem confirmação explícita antes de executar
- Nenhum shell arbitrário é executado — apenas ações da whitelist em `actions.py`

## Roadmap completo

Ver `_docs/JAVIS-LOCAL-INTERFACE-ROADMAP.md`
