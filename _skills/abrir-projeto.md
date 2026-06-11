# abrir-projeto

## Objetivo

Abrir a pasta de um projeto específico do Javis no Explorer ou no VS Code, com base no nome mencionado por Murillo.

## Quando usar

- Murillo diz "abre o projeto X", "abrir projeto Y"
- Intent classificado como `abrir_projeto` pelo Command Router

## Processo

1. Identificar o nome do projeto no texto do usuário
2. Procurar em `_projetos/` por um arquivo `.md` ou pasta com nome similar
3. Se encontrado: abrir a pasta correspondente (`os.startfile`) ou VS Code (`code .`)
4. Se não encontrado: listar os projetos disponíveis em `_projetos/`

## Lookup de projetos

```
_projetos/
├── [nome-do-projeto].md   — contexto do projeto
```

Extrai o campo "pasta:" ou "path:" do frontmatter se existir. Caso contrário,
usa `JAVIS_ROOT` como fallback.

## Saída esperada

- "✅ Abrindo projeto [nome] em [caminho]"
- "❌ Projeto '[nome]' não encontrado. Projetos disponíveis: [lista]"

## Regras

- Só abre pastas dentro de `C:\Users\noteacer\Desktop\javis` ou subpastas conhecidas
- Nunca navega para fora do Javis sem aprovação explícita
- Máximo de 3 linhas de resposta
