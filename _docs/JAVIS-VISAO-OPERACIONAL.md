# Javis — Visão Operacional

> Documento-resumo do que o Javis é **hoje** e como ele opera, ponta a ponta.
> Última atualização: 2026-06-20. Fonte de verdade técnica: o código em
> `_apps/javis-local-interface/` e o roteiro `_docs/TESTE_E2E_CAMPANHA_VP.md`.

---

## 1. O que é o Javis hoje

Javis é o assistente pessoal e operacional de Murillo. Hoje ele já não é só um
chat: é um **orquestrador local** que conversa, lembra (RAG sobre as pastas do
projeto), aciona agentes e conduz uma **campanha de marketing de ponta a ponta**
com aprovação humana em cada etapa.

Duas camadas convivem:

- **Conversa** — chat/voz com tool-use (entende intenção e encadeia ações),
  memória persistente e RAG das pastas do projeto.
- **Operação** — o **Quadro** (Kanban estilo Plane) + o painel **CONVERSA**,
  onde uma campanha nasce de uma pauta e caminha por 3 gates até virar um pacote
  de publicação manual.

Tudo roda **local**, em **modo seguro**: nada é publicado automaticamente e
nenhuma integração externa é acionada sem decisão explícita do Murillo.

---

## 2. Como rodar localmente

**Servidor (API + Quadro + CONVERSA):**

```powershell
cd _apps/javis-local-interface/backend
uvicorn server:app --reload
```

Abre em **http://localhost:8000/** — topbar com contadores reais (mensagens /
agentes) e indicador de cérebro online; painel **CONVERSA** + **Quadro**.

**Pré-requisitos:**
- SQLite acessível (fonte principal de tasks/aprovações — criado no `init_db()`).
- Suíte de testes verde antes de validar manualmente (ver §10).

> Open WebUI (`localhost:3000`, Docker + Ollama) é a interface de conversa
> complementar; o pipeline operacional vive no servidor da porta 8000.

---

## 3. Pipeline Vem Passear Jampa

O fluxo operacional principal é a **campanha semanal da Vem Passear Jampa**
(projeto Cérebro Jampa, plugado como repo externo — o Javis não o absorve).

```
[Murillo] "cria a pauta da semana da Vem Passear"  (painel CONVERSA)
   │
   ▼  agente Nova → gerar_pauta_vp
pauta-semana.md ──▶ 🚦 GATE 1 (aprova a pauta)
                         │ aprovado → destrava Design
                         ▼  "🎨 Rodar Estúdio" — agente Estúdio
                    criativos-semana.md ──▶ 🚦 GATE 2 (aprova criativos)
                                                │ aprovado → cria task Distribuição
                                                ▼  "📤 Preparar Distribuição" — agente Midas
                                           distribuicao-semana.md ──▶ 🚦 GATE 3 (aprova distribuição)
                                                                          │ aprovado
                                                                          ▼
                                                pacote-publicacao-semana.md  (PUBLICAÇÃO MANUAL)
                                                  → task concluída/morta + digest de IA
```

**Os 4 entregáveis** (em `_projetos/cerebro-jampa/posts/`, gerados nesta ordem):

| Ordem | Arquivo | Gerado por | Conteúdo |
|-------|---------|------------|----------|
| 1 | `pauta-semana.md` | Nova (chat) | ~3 posts, pilares variados, no máx. 1 de venda |
| 2 | `criativos-semana.md` | Estúdio | headline, legenda, CTA e briefing visual por peça |
| 3 | `distribuicao-semana.md` | Midas | calendário, canais, horário e checklist por peça |
| 4 | `pacote-publicacao-semana.md` | Midas | pacote final manual + aviso de publicação manual |

Dados não confirmados (maré, vaga, preço, horário) saem sempre como
`[CONFIRMAR COM MURILLO]` — o sistema não inventa número.

---

## 4. SQLite como fonte principal

O **SQLite é a fonte de verdade** de tasks e aprovações. O backlog em Markdown
(`_data/codex_backlog.md`) continua existindo, mas como **dual-write**: quando
uma gate é aprovada, o `[x]` correspondente é refletido lá, sem deixar de gravar
no banco.

Por que isso importa:
- O **Quadro** lê as tasks do SQLite (não de um mock hardcoded).
- Aprovações pendentes vêm de `GET /approvals/pending`.
- Estatísticas (`GET /stats`) e digests também saem do banco.
- O Markdown vira reflexo humano-legível, não a fonte que pode divergir.

---

## 5. Quadro operacional

O **Quadro** é o Kanban (estilo Plane) servido em `http://localhost:8000/`. Cada
etapa da campanha é uma **task** com agente responsável e um botão de ação:

- **Pauta** (Nova) — nasce do chat.
- **[Design] Produzir os criativos** (Estúdio) — botão **"🎨 Rodar Estúdio"**,
  liberado só após a Gate 1.
- **[Distribuição] Preparar pacote** (Midas) — botão **"📤 Preparar
  Distribuição"**, criada só após a Gate 2.
- **🪦 Concluído/Morto** — coluna final; a task encerrada recebe selo de
  **digest**.

As aprovações pendentes aparecem no bloco `#approvals-box` no topo do painel
CONVERSA, com botões **Aprovar / Rejeitar** e campo de observação.

---

## 6. Gates 1, 2 e 3

Cada gate é uma **aprovação humana explícita**. O fluxo **nunca avança sozinho**
de uma etapa para a próxima.

| Gate | Agente | Aprova | Efeito ao aprovar |
|------|--------|--------|-------------------|
| **Gate 1** | nova | a pauta da semana | destrava a task de Design ("Rodar Estúdio") |
| **Gate 2** | estudio | os criativos antes de publicar | cria a task de Distribuição (Midas) |
| **Gate 3** | midas | a distribuição antes de publicar | gera o pacote manual + encerra a campanha |

**Idempotência:** re-decidir uma gate já resolvida, ou re-rodar Estúdio/
Distribuição no mesmo `task_id`, retorna **409** — sem duplicar tasks.

**Rejeição (ex.: Gate 2):** a etapa seguinte **não** nasce. A task de Design
volta para `pending` (o botão "Rodar Estúdio" reaparece), o sistema registra
**`adjustment_required`** e nenhum arquivo de distribuição/pacote é criado.

---

## 7. Journey Log

Cada task carrega um **Journey Log** — a timeline real de eventos, visível em
`GET /tasks/{id}/events` e no card via **"Ver jornada"**. Exemplo da task de
Distribuição, do início ao encerramento:

```
agent_called → file_generated → approval_requested → approval_approved
→ file_generated → manual_publication_package_created → task_completed
→ entity_killed → ai_digest_created
```

Em paralelo, `action_logs` registra as decisões (`approval_decide`,
`workflow_advance`). É o que prova, depois, que cada agente operou em modo
seguro e em que ordem as coisas aconteceram.

---

## 8. Digest

Quando a task é concluída, a **entidade "morre"** e o Javis gera um **digest de
IA** — um resumo curto da jornada daquela task. O card ganha o selo **📄
digest** e, em "Ver jornada", aparece o bloco **"📄 Digest da entidade"** com:

- status e duração;
- o que foi feito e quem participou;
- principais eventos e a aprovação;
- gargalos e o **próximo passo**.

Disponível também em `GET /tasks/{id}/digest`.

---

## 9. Modo seguro: sem publicar nada automaticamente

Princípio inegociável do pipeline atual:

- **Nada é publicado de verdade.** Não há chamada para WhatsApp, Instagram ou
  Google Meu Negócio em nenhuma etapa.
- **Não há geração de imagem** nem integração externa — tudo é template/arquivo
  local.
- O entregável final, `pacote-publicacao-semana.md`, traz o aviso explícito:
  **"PUBLICAÇÃO MANUAL — nenhuma integração externa foi acionada."**
- A publicação é **decisão e ação manual do Murillo**; o Javis prepara o pacote
  e para.

Verificação rápida de que segue seguro: `action_logs` não deve ter nenhum intent
de publicação/envio externo, e os módulos de studio/distribution/efeitos de
aprovação não chamam APIs externas.

---

## 10. Como executar o teste E2E

Roteiro manual completo (incluindo o **teste negativo** de rejeição de gate) em
`_docs/TESTE_E2E_CAMPANHA_VP.md`.

**Baseline automática (rodar antes do teste manual):**

```powershell
cd _apps/javis-local-interface
python -m pytest tests/ -q
```

→ deve ficar **verde** (baseline do roteiro: 117 passed) antes de começar.

**Teste manual, em resumo:**
1. No painel CONVERSA: *"Javis, cria a pauta da semana da Vem Passear"* → gera
   `pauta-semana.md` e abre a **Gate 1**.
2. Aprovar Gate 1 → destrava Design → **"🎨 Rodar Estúdio"** → `criativos-semana.md`
   + **Gate 2**.
3. Aprovar Gate 2 → cria Distribuição → **"📤 Preparar Distribuição"** →
   `distribuicao-semana.md` + **Gate 3**.
4. Aprovar Gate 3 → `pacote-publicacao-semana.md` (manual) → task **Concluída/
   Morta** + digest.

**Critério de aceite:** as 3 gates criadas/aprovadas sem duplicar task (com
idempotência confirmada), os 4 arquivos gerados na ordem certa, **nenhuma**
chamada externa, e `pytest` ainda verde ao final.

> Se rodar sobre dados reais da campanha, faça backup dos 4 `.md` antes e
> restaure o estado do Quadro/SQLite depois (a seção de restauração do roteiro
> explica como).
