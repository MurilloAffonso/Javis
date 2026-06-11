# Javis Local Interface — v0

Interface de execução local do Javis. Classifica intenções por palavra-chave e executa
ações seguras no computador de Murillo, sem precisar de LLM para ações rotineiras.

## Iniciar (CLI)

```powershell
cd _apps/javis-local-interface
python backend/main.py
```

## Estrutura

```
javis-local-interface/
├── backend/
│   ├── command_router.py  — classifica intenção (sem LLM)
│   ├── actions.py         — executa ações locais
│   ├── logger.py          — JSONL em logs/actions.jsonl
│   └── main.py            — loop CLI
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
