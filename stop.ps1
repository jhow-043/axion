#Requires -Version 5.1
<#
.SYNOPSIS
    Para toda a stack de desenvolvimento iniciada por start.ps1.
.PARAMETER KeepDocker
    Se presente, mantém os contêineres Docker rodando (apenas encerra uvicorn/celery/vite).
#>
param(
    [switch]$KeepDocker
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$Root    = $PSScriptRoot
$PidFile = Join-Path $Root ".dev-pids.json"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }

function Stop-ByPid($Name, $Id) {
    if (-not $Id) { return }
    $proc = Get-Process -Id $Id -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $Id -Force -ErrorAction SilentlyContinue
        Write-Ok "$Name (PID $Id) encerrado."
    } else {
        Write-Ok "$Name (PID $Id) já não estava rodando."
    }
}

# ── Encerra processos salvos pelo start.ps1 ───────────────────────────────────

Write-Step "Encerrando processos de desenvolvimento..."

if (Test-Path $PidFile) {
    $pids = Get-Content $PidFile -Raw | ConvertFrom-Json
    Stop-ByPid "Uvicorn" $pids.uvicorn
    Stop-ByPid "Celery"  $pids.celery
    Stop-ByPid "Vite"    $pids.vite
    Remove-Item $PidFile -Force
} else {
    Write-Host "    Arquivo .dev-pids.json não encontrado — tentando matar por nome..." -ForegroundColor Yellow
}

# ── Fallback: mata por nome de processo ──────────────────────────────────────
# Útil quando start.ps1 foi interrompido antes de salvar o PidFile.

$killed = $false

Get-Process -Name "uvicorn"   -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force; $killed = $true
    Write-Ok "uvicorn (PID $($_.Id)) encerrado pelo nome."
}

Get-Process -Name "celery"    -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force; $killed = $true
    Write-Ok "celery (PID $($_.Id)) encerrado pelo nome."
}

# Vite roda via Node; filtra pelo argumento "vite"
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    ($_.CommandLine -match "vite" -or $_.MainWindowTitle -match "vite")
} | ForEach-Object {
    Stop-Process -Id $_.Id -Force; $killed = $true
    Write-Ok "Vite/node (PID $($_.Id)) encerrado."
}

# pnpm spawna um processo filho node; tenta também pelo título da janela
Get-Process -Name "pnpm" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force; $killed = $true
    Write-Ok "pnpm (PID $($_.Id)) encerrado."
}

# ── Docker Compose ────────────────────────────────────────────────────────────

if (-not $KeepDocker) {
    Write-Step "Parando contêineres Docker..."
    Set-Location $Root
    docker compose stop
    Write-Ok "Contêineres parados (volumes preservados). Use 'docker compose down -v' para apagar volumes."
} else {
    Write-Host "`n    Docker mantido rodando (-KeepDocker)." -ForegroundColor DarkGray
}

# ── Resumo ────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "  Stack encerrada." -ForegroundColor White
Write-Host "  Para subir novamente: .\start.ps1" -ForegroundColor DarkGray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
