# Skill: Abrir Sessão de Trabalho no Javis

## Propósito

Iniciar uma sessão de trabalho de forma estruturada, com contexto carregado e ferramentas prontas.
Garante que cada sessão começa do estado correto e que o trabalho será registrado ao final.

---

## Quando usar

Ao começar qualquer sessão de trabalho no Javis — especialmente antes de mudanças de código,
planejamento, auditorias ou qualquer tarefa que dure mais de 10 minutos.

---

## O que fazer (passo a passo)

### 1. Carregar contexto atual

```
ctx_read("_estado/estado-atual.md", "full")
ctx_read("_estado/proximos-passos.md", "full")
```

### 2. Verificar se há entrada nova

```
ctx_tree("_inbox/", 1)
```

Se houver arquivo em `_inbox/`: ler antes de começar.

### 3. Carregar conhecimento LeanCTX

```
ctx_knowledge(action="wakeup")
```

### 4. Registrar início da sessão

Criar arquivo `_sessoes/YYYY-MM-DD_HHhMM_[slug].md` com:

```markdown
# Sessão — YYYY-MM-DD HH:MM

**Objetivo:** [uma frase]
**Contexto carregado:** estado-atual.md, proximos-passos.md
**Pendências anteriores:** [do proximos-passos.md]

## Trabalho planejado
- [ ] ...
```

### 5. Confirmar ferramentas

- LeanCTX: usar ctx_read/ctx_search/ctx_shell (não Read/Grep/Bash)
- CodeGraph: usar codegraph_explore para localizar código antes de ler
- Regra: ler antes de editar (`ctx_read(path, "full")` antes de qualquer mudança)

---

## Regras absolutas

- **Não fazer commit** sem aprovação de Murillo
- **Não alterar dry_run** para false
- **Não instalar nada** sem aprovação
- **Não alterar execução por voz** sem aprovação
- **Não mexer em Docker/Open WebUI** sem aprovação
