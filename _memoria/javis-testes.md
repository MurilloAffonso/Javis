---
tags: [memoria, testes, pytest, javis]
---

# Estado dos Testes

**Data:** 2026-06-11
**Resultado:** 189/189 passando ✓

## Arquivos de teste

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_command_router.py` | roteamento de intents | command_router.py |
| `test_voice_bridge.py` | pipeline de voz | voice_bridge.py |
| `test_actions.py` | whitelist de ações | actions.py |
| `test_logger.py` | logs JSONL | logger.py |
| `test_intent_consistency.py` | router ↔ commands.yaml | ambos |

## Como rodar

```bash
cd _apps/javis-local-interface
python -m pytest tests/ -v
```

## test_intent_consistency.py

Parser manual de YAML (PyYAML não disponível). Verifica:
- Todos os intents do `RISK_MAP` estão em `commands.yaml`
- `risk_level` e `requires_approval` batem entre os dois
- Actions do `ACTION_MAP` batem com `commands.yaml`

**Divergência conhecida (não falha, apenas WARN):**
- `abrir_projeto` ausente em `frontend/app.js` — próximo passo: adicionar

## Próximo passo nos testes

Ao adicionar/remover intents: atualizar `command_router.py` (autoritativo) + `commands.yaml` (espelho) + `frontend/app.js` (espelho).

---
Relacionado: [[javis-arquitetura]] · [[javis-protocolo]] · [[JAVIS-CEREBRO]]
