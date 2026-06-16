# codex_orchestrator.ps1 — Codex como orquestrador autônomo do Javis
# Uso: .\codex_orchestrator.ps1
# Lê backlog de _data/codex_backlog.md, executa tarefa a tarefa, commita.

$REPO = "C:\Users\noteacer\Desktop\javis"
$BACKLOG = "$REPO\_apps\javis-local-interface\_data\codex_backlog.md"
$LOG = "$REPO\_apps\javis-local-interface\_data\codex_orch_log.txt"

Set-Location $REPO

function Write-Log($msg) {
    $ts = Get-Date -Format "HH:mm:ss"
    "$ts  $msg" | Tee-Object -Append -FilePath $LOG
}

Write-Log "=== Codex Orquestrador iniciado ==="

# Verifica se backlog existe
if (-not (Test-Path $BACKLOG)) {
    Write-Log "ERRO: backlog não encontrado em $BACKLOG"
    exit 1
}

$tasks = Get-Content $BACKLOG
$pendingIndex = -1
$pendingTask = ""

# Encontra primeira tarefa pendente (linha com "[ ]")
for ($i = 0; $i -lt $tasks.Count; $i++) {
    if ($tasks[$i] -match "^\s*-\s*\[ \]") {
        $pendingIndex = $i
        $pendingTask = $tasks[$i] -replace "^\s*-\s*\[ \]\s*", ""
        break
    }
}

if ($pendingIndex -eq -1) {
    Write-Log "Backlog vazio — nenhuma tarefa pendente."
    exit 0
}

Write-Log "Tarefa: $pendingTask"

# Monta prompt para Codex
$promptFile = "$REPO\_apps\javis-local-interface\_data\codex_orch_task.txt"
$systemContext = @"
Você é o agente Codex operando como orquestrador do projeto Javis.

IMPORTANTE — FERRAMENTAS: NÃO use nenhuma ferramenta MCP (lean-ctx, ctx_*).
Use apenas leitura/escrita de arquivo nativa. Raiz do repo: $REPO

CONTEXTO DO PROJETO: Javis é um AIOS (AI Operating System) pessoal do Murillo.
- Interface: _apps/javis-local-interface/frontend/ (index.html, app.js, style.css)
- Backend: _apps/javis-local-interface/backend/server.py
- Projetos ativos: _projetos/cerebro-jampa/ (Vem Passear Jampa — turismo em João Pessoa)
- Linha editorial: _projetos/cerebro-jampa/linha-editorial.md
- Plano SEO: _projetos/cerebro-jampa/seo-plano.md
- Agentes: AGENTS.md

REGRAS RÍGIDAS:
- NÃO faça git push
- NÃO delete arquivos existentes
- NÃO modifique .env
- Trabalhe SOMENTE dentro de $REPO
- Edições cirúrgicas, não reescritas completas

TAREFA A EXECUTAR:
$pendingTask

Execute a tarefa completamente. Ao terminar, escreva "CONCLUÍDO: [resumo em 1 linha]" no final.
"@

$systemContext | Out-File -Encoding utf8 $promptFile

Write-Log "Executando Codex..."
$output = Get-Content $promptFile -Raw | codex exec --sandbox workspace-write 2>&1
$output | Out-File -Encoding utf8 -Append $LOG

# Marca tarefa como concluída no backlog
if ($output -match "CONCLUÍDO|CONCLUIDO|done|✅") {
    $tasks[$pendingIndex] = $tasks[$pendingIndex] -replace "\[ \]", "[x]"
    $tasks | Out-File -Encoding utf8 $BACKLOG
    Write-Log "Tarefa marcada como [x] no backlog."

    # Commit automático
    git add -A
    $msg = "codex-orch: $($pendingTask.Substring(0, [Math]::Min(60, $pendingTask.Length)))"
    git commit -m $msg
    Write-Log "Commit feito: $msg"
} else {
    Write-Log "AVISO: Codex não confirmou conclusão — revisar manualmente."
}

Write-Log "=== Sessão encerrada ==="
