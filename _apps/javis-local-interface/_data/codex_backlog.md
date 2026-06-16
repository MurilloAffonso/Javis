# Backlog Codex Orquestrador
# Formato: - [ ] tarefa pendente | - [x] tarefa concluída
# Execute: .\backend\codex_orchestrator.ps1 (dentro de _apps/javis-local-interface)

## Conteúdo Vem Passear Jampa
- [ ] Gere 10 legendas prontas para Instagram da Vem Passear Jampa. ANTES de gerar, leia `_projetos/cerebro-jampa/linha-editorial.md` para seguir o tom, pilares e hashtag strategy. Salve em `_projetos/cerebro-jampa/posts/legendas-instagram-01.md` com título, formato (feed/reel/stories), gancho, legenda completa e hashtags para cada post. Use português caloroso e local, específico para João Pessoa e piscinas naturais.
- [ ] Gere 5 roteiros de Reel completos para Vem Passear Jampa. Leia PRIMEIRO `_projetos/cerebro-jampa/linha-editorial.md` (seção formatos de Reel) e `_projetos/cerebro-jampa/seo-plano.md` (seção Instagram SEO). Cada roteiro deve ter: título do reel, gancho 3s, desenvolvimento (cenas, fala, legenda de tela), CTA final, hashtags, palavras-chave SEO. Salve em `_projetos/cerebro-jampa/posts/roteiros-reel-01.md`.
- [ ] Crie templates de resposta WhatsApp para Vem Passear Jampa. Leia `_projetos/cerebro-jampa/linha-editorial.md` para o tom. Crie templates para: (1) primeiro contato do turista, (2) perguntas sobre maré/horário, (3) perguntas sobre preço, (4) confirmação de reserva, (5) pós-passeio pedindo avaliação no Google. Salve em `_projetos/cerebro-jampa/posts/templates-whatsapp.md`.
- [ ] Analise `_apps/javis-local-interface/frontend/style.css` e `frontend/app.js`. Identifique 3 melhorias visuais ou de UX que podem ser feitas sem quebrar nada existente. Implemente as melhorias diretamente. Ao final, liste o que mudou.

## Interface Javis
- [ ] No arquivo `_apps/javis-local-interface/frontend/app.js`, melhore a função `renderAgentGallery()` (ou crie se não existir — busque em app.js como a galeria é renderizada). Adicione para cada card de agente: um badge de "última atividade" (ex: "há 3min"), um indicador de tarefas em fila (número), e um botão "Convocar" que faz switchView('chat') e preenche o input com "@[nome do agente]". Seja cirúrgico, não quebre IDs existentes.

## Cérebro Jampa — SEO
- [ ] Implemente as 5 quick wins de SEO identificadas no plano `_projetos/cerebro-jampa/seo-plano.md`. Para cada quick win, crie um arquivo de checklist em `_projetos/cerebro-jampa/seo-checklist.md` com: o que fazer, como fazer passo a passo, quem faz (Murillo/Nova/Midas), tempo estimado. Seja específico e acionável, não genérico.
