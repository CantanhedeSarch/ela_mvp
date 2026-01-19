"""
Esquemas de Mensagens - Contratos de Dados
==========================================

Define estruturas de dados padronizadas para comunicação via WebSocket,
garantindo consistência de tipos e facilitando validação automática.

Decisão arquitetural:
- Uso de Pydantic para validação declarativa e serialização JSON
- Timestamps em formato ISO-8601 para interoperabilidade
- Enumerações explícitas para tipos de mensagem
- Estruturas aninhadas para metadados de despacho

Fundamentação acadêmica:
A padronização de mensagens permite rastreabilidade completa do fluxo
de dados, essencial para avaliação experimental e análise de latência.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# ==========================================
# Enumerações de Tipos
# ==========================================

class TipoMensagemSTT(str, Enum):
    """
    Tipos de mensagens emitidas pelo serviço STT.
    
    - SESSAO_INICIADA: Confirmação de estabelecimento da sessão WebSocket
    - TRANSCRICAO_PARCIAL: Resultado intermediário da transcrição
    - TRANSCRICAO_FINAL: Resultado definitivo após detecção de fronteira
    - ERRO: Notificação de erro durante processamento
    """
    SESSAO_INICIADA = "session_started"
    TRANSCRICAO_PARCIAL = "partial"
    TRANSCRICAO_FINAL = "final"
    ERRO = "error"


# ==========================================
# Utilitários de Timestamp
# ==========================================

def obter_timestamp_iso() -> str:
    """
    Retorna timestamp atual em formato ISO-8601 com UTC.
    
    Exemplo: "2026-01-14T15:30:45.123456Z"
    
    Fundamentação: ISO-8601 é o padrão internacional para representação
    de data/hora, garantindo parsing consistente em diferentes plataformas.
    """
    return datetime.utcnow().isoformat() + "Z"


# ==========================================
# Mensagem: Sessão Iniciada
# ==========================================

class MensagemSessaoIniciada(BaseModel):
    """
    Emitida ao estabelecer conexão WebSocket.
    
    Comunica ao cliente as capacidades e configurações da sessão,
    permitindo validação de compatibilidade (taxa de amostragem, formato).
    """
    type: str = Field(
        default=TipoMensagemSTT.SESSAO_INICIADA.value,
        description="Tipo fixo da mensagem"
    )
    session_id: str = Field(
        ...,
        description="Identificador único da sessão (UUID v4)"
    )
    language: str = Field(
        default="pt-br",
        description="Idioma de entrada esperado"
    )
    sample_rate: int = Field(
        default=16000,
        description="Taxa de amostragem esperada (Hz)"
    )
    channels: int = Field(
        default=1,
        description="Número de canais de áudio (1=mono)"
    )
    timestamp: str = Field(
        default_factory=obter_timestamp_iso,
        description="Momento de criação da sessão (ISO-8601)"
    )
    version: str = Field(
        ...,
        description="Versão do serviço STT"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "session_started",
                "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "language": "pt-br",
                "sample_rate": 16000,
                "channels": 1,
                "timestamp": "2026-01-14T15:30:45.123456Z",
                "version": "1.0.0"
            }
        }


# ==========================================
# Mensagem: Transcrição Parcial
# ==========================================

class MensagemTranscricaoParcial(BaseModel):
    """
    Emitida durante processamento incremental.
    
    Fundamentação acadêmica:
    Transcrições parciais permitem análise em tempo real e
    reduzem latência percebida pelo usuário, mas NÃO disparam
    tradução para glossa (apenas transcrições finais fazem isso).
    """
    type: str = Field(
        default=TipoMensagemSTT.TRANSCRICAO_PARCIAL.value,
        description="Tipo fixo da mensagem"
    )
    session_id: str = Field(
        ...,
        description="Identificador da sessão ativa"
    )
    text: str = Field(
        ...,
        description="Texto transcrito até o momento (pode mudar)"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confiança da transcrição (0-1), se disponível"
    )
    timestamp: str = Field(
        default_factory=obter_timestamp_iso,
        description="Momento da emissão (ISO-8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "partial",
                "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "text": "olá como você est",
                "confidence": 0.85,
                "timestamp": "2026-01-14T15:30:46.500000Z"
            }
        }


# ==========================================
# Mensagem: Resultado de Despacho
# ==========================================

class ResultadoDespachoGlossa(BaseModel):
    """
    Metadados sobre o envio da transcrição final ao serviço de tradução.
    
    Decisão arquitetural:
    Incluir resultado do despacho na mensagem final permite ao cliente
    rastrear todo o pipeline e identificar falhas na integração.
    """
    target_url: str = Field(
        ...,
        description="URL do serviço de tradução contatado"
    )
    request_sent: bool = Field(
        ...,
        description="Se a requisição foi enviada com sucesso"
    )
    response_status: Optional[int] = Field(
        default=None,
        description="Código HTTP de resposta (se houver)"
    )
    response_body: Optional[dict] = Field(
        default=None,
        description="Corpo da resposta (resumido, se disponível)"
    )
    duration_ms: Optional[float] = Field(
        default=None,
        description="Duração da requisição em milissegundos"
    )
    error: Optional[str] = Field(
        default=None,
        description="Mensagem de erro, se houver falha"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_url": "http://localhost:9000/traduzir",
                "request_sent": True,
                "response_status": 200,
                "response_body": {"translation": "..."},
                "duration_ms": 45.2,
                "error": None
            }
        }
    
    def dict(self, **kwargs):
        """Sobrescreve dict para garantir response_body seja sempre um dicionário limpo"""
        d = super().dict(**kwargs)
        # Garantir que response_body é um dict Python puro
        if d.get('response_body') is not None:
            if isinstance(d['response_body'], dict):
                d['response_body'] = dict(d['response_body'])
        return d


# ==========================================
# Mensagem: Transcrição Final
# ==========================================

class MensagemTranscricaoFinal(BaseModel):
    """
    Emitida após detecção de fronteira semântica (fim da fala).
    
    Decisão arquitetural crítica:
    APENAS transcrições finais disparam envio ao serviço de tradução.
    Esta mensagem encapsula tanto o resultado da transcrição quanto
    o status do despacho para o serviço de glossa.
    
    Fundamentação acadêmica:
    A separação entre parcial/final implementa o desacoplamento entre
    STT e tradução, permitindo que o motor STT opere de forma agnóstica
    ao domínio enquanto o orquestrador decide quando traduzir.
    """
    type: str = Field(
        default=TipoMensagemSTT.TRANSCRICAO_FINAL.value,
        description="Tipo fixo da mensagem"
    )
    session_id: str = Field(
        ...,
        description="Identificador da sessão ativa"
    )
    text: str = Field(
        ...,
        description="Texto transcrito final (estável)"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confiança da transcrição (0-1), se disponível"
    )
    timestamp: str = Field(
        default_factory=obter_timestamp_iso,
        description="Momento da finalização (ISO-8601)"
    )
    dispatch: Optional[ResultadoDespachoGlossa] = Field(
        default=None,
        description="Metadados sobre o envio ao serviço de glossa"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "final",
                "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "text": "olá como você está",
                "confidence": 0.92,
                "timestamp": "2026-01-14T15:30:47.800000Z",
                "dispatch": {
                    "target_url": "http://localhost:9000/traduzir",
                    "request_sent": True,
                    "response_status": 200,
                    "response_body": {"translation": "OLHAR COMO VOCE ESTAR"},
                    "duration_ms": 45.2,
                    "error": None
                }
            }
        }


# ==========================================
# Mensagem: Erro
# ==========================================

class MensagemErro(BaseModel):
    """
    Emitida quando ocorre erro durante processamento.
    
    Permite ao cliente distinguir entre diferentes tipos de falha
    e tomar ações apropriadas (retry, fallback, notificação).
    """
    type: str = Field(
        default=TipoMensagemSTT.ERRO.value,
        description="Tipo fixo da mensagem"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Identificador da sessão (se disponível)"
    )
    error_code: str = Field(
        ...,
        description="Código de erro categorizado"
    )
    error_message: str = Field(
        ...,
        description="Descrição legível do erro"
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Informações adicionais para depuração"
    )
    timestamp: str = Field(
        default_factory=obter_timestamp_iso,
        description="Momento da ocorrência do erro (ISO-8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "error_code": "AUDIO_FORMAT_INVALID",
                "error_message": "Taxa de amostragem incompatível. Esperado: 16000Hz",
                "details": {"received_rate": 44100},
                "timestamp": "2026-01-14T15:30:48.000000Z"
            }
        }


# ==========================================
# Schema: Health Check
# ==========================================

class RespostaHealthCheck(BaseModel):
    """
    Resposta do endpoint de saúde do serviço.
    
    Permite monitoramento externo e validação de prontidão operacional.
    """
    status: str = Field(
        ...,
        description="Status geral do serviço (healthy, degraded, unhealthy)"
    )
    timestamp: str = Field(
        default_factory=obter_timestamp_iso,
        description="Momento da verificação (ISO-8601)"
    )
    version: str = Field(
        ...,
        description="Versão do serviço"
    )
    components: dict[str, Any] = Field(
        ...,
        description="Status de componentes individuais"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-01-14T15:30:00.000000Z",
                "version": "1.0.0",
                "components": {
                    "vosk_model": {
                        "status": "loaded",
                        "path": "models/vosk-model-small-pt-0.3",
                        "sample_rate": 16000
                    },
                    "glossa_service": {
                        "status": "reachable",
                        "url": "http://localhost:9000/traduzir"
                    }
                }
            }
        }
