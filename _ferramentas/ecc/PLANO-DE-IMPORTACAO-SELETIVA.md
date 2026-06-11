# Plano de Importação Seletiva — ECC para Javis

Data: 2026-06-11

---

## Classificação por grupo

### A) Importar/adaptar agora

| Componente | Origem no ECC | Destino no Javis | Ação |
|---|---|---|---|
| Prompt defense baseline | `.claude/rules/everything-claude-code-guardrails.md` | nova seção em `AGENTS.md` | Adaptar — remover referências a TS/JS |
| Error-handling principles | `skills/error-handling/SKILL.md` | backend Python (`actions.py`, `voice_bridge.py`) | Aplicar padrões: fail fast, typed errors, never swallow |
| Checkpoint antes de mudar | conceito ECC | `_skills/checkpoint-antes-de-mudar.md` | Criar skill nova |
| Quality gate | conceito ECC | `_skills/quality-gate.md` | Criar skill nova |
| Testar antes de integrar | `skills/verification-loop/SKILL.md` | `_skills/testar-antes-de-integrar.md` | Adaptar para Python/Javis |
| Research first | `skills/deep-research/SKILL.md` | `_skills/research-first.md` | Adaptar — sem MCPs externos |
| Auditar segurança | `skills/automation-audit-ops` | `_skills/auditar-seguranca-local.md` | Criar versão Javis |

---

### B) Estudar melhor antes de usar

| Componente | Por que estudar mais | Quando revisitar |
|---|---|---|
| `architecture-decision-records` | Formato ADR pode ser muito formal para o ritmo do Javis | Quando o projeto tiver 5+ ADRs em `_logs/` |
| `agent-introspection-debugging` | Útil quando o Javis ganhar agentes mais complexos | Quando tivermos mais de 1 agente ativo |
| `codebase-onboarding` | Para quando outros colaboradores precisarem entender o Javis | Quando o projeto crescer |
| `coding-standards` (Python) | Pode conflitar com convenções atuais | Revisar junto com o backend quando chegar em v1 |
| Conventional commits | Já temos regra de não commitar sem aprovação | Ativar quando Murillo aprovar o primeiro commit |

---

### C) Guardar para o futuro

| Componente | Quando usar | Pré-requisito |
|---|---|---|
| `ai-regression-testing` | Quando o Command Router tiver histórico de 50+ comandos reais | Logs suficientes para baseline |
| `agent-architecture-audit` | Quando o Javis tiver 3+ agentes integrados | Javis Local Interface v1+ |
| `benchmark-optimization-loop` | Quando o voice pipeline precisar de otimização de latência | Pipeline conectado ao voice_bridge |
| `e2e-testing` | Quando o frontend ganhar backend servido (FastAPI) | v1 da Local Interface |
| CI/CD patterns | Quando o projeto tiver pipeline automatizado | Aprovação de Murillo + setup de CI |
| Multi-IDE support | Se Murillo quiser usar Cursor ou Codex | Aprovação explícita |

---

### D) Não usar

| Componente | Motivo |
|---|---|
| Plugin system completo (`.claude-plugin`, `.codex-plugin`) | Sobrecomplexidade, não é o modelo do Javis |
| Hooks automáticos de qualquer IDE | Executam código sem aprovação — contra as regras do Javis |
| Install scripts (`install.ps1`, `install.sh`) | Instalam globalmente sem controle |
| `autonomous-loops` skill | Loops autônomos sem aprovação — proibido no Javis |
| `autonomous-agent-harness` | Mesmo problema |
| `agent-payment-x402` | Pagamentos automáticos — completamente proibido |
| `ecc-tools-cost-audit` | Requer APIs externas não configuradas |
| `deep-research` com firecrawl/exa | MCPs externos não disponíveis |
| `.cursor/`, `.gemini/`, `.codex/` configs | Javis usa só Claude Code |
| Domain skills (videodb, visa, blender, cisco, etc.) | Sem relação com o Javis |
| 200+ skills de framework específico (Angular, Flutter, etc.) | Não usados no Javis |

---

## Prioridade de execução

**Agora (esta sessão):**
1. Adaptar guardrails de prompt defense → `AGENTS.md`
2. Criar 5 skills inspiradas no ECC
3. Melhorar error handling no backend Python
4. Criar testes em `_apps/javis-local-interface/tests/`

**Próxima sessão (com aprovação de Murillo):**
5. Formalizar ADR format nos `_logs/`
6. Avaliar conventional commits

**Futuro indefinido:**
7. Tudo na categoria C e D
