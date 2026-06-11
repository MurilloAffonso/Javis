# Skill: Revisar Logs de Voz do Javis

## Propósito

Analisar o log JSONL de voz de um determinado dia e produzir um relatório de auditoria:
quais comandos foram detectados, quais foram bloqueados, quais foram hallucinations,
quais ficaram sem classificação e o que pode ser melhorado no roteador.

**Esta skill é de leitura somente.** Nunca executa ações, nunca altera logs, nunca libera dry_run.

---

## Entrada

Fornecer um dos dois:

```
data: 2026-06-11
```

ou

```
data: ontem
```

ou o caminho direto:

```
caminho: _apps/javis-local-interface/logs/actions-2026-06-11.jsonl
```

---

## O que fazer (passo a passo)

### 1. Localizar o arquivo

```
_apps/javis-local-interface/logs/actions-YYYY-MM-DD.jsonl
```

Se "ontem": calcular a data (hoje - 1 dia) e compor o nome do arquivo.

Se o arquivo não existir: informar que não há logs para a data informada.

### 2. Ler e agrupar por intent

Para cada linha do JSONL:
- Decodificar o JSON
- Agrupar por campo `intent`
- Contar ocorrências

### 3. Produzir o resumo

#### 3a. Totais por intent

```
abrir_youtube       : N ocorrências
status_sistema      : N ocorrências
conversa            : N ocorrências
desconhecido        : N ocorrências
acao_perigosa       : N ocorrências
blocked_hallucination: N ocorrências
...
```

#### 3b. Comandos executados (would_execute=true)

Listar intent + user_text original + normalized_text para cada evento com `would_execute: true`.

#### 3c. Comandos perigosos bloqueados (risk_level=critical)

Listar user_text + intent + note para cada evento com `risk_level: "critical"`.

#### 3d. Hallucinations bloqueadas

Listar user_text + note para cada evento com `note: "blocked_hallucination"`.

#### 3e. Intents desconhecidos

Listar user_text + normalized_text para cada evento com `intent: "desconhecido"`.

#### 3f. Possíveis falsos positivos

Identificar casos onde:
- `intent` foi atribuído mas `normalized_text` sugere algo diferente
- Frases muito curtas foram classificadas como comando (< 3 palavras)
- `confidence` < 0.5 mas intent foi classificado como comando

### 4. Recomendações

Com base nos dados acima, sugerir:
- Keywords novas para o command_router (para intents desconhecidos recorrentes)
- Ajustes no limiar de hallucination se muitos bloqueios legítimos ocorreram
- Frases que deveriam ser `conversa` mas foram classificadas como comando
- Frases que deveriam ser comando mas foram para `desconhecido`

### 5. Próximos testes sugeridos

Listar 3-5 frases que deveriam ser testadas com base no log analisado.

---

## Formato de saída

```markdown
## Revisão de Logs de Voz — YYYY-MM-DD

**Total de eventos:** N
**Período:** HH:MM - HH:MM (UTC)

### Resumo por intent
| Intent | Ocorrências | would_execute |
|--------|------------|---------------|
| ...    | N          | sim/não       |

### Comandos executados
- "frase original" → intent (normalized: "frase limpa")

### Bloqueados — perigosos
- "frase" → acao_perigosa — note: ...

### Bloqueados — hallucination
- "frase" (N palavras de comando detectadas)

### Desconhecidos
- "frase" → desconhecido (normalized: "frase limpa")

### Possíveis falsos positivos
- "frase" classificada como intent mas parece ser conversa

### Recomendações
1. ...

### Próximos testes sugeridos
- "frase para testar"
```

---

## Regras absolutas

- **Leitura somente** — nunca modificar nenhum arquivo de log
- **Não alterar** `dry_run`, `would_execute`, ou qualquer variável de execução
- **Não executar** nenhuma ação local ou remota
- **Não deletar** logs antigos
- **Não fazer** commit, push ou git add
- Se o arquivo de log não existir, informar e encerrar sem erro
