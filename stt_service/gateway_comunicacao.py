"""
Gateway de Comunicação - Camada de Entrada WebSocket
====================================================

Ponto de entrada do microsserviço, responsável por:
- Gerenciar conexões WebSocket
- Validar protocolo de comunicação
- Orquestrar interação entre motor STT e despachante
- Emitir mensagens padronizadas para o cliente

Decisão arquitetural:
Esta camada NÃO conhece detalhes de Vosk ou do serviço de glossa.
Ela apenas coordena o fluxo de dados entre componentes especializados,
mantendo baixo acoplamento e alta coesão.

Fundamentação acadêmica:
A separação clara de responsabilidades facilita:
- Testes unitários de cada camada isoladamente
- Substituição de componentes (ex: trocar Vosk por Whisper)
- Análise de latência por etapa do pipeline
- Documentação e explicação em artigos científicos
"""

import asyncio
import logging
import uuid
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .configuracao import ConfiguracaoSTT
from .esquema_mensagens import (
    MensagemSessaoIniciada,
    MensagemTranscricaoParcial,
    MensagemTranscricaoFinal,
    MensagemErro,
    RespostaHealthCheck,
    obter_timestamp_iso
)
from .motor_stt_vosk import MotorSTTVosk, CarregadorModeloVosk
from .orquestrador_envio import OrquestradorEnvioGlossa


# ==========================================
# Configuração de Logging
# ==========================================

def configurar_logging():
    """
    Configura logging estruturado com handlers de arquivo e console.
    
    Alinhado com padrão do professional_api.py:
    - Logs em arquivo rotativo
    - Logs no console para desenvolvimento
    - Formato com timestamp, nível e módulo
    """
    log_file = ConfiguracaoSTT.DIRETORIO_LOGS / ConfiguracaoSTT.ARQUIVO_LOG
    
    logging.basicConfig(
        level=getattr(logging, ConfiguracaoSTT.NIVEL_LOG),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("STT Microsserviço - Inicialização")
    logger.info(f"Versão: {ConfiguracaoSTT.VERSAO_SERVICO}")
    logger.info(f"Porta: {ConfiguracaoSTT.PORTA_SERVICO}")
    logger.info(f"Logs: {log_file}")
    logger.info("=" * 60)


# ==========================================
# Aplicação FastAPI
# ==========================================

app = FastAPI(
    title="STT Microsserviço",
    description=(
        "Serviço de transcrição de fala em tempo real (pt-BR) "
        "com streaming via WebSocket e integração com serviço de glossa."
    ),
    version=ConfiguracaoSTT.VERSAO_SERVICO,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configura CORS para permitir acesso cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=ConfiguracaoSTT.ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


# ==========================================
# Lifecycle: Startup
# ==========================================

@app.on_event("startup")
async def startup():
    """
    Inicialização do serviço.
    
    Decisão de design: Validar configurações e pré-carregar
    modelo Vosk no startup para fail-fast em caso de erro.
    """
    try:
        logger.info("Iniciando serviço STT...")
        
        # Valida configurações
        ConfiguracaoSTT.validar()
        logger.info("✓ Configurações validadas")
        
        # Pré-carrega modelo Vosk
        CarregadorModeloVosk.obter_modelo()
        logger.info("✓ Modelo Vosk pré-carregado")
        
        logger.info("✓ Serviço STT pronto para aceitar conexões")
        
    except Exception as e:
        logger.critical(f"✗ Falha na inicialização: {e}")
        raise


# ==========================================
# Endpoint: Health Check
# ==========================================

@app.get(
    "/health",
    response_model=RespostaHealthCheck,
    summary="Verificação de saúde do serviço",
    tags=["Monitoramento"]
)
async def health_check():
    """
    Endpoint de saúde para monitoramento externo.
    
    Retorna status dos componentes críticos:
    - API (sempre healthy se endpoint responde)
    - Modelo Vosk (loaded/not_loaded)
    - Serviço de glossa (não verifica conexão aqui)
    """
    modelo_carregado = CarregadorModeloVosk.modelo_esta_carregado()
    
    componentes = {
        "api": {
            "status": "healthy",
            "porta": ConfiguracaoSTT.PORTA_SERVICO
        },
        "vosk_model": {
            "status": "loaded" if modelo_carregado else "not_loaded",
            "path": str(ConfiguracaoSTT.CAMINHO_MODELO_VOSK) if modelo_carregado else None,
            "sample_rate": ConfiguracaoSTT.TAXA_AMOSTRAGEM,
            "language": ConfiguracaoSTT.IDIOMA_ENTRADA
        },
        "glossa_service": {
            "status": "configured",
            "url": ConfiguracaoSTT.URL_SERVICO_GLOSSA
        }
    }
    
    # Status geral: healthy se modelo carregado
    status_geral = "healthy" if modelo_carregado else "degraded"
    
    return RespostaHealthCheck(
        status=status_geral,
        timestamp=obter_timestamp_iso(),
        version=ConfiguracaoSTT.VERSAO_SERVICO,
        components=componentes
    )


# ==========================================
# Endpoint: Root
# ==========================================

@app.get("/", tags=["Informações"])
async def root():
    """
    Endpoint raiz com informações básicas do serviço.
    """
    return {
        "service": ConfiguracaoSTT.NOME_SERVICO,
        "version": ConfiguracaoSTT.VERSAO_SERVICO,
        "language": ConfiguracaoSTT.IDIOMA_ENTRADA,
        "websocket_endpoint": "/stt",
        "documentation": "/docs",
        "health_check": "/health",
        "timestamp": obter_timestamp_iso()
    }


# ==========================================
# Endpoint: WebSocket /stt
# ==========================================

@app.websocket("/stt")
async def websocket_stt(websocket: WebSocket):
    """
    Endpoint WebSocket para streaming de áudio e transcrição.
    
    Protocolo:
    1. Cliente conecta ao WebSocket
    2. Servidor envia MensagemSessaoIniciada com session_id
    3. Cliente envia frames de áudio binário (PCM mono 16kHz)
    4. Servidor processa e emite:
       - MensagemTranscricaoParcial (incrementais)
       - MensagemTranscricaoFinal (após fronteira + dispatch)
    5. Ao fechar conexão, servidor finaliza sessão
    
    Decisão de fluxo:
    - Aceita conexão imediatamente (sem autenticação inicial)
    - Gera session_id único (UUID v4)
    - Instancia motor STT e orquestrador por sessão
    - Loop de recepção de áudio até desconexão
    - Cleanup automático ao fechar
    
    Fundamentação acadêmica:
    O fluxo implementa o conceito de "sessão de transcrição",
    onde cada conexão mantém estado isolado, permitindo
    análise granular de performance por usuário/sessão.
    """
    # Gera ID único para esta sessão
    session_id = str(uuid.uuid4())
    session_logger = logging.getLogger(f"{__name__}.{session_id[:8]}")
    
    # Aceita conexão WebSocket
    await websocket.accept()
    session_logger.info(f"Nova sessão WebSocket estabelecida: {session_id}")
    
    # Inicializa componentes da sessão
    motor_stt: Optional[MotorSTTVosk] = None
    orquestrador: Optional[OrquestradorEnvioGlossa] = None
    
    try:
        # Instancia motor STT
        motor_stt = MotorSTTVosk(session_id)
        session_logger.info("Motor STT inicializado")
        
        # Instancia orquestrador de envio
        orquestrador = OrquestradorEnvioGlossa(session_id)
        session_logger.info("Orquestrador de envio inicializado")
        
        # Envia mensagem de sessão iniciada
        mensagem_inicio = MensagemSessaoIniciada(
            session_id=session_id,
            version=ConfiguracaoSTT.VERSAO_SERVICO
        )
        await websocket.send_json(mensagem_inicio.dict())
        session_logger.info("Mensagem de sessão iniciada enviada")
        
        # Controle de throttling para parciais
        ultima_emissao_parcial = 0.0
        
        # Loop principal: recebe e processa áudio
        while True:
            # Aguarda próximo frame de áudio (binário)
            audio_bytes = await websocket.receive_bytes()
            
            if not audio_bytes:
                session_logger.warning("Frame vazio recebido, ignorando")
                continue
            
            # Processa áudio com motor STT
            is_final, texto, confianca = motor_stt.processar_audio(audio_bytes)
            
            if is_final and texto:
                # Transcrição final: envia para glossa e emite mensagem
                session_logger.info(f"Transcrição final detectada: '{texto}'")
                
                # Despacha para serviço de glossa
                resultado_dispatch = orquestrador.enviar_para_glossa(
                    texto,
                    confianca
                )
                
                # Emite mensagem final para cliente
                mensagem_final = MensagemTranscricaoFinal(
                    session_id=session_id,
                    text=texto,
                    confidence=confianca,
                    dispatch=resultado_dispatch
                )
                await websocket.send_json(mensagem_final.dict())
                session_logger.info("Mensagem de transcrição final enviada")
            
            elif not is_final and texto:
                # Transcrição parcial: emite com throttling
                import time
                agora = time.time()
                
                if agora - ultima_emissao_parcial >= ConfiguracaoSTT.INTERVALO_EMISSAO_PARCIAL:
                    mensagem_parcial = MensagemTranscricaoParcial(
                        session_id=session_id,
                        text=texto,
                        confidence=confianca
                    )
                    await websocket.send_json(mensagem_parcial.dict())
                    ultima_emissao_parcial = agora
                    # Log throttled para evitar verbosidade
                    if motor_stt.transcricoes_parciais % 20 == 0:
                        session_logger.debug(f"Parcial enviada: '{texto[:30]}...'")
    
    except WebSocketDisconnect:
        session_logger.info("Cliente desconectou WebSocket")
    
    except Exception as e:
        session_logger.exception(f"Erro durante processamento: {e}")
        
        # Tenta enviar mensagem de erro ao cliente
        try:
            mensagem_erro = MensagemErro(
                session_id=session_id,
                error_code="PROCESSING_ERROR",
                error_message=str(e)
            )
            await websocket.send_json(mensagem_erro.dict())
        except Exception:
            pass  # Cliente já desconectou
    
    finally:
        # Cleanup: finaliza sessão e exibe estatísticas
        session_logger.info("Finalizando sessão...")
        
        if motor_stt:
            # Tenta extrair última transcrição pendente
            resultado_final = motor_stt.finalizar_sessao()
            if resultado_final:
                texto_final, confianca_final = resultado_final
                session_logger.info(
                    f"Transcrição final forçada: '{texto_final}'"
                )
                
                # Opcionalmente, envia para glossa
                if orquestrador:
                    orquestrador.enviar_para_glossa(texto_final, confianca_final)
            
            # Log estatísticas do motor
            stats_motor = motor_stt.obter_estatisticas()
            session_logger.info(f"Estatísticas STT: {stats_motor}")
        
        if orquestrador:
            # Log estatísticas do orquestrador
            stats_orquestrador = orquestrador.obter_estatisticas()
            session_logger.info(f"Estatísticas envio: {stats_orquestrador}")
        
        session_logger.info(f"Sessão {session_id[:8]} encerrada")


# ==========================================
# Ponto de Entrada
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    # Configura logging antes de iniciar servidor
    configurar_logging()
    
    logger.info(
        f"Iniciando servidor na porta {ConfiguracaoSTT.PORTA_SERVICO}..."
    )
    
    # Inicia servidor Uvicorn
    uvicorn.run(
        "gateway_comunicacao:app",
        host="0.0.0.0",
        port=ConfiguracaoSTT.PORTA_SERVICO,
        log_level=ConfiguracaoSTT.NIVEL_LOG.lower(),
        reload=False  # Desabilitar reload em produção
    )
