# Arquitetura Javis OS — orquestrador central + projetos plugáveis

> Inspirada na lógica estrutural do blueprint COHORT
> (`_docs/blueprint-cohort-marketing-os.md`), mas ancorada no que o Javis JÁ tem
> (`project_registry.py`, `vp_squad.py`, `conclave.py`, gates). Não é cópia — é a
> formalização do grafo de agentes do Javis. Data: 2026-06-23.

## Peça central reutilizável: o SQUAD CONTRACT
Todo squad de qualquer projeto é o MESMO contrato (estende o schema já usado em
`vp_squad.py`, somando os 3 campos que faltavam: métricas, responsável, aprovação):

```yaml
squad:
  id: slug-unico
  nome: "Nome humano"
  area: inteligencia|oferta|conteudo|design|trafego|dados|painel
  agente_responsavel: qual cérebro/persona executa (ex.: Claude assinatura, Gemini, Conclave)
  funcao:   o que FAZ (1-3 verbos)
  nao_faz:  o que NÃO faz → delega para <outro squad>
  input:    o que consome (e de quem)
  output:   o que entrega (→ alimenta <outro squad>)
  ferramentas: [tools concretas]
  metricas: como se mede o sucesso DESTE squad
  aprovacao_humana: gatilho exato em que PARA e pede OK ao Murillo (ou "nunca")
```
O `nao_faz` é o mecanismo anti-caos (vem do blueprint). O `aprovacao_humana` é o
gate por-squad (vem do pipeline de 3 gates que o Javis já tem).

---

## BLOCO A — Núcleo Central do Javis (o Kernel)
Jamba é o orquestrador. O núcleo NÃO executa trabalho de projeto — ele roteia,
lembra, decide e cobra. Camadas reais:

- **Roteamento** — `command_router.py` (intent por palavra-chave, sem LLM) +
  fast-path.
- **Cérebro/cascata** — `agent.respond()`: conversa leve → Gemini grátis;
  pesado → Claude assinatura → OpenAI → Claude API → Gemini → OpenRouter.
- **Tool-gating** — `_gate_tools()` libera só as ferramentas do contexto.
- **Memória** — RAG (`knowledge.py`, indexa o vault) + perfil (`profile.py`) +
  estado (`_estado/`, `javis.db`).
- **Aprovação** — gates (Pauta→Estúdio→Distribuição) com SQLite + Journey Log.
- **Telemetria** — custo/token sanitizados (`_log_usage`).

O Kernel é o "VOCÊ + AI Head" do blueprint, fundidos: estratégia + roteamento.

## BLOCO B — Conselheiros Estratégicos
Camada consultiva (decide, não executa) — já existe como **Conclave**
(`conclave.py`, tool `consultar_especialistas`) + os 17 agentes da mente.

Formalizar como **personas com lógica de decisão explícita** (não "treinar clones"
— capacidade = SKILL.md + cérebro forte):
- **Estrategista de Oferta** — "a oferta sai da gaveta?" (lógica Hormozi).
- **Guardião de Métrica** — "isso move receita ou é vaidade?" (lógica Kaushik).
- **Leitor de Funil** — "onde está o gargalo?" (lógica AARRR/McClure).
- **Crítico / Advogado / Sintetizador** — o Conclave atual (audita / ataca / integra).

Acionados só em decisão pesada (gatilho `_is_heavy_request` / `use_conclave`).

## BLOCO C — Squads Globais do Javis (transversais a TODO projeto)
Vivem no núcleo e servem qualquer projeto plugado. São templates de squad:

| Squad global | Área | Função | Aprovação |
|---|---|---|---|
| **Inteligência** | inteligencia | pesquisa, concorrentes, trends | nunca (read-only) |
| **Conteúdo** | conteudo | pauta + copy na voz da marca | antes de publicar |
| **Design** | design | criativos (só via plugin Adobe/Canva) | antes de publicar |
| **Tráfego** | trafego | campanhas: criar/otimizar/escalar | subir verba / escalar |
| **Dados** | dados | consolida métricas, lê funil | nunca (read-only) |
| **Painel** | painel | dashboard + recomendação | nunca (entrega) |
| **Coders** (infra) | execucao | Claude Code / Codex executam código | edição de arquivo/commit |
| **Memória** (infra) | memoria | indexa vault, lembra fatos | nunca |

Um projeto **herda** esses templates e os especializa com seus dados.

## BLOCO D — Como projetos são plugados
Modelo **registry/pointer** (`project_registry.py`): o Javis APONTA pro projeto,
não absorve. Plugar um projeto = fornecer 3 coisas no repo dele:

1. **Manifesto** (`projeto.json`): nome, empresa, fase_atual, modelo_ia,
   validacao, contato_responsavel.
2. **Manifesto de skills/squads** (`skills.json`): lista de squads ativos, cada um
   no Squad Contract (id, categoria/área, papel, risco/aprovação).
3. **Fonte da verdade** (1 arquivo): o dado canônico do projeto (catálogo, preços).

O Javis lê (nunca escreve no repo do projeto), instancia os squads globais com os
dados do projeto, e expõe via `/agents`/`/projects`. Adicionar projeto novo = novo
registro no `REGISTRY` + esses 3 arquivos. Zero código novo de núcleo.

## BLOCO E — Estrutura do projeto Vem Passear dentro do Javis
VP é o **primeiro grafo instanciado**. Hoje vive parcialmente em `vp_squad.py` +
`vp_store.py` + `_data/vp_*.json`. Formalizar como projeto plugado:

- **Manifesto:** empresa=Vem Passear Jampa, fase=operação de conteúdo+conversão.
- **Fonte da verdade:** catálogo real (passeios, preços, horários) — NUNCA inventar.
- **Squads:** os 5 abaixo (Bloco F).
- **Dados:** `vp_passeios.json`, `vp_conteudos.json`, `vp_pauta.json`,
  `vp_clientes.json` (CRM).
- **Gates:** Pauta (Gate 1) → Estúdio (Gate 2) → Distribuição (Gate 3).
- **Canais:** WhatsApp, Google Meu Negócio, Instagram, Meta Ads.

## BLOCO F — Squads específicos da Vem Passear (Squad Contract completo)
Estende os 5 reais de `vp_squad.py` com métricas + responsável + aprovação:

**1. Olheiro 🔭 (inteligência)**
- responsável: Gemini/Claude · funcao: capta trends/áudios de turismo que bombam
- nao_faz: criar conteúdo (→ Nova) · input: semana + pilares editoriais
- output: 3-5 referências → alimenta Nova · tools: IG/TikTok busca, pesquisar_redes
- metricas: nº de trends acionáveis aproveitadas · aprovacao: nunca (read-only)

**2. Nova 🎨 (conteúdo)**
- responsável: Claude assinatura · funcao: pauta (pilares, máx 2 venda/10) + copy no tom local
- nao_faz: gerar arte (→ Estúdio) / subir tráfego (→ Midas) · input: briefing + refs do Olheiro
- output: pauta-semana.md (posts c/ gancho, legenda, CTA) · tools: linha-editorial.md, Claude
- metricas: % pauta aprovada sem retrabalho · **aprovacao: Gate 1 (pauta)**

**3. Estúdio 🖼️ (design)**
- responsável: plugin Adobe/Canva + Claude Design · funcao: gera artes, aplica identidade
- nao_faz: escrever copy (→ Nova) / publicar (→ Midas) · input: pauta aprovada + fotos
- output: peças prontas em outputs/ · tools: gerar_carrossel.py, Canva, Claude Design
- metricas: peças aprovadas/retrabalho · **aprovacao: Gate 2 (criativo) — regra: só via plugin**

**4. Midas 📈 (tráfego + WhatsApp)**
- responsável: humano-no-loop + Claude · funcao: agenda/publica, marca o que impulsionar, monta resposta WhatsApp
- nao_faz: definir verba sozinho (→ pede Murillo) · input: peças aprovadas (Gate 2) + msgs WhatsApp
- output: posts publicados + RASCUNHOS de resposta pro Murillo enviar · tools: Meta Suite/Ads, templates-whatsapp.md
- metricas: cliques no WhatsApp, reservas, ROAS · **aprovacao: Gate 3 (distribuição) + qualquer verba**

**5. Analista 📊 (dados)**
- responsável: Claude · funcao: lê desempenho, aponta os 3 melhores posts, recomenda repetir/variar
- nao_faz: rodar campanha / escrever copy · input: métricas da semana
- output: decisão da semana → vira briefing da semana seguinte · tools: IG Insights, planilha, Claude
- metricas: acerto da recomendação (post repetido performou?) · aprovacao: nunca (recomenda, Murillo decide)

## BLOCO G — Fluxo operacional diário
1. **Briefing matinal** (já existe `briefing.py`): Javis injeta estado real +
   saudação proativa.
2. **Olheiro** roda em background → deposita referências do dia.
3. **Midas** verifica WhatsApp → monta rascunhos de resposta → Murillo envia.
4. Murillo conversa com o Javis (agora ~2s via Gemini) pra ajustar/pedir.
5. Tudo que muda estado é registrado em `_logs/` / Journey Log.

## BLOCO H — Fluxo semanal de decisão (Ritual)
Cron semanal (30 min, do blueprint):
1. **Analista** consolida métricas da semana.
2. **Guardião de Métrica** (conselho) separa receita de vaidade.
3. Veredito por item: **Escalar** (repetir/impulsionar o que converteu) /
   **Manter** (observar) / **Matar** (cortar o que não paga).
4. Decisão vira o **briefing da semana seguinte** (loop fechado).
5. Murillo aprova o pacote (gate humano).

## BLOCO I — Métricas principais
Separadas como no blueprint:
- **Movem receita (decidem):** reservas, cliques no WhatsApp, CAC por passeio,
  LTV de cliente recorrente, ROAS por campanha, payback.
- **Operacionais (saúde):** % pauta aprovada sem retrabalho, latência de resposta
  do Javis, custo/token (telemetria atual).
- **Vaidade (ignorar na decisão):** likes, alcance, seguidores, impressões.

## BLOCO J — Aprovações humanas obrigatórias
- **Gate 1 — Pauta:** nada vai pra produção sem Murillo aprovar a pauta (Nova).
- **Gate 2 — Criativo:** nenhuma arte sem aprovação + **regra: só via plugin
  Adobe/Canva** (Estúdio).
- **Gate 3 — Distribuição:** nada publicado/agendado sem OK (Midas).
- **Verba:** qualquer gasto de anúncio para e pede Murillo.
- **WhatsApp:** Javis só monta RASCUNHO; quem envia é o Murillo.
- **Escrita fora do escopo / commit / push:** guard do Javis bloqueia (já existe).
- **Dados de cliente/CRM:** nunca expostos a provedor externo sem decisão.

## BLOCO K — Estrutura de arquivos e pastas
```
javis/
├── _apps/javis-local-interface/backend/
│   ├── agent.py            # kernel: cascata + tool-use
│   ├── command_router.py   # roteamento de intent
│   ├── orchestrator.py     # conclave/squad/memória
│   ├── conclave.py         # conselheiros (debate)
│   ├── project_registry.py # registry/pointer de projetos
│   ├── squads/             # (NOVO) Squad Contract + loader genérico
│   │   ├── contract.py     #   schema + validação do contrato
│   │   └── registry.py     #   instancia squads globais p/ um projeto
│   └── projects/
│       └── vem_passear/    # (formaliza vp_squad.py)
│           ├── manifesto.json
│           ├── skills.json   # squads no Squad Contract
│           └── squads.py
├── _projetos/<slug>/       # contexto humano de cada projeto (docs)
├── _data/                  # dados de runtime (vp_*.json, javis.db)
├── _docs/                  # blueprints + arquitetura (indexado na memória)
├── _estado/                # estado vivo + próximos passos
└── _logs/                  # decisões datadas
```

## BLOCO L — Próximos passos técnicos
1. **Criar `squads/contract.py`** — dataclass do Squad Contract + validador
   (todo campo obrigatório, `aprovacao_humana` explícito).
2. **Migrar `vp_squad.py`** pra o contrato completo (somar métricas + responsável
   + aprovacao aos 5 squads — dados já existem, é preencher).
3. **`squads/registry.py`** — função que, dado um manifesto de projeto, instancia
   os squads globais especializados (generaliza o que `vp_squad` faz à mão).
4. **Endpoint `/projects/<slug>/squads`** — expõe o grafo (já há `/agents`).
5. **Ritual semanal como cron** — job que dispara o Bloco H e abre um gate.
6. **Painel de Receita** — estender telemetria atual pra métricas de negócio.
7. **Testes** — validação do contrato (campos obrigatórios), e que `aprovacao_humana`
   nunca fica vazio num squad que escreve/publica/gasta.
8. **Plugar o 2º projeto** (prova de reúso) — repetir o manifesto+skills pra outro
   negócio, sem tocar no núcleo.
```
```
