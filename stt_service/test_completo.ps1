# ============================================================
# Script de Teste Completo - Microsserviço STT
# ============================================================
# Executa verificação completa do serviço em um único comando
# Uso: .\test_completo.ps1
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TESTE COMPLETO - Microsserviço STT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Contador de erros
$erros = 0

# ============================================================
# 1. Verificar Python
# ============================================================
Write-Host "[1/7] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Python encontrado: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python não encontrado"
    }
} catch {
    Write-Host "  ✗ Python não está instalado ou não está no PATH" -ForegroundColor Red
    $erros++
}
Write-Host ""

# ============================================================
# 2. Verificar Ambiente Virtual
# ============================================================
Write-Host "[2/7] Verificando ambiente virtual..." -ForegroundColor Yellow
if (Test-Path "venv_stt\Scripts\activate.ps1") {
    Write-Host "  ✓ Ambiente virtual encontrado" -ForegroundColor Green
    
    # Ativar ambiente virtual
    & "venv_stt\Scripts\activate.ps1"
    Write-Host "  ✓ Ambiente virtual ativado" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Ambiente virtual não encontrado. Criando..." -ForegroundColor Yellow
    python -m venv venv_stt
    
    if (Test-Path "venv_stt\Scripts\activate.ps1") {
        Write-Host "  ✓ Ambiente virtual criado" -ForegroundColor Green
        & "venv_stt\Scripts\activate.ps1"
        
        Write-Host "  ⚠ Instalando dependências..." -ForegroundColor Yellow
        pip install -q -r requirements.txt
        Write-Host "  ✓ Dependências instaladas" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Falha ao criar ambiente virtual" -ForegroundColor Red
        $erros++
    }
}
Write-Host ""

# ============================================================
# 3. Verificar Modelo Vosk
# ============================================================
Write-Host "[3/7] Verificando modelo Vosk..." -ForegroundColor Yellow

# Verificar variável de ambiente
if ($env:VOSK_MODEL_PATH) {
    Write-Host "  ✓ VOSK_MODEL_PATH configurado: $env:VOSK_MODEL_PATH" -ForegroundColor Green
    
    # Verificar se diretório existe
    if (Test-Path $env:VOSK_MODEL_PATH) {
        Write-Host "  ✓ Diretório do modelo encontrado" -ForegroundColor Green
        
        # Verificar estrutura do modelo
        $requiredDirs = @("am", "graph", "conf")
        $allFound = $true
        foreach ($dir in $requiredDirs) {
            $path = Join-Path $env:VOSK_MODEL_PATH $dir
            if (-not (Test-Path $path)) {
                Write-Host "  ✗ Diretório obrigatório não encontrado: $dir" -ForegroundColor Red
                $allFound = $false
            }
        }
        
        if ($allFound) {
            Write-Host "  ✓ Estrutura do modelo válida" -ForegroundColor Green
        } else {
            $erros++
        }
    } else {
        Write-Host "  ✗ Diretório não existe: $env:VOSK_MODEL_PATH" -ForegroundColor Red
        Write-Host "  💡 Baixe o modelo de: https://alphacephei.com/vosk/models" -ForegroundColor Yellow
        $erros++
    }
} else {
    Write-Host "  ✗ VOSK_MODEL_PATH não configurado" -ForegroundColor Red
    Write-Host "  💡 Configure com: `$env:VOSK_MODEL_PATH = 'caminho\do\modelo'" -ForegroundColor Yellow
    
    # Tentar detectar modelo automaticamente
    $possiblePaths = @(
        "d:\ela_teste\ela_mvp\models\vosk-model-small-pt-0.3",
        "..\models\vosk-model-small-pt-0.3",
        "models\vosk-model-small-pt-0.3"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            Write-Host "  ⚠ Modelo detectado em: $path" -ForegroundColor Yellow
            Write-Host "  ⚠ Configurando automaticamente..." -ForegroundColor Yellow
            $env:VOSK_MODEL_PATH = (Resolve-Path $path).Path
            Write-Host "  ✓ VOSK_MODEL_PATH definido: $env:VOSK_MODEL_PATH" -ForegroundColor Green
            break
        }
    }
    
    if (-not $env:VOSK_MODEL_PATH) {
        $erros++
    }
}
Write-Host ""

# ============================================================
# 4. Configurar Variáveis Adicionais (Opcionais)
# ============================================================
Write-Host "[4/7] Configurando variáveis de ambiente..." -ForegroundColor Yellow

if (-not $env:GLOSSA_SERVICE_URL) {
    $env:GLOSSA_SERVICE_URL = "http://localhost:9000/traduzir"
    Write-Host "  ⚠ GLOSSA_SERVICE_URL não configurado, usando padrão: $env:GLOSSA_SERVICE_URL" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ GLOSSA_SERVICE_URL: $env:GLOSSA_SERVICE_URL" -ForegroundColor Green
}

if (-not $env:STT_PORT) {
    $env:STT_PORT = "9100"
}
Write-Host "  ✓ STT_PORT: $env:STT_PORT" -ForegroundColor Green

if (-not $env:STT_LOG_LEVEL) {
    $env:STT_LOG_LEVEL = "INFO"
}
Write-Host "  ✓ STT_LOG_LEVEL: $env:STT_LOG_LEVEL" -ForegroundColor Green
Write-Host ""

# ============================================================
# 5. Parar Processos Existentes
# ============================================================
Write-Host "[5/7] Verificando processos existentes..." -ForegroundColor Yellow

# Verificar se porta já está em uso
$portInUse = Get-NetTCPConnection -LocalPort $env:STT_PORT -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "  ⚠ Porta $env:STT_PORT já em uso" -ForegroundColor Yellow
    Write-Host "  ⚠ Tentando liberar..." -ForegroundColor Yellow
    
    $processId = $portInUse.OwningProcess
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Porta liberada" -ForegroundColor Green
} else {
    Write-Host "  ✓ Porta $env:STT_PORT disponível" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# 6. Iniciar Serviço STT
# ============================================================
Write-Host "[6/7] Iniciando serviço STT..." -ForegroundColor Yellow

if ($erros -gt 0) {
    Write-Host "  ✗ Não é possível iniciar o serviço devido a erros anteriores" -ForegroundColor Red
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  TESTE FALHOU - $erros erro(s) encontrado(s)" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    exit 1
}

# Iniciar serviço em background
$job = Start-Job -ScriptBlock {
    param($modelPath, $glossaUrl, $port, $logLevel)
    
    $env:VOSK_MODEL_PATH = $modelPath
    $env:GLOSSA_SERVICE_URL = $glossaUrl
    $env:STT_PORT = $port
    $env:STT_LOG_LEVEL = $logLevel
    
    Set-Location $using:PWD
    & venv_stt\Scripts\python.exe run_stt_service.py
} -ArgumentList $env:VOSK_MODEL_PATH, $env:GLOSSA_SERVICE_URL, $env:STT_PORT, $env:STT_LOG_LEVEL

Write-Host "  ⚠ Aguardando inicialização do serviço..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificar se job está rodando
if ($job.State -eq "Running") {
    Write-Host "  ✓ Serviço STT iniciado (Job ID: $($job.Id))" -ForegroundColor Green
} else {
    Write-Host "  ✗ Falha ao iniciar serviço" -ForegroundColor Red
    Receive-Job -Job $job
    Remove-Job -Job $job -Force
    $erros++
}
Write-Host ""

# ============================================================
# 7. Executar Testes
# ============================================================
Write-Host "[7/7] Executando testes..." -ForegroundColor Yellow
Write-Host ""

# Teste 1: Health Check
Write-Host "  [Teste 1/3] Health Check..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:$env:STT_PORT/health" -Method Get -TimeoutSec 5
    
    if ($response.status -eq "healthy") {
        Write-Host "    ✓ Health check passou" -ForegroundColor Green
        Write-Host "      - Status: $($response.status)" -ForegroundColor Gray
        Write-Host "      - Versão: $($response.version)" -ForegroundColor Gray
        Write-Host "      - Modelo: $($response.components.vosk_model.status)" -ForegroundColor Gray
    } else {
        Write-Host "    ✗ Status não é 'healthy': $($response.status)" -ForegroundColor Red
        $erros++
    }
} catch {
    Write-Host "    ✗ Falha ao conectar ao serviço" -ForegroundColor Red
    Write-Host "      Erro: $_" -ForegroundColor Red
    $erros++
}
Write-Host ""

# Teste 2: Endpoint Root
Write-Host "  [Teste 2/3] Endpoint raiz (/)..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:$env:STT_PORT/" -Method Get -TimeoutSec 5
    
    if ($response.service) {
        Write-Host "    ✓ Endpoint raiz respondeu" -ForegroundColor Green
        Write-Host "      - Serviço: $($response.service)" -ForegroundColor Gray
        Write-Host "      - WebSocket: $($response.websocket_endpoint)" -ForegroundColor Gray
    } else {
        Write-Host "    ✗ Resposta inválida" -ForegroundColor Red
        $erros++
    }
} catch {
    Write-Host "    ✗ Falha ao acessar endpoint raiz" -ForegroundColor Red
    $erros++
}
Write-Host ""

# Teste 3: Documentação Swagger
Write-Host "  [Teste 3/3] Documentação Swagger..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$env:STT_PORT/docs" -Method Get -TimeoutSec 5
    
    if ($response.StatusCode -eq 200) {
        Write-Host "    ✓ Documentação acessível" -ForegroundColor Green
        Write-Host "      - URL: http://localhost:$env:STT_PORT/docs" -ForegroundColor Gray
    } else {
        Write-Host "    ✗ Status inesperado: $($response.StatusCode)" -ForegroundColor Red
        $erros++
    }
} catch {
    Write-Host "    ✗ Falha ao acessar documentação" -ForegroundColor Red
    $erros++
}
Write-Host ""

# ============================================================
# Resultado Final
# ============================================================
Write-Host "============================================================" -ForegroundColor Cyan
if ($erros -eq 0) {
    Write-Host "  ✅ TODOS OS TESTES PASSARAM!" -ForegroundColor Green
    Write-Host "" -ForegroundColor Cyan
    Write-Host "  O serviço está rodando em:" -ForegroundColor Cyan
    Write-Host "    • WebSocket: ws://localhost:$env:STT_PORT/stt" -ForegroundColor White
    Write-Host "    • Health: http://localhost:$env:STT_PORT/health" -ForegroundColor White
    Write-Host "    • Docs: http://localhost:$env:STT_PORT/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "  Próximos passos:" -ForegroundColor Cyan
    Write-Host "    1. Abrir cliente web: start test_client.html" -ForegroundColor White
    Write-Host "    2. Ver logs: Get-Content ..\logs\stt_service.log -Wait" -ForegroundColor White
    Write-Host "    3. Parar serviço: Stop-Job $($job.Id)" -ForegroundColor White
    Write-Host ""
    Write-Host "  Job ID do serviço: $($job.Id)" -ForegroundColor Yellow
    Write-Host "  Para parar: Stop-Job $($job.Id) ; Remove-Job $($job.Id)" -ForegroundColor Yellow
} else {
    Write-Host "  ❌ TESTES FALHARAM - $erros erro(s)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Verifique os erros acima e tente novamente." -ForegroundColor Yellow
    
    # Parar job se iniciado
    if ($job -and $job.State -eq "Running") {
        Stop-Job -Job $job -Force
        Remove-Job -Job $job -Force
        Write-Host "  ✓ Serviço parado" -ForegroundColor Green
    }
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

exit $erros
