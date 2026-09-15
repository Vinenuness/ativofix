# ============================================================
# AtivoFix - Instalador do Agente (Windows)
# Uso: powershell -ExecutionPolicy Bypass -File instalar-agente.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# >>> CONFIGURACAO DE PRODUCAO <<<
$SERVER_URL = "http://147.93.181.158"   # troque para https://ativofix.com.br quando o DNS ativar
$AGENT_TOKEN = "451f686c709a28cccf5584d81f21126d50e8d79f2253840e"
# ==================================

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " AtivoFix - Instalacao do Agente" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1) Localizar o agente (mesma pasta deste script)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentPath = Join-Path $scriptDir "agente.py"
if (-not (Test-Path $agentPath)) {
    # fallback: pasta templates\
    $agentPath = Join-Path $scriptDir "templates\agente.py"
}
if (-not (Test-Path $agentPath)) {
    Write-Host "ERRO: agente.py nao encontrado junto ao instalador." -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit 1
}
Write-Host "[1/5] Agente encontrado: $agentPath"

# 2) Verificar Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERRO: Python nao encontrado no PATH." -ForegroundColor Red
    Write-Host "Instale de https://www.python.org/downloads/ (marque 'Add to PATH')" -ForegroundColor Yellow
    Read-Host "Pressione ENTER para sair"
    exit 1
}
Write-Host "[2/5] Python OK: $($python.Source)"

# 3) Dependencias
Write-Host "[3/5] Instalando dependencias (requests, psutil, wmi, pywin32)..."
python -m pip install --quiet --disable-pip-version-check requests psutil wmi pywin32
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: falha ao instalar dependencias." -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit 1
}
Write-Host "      Dependencias OK."

# 4) Variaveis de ambiente persistentes (usuario)
[Environment]::SetEnvironmentVariable("AGENT_SERVER_URL", $SERVER_URL, "User")
[Environment]::SetEnvironmentVariable("AGENT_TOKEN", $AGENT_TOKEN, "User")
Write-Host "[4/5] Configuracao gravada: $SERVER_URL"

# 5) Auto-start no Windows (HKCU Run, sem janela)
$pythonDir = Split-Path -Parent (Get-Command python).Source
$pythonw = Join-Path $pythonDir "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = (Get-Command python).Source }
$runValue = '"' + $pythonw + '" "' + $agentPath + '"'
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "AtivoFixAgent" -Value $runValue
Write-Host "[5/5] Auto-start registrado (inicia no login, sem janela)."

# Resumo
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host " Instalacao concluida!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host " Servidor : $SERVER_URL"
Write-Host " Token    : $($AGENT_TOKEN.Substring(0,8))..."
Write-Host ""
Write-Host " O agente inicia automaticamente no proximo login."
Write-Host " Na primeira janela ele pode pedir a TAG do PC."
Write-Host ""

$resp = Read-Host " Iniciar o agente agora? (S/n)"
if ($resp -ne "n") {
    $env:AGENT_SERVER_URL = $SERVER_URL
    $env:AGENT_TOKEN = $AGENT_TOKEN
    Start-Process -FilePath $pythonw -ArgumentList ('"' + $agentPath + '"') -WorkingDirectory $scriptDir
    Write-Host " Agente iniciado em background." -ForegroundColor Green
}
Read-Host " Pressione ENTER para fechar"
