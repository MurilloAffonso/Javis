# Projeto: Javis v0

Data de criação: 2026-06-10
Status: em construção ativa
Responsável: Murillo

---

## Objetivo

Criar a base funcional do Javis — assistente pessoal e operacional de Murillo — com interface de conversa, memória estruturada, organização de ideias e projetos, e execução segura de próximos passos.

O v0 não precisa ser perfeito. Precisa ser estável, útil e não criar bagunça.

---

## Resultado esperado do v0

- Murillo consegue conversar com o Javis pelo Open WebUI e receber respostas úteis.
- Murillo consegue capturar ideias, estruturar projetos e registrar decisões com as skills.
- O sistema funciona localmente, sem custos de API, sem exposição externa.
- A estrutura de pastas e documentação permite crescer sem reescrever do zero.

---

## Stack atual

| Ferramenta | Função | Status |
|---|---|---|
| **Open WebUI** | Interface de conversa | ✅ Ativo — http://localhost:3000 |
| **Ollama** | Motor de IA local | ✅ Ativo — llama3.2:3b, phi3:mini |
| **LeanCTX** | Economia de contexto para Claude Code | ✅ Ativo — MCP configurado |
| **CodeGraph** | Mapa estrutural de código | ✅ Inicializado — índice local |
| **Skills próprias** | Organização de ideias/projetos | ✅ 5 skills em `_skills/` |
| **Docker Compose** | Orquestração do Open WebUI | ✅ Ativo |

---

## Ferramentas pausadas

| Ferramenta | Motivo | Quando retomar |
|---|---|---|
| **Headroom** | Incompatibilidade Python 3.14 + PyO3 0.22.6 | Quando nova versão do headroom-ai suportar Python 3.14 |
| **n8n** | Ainda não necessário | Quando Javis precisar automatizar fluxos externos |

---

## Ferramentas de referência (não instalar)

| Ferramenta | Uso |
|---|---|
| **agent-skills** | Inspiração metodológica para criar skills (`/spec /plan /build /test /review`) |
| **ai-engineering-from-scratch** | Estudo futuro — RAG, agentes avançados, fundamentos |

---

## Próximos passos

### Imediatos (fazer agora)
- [ ] Criar conta de administrador no Open WebUI (http://localhost:3000)
- [ ] Colar o prompt mestre (`_prompts/system-openwebui-javis.md`) no System Prompt do Open WebUI
- [ ] Testar uma conversa simples com o Javis usando `llama3.2:3b`
- [ ] Criar `_memoria/decisoes/` para registrar decisões futuras

### Próximos (depois que o básico funcionar)
- [ ] Criar `_memoria/contextos/` para memórias de projetos específicos
- [ ] Definir quais decisões do dia a dia valem ser registradas com `resumir-decisao`
- [ ] Criar primeiro projeto real em `_projetos/` além do javis-v0
- [ ] Avaliar se vale criar um segundo modelo no Ollama para tarefas específicas

### Futuros (não agora)
- [ ] Resolver Headroom quando Python 3.14 for suportado
- [ ] Avaliar n8n para automação de fluxos
- [ ] Estudar ai-engineering-from-scratch quando Javis precisar de RAG próprio
- [ ] Criar skill de pesquisa (`pesquisar-tema.md`)
- [ ] Criar skill de retrospectiva semanal (`retrospectiva-semanal.md`)

---

## Critérios de sucesso do v0

1. Murillo consegue abrir http://localhost:3000 e conversar com o Javis.
2. O Javis segue o estilo de resposta definido no prompt mestre.
3. As 5 skills funcionam na prática — Murillo usa pelo menos 2 delas.
4. Nenhuma informação sensível foi commitada.
5. O sistema funciona após reinicialização do computador (`docker compose up -d`).
6. A estrutura de pastas faz sentido e não está bagunçada.

---

## O que não fazer agora

- Não instalar mais ferramentas sem precisar.
- Não criar skills antes de usar as 5 existentes.
- Não conectar APIs externas pagas.
- Não expor o Open WebUI para acesso externo permanente.
- Não commitar dados do Open WebUI (`open-webui-data/`).
- Não misturar contexto do Javis com outros projetos de Murillo.
- Não reescrever o que está funcionando.

---

## Estrutura atual do projeto

```
javis/
├── AGENTS.md              — instruções para agentes AI
├── CLAUDE.md              — regras para Claude Code
├── README.md              — visão geral e documentação
├── docker-compose.yml     — Open WebUI + Ollama
├── .gitignore             — protege dados locais
├── _memoria/
│   └── murillo.md         — memória base de Murillo
├── _ideias/               — ideias capturadas
├── _projetos/
│   └── javis-v0.md        — este arquivo
├── _prompts/
│   └── system-openwebui-javis.md  — prompt mestre
├── _skills/
│   ├── capturar-ideia.md
│   ├── transformar-em-projeto.md
│   ├── planejar-proximo-passo.md
│   ├── revisar-plano.md
│   └── resumir-decisao.md
├── _logs/                 — decisões técnicas
├── _inbox/                — entradas para processar
├── _outbox/               — saídas elaboradas
├── _ferramentas/
│   ├── leanctx/STATUS.md
│   ├── headroom/STATUS.md
│   └── repositorios-avaliados.md
└── open-webui-data/       — dados do Open WebUI (ignorado pelo git)
```
