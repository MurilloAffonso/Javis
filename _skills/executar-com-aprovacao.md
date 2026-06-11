# executar-com-aprovacao

## Objetivo

Apresentar uma ação que requer aprovação explícita de Murillo antes de qualquer execução, com contexto claro do que será feito, por que é necessária aprovação e o que pode ser revertido ou não.

## Quando usar

- Command Router retornou `requires_approval: true`
- Murillo pede para "abrir o terminal" ou outra ação de risco médio
- Qualquer ação que modifique estado além da whitelist de baixo risco

## Quando não usar

- `acao_perigosa` (risk_level: critical) — não pedir aprovação, apenas bloquear e logar
- Ações já na whitelist de baixo risco — executam diretamente sem prompt
- Conversas ou perguntas ao LLM — não passam por aprovação

## Entrada esperada

- Resultado do `command_router.route()` com `requires_approval: true`
- Texto original do usuário
- Contexto opcional de por que a ação foi solicitada

## Saída esperada

```
⚠️  Ação solicitada: [descrição clara]
   Intent: [intent]   Risk: [risk_level]
   O que será feito: [ação exata, sem ambiguidade]
   Reversível: [sim/não — e por quê]

Confirmar? (s/N):
```

## Riscos

- Inferir aprovação por contexto ("o usuário parece querer") → nunca fazer
- Executar `acao_perigosa` mesmo com "s" → sempre bloqueado no router
- Omitir o que exatamente será executado → cria confusão e falsa segurança
- Não logar quando aprovação for negada → perde auditoria

## Regra de aprovação

- Aprovação deve ser **explícita**: teclar "s" ou "sim"
- Qualquer outra resposta (Enter, "ok", "pode", silêncio) = negado
- Nunca re-perguntar após negação — aceitar e logar `approved: false`

## Regra de log

- Sempre logar: `approved: true` ou `approved: false`
- Incluir `user_text`, `intent`, `risk_level`, `duration_ms`
- Destino: `logs/actions.jsonl` com `source: "cli"`

## Exemplo bom

```
Murillo: "abre o terminal"
⚠️  Ação solicitada: Abrir terminal PowerShell
   Intent: abrir_terminal   Risk: medium
   O que será feito: subprocess.Popen(["powershell.exe", "-NoExit", ...])
   Reversível: sim — fechar a janela

Confirmar? (s/N): s
✅ Terminal aberto.
```

## Exemplo ruim

```
Murillo: "abre o terminal"
Javis: [abre diretamente sem pedir aprovação]
→ ERRADO — abrir_terminal requer requires_approval: true
```
