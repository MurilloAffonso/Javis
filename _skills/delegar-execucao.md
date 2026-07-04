# Skill: Delegar Execução pro Codex

## O quê
Detecta automaticamente tarefas de execução (programação, testes, refatoração) e as
delega pro Codex (seu "segundo programador") em vez de o Claude fazer tudo.
**O Claude é o cérebro (arquitetura/raciocínio); o Codex são as mãos (execução).**

## Por quê
Economia de cota do Claude. Você paga pelo Claude (assinatura); Codex é outra
assinatura que já tem. Deixa o raciocínio caro no Claude, execução no Codex.
O Claude audita o resultado do Codex depois (via `_audit_after_codex`).

## Como ativa
```bash
# No seu shell, antes de rodar o Javis:
set JAVIS_AUTO_CODEX=1

# Ou via Claude Code:
export JAVIS_AUTO_CODEX=true
```

**Default:** desligado (`JAVIS_AUTO_CODEX=0` ou não definida).

## O que dispara delegação

### Atalho (zero LLM, rápido) — tarefas óbvias
Verbo inequívoco no começo/meio da tarefa:
- "**programa** uma função que..." ✓ delegado
- "**implementa** o algoritmo de..." ✓ delegado
- "**refatora** o arquivo X" ✓ delegado
- "**roda** os testes do projeto" ✓ delegado
- "**cria** o arquivo main.py" ✓ delegado
- "**corrige** o bug na linha 42" ✓ delegado
- "**testa** a integração" ✓ delegado

### Via classificador (LLM leve) — tarefas ambíguas
Se a tarefa não bate no atalho, o Claude classifica leve:
- Input: "Analisando o projeto, você vê que o módulo X precisa refatoração. Faça."
- Classificador marca `response_type: "code"` ou `brain: "exec"`
- Resultado: roteia pro Codex

### NÃO delega (Claude mantém) — raciocínio
- "qual é a melhor arquitetura para..." ✗ Claude fica
- "explica como este código funciona" ✗ Claude fica
- "monta um plano pra..." ✗ Claude fica
- "analisa este log e diz o que significa" ✗ Claude fica

## Guardrails (automáticos)

Toda tarefa delegada chega ao Codex com este preâmbulo:
```
⚠️ GUARDRAILS:
- Não faça `git commit` nem `git push` — deixe as mudanças no working tree para revisão.
- Trabalhe na pasta do projeto...
```

**Por quê:** seu `CLAUDE.md` é rígido em segurança. Codex mexe nos arquivos, mas
commit/push continuam manuais. O Claude audita tudo depois.

## Fluxo completo

```
Você fala: "programa uma função que..."
         ↓
should_delegate() vê "programa" ✓
         ↓
delegacao.montar_brief() monta: objetivo + guardrails
         ↓
brain_switch.dispatch(brief, engine="codex")
         ↓
code_agent roda: codex exec <brief> (working tree, streaming)
         ↓
_audit_after_codex (Claude audita resultado e te notifica)
```

## Customizar (editar esta skill)

Para mudar quais verbos disparam delegação, edite a lista `EXEC_VERBS` em
`backend/delegacao.py` — depois rode os testes:

```bash
pytest tests/test_delegacao.py -v
```

Se adicionar um verbo, a skill não precisa atualizar (o código é a fonte-da-verdade).

## Debugging

**Ver se está ativo:**
```bash
python -c "import os; print(os.environ.get('JAVIS_AUTO_CODEX', 'não definida'))"
```

**Forçar Claude mesmo com tarefa de execução:**
```bash
set JAVIS_AUTO_CODEX=0
# rodar Javis normalmente
```

**Ver o brief que vai pro Codex:**
Rode os testes em `tests/test_delegacao.py::test_montar_brief_*` — eles mostram
exatamente o que o Codex recebe.
