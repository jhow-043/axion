#Requires -Version 5.1
<#
.SYNOPSIS
    Sobe toda a stack de desenvolvimento: infra (Docker), backend (FastAPI + Celery) e frontend (Vite).
.PARAMETER Seed
    Se presente, roda o script de seed após as migrations.
.PARAMETER SkipDocker
    Se presente, assume que o Docker já está rodando e pula o docker compose up.
#>
param(
    [switch]$Seed,
    [switch]$SkipDocker
)

$Root        = $PSScriptRoot
$BackendDir  = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$PidFile     = Join-Path $Root ".dev-pids.json"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "    ERRO $msg" -ForegroundColor Red; exit 1 }

# ── 1. Docker Compose ─────────────────────────────────────────────────────────

if (-not $SkipDocker) {
    Write-Step "Subindo servicos Docker (postgres, redis, minio, mailhog)..."
    docker compose -f (Join-Path $Root "docker-compose.yml") up -d
    if ($LASTEXITCODE -ne 0) { Write-Fail "docker compose up falhou." }
    Write-Ok "Conteineres rodando."
}

# ── 2. Aguarda Postgres ───────────────────────────────────────────────────────

Write-Step "Aguardando PostgreSQL ficar pronto..."
$tries = 0
while ($tries -lt 30) {
    $result = docker compose exec -T postgres pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Ok "PostgreSQL pronto."; break }
    $tries++
    Start-Sleep -Seconds 2
}
if ($tries -ge 30) { Write-Fail "PostgreSQL nao respondeu apos 60s." }

# ── 3. Migrations ─────────────────────────────────────────────────────────────

Write-Step "Rodando migrations Alembic..."
Push-Location $BackendDir
uv run alembic upgrade head
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Fail "alembic upgrade head falhou." }
Pop-Location
Write-Ok "Migrations aplicadas."

# ── 4. Seed (opcional) ────────────────────────────────────────────────────────

if ($Seed) {
    Write-Step "Rodando seed de desenvolvimento..."
    Push-Location $BackendDir
    uv run python scripts/seed_dev.py
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Fail "seed_dev.py falhou." }
    Pop-Location
    Write-Ok "Seed concluido."
}

# ── 5. Uvicorn ────────────────────────────────────────────────────────────────

Write-Step "Iniciando backend (uvicorn)..."
$uvProc = Start-Process powershell `
    -ArgumentList "-NoExit", "-Command", "cd '$BackendDir'; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" `
    -PassThru
Write-Ok ("Uvicorn iniciado (PID {0}) - porta 8000" -f $uvProc.Id)

Start-Sleep -Seconds 3

# ── 6. Celery worker ──────────────────────────────────────────────────────────

Write-Step "Iniciando Celery worker..."
$celProc = Start-Process powershell `
    -ArgumentList "-NoExit", "-Command", "cd '$BackendDir'; uv run celery -A app.core.celery_app worker --loglevel=info --concurrency=2" `
    -PassThru
Write-Ok ("Celery iniciado (PID {0})" -f $celProc.Id)

# ── 7. Vite dev server ────────────────────────────────────────────────────────

Write-Step "Iniciando frontend (Vite)..."
$viteProc = Start-Process powershell `
    -ArgumentList "-NoExit", "-Command", "cd '$FrontendDir'; npm run dev" `
    -PassThru
Write-Ok ("Vite iniciado (PID {0}) - porta 5173" -f $viteProc.Id)

# ── Salva PIDs ────────────────────────────────────────────────────────────────

@{ uvicorn = $uvProc.Id; celery = $celProc.Id; vite = $viteProc.Id } `
    | ConvertTo-Json | Set-Content -Path $PidFile -Encoding utf8

# ── Resumo ────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host "  Stack de desenvolvimento rodando" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host "  Backend API  : http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs     : http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Frontend     : http://localhost:5173" -ForegroundColor Yellow
Write-Host "  MinIO Console: http://localhost:9001  (minioadmin/minioadmin)" -ForegroundColor Yellow
Write-Host "  MailHog      : http://localhost:8025" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host "  Para parar tudo: .\stop.ps1" -ForegroundColor DarkGray
Write-Host ""
