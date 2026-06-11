# research-first

## Objetivo

Pesquisar e entender antes de implementar — evitar refatorações desnecessárias, decisões baseadas em suposições e soluções que já existem no projeto.

## Quando usar

- Antes de criar um novo módulo ou integração
- Quando não sabe onde algo está no codebase
- Quando avaliando uma nova biblioteca ou ferramenta
- Quando Murillo pergunta "qual é a melhor forma de fazer X?"
- Antes de propor uma mudança de arquitetura

## Quando não usar

- Tarefa de execução clara com contexto já conhecido — executar direto
- Correção de bug já identificado — corrigir, não pesquisar
- Criação de arquivo novo sem dependências — criar direto

## Processo (adaptado do ECC deep-research, sem MCPs externos)

### Passo 1 — Entender o objetivo
- O que exatamente precisa ser feito?
- Qual é a restrição mais importante (segurança, performance, simplicidade)?
- Existe algo no projeto que já resolve isso parcialmente?

### Passo 2 — Pesquisar no projeto
```
ctx_search("padrão relevante", "_apps/")
ctx_search("padrão relevante", "_skills/")
ctx_overview("tarefa descrita")
```

### Passo 3 — Mapear o que existe
- Qual arquivo tocaria essa tarefa?
- Qual função já faz algo parecido?
- Existe skill ou doc que cobre isso?

### Passo 4 — Avaliar alternativas
- Opção A: [o que parece óbvio]
- Opção B: [alternativa mais simples]
- Opção C: [fazer nada / usar o que já existe]

### Passo 5 — Recomendar
- Uma recomendação direta com motivo
- Tradeoffs em 1-2 linhas

## Saída esperada

```
Pesquisa: [o que foi investigado]
O que existe: [módulos/docs relevantes encontrados]
Recomendação: [opção concreta]
Motivo: [1 frase]
Tradeoff: [o que se perde com essa escolha]
```

## Riscos

- Pesquisar demais sem decidir → paralisia
- Ignorar o que já existe e reimplementar → duplicação
- Basear a recomendação em suposição sem verificar o código → erro de premissa

## Regra de aprovação

- Pesquisa não requer aprovação — é investigação
- Implementação baseada na pesquisa requer aprovação se afetar código existente

## Regra de log

- Pesquisas significativas → registrar decisão em `_logs/YYYY-MM-DD_[decisao].md`
- Pequenas pesquisas → sem log necessário

## Exemplo bom

```
Murillo: "qual a melhor forma de servir o frontend da Local Interface?"
Javis: [pesquisa o projeto, vê que main.py é CLI puro, sem FastAPI ainda]
Recomendação: FastAPI é a escolha natural para v1 — já tem Python, zero setup extra
Tradeoff: adiciona uma dependência nova (aprovação necessária antes de instalar)
```

## Exemplo ruim

```
Murillo: "qual a melhor forma de servir o frontend?"
Javis: [instala FastAPI direto sem pesquisar o estado atual]
→ ERRADO — implementar sem pesquisar o que já existe
```
