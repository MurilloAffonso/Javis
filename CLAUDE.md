# CLAUDE.md — Regras para Claude Code no Projeto Javes

## Identidade do Projeto

Este é o projeto **Javes** — assistente pessoal e operacional de Murillo.

Diretório raiz: `C:\Users\noteacer\Desktop\javis`

Javes é independente e **não mistura contexto automaticamente**:
- **Cérebro Jampa** e **Vem Passear Jampa** são projetos **externos** — conectados ao Javes **por registro**, com autorização e fronteira clara (ver `_docs/GLOSSARIO-NOMES.md`). Não fazem parte do núcleo do Javes e não são herdados sem registro/seleção explícita.
- Não tem relação com qualquer projeto financeiro ou de trading.

---

## Regras de Operação

### Escopo
- Trabalhe SOMENTE dentro de `C:\Users\noteacer\Desktop\javis`
- Nunca leia ou modifique arquivos fora desta pasta sem aprovação explícita
- Não misture contexto de outros projetos automaticamente — projetos externos só entram por registro autorizado, com fronteira clara

### Commits e Git
- NÃO faça `git commit` sem aprovação explícita de Murillo
- NÃO faça `git push` nunca, a menos que Murillo peça explicitamente
- NÃO faça `git add .` sem revisar o que está sendo staged
- Ao criar arquivos novos, informe Murillo antes de stagar

### Edições de Arquivo
- NÃO delete arquivos
- NÃO sobrescreva arquivos existentes sem ler o conteúdo atual primeiro
- Prefira edições cirúrgicas (Edit) a reescritas completas (Write)
- Sempre use `ctx_read(path, "full")` antes de qualquer edição

### Configurações e Variáveis de Ambiente
- NÃO altere `ANTHROPIC_BASE_URL` globalmente
- NÃO configure proxy permanente sem aprovação
- NÃO instale pacotes globais sem explicar o impacto
- Se um comando exigir `sudo` ou permissão de administrador, PARE e explique

---

## Economia de Tokens — Como Operar

Este projeto usa **LeanCTX** como MCP server para reduzir consumo de tokens.

Regras obrigatórias:

| Em vez de | Use |
|-----------|-----|
| `Read` / `cat` | `ctx_read(path, mode)` |
| `Grep` / `rg` | `ctx_search(pattern, path)` |
| `Bash` / `Shell` | `ctx_shell(command)` |
| `ls` / `find` | `ctx_tree(path, depth)` |

Modos do `ctx_read`:
- `full` — antes de qualquer edição
- `signatures` — para entender API sem editar
- `diff` — para verificar após edição
- `map` — para arquivos grandes (>500 linhas)
- `lines:N-M` — quando sabe o trecho exato

**Headroom** (`headroom wrap claude`) é usado apenas em modo de teste.
NÃO configure como padrão permanente.

---

## Fluxo de Trabalho Padrão

### Ao receber uma tarefa
1. Leia o contexto em `_inbox/` se houver entrada nova
2. Oriente-se com `ctx_overview(task)`
3. Localize o que precisa com `ctx_search`
4. Leia com `ctx_read` antes de editar
5. Edite com `Edit` nativo (ou `ctx_edit` se necessário)
6. Verifique com `ctx_read(path, "diff")`
7. Registre decisões em `_logs/YYYY-MM-DD_decisao.md`

### Ao finalizar uma tarefa
1. Coloque o resultado em `_outbox/` se for uma entrega
2. Registre o que foi feito e o que falta em `_logs/`
3. NÃO faça commit sem aprovação

---

## Registro de Decisões

Para decisões técnicas importantes, crie um arquivo em `_logs/` com o formato:

```
_logs/YYYY-MM-DD_nome-da-decisao.md
```

Conteúdo mínimo:
- O que foi decidido
- Por quê
- Alternativas consideradas
- Próximo passo

---

## Estrutura de Pastas

```
javis/
├── AGENTS.md          — instruções para agentes
├── CLAUDE.md          — este arquivo
├── JAVIS-CEREBRO.md   — identidade / mente do Javes
├── README.md          — visão geral do projeto
├── docker-compose.yml — orquestração de serviços
├── javis-start.bat    — launcher local
│
├── _apps/             — código de aplicação (javis-local-interface: backend + frontend)
├── _estado/           — JSONs de estado vivo (brain_ativo, proximos-passos, estado-atual)
├── _memoria/          — memórias persistentes
├── _ideias/           — ideias capturadas
├── _projetos/         — contexto de projetos ativos
├── _prompts/          — prompts reutilizáveis
├── _skills/           — skills personalizadas
├── _arquitetura/      — decisões arquiteturais
├── _treinamento/      — material de treino de agentes
├── _referencias/      — estudos externos (ECC, silero-vad, etc.)
├── _templates/        — modelos reutilizáveis
├── _sessoes/          — histórico de sessões
├── _logs/             — decisões e registros (inclui _logs/screenshots/ e _logs/dumps/)
├── _inbox/            — entradas para processar
├── _outbox/           — saídas elaboradas
├── _arquivo/          — gaveta de arquivos abandonados (revisar antes de deletar)
├── docs/              — documentação geral
└── _ferramentas/
    ├── leanctx/       — config e notas sobre LeanCTX
    └── headroom/      — config e notas sobre Headroom
```

---

## Misturar com Outros Projetos

**Nunca misture o contexto do Javes com outros projetos.**

Se Claude Code estiver sendo usado em múltiplos projetos, certifique-se de que:
- O CLAUDE.md do Javes está ativo
- O contexto de outros projetos não está no mesmo contexto de sessão
- Variáveis globais não foram alteradas por outros projetos
