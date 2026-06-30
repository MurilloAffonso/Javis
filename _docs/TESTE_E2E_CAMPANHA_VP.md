# Teste E2E — Pipeline de Campanha Vem Passear Jampa

Roteiro manual para validar, ponta a ponta, o fluxo:
**Pauta (chat) → Gate 1 → Design/Estúdio → Gate 2 → Distribuição → Gate 3 → pacote manual.**

Servidor: `_apps/javis-local-interface/backend/server.py` (porta 8000, `uvicorn server:app`).
UI: `http://localhost:8000/` (painel CONVERSA + Quadro).

> Modo seguro confirmado em todas as etapas: sem publicação real, sem integração
> externa (WhatsApp/Instagram/GMB), sem geração de imagem. Tudo template/local.

---

## Pré-requisitos

- [ ] **Rodar a suíte de testes:** `cd _apps/javis-local-interface && python -m pytest tests/ -q`
  → deve dar **117 passed** (baseline verde antes do teste manual).
- [ ] **Abrir o Javes:** `http://localhost:8000/` no navegador; topbar com
  contadores reais (msgs / 16 agentes) e indicador **CLAUDE** online.
- [ ] Servidor rodando (`uvicorn server:app --reload` dentro de `backend/`).
- [ ] SQLite acessível (fonte principal de tasks/approvals).
- [ ] Backup dos arquivos que serão sobrescritos durante o teste:
  - `_projetos/cerebro-jampa/posts/pauta-semana.md`
  - `_projetos/cerebro-jampa/posts/criativos-semana.md`
  - `_projetos/cerebro-jampa/posts/distribuicao-semana.md`
  - `_projetos/cerebro-jampa/posts/pacote-publicacao-semana.md` (se existir)
- [ ] Anotar estado atual do Quadro (`GET /tasks`) e de `GET /approvals/pending`
  antes de começar, para restaurar ao final se necessário.

---

## 1. Criação da pauta pelo chat

**Ação:** No painel CONVERSA, enviar a mensagem:

> "Javes, cria a pauta da semana da Vem Passear"

(equivalente programático: `POST /chat` com esse texto, ou `server._brain(...)`).

**Validar:**
- [ ] Resposta do chat indica que a ferramenta `gerar_pauta_vp` foi chamada.
- [ ] A agente Nova gerou uma pauta com pilares variados (não só venda) e usou
  `[CONFIRMAR COM MURILLO]` em maré/vaga/preço/horário em vez de inventar dado.
- [ ] Mensagem final do fluxo pede explicitamente a aprovação da Gate 1 (não
  avança para Design sozinho).

## 2. Geração de `pauta-semana.md`

**Validar:**
- [ ] Arquivo `_projetos/cerebro-jampa/posts/pauta-semana.md` foi atualizado
  com timestamp recente.
- [ ] Conteúdo tem ~3 posts, pilares variados, no máx. 1 post de venda.

## 3. Gate 1 criada

**Validar:**
- [ ] `GET /approvals/pending` retorna uma aprovação com `agent=nova`, assunto
  contendo "pauta da semana" (Gate 1), `status=pending`, `task_id` apontando
  para a task t1 do Quadro.
- [ ] Na UI, o bloco `#approvals-box` (topo do painel CONVERSA) mostra o card
  "Aprovar a pauta da semana… (Gate 1)" com botões **Aprovar**/**Rejeitar** e
  campo de observação.
- [ ] No Quadro, a Raia 1 (t1) está marcada `done`/`gate_approved` pendente de
  decisão (task da pauta concluída, aguardando gate).

## 4. Aprovação da Gate 1

**Ação:** Clicar **Aprovar** no card da Gate 1 (ou `POST /approvals/{id}/decide`
com `{"decision":"approved"}`).

**Validar:**
- [ ] Resposta/toast: "Gate 1 aprovada. Produção de criativos destravada."
- [ ] SQLite: task t1 = `gate_approved`.
- [ ] Backlog Markdown (`codex_backlog.md` ou equivalente) reflete `[x]` na Gate 1
  (dual-write).
- [ ] `action_logs` registra `approval_decide` + `workflow_advance`.
- [ ] `GET /approvals/pending` não mostra mais a Gate 1.
- [ ] Re-clicar Aprovar/Rejeitar na mesma Gate 1 retorna 409 (idempotência —
  não precisa ser repetido neste teste, só confirmar que o botão não reaparece).

## 5. Liberação da task de Design

**Validar:**
- [ ] No Quadro, a task "[Design] Produzir os criativos da pauta aprovada" (t2)
  passa para `pending` (estava bloqueada/inexistente para o usuário até aqui).
- [ ] Card de Design mostra o botão **"🎨 Rodar Estúdio"**.
- [ ] Nenhuma task de Design duplicada foi criada (deve ser a mesma t2 do
  backlog, não uma nova).

## 6. Rodar Estúdio

**Ação:** Clicar **"🎨 Rodar Estúdio"** no card de Design (ou
`POST /tasks/{task_id}/run-studio` com o `ext_id` da task t2).

**Validar:**
- [ ] Toast: "Criativos gerados. Gate 2 aguardando aprovação."
- [ ] Task de Design muda para `in_progress` durante a execução, agente `estudio`.
- [ ] Journey Log da task t2 registra, em ordem: `agent_called` (estudio) →
  `file_generated` (estudio) → `approval_requested`.
- [ ] Repetir a chamada no mesmo task_id retorna 409 (idempotente).

## 7. Geração de `criativos-semana.md`

**Validar:**
- [ ] Arquivo `_projetos/cerebro-jampa/posts/criativos-semana.md` criado/atualizado.
- [ ] Conteúdo lê a `pauta-semana.md` (pilar/formato/gancho/CTA por post) e monta,
  por peça: ideia, headline, legenda, CTA, briefing visual, orientação story/reels.
- [ ] Peças visuais marcadas `[CONFIRMAR COM MURILLO]` + seção "Observações
  pendentes".
- [ ] Termina com "Status: ... aguardando aprovação do Murillo (Gate 2)".

## 8. Gate 2 criada

**Validar:**
- [ ] `GET /approvals/pending` mostra aprovação `agent=estudio`, assunto "Aprovar
  criativos da semana antes de publicar", `status=pending`, `task_id` = task de
  Design (t2).
- [ ] Card visível na UI igual ao padrão da Gate 1.

## 9. Aprovação da Gate 2

**Ação:** Clicar **Aprovar** no card da Gate 2 (ou `POST /approvals/{id}/decide`).

**Validar:**
- [ ] Toast: "Distribuição destravada (sem publicar)" (ou mensagem equivalente
  do efeito `_advance_gate2`).
- [ ] Task de Design (t2) marcada `gate_approved`.
- [ ] Nova task "[Distribuição] Preparar pacote de publicação da pauta aprovada"
  criada no SQLite, agente `midas`, `status=pending`, com origem (`source`) no
  `approval_id`.
- [ ] Journey Log na task de Design registra `approval_approved` /
  `workflow_advanced` / `distribution_task_unlocked`.
- [ ] `action_logs` registra `workflow_advance`.

## 10. Liberação da Distribuição

**Validar:**
- [ ] No Quadro, a task de Distribuição aparece `pending`, agente `midas`.
- [ ] Card mostra o botão **"📤 Preparar Distribuição"**.
- [ ] Não há duplicação se o Gate 2 já tinha sido aprovado antes (idempotência).

## 11. Preparar pacote de Distribuição / publicação manual

**Ação:** Clicar **"📤 Preparar Distribuição"** (ou
`POST /tasks/{task_id}/prepare-distribution`).

**Validar:**
- [ ] Toast: "Distribuição preparada. Gate 3 aguardando aprovação."
- [ ] Arquivo `_projetos/cerebro-jampa/posts/distribuicao-semana.md` gerado, lendo
  `pauta-semana.md` + `criativos-semana.md`: calendário (dia/peça/canais/horário),
  canais (Feed/Stories/WhatsApp Status/Google Meu Negócio), legenda final + CTA +
  melhor horário por peça, `[CONFIRMAR COM MURILLO]` e checklist antes de publicar.
  Termina em "aguardando aprovação (Gate 3)".
- [ ] Journey Log na task de Distribuição: `agent_called` (midas) →
  `file_generated` (midas) → `approval_requested`.
- [ ] Gate 3 criada: `agent=midas`, assunto "Aprovar distribuição antes de
  publicar", `status=pending`, `task_id` = task de Distribuição. Visível em
  `/approvals/pending` e na UI.

### 11b. Aprovação da Gate 3 — pacote final manual

**Ação:** Clicar **Aprovar** no card da Gate 3.

**Validar:**
- [ ] Toast: "Pacote manual de publicação gerado. Campanha concluída com digest."
- [ ] Arquivo `_projetos/cerebro-jampa/posts/pacote-publicacao-semana.md` gerado:
  resumo da campanha, lista final de peças, legenda+CTA+canal+horário por peça,
  checklist manual antes de publicar, `[CONFIRMAR COM MURILLO]`, e o aviso
  **"PUBLICAÇÃO MANUAL — nenhuma integração externa foi acionada."**
- [ ] Journey Log na task de Distribuição: `approval_approved` → `file_generated`
  → `manual_publication_package_created` → `task_completed` → `entity_killed` →
  `ai_digest_created`.
- [ ] Task de Distribuição passa para `completed` no Quadro, com selo de digest.
- [ ] `GET /approvals/pending` não mostra mais nenhuma gate da campanha.

---

## Validações finais (passos 16–20)

### 16. Conclusão/morte da task
- [ ] No Quadro, a task de Distribuição está na coluna **🪦 Concluído/Morto**,
  status `completed`.
- [ ] `GET /tasks` mostra a task com `status: completed`, `completed_at` e
  `killed_at` preenchidos.

### 17. Digest
- [ ] O card da task de Distribuição tem o selo **📄 digest**.
- [ ] **Ver jornada** no card → bloco "📄 Digest da entidade" com: status, duração,
  o que foi feito, quem participou, principais eventos, aprovação, gargalos,
  próximo passo.
- [ ] `GET /tasks/vp-distribuicao-preparar/digest` retorna `digest_text` não-vazio.

### 18. Journey Log completo
- [ ] `GET /tasks/vp-distribuicao-preparar/events` → timeline na ordem:
  `agent_called` → `file_generated` → `approval_requested` → `approval_approved`
  → `file_generated` → `manual_publication_package_created` → `task_completed`
  → `entity_killed` → `ai_digest_created`.
- [ ] Jornada da pauta (`pipeline-marketing-vem-passear-jampa-t0`):
  `task_created` → `intent_detected` → `agent_called` → `file_generated` →
  `approval_requested` → `approval_approved` → `workflow_advanced` →
  `design_task_unlocked`.

### 19. Aprovações pendentes zeradas
- [ ] `GET /stats` → `approvals_pending: 0`.
- [ ] Painel de aprovações da UI vazio (o bloco `#approvals-box` some).

### 20. Nada foi publicado / sem integração externa
- [ ] Confirmar manualmente que NADA foi postado no Instagram/WhatsApp/GMB.
- [ ] `pacote-publicacao-semana.md` traz o aviso "PUBLICAÇÃO MANUAL — nenhuma
  integração externa foi acionada."
- [ ] (Opcional) `grep -ri "whatsapp_send\|integrations\.\|graph.facebook\|\.publish("`
  em `backend/{studio,distribution,approval_effects}.py` → **nenhuma ocorrência**.
- [ ] (Opcional) `action_logs` não tem nenhum intent de publicação/envio externo.

---

## Parte B — Teste NEGATIVO (rejeitar Gate 2)

> Objetivo: rejeitar os criativos no Gate 2 e confirmar que a Distribuição **não**
> nasce, o Gate 3 **não** aparece e o sistema sinaliza `adjustment_required`.

### Setup do Gate 2 pendente (sem depender da cota)
```bash
cd _apps/javis-local-interface/backend
python -c "
import db, repositories as repo
db._initialized=False; db.init_db()
t2='pipeline-marketing-vem-passear-jampa-t2'
repo.tasks.upsert(t2,'[Design] Produzir os criativos da pauta aprovada', status='in_progress', mission='pipeline-marketing-vem-passear-jampa')
print('Gate 2 id =', repo.approvals.add('Aprovar criativos da semana antes de publicar', agent='estudio', task_id=t2))
"
```

### B1. Rejeitar o Gate 2
- [ ] No painel de aprovações, abrir o Gate 2, escrever uma observação (ex.:
  "trocar o gancho do post 1") e clicar **Rejeitar**.
- [ ] Toast: "Gate 2 rejeitada. Criativos aguardando ajuste."

### B2. Distribuição NÃO é criada
- [ ] `GET /tasks` **não** contém `vp-distribuicao-preparar`.
- [ ] No Quadro não aparece a task "[Distribuição] Preparar pacote...".

### B3. Gate 3 NÃO aparece
- [ ] `GET /approvals/pending` **não** tem "Aprovar distribuição antes de publicar".

### B4. Sistema registra `adjustment_required`
- [ ] `GET /tasks/pipeline-marketing-vem-passear-jampa-t2/events` inclui
  `approval_rejected` e **`adjustment_required`**.
- [ ] A task de Design volta para **pending** (botão "Rodar Estúdio" reaparece) —
  Design disponível para ajuste.
- [ ] (Opcional) `memories` tem o sinal "Criativos da semana VP reprovados no Gate 2…".

### B5. Nenhum pacote final
- [ ] `distribuicao-semana.md` e `pacote-publicacao-semana.md` **não** foram criados
  por causa da rejeição.

---

## Critério de aceite do teste completo

- [ ] As 3 gates (1, 2, 3) foram criadas, aprovadas e avançaram o workflow sem
  duplicar tasks e sem reagir a re-decisão (idempotência confirmada em pelo
  menos uma gate).
- [ ] Os 4 arquivos foram gerados/atualizados na ordem correta:
  `pauta-semana.md` → `criativos-semana.md` → `distribuicao-semana.md` →
  `pacote-publicacao-semana.md`.
- [ ] Nenhuma chamada de integração externa ocorreu (sem WhatsApp/Instagram/GMB,
  sem geração de imagem) — confirmar via `action_logs`/Journey Log que todos os
  agentes envolvidos (nova, estudio, midas) operaram em modo seguro/local.
- [ ] `pytest tests/ -q` permanece verde após o teste manual (sem regressão).

## Restauração do ambiente após o teste

- [ ] Reverter os 4 arquivos `.md` gerados para o estado anterior (backup do
  pré-requisito), se o teste foi feito em dados reais da campanha.
- [ ] Restaurar status das tasks (t1/t2/Distribuição) e remover/reverter as gates
  de teste no SQLite, se necessário, para não confundir o Murillo com dados
  fictícios no Quadro real.
- [ ] Registrar no `_logs/` a execução deste roteiro (data, resultado, achados).
