# ============================================================
# Script para Rodar a Aplicação STT
# ============================================================
# Este script configura e inicia o microsserviço STT
# Uso: .\rodar.ps1
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Iniciando Microsserviço STT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Passo 1: Criar ambiente virtual
# ============================================================
Write-Host "[1] Verificando ambiente virtual..." -ForegroundColor Yellow

if (Test-Path "venv_stt\Scripts\activate.ps1") {
    Write-Host "  ✓ Ambiente virtual já existe" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv_stt
    
    if (Test-Path "venv_stt\Scripts\activate.ps1") {
        Write-Host "  ✓ Ambiente virtual criado" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Falha ao criar ambiente virtual" -ForegroundColor Red
        exit 1
    }
}

# ============================================================
# Passo 2: Ativar ambiente virtual
# ============================================================
Write-Host "[2] Ativando ambiente virtual..." -ForegroundColor Yellow
& "venv_stt\Scripts\activate.ps1"
Write-Host "  ✓ Ambiente ativado" -ForegroundColor Green
Write-Host ""

# ============================================================
# Passo 3: Instalar dependências
# ============================================================
Write-Host "[3] Verificando dependências..." -ForegroundColor Yellow

$vosk_installed = pip show vosk 2>&1 | Select-String "Name: vosk"

if ($vosk_installed) {
    Write-Host "  ✓ Dependências já instaladas" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Instalando dependências..." -ForegroundColor Yellow
    pip install -q -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Dependências instaladas com sucesso" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Falha ao instalar dependências" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# ============================================================
# Passo 4: Verificar/Criar diretório de modelos
# ============================================================
Write-Host "[4] Verificando modelo Vosk..." -ForegroundColor Yellow

$modelPath = "d:\ela_teste\ela_mvp\models\vosk-model-small-pt-0.3"
$parentPath = "d:\ela_teste\ela_mvp\models"

if (-not (Test-Path $parentPath)) {
    Write-Host "  ⚠ Criando diretório models..." -ForegroundColor Yellow
    mkdir $parentPath | Out-Null
    Write-Host "  ✓ Diretório criado" -ForegroundColor Green
}

if (Test-Path "$modelPath\am") {
    Write-Host "  ✓ Modelo Vosk encontrado" -ForegroundColor Green
    $env:VOSK_MODEL_PATH = $modelPath
} else {
    Write-Host ""
    Write-Host "  ⚠⚠⚠ MODELO VOSK NÃO ENCONTRADO ⚠⚠⚠" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Para usar o serviço, você precisa:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Abra seu navegador e acesse:" -ForegroundColor Yellow
    Write-Host "     https://alphacephei.com/vosk/models" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Baixe este arquivo: vosk-model-small-pt-0.3.zip - tamanho 50 MB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  3. Extraia para: $modelPath\" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  4. Execute este script novamente: .\rodar.ps1" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
Write-Host ""

# ============================================================
# Passo 5: Configurar variáveis de ambiente
# ============================================================
Write-Host "[5] Configurando variáveis..." -ForegroundColor Yellow

$env:VOSK_MODEL_PATH = $modelPath
$env:GLOSSA_SERVICE_URL = "http://localhost:9000/traduzir"
$env:STT_PORT = "9100"
$env:STT_LOG_LEVEL = "INFO"

Write-Host "  ✓ VOSK_MODEL_PATH: $env:VOSK_MODEL_PATH" -ForegroundColor Green
Write-Host "  ✓ STT_PORT: $env:STT_PORT" -ForegroundColor Green
Write-Host "  ✓ GLOSSA_SERVICE_URL: $env:GLOSSA_SERVICE_URL" -ForegroundColor Green
Write-Host ""

# ============================================================
# Passo 6: Liberar porta se necessário
# ============================================================
Write-Host "[6] Verificando porta..." -ForegroundColor Yellow

$portInUse = Get-NetTCPConnection -LocalPort 9100 -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "  ⚠ Porta 9100 já em uso" -ForegroundColor Yellow
    Write-Host "  ⚠ Liberando..." -ForegroundColor Yellow
    Stop-Process -Id $portInUse.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Porta liberada" -ForegroundColor Green
} else {
    Write-Host "  ✓ Porta 9100 disponível" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# Passo 7: Criar diretório de logs
# ============================================================
Write-Host "[7] Criando diretório de logs..." -ForegroundColor Yellow

if (-not (Test-Path "..\logs")) {
    mkdir ..\logs | Out-Null
}
Write-Host "  ✓ Diretório de logs pronto" -ForegroundColor Green
Write-Host ""

# ============================================================
# Passo 8: Iniciar serviço
# ============================================================
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✓ INICIANDO SERVIÇO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "  WebSocket: ws://localhost:9100/stt" -ForegroundColor Cyan
Write-Host "  Health:    http://localhost:9100/health" -ForegroundColor Cyan
Write-Host "  Docs:      http://localhost:9100/docs" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Pressione CTRL+C para parar o serviço" -ForegroundColor Yellow
Write-Host ""

# Inicia o serviço
python run_stt_service.py
