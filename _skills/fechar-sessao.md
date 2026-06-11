# Skill: Fechar Sessão de Trabalho no Javis

## Propósito

Encerrar a sessão de forma estruturada: registrar o que foi feito, atualizar o estado,
medir a economia de tokens e definir o próximo passo.

---

## Quando usar

Ao encerrar qualquer sessão de trabalho — especialmente antes de fechar o terminal
ou passar para outro projeto.

---

## O que fazer (passo a passo)

### 1. Registrar decisão no LeanCTX

```
ctx_session(action="decision", content="[o que foi feito + próximo passo]")
```

### 2. Atualizar o arquivo de sessão

Completar o arquivo `_sessoes/YYYY-MM-DD_HHhMM_[slug].md` com:

```markdown
## Trabalho realizado

### Arquivos lidos
- `path/arquivo.py` — motivo

### Arquivos alterados
- `path/arquivo.py` — o que mudou e por quê

### Ferramentas usadas
- LeanCTX: ctx_read (N chamadas), ctx_shell (N), ctx_search (N)
- CodeGraph: codegraph_explore (N chamadas)
- Outros: ...

### Economia de tokens estimada
- lean-ctx gain mostra: X tokens salvos, Y% compressão

### Decisões tomadas
1. ...

## Próximo passo
[uma frase clara — o que Murillo deve fazer ou pedir na próxima sessão]
```

### 3. Atualizar _estado/estado-atual.md

Se o estado do projeto mudou (novo módulo, nova feature, bug corrigido):
- Atualizar a tabela de status
- Atualizar "Sessões recentes"

### 4. Atualizar _estado/proximos-passos.md

- Marcar como `[x]` o que foi concluído
- Adicionar novos próximos passos descobertos na sessão

### 5. Atualizar _logs/token-economy.md

```bash
lean-ctx gain --deep
```

Adicionar nova linha na tabela de "Registro por Sessão" com:
- Data, slug da sessão, estimativa de economia, ferramentas usadas

### 6. Verificar testes (se código foi alterado)

```bash
cd _apps/javis-local-interface
python tests/test_command_router.py
python tests/test_voice_bridge.py
python tests/test_actions.py
python tests/test_logger.py
python tests/test_intent_consistency.py
```

---

## Regras absolutas

- **Não fazer commit** sem aprovação de Murillo — mesmo que tudo esteja verde
- **Não fazer push** — nunca
- **Não apagar arquivos de sessão** — são o histórico do projeto
- **Não alterar dry_run** para false
