"""
Configuração do Microsserviço STT

Centraliza variáveis de ambiente e configurações do sistema.
Valores padrão para desenvolvimento local; use variáveis de ambiente para produção.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env', override=False)
from pathlib import Path
from typing import Optional


class ConfiguracaoSTT:
    """Configurações centralizadas do microsserviço STT."""
    

    PORTA_SERVICO: int = int(os.getenv("STT_PORT", "9100"))

    ORIGENS_PERMITIDAS: list[str] = os.getenv(
        "STT_ALLOWED_ORIGINS", 
        "*"
    ).split(",")
    

    URL_SERVICO_GLOSSA: str = os.getenv(
        "GLOSSA_SERVICE_URL",
        "http://127.0.0.1:5000/translate"  # API de tradução PT-BR -> LIBRAS
    )
    

    TIMEOUT_GLOSSA: int = int(os.getenv("GLOSSA_TIMEOUT", "10"))

    CAMINHO_MODELO_VOSK: Optional[str] = os.getenv(
        "VOSK_MODEL_PATH",
        None  # Deve ser fornecido pelo operador
    )
    

    # Taxa de amostragem do áudio (Hz). Fixado em 16kHz para compatibilidade Vosk.
    TAXA_AMOSTRAGEM: int = 16000
    CANAIS_AUDIO: int = 1
    # 8192 bytes ≈ 256ms de áudio em 16kHz mono PCM16
    TAMANHO_BUFFER_AUDIO: int = int(os.getenv("STT_BUFFER_SIZE", "8192"))

    TIMEOUT_INATIVIDADE: int = int(os.getenv("STT_SESSION_TIMEOUT", "300"))
    INTERVALO_EMISSAO_PARCIAL: float = float(os.getenv("STT_PARTIAL_INTERVAL", "0.5"))

    NIVEL_LOG: str = os.getenv("STT_LOG_LEVEL", "INFO")
    DIRETORIO_LOGS: Path = Path(os.getenv("STT_LOG_DIR", "logs"))
    

    ARQUIVO_LOG: str = "stt_service.log"

    VERSAO_SERVICO: str = "1.0.0"
    NOME_SERVICO: str = "STT Microsserviço - Português Brasileiro"
    IDIOMA_ENTRADA: str = "pt-br"
    
    @classmethod
    def validar(cls) -> None:
        """
        Valida configurações críticas.
        
        Levanta exceções se configurações obrigatórias estiverem ausentes
        ou inválidas, garantindo falha rápida (fail-fast) no startup.
        """
        if not cls.CAMINHO_MODELO_VOSK:
            raise ValueError(
                "VOSK_MODEL_PATH não configurado. "
                "Defina a variável de ambiente com o caminho do modelo pt-BR."
            )
        
        caminho_modelo = Path(cls.CAMINHO_MODELO_VOSK)
        if not caminho_modelo.exists():
            raise FileNotFoundError(
                f"Modelo Vosk não encontrado: {cls.CAMINHO_MODELO_VOSK}"
            )
        
        if not caminho_modelo.is_dir():
            raise NotADirectoryError(
                f"Caminho do modelo Vosk deve ser um diretório: {cls.CAMINHO_MODELO_VOSK}"
            )
        
        # Valida taxa de amostragem
        if cls.TAXA_AMOSTRAGEM not in [8000, 16000, 32000, 44100, 48000]:
            raise ValueError(
                f"Taxa de amostragem inválida: {cls.TAXA_AMOSTRAGEM}Hz. "
                "Vosk suporta 8000, 16000, 32000, 44100, 48000 Hz."
            )
        
        # Cria diretório de logs se não existir
        cls.DIRETORIO_LOGS.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def resumo(cls) -> dict:
        """
        Retorna resumo das configurações ativas (para health check).
        """
        return {
            "porta": cls.PORTA_SERVICO,
            "versao": cls.VERSAO_SERVICO,
            "idioma": cls.IDIOMA_ENTRADA,
            "taxa_amostragem": cls.TAXA_AMOSTRAGEM,
            "modelo_vosk": cls.CAMINHO_MODELO_VOSK,
            "url_glossa": cls.URL_SERVICO_GLOSSA,
        }
