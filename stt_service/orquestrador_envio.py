"""
Orquestrador de Envio - Camada de Decisão
=========================================

Responsável por detectar fronteiras semânticas e despachar
transcrições finais para o serviço de tradução de glossa.

Decisão arquitetural crítica:
Esta camada implementa a lógica de QUANDO enviar transcrições
para tradução, mantendo o motor STT agnóstico ao domínio.

Fundamentação acadêmica:
A separação entre "detectar fim de fala" (motor STT) e "decidir
enviar para tradução" (orquestrador) permite flexibilidade para:
- Filtrar transcrições curtas/irrelevantes
- Implementar debouncing/throttling
- Adicionar pré-processamento (normalização, PII removal)
- Medir latência end-to-end do pipeline

Esta arquitetura desacoplada é o diferencial autoral do trabalho.
"""

import logging
import time
from typing import Optional
import requests
from requests.exceptions import RequestException, Timeout

from .configuracao import ConfiguracaoSTT
from .esquema_mensagens import ResultadoDespachoGlossa


logger = logging.getLogger(__name__)


# ==========================================
# Orquestrador de Envio para Glossa
# ==========================================

class OrquestradorEnvioGlossa:
    """
    Gerencia envio de transcrições finais para o serviço de tradução.
    
    Responsabilidades:
    1. Validar se transcrição deve ser enviada (filtros)
    2. Formatar payload conforme contrato do serviço de glossa
    3. Realizar requisição HTTP POST com timeout
    4. Capturar metadados de performance (latência)
    5. Tratar erros de rede/timeout gracefully
    
    Decisão de design:
    - Envio síncrono (bloqueante) por simplicidade
    - Timeout configurável para evitar travamento
    - Não implementa retry (responsabilidade do cliente)
    - Retorna metadados completos para rastreabilidade
    
    Futuras extensões (fora do escopo inicial):
    - Fila assíncrona para envios não-bloqueantes
    - Circuit breaker para proteção contra falhas
    - Retry com backoff exponencial
    """
    
    def __init__(self, session_id: str):
        """
        Inicializa orquestrador para uma sessão específica.
        
        Args:
            session_id: Identificador da sessão WebSocket
        """
        self.session_id = session_id
        self.logger = logging.getLogger(f"{__name__}.{session_id[:8]}")
        
        # URL do serviço de tradução
        self.url_glossa = ConfiguracaoSTT.URL_SERVICO_GLOSSA
        
        # Timeout para requisições HTTP
        self.timeout = ConfiguracaoSTT.TIMEOUT_GLOSSA
        
        # Estatísticas
        self.total_envios: int = 0
        self.envios_sucesso: int = 0
        self.envios_falha: int = 0
        self.latencia_total_ms: float = 0.0
        
        self.logger.info(
            f"Orquestrador de envio inicializado "
            f"(destino: {self.url_glossa}, timeout: {self.timeout}s)"
        )
    
    def deve_enviar(self, texto: str, confianca: Optional[float] = None) -> bool:
        """
        Decide se transcrição deve ser enviada para tradução.
        
        Args:
            texto: Texto transcrito
            confianca: Score de confiança [0-1], se disponível
        
        Returns:
            True se deve enviar, False caso contrário
        
        Decisão de filtros (configurável):
        - Textos muito curtos (< 3 caracteres) são descartados
        - Textos com confiança muito baixa (< 0.3) são descartados
        - Textos vazios ou só espaços são descartados
        
        Fundamentação:
        Filtros reduzem ruído e carga no serviço de tradução,
        melhorando qualidade geral do pipeline.
        """
        # Filtro: texto vazio ou só espaços
        if not texto or not texto.strip():
            self.logger.debug("Filtrado: texto vazio")
            return False
        
        # Filtro: texto muito curto (possivelmente ruído)
        if len(texto.strip()) < 3:
            self.logger.debug(f"Filtrado: texto curto '{texto}'")
            return False
        
        # Filtro: confiança muito baixa (se disponível)
        if confianca is not None and confianca < 0.3:
            self.logger.debug(
                f"Filtrado: confiança baixa ({confianca:.2f}) para '{texto}'"
            )
            return False
        
        # Passa em todos os filtros
        return True
    
    def enviar_para_glossa(
        self,
        texto: str,
        confianca: Optional[float] = None
    ) -> ResultadoDespachoGlossa:
        """
        Envia transcrição final para o serviço de tradução.
        
        Args:
            texto: Texto transcrito final
            confianca: Score de confiança, se disponível
        
        Returns:
            ResultadoDespachoGlossa com metadados do envio
        
        Decisão de formato:
        Alinhado com estrutura do professional_api.py, enviamos:
        {
            "text": "<transcrição>",
            "metadata": {
                "session_id": "...",
                "confidence": 0.XX,
                "source": "stt_microservice"
            }
        }
        
        Fundamentação:
        Metadados adicionais permitem rastreabilidade end-to-end
        e análises futuras de correlação entre confiança STT e
        qualidade da tradução para glossa.
        """
        self.total_envios += 1
        
        # Verifica se deve enviar (filtros)
        if not self.deve_enviar(texto, confianca):
            self.logger.info("Envio cancelado por filtros de validação")
            return ResultadoDespachoGlossa(
                target_url=self.url_glossa,
                request_sent=False,
                error="Transcrição filtrada (texto muito curto ou confiança baixa)"
            )
        
        # Monta payload
        payload = {
            "text": texto,
            "metadata": {
                "session_id": self.session_id,
                "confidence": confianca,
                "source": "stt_microservice",
                "service_version": ConfiguracaoSTT.VERSAO_SERVICO
            }
        }
        
        if confianca is not None:
            conf_str = f"{confianca:.2f}"
        else:
            conf_str = "N/A"
        self.logger.info(
            f"Enviando transcrição para glossa: '{texto}' (confiança: {conf_str})"
        )
        
        # Realiza requisição HTTP POST
        inicio = time.perf_counter()
        
        try:
            response = requests.post(
                self.url_glossa,
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"STT-Microservice/{ConfiguracaoSTT.VERSAO_SERVICO}",
                    "X-Session-ID": self.session_id
                }
            )
            
            duracao_ms = (time.perf_counter() - inicio) * 1000
            self.latencia_total_ms += duracao_ms
            
            # Sucesso (2xx)
            if 200 <= response.status_code < 300:
                self.envios_sucesso += 1
                
                # Tenta extrair corpo da resposta
                try:
                    response_body = response.json()
                except Exception:
                    response_body = {"raw": response.text[:200]}
                
                self.logger.info(
                    f"✓ Envio bem-sucedido "
                    f"(status: {response.status_code}, latência: {duracao_ms:.1f}ms)"
                )
                
                return ResultadoDespachoGlossa(
                    target_url=self.url_glossa,
                    request_sent=True,
                    response_status=response.status_code,
                    response_body=response_body,
                    duration_ms=duracao_ms,
                    error=None
                )
            
            # Erro HTTP (4xx, 5xx)
            else:
                self.envios_falha += 1
                
                erro_msg = (
                    f"Serviço de glossa retornou erro HTTP {response.status_code}"
                )
                
                self.logger.warning(
                    f"✗ {erro_msg} (latência: {duracao_ms:.1f}ms)"
                )
                
                return ResultadoDespachoGlossa(
                    target_url=self.url_glossa,
                    request_sent=True,
                    response_status=response.status_code,
                    response_body={"error": response.text[:200]},
                    duration_ms=duracao_ms,
                    error=erro_msg
                )
        
        except Timeout:
            self.envios_falha += 1
            duracao_ms = (time.perf_counter() - inicio) * 1000
            
            erro_msg = f"Timeout ao contatar serviço de glossa (>{self.timeout}s)"
            self.logger.error(f"✗ {erro_msg}")
            
            return ResultadoDespachoGlossa(
                target_url=self.url_glossa,
                request_sent=True,
                response_status=None,
                duration_ms=duracao_ms,
                error=erro_msg
            )
        
        except RequestException as e:
            self.envios_falha += 1
            duracao_ms = (time.perf_counter() - inicio) * 1000
            
            erro_msg = f"Erro de rede ao contatar serviço de glossa: {str(e)}"
            self.logger.error(f"✗ {erro_msg}")
            
            return ResultadoDespachoGlossa(
                target_url=self.url_glossa,
                request_sent=False,
                duration_ms=duracao_ms,
                error=erro_msg
            )
        
        except Exception as e:
            self.envios_falha += 1
            
            erro_msg = f"Erro inesperado ao enviar para glossa: {str(e)}"
            self.logger.exception(f"✗ {erro_msg}")
            
            return ResultadoDespachoGlossa(
                target_url=self.url_glossa,
                request_sent=False,
                error=erro_msg
            )
    
    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas de envio para monitoramento.
        """
        taxa_sucesso = (
            (self.envios_sucesso / self.total_envios * 100)
            if self.total_envios > 0
            else 0.0
        )
        
        latencia_media = (
            (self.latencia_total_ms / self.envios_sucesso)
            if self.envios_sucesso > 0
            else 0.0
        )
        
        return {
            "session_id": self.session_id,
            "total_envios": self.total_envios,
            "envios_sucesso": self.envios_sucesso,
            "envios_falha": self.envios_falha,
            "taxa_sucesso_pct": round(taxa_sucesso, 1),
            "latencia_media_ms": round(latencia_media, 1),
            "url_destino": self.url_glossa,
        }
