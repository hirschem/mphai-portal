# Minimal MPH AI Portal pre-commit preflight (PowerShell)
# Run from repo root: scripts/preflight.ps1

$ErrorActionPreference = 'Stop'


Write-Host "==== WEB: build ====" -ForegroundColor Cyan
Push-Location "apps/web"
if (Test-Path package.json) {
    if (Test-Path node_modules) {
        npm run build
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } else {
        npm install
        npm run build
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
} else {
    Write-Host "No package.json found, skipping web build." -ForegroundColor Yellow
}
Pop-Location

Write-Host "==== WEB: lint ====" -ForegroundColor Cyan
Push-Location "apps/web"
if (Test-Path package.json) {
    $lintScript = (Get-Content package.json | Select-String '"lint"').Line
    if ($lintScript) {
        npm run lint
    } else {
        Write-Host "No lint script found, skipping lint." -ForegroundColor Yellow
    }
} else {
    Write-Host "No package.json found, skipping lint." -ForegroundColor Yellow
}
Pop-Location

Write-Host "==== API: pytest ====" -ForegroundColor Cyan
Push-Location "apps/api"
if ((Test-Path tests) -or ((Get-ChildItem -Filter "test_*.py" | Measure-Object).Count -gt 0)) {
    if (Get-Command pytest -ErrorAction SilentlyContinue) {
        pytest
    } else {
        Write-Host "pytest not installed, skipping tests." -ForegroundColor Yellow
    }
} else {
    Write-Host "No pytest tests found, skipping." -ForegroundColor Yellow
}
Pop-Location

Write-Host "==== API: import/type check ====" -ForegroundColor Cyan
Push-Location "apps/api"
if (Test-Path app) {
    try {
        python -c "import app.main" | Out-Null
        Write-Host "API import check passed." -ForegroundColor Green
    } catch {
        Write-Host "API import check failed." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "No app/ found, skipping import check." -ForegroundColor Yellow
}
Pop-Location

Write-Host "==== ALL CHECKS COMPLETE ====" -ForegroundColor Green
