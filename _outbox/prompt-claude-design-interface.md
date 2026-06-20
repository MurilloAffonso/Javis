# Prompt pra rodar no Claude Design Web — Redesenho didático do Javis

> Cole o bloco abaixo no Claude Design Web. Anexe junto a screenshot
> `interface-atual-chat.png` (a interface de hoje) pra ele ver o ponto de partida.
> Depois me traga o resultado que EU implemento no app real (index.html/app.js/style.css).

---

## BRIEF — Redesenho da interface do "Javis" (assistente pessoal operacional)

### Contexto
O Javis é um assistente pessoal e operacional (estilo "JARVIS") de **Murillo**,
empreendedor de **turismo** (marca Vem Passear Jampa, João Pessoa/PB). Ele
**não é programador**. Usa o Javis por **voz e texto** pra: conversar, orquestrar
agentes de IA, acompanhar tarefas/missões em quadro, e gerir o marketing da
empresa. Hoje é uma web app local (HTML/CSS/JS puro, tema escuro).

### Problema (o mais importante)
A interface atual é **bonita mas NÃO didática**: parece painel de nave, é densa,
cheia de controles pequenos e **jargão técnico** (Conclave, AIOS Master, motor,
RAG) sem explicação. Não há "comece por aqui". Pra um dono de empresa não-técnico,
é difícil saber o que clicar e o que cada área faz.

### Objetivo
Redesenhar pra ficar **didático, guiado e fácil** — sem perder a identidade
"assistente inteligente". Clareza acima de "efeito visual". Tudo em **português**.

### Estrutura atual (10 áreas na barra lateral — preciso simplificar/agrupar)
Chat · Agentes · Mente (organograma dos agentes) · Workflows · Sala dos agentes ·
Quadro (kanban de tarefas) · Fluxo VP (pipeline de marketing em raias) · Projetos ·
Treino · Integrações.

### Metas de design (o que eu quero que você entregue)
1. **Reduzir carga cognitiva:** agrupe as 10 áreas em 3-4 seções com rótulos
   claros (ex.: "Conversar", "Meu trabalho", "Time de IA", "Ajustes"). Esconda o
   avançado sob "mais".
2. **Linguagem simples:** troque/explique o jargão. Cada área com 1 frase do que
   faz, visível (subtítulo ou tooltip). Ex.: "Mente = quem é cada agente do seu time".
3. **Tela inicial "Comece aqui":** ao abrir, uma home que em 10 segundos diz o que
   dá pra fazer e leva pra ação principal (conversar / ver as tarefas da semana).
4. **Uma ação primária por tela** (botão claro), o resto secundário.
5. **Estados vazios que ENSINAM:** "Nenhuma missão ainda — clique + pra criar a
   primeira", em vez de tela morta.
6. **Hierarquia visual forte:** título → subtítulo explicativo → conteúdo. Espaço
   pra respirar, menos caixinhas competindo.
7. **Onboarding leve:** um tour de 3-4 passos ou dicas contextuais na 1ª vez.
8. Manter a "alma" do Javis (pode manter um elemento visual de assistente, tipo o
   orbe), mas o **centro tem que ser a conversa/ação**, não o enfeite.

### Restrições
- Tema escuro pode ficar, mas **prioridade é legibilidade** (contraste, fonte
  maior, menos elementos minúsculos).
- Vai virar HTML/CSS/JS simples — nada de framework pesado.
- Mobile-friendly seria ótimo (ele usa muito no celular/voz).
- Identidade: assistente pessoal + marca Vem Passear (turismo, mar, João Pessoa)
  pode inspirar a paleta (azuis de mar, areia), mas sem virar site de viagem.

### Entregáveis que eu quero de você
1. **Design system enxuto**: paleta, tipografia, espaçamentos, componentes-base
   (card, botão, item de menu, estado vazio, tooltip).
2. **3 telas-chave** redesenhadas: (a) Home "Comece aqui", (b) Conversa/Chat,
   (c) Quadro de tarefas (kanban) OU o Fluxo de marketing em raias.
3. **O padrão didático**: como os subtítulos/tooltips/estados vazios ensinam o
   usuário, com exemplos de texto pronto em português.
4. Antes/depois explicado: o que mudou e por quê ficou mais fácil.
