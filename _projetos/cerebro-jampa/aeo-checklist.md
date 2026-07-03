# AEO — Answer Engine Optimization (ser recomendado pela IA)

> Minerado dos agentes `ai-citation-strategist` e `agentic-search-optimizer` (The Agency),
> aterrado na Vem Passear Jampa. Complementa `seo-checklist.md`/`seo-plano.md`.
> **Problema que resolve:** quando um turista pergunta ao ChatGPT/Gemini/Perplexity
> *"o que fazer em João Pessoa"* ou *"passeio de barco nas piscinas naturais"*, a Vem
> Passear precisa **aparecer e ser citada** — não basta ranquear no Google.

## Por que é diferente de SEO
SEO mira **ranquear links**. AEO mira ser **sintetizado e citado na resposta da IA**.
Os sinais mudam: menos backlink, mais **clareza de entidade, FAQ estruturada, schema
e conteúdo que casa com o padrão da pergunta**.

## Checklist (ordem de prioridade)

### 1. Entidade clara e consistente
- [ ] Nome, endereço, telefone (NAP) idênticos no site, Google Business, Instagram, redes.
- [ ] Uma frase-âncora repetida em todo lugar: *"Vem Passear Jampa — passeios de barco
      nas piscinas naturais de João Pessoa (Seixas, Picãozinho, Areia Vermelha)."*
- [ ] Google Business Profile completo e verificado (a IA lê isso).

### 2. FAQ com schema (o que mais move o ponteiro)
- [ ] Página de FAQ respondendo às perguntas REAIS que turista faz:
      "quanto custa", "quanto tempo dura", "precisa saber nadar", "tem para criança",
      "qual a melhor maré/horário", "onde é o ponto de encontro", "cancela se chover".
- [ ] Marcar com `FAQPage` schema (JSON-LD) — a IA extrai resposta direto do markup.
- [ ] Resposta curta e factual primeiro (a IA cita o primeiro parágrafo).

### 3. Guias de destino que casam com o prompt
- [ ] Artigo *"O que fazer em João Pessoa: piscinas naturais"* — estrutura de resposta
      (lista, prós, preço médio, melhor época), não texto publicitário.
- [ ] Comparativo honesto *"Seixas x Picãozinho x Areia Vermelha"* — IA adora comparativo.
- [ ] `Product`/`TouristTrip`/`Offer` schema nos passeios (preço, duração, o que inclui).

### 4. Medir citação
- [ ] Mensalmente, perguntar em ChatGPT/Gemini/Perplexity: *"melhores passeios de barco
      em João Pessoa"*, *"o que fazer nas piscinas naturais de JP"*. Anotar: a Vem Passear
      aparece? Quais concorrentes aparecem? O que eles têm que você não tem?
- [ ] Fechar o gap do concorrente citado (geralmente: FAQ + guia + reviews).

### 5. Reviews e sinais sociais
- [ ] Volume e recência de avaliações no Google (a IA pondera isso como confiança).
- [ ] Depoimentos com texto (não só estrela) mencionando os passeios pelo nome.

## Fase 3 (futuro) — WebMCP / ação executável
Quando o site tiver reserva online, declarar as ações via `data-mcp-*` (WebMCP) para que
um agente de IA (ex: Claude no Chrome) consiga **reservar**, não só recomendar. Só faz
sentido depois que existir fluxo de reserva no site. Marcar como backlog.

## Dono no squad
Encaixa na missão *Cérebro Jampa — SEO*. O **Analista** mede citação mensal; a **Nova**
produz FAQ/guia; execução de schema é técnica (site Next.js do Cérebro Jampa).
