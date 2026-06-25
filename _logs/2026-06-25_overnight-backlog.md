# Backlog noturno — loop de melhorias (2026-06-25)

Loop autônomo enquanto Murillo dorme. Regras: SEM git commit/push, SEM apagar,
SEM enviar pra fora, só dentro de `javis`, tudo aditivo/reversível, rodar
`pytest` a cada mudança e reverter se quebrar. Registrar tudo em
`2026-06-25_overnight-progress.md`.

A cada acordar: pegar o PRÓXIMO item não-feito, implementar, verificar (testes +
endpoint/screenshot), marcar [x], logar progresso, reagendar.

## Fila
- [x] 1. Ingerir scripts do backend → catálogo + /ui/scripts + aba Scripts (Config)
- [x] 2. COMANDO DE VOZ (pedido do Murillo): botão 🎙️ no chat do Command Center —
      grava → /transcribe (OpenAI) → /chat (_brain, orquestra todos os projetos)
      → fala a resposta com /tts (Piper local). Feito + 142 testes OK.
- [x] 3. Telemetria rica: brain vem do SQLite (messages) no telemetry_adapter;
      Métricas mostra Brain + Tools (tools da conversa ao vivo). 142 testes OK.
- [x] 4. Aprovações automáticas: gate requires_approval no app_ui.py cria aprovação
      real (repo.approvals.add) → aparece no painel direito do Command Center.
- [x] 5. World interativo: torre pulsa quando há agente executando; clicar no setor
      abre o chat do 1º agente dele.
- [x] 6. Agente clicável (sidebar/World) → abre o Chat daquele agente. (já no código)
- [x] 7. Dashboards reais Vem Passear: ui_state.vp_metrics() lê _data/vp_*.json e
      injeta KPIs reais no manifesto (reservas 1, receita R$3, criativos 2).
- [x] 8. Busca global: topbar/sidebar → viewSearch no canvas (agentes/squads/skills/
      scripts), agente clicável abre o chat.
- [x] 9. Projeto externo com status real: ui_state.get_projects enriquece cerebro-jampa
      via project_registry → card mostra "online".
- [x] 10. Doc do sistema completo: COMMAND_CENTER.md (arquitetura, telas, rodar, segurança).
- [x] 11. Polimento visual: aplicado ao longo dos ciclos (fundo quente, nav em tiles,
      rodapé glow, skills multicor, World isométrico, botão de voz). 0 erros de console.

## FILA COMPLETA — modo verificação a partir daqui

## Quando a fila acabar
Entrar em modo verificação: health-check dos serviços a cada ciclo, rodar testes,
e deixar o relatório da manhã em progress.md. Não inventar mudanças arriscadas.
