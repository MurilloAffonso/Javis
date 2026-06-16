# Análise Estratégica — Vem Passear Jampa
*Produzido autonomamente pelo Javis/Claude na madrugada de 2026-06-14, enquanto Murillo dormia.*
*O Conclave automático (Ollama local) deu timeout — então o debate Crítico/Advogado/Sintetizador abaixo foi escrito por mim (Claude) diretamente, com mais qualidade.*

---

## 1. Leitura do projeto (o que existe hoje)

**Negócio (Vem Passear Jampa):** agência de turismo certificada Cadastur em João Pessoa/PB.
Catálogo robusto e real (fonte: `cerebro-jampa/_conhecimento/catalogo_vempassear_estruturado.md`):
- **Piscinas Naturais** (Seixas, Picãozinho, Penha) — R$60, catamarã, dependem de maré baixa
- **Litoral Norte** (clássico R$80, Areia Vermelha R$70, combo R$160, Pôr do Sol do Jacaré R$90, lancha R$1.590+)
- **Litoral Sul** (clássico R$80, combos com quadriciclo R$240–330)
- **City Tour** R$80, **Interestaduais** (Porto de Galinhas/Pipa/Natal) R$160, **Pacotes** R$140–700
- **Mídias:** 811 MB organizados por passeio em `VemPassearJampa-Midias` (fotos/vídeos/textos reais)

**Ativos digitais:** Instagram @vempassearjampa (662 seg., reels de até ~2k views), WhatsApp Business
com catálogo, perfil aberto 24h. Site em planejamento (skill `lovable-site-builder`).

**Diagnóstico central:** o negócio vende BEM no presencial, mas o digital está parado.
Não falta produto, estrutura, nem conteúdo bruto. Falta **máquina de aquisição ligada**:
tráfego entrando → resposta rápida → reserva. Tudo o resto é detalhe perto disso.

---

## 2. Debate (Claude consigo mesmo — 3 vozes)

### 🔴 Crítico — onde o plano pode furar
1. **R$100 é pouco pra testar 3 canais.** Instagram + Google Ads + Google Meu Negócio ao mesmo
   tempo dilui a verba e nenhum gera dado conclusivo. Foco demais vira foco nenhum.
2. **Maré como eixo único é frágil.** Em maré alta a oferta-isca (piscinas) some. Precisa de uma
   oferta "à prova de maré" (Pôr do Sol do Jacaré, City Tour, Litoral Sul) pros dias sem piscina.
3. **Painel sem operação por trás é vaidade.** Gerar conteúdo bonito não fecha venda; quem fecha é
   resposta em <5min e cobrança de sinal. O painel só vale se reduzir o tempo de resposta.

### ⚔️ Advogado — suposições não verificadas
1. **"Tem gente procurando piscinas naturais em JP."** Verdade — mas sazonal. Junho é baixa
   temporada relativa; o pico é dez–fev e julho. Precisa medir CPL antes de declarar vitória.
2. **"O reel de 2k views converte em venda."** Views ≠ intenção de compra. Reel viralizou por
   estética; precisa de criativo com PREÇO e CTA explícito pra atrair quem quer COMPRAR, não só ver.
3. **"Responder rápido basta pra fechar."** Não — fecha quem pede o sinal sem medo. O gargalo
   psicológico costuma ser o vendedor hesitar em pedir o Pix. Roteiro de fechamento resolve isso.

### ✅ Sintetizador — a decisão robusta
Junta o que é válido: **um canal, uma oferta principal, uma oferta reserva, e fechamento agressivo.**
- **Canal único v1:** Instagram impulsionado (objetivo Mensagens no WhatsApp). É onde o ativo
  (reels) já performa e o CPL tende a ser menor que Google em turismo.
- **Oferta principal:** Piscinas R$60 nos dias de maré boa. **Oferta reserva:** Pôr do Sol do
  Jacaré R$90 (diário, independe de maré, experiência única/instagramável) nos dias de maré alta.
- **Google Meu Negócio:** ativar JÁ (grátis) — review de todo cliente presencial é o maior trunfo
  de SEO local e custa R$0.
- **Fechamento:** script de 3 mensagens terminando em Pix de sinal (não negociável).
- **Painel:** serve pra (a) gerar a linha editorial e (b) controlar passeios/leads. Nada de
  integração pesada antes de a aquisição provar caixa.

---

## 3. Plano priorizado (próximos 30 dias)

**Semana 1 — Ligar a máquina (R$100)**
1. Ativar/otimizar Google Meu Negócio (grátis) + subir fotos da pasta de mídias.
2. Impulsionar o reel campeão → R$20/dia × 5 dias, objetivo Mensagens, oferta Piscinas R$60.
3. Salvar os 3 scripts de WhatsApp como Respostas Rápidas. Meta: responder < 5 min.
4. Planilha diária: gasto | conversas | vendas | faturamento.

**Semana 2 — Ler os dados e dobrar no que funciona**
5. Se CPL < R$5 e ≥1 venda: manter e reinvestir o lucro. Se não: trocar criativo/oferta.
6. Postar 1 conteúdo/dia (linha editorial pronta) alternando piscinas (maré boa) e Pôr do Sol
   (maré alta).

**Semana 3-4 — Estruturar pra escalar**
7. Subir a primeira página de passeio do site (Seixas) — já há skill e dados prontos.
8. Começar a coletar reviews no Google sistematicamente (presencial → QR code → review).
9. Avaliar 2º canal (Google Ads "passeio piscinas naturais joão pessoa") só se o IG saturar.

---

## 4. O que o Javis/Painel deve virar (visão sóbria)
- **Hoje:** painel local que gera conteúdo (com catálogo real) e controla passeios/leads. ✅ já feito.
- **Fase 2 (quando houver volume):** captura automática de lead do WhatsApp (Cloud API oficial),
  agenda de passeios com tábua de maré, biblioteca de conteúdo reutilizável.
- **Nunca:** virar um fim em si mesmo. O painel é ferramenta de venda, não o produto.

> **Frase-guia:** o Javis não vende passeio — o Jampa vende. Cada hora de código só se justifica
> se encurtar o caminho entre o lead e o Pix.
