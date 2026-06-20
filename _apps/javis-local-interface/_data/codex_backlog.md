# Backlog Codex Orquestrador
# Formato: - [ ] tarefa pendente | - [x] tarefa concluída
# codex_orchestrator.py/.ps1 foram removidos (auto-commitavam sem aprovação,
# contra a regra do CLAUDE.md). Acione o Codex direto quando precisar.

## Conteúdo Vem Passear Jampa
- [x] Gere 10 legendas prontas para Instagram da Vem Passear Jampa. ANTES de gerar, leia `_projetos/cerebro-jampa/linha-editorial.md` para seguir o tom, pilares e hashtag strategy. Salve em `_projetos/cerebro-jampa/posts/legendas-instagram-01.md` com título, formato (feed/reel/stories), gancho, legenda completa e hashtags para cada post. Use português caloroso e local, específico para João Pessoa e piscinas naturais.
- [x] Gere 5 roteiros de Reel completos para Vem Passear Jampa. Leia PRIMEIRO `_projetos/cerebro-jampa/linha-editorial.md` (seção formatos de Reel) e `_projetos/cerebro-jampa/seo-plano.md` (seção Instagram SEO). Cada roteiro deve ter: título do reel, gancho 3s, desenvolvimento (cenas, fala, legenda de tela), CTA final, hashtags, palavras-chave SEO. Salve em `_projetos/cerebro-jampa/posts/roteiros-reel-01.md`.
- [x] Crie templates de resposta WhatsApp para Vem Passear Jampa. Leia `_projetos/cerebro-jampa/linha-editorial.md` para o tom. Crie templates para: (1) primeiro contato do turista, (2) perguntas sobre maré/horário, (3) perguntas sobre preço, (4) confirmação de reserva, (5) pós-passeio pedindo avaliação no Google. Salve em `_projetos/cerebro-jampa/posts/templates-whatsapp.md`.
- [x] Analise `_apps/javis-local-interface/frontend/style.css` e `frontend/app.js`. Identifique 3 melhorias visuais ou de UX que podem ser feitas sem quebrar nada existente. Implemente as melhorias diretamente. Ao final, liste o que mudou.

## Interface Javis
- [x] No arquivo `_apps/javis-local-interface/frontend/app.js`, melhore a função `renderAgentGallery()` (ou crie se não existir — busque em app.js como a galeria é renderizada). Adicione para cada card de agente: um badge de "última atividade" (ex: "há 3min"), um indicador de tarefas em fila (número), e um botão "Convocar" que faz switchView('chat') e preenche o input com "@[nome do agente]". Seja cirúrgico, não quebre IDs existentes.

## Cérebro Jampa — SEO
- [x] Implemente as 5 quick wins de SEO identificadas no plano `_projetos/cerebro-jampa/seo-plano.md`. Para cada quick win, crie um arquivo de checklist em `_projetos/cerebro-jampa/seo-checklist.md` com: o que fazer, como fazer passo a passo, quem faz (Murillo/Nova/Midas), tempo estimado. Seja específico e acionável, não genérico.

## Pipeline Marketing — Vem Passear Jampa
# Adaptado do Fluxograma "Gestão Processos FAST" (ver _outbox/fluxograma-analise-marketing.md).
# Tradução pra realidade da Vem Passear: Murillo = dono/aprovador (não há cliente externo);
# este Quadro Kanban = o "Monday" da agência; cada raia passa por conferência antes de avançar;
# reprovado volta pra correção, não pula etapa. Raias: Conteúdo → Design → Copy → Distribuição.
- [x] [Conteúdo] Planejar a pauta da semana: revisar `_projetos/cerebro-jampa/linha-editorial.md` e `_projetos/cerebro-jampa/posts/post-catamara-piscinas-2026-06-16.md`, definir os próximos 3 posts (tema, formato, fotos necessárias) e salvar em `_projetos/cerebro-jampa/posts/pauta-semana.md`.
- [ ] [Gate 1 — aprovação Murillo] Conferir `pauta-semana.md` e aprovar (só o Murillo marca). Reprovado = ajustar a pauta e refazer antes de seguir pro Design.
- [ ] [Design] Produzir os criativos da pauta aprovada: rodar `_projetos/cerebro-jampa/gerar_carrossel.py` com as fotos em `_projetos/cerebro-jampa/imagens/_FOTOS-AQUI/`, gerando as peças em `_projetos/cerebro-jampa/outputs/`.
- [ ] [Conferência interna — Design] Revisar as peças em `_projetos/cerebro-jampa/outputs/`: consistência de marca (cores/Design System). Reprovado = corrigir a arte e voltar, sem avançar pra Copy.
- [ ] [Copy] Escrever as legendas/copy dos posts aprovados seguindo o tom da `linha-editorial.md`, e anexar cada copy ao seu post em `_projetos/cerebro-jampa/posts/pauta-semana.md`.
- [ ] [Gate 2 — aprovação Murillo] Conferir peças + copy finais juntas e aprovar pra publicar (só o Murillo marca). Reprovado = volta pra Design ou Copy conforme o erro.
- [ ] [Distribuição] Publicar os posts aprovados no Instagram e registrar o resultado (alcance/engajamento) em `_projetos/cerebro-jampa/posts/pauta-semana.md`.
