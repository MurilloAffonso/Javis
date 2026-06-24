<!--
TEMPLATE_PROJETO_SQUADS.md — modelo reutilizável para plugar QUALQUER projeto no Javis.
COMO USAR:
  1. Copie este arquivo para _projetos/<slug>/PROJETO_SQUADS.md (ou para o repo do projeto).
  2. Substitua todo {{PLACEHOLDER}} e remova os comentários <!-- ... -->.
  3. Mantenha só os squads que o projeto precisa (a Seção 5 traz uma biblioteca por tipo).
  4. Gere os 2 manifestos que o Javis lê (ver Seção 15): manifesto.json + skills.json.
Base: Squad Contract de _docs/arquitetura-javis-os.md. Exemplo preenchido: _docs/vem-passear-squads.md.
TIPOS-ALVO: agência de turismo · agência digital · produto digital · app · projeto de
conteúdo · automação para empresas · projeto pessoal.
-->

# {{NOME_DO_PROJETO}} — Projeto & Squads no Javis

`slug: {{slug-do-projeto}}` · `tipo: {{turismo|agencia-digital|produto|app|conteudo|automacao|pessoal}}`
`atualizado_em: {{AAAA-MM-DD}}`

---

## 1. Nome do projeto
**{{NOME_DO_PROJETO}}** — {{uma linha do que é}}.
<!-- ex.: "Vem Passear Jampa — agência de passeios turísticos em João Pessoa." -->

## 2. Objetivo do projeto
- **Missão:** {{o que o projeto existe pra entregar}}
- **Meta atual (mensurável):** {{ex.: X reservas/mês, Y MRR, Z usuários ativos}}
- **Horizonte:** {{prazo da meta}}

## 3. Status atual
- **Fase:** {{ideação | validação | operação | escala}}
- **O que já existe:** {{ativos, canais, base de clientes, código, audiência}}
- **Gargalo nº 1:** {{o que mais trava hoje}}

## 4. Base de conhecimento
- **Fonte da verdade (1 arquivo canônico):** {{caminho/descrição — catálogo, specs, backlog}}
  <!-- regra-mãe: nenhum squad inventa dado; tudo sai daqui -->
- **Documentos de apoio:** {{links/arquivos: marca, tom de voz, processos, métricas}}
- **Dados estruturados:** {{CRM, planilhas, DB, analytics}}
- **Onde mora:** {{repo do projeto / pasta _projetos/<slug>/ / serviço externo}}

## 5. Squads necessários
<!-- Escolha os squads que o projeto precisa. Cada squad é o MESMO contrato.
     Biblioteca por tipo de projeto (sugestão — adapte):
     • turismo:        Atendimento&Vendas · Conteúdo · Tráfego · Operação · Pós-venda · Dados · Parcerias · Site/SEO · Oferta
     • agência digital: Prospecção · Atendimento/Conta · Criação · Tráfego · Produção · Dados · Financeiro
     • produto digital: Pesquisa · Produto/Roadmap · Conteúdo · Aquisição · Onboarding/Sucesso · Dados · Suporte
     • app:            Pesquisa · Produto · Engenharia · Growth/Aquisição · Suporte · Dados/Analytics
     • conteúdo:       Pesquisa/Trends · Pauta · Produção · Distribuição · Comunidade · Dados · Monetização
     • automação B2B:  Discovery · Mapeamento de Processo · Build/Integração · QA · Suporte · Dados
     • pessoal:        Foco/Planejamento · Execução · Aprendizado · Finanças · Revisão
     Para CADA squad escolhido, preencha o contrato abaixo (duplique o bloco). -->

### Squad: {{NOME_DO_SQUAD}} {{emoji}}  (área: {{inteligencia|oferta|conteudo|design|trafego|operacao|dados|retencao|painel}})
- **Agente responsável:** {{qual cérebro/persona executa — Claude assinatura, Gemini, Conclave, humano-no-loop}}
- **Faz:** {{1–3 verbos do que entrega}}
- **Não faz:** {{o que evita}} → delega para {{outro squad}}
- **Input:** {{o que consome}} (de {{quem}})
- **Output:** {{o que entrega}} → alimenta {{outro squad}}
- **Ferramentas:** {{tools concretas}}
- **Métricas:** {{como se mede o sucesso DESTE squad}}
- **Rotina diária:** {{o que faz todo dia}}
- **Rotina semanal:** {{o que faz toda semana}}
- **Aprovação humana:** {{gatilho exato que PARA e pede OK — ou "nunca"}}

<!-- repita o bloco acima para cada squad -->

## 6. Inputs principais (do projeto como um todo)
- {{ex.: leads, briefings, dados de uso, pedidos de cliente, conteúdo bruto}}
- {{fontes externas: APIs, planilhas, canais}}

## 7. Outputs esperados (do projeto como um todo)
- {{ex.: vendas/reservas, peças publicadas, features entregues, relatórios}}
- {{entregáveis que vão pro mundo / pro cliente}}

## 8. Ferramentas usadas
- **Cérebros:** {{Claude assinatura, Gemini grátis, OpenRouter}} (via cascata do Javis)
- **Execução:** {{Claude Code, Codex}}
- **Canais:** {{WhatsApp, Instagram, e-mail, site, app}}
- **Dados:** {{SQLite, planilhas, analytics}}
- **Criativo:** {{plugin Adobe/Canva — regra: criativo só via plugin}}
- **Automação/integração:** {{webhooks, scripts}}

## 9. Métricas principais
- **Que MOVEM o resultado (decidem):** {{ex.: receita, CAC, LTV, ROAS, retenção, MRR, ativação}}
- **Operacionais (saúde):** {{tempo de resposta, % entregue sem retrabalho, custo/token}}
- **Vaidade (NÃO decidem):** {{likes, alcance, seguidores, downloads sem uso}}

## 10. Fluxo diário
1. {{briefing/abertura: Javis injeta estado do projeto}}
2. {{squads de rotina rodam: ex. ler canais, atualizar dados}}
3. {{Javis monta rascunhos/ações pra você aprovar}}
4. {{registro do que mudou em _logs/}}

## 11. Fluxo semanal (ritual de decisão)
1. Squad de Dados consolida a semana.
2. Conselho separa o que move resultado do que é vaidade.
3. Veredito por item: **Escalar / Manter / Matar**.
4. Decisão vira o **briefing da semana seguinte** (loop fechado).
5. Você aprova o pacote.

## 12. Aprovações humanas
<!-- Liste os gates. Padrão: nada que publica, gasta, ou fala com cliente vai sem OK. -->
- {{Gate 1: ex. pauta/plano antes de produzir}}
- {{Gate 2: criativo — só via plugin Adobe/Canva}}
- {{Gate 3: publicação/entrega}}
- **Dinheiro:** qualquer gasto/verba para e pede você.
- **Mensagem a cliente:** Javis monta rascunho; você envia.
- **Irreversível/externo:** commit, push, deploy, contrato → guard do Javis bloqueia.
- **Dados sensíveis (CRM/cliente):** nunca expostos a provedor externo sem decisão.

## 13. Riscos
- **Operacionais:** {{o que pode falhar na entrega}}
- **De dados:** {{dado desatualizado, fonte da verdade divergente}}
- **De canal/plataforma:** {{ToS, bloqueio de conta, dependência de terceiro}}
- **De custo:** {{verba de ads, API paga}}
- **Mitigação:** {{como cada risco é contido — gate, fallback, limite}}

## 14. Próximas ações
- [ ] {{ação 1 — responsável — prazo}}
- [ ] {{ação 2}}
- [ ] {{ação 3}}
<!-- estas alimentam _estado/proximos-passos.md do Javis -->

## 15. Como esse projeto aparece na interface do Javis
O Javis usa modelo **registry/pointer** (`project_registry.py`): ele APONTA pro
projeto, não absorve. Para aparecer, o projeto fornece 3 coisas:

1. **`manifesto.json`** (o cartão do projeto):
   ```json
   {
     "projeto": "{{NOME_DO_PROJETO}}",
     "empresa": "{{empresa ou pessoa}}",
     "fase_atual": "{{fase}}",
     "descricao_fase": "{{1 linha}}",
     "atualizado_em": "{{AAAA-MM-DD}}",
     "modelo_ia": { "principal": "claude-assinatura", "rapido": "gemini" },
     "fonte_da_verdade": "{{arquivo canônico}}",
     "validacao": { "status": "{{ok|pendente}}" },
     "contato_responsavel": { "nome": "{{você}}", "canal": "{{whatsapp/email}}" }
   }
   ```
2. **`skills.json`** (os squads ativos, cada um no Squad Contract):
   ```json
   { "skills": [
     { "id": "{{slug-squad}}", "categoria": "{{area}}", "papel": "{{faz}}",
       "risco": "{{baixo|medio|alto}}", "status": "ativo" }
   ] }
   ```
3. **Fonte da verdade** (o arquivo canônico citado no manifesto).

**Onde fica visível:**
- **Card do projeto** na view de Projetos (nome, fase, status online/offline, nº squads).
- **Quadro/Kanban** (estilo Plane) das missões/tarefas do projeto.
- **`/projects/{{slug}}`** e **`/projects/{{slug}}/squads`** — o grafo de squads.
- **Briefing** matinal puxa o estado do projeto pro cérebro do Javis.

**Plugar um projeto novo = registrar o slug + esses 3 arquivos. Zero código de núcleo.**

---

> Gerado a partir do template `_docs/TEMPLATE_PROJETO_SQUADS.md`.
> Squad Contract: `_docs/arquitetura-javis-os.md` · Exemplo real: `_docs/vem-passear-squads.md`.
