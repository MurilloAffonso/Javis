# 2026-06-15 — Assinatura do Claude como motor de execução

## O que foi decidido
Conectar a **assinatura do Claude** (Claude Code headless) como o **motor de
execução** do Javis — espelhando o projeto de referência (@gaabflemander7,
codandoai.com/jarvis): *Claude (assinatura) = execução; OpenAI = voz/conversa*.

- **Escopo:** Claude vira o executor principal de tarefas (código + tarefas
  agênticas gerais); Codex (`code_agent.py`) vira fallback.
- **Segurança:** allowlist segura — pode ler/editar/criar arquivos e rodar testes;
  hook `PreToolUse` bloqueia git push/reset/clean, `rm -rf`, `del /f`, `sudo`,
  `format`; escopo só na pasta do Javis; sem commit automático.

## Por quê
- A `ANTHROPIC_API_KEY` está sem crédito → usar a API por token não serve.
- O Murillo JÁ tem assinatura do Claude (Claude Code logado por OAuth,
  `vempassearjampa@gmail.com`). A assinatura é flat → execução "ilimitada" sem
  gastar token. A OpenAI fica só com voz/conversa (centavos).

## Como (implementação)
- **`backend/claude_exec.py`** (novo): `run`/`dispatch` chamam
  `claude -p <tarefa> --output-format text --permission-mode acceptEdits
  --allowedTools Read Edit Write Bash --add-dir <JAVIS_ROOT> --append-system-prompt …`,
  `cwd=JAVIS_ROOT`. **CRÍTICO:** `_env()` remove `ANTHROPIC_API_KEY` do ambiente do
  subprocesso → força login pela ASSINATURA (senão o Claude Code tentaria a API sem
  crédito). `dispatch` roda em background e avisa por reminders/Telegram.
- **`backend/agent.py`**: a ferramenta `programar` agora usa `claude_exec.dispatch`
  quando o Claude está disponível, com `code_agent.dispatch` (Codex) de fallback.
  Descrição ampliada para execução geral (não só código).
- **`.claude/settings.json`** (novo) + **`.claude/hooks/guard_dangerous.py`** (novo):
  hook `PreToolUse` para Bash que bloqueia comandos destrutivos. **Fail-open**: em
  qualquer erro, libera (nunca trava trabalho legítimo). Vale para o subprocesso
  headless E para as sessões interativas do Claude Code na pasta.
- **`.env.example`**: documenta o modelo de custo (voz=OpenAI, execução=assinatura
  Claude) + `JAVIS_CLAUDE_EXEC_TIMEOUT`.

## Verificação
- `claude -p` headless com `ANTHROPIC_API_KEY` removida → responde pela assinatura
  (exit 0), apesar da API sem crédito.
- `claude_exec.run('crie _smoke_claude.txt …')` → criou o arquivo de fato (prova o
  fluxo: subprocesso → assinatura → allowedTools Write → acceptEdits).
- `_test_guard.py` → 10/10: bloqueia git push/rm -rf/reset --hard/clean/sudo;
  libera pytest/git status/npm test; fail-open em payload inválido.
- `python -m pytest -q` → **54 passando**. Imports OK.

## Alternativas consideradas
- API Anthropic por token: descartada (sem crédito; custo por uso).
- `--dangerously-skip-permissions`: descartado (Murillo escolheu allowlist segura).
- Manter Codex como principal: descartado (objetivo é usar a assinatura do Claude).

## Artefatos de teste deixados (padrão `_test_`/`_smoke_` do backend)
- `backend/_test_guard.py` (regressão útil do guard).
- `backend/_smoke_claude.txt` (prova do fluxo; pode apagar quando quiser).

## Próximo passo
- Testar pela voz/interface: "Jamba, programe/execute X" deve disparar o Claude e
  avisar ao terminar (Telegram/orbe).
- Nada commitado — aguardando aprovação do Murillo.
