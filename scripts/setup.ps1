$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> Projeto: $root" -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "==> Criando venv (.venv) com Python 3.12..." -ForegroundColor Cyan
    py -3.12 -m venv .venv
} else {
    Write-Host "==> venv já existe, reutilizando." -ForegroundColor DarkGray
}

$py = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "==> Atualizando pip e instalando dependências..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt

Write-Host "==> Gerando requirements.lock.txt..." -ForegroundColor Cyan
& $py -m pip freeze | Out-File -Encoding utf8 requirements.lock.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> .env criado a partir de .env.example" -ForegroundColor Green
}

Write-Host "==> Baixando modelos do Ollama (pode demorar)..." -ForegroundColor Cyan
ollama pull qwen2.5:7b-instruct
ollama pull bge-m3

Write-Host ""
Write-Host "==> Setup concluído." -ForegroundColor Green
Write-Host "    Ative o venv:  .\.venv\Scripts\Activate.ps1"
Write-Host "    Smoke test:    python -m scripts.smoke_test"
