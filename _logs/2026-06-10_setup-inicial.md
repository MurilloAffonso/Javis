# Setup Inicial do Javis

Data: 2026-06-10
Sessão: Arquiteto Técnico / Configuração Base

## O que foi feito

### Estrutura criada

- AGENTS.md — instruções para agentes AI
- CLAUDE.md — regras para Claude Code no projeto
- README.md — visão geral, arquitetura, comandos
- .gitignore — ignora node_modules, pyc, .env, etc.
- _memoria/, _ideias/, _projetos/, _prompts/, _skills/ — estrutura de trabalho
- _logs/, _inbox/, _outbox/ — fluxo de comunicação
- _ferramentas/leanctx/STATUS.md — status do LeanCTX
- _ferramentas/headroom/STATUS.md — status do Headroom (com problema documentado)

### LeanCTX

- Já estava instalado (v3.7.5) — nenhuma ação necessária
- MCP já configurado no Claude Code ✅
- Doctor: 25/26 (1 aviso menor: alias shell, sem impacto)
- Gain: 88% compressão, 924K tokens salvos, $2.38 economizados

### Headroom

- Instalação FALHOU por incompatibilidade Python 3.14 + PyO3 0.22.6
- PyO3 0.22.6 suporta no máximo Python 3.13
- Nada foi instalado parcialmente — sistema limpo
- Workaround sugerido: PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
- Aguardando aprovação de Murillo

## Decisões Tomadas

1. LeanCTX como modo padrão de operação — já funcionando
2. Headroom em espera — aguardando aprovação do workaround ou nova versão
3. Git init separado não foi feito — javis está dentro do repo home do usuário
   Observação: considerar fazer `git init` dentro de javis para isolamento
4. Nenhum commit feito
5. Nenhum push feito
6. Nenhum projeto externo tocado

## Próximos Passos

- [ ] Murillo aprovar ou rejeitar workaround Headroom
- [ ] Se aprovado: `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install headroom-ai`
- [ ] Depois: testar `headroom wrap claude` em sessão separada
- [ ] Criar _memoria/murillo.md com contexto básico
- [ ] Definir primeiro projeto ativo em _projetos/
- [ ] Considerar git init dentro de javis para isolamento
