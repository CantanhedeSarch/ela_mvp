"""
Script de Inicialização do Microsserviço STT
============================================

Ponto de entrada simplificado para execução do serviço.
Configura logging e inicia servidor Uvicorn.

Uso:
    python run_stt_service.py
"""

import sys
import logging
from pathlib import Path

# Adiciona diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from stt_service.configuracao import ConfiguracaoSTT
from stt_service.gateway_comunicacao import app, configurar_logging


def main():
    """
    Inicializa e executa o microsserviço STT.
    """
    try:
        # Configura logging
        configurar_logging()
        logger = logging.getLogger(__name__)
        
        # Valida configurações antes de iniciar
        logger.info("Validando configurações...")
        ConfiguracaoSTT.validar()
        
        # Exibe resumo de configurações
        resumo = ConfiguracaoSTT.resumo()
        logger.info("=" * 60)
        logger.info("Configurações do Serviço:")
        for chave, valor in resumo.items():
            logger.info(f"  {chave}: {valor}")
        logger.info("=" * 60)
        
        # Inicia servidor Uvicorn
        import uvicorn
        
        logger.info(f"Iniciando servidor na porta {ConfiguracaoSTT.PORTA_SERVICO}...")
        logger.info(f"Documentação disponível em: http://localhost:{ConfiguracaoSTT.PORTA_SERVICO}/docs")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=ConfiguracaoSTT.PORTA_SERVICO,
            log_level=ConfiguracaoSTT.NIVEL_LOG.lower(),
            access_log=True
        )
        
    except ValueError as e:
        print(f"\n❌ Erro de configuração: {e}")
        print("\nVerifique se:")
        print("  1. A variável VOSK_MODEL_PATH está definida")
        print("  2. O modelo Vosk foi baixado e extraído corretamente")
        print("  3. O caminho aponta para o diretório raiz do modelo\n")
        sys.exit(1)
        
    except FileNotFoundError as e:
        print(f"\n❌ Arquivo não encontrado: {e}")
        print("\nBaixe o modelo Vosk de: https://alphacephei.com/vosk/models")
        print("Extrai para: models/vosk-model-small-pt-0.3/\n")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
