# ============================================================
# Truthline Launcher
# ------------------------------------------------------------
# 1. Stop previous server (if running)
# 2. Clear Python cache
# 3. Activate virtual environment
# 4. Run server
#
# Usage:
#   .\activate.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot
$ServerPort = 8080

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Truthline - Crisis at Caspian Station" -ForegroundColor Cyan
Write-Host "  Auto-launch (clean + activate + run)" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Step 1: Stop previous server
# ============================================================
Write-Host "[1/4] Checking for running server..." -ForegroundColor Yellow

$killedProcess = $false
try {
    $connection = Get-NetTCPConnection `
        -LocalPort $ServerPort `
        -State Listen `
        -ErrorAction SilentlyContinue

    if ($connection) {
        $existingPid = ($connection | Select-Object -First 1).OwningProcess

        if ($existingPid -and $existingPid -gt 0) {
            Write-Host "  Stopping previous server (PID: $existingPid)..." -ForegroundColor Gray
            Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1

            $stillRunning = Get-NetTCPConnection `
                -LocalPort $ServerPort `
                -State Listen `
                -ErrorAction SilentlyContinue

            if ($stillRunning) {
                Write-Host "  WARNING: Previous server still running." -ForegroundColor Yellow
                Write-Host "  Please close the old terminal manually." -ForegroundColor Yellow
            } else {
                Write-Host "  OK - Previous server stopped" -ForegroundColor Green
                $killedProcess = $true
            }
        }
    }

    if (-not $killedProcess) {
        Write-Host "  OK - No server was running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  WARNING: Error checking server: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ============================================================
# Step 2: Clear Python cache
# ============================================================
Write-Host "[2/4] Clearing Python cache..." -ForegroundColor Yellow

$cacheCount = 0
Get-ChildItem `
    -Path $ProjectRoot `
    -Recurse `
    -Directory `
    -Filter "__pycache__" `
    -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\\.venv\\" } |
    ForEach-Object {
        try {
            Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            $cacheCount++
        } catch {}
    }

Get-ChildItem `
    -Path $ProjectRoot `
    -Recurse `
    -File `
    -Include "*.pyc","*.pyo" `
    -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\\.venv\\" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

$cacheDirs = @(
    (Join-Path $ProjectRoot ".pytest_cache"),
    (Join-Path $ProjectRoot ".mypy_cache"),
    (Join-Path $ProjectRoot ".ruff_cache"),
    (Join-Path $ProjectRoot ".pyright")
)
foreach ($dir in $cacheDirs) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "  OK - $cacheCount __pycache__ folders removed" -ForegroundColor Green
Write-Host "  OK - .pyc files and tool caches cleared" -ForegroundColor Green

# ============================================================
# Step 3: Activate virtual environment
# ============================================================
Write-Host "[3/4] Activating virtual environment..." -ForegroundColor Yellow

$venvPath = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "  OK - Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  ERROR - Virtual environment not found: $venvPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "  To create it:" -ForegroundColor Yellow
    Write-Host "    python -m venv .venv" -ForegroundColor Yellow
    Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "    pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# ============================================================
# Step 4: Run server
# ============================================================
Write-Host "[4/4] Starting server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Stop:  Ctrl+C" -ForegroundColor Gray
Write-Host "  App:   http://localhost:$ServerPort" -ForegroundColor Gray
Write-Host "  Admin: http://localhost:$ServerPort/admin" -ForegroundColor Gray
Write-Host ""
Write-Host "-------------------------------------------" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectRoot

try {
    python -m web_app.app
} catch {
    Write-Host ""
    Write-Host "ERROR running server: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================
# End message (after Ctrl+C)
# ============================================================
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Server stopped" -ForegroundColor Green
Write-Host "  To run again:  .\activate.ps1" -ForegroundColor Gray
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

#.\activate.ps1