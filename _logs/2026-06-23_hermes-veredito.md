# Veredito: Hermes Agent lado a lado × Javis

**Data:** 2026-06-23
**Contexto:** `_logs/2026-06-23_hermes-analise.md` (estrutura/comparação). Aqui o
resultado do tour real (instalado, configurado, testado nos 4 pilares). Custo
do tour: **US$0** (só modelos free do OpenRouter). Javis ficou 100% intacto —
Hermes vive isolado em `~/.hermes` (`C:\Users\noteacer\AppData\Local\hermes`).

---

## Resultado dos 4 pilares

| Pilar | Resultado | Observação |
|---|---|---|
| **Multi-modelo barato** | ✅ funciona | Catálogo free do OpenRouter é **volátil** — 3 dos 4 modelos free testados (`llama-3.3-70b:free`, `nex-n2-pro:free`, `deepseek-v3:free`, `qwen2.5-72b:free`) estavam fora do ar/descontinuados na hora do teste. `openai/gpt-oss-20b:free` funcionou. Troca de modelo via `hermes config set model.default` é simples. |
| **Memória persistente** | ✅ funciona | Disse "meu nome é Murillo, gosto de respostas curtas" numa invocação; em invocação **separada** (novo processo, sem `--continue`) ele lembrou nome + preferência. Persiste em `state.db` (SQLite), bate com o documentado (FTS5 + sumarização). |
| **Gateway multi-plataforma** | ✅ funciona | Bot novo `@Jampa01bot` criado via BotFather, configurado via `TELEGRAM_BOT_TOKEN` no `.env` (não no `config.yaml` — achado por tentativa: a chave certa é env var, não config). Mensagem ida e volta confirmada. Não tocou no bot do Javis. |
| **Maturidade/pronto** | ✅ boa | Instala limpo (script oficial, ~1min de download, zero erro). 24 tools ativas (`browser_*`, `terminal`, `memory`, `skill_manage`, `delegate_task`, `text_to_speech`...). CLI responsiva. Setup wizard não funciona sem TTY (esperado, contornado via `config set`). |

## Atritos encontrados (não bloqueantes, mas reais)

1. **Flag de prompt não é `-p`, é `-z`** com `--cli` — doc/UX confuso na primeira tentativa.
2. **Catálogo free do OpenRouter muda rápido** — qualquer integração que hardcode um modelo `:free` específico vai quebrar sem aviso. Precisa de fallback automático entre 2-3 candidatos, não um único modelo fixo.
3. **Config do Telegram não é onde parece** — `gateway.telegram.token` no `config.yaml` é aceito mas **ignorado**; o gateway só lê `TELEGRAM_BOT_TOKEN` do `.env`. Achado por leitura do código-fonte (`gateway/config.py:1174`), não pela doc.
4. **"Auxiliary Nous client"** dispara avisos repetidos de erro de pagamento/crédito mesmo sem usar o Portal pago — é um recurso auxiliar (provavelmente sumarização/insights) que tenta autenticar e falha silenciosamente em loop. Não impediu a resposta principal, mas poluiu o log.

## Teste extra: skill-learning automático (validado, com ressalva)

1ª tentativa (multi-step com browser: navegar no OpenRouter, montar tabela,
salvar como skill) **falhou por fricção de ambiente** — `browser_navigate`
deu erro de spawn do Node 3x e o fallback pro `terminal` tentou WSL e também
falhou (`execvpe(/bin/bash) failed`). Não é defeito do Hermes, é a camada de
shell aninhada em que rodei o teste.

2ª tentativa (pedido direto, sem depender de browser/terminal: "crie uma skill
chamada resumo-diario que pergunta 3 coisas") **funcionou de fato**: ele
chamou a ferramenta `skill_manage` e gravou
`~/.hermes/skills/resumo-diario/SKILL.md` no disco — confirmado lendo o
arquivo. **Ressalva real:** o que foi salvo é a *descrição* da skill (nome,
frase-gatilho, as 3 perguntas), mas o corpo do arquivo é um **stub** —
literalmente `# Implement the logic here` e `# Skill body placeholder`. Ou
seja, ele registra a intenção da skill corretamente, mas não gera lógica
executável sozinho; a "lógica" ainda depende do host/app interpretar a
descrição. Skill-learning automático real (criar + persistir) **passa**;
skill com lógica própria pronta pra rodar **não chega lá** nesse teste.

## Análise do trace interno (81 mensagens da sessão de teste)

Lendo o `state.db` linha a linha (não só a resposta final), aparecem 3 achados
que a resposta apresentada ao usuário não deixa ver:

1. **Bug real de validação:** a 1ª tentativa de `skill_manage(action='create')`
   quebrou porque o próprio modelo gerou uma descrição com bullets (`•`) dentro
   do YAML frontmatter, e o parser não escapou — `YAML frontmatter parse error`.
   Levou 2 tentativas e um placeholder de corpo pra passar a validação
   (`"SKILL.md must have content after the frontmatter"`).
2. **Gap de honestidade entre raciocínio e resposta:** o scratchpad interno
   (que vazou pro log, msg 148) mostra o modelo admitindo dúvida real —
   *"Skills not auto-triggered by phrase unless using built-in rule... maybe
   can't trigger automatically"* — e decidindo criar um placeholder mesmo
   assim. A resposta final ao usuário (`"Skill was created successfully"`) **não
   menciona essa dúvida**. Apresentou certeza onde só havia uma aposta.
3. **Loop pós-tarefa ignorando guardrail:** depois de já ter entregue a
   resposta, o agente continuou por **~40 chamadas de ferramenta** tentando
   "verificar" o próprio trabalho — `search_files` falhou 4x (sem ripgrep
   instalado), `terminal`/`write_file` falharam 6x+ (sem WSL/bash instalado). O
   guardrail anti-loop do próprio Hermes avisou **5 vezes explicitamente**
   ("this looks like a loop, change strategy") e o modelo (free tier
   `gpt-oss-20b`) ignorou e repetiu quase a mesma chamada. Também rebuscou a
   lista de skills (8.9KB) e o conteúdo do skill `hermes-agent` (52KB) **3x**
   na mesma sessão — desperdício de tokens que em modelo pago seria custo real.

**Implicação prática:** o guardrail anti-loop do Hermes *detecta* mas não
*impede* — é aviso, não trava dura. E duas dependências externas (ripgrep,
WSL/bash) são assumidas pelas tools nativas mas não verificadas/instaladas
pelo instalador Windows — isso deixa parte do toolkit morto até instalar à
mão.

## A leitura final

Os 4 pilares **passaram de fato**, não só no papel. Hermes é um chassi de agente
genuinamente pronto: instala fácil, multi-modelo funciona, memória persiste,
gateway funciona. Isso confirma a leitura da análise anterior.

Mas nenhum atrito encontrado muda a conclusão de arquitetura: **Hermes = chassi
genérico; Javis = chassi próprio + persona (Jamba) + pipeline de campanha (3
gates) + integração Cérebro Jampa**. Não existe equivalente do "Jamba" nem do
pipeline VP no Hermes — não tem como ter, é genérico por design.

## Veredito: **MINERAR, não adotar como substrato**

Não migrar o Javis para rodar "em cima" do Hermes (nível 3 da análise anterior).
O custo de abandonar 126 testes + pipeline de 3 gates + persona pra ganhar um
chassi genérico não compensa — o Javis já tem chassi próprio funcionando.

**O que vale trazer pro Javis (nível 1 — minerar, risco 0, MIT permite copiar):**
- **Padrão de fallback entre múltiplos modelos free** (não fixar 1 só — o atrito
  #2 provou que isso quebra). Aplicar isso na futura rota Gemini/OpenRouter da
  cascata do `agent.py`.
- **Skill-learning automático** (`skill_manage`, criar skill após tarefa
  complexa) — ideia interessante pro RAG/`knowledge.py` do Javis, mas **não**
  prioridade agora (frente ativa é a rota Gemini).
- Nada do gateway — Javis já tem Telegram funcionando e não precisa de 20
  plataformas.

**Não vale trazer agora:** sandbox de terminal isolado (Javis não tem essa
necessidade hoje), cron em linguagem natural (Javis já tem rotina matinal),
Honcho/user-modeling (RAG do Javis já cobre isso pro caso de uso atual).

## Próximo passo

Nenhuma ação de código imediata. Hermes fica instalado em `~/.hermes` (não
ocupa espaço relevante no projeto, ~1GB fora do repo) caso queira voltar a
testar. Item "Hermes" sai do parqueado como **decidido** — ver
`_estado/proximos-passos.md`.
