# Pacote 2 — Vem Passear REAL: 4 endpoints conectados na UI

**Data:** 2026-07-03 (fase pós-auditoria de endpoints órfãos)

## O que foi decidido
Conectar o "Pacote 2 — VP real" da auditoria (escolha de Murillo): os botões fake da
Vem Passear viram operações reais, todas com confirmação forte (`confirmStrong`).
Guia de risco: `_arquitetura/catalogo-acoes-risco.md`.

## Conexões feitas (tudo em js/views/vempassear.js)
1. **➕ Novo atendimento** (Resumo) — era modal "Fase visual". Agora: form
   (nome/contato/obs) → confirmação forte → `POST /vp/clientes` → lead real 🔗.
2. **➡ Próxima etapa** (Funil) — era modal fake. Agora, para leads reais (🔗):
   confirmação forte → `PATCH /vp/clientes/{id}` gravando a etapa do funil.
   Leads sintéticos (demo) continuam com modal visual.
   - `vpSyncRealLeads` agora guarda `backendId` e respeita a etapa salva
     (status ∈ AT_FUNNEL → usa; senão "Lead novo").
3. **✨ Gerar com o squad** (Atendimento) — substituiu o "Reescrever · em breve".
   Chama `POST /jampa/responder-lead` (Hunter+LNS, fluxo-dinheiro) e coloca a
   mensagem real na caixa de sugestão. Copiar copia o texto exibido. Nada é
   enviado ao cliente daqui.
4. **▶ Rodar agente** (aba Agentes) — cada agente ganhou textarea + botão com
   confirmação forte (risco alto) → `POST /vp/agents/run {agent_id, task}` →
   resultado inline no card.

## Bugs corrigidos de brinde
- Aba Agentes lia `a.nome`/`a.papel`, mas o backend manda `name`/`role` — renderizava
  "(agente)" vazio desde sempre. Corrigido (com fallback aos nomes antigos).

## Contratos verificados no backend (smoke test live)
- `POST /vp/clientes {nome,contato,obs}` → `{status:"ok", item:{id,…,status:"lead"}}`
- `PATCH /vp/clientes/{id} {status}` → `{status:"ok"|"not_found"}` (status é string
  livre — gravamos a etapa do funil; `list_clientes` só separa por "fechado")
- `POST /jampa/responder-lead {nome,contato,interesse,obs}` → `{status,mensagem,numero}`
- `POST /vp/agents/run {agent_id,task}` → `{status,agent,name,result|message}`
- Lead real existente no store: "carlos" (id 2026070101…) — bom caso de teste.

## Banners atualizados (honestidade)
"Somente leitura nesta fase" → "escritas reais sempre com confirmação forte" (boundary,
nota do Atendimento e comentário de fronteira do módulo).

## Adendo (mesmo dia): confirmação vira 1 clique
Decisão de UX do Murillo: removida a digitação de "CONFIRMAR" no `confirmStrong` —
o modal continua mostrando endpoint/alvo/efeito/risco, mas libera com um clique.
`opts.phrase` segue aceito e ignorado (compatibilidade). **Bug crítico corrigido
junto:** o modal usava `acRiskBadge()`, que foi arquivado com a tela Ações —
qualquer ação de escrita quebrava com ReferenceError desde o minimalismo. Badge de
risco agora é local ao núcleo (`CS_RISK`).

## Próximo passo
1. Murillo testa os 4 fluxos (cadastrar lead teste, mover carlos no funil, gerar
   sugestão do squad, rodar agente com tarefa curta).
2. Commit (aguardando aprovação).
3. Pacotes seguintes da auditoria: 1 (ciclo de vida: /tasks/complete, /missions/done,
   /reminders/poll), 3 (conhecimento), 4 (miúdos).
