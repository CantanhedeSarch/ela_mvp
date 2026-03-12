# Guia Rápido - Microsserviço STT



### 1. Preparar Ambiente

```powershell
# No diretório raiz do projeto
cd stt_service

# Criar ambiente virtual
python -m venv venv_stt
venv_stt\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Baixar Modelo Vosk

**Modelo recomendado para testes:**
- Nome: `vosk-model-small-pt-0.3`
- Link: https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
- Tamanho: 50 MB

**Extrair para:**
```
d:\ela_teste\ela_mvp\models\vosk-model-small-pt-0.3\
```

### 3. Configurar Variáveis de Ambiente

```powershell
# PowerShell
$env:VOSK_MODEL_PATH = "d:\ela_teste\ela_mvp\models\vosk-model-small-pt-0.3"
$env:GLOSSA_SERVICE_URL = "http://localhost:9000/traduzir"
```

### 4. Iniciar Serviço

```powershell
# Opção 1: Script direto
python run_stt_service.py

# Opção 2: Via uvicorn
uvicorn stt_service.gateway_comunicacao:app --host 0.0.0.0 --port 9100
```

### 5. Verificar Funcionamento

```powershell
# Health check
curl http://localhost:9100/health

# Documentação interativa
start http://localhost:9100/docs
```

---

## 🧪 Testar com Cliente WebSocket

### Preparar áudio de teste

Converter qualquer áudio para o formato correto:

```powershell
# Instalar ffmpeg (se não tiver)
# Baixe de: https://ffmpeg.org/download.html

# Converter para PCM mono 16kHz
ffmpeg -i audio_original.mp3 -ar 16000 -ac 1 audio_teste.wav
```

### Executar cliente de teste

```powershell
python test_client.py audio_teste.wav
```

**Saída esperada:**
```
🔌 Conectando a ws://localhost:9100/stt...
✓ Conexão estabelecida

📨 Sessão iniciada:
   Session ID: a1b2c3d4-...
   Language: pt-br
   Sample Rate: 16000Hz
   Version: 1.0.0

📂 Lendo áudio de: audio_teste.wav
📊 Bytes de áudio: 320000
⏱️  Duração aproximada: 10.00s

📡 Enviando 39 chunks de áudio...

💬 Parcial: olá
💬 Parcial: olá como
💬 Parcial: olá como você

✅ Final: olá como você está
   Confiança: 0.92

📤 Dispatch para glossa:
   URL: http://localhost:9000/traduzir
   Status: 200
   Duração: 45.2ms
   Resposta: {'translation': 'OLHAR COMO VOCE ESTAR'}
```

---

## 📁 Estrutura de Arquivos

```
stt_service/
├── __init__.py                  # Inicialização do pacote
├── configuracao.py              # Configurações e variáveis de ambiente
├── esquema_mensagens.py         # Schemas Pydantic (contratos de dados)
├── motor_stt_vosk.py            # Camada de processamento de áudio
├── orquestrador_envio.py        # Camada de decisão e dispatch
├── gateway_comunicacao.py       # Camada de comunicação WebSocket
├── requirements.txt             # Dependências Python
├── run_stt_service.py           # Script de inicialização
├── test_client.py               # Cliente de teste WebSocket
└── README.md                    # Documentação completa
```

---

## 🔧 Variáveis de Ambiente (Todas Opcionais Exceto VOSK_MODEL_PATH)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VOSK_MODEL_PATH` | *(obrigatório)* | Caminho do modelo Vosk pt-BR |
| `GLOSSA_SERVICE_URL` | `http://localhost:9000/traduzir` | URL do serviço de glossa |
| `STT_PORT` | `9100` | Porta do servidor STT |
| `STT_LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |
| `STT_ALLOWED_ORIGINS` | `*` | Origens permitidas para CORS |
| `STT_BUFFER_SIZE` | `8192` | Tamanho do buffer de áudio (bytes) |
| `STT_PARTIAL_INTERVAL` | `0.5` | Intervalo entre emissões parciais (segundos) |

---

## 🐛 Troubleshooting

### Erro: "VOSK_MODEL_PATH não configurado"

**Solução:**
```powershell
$env:VOSK_MODEL_PATH = "caminho\completo\do\modelo"
```

### Erro: "Modelo Vosk não encontrado"

**Verifique:**
1. Caminho está correto
2. Diretório contém subpastas `am/`, `graph/`, `ivector/`, `conf/`
3. Não aponta para o arquivo `.zip`, mas para a pasta extraída

### Erro: "Address already in use"

**Solução:** Porta 9100 já está em uso. Mude a porta:
```powershell
$env:STT_PORT = "9101"
```

### Transcrições vazias ou ruins

**Possíveis causas:**
1. Áudio não está em PCM mono 16kHz → Converter com ffmpeg
2. Modelo muito pequeno → Usar modelo maior (1.6GB)
3. Áudio com muito ruído → Pré-processar áudio

---

## 📊 Logs

Logs são salvos em: `logs/stt_service.log`

**Ver logs em tempo real:**
```powershell
Get-Content logs\stt_service.log -Wait
```

---

## 🚀 Deploy em Produção

### Docker (recomendado)

Criar `Dockerfile` no diretório `stt_service/`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Baixar modelo Vosk (ou montar volume)
RUN mkdir -p models && \
    wget -O /tmp/vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip && \
    unzip /tmp/vosk-model.zip -d models/ && \
    rm /tmp/vosk-model.zip

# Configurar variável de ambiente
ENV VOSK_MODEL_PATH=/app/models/vosk-model-small-pt-0.3

EXPOSE 9100

CMD ["python", "run_stt_service.py"]
```

**Build e Run:**
```powershell
docker build -t stt-service .
docker run -p 9100:9100 -e GLOSSA_SERVICE_URL=http://host.docker.internal:9000/traduzir stt-service
```

---

## 📞 Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações básicas do serviço |
| `/health` | GET | Health check com status de componentes |
| `/stt` | WebSocket | Endpoint de streaming de áudio |
| `/docs` | GET | Documentação Swagger UI |
| `/redoc` | GET | Documentação ReDoc |

---

## 🔗 Links Úteis

- **Modelos Vosk:** https://alphacephei.com/vosk/models
- **Documentação FastAPI:** https://fastapi.tiangolo.com/
- **Documentação WebSocket:** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **FFmpeg Download:** https://ffmpeg.org/download.html

---

**Pronto para usar! 🎉**
