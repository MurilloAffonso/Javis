"""
codex_orchestrator.py — Codex como orquestrador autonomo do Javis
Uso: python codex_orchestrator.py
Le backlog de _data/codex_backlog.md, executa proxima tarefa pendente via Codex CLI.
"""
import subprocess, sys, os, re
from pathlib import Path
from datetime import datetime

REPO       = Path(r"C:\Users\noteacer\Desktop\javis")
BACKLOG    = REPO / "_apps/javis-local-interface/_data/codex_backlog.md"
TASK_FILE  = REPO / "_apps/javis-local-interface/_data/codex_orch_task.txt"
LOG_FILE   = REPO / "_apps/javis-local-interface/_data/codex_orch_log.txt"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"{ts}  {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def find_pending(lines):
    for i, line in enumerate(lines):
        if re.match(r"\s*-\s*\[ \]", line):
            task = re.sub(r"^\s*-\s*\[ \]\s*", "", line).strip()
            return i, task
    return -1, ""

def build_prompt(task: str) -> str:
    return f"""Voce e o agente Codex operando como orquestrador do projeto Javis.

IMPORTANTE — FERRAMENTAS: NAO use nenhuma ferramenta MCP (lean-ctx, ctx_*).
Use apenas leitura/escrita de arquivo nativa. Raiz do repo: {REPO}

CONTEXTO DO PROJETO:
- Interface: _apps/javis-local-interface/frontend/ (index.html, app.js, style.css)
- Backend: _apps/javis-local-interface/backend/server.py
- Projetos: _projetos/cerebro-jampa/ (Vem Passear Jampa — turismo Joao Pessoa/PB)
- Linha editorial: _projetos/cerebro-jampa/linha-editorial.md
- Plano SEO: _projetos/cerebro-jampa/seo-plano.md
- Regras de agentes: AGENTS.md

REGRAS RIGIDAS:
- NAO faca git push
- NAO delete arquivos existentes
- NAO modifique .env
- Trabalhe SOMENTE dentro de {REPO}
- Edicoes ciurgicas, nao reescritas completas
- Ao terminar, escreva exatamente: CONCLUIDO: [resumo em 1 linha]

TAREFA:
{task}
"""

def main():
    log("=== Codex Orquestrador iniciado ===")
    os.chdir(REPO)

    if not BACKLOG.exists():
        log(f"ERRO: backlog nao encontrado em {BACKLOG}")
        sys.exit(1)

    lines = BACKLOG.read_text(encoding="utf-8").splitlines()
    idx, task = find_pending(lines)

    if idx == -1:
        log("Backlog vazio — nenhuma tarefa pendente.")
        sys.exit(0)

    log(f"Tarefa #{idx+1}: {task[:80]}...")

    prompt = build_prompt(task)
    TASK_FILE.write_text(prompt, encoding="utf-8")

    log("Executando Codex CLI...")
    result = subprocess.run(
        ["powershell", "-Command",
         f'Get-Content "{TASK_FILE}" -Raw | codex exec --sandbox workspace-write'],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO), timeout=480
    )

    output = result.stdout + result.stderr
    log(f"Exit code: {result.returncode}")

    # Salvar saída no log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n--- OUTPUT CODEX ---\n")
        f.write(output[-3000:] if len(output) > 3000 else output)
        f.write("\n--- FIM ---\n")

    # Verificar conclusao
    concluido = bool(re.search(r"CONCLU[IÍ]DO|conclu[ií]do|✅|DONE", output, re.IGNORECASE))

    if concluido or result.returncode == 0:
        lines[idx] = lines[idx].replace("[ ]", "[x]", 1)
        BACKLOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log("Tarefa marcada como [x] no backlog.")

        subprocess.run(["git", "add", "-A"], cwd=str(REPO))
        label = task[:60].replace('"', "'")
        subprocess.run(
            ["git", "commit", "-m", f"codex-orch: {label}"],
            cwd=str(REPO)
        )
        log("Commit feito.")
    else:
        log("AVISO: Codex nao confirmou conclusao — revisar manualmente.")

    log("=== Sessao encerrada ===")

if __name__ == "__main__":
    main()
