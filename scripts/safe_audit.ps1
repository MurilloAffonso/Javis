Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== Javis Safe Audit =="
Write-Host "Root: $Root"
Write-Host ""

Write-Host "== Git =="
Write-Host "Branch:"
git branch --show-current
Write-Host ""
Write-Host "Status:"
git status -sb
Write-Host ""

Write-Host "== Tracked sensitive-looking file names =="
$patterns = @("token", "credential", "credentials", "secret", "key", "env", "pem", "p12")
$tracked = git ls-files
$tracked |
  Where-Object {
    $name = $_.ToLowerInvariant()
    foreach ($pattern in $patterns) {
      if ($name.Contains($pattern)) { return $true }
    }
    return $false
  } |
  ForEach-Object { Write-Host $_ }
Write-Host ""

Write-Host "== Tracked .env =="
git ls-files .env
Write-Host ""

Write-Host "== Untracked files =="
git ls-files --others --exclude-standard
Write-Host ""

Write-Host "== Ignored runtime/cache snapshot =="
git status --ignored -sb
Write-Host ""

Write-Host "== Expected safe flags =="
$flags = @(
  "JAVIS_ENABLE_EXTERNAL_ADAPTERS",
  "JAVIS_ENABLE_CODEX_EXEC",
  "JAVIS_ENABLE_CLAUDE_EXEC",
  "JAVIS_ENABLE_BROWSER",
  "JAVIS_ENABLE_TELEGRAM",
  "JAVIS_ENABLE_MCP",
  "JAVIS_ENABLE_LOCAL_ACTIONS",
  "JAVIS_ENABLE_VP_EFFECTS",
  "JAVIS_DEV_ALLOW_CORS"
)
foreach ($flag in $flags) {
  $value = [Environment]::GetEnvironmentVariable($flag, "Process")
  if ([string]::IsNullOrWhiteSpace($value)) { $value = "<unset>" }
  Write-Host "$flag=$value"
}

Write-Host ""
Write-Host "No server, agent, external adapter, commit, or push was executed by this script."
