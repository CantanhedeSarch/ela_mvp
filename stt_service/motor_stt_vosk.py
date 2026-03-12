"""
Motor STT - Camada de Processamento de Áudio

Encapsula a lógica de transcrição de áudio usando Vosk,
isolando dependências de bibliotecas externas e fornecendo
interface simplificada para o gateway de comunicação.
"""

import json
import logging
from typing import Optional, Tuple
from vosk import Model, KaldiRecognizer

from .configuracao import ConfiguracaoSTT


logger = logging.getLogger(__name__)


class CarregadorModeloVosk:
    """Singleton que carrega e mantém o modelo Vosk em memória. Carregamento único para otimizar recursos."""
    
    _instancia_modelo: Optional[Model] = None
    _modelo_carregado: bool = False
    
    @classmethod
    def obter_modelo(cls) -> Model:
        """
        Retorna instância do modelo Vosk, carregando-o se necessário.
        
        Raises:
            ValueError: Se caminho do modelo não estiver configurado
            FileNotFoundError: Se modelo não for encontrado
            Exception: Se ocorrer erro durante carregamento
        """
        if cls._modelo_carregado and cls._instancia_modelo:
            logger.debug("Modelo Vosk já carregado, reutilizando instância")
            return cls._instancia_modelo
        
        logger.info(
            f"Carregando modelo Vosk de: {ConfiguracaoSTT.CAMINHO_MODELO_VOSK}"
        )
        
        try:
            cls._instancia_modelo = Model(ConfiguracaoSTT.CAMINHO_MODELO_VOSK)
            cls._modelo_carregado = True
            
            logger.info(
                f"✓ Modelo Vosk carregado com sucesso "
                f"(taxa: {ConfiguracaoSTT.TAXA_AMOSTRAGEM}Hz)"
            )
            
            return cls._instancia_modelo
            
        except Exception as e:
            logger.error(f"✗ Falha ao carregar modelo Vosk: {e}")
            raise
    
    @classmethod
    def modelo_esta_carregado(cls) -> bool:
        """Verifica se o modelo já foi carregado."""
        return cls._modelo_carregado and cls._instancia_modelo is not None


class MotorSTTVosk:
    """
    Processa áudio em streaming e gera transcrições incrementais.

    Conceitos Vosk:
    - Partial result: transcrição intermediária (pode mudar)
    - Final result: transcrição estável (fim de frase/pausa)
    - AcceptWaveform: alimenta áudio e retorna se detectou fronteira (fim de frase)
    """
    
    def __init__(self, session_id: str):
        """
        Inicializa motor para uma sessão específica.
        
        Args:
            session_id: Identificador único da sessão WebSocket
        """
        self.session_id = session_id
        self.logger = logging.getLogger(f"{__name__}.{session_id[:8]}")
        
        # Carrega modelo (singleton)
        modelo = CarregadorModeloVosk.obter_modelo()
        
        # Cria reconhecedor específico para esta sessão
        self.recognizer = KaldiRecognizer(
            modelo,
            ConfiguracaoSTT.TAXA_AMOSTRAGEM
        )
        
        self.recognizer.SetWords(True)  # Habilita timestamps por palavra
        
        self.logger.info(
            f"Motor STT inicializado para sessão {session_id[:8]} "
            f"(taxa: {ConfiguracaoSTT.TAXA_AMOSTRAGEM}Hz)"
        )
        
        # Estatísticas da sessão
        self.bytes_processados: int = 0
        self.transcricoes_parciais: int = 0
        self.transcricoes_finais: int = 0
    
    def processar_audio(self, audio_bytes: bytes) -> Tuple[bool, str, Optional[float]]:
        """
        Processa chunk de áudio e retorna resultado.
        
        Args:
            audio_bytes: Bytes de áudio PCM mono 16kHz (little-endian)
        
        Returns:
            Tupla (is_final, texto, confianca):
            - is_final: True se detectou fim de frase/pausa
            - texto: Transcrição parcial ou final
            - confianca: Score de confiança [0-1], se disponível
        
        Vosk retorna JSON com estrutura:
        - Partial: {"partial": "texto..."}
        - Final: {"text": "texto...", "result": [...palavras...]}
        """
        self.bytes_processados += len(audio_bytes)

        # AcceptWaveform retorna True quando detecta fronteira (fim de frase)
        detectou_fronteira = self.recognizer.AcceptWaveform(audio_bytes)
        
        if detectou_fronteira:
            # Resultado final: fim de frase/pausa detectada
            resultado_json = self.recognizer.Result()
            resultado = json.loads(resultado_json)
            
            texto = resultado.get("text", "").strip()
            confianca = self._calcular_confianca_media(resultado)
            
            if texto:  # Ignora finais vazios
                self.transcricoes_finais += 1
                if confianca is not None:
                    conf_str = f"{confianca:.2f}"
                else:
                    conf_str = "N/A"
                self.logger.debug(
                    f"Transcrição final #{self.transcricoes_finais}: '{texto}' (confiança: {conf_str})"
                )
                return True, texto, confianca
            else:
                # Final vazio, continua aguardando
                return False, "", None
        
        else:
            # Resultado parcial: transcrição intermediária
            resultado_json = self.recognizer.PartialResult()
            resultado = json.loads(resultado_json)
            
            texto = resultado.get("partial", "").strip()
            
            if texto:
                self.transcricoes_parciais += 1
                # Log menos verboso para parciais (podem ser frequentes)
                if self.transcricoes_parciais % 10 == 0:
                    self.logger.debug(
                        f"Transcrição parcial #{self.transcricoes_parciais}: "
                        f"'{texto[:50]}...'"
                    )
                return False, texto, None
            else:
                return False, "", None
    
    def finalizar_sessao(self) -> Optional[Tuple[str, Optional[float]]]:
        """
        Força finalização e retorna última transcrição disponível.
        
        Útil quando a sessão WebSocket é encerrada abruptamente
        e ainda há áudio no buffer do reconhecedor.
        
        Returns:
            Tupla (texto, confianca) ou None se buffer vazio
        """
        resultado_json = self.recognizer.FinalResult()
        resultado = json.loads(resultado_json)
        
        texto = resultado.get("text", "").strip()
        confianca = self._calcular_confianca_media(resultado)
        
        if texto:
            self.logger.info(
                f"Finalização forçada da sessão: "
                f"'{texto}' (confiança: {confianca:.2f if confianca else 'N/A'})"
            )
            return texto, confianca
        
        return None
    
    def _calcular_confianca_media(self, resultado: dict) -> Optional[float]:
        """
        Calcula confiança média baseada nos resultados detalhados do Vosk.
        
        Vosk retorna array "result" com objetos:
        [{"word": "olá", "start": 0.5, "end": 0.8, "conf": 0.95}, ...]
        
        Calculamos média ponderada por duração das palavras.
        """
        palavras_detalhadas = resultado.get("result", [])
        
        if not palavras_detalhadas:
            return None
        
        soma_confianca = 0.0
        soma_duracao = 0.0
        
        for palavra in palavras_detalhadas:
            confianca = palavra.get("conf", 0.0)
            inicio = palavra.get("start", 0.0)
            fim = palavra.get("end", 0.0)
            duracao = fim - inicio
            
            if duracao > 0:
                soma_confianca += confianca * duracao
                soma_duracao += duracao
        
        if soma_duracao > 0:
            return soma_confianca / soma_duracao
        
        # Fallback: média simples se duração não disponível
        return sum(p.get("conf", 0.0) for p in palavras_detalhadas) / len(palavras_detalhadas)
    
    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas da sessão para logging/monitoramento.
        """
        return {
            "session_id": self.session_id,
            "bytes_processados": self.bytes_processados,
            "transcricoes_parciais": self.transcricoes_parciais,
            "transcricoes_finais": self.transcricoes_finais,
            "mb_processados": round(self.bytes_processados / 1024 / 1024, 2),
        }
