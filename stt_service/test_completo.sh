#!/bin/bash
# ============================================================
# Script de Teste Completo - Microsserviço STT (Linux/Mac)
# ============================================================
# Executa verificação completa do serviço em um único comando
# Uso: ./test_completo.sh
# ============================================================

echo "============================================================"
echo "  TESTE COMPLETO - Microsserviço STT"
echo "============================================================"
echo ""

# Contador de erros
ERROS=0

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================
# 1. Verificar Python
# ============================================================
echo -e "${YELLOW}[1/7] Verificando Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓ Python encontrado: $PYTHON_VERSION${NC}"
else
    echo -e "  ${RED}✗ Python3 não está instalado${NC}"
    ((ERROS++))
fi
echo ""

# ============================================================
# 2. Verificar Ambiente Virtual
# ============================================================
echo -e "${YELLOW}[2/7] Verificando ambiente virtual...${NC}"
if [ -f "venv_stt/bin/activate" ]; then
    echo -e "  ${GREEN}✓ Ambiente virtual encontrado${NC}"
    source venv_stt/bin/activate
    echo -e "  ${GREEN}✓ Ambiente virtual ativado${NC}"
else
    echo -e "  ${YELLOW}⚠ Ambiente virtual não encontrado. Criando...${NC}"
    python3 -m venv venv_stt
    
    if [ -f "venv_stt/bin/activate" ]; then
        echo -e "  ${GREEN}✓ Ambiente virtual criado${NC}"
        source venv_stt/bin/activate
        
        echo -e "  ${YELLOW}⚠ Instalando dependências...${NC}"
        pip install -q -r requirements.txt
        echo -e "  ${GREEN}✓ Dependências instaladas${NC}"
    else
        echo -e "  ${RED}✗ Falha ao criar ambiente virtual${NC}"
        ((ERROS++))
    fi
fi
echo ""

# ============================================================
# 3. Verificar Modelo Vosk
# ============================================================
echo -e "${YELLOW}[3/7] Verificando modelo Vosk...${NC}"

if [ -n "$VOSK_MODEL_PATH" ]; then
    echo -e "  ${GREEN}✓ VOSK_MODEL_PATH configurado: $VOSK_MODEL_PATH${NC}"
    
    if [ -d "$VOSK_MODEL_PATH" ]; then
        echo -e "  ${GREEN}✓ Diretório do modelo encontrado${NC}"
        
        # Verificar estrutura
        ALL_FOUND=true
        for dir in am graph conf; do
            if [ ! -d "$VOSK_MODEL_PATH/$dir" ]; then
                echo -e "  ${RED}✗ Diretório obrigatório não encontrado: $dir${NC}"
                ALL_FOUND=false
            fi
        done
        
        if [ "$ALL_FOUND" = true ]; then
            echo -e "  ${GREEN}✓ Estrutura do modelo válida${NC}"
        else
            ((ERROS++))
        fi
    else
        echo -e "  ${RED}✗ Diretório não existe: $VOSK_MODEL_PATH${NC}"
        echo -e "  ${YELLOW}💡 Baixe o modelo de: https://alphacephei.com/vosk/models${NC}"
        ((ERROS++))
    fi
else
    echo -e "  ${RED}✗ VOSK_MODEL_PATH não configurado${NC}"
    echo -e "  ${YELLOW}💡 Configure com: export VOSK_MODEL_PATH='caminho/do/modelo'${NC}"
    
    # Tentar detectar automaticamente
    POSSIBLE_PATHS=(
        "../models/vosk-model-small-pt-0.3"
        "models/vosk-model-small-pt-0.3"
        "/usr/local/share/vosk-model-small-pt-0.3"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -d "$path" ]; then
            echo -e "  ${YELLOW}⚠ Modelo detectado em: $path${NC}"
            echo -e "  ${YELLOW}⚠ Configurando automaticamente...${NC}"
            export VOSK_MODEL_PATH=$(realpath "$path")
            echo -e "  ${GREEN}✓ VOSK_MODEL_PATH definido: $VOSK_MODEL_PATH${NC}"
            break
        fi
    done
    
    if [ -z "$VOSK_MODEL_PATH" ]; then
        ((ERROS++))
    fi
fi
echo ""

# ============================================================
# 4. Configurar Variáveis Adicionais
# ============================================================
echo -e "${YELLOW}[4/7] Configurando variáveis de ambiente...${NC}"

if [ -z "$GLOSSA_SERVICE_URL" ]; then
    export GLOSSA_SERVICE_URL="http://localhost:9000/traduzir"
    echo -e "  ${YELLOW}⚠ GLOSSA_SERVICE_URL não configurado, usando padrão: $GLOSSA_SERVICE_URL${NC}"
else
    echo -e "  ${GREEN}✓ GLOSSA_SERVICE_URL: $GLOSSA_SERVICE_URL${NC}"
fi

if [ -z "$STT_PORT" ]; then
    export STT_PORT="9100"
fi
echo -e "  ${GREEN}✓ STT_PORT: $STT_PORT${NC}"

if [ -z "$STT_LOG_LEVEL" ]; then
    export STT_LOG_LEVEL="INFO"
fi
echo -e "  ${GREEN}✓ STT_LOG_LEVEL: $STT_LOG_LEVEL${NC}"
echo ""

# ============================================================
# 5. Parar Processos Existentes
# ============================================================
echo -e "${YELLOW}[5/7] Verificando processos existentes...${NC}"

# Verificar se porta está em uso
if lsof -Pi :$STT_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠ Porta $STT_PORT já em uso${NC}"
    echo -e "  ${YELLOW}⚠ Tentando liberar...${NC}"
    
    PID=$(lsof -Pi :$STT_PORT -sTCP:LISTEN -t)
    kill -9 $PID 2>/dev/null
    sleep 2
    echo -e "  ${GREEN}✓ Porta liberada${NC}"
else
    echo -e "  ${GREEN}✓ Porta $STT_PORT disponível${NC}"
fi
echo ""

# ============================================================
# 6. Iniciar Serviço STT
# ============================================================
echo -e "${YELLOW}[6/7] Iniciando serviço STT...${NC}"

if [ $ERROS -gt 0 ]; then
    echo -e "  ${RED}✗ Não é possível iniciar o serviço devido a erros anteriores${NC}"
    echo ""
    echo "============================================================"
    echo -e "  ${RED}TESTE FALHOU - $ERROS erro(s) encontrado(s)${NC}"
    echo "============================================================"
    exit 1
fi

# Iniciar serviço em background
python3 run_stt_service.py > /tmp/stt_service.log 2>&1 &
SERVICE_PID=$!

echo -e "  ${YELLOW}⚠ Aguardando inicialização do serviço...${NC}"
sleep 5

# Verificar se processo está rodando
if ps -p $SERVICE_PID > /dev/null; then
    echo -e "  ${GREEN}✓ Serviço STT iniciado (PID: $SERVICE_PID)${NC}"
else
    echo -e "  ${RED}✗ Falha ao iniciar serviço${NC}"
    cat /tmp/stt_service.log
    ((ERROS++))
fi
echo ""

# ============================================================
# 7. Executar Testes
# ============================================================
echo -e "${YELLOW}[7/7] Executando testes...${NC}"
echo ""

# Teste 1: Health Check
echo -e "  ${CYAN}[Teste 1/3] Health Check...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:$STT_PORT/health)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "    ${GREEN}✓ Health check passou${NC}"
    echo "$HEALTH_RESPONSE" | head -n-1 | python3 -m json.tool 2>/dev/null | head -n 5 | sed 's/^/      /'
else
    echo -e "    ${RED}✗ Health check falhou (HTTP $HTTP_CODE)${NC}"
    ((ERROS++))
fi
echo ""

# Teste 2: Endpoint Root
echo -e "  ${CYAN}[Teste 2/3] Endpoint raiz (/)...${NC}"
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:$STT_PORT/)
HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "    ${GREEN}✓ Endpoint raiz respondeu${NC}"
    echo "$ROOT_RESPONSE" | head -n-1 | python3 -m json.tool 2>/dev/null | grep -E "(service|websocket_endpoint)" | sed 's/^/      /'
else
    echo -e "    ${RED}✗ Endpoint raiz falhou (HTTP $HTTP_CODE)${NC}"
    ((ERROS++))
fi
echo ""

# Teste 3: Documentação Swagger
echo -e "  ${CYAN}[Teste 3/3] Documentação Swagger...${NC}"
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$STT_PORT/docs)

if [ "$DOCS_CODE" = "200" ]; then
    echo -e "    ${GREEN}✓ Documentação acessível${NC}"
    echo -e "      ${CYAN}- URL: http://localhost:$STT_PORT/docs${NC}"
else
    echo -e "    ${RED}✗ Documentação não acessível (HTTP $DOCS_CODE)${NC}"
    ((ERROS++))
fi
echo ""

# ============================================================
# Resultado Final
# ============================================================
echo "============================================================"
if [ $ERROS -eq 0 ]; then
    echo -e "  ${GREEN}✅ TODOS OS TESTES PASSARAM!${NC}"
    echo ""
    echo -e "  ${CYAN}O serviço está rodando em:${NC}"
    echo -e "    • WebSocket: ws://localhost:$STT_PORT/stt"
    echo -e "    • Health: http://localhost:$STT_PORT/health"
    echo -e "    • Docs: http://localhost:$STT_PORT/docs"
    echo ""
    echo -e "  ${CYAN}Próximos passos:${NC}"
    echo -e "    1. Abrir cliente web: open test_client.html (Mac) ou xdg-open test_client.html (Linux)"
    echo -e "    2. Ver logs: tail -f ../logs/stt_service.log"
    echo -e "    3. Parar serviço: kill $SERVICE_PID"
    echo ""
    echo -e "  ${YELLOW}PID do serviço: $SERVICE_PID${NC}"
    echo -e "  ${YELLOW}Para parar: kill $SERVICE_PID${NC}"
else
    echo -e "  ${RED}❌ TESTES FALHARAM - $ERROS erro(s)${NC}"
    echo ""
    echo -e "  ${YELLOW}Verifique os erros acima e tente novamente.${NC}"
    
    # Parar serviço
    if ps -p $SERVICE_PID > /dev/null; then
        kill $SERVICE_PID 2>/dev/null
        echo -e "  ${GREEN}✓ Serviço parado${NC}"
    fi
fi
echo "============================================================"
echo ""

exit $ERROS
