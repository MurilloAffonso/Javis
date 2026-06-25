# Resumo: 2026-06-16_video_agentes-de-ia-o-que-s-o-e-como-trabalhar-com-eles-dicion-rio_b6e2875a

Área: tecnico
Resumido em: 2026-06-25 (Javis / Claude assinatura)
Origem: _entrada/2026-06-16_video_agentes-de-ia-o-que-s-o-e-como-trabalhar-com-eles-dicion-rio_b6e2875a.md

Heads-up: o arquivo só traz o **título e os metadados** do vídeo — não tem transcrição nem notas de conteúdo (o próprio arquivo diz que falta subir no NotebookLM). Então resumo abaixo o tema "Agentes de IA" do canal Código Fonte TV, aplicado ao teu contexto. Quando processar o vídeo no NotebookLM, dá pra refinar com as falas exatas.

## 1) Resumo
Agente de IA é um modelo de linguagem com **autonomia para agir**: ele não só responde, mas decide passos, usa ferramentas (buscar, calcular, mandar mensagem, abrir sistema) e encadeia ações até cumprir um objetivo. A diferença para um chatbot comum é o ciclo *pensar → agir → observar resultado → ajustar*. Trabalhar com agentes é menos sobre "perguntar" e mais sobre **dar objetivo, ferramentas e limites claros**.

## 2) Aprendizados aplicáveis ao negócio
- **Agente = objetivo + ferramentas, não só prompt.** O Javis já segue isso (skill > treino). Pra Vem Passear, vale mapear quais *ferramentas reais* cada agente precisa (WhatsApp, agenda, tabela de roteiros) antes de pedir autonomia.
- **Autonomia exige limites.** Agente que age sozinho precisa de "trilhos" (o que pode e não pode fazer) — exatamente o papel do teu CLAUDE.md e dos guardrails de git/escopo.
- **Encadeamento de tarefas é o ganho real.** Um agente de atendimento Vem Passear pode: receber lead no WhatsApp → consultar disponibilidade → montar orçamento → registrar no CRM, sem você no meio.
- **Ferramentas certas valem mais que modelo melhor.** Reforça a tua tese do OpenRouter: o diferencial é o app/integração, não trocar de LLM.

## 3) Ações concretas
1. **Definir 1 agente-piloto Vem Passear** (ex.: "Atendente de roteiros") listando objetivo, 3-4 ferramentas que ele precisa e os limites — no formato de SKILL.md que você já usa.
2. **Subir o vídeo no NotebookLM** e colar a transcrição-resumo em `_resumos/`, pra trocar este resumo genérico por um baseado no conteúdo real.
