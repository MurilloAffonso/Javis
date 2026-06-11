# comando-de-voz-local

## Objetivo

Processar um texto de comando local e retornar a ação mapeada pelo Command Router, sem executar nada sem aprovação explícita. Útil quando Murillo ditar um comando pelo sandbox de voz e quiser saber o que será feito antes.

## Quando usar

- Murillo dita um comando e pede "o que você faria com isso?"
- Antes de integrar o sandbox de voz ao Command Router (fase futura)
- Para testar novas regras de roteamento sem rodar o CLI

## Processo

1. Receber o texto do comando
2. Simular o `route()` do `command_router.py` com as mesmas regras de palavra-chave
3. Retornar o JSON de roteamento com intent, risk_level, requires_approval, action, reason
4. Se `requires_approval: true`, avisar Murillo antes de sugerir qualquer execução
5. Nunca executar ações diretamente — só mostrar o que seria feito

## Saída esperada

```json
{
  "intent": "abrir_youtube",
  "confidence": "high",
  "risk_level": "low",
  "requires_approval": false,
  "action": "open_url",
  "reason": "palavra-chave 'youtube' detectada"
}
```

Seguido de: "Para executar: `python _apps/javis-local-interface/backend/main.py`"

## Regras

- Sem LLM para classificar — só palavras-chave (igual ao router em Python)
- Nunca sugerir execução de `acao_perigosa`
- Máximo de 5 linhas de resposta além do JSON
