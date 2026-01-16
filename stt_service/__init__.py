"""
Microsserviço STT - Speech-to-Text em Tempo Real
=================================================

Arquitetura modular para transcrição incremental de fala em português brasileiro,
com separação clara entre camadas de comunicação, processamento e orquestração.

Módulos:
- gateway_comunicacao: Camada de comunicação WebSocket (FastAPI)
- motor_stt_vosk: Camada de processamento de áudio (Vosk pt-BR)
- orquestrador_envio: Camada de decisão de envio (detecção de fronteira)
- esquema_mensagens: Schemas e contratos de dados (Pydantic)
- configuracao: Configurações e variáveis de ambiente

Objetivo acadêmico:
Demonstrar desacoplamento entre STT e tradução para glossa,
utilizando representação textual intermediária e streaming incremental.
"""

__version__ = "1.0.0"
__author__ = "ELA MVP - Projeto Acadêmico"
