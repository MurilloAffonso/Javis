# Vem Passear Jampa — Mapa Operacional em Squads (dentro do Javis)

> Instância do Squad Contract (`_docs/arquitetura-javis-os.md`) para o 1º projeto
> plugado. Agência de passeios em João Pessoa/PB. Data: 2026-06-23.
> Regra-mãe: nunca inventar preço/horário/vaga — sempre da FONTE DA VERDADE
> (catálogo VP). WhatsApp = Javis monta rascunho, Murillo envia.

## Catálogo (fonte da verdade — referência)
Piscinas: Seixas · Picãozinho · Areia Vermelha · (Penha) — dependem de MARÉ baixa.
Roteiros: Litoral Sul · Litoral Norte · City Tour · Pôr do Sol do Jacaré (Bolero ao vivo).
Bate-volta/outros estados: Pipa · Natal · Porto de Galinhas.
Aventura: Quadriciclo em Coqueirinho (Litoral Sul).
Canais: WhatsApp · Instagram · Google Meu Negócio · Site · Tráfego pago · Indicações · Parcerias.

---

## 1. CENTRAL DO PROJETO (núcleo VP — não é squad, é o maestro)
- **Papel:** o Javis (Jamba) orquestrando a VP. Roteia pedidos, guarda contexto
  (catálogo, maré, agenda, CRM), aciona o squad certo, cobra métricas, segura os gates.
- **Fonte da verdade:** catálogo (passeios/preços/horários), tábua de maré, agenda
  de saídas, CRM (`vp_clientes.json`).
- **Decide:** qual squad ativar, quando subir pro Conselho (decisão pesada), quando
  PARAR e pedir Murillo.
- **Nunca:** publica, gasta verba, confirma reserva ou envia WhatsApp sozinho.

---

## 2. SQUAD ATENDIMENTO E VENDAS  💬  (área: trafego/conversao)
- **Faz:** lê mensagens do WhatsApp/Direct; qualifica (passeio, data, nº pessoas);
  consulta disponibilidade e preço na fonte da verdade; monta RASCUNHO de resposta
  e de fechamento; registra lead no CRM.
- **Não faz:** enviar mensagem sozinho (→ Murillo envia); inventar preço/vaga
  (→ consulta Operação); dar desconto fora de tabela (→ Squad Oferta).
- **Input:** mensagens recebidas + catálogo + vagas (Operação) + CRM.
- **Output:** rascunho de resposta pronto pro Murillo + lead/reserva no CRM →
  alimenta Operação e Dados.
- **Ferramentas:** WhatsApp, templates-whatsapp.md, `vp_clientes.json`, Claude.
- **Métricas:** tempo de 1ª resposta · taxa conversa→reserva · ticket médio · nº leads/dia.
- **Rotina diária:** triar conversas novas → rascunhos de resposta → atualizar CRM →
  passar reservas confirmadas pra Operação.
- **Rotina semanal:** revisar motivos de "não fechou" → realimentar Oferta e Conteúdo.
- **Aprovação humana:** TODA mensagem enviada (rascunho→Murillo); confirmar reserva
  com pagamento; qualquer desconto.

## 3. SQUAD CONTEÚDO  🎨  (área: conteudo)
- **Faz:** define pauta (pilares, máx. 2 de venda a cada 10); cria gancho 3s, formato
  e copy no tom caloroso/local; usa CTAs padrão (MARÉ/COMBO/SEIXAS).
- **Não faz:** gerar a arte final (→ vai pro plugin/Estúdio); publicar (→ Distribuição/
  Tráfego); rodar anúncio.
- **Input:** briefing da semana (maré, agenda, vagas, fotos) + tendências (pesquisa) +
  decisão do Analista.
- **Output:** pauta-semana.md (posts com dia, pilar, formato, gancho, legenda, CTA,
  hashtags) → alimenta Criativo e Distribuição.
- **Ferramentas:** linha-editorial.md, Claude assinatura. **Arte só via plugin Adobe/Canva.**
- **Métricas:** % pauta aprovada sem retrabalho · alcance→clique WhatsApp · salvamentos.
- **Rotina diária:** capturar 1 gancho do dia (maré/clima/sazonal) pra story.
- **Rotina semanal:** montar pauta da semana → submeter ao Gate 1.
- **Aprovação humana:** **Gate 1 (pauta)** antes de produzir; **Gate 2 (arte)** —
  criativo só via plugin.

## 4. SQUAD TRÁFEGO PAGO  📈  (área: trafego)
- **Faz:** monta estrutura de campanha (Meta/Google); sugere segmentação e verba;
  otimiza (pausa o que não converte, escala o que paga); marca posts orgânicos com
  potencial de impulsionar.
- **Não faz:** criar a arte (→ Conteúdo/plugin); definir/gastar verba sozinho
  (→ Murillo); escrever a copy do post (→ Conteúdo).
- **Input:** peças aprovadas (Gate 2) + objetivo + budget aprovado + métricas (Dados).
- **Output:** campanhas configuradas + recomendação de escala/corte → alimenta Dados.
- **Ferramentas:** Meta Business Suite, Meta Ads, Google Ads, planilha.
- **Métricas:** CAC por passeio · ROAS · CPL · CTR · custo por conversa WhatsApp.
- **Rotina diária:** ler métricas das campanhas ativas → ajustes pequenos (público,
  criativo) dentro do orçamento já aprovado.
- **Rotina semanal:** propor escala/corte (ritual Escalar/Manter/Matar) → pedir verba.
- **Aprovação humana:** QUALQUER verba ou aumento de budget; subir campanha nova.

## 5. SQUAD OPERAÇÃO DOS PASSEIOS  ⛵  (área: operacao)
- **Faz:** confere maré/clima por passeio; consolida vagas por saída/embarcação;
  monta lista de embarque; confirma com parceiros (catamarãs/lanchas/vans); aciona
  remarcação quando maré/clima inviabiliza (piscinas só na maré baixa).
- **Não faz:** vender/atender (→ Vendas); decidir cancelar/remarcar sozinho
  (→ Murillo); fechar parceria nova (→ Parcerias).
- **Input:** reservas confirmadas (Vendas) + tábua de maré + previsão do tempo +
  agenda de saídas + capacidade dos parceiros.
- **Output:** confirmação/ajuste de cada saída + lista de embarque + alerta de
  remarcação → alimenta Vendas (avisar cliente) e Dados (ocupação).
- **Ferramentas:** tábua de maré, previsão do tempo, agenda/planilha de saídas,
  contatos de parceiros.
- **Métricas:** ocupação por embarcação · % saídas sem incidente · nº remarcações
  por clima · antecedência média de confirmação.
- **Rotina diária:** checar maré+clima do dia seguinte → confirmar saídas e vagas →
  sinalizar risco de remarcação.
- **Rotina semanal:** fechar grade de saídas da semana com parceiros; revisar
  capacidade vs demanda por passeio.
- **Aprovação humana:** remarcar/cancelar por clima; aceitar overbooking; mudar
  embarcação/parceiro de uma saída.

## 6. SQUAD PÓS-VENDA E AVALIAÇÕES  ⭐  (área: retencao)
- **Faz:** após o passeio, monta rascunho de mensagem de agradecimento + pedido de
  avaliação (Google Meu Negócio/Instagram); identifica clientes pra recompra/indicação;
  sinaliza insatisfação pra Murillo agir rápido.
- **Não faz:** enviar sozinho (→ Murillo); responder review público sem aprovação;
  prometer brinde/desconto (→ Oferta).
- **Input:** lista de quem fez passeio (Operação/CRM) + reviews recebidos.
- **Output:** rascunhos de follow-up + lista de recompra/indicação + alertas de
  insatisfação → alimenta Vendas e Dados.
- **Ferramentas:** Google Meu Negócio, WhatsApp, `vp_clientes.json`, Claude.
- **Métricas:** nº avaliações 5★/semana · nota média GMN · taxa de recompra · taxa de
  indicação · tempo de resolução de reclamação.
- **Rotina diária:** listar passeios concluídos no dia → rascunho de agradecimento+review.
- **Rotina semanal:** campanha de reativação de inativos (rascunho) → revisar reviews
  e responder (com aprovação).
- **Aprovação humana:** envio de qualquer mensagem; resposta pública a review;
  oferta de cortesia/desconto de retenção.

## 7. SQUAD DADOS E RECEITA  📊  (área: dados/painel)
- **Faz:** consolida números (reservas, ads, WhatsApp, GMN, site); calcula CAC, LTV,
  ROAS, payback e margem POR PASSEIO; monta o Painel de Receita; aponta gargalos e o
  que move dinheiro.
- **Não faz:** inventar/estimar dado faltante (sinaliza buraco); rodar campanha;
  escrever copy; decidir sozinho (recomenda → Murillo decide).
- **Input:** fontes (CRM, Meta/Google Ads, GMN, site, planilha de saídas).
- **Output:** Painel de Receita + decisões priorizadas → alimenta o Ritual Semanal e
  o briefing da semana seguinte.
- **Ferramentas:** planilhas, Supabase/SQLite, Claude, dashboard (HTML).
- **Métricas (as que decidem):** Receita · CAC · LTV · ROAS · Payback · margem/passeio ·
  ocupação. (Vaidade — likes/alcance/seguidores — fica fora da decisão.)
- **Rotina diária:** atualizar números do dia (reservas, gasto de ads).
- **Rotina semanal:** fechar o painel + ranking de passeios por receita/margem → abrir
  o Ritual de decisão.
- **Aprovação humana:** nunca executa — só entrega; Murillo decide sobre as recomendações.

## 8. SQUAD PARCERIAS  🤝  (área: oferta/distribuicao)
- **Faz:** mapeia e organiza parceiros (pousadas, hotéis, guias, lanchas, receptivos);
  monta rascunho de proposta/condição; controla comissões e reservas vindas de parceria.
- **Não faz:** fechar acordo/comissão sozinho (→ Murillo); atender o cliente final do
  parceiro (→ Vendas); definir preço fora de tabela (→ Oferta).
- **Input:** lista de parceiros + demanda por passeio (Dados/Operação) + condições atuais.
- **Output:** rascunho de proposta + planilha de parceiros ativos + reservas por
  parceria → alimenta Vendas, Operação e Dados.
- **Ferramentas:** CRM de parceiros (planilha), WhatsApp, Claude.
- **Métricas:** nº parceiros ativos · reservas via parceria · receita por parceiro ·
  comissão paga vs receita gerada.
- **Rotina diária:** registrar/encaminhar reservas vindas de parceiros.
- **Rotina semanal:** revisar parceiros (quem trouxe reserva, quem esfriou) → propor
  ação (rascunho de contato).
- **Aprovação humana:** fechar/alterar acordo; definir/alterar comissão; condição
  especial de preço.

## 9. SQUAD SITE E SEO  🌐  (área: aquisicao)
- **Faz:** mantém site e Google Meu Negócio (descrições, fotos, horários, passeios);
  otimiza SEO local ("passeio piscinas naturais João Pessoa", "Areia Vermelha"); garante
  que o site leva pro WhatsApp; sugere conteúdo de busca.
- **Não faz:** rodar tráfego pago (→ Tráfego); criar arte (→ plugin); inventar
  preço/horário (→ fonte da verdade).
- **Input:** catálogo atualizado + termos de busca + métricas do site/GMN.
- **Output:** site/GMN atualizados + recomendações de SEO + páginas por passeio →
  alimenta Aquisição e Vendas.
- **Ferramentas:** site (Vercel/HTML), Google Meu Negócio, Search Console, Claude.
- **Métricas:** posição no GMN local · tráfego orgânico · conversão site→WhatsApp ·
  cliques "como chegar"/ligar no GMN.
- **Rotina diária:** conferir que site/GMN refletem disponibilidade real (saídas, vagas).
- **Rotina semanal:** revisar 1 página de passeio por SEO + atualizar fotos/reviews no GMN.
- **Aprovação humana:** publicar mudança estrutural no site; alterar dados do GMN;
  mudar preço exibido.

## 10. SQUAD OFERTA E PROMOÇÕES  🏷️  (área: oferta)
- **Faz:** desenha combos (ex.: Litoral Norte + Areia Vermelha) e promoções por
  sazonalidade (alta dez–fev/julho; baixa); ajusta para ocupação (encher saída ociosa);
  define a regra de desconto que os outros squads seguem.
- **Não faz:** publicar a promoção (→ Conteúdo/Tráfego); aprovar a própria margem
  (→ Murillo); atender (→ Vendas).
- **Input:** ocupação e margem por passeio (Dados) + sazonalidade + capacidade ociosa
  (Operação).
- **Output:** tabela de combos/promoções + regra de desconto vigente → alimenta Vendas,
  Conteúdo, Tráfego, Site.
- **Ferramentas:** catálogo, planilha de margem, Claude.
- **Métricas:** conversão de combo · ticket médio · ocupação em baixa temporada ·
  margem após desconto.
- **Rotina diária:** sinalizar saída ociosa de amanhã que pede empurrão (oferta relâmpago).
- **Rotina semanal:** revisar calendário sazonal → propor promoção da semana (com margem).
- **Aprovação humana:** SEMPRE — toda promoção/combo/desconto novo afeta margem e precisa
  do Murillo antes de virar regra.

---

## MAPA TEXTUAL (pronto pra virar interface visual)

```
                         ┌──────────────────────────────┐
                         │   CENTRAL VEM PASSEAR (Javis) │
                         │  catálogo · maré · agenda · CRM│
                         └───────────────┬───────────────┘
                                         │ roteia · cobra · segura gates
   ┌───────────────┬──────────────┬──────┴───────┬──────────────┬───────────────┐
   ▼ ATRAIR        ▼ ATRAIR       ▼ CONVERTER     ▼ OPERAR       ▼ RETER          ▼ ANALISAR
┌─────────┐   ┌──────────┐   ┌──────────────┐ ┌────────────┐ ┌────────────┐  ┌────────────┐
│ CONTEÚDO│   │ TRÁFEGO  │   │ ATENDIMENTO  │ │ OPERAÇÃO   │ │ PÓS-VENDA  │  │ DADOS &    │
│   🎨    │──▶│ PAGO 📈  │──▶│ & VENDAS 💬  │▶│ PASSEIOS ⛵│▶│ AVALIAÇÕES⭐│─▶│ RECEITA 📊 │
└────┬────┘   └────┬─────┘   └──────┬───────┘ └─────┬──────┘ └─────┬──────┘  └─────┬──────┘
     │ pauta       │ campanhas      │ reserva       │ vagas        │ reviews        │ painel
     │ (Gate 1/2)  │ (verba)        │ (rascunho WA) │ (remarcação) │ (recompra)     │ decide
     └─────────────┴────────────────┴───────────────┴──────────────┴────────────────┘
                                         │ realimenta (decisão da semana → briefing)
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼ TRANSVERSAIS (apoiam todo o funil)                               ▼
   ┌──────────┐        ┌──────────────┐        ┌──────────────────┐
   │ PARCERIAS│        │ SITE & SEO   │        │ OFERTA &         │
   │   🤝     │        │   🌐         │        │ PROMOÇÕES 🏷️     │
   └──────────┘        └──────────────┘        └──────────────────┘

LEGENDA DE FLUXO:  CONTEÚDO+TRÁFEGO atraem → VENDAS converte (rascunho, Murillo envia)
→ OPERAÇÃO entrega o passeio (maré/clima/vagas) → PÓS-VENDA retém (review/recompra)
→ DADOS lê tudo e decide → vira briefing da semana seguinte.
GATES HUMANOS: pauta · arte(plugin) · verba · envio de WhatsApp · remarcação ·
promoção/desconto · acordo de parceria · mudança no site/GMN.
```

## Ritual semanal (fecha o ciclo)
Dados consolida → ranking de passeios por receita/margem → Escalar (o que converte) /
Manter / Matar (anúncio/oferta que não paga) → vira o briefing da próxima semana →
Murillo aprova o pacote.
