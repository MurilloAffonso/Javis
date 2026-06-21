# Javis — Assistente Virtual Pessoal e Operacional

Javis é o assistente de Murillo para gestão pessoal, operacional e intelectual.

## Visão

Javis é um espaço onde Murillo conversa, pensa, organiza e age.

Não é um produto. É uma extensão digital do Murillo — um parceiro de trabalho que lembra, organiza, pesquisa e eventualmente age no computador (com aprovação).

### O que Javis faz

- Conversa e responde perguntas com contexto persistente
- Guarda e recupera memórias relevantes
- Captura e desenvolve ideias
- Organiza projetos e próximos passos
- Pesquisa e sintetiza informações
- Registra decisões e aprendizados
- (Futuro) Executa ações no computador com aprovação humana

### O que Javis NÃO é

- Não é radar financeiro
- Não é sistema de trading
- Não é scanner de mercado
- Não herda contexto de projetos antigos

---

## Arquitetura Inicial

```
javis/
├── AGENTS.md          — instruções para agentes AI
├── CLAUDE.md          — regras para Claude Code
├── README.md          — este arquivo
├── _memoria/          — memórias persistentes de Murillo e do projeto
├── _ideias/           — ideias capturadas, brutas ou elaboradas
├── _projetos/         — contexto de projetos ativos
├── _prompts/          — prompts reutilizáveis e templates
├── _skills/           — skills personalizadas para Claude Code
├── _logs/             — decisões técnicas e registros de sessão
├── _inbox/            — entradas para processar (tarefas, perguntas)
├── _outbox/           — saídas elaboradas (relatórios, respostas)
└── _ferramentas/
    ├── leanctx/       — config e notas sobre LeanCTX
    └── headroom/      — config e notas sobre Headroom
```

---

## Ferramentas de Economia de Tokens

### LeanCTX

LeanCTX é um MCP server que comprime a leitura de arquivos e outputs de shell em até 99%, reduzindo drasticamente o gasto de tokens do Claude.

Repositório: https://github.com/yvgude/lean-ctx

```bash
# Verificar versão
lean-ctx --version

# Diagnóstico
lean-ctx doctor

# Análise de ganho potencial
lean-ctx gain --deep

# Inicializar para Claude Code
lean-ctx init --agent claude
```

**Quando usar:** Sempre. LeanCTX deve ser o modo padrão de operação no dia a dia.

### Headroom

Headroom é uma ferramenta que envolve o Claude com um proxy local para compressão adicional de tokens.

Repositório: https://github.com/chopratejas/headroom

```bash
# Verificar versão
headroom --version

# Teste de performance
headroom perf

# Testar wrapper (modo de teste apenas)
headroom wrap claude

# AVISO: NÃO usar como proxy permanente sem aprovação de Murillo
# NÃO alterar ANTHROPIC_BASE_URL globalmente
```

**Quando usar:** Apenas em modo de teste e comparação. Não configure como padrão permanente.

> **Status (2026-06-10):** Headroom não está instalado. Python 3.14 é incompatível com PyO3 0.22.6 (usado internamente pelo headroom-ai). Aguardando aprovação para usar workaround `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`, ou aguardar nova versão do headroom. Ver `_ferramentas/headroom/STATUS.md`.

---

## Modo Recomendado de Operação

### Dia a dia — Claude normal + LeanCTX

```bash
claude
```

Com LeanCTX ativo como MCP server, Claude automaticamente usará as ferramentas comprimidas (`ctx_read`, `ctx_search`, `ctx_shell`, `ctx_tree`).

### Teste comparativo — Claude via Headroom

```bash
headroom wrap claude
```

Use isso apenas para medir a diferença. Documente o resultado em `_logs/`.

### Combinação LeanCTX + Headroom

**Não combine ainda.** Meça primeiro cada ferramenta separadamente antes de combinar.

---

## Comandos Úteis

```bash
# Verificar ferramentas instaladas
lean-ctx --version
headroom --version
node --version
python --version
claude --version

# Status do projeto
lean-ctx doctor
headroom perf

# Abrir Claude Code no projeto
claude

# Ver estrutura de pastas
tree /F (Windows) ou ls -R (bash)
```

---

## Interface de Conversa — Open WebUI

Open WebUI é a interface de conversa do Javis, rodando via Docker Compose e conectada ao Ollama local.

- Acesso local: **http://localhost:3000**
- Dados persistidos em: `open-webui-data/` (dentro do projeto)
- Motor de IA: Ollama em `http://host.docker.internal:11434`
- Modelos disponíveis: `llama3.2:3b`, `phi3:mini`
- Nome da interface: **Javis**

### Modelos especializados do Javis (Open WebUI)

Os modelos abaixo estão configurados em **Espaço de Trabalho → Modelos**:

| Modelo | Quando usar | Formato de saída |
|--------|-------------|-----------------|
| **Javis Geral** | Conversa livre, ideias, dúvidas, planejamento | Resposta direta + próximo passo |
| **Javis Ideias** | Capturar uma ideia nova | `💡 IDEIA CAPTURADA` |
| **Javis Projetos** | Transformar ideia em projeto estruturado | `🚀 PROJETO ESTRUTURADO` |
| **Javis Próximo Passo** | Destravar quando está sobrecarregado ou travado | `🎯 PRÓXIMO PASSO` |
| **Javis Decisões** | Registrar uma decisão tomada | `📌 DECISÃO REGISTRADA` |
| **Javis Revisor** | Revisar um plano antes de executar | `🔍 REVISÃO DO PLANO` |

**Recomendação de uso:**
- Use **Javis Geral** para conversa livre do dia a dia
- Use os modelos especializados para tarefas específicas — eles são mais obedientes e diretos
- Todos os modelos usam `llama3.2:3b` como base, temperatura baixa, e têm a palavra "Acompanhamento" como sequência de parada

**Capacidades desligadas em todos os modelos especializados:**
Pesquisa na Web, Geração de Imagem, Interpretador de Código, Terminal, Ferramentas Integradas, Automações, Calendário, Task Management

### Comandos

```bash
# Iniciar
docker compose up -d

# Parar
docker compose down

# Ver logs em tempo real
docker compose logs -f open-webui

# Ver status dos containers
docker compose ps

# Atualizar imagem futuramente
docker compose pull
docker compose up -d
```

### Primeiro acesso

1. Abrir http://localhost:3000 no navegador
2. Criar conta de administrador (primeiro usuário é automaticamente admin)
3. Verificar se os modelos do Ollama aparecem no seletor de modelos
4. Configurar nome/persona do Javis em Configurações → Interface

### Acesso pelo celular (mesma rede Wi-Fi)

Descubra o IP local do computador:
```bash
ipconfig  # Windows
```
Procure por "Endereço IPv4" na interface Wi-Fi (ex: 192.168.1.X).
Acesse no celular: **http://192.168.1.X:3000**

---

## Ativação no Open WebUI

O prompt mestre do Javis está em:

```
_prompts/system-openwebui-javis.md
```

### Como configurar no Open WebUI

**Opção A — System Prompt global (recomendado para começar):**

1. Abrir http://localhost:3000
2. Ir em **Admin Panel** → **Settings** → **Interface**
3. Colar o conteúdo do bloco de código de `_prompts/system-openwebui-javis.md` no campo **System Prompt**
4. Salvar

**Opção B — Persona dedicada chamada "Javis":**

1. Abrir http://localhost:3000
2. Ir em **Workspace** → **Models**
3. Criar um novo modelo baseado em `llama3.2:3b` ou `phi3:mini`
4. Nome: **Javis**
5. Colar o prompt mestre no campo **System Prompt**
6. Salvar — o Javis aparecerá como modelo separado no seletor

A opção B é preferível: permite conversar com "Javis" e com o modelo base separadamente.

### Primeiro teste recomendado

Após colar o prompt, teste com:

> "Tive uma ideia de criar um app de anotações de voz que transcreve automaticamente. O que acha?"

O Javis deve responder usando o formato **💡 IDEIA CAPTURADA** com resumo, categoria, valor potencial, próximo passo e destino.

---

## Ferramentas Futuras do Javis

| Ferramenta | Status | Função |
|---|---|---|
| **LeanCTX** | ✅ Ativo | Economia de contexto — compressão até 99% nos reads/shells |
| **CodeGraph** | ✅ Inicializado | Mapa estrutural de código — navegação por símbolo sem ler tudo |
| **agent-skills** | 📐 Referência | Metodologia `/spec /plan /build /test /review` para skills |
| **ai-engineering-from-scratch** | 📚 Estudo futuro | Referência de RAG, agentes, fundamentos — não instalar agora |
| **Headroom** | ⏸ Pendente | Proxy de compressão — aguardando compatibilidade Python 3.14 |

### LeanCTX (ativo)
Já configurado como MCP server. Reduz tokens em até 99% substituindo Read/Grep/Shell por ctx_read/ctx_search/ctx_shell.

### CodeGraph ✅

CodeGraph foi inicializado no projeto Javis (v0.9.9).

**Função:** mapear a estrutura de código como grafo de símbolos, permitindo que Claude Code navegue por relações entre arquivos, funções e módulos sem precisar ler arquivos inteiros — economizando tokens em projetos com código.

**Uso:** análise estrutural quando o projeto tiver código-fonte (Python, JS, TS, etc.). Atualmente o projeto é só Markdown e YAML — o índice crescerá conforme o Javis ganhar código.

**Observação:** `.codegraph/` está no `.gitignore` e não será commitado. O índice é local por máquina.

```bash
# Verificar status
codegraph status

# Atualizar índice manualmente (normalmente automático)
codegraph index
```

Ver detalhes: `_ferramentas/repositorios-avaliados.md`

### agent-skills (referência de metodologia)
Fluxo disciplinado para criação de features:
```
/spec → /plan → /build → /test → /review
```
Usar como modelo ao criar skills em `_skills/`. Não importar completo.

### ai-engineering-from-scratch (estudo futuro)
Guia progressivo de engenharia de IA. Útil quando Javis precisar de RAG próprio ou agentes avançados. Não instalar agora — traz dependências desnecessárias.

---

## Skills Iniciais do Javis

Skills são instruções operacionais que orientam o Javis sobre como processar situações específicas. Foram criadas do zero, inspiradas na lógica metodológica do projeto [agent-skills](https://github.com/addyosmani/agent-skills) (`/spec → /plan → /build → /test → /review`), mas **nenhuma skill externa foi instalada** — todas são próprias do Javis.

Localização: `_skills/`

| Skill | Arquivo | Quando usar |
|---|---|---|
| **Capturar Ideia** | `capturar-ideia.md` | Murillo manda pensamento solto, fragmentado ou informal |
| **Transformar em Projeto** | `transformar-em-projeto.md` | Uma ideia tem potencial e precisa de estrutura para começar |
| **Planejar Próximo Passo** | `planejar-proximo-passo.md` | Murillo está travado, sobrecarregado ou com muitas ideias em paralelo |
| **Revisar Plano** | `revisar-plano.md` | Antes de executar qualquer plano — detecta riscos, confusões e excesso |
| **Resumir Decisão** | `resumir-decisao.md` | Uma decisão importante foi tomada e precisa ser registrada para memória futura |

### Fluxo típico de uso

```
Ideia solta
  → capturar-ideia
    → (se tiver potencial) → transformar-em-projeto
      → (antes de executar) → revisar-plano
        → (quando travado) → planejar-proximo-passo
          → (ao decidir algo) → resumir-decisao → _memoria/decisoes/
```

Cada skill define: objetivo, quando usar, entrada esperada, processo, saída esperada, regras de economia de tokens e template de resposta.

---

## Interface Local — Ações no Computador

A **Javis Local Interface** (`_apps/javis-local-interface/`) é uma camada de execução local que complementa o Open WebUI. Enquanto o Open WebUI cuida da conversa, a interface local executa ações no computador de Murillo.

```
[Murillo]
    │
    ├── texto/voz
    │       ▼
    │   [Command Router]  ← classifica intenção por regras (sem LLM)
    │       │
    │       ├── conversa → Open WebUI / Ollama
    │       ├── ação segura → executa → log
    │       └── ação perigosa → pede aprovação → log
    └── resultado + log → CLI / frontend
```

**Iniciar o servidor (API + Quadro + CONVERSA):**
```powershell
cd _apps/javis-local-interface/backend
uvicorn server:app --reload   # abre em http://localhost:8000/
```

**Testar roteamento de voz (dry-run):**
```powershell
python backend/voice_bridge.py "abre o youtube"
python backend/voice_bridge.py "apaga meus arquivos"
```

**Abrir o frontend estático:**
Abra `_apps/javis-local-interface/frontend/index.html` no navegador.

Arquitetura completa: `_docs/JAVIS-LOCAL-INTERFACE-ROADMAP.md`  
Integração voz→comando: `_docs/JAVIS-VOICE-TO-COMMAND-ROUTER.md`

### Skills da Interface Local

| Skill | Arquivo | Quando usar |
|---|---|---|
| **Comando de Voz Local** | `comando-de-voz-local.md` | Simular roteamento de um comando antes de executar |
| **Executar com Aprovação** | `executar-com-aprovacao.md` | Ações que requerem confirmação explícita |
| **Abrir Projeto** | `abrir-projeto.md` | Abrir pasta de projeto por nome |
| **Registrar Log** | `registrar-log.md` | Gravar evento no JSONL de ações |

---

## Pipeline Operacional — Campanha com Gates de Aprovação

O coração operacional do Javis é o **Quadro** (Kanban estilo Plane, na view
do servidor em `http://localhost:8000/`) somado ao painel **CONVERSA**. Por ali
roda uma campanha de marketing ponta a ponta, sempre em **modo seguro**: nada é
publicado de verdade e nenhuma integração externa (WhatsApp/Instagram/Google Meu
Negócio) é acionada — tudo é template/arquivo local até Murillo decidir o
contrário.

### Fluxo ponta a ponta

```
[Murillo] "cria a pauta da semana da Vem Passear"  (painel CONVERSA)
   │
   ▼  agente Nova → gerar_pauta_vp
pauta-semana.md ──▶ 🚦 GATE 1 (Murillo aprova a pauta)
                         │ aprovado → destrava Design
                         ▼  botão "🎨 Rodar Estúdio" — agente Estúdio
                    criativos-semana.md ──▶ 🚦 GATE 2 (aprova criativos)
                                                │ aprovado → cria task Distribuição
                                                ▼  botão "📤 Preparar Distribuição" — agente Midas
                                           distribuicao-semana.md ──▶ 🚦 GATE 3 (aprova distribuição)
                                                                          │ aprovado
                                                                          ▼
                                                pacote-publicacao-semana.md  (PUBLICAÇÃO MANUAL)
                                                  → task concluída/morta + digest de IA
```

Cada gate é uma **aprovação humana explícita** — o fluxo nunca avança sozinho de
uma etapa para a outra. Rejeitar uma gate (ex.: Gate 2) **não** cria a etapa
seguinte: a task volta para `pending`, o sistema marca `adjustment_required` e o
botão da etapa reaparece para refazer.

### Os 4 entregáveis (gerados em ordem)

| Ordem | Arquivo (`_projetos/cerebro-jampa/posts/`) | Gerado por | Conteúdo |
|-------|--------------------------------------------|------------|----------|
| 1 | `pauta-semana.md` | Nova (chat) | ~3 posts, pilares variados, no máx. 1 de venda |
| 2 | `criativos-semana.md` | Estúdio | headline, legenda, CTA e briefing visual por peça |
| 3 | `distribuicao-semana.md` | Midas | calendário, canais, horário e checklist por peça |
| 4 | `pacote-publicacao-semana.md` | Midas | pacote final manual + aviso "nenhuma integração externa foi acionada" |

Dados não confirmados (maré, vaga, preço, horário) saem sempre como
`[CONFIRMAR COM MURILLO]` em vez de serem inventados.

### Como o estado é guardado

- **SQLite** é a fonte principal de tasks e aprovações; o backlog em Markdown
  (`_data/codex_backlog.md`) recebe *dual-write* (`[x]` na gate aprovada).
- **Journey Log** por task registra a timeline real (`agent_called` →
  `file_generated` → `approval_requested` → `approval_approved` → … →
  `entity_killed` → `ai_digest_created`); `action_logs` registra as decisões.
- **Idempotência:** re-decidir uma gate já resolvida, ou re-rodar Estúdio/
  Distribuição no mesmo `task_id`, retorna **409** — sem duplicar tasks.
- Ao concluir, a task vai para a coluna **🪦 Concluído/Morto** com um **digest**
  de IA (o que foi feito, quem participou, gargalos, próximo passo).

### Validação

Roteiro manual completo (incl. teste negativo de rejeição) em
`_docs/TESTE_E2E_CAMPANHA_VP.md`. Baseline automática:

```powershell
cd _apps/javis-local-interface
python -m pytest tests/ -q
```

---

## Próximos Passos

- [x] LeanCTX funcionando como MCP server
- [x] Open WebUI rodando (http://localhost:3000)
- [x] CodeGraph inicializado
- [x] Skills iniciais criadas (9 skills em `_skills/`)
- [x] Configurar 6 modelos especializados do Javis
- [x] Sandbox de voz validado (voz → transcrição → LLM → fala)
- [x] Javis Local Interface v0 — CLI + Command Router + Actions + Logger + Frontend
- [x] voice_bridge.py em modo dry-run — classifica e loga, não executa
- [x] v1 — Servidor FastAPI (`server.py`, porta 8000) servindo Quadro + CONVERSA
- [x] Primeiro projeto ativo plugado — Cérebro Jampa / campanha Vem Passear Jampa
- [x] Pipeline de campanha com 3 gates de aprovação humana (Pauta → Estúdio → Distribuição), SQLite + Journey Log + digest, tudo em modo seguro
- [ ] Resolver instalação do Headroom (incompatibilidade Python 3.14)
- [ ] v2 — Murillo valida logs dry-run → liberar execução por voz (risk: low)
- [ ] v3 — Conectar transcrição real do Open-LLM-VTuber ao voice_bridge

---

## Segurança

- Nunca faz commit sem aprovação de Murillo
- Nunca faz push sem aprovação de Murillo
- Nunca altera variáveis globais sem explicar
- Nunca executa ações no computador sem aprovação
- Nunca mistura contexto com outros projetos

---

*Criado em: 2026-06-10*
*Versão: 0.7.0 — Pipeline operacional de campanha com gates de aprovação*
