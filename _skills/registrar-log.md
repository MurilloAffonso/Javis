# registrar-log

## Objetivo

Registrar um evento de ação no arquivo `_apps/javis-local-interface/logs/actions.jsonl` com o formato padrão JSONL do Javis Local Interface.

## Quando usar

- Após qualquer ação executada via Command Router
- Quando Murillo pede para "logar" ou "registrar" uma ação manualmente
- Para auditoria de ações executadas

## Formato do registro

```json
{
  "timestamp": "2026-06-10T22:00:00.000Z",
  "source": "cli",
  "user_text": "texto original do comando",
  "intent": "abrir_youtube",
  "risk_level": "low",
  "requires_approval": false,
  "approved": null,
  "action_result": "ok",
  "message": "YouTube aberto.",
  "error": null,
  "duration_ms": 120
}
```

## Campos obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| timestamp | ISO 8601 UTC | Quando ocorreu |
| source | string | "cli", "frontend" ou "voz" |
| user_text | string | Texto original do usuário |
| intent | string | Intent classificado |
| risk_level | string | critical/medium/low/none |
| action_result | string | ok/error/blocked/cancelled/llm |

## Processo

1. Verificar se `logs/actions.jsonl` existe — criar se necessário
2. Montar o dict com os campos obrigatórios
3. Fazer `json.dumps(record, ensure_ascii=False)` + `\n`
4. Append ao arquivo (nunca sobrescrever)
5. Confirmar: "✅ Logado: [intent] — [action_result]"

## Regras

- Sempre append, nunca overwrite
- ensure_ascii=False para preservar português
- Nunca logar senhas, tokens ou dados pessoais
