# Visão: Javis passa a ler imagem e PDF-diagrama — 19/06

## Recomendação (modo mega) e por quê

Murillo pediu pra eu recomendar o melhor reajuste pra fazer agora gastando token.
Escolhi DAR VISÃO ao Javis — porque era exatamente onde ele travou hoje: o
Fluxograma é um diagrama (imagem em PDF), o markitdown não lê, e o
`analisar_arquivo` morria. Desbloqueia o 80/20 dele de verdade.

## O que foi feito

- **`claude_brain.answer`**: novo parâmetro `add_dirs` → passa `--add-dir` pro
  Claude headless poder LER arquivos fora da pasta do projeto (ex.: Downloads).
  Read continua liberado; Bash/Edit/Write seguem bloqueados → leitura segura.
- **`file_analyzer.py`**:
  - Novo caminho de VISÃO (`_analyze_visual`): manda o CAMINHO do arquivo pro
    `claude_brain` com um system prompt de analista visual; o Claude ABRE o
    arquivo com a própria ferramenta de leitura (enxerga imagem E PDF) e
    descreve. Pra fluxograma, mapeia o fluxo passo a passo.
  - `analyze()`: imagem (`.png/.jpg/...`) vai direto pra visão; PDF/doc cujo
    texto não dá pra extrair também cai na visão.
  - **Bug raiz corrigido em `_to_markdown`**: o markitdown falhava e o fallback
    antigo (`read_text errors='replace'`) vomitava os BYTES CRUS do PDF como se
    fossem texto (192 mil chars de `%PDF-1.7...`), então o arquivo nunca era
    reconhecido como "sem texto" e mandava lixo binário pro cérebro. Agora
    `_to_markdown` detecta `%PDF`/conteúdo majoritariamente binário e retorna ""
    (→ cai na visão); o último recurso usa `errors='strict'` (binário falha em
    vez de virar lixo).

## Verificação (ao vivo, real)

- CLI da assinatura confirmada funcionando (`claude -p "ok"` → exit 0) — o
  "sem cérebro" do 1º teste era o bug do binário, NÃO cota esgotada.
- `_to_markdown(Fluxograma.pdf)` agora → "" (antes: 192514 chars de lixo).
- `file_analyzer.analyze(Fluxograma.pdf, ...)` → `status:ok, modo:visao`, 72-82s,
  6304 chars de análise REAL do diagrama: mapeou as raias (Criação de Conteúdo,
  Designer, Tráfego, Copy), o fluxo C.S → P.CN → planejamento → aprovação do
  cliente → P.MKT → Design, com as etapas e aprovações. Exatamente a "gestão de
  marketing, como gerir e por onde passa" que ele pediu lá no começo.
- Deliverable salvo em `_outbox/fluxograma-analise-marketing.md`.
- `pytest tests/ -q` → 71 passed.

## Nota
Latência da visão ~75-80s (Opus lendo o arquivo). Aceitável pra análise de
documento (não é voz). Custo conhecido da assinatura.

**Sem commit/push — Murillo revisa e decide.**
