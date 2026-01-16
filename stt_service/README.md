# Microsserviço STT - Speech-to-Text em Tempo Real

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688.svg)](https://fastapi.tiangolo.com/)
[![Vosk](https://img.shields.io/badge/Vosk-0.3.45-orange.svg)](https://alphacephei.com/vosk/)
[![License](https://img.shields.io/badge/license-Academic-green.svg)]()

## 📚 Contexto Acadêmico

Este microsserviço faz parte de um **trabalho acadêmico de pesquisa** focado em acessibilidade e tradução automática de fala em português brasileiro para glossa (representação textual de Libras).

### Contribuição Original

A originalidade do trabalho está na **arquitetura desacoplada** proposta, que implementa:

1. **Separação clara entre STT e tradução para glossa**
   - O motor STT é agnóstico ao domínio de acessibilidade
   - A decisão de "quando traduzir" é responsabilidade de uma camada específica
   
2. **Representação textual intermediária**
   - Transcrição em português como formato pivot
   - Permite análise, filtragem e pré-processamento antes da tradução
   
3. **Processamento incremental com fronteiras semânticas**
   - Emissão de resultados parciais para feedback em tempo real
   - Envio para tradução apenas após detecção de fim de fala
   
4. **Aplicação de microsserviços em cenários de acessibilidade**
   - Escalabilidade independente de componentes
   - Facilita testes A/B de diferentes motores STT ou tradutores

---

## 🏗️ Arquitetura

### Visão Geral

```
┌─────────────┐      WebSocket       ┌──────────────────────┐
│   Cliente   │◄────────────────────►│ Gateway Comunicação  │
│  (Browser)  │   Áudio PCM 16kHz    │    (FastAPI)         │
└─────────────┘                       └──────────┬───────────┘
                                                 │
                                                 ▼
                                      ┌──────────────────────┐
                                      │    Motor STT Vosk    │
                                      │  (Processamento de   │
                                      │       Áudio)         │
                                      └──────────┬───────────┘
                                                 │
                                      ┌──────────▼───────────┐
                                      │  Orquestrador Envio  │
                                      │ (Decisão + Dispatch) │
                                      └──────────┬───────────┘
                                                 │ HTTP POST
                                                 ▼
                                      ┌──────────────────────┐
                                      │  Serviço de Glossa   │
                                      │   (Tradução pt-BR    │
                                      │    → Glossa)         │
                                      └──────────────────────┘
```

### Camadas e Responsabilidades

| Camada | Módulo | Responsabilidade |
|--------|--------|------------------|
| **Comunicação** | `gateway_comunicacao.py` | Gerenciar WebSocket, validar protocolo, emitir mensagens JSON |
| **Processamento** | `motor_stt_vosk.py` | Processar áudio PCM, gerar transcrições incrementais via Vosk |
| **Orquestração** | `orquestrador_envio.py` | Decidir quando enviar, despachar para serviço de glossa |
| **Contratos** | `esquema_mensagens.py` | Definir schemas Pydantic, validar dados, timestamps ISO-8601 |
| **Configuração** | `configuracao.py` | Centralizar settings, validar ambiente, fail-fast |

### Princípios de Design

- **Baixo Acoplamento**: Cada camada pode ser substituída independentemente
- **Alta Coesão**: Responsabilidades bem definidas por módulo
- **Fail-Fast**: Validação de configurações no startup
- **Rastreabilidade**: Logs estruturados e metadados em todas as mensagens

---

## 🔄 Fluxo de Dados

### 1. Estabelecimento de Sessão

```json
// Cliente conecta via WebSocket
ws://localhost:9100/stt

// Servidor responde
{
  "type": "session_started",
  "session_id": "a1b2c3d4-...",
  "language": "pt-br",
  "sample_rate": 16000,
  "channels": 1,
  "timestamp": "2026-01-14T15:30:45.123456Z",
  "version": "1.0.0"
}
```

### 2. Streaming de Áudio

```
Cliente → Servidor: bytes de áudio PCM mono 16kHz (frames contínuos)
```

### 3. Transcrições Parciais

```json
// Emitidas durante a fala (throttled a cada 0.5s)
{
  "type": "partial",
  "session_id": "a1b2c3d4-...",
  "text": "olá como você est",
  "confidence": 0.85,
  "timestamp": "2026-01-14T15:30:46.500000Z"
}
```

### 4. Transcrição Final + Dispatch

```json
// Emitida após detecção de fronteira (pausa/fim de frase)
{
  "type": "final",
  "session_id": "a1b2c3d4-...",
  "text": "olá como você está",
  "confidence": 0.92,
  "timestamp": "2026-01-14T15:30:47.800000Z",
  "dispatch": {
    "target_url": "http://localhost:9000/traduzir",
    "request_sent": true,
    "response_status": 200,
    "response_body": {
      "translation": "OLHAR COMO VOCE ESTAR"
    },
    "duration_ms": 45.2,
    "error": null
  }
}
```

### 5. Tratamento de Erros

```json
{
  "type": "error",
  "session_id": "a1b2c3d4-...",
  "error_code": "AUDIO_FORMAT_INVALID",
  "error_message": "Taxa de amostragem incompatível. Esperado: 16000Hz",
  "details": {"received_rate": 44100},
  "timestamp": "2026-01-14T15:30:48.000000Z"
}
```

---

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.10 ou superior
- Windows 10/11 (testado)
- Modelo Vosk pt-BR (download necessário)

### Passo 1: Clonar/Copiar Código

```bash
cd stt_service/
```

### Passo 2: Criar Ambiente Virtual

```powershell
python -m venv venv_stt
venv_stt\Scripts\activate
```

### Passo 3: Instalar Dependências

```powershell
pip install -r requirements.txt
```

### Passo 4: Baixar Modelo Vosk

Acesse: https://alphacephei.com/vosk/models

**Opções recomendadas:**

| Modelo | Tamanho | Precisão | Uso Recomendado |
|--------|---------|----------|-----------------|
| `vosk-model-small-pt-0.3` | 50 MB | Boa | Desenvolvimento, testes rápidos |
| `vosk-model-pt-fb-v0.1.1-20220516_2113` | 1.6 GB | Excelente | Produção, avaliação científica |

**Extrair para:**

```
models/
  └── vosk-model-small-pt-0.3/
      ├── am/
      ├── graph/
      ├── ivector/
      └── conf/
```

### Passo 5: Configurar Variáveis de Ambiente

```powershell
# Caminho do modelo Vosk (OBRIGATÓRIO)
$env:VOSK_MODEL_PATH = "models/vosk-model-small-pt-0.3"

# URL do serviço de glossa (opcional, padrão: http://localhost:9000/traduzir)
$env:GLOSSA_SERVICE_URL = "http://localhost:9000/traduzir"

# Porta do serviço STT (opcional, padrão: 9100)
$env:STT_PORT = "9100"

# Nível de log (opcional, padrão: INFO)
$env:STT_LOG_LEVEL = "DEBUG"
```

### Passo 6: Executar Serviço

**Opção 1: Direto via Python**

```powershell
python -m stt_service.gateway_comunicacao
```

**Opção 2: Via Uvicorn (recomendado)**

```powershell
uvicorn stt_service.gateway_comunicacao:app --host 0.0.0.0 --port 9100 --log-level info
```

### Passo 7: Verificar Saúde

```powershell
curl http://localhost:9100/health
```

Resposta esperada:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T15:30:00.000000Z",
  "version": "1.0.0",
  "components": {
    "api": {"status": "healthy", "porta": 9100},
    "vosk_model": {
      "status": "loaded",
      "path": "models/vosk-model-small-pt-0.3",
      "sample_rate": 16000,
      "language": "pt-br"
    }
  }
}
```

---

## 📊 Avaliação Experimental

### Métricas Propostas

Esta arquitetura foi projetada para facilitar medições experimentais em artigos científicos:

#### 1. **Latência End-to-End**

Medir tempo desde recepção do áudio até emissão da transcrição final:

```
Latência Total = T(recepção_audio) → T(emissão_final)
```

**Coleta:**
- Logs de cada sessão incluem timestamps ISO-8601 em todas as mensagens
- Campo `dispatch.duration_ms` captura latência do POST para glossa

#### 2. **Acurácia da Transcrição (WER - Word Error Rate)**

Comparar transcrições com referência gold-standard:

```
WER = (S + D + I) / N
S = substituições, D = deleções, I = inserções, N = palavras totais
```

**Coleta:**
- Gravar áudios de teste com transcrições conhecidas
- Processar via STT e comparar campo `text` da mensagem final

#### 3. **Taxa de Sucesso do Dispatch**

Avaliar confiabilidade da integração com serviço de glossa:

```
Taxa_Sucesso = (envios_sucesso / total_envios) × 100
```

**Coleta:**
- Estatísticas disponíveis via `OrquestradorEnvioGlossa.obter_estatisticas()`
- Logs incluem status HTTP e erros de cada tentativa

#### 4. **Throughput de Áudio**

Medir volume de áudio processado:

```
Throughput = bytes_processados / tempo_sessao (MB/s)
```

**Coleta:**
- Campo `bytes_processados` em `MotorSTTVosk.obter_estatisticas()`

#### 5. **Confiança Média das Transcrições**

Avaliar qualidade percebida pelo modelo:

```
Confiança_Média = Σ(confidence) / total_transcricoes_finais
```

**Coleta:**
- Campo `confidence` em mensagens `final`
- Agregado por sessão ou dataset completo

### Experimentos Sugeridos

#### Experimento 1: Comparação de Modelos Vosk

**Objetivo:** Avaliar trade-off tamanho × precisão

**Variáveis:**
- Modelo small (50MB) vs. modelo large (1.6GB)
- Mesmos áudios de teste

**Métricas:** WER, latência, throughput

---

#### Experimento 2: Impacto de Ruído de Fundo

**Objetivo:** Testar robustez em condições reais

**Variáveis:**
- Áudios limpos vs. com ruído (SNR 20dB, 10dB, 5dB)

**Métricas:** WER, confiança média, taxa de transcrições vazias

---

#### Experimento 3: Latência de Integração

**Objetivo:** Identificar gargalos no pipeline

**Análise:**
- Latência STT puro (sem dispatch)
- Latência do POST para glossa (`dispatch.duration_ms`)
- Latência total end-to-end

**Métricas:** Percentis P50, P95, P99

---

## 🛠️ Desenvolvimento e Extensões

### Substituindo o Motor STT

Para trocar Vosk por outro motor (ex: Whisper streaming):

1. Criar novo módulo `motor_stt_whisper.py`
2. Implementar mesma interface:
   ```python
   def processar_audio(audio_bytes) -> Tuple[bool, str, Optional[float]]
   ```
3. Atualizar import em `gateway_comunicacao.py`

**Não há necessidade de modificar:**
- Camada de comunicação (WebSocket)
- Orquestrador de envio
- Schemas de mensagens

---

### Adicionando Pré-processamento

Para normalizar texto antes de enviar para glossa:

```python
# Em orquestrador_envio.py, método enviar_para_glossa()

texto_normalizado = self._normalizar_texto(texto)
payload = {"text": texto_normalizado, ...}
```

Exemplos de normalização:
- Remover pontuação excessiva
- Expandir abreviações
- Converter números por extenso

---

### Implementando Autenticação

Para proteger o WebSocket:

```python
# Em gateway_comunicacao.py

@app.websocket("/stt")
async def websocket_stt(websocket: WebSocket, token: str = Query(...)):
    if not validar_token(token):
        await websocket.close(code=4001, reason="Unauthorized")
        return
    # ... resto do código
```

---

## 📝 Estrutura de Logs

Logs são salvos em `logs/stt_service.log` com formato estruturado:

```
2026-01-14 15:30:45 - stt_service.motor_stt_vosk.a1b2c3d4 - INFO - Motor STT inicializado
2026-01-14 15:30:46 - stt_service.orquestrador_envio.a1b2c3d4 - INFO - Enviando transcrição para glossa: 'olá'
2026-01-14 15:30:46 - stt_service.orquestrador_envio.a1b2c3d4 - INFO - ✓ Envio bem-sucedido (status: 200, latência: 45.2ms)
```

**Campos relevantes para análise:**
- Timestamp (ISO-8601)
- Módulo e session_id
- Mensagens de início/fim de sessão
- Estatísticas de performance

---

## 🔬 Citação

Se este trabalho for usado em pesquisa acadêmica, sugerimos a seguinte citação:

```
[Autor]. (2026). Arquitetura Desacoplada para Tradução de Fala em Português
para Glossa: Um Microsserviço STT com Processamento Incremental.
[Nome da Instituição/Conferência].
```

---

## 📄 Licença

Este código foi desenvolvido para fins acadêmicos e de pesquisa.

---

## 🤝 Contribuições

Este é um projeto acadêmico autoral. Sugestões e melhorias são bem-vindas, desde que mantenham a clareza arquitetural e rastreabilidade das decisões de design.

---

## 📞 Suporte

Para dúvidas sobre implementação ou extensões:

- **Logs:** Verifique `logs/stt_service.log`
- **Health Check:** `GET /health`
- **Documentação Interativa:** `http://localhost:9100/docs` (Swagger UI)

---

## 🔍 Referências

- **Vosk Speech Recognition:** https://alphacephei.com/vosk/
- **FastAPI Framework:** https://fastapi.tiangolo.com/
- **WebSocket Protocol:** https://datatracker.ietf.org/doc/html/rfc6455
- **ISO 8601 Timestamps:** https://www.iso.org/iso-8601-date-and-time-format.html

---

**Desenvolvido com foco em clareza arquitetural e reprodutibilidade científica.**
