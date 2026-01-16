# Script simplificado para rodar o serviço STT
# Uso: .\rodar_simples.ps1

Write-Host "===============================" -ForegroundColor Cyan
Write-Host "  INICIANDO SERVIÇO STT" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# 1. Ambiente virtual
if (!(Test-Path "venv_stt\Scripts\activate.ps1")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv_stt
}

# 2. Ativar ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
. "venv_stt\Scripts\Activate.ps1"

# 3. Instalar dependências
Write-Host "Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt

# 4. Verificar modelo Vosk
$modelPath = "d:\ela_teste\ela_mvp\models\vosk-model-small-pt-0.3"
if (!(Test-Path "$modelPath\am")) {
    Write-Host "MODELO VOSK NÃO ENCONTRADO!" -ForegroundColor Red
    Write-Host "Baixe e extraia para: $modelPath" -ForegroundColor Yellow
    Write-Host "https://alphacephei.com/vosk/models" -ForegroundColor Cyan
    exit 1
}

# 5. Configurar variáveis de ambiente
$env:VOSK_MODEL_PATH = $modelPath
$env:GLOSSA_SERVICE_URL = "http://localhost:9000/traduzir"
$env:STT_PORT = "9100"
$env:STT_LOG_LEVEL = "INFO"

# 6. Rodar serviço
Write-Host "Rodando serviço..." -ForegroundColor Green
python run_stt_service.py
