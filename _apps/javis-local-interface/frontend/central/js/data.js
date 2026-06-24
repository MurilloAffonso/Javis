// data.js — dados MOCK da Central de Comando do Javis.
// Fonte: _projetos/vem-passear/VEM_PASSEAR_SQUAD_MAP.md
// Depois, basta trocar este arquivo por fetch() nos endpoints reais (/projects, /agents).

export const KPIS_GLOBAIS = [
  { label: "Receita (semana)", value: "R$ 128k", trend: +23, spark: [4, 6, 5, 8, 7, 9, 11] },
  { label: "Aprovações pendentes", value: "3", trend: 0, tone: "warn" },
  { label: "Squads ativos", value: "9", trend: 0 },
  { label: "Custo IA (dia)", value: "US$ 0,40", trend: -12, tone: "ok" },
];

export const PROJETOS = [
  {
    slug: "vem-passear",
    nome: "Vem Passear Jampa",
    icone: "⛵",
    tipo: "Agência de turismo",
    fase: "Operação",
    status: "online",
    metrica: { label: "Reservas/sem", value: "24" },
    kpis: [
      { label: "Reservas (semana)", value: "24", trend: +9, spark: [12, 14, 11, 18, 16, 20, 24] },
      { label: "CAC / passeio", value: "R$ 72", trend: -8, tone: "ok" },
      { label: "ROAS", value: "3,4x", trend: +6, tone: "ok" },
      { label: "Ocupação", value: "78%", trend: +4 },
    ],
    contexto: { titulo: "🌊 Maré baixa hoje 13h–16h", sub: "☀ Sem risco de remarcação" },
  },
];

// Os 9 squads da Vem Passear (Central é o maestro, não squad).
// fase: atrair | converter | operar | reter | analisar | transversal
export const SQUADS = {
  "vem-passear": [
    {
      id: "atendimento-vendas", nome: "Atendimento & Vendas", icone: "💬",
      area: "trafego", fase: "converter", agente: "humano-no-loop + Claude",
      faz: ["tria WhatsApp/Direct", "qualifica (passeio/data/nº pessoas)", "consulta preço+vaga", "monta rascunho de resposta e fechamento", "registra lead no CRM"],
      nao_faz: ["enviar sozinho → Murillo envia", "inventar vaga → Operação", "dar desconto → Oferta"],
      input: "mensagens recebidas + catálogo + vagas (Operação) + CRM",
      output: "rascunho pronto p/ Murillo + reserva no CRM → Operação/Dados",
      ferramentas: ["WhatsApp", "templates-whatsapp.md", "vp_clientes.json", "Claude"],
      metricas: [
        { label: "1ª resposta", value: "4 min", trend: -20, tone: "ok" },
        { label: "Conversa→reserva", value: "31%", trend: +5 },
        { label: "Ticket médio", value: "R$ 148", trend: +3 },
      ],
      rotina_diaria: "triar conversas → rascunhos → atualizar CRM → passar reservas pra Operação",
      rotina_semanal: "revisar motivos de 'não fechou' → realimenta Oferta e Conteúdo",
      aprovacao: "Toda mensagem enviada · reserva com pagamento · qualquer desconto",
    },
    {
      id: "conteudo", nome: "Conteúdo", icone: "🎨",
      area: "conteudo", fase: "atrair", agente: "Claude assinatura",
      faz: ["define pauta (máx. 2 venda/10)", "gancho 3s + formato", "copy no tom caloroso/local", "CTAs padrão (MARÉ/COMBO/SEIXAS)"],
      nao_faz: ["gerar arte final → plugin/Estúdio", "publicar → Tráfego", "rodar anúncio"],
      input: "briefing (maré/agenda/vagas/fotos) + trends + decisão do Analista",
      output: "pauta-semana.md → Criativo/Distribuição",
      ferramentas: ["linha-editorial.md", "Claude", "plugin Adobe/Canva (arte)"],
      metricas: [
        { label: "Pauta s/ retrabalho", value: "82%", trend: +7 },
        { label: "Alcance→clique WA", value: "6,1%", trend: +2 },
        { label: "Salvamentos", value: "340", trend: +18 },
      ],
      rotina_diaria: "capturar 1 gancho do dia (maré/clima) pra story",
      rotina_semanal: "montar pauta da semana → submeter ao Gate 1",
      aprovacao: "Gate 1 (pauta) antes de produzir · Gate 2 (arte) — só via plugin",
    },
    {
      id: "trafego", nome: "Tráfego Pago", icone: "📈",
      area: "trafego", fase: "atrair", agente: "humano-no-loop + Claude",
      faz: ["monta estrutura de campanha (Meta/Google)", "sugere segmentação e verba", "otimiza (pausa/escala)", "marca posts p/ impulsionar"],
      nao_faz: ["criar arte → Conteúdo/plugin", "gastar verba sozinho → Murillo", "escrever copy → Conteúdo"],
      input: "peças aprovadas (Gate 2) + objetivo + budget + métricas (Dados)",
      output: "campanhas configuradas + recomendação escala/corte → Dados",
      ferramentas: ["Meta Business Suite", "Meta Ads", "Google Ads", "planilha"],
      metricas: [
        { label: "CAC / passeio", value: "R$ 72", trend: -8, tone: "ok" },
        { label: "ROAS", value: "3,4x", trend: +6, tone: "ok" },
        { label: "CPL", value: "R$ 18", trend: -4, tone: "ok" },
      ],
      rotina_diaria: "ler métricas → ajustes dentro do orçamento já aprovado",
      rotina_semanal: "propor escala/corte (Escalar/Manter/Matar) → pedir verba",
      aprovacao: "QUALQUER verba ou aumento de budget · subir campanha nova",
    },
    {
      id: "operacao", nome: "Operação dos Passeios", icone: "⛵",
      area: "operacao", fase: "operar", agente: "Claude + humano-no-loop",
      faz: ["confere maré/clima por passeio", "consolida vagas por saída/embarcação", "monta lista de embarque", "confirma com parceiros", "aciona remarcação quando inviável"],
      nao_faz: ["vender/atender → Vendas", "cancelar sozinho → Murillo", "fechar parceria → Parcerias"],
      input: "reservas confirmadas + tábua de maré + previsão + agenda + capacidade dos parceiros",
      output: "confirmação/ajuste de saída + lista de embarque + alerta de remarcação → Vendas/Dados",
      ferramentas: ["tábua de maré", "previsão do tempo", "agenda de saídas", "contatos de parceiros"],
      metricas: [
        { label: "Ocupação/embarcação", value: "78%", trend: +4 },
        { label: "Saídas s/ incidente", value: "97%", trend: +1, tone: "ok" },
        { label: "Remarcações/clima", value: "2", trend: 0, tone: "warn" },
      ],
      rotina_diaria: "checar maré+clima de amanhã → confirmar vagas → sinalizar risco",
      rotina_semanal: "fechar grade de saídas com parceiros · capacidade vs demanda",
      aprovacao: "Remarcar/cancelar por clima · overbooking · trocar embarcação",
    },
    {
      id: "pos-venda", nome: "Pós-venda & Avaliações", icone: "⭐",
      area: "retencao", fase: "reter", agente: "Claude",
      faz: ["rascunho de agradecimento + pedido de review (GMN/IG)", "identifica recompra/indicação", "sinaliza insatisfação"],
      nao_faz: ["enviar sozinho → Murillo", "responder review público sem OK", "prometer brinde → Oferta"],
      input: "lista de quem fez passeio (Operação/CRM) + reviews recebidos",
      output: "rascunhos de follow-up + lista de recompra + alertas → Vendas/Dados",
      ferramentas: ["Google Meu Negócio", "WhatsApp", "vp_clientes.json", "Claude"],
      metricas: [
        { label: "Avaliações 5★/sem", value: "11", trend: +22 },
        { label: "Nota GMN", value: "4,9", trend: 0, tone: "ok" },
        { label: "Recompra", value: "18%", trend: +3 },
      ],
      rotina_diaria: "listar passeios concluídos → rascunho agradecimento+review",
      rotina_semanal: "reativar inativos · revisar e responder reviews (com OK)",
      aprovacao: "Envio de mensagem · resposta pública a review · cortesia/desconto",
    },
    {
      id: "dados", nome: "Dados & Receita", icone: "📊",
      area: "dados", fase: "analisar", agente: "Claude",
      faz: ["consolida números (reservas/ads/WA/GMN/site)", "calcula CAC/LTV/ROAS/payback/margem por passeio", "monta Painel de Receita", "aponta gargalos"],
      nao_faz: ["inventar dado (sinaliza buraco)", "rodar campanha", "escrever copy", "decidir sozinho → Murillo decide"],
      input: "fontes (CRM, Meta/Google Ads, GMN, site, planilha de saídas)",
      output: "Painel de Receita + decisões priorizadas → Ritual Semanal/briefing",
      ferramentas: ["planilhas", "SQLite/Supabase", "Claude", "dashboard HTML"],
      metricas: [
        { label: "Receita (semana)", value: "R$ 128k", trend: +23 },
        { label: "LTV:CAC", value: "3,2x", trend: +5, tone: "ok" },
        { label: "Payback", value: "42 d", trend: -6, tone: "ok" },
      ],
      rotina_diaria: "atualizar números do dia (reservas, gasto de ads)",
      rotina_semanal: "fechar painel + ranking de passeios → abrir o Ritual",
      aprovacao: "Nunca executa — só entrega; Murillo decide as recomendações",
    },
    {
      id: "parcerias", nome: "Parcerias", icone: "🤝",
      area: "oferta", fase: "transversal", agente: "Claude + humano-no-loop",
      faz: ["mapeia parceiros (pousadas/hotéis/guias/lanchas)", "rascunho de proposta", "controla comissões e reservas por parceria"],
      nao_faz: ["fechar acordo sozinho → Murillo", "atender cliente do parceiro → Vendas", "preço fora de tabela → Oferta"],
      input: "lista de parceiros + demanda (Dados/Operação) + condições atuais",
      output: "proposta + planilha de ativos + reservas por parceria → Vendas/Operação/Dados",
      ferramentas: ["CRM de parceiros (planilha)", "WhatsApp", "Claude"],
      metricas: [
        { label: "Parceiros ativos", value: "7", trend: +1 },
        { label: "Reservas/parceria", value: "5", trend: +2 },
        { label: "Receita/parceiro", value: "R$ 1,2k", trend: +9 },
      ],
      rotina_diaria: "registrar/encaminhar reservas vindas de parceiros",
      rotina_semanal: "revisar quem trouxe/esfriou → propor ação (rascunho)",
      aprovacao: "Fechar/alterar acordo · definir comissão · condição especial",
    },
    {
      id: "site-seo", nome: "Site & SEO", icone: "🌐",
      area: "inteligencia", fase: "transversal", agente: "Claude",
      faz: ["mantém site + GMN (descrições/fotos/horários)", "SEO local ('piscinas naturais João Pessoa')", "garante site→WhatsApp"],
      nao_faz: ["rodar tráfego pago → Tráfego", "criar arte → plugin", "inventar preço → fonte da verdade"],
      input: "catálogo atualizado + termos de busca + métricas do site/GMN",
      output: "site/GMN atualizados + recomendações SEO + páginas por passeio → Aquisição/Vendas",
      ferramentas: ["site (Vercel/HTML)", "Google Meu Negócio", "Search Console", "Claude"],
      metricas: [
        { label: "Posição GMN local", value: "#2", trend: +1, tone: "ok" },
        { label: "Tráfego orgânico", value: "1,8k", trend: +14 },
        { label: "Site→WhatsApp", value: "9,3%", trend: +2 },
      ],
      rotina_diaria: "conferir que site/GMN refletem disponibilidade real",
      rotina_semanal: "revisar 1 página de passeio por SEO + fotos/reviews no GMN",
      aprovacao: "Mudança estrutural no site · alterar GMN · mudar preço exibido",
    },
    {
      id: "oferta", nome: "Oferta & Promoções", icone: "🏷️",
      area: "oferta", fase: "transversal", agente: "Claude + humano-no-loop",
      faz: ["desenha combos (ex.: Litoral Norte + Areia Vermelha)", "promoções por sazonalidade", "ajusta p/ ocupação ociosa", "define a regra de desconto"],
      nao_faz: ["publicar → Conteúdo/Tráfego", "aprovar a própria margem → Murillo", "atender → Vendas"],
      input: "ocupação+margem (Dados) + sazonalidade + capacidade ociosa (Operação)",
      output: "tabela de combos + regra de desconto → Vendas/Conteúdo/Tráfego/Site",
      ferramentas: ["catálogo", "planilha de margem", "Claude"],
      metricas: [
        { label: "Conversão de combo", value: "27%", trend: +6 },
        { label: "Ticket médio", value: "R$ 148", trend: +3 },
        { label: "Ocupação baixa temp.", value: "61%", trend: +11, tone: "ok" },
      ],
      rotina_diaria: "sinalizar saída ociosa de amanhã → oferta relâmpago",
      rotina_semanal: "calendário sazonal → propor promoção da semana (com margem)",
      aprovacao: "SEMPRE — toda promoção/combo/desconto afeta margem",
    },
  ],
};

export const APROVACOES = [
  { id: "a1", tipo: "Pauta", projeto: "Vem Passear", squad: "Conteúdo 🎨", contexto: "Pauta da semana (5 posts) pronta pra produção", previa: "3 educativos · 2 de venda (MARÉ/COMBO)", tone: "warn" },
  { id: "a2", tipo: "Verba", projeto: "Vem Passear", squad: "Tráfego 📈", contexto: "Escalar campanha Areia Vermelha (ROAS 4,1x)", previa: "+ R$ 200 / dia", tone: "warn" },
  { id: "a3", tipo: "Remarcação", projeto: "Vem Passear", squad: "Operação ⛵", contexto: "Saída de amanhã 14h sob risco de maré alta", previa: "Remarcar 8 reservas p/ sábado", tone: "danger" },
];

export const PROXIMOS_PASSOS = {
  agora:      [{ t: "Aprovar pauta da semana", squad: "Conteúdo" }],
  proximo:    [{ t: "Escalar Areia Vermelha", squad: "Tráfego" }, { t: "Reativar inativos 30d", squad: "Pós-venda" }],
  depois:     [{ t: "Combo Litoral Norte + Areia Vermelha", squad: "Oferta" }, { t: "Página SEO Pôr do Sol do Jacaré", squad: "Site & SEO" }],
  concluido:  [{ t: "Painel de receita da semana", squad: "Dados" }],
};

// Métricas que decidem vs vaidade (tela de Métricas)
export const METRICAS = {
  receita: [
    { label: "Receita", value: "R$ 128k", trend: +23, spark: [80, 92, 88, 104, 110, 119, 128] },
    { label: "CAC", value: "R$ 72", trend: -8, tone: "ok" },
    { label: "LTV", value: "R$ 540", trend: +5 },
    { label: "ROAS", value: "3,4x", trend: +6, tone: "ok" },
    { label: "Payback", value: "42 d", trend: -6, tone: "ok" },
  ],
  vaidade: [
    { label: "Likes", value: "3,1k" },
    { label: "Alcance", value: "48k" },
    { label: "Seguidores", value: "12,4k" },
  ],
};

export const FASES = [
  { id: "atrair", nome: "Atrair" },
  { id: "converter", nome: "Converter" },
  { id: "operar", nome: "Operar" },
  { id: "reter", nome: "Reter" },
  { id: "analisar", nome: "Analisar" },
];

// cor por área (usada nos nós de squad)
export const COR_AREA = {
  conteudo: "var(--ai)", trafego: "var(--accent)", operacao: "var(--ok)",
  retencao: "var(--warn)", dados: "var(--ai)", oferta: "var(--accent)",
  inteligencia: "var(--ok)",
};
