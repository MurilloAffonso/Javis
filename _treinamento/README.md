# _treinamento — onde o Javis aprende

Pasta onde Murillo despeja material (vídeo, link, repositório, PDF, transcrição)
para os agentes absorverem conhecimento por área. O Javis indexa o que cai em
`_resumos/` no RAG (`knowledge.py`) — então qualquer resumo aqui vira busca
semântica disponível pro chat e pros agentes (`buscar_conhecimento`).

## Áreas

| Pasta | Quem usa | Foco |
|-------|----------|------|
| `vendas/` | Khan, Phantom, Hunter, LNS, Nero | objeções, scripts, qualificação de lead, follow-up |
| `conteudo/` | Vera, Nova, Atlas | reels, copy, SEO, referências visuais, tendências |
| `tecnico/` | Javis core / Codex | engenharia, arquitetura, ferramentas novas (ex: NotebookLM, OpenWA) |
| `estrategia/` | Orion, Titan | orquestração, modelo de negócio, expansão |

Cada área tem duas subpastas:

- **`_entrada/`** — Murillo joga aqui o material bruto: link de vídeo (.txt/.md com a URL),
  PDF, transcrição, link de repositório do GitHub. Sem processamento ainda.
- **`_resumos/`** — onde entra o resumo já processado (hoje: colado manualmente do
  NotebookLM; futuro: via API/plugin quando existir). Isso AQUI é o que entra no RAG.

## Fluxo hoje (manual, sem API do NotebookLM)

1. Murillo cola o link/arquivo em `<área>/_entrada/`.
2. Murillo sobe o mesmo material no NotebookLM (conta já existente — ver
   `_logs/` para status de conexão).
3. Murillo cola o resumo gerado pelo NotebookLM em `<área>/_resumos/AAAA-MM-DD-titulo.md`.
4. Endpoint `/knowledge/reindex` (ou reindexação automática por mtime no startup)
   pega esse `.md` e ele passa a valer pra busca semântica e pros agentes.

## Fluxo futuro (quando NotebookLM tiver API/plugin acessível)

Substituir o passo 2-3 manual por automação: o Javis decide quando está "ocioso",
varre `_entrada/` por itens novos, envia para o NotebookLM, recebe o resumo e
grava direto em `_resumos/` sem Murillo precisar copiar/colar. Ver
`_logs/2026-06-17_orquestracao-noturna.md` para o estado dessa investigação.

## Não fazer

- Não apagar nada em `_entrada/` — é o material bruto, fonte da verdade do que foi ensinado.
- Não inventar resumo se o NotebookLM não tiver processado ainda — deixar vazio é melhor que alucinar.
