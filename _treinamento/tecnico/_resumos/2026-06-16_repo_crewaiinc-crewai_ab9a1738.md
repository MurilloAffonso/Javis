# Resumo: 2026-06-16_repo_crewaiinc-crewai_ab9a1738

Área: tecnico
Resumido em: 2026-06-25 (Javis / Claude assinatura)
Origem: _entrada/2026-06-16_repo_crewaiinc-crewai_ab9a1738.md

## Resumo — crewAI (framework de agentes IA)

**1) Resumo**
CrewAI é um framework open-source (53k+ estrelas) para orquestrar agentes de IA autônomos que assumem papéis ("role-playing") e colaboram entre si. A ideia central é a "inteligência colaborativa": vários agentes especializados — cada um com função, objetivo e ferramentas próprias — trabalham juntos em tarefas complexas, dividindo o trabalho como uma equipe. É o mesmo padrão de "squad de agentes" que você já vem montando no Javis (schema faz/não-faz/input/output/ferramentas).

**2) Aprendizados aplicáveis ao negócio**
- **Padrão "crew" valida sua arquitetura de squads:** o modelo de agentes com papel + ferramentas + handoff é o que o Javis já persegue. CrewAI serve de referência madura, não de substituto.
- **Especialização > generalista:** dividir tarefas (ex.: um agente de pesquisa de roteiro, um de copy, um de atendimento WhatsApp) rende mais que um único agente fazendo tudo — vale tanto pro Javis quanto pro Cérebro Jampa.
- **Orquestração sequencial vs. hierárquica:** CrewAI separa quem executa de quem coordena — espelha sua ideia do Javis como orquestrador mestre dos 17 agentes.
- **Ferramentas plugáveis por agente:** cada agente só recebe as tools que precisa — mesma disciplina do seu schema de squad e do controle de escopo.

**3) Ações concretas**
- Estudar 1 exemplo de "crew" do repo e mapear se vale como pipeline real para a Vem Passear (ex.: crew de criação de conteúdo turístico) — colar o veredito em `_resumos/`.
- Comparar o modelo de orquestração do CrewAI com o seu OS de squads atual e registrar em `_logs/` se há algo para minerar (como você fez com o Hermes: minerar, não adotar).

Próximo passo do material (NotebookLM) segue válido se quiser o aprofundamento.
