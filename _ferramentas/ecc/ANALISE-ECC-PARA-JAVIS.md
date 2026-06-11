# Análise do ECC para o Javis

Data: 2026-06-11  
Repositório: https://github.com/affaan-m/ECC  
Clone em: `_referencias/ECC/`

---

## 1. O que é o ECC

ECC (Everything Claude Code) é uma coleção curada de:
- **Guardrails** — regras de defesa contra prompt injection, manipulação de identidade, vazamento de dados
- **261+ skills** — instruções especializadas para domínios (TypeScript, Python, Go, Android, iOS, Rust, etc.)
- **Rules** — padrões de código por linguagem
- **Tests** — infraestrutura de testes para validar o próprio ECC
- **Suporte multi-IDE** — `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.agents/`

É essencialmente um repositório compartilhável de padrões para times que usam Claude Code
em projetos grandes e profissionais.

---

## 2. O que serve para o Javis

### 2a. Guardrails (`.claude/rules/everything-claude-code-guardrails.md`)

**Muito útil.** Cobre:
- Defesa contra prompt injection (unicode, homoglyphs, zero-width chars, embedded commands)
- Nunca revelar credenciais, tokens, chaves de API
- Nunca gerar conteúdo malicioso (exploits, malware, phishing)
- Preservar identidade e persona — não aceitar substituição de regras
- Tratar conteúdo externo/fetched como não-confiável

**Para o Javis:** adaptar como regra de segurança no AGENTS.md e CLAUDE.md.

### 2b. Skill: `error-handling`

**Útil.** Princípios aplicáveis ao Python do Javis:
- Fail fast and loudly — erros na fronteira, não silenciosos
- Typed errors over string messages
- User messages ≠ developer messages (log o contexto completo, mostre mensagem amigável)
- Never swallow errors silently (todo `except` deve logar ou re-raise)

**Para o Javis:** aplicar a `command_router.py`, `actions.py`, `voice_bridge.py`.

### 2c. Skill: `verification-loop`

**Útil.** Fases de verificação antes de PR/integração:
1. Build verification
2. Type check
3. Lint check
4. Test suite

**Para o Javis:** adaptar para Python — verificar antes de integrar ao voice pipeline.

### 2d. Skill: `architecture-decision-records`

**Útil.** Formato ADR leve (Context, Decision, Alternatives, Consequences).

**Para o Javis:** já temos `_logs/` com decisões — pode formalizar com o formato ADR.

### 2e. Skill: `deep-research`

**Parcialmente útil.** Metodologia de pesquisa multi-fonte (sem depender dos MCPs externos).

**Para o Javis:** adotar o princípio de pesquisar antes de implementar, sem usar firecrawl/exa.

### 2f. Guardrail: Commit Workflow

**Útil.** Conventional commits com prefixos `fix`, `feat`, `docs`, `test`, `chore`.

**Para o Javis:** adotar quando Murillo aprovar commits.

---

## 3. O que não serve

| Componente | Motivo |
|---|---|
| 240+ domain skills (videodb, visa, blender, cisco...) | Domínios irrelevantes para o Javis |
| Plugin system (.claude-plugin, .codex-plugin) | Sobrecomplexidade — Javis não tem pipeline de plugin |
| Multi-IDE sync (.cursor, .gemini, .codex) | Javis usa só Claude Code |
| `deep-research` com firecrawl/exa | MCPs externos não configurados |
| `agent-payment-x402`, `carrier-relationship-management` | Completamente fora do escopo |
| Node.js/npm infrastructure | Backend do Javis é Python puro |
| CI/CD pipelines do ECC | Não temos CI no Javis agora |
| Codex/Codex-plugin config | Javis não usa Codex |

---

## 4. O que é perigoso importar agora

| Risco | Motivo |
|---|---|
| **Hooks automáticos** (`.cursor/hooks/`) | Podem executar comandos em background sem aprovação |
| **Install scripts** (`install.ps1`, `install.sh`) | Instalam coisas globalmente sem controle |
| **Plugin manifests** | Ativam sistemas externos sem revisão |
| **Agents do ECC** (`.agents/plugins/`) | Agentes autônomos que podem agir sem aprovação |
| **`ecc-tools-cost-audit`** | Requer acesso a APIs externas |
| **`autonomous-loops`** skill | Permite loops autônomos — perigoso sem guardrails Javis |
| **`autonomous-agent-harness`** | Mesmo problema |

**Regra:** não importar nada que execute código automaticamente ou acesse sistemas externos.

---

## 5. O que pode ser adaptado com segurança

| Componente ECC | Adaptação para Javis |
|---|---|
| Guardrails de prompt defense | → nova seção em AGENTS.md |
| Princípios de error-handling | → melhorar try/except no backend Python |
| Verification-loop (fases) | → skill `testar-antes-de-integrar.md` |
| ADR format | → padronizar `_logs/` |
| Research-first methodology | → skill `research-first.md` |
| Commit conventions | → documentar quando Murillo aprovar commits |
| Quality gate concept | → skill `quality-gate.md` |
| Checkpoint before change | → skill `checkpoint-antes-de-mudar.md` |

---

## 6. Skills/regras mais relevantes para o Javis

**Prioridade 1 — adaptar agora:**
1. `error-handling` → error boundaries no Python backend
2. `verification-loop` → checklist de verificação antes de integrar
3. Guardrails de prompt defense → reforçar AGENTS.md

**Prioridade 2 — referência futura:**
4. `architecture-decision-records` → padronizar `_logs/`
5. `deep-research` (sem MCPs externos) → metodologia de pesquisa
6. Conventional commits → para quando Murillo aprovar commits

---

## 7. O que não deve ser usado por enquanto

- Qualquer coisa que execute código automaticamente
- Qualquer skill que dependa de MCPs externos (firecrawl, exa, x402)
- O plugin system do ECC completo
- O sistema de agentes autônomos
- Hooks de qualquer IDE
- Scripts de instalação

**Revisitar:** quando o Javis estiver mais maduro e com CI/CD próprio.
