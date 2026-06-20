# O coração do Javis: 1º fluxo REAL ponta a ponta — 20/06

## Contexto
Murillo trouxe um diagnóstico afiado: a interface já parece produto, mas "tela
bonita não é Javis real — Javis real é quando cada botão executa, registra,
aprende e pede aprovação". Pediu pra PARAR de criar tela e fazer UM fluxo
funcionar de verdade. Escolheu o fluxo:

> "Javis, cria a pauta da semana da Vem Passear" → briefing → Nova → tarefa no
> Quadro → pede aprovação → registra no log.

## O que foi feito
Implementei esse fluxo exato como uma ferramenta que o CHAT aciona em linguagem
natural — ligando peças que já existiam mas estavam soltas.

- **`backend/agent.py`**:
  - Nova tool `gerar_pauta_vp` (sem parâmetro) no catálogo do agente.
  - `_fluxo_pauta_vp()`: o fluxo real em 5 passos —
    1. chama `vp_squad.run("nova", ...)` (a agente Nova, na assinatura);
    2. salva em `_projetos/cerebro-jampa/posts/pauta-semana.md`;
    3. registra no Quadro (`mission_board.set_task_done` → Raia 1 concluída);
    4. **para no Gate 1** e devolve mensagem pedindo a aprovação do Murillo;
    5. grava `logger.log(...)` com intent, agente, arquivo, gate pendente.

## Verificação (real, disparado pelo chat de verdade)
`server._brain("cria a pauta da semana da Vem Passear")`:
- ✅ **Chat escolheu a ferramenta** certa: `tools: ['gerar_pauta_vp']`.
- ✅ **Nova gerou** uma pauta de qualidade: 3 posts, pilares variados, 1 venda
  (regra respeitada), e — importante — usou `[CONFIRMAR COM MURILLO]` em maré/
  vaga/preço/horário em vez de inventar (Regra Ouro + regra do criativo).
- ✅ **Arquivo** `pauta-semana.md` atualizado.
- ✅ **Quadro**: Raia 1 (t0) = `done`.
- ✅ **Log**: `intent=gerar_pauta_vp, agente=nova, gate=1 pendente`.
- ✅ **Aprovação**: o fluxo PAROU no Gate 1 pedindo o OK do Murillo (não avançou
  pro Design sozinho).
- `pytest tests/ -q` → 71 passed.

Latência: ~100s (geração da Nova + rodadas de decisão da ferramenta na assinatura).
É uma operação semanal pesada — aceitável, mas é o gargalo conhecido.

## O que isso significa
O loop **chat → intenção → agente → arquivo → quadro → aprovação → log** está
VIVO. É o "mínimo funcionando de verdade" que o Murillo pediu — o coração real,
não cinematográfico. As peças (history_store, mission_board, vp_squad, logger,
gates) já existiam; o que faltava era a costura num fluxo único disparado por fala.

## Roadmap do Murillo (registrado, ainda não feito)
Ele mapeou fases maiores: login simples, banco de dados (SQLite: projects/agents/
tasks/logs/approvals/memories...), mais integrações (Sheets, Evolution/WhatsApp,
Gmail/Notion). Também bugs de UI: aviso --no-sandbox, scroll horizontal no
Workflows, números fixos no topo ("8 agentes / 0 msgs"), chat lateral apertado.
Tudo válido como próximas fases — mas o CORAÇÃO já provou que bate.

**Sem commit/push — Murillo revisa e decide.**
