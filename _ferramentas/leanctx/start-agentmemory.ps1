# start-agentmemory.ps1
# Inicia o servidor agentmemory em background
# Rodar uma vez antes de usar o Claude Code

$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"

# Verificar se já está rodando
$test = Test-NetConnection -ComputerName localhost -Port 3111 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($test) {
    Write-Host "agentmemory já está rodando em http://localhost:3111"
    exit 0
}

Write-Host "Iniciando agentmemory..."
Start-Process -FilePath "npx" -ArgumentList "@agentmemory/agentmemory" -WindowStyle Minimized
Start-Sleep -Seconds 5

$test2 = Test-NetConnection -ComputerName localhost -Port 3111 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($test2) {
    Write-Host "agentmemory iniciado em http://localhost:3111"
    Write-Host "Dashboard: http://localhost:3113"
} else {
    Write-Host "ERRO: agentmemory nao iniciou. Verifique se iii.exe está no PATH."
}
