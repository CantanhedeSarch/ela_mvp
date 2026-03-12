# ELA MVP — Documentação de Integração Mobile

**Destinatário:** Mirella (desenvolvedora responsável pela integração mobile)
**Versão do sistema:** MVP v4.0 (API de tradução) + STT Microsserviço v1.0.0
**Data:** Março de 2026

---

## Visão Geral

O ELA MVP é um sistema de tradução de **Português Brasileiro (PT-BR) para LIBRAS** (em formato Gloss). A aplicação é composta por dois serviços independentes que podem ser usados juntos ou separadamente:

| Serviço | Tecnologia | Porta padrão | Uso |
|---|---|---|---|
| **API de Tradução** | Flask (REST HTTP) | `5000` | Traduz texto PT-BR → Gloss LIBRAS |
| **Serviço STT** | FastAPI (WebSocket) | `9100` | Transcreve fala em tempo real e encaminha para tradução |

**Fluxo completo:**
```
Microfone (mobile) → WebSocket → STT (Vosk) → HTTP POST → API de Tradução → Gloss LIBRAS
```

**Fluxo simplificado (só tradução de texto):**
```
Campo de texto (mobile) → HTTP POST → API de Tradução → Gloss LIBRAS
```

---

## 1. API de Tradução (REST)

### Iniciar o serviço

```powershell
# No diretório raiz do projeto
ela_env\Scripts\activate
python api_simples.py
```

O serviço estará disponível em `http://127.0.0.1:5000`.

### Endpoints

#### `GET /`
Retorna informações básicas e exemplos de uso.

**Resposta:**
```json
{
  "name": "ELA MVP - Tradutor PT-BR → LIBRAS",
  "version": "4.0",
  "status": "online",
  "examples": [
    {"input": "quero agua", "output": "QUERER AGUA"}
  ],
  "usage": "POST /translate com {\"text\": \"sua frase\"}"
}
```

#### `POST /translate`
Traduz um texto PT-BR para Gloss LIBRAS.

**Request:**
```http
POST /translate
Content-Type: application/json

{
  "text": "quero água"
}
```

**Response de sucesso (`200`):**
```json
{
  "success": true,
  "input": "quero água",
  "output": "QUERER ÁGUA",
  "method": "word_mapping",
  "confidence": 0.95
}
```

**Response de erro (`400`):**
```json
{
  "error": "Campo 'text' obrigatório"
}
```

**Response quando serviço indisponível (`503`):**
```json
{
  "error": "Tradutor indisponível"
}
```

**Campo `method`** indica como a tradução foi feita:
- `phrase_mapping` — frase completa encontrada no dicionário (maior confiança)
- `word_mapping` — tradução palavra a palavra
- `error` — falha no processamento

**Campo `confidence`** varia de `0.0` a `1.0`. Valor `0.95` indica frase encontrada diretamente no dicionário.

### Exemplo de integração mobile (Kotlin/Android)

```kotlin
suspend fun traduzirTexto(texto: String): String {
    val client = OkHttpClient()
    val json = JSONObject().put("text", texto).toString()
    val body = json.toRequestBody("application/json".toMediaType())
    val request = Request.Builder()
        .url("http://<IP_DO_SERVIDOR>:5000/translate")
        .post(body)
        .build()

    val response = client.newCall(request).execute()
    val respJson = JSONObject(response.body!!.string())
    return respJson.getString("output")
}
```

### Exemplo de integração mobile (Swift/iOS)

```swift
func traduzirTexto(_ texto: String, completion: @escaping (String?) -> Void) {
    guard let url = URL(string: "http://<IP_DO_SERVIDOR>:5000/translate") else { return }
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try? JSONSerialization.data(withJSONObject: ["text": texto])

    URLSession.shared.dataTask(with: request) { data, _, _ in
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let output = json["output"] as? String else {
            completion(nil); return
        }
        completion(output)
    }.resume()
}
```

---

## 2. Serviço STT — Transcrição de Fala em Tempo Real

### Iniciar o serviço

```powershell
# No diretório raiz do projeto
ela_env\Scripts\activate

# Definir o caminho do modelo Vosk (obrigatório)
$env:VOSK_MODEL_PATH = "models/vosk-model-small-pt-0.3"

python run_stt_service.py
```

O serviço estará disponível em `ws://0.0.0.0:9100`.

> **Importante:** O modelo Vosk deve estar na pasta `models/`. O modelo usado em desenvolvimento é `vosk-model-small-pt-0.3` (pt-BR). Não commitar o modelo no repositório — baixar em https://alphacephei.com/vosk/models.

### Variáveis de ambiente disponíveis

| Variável | Padrão | Descrição |
|---|---|---|
| `VOSK_MODEL_PATH` | — | **(Obrigatório)** Caminho para o modelo Vosk pt-BR |
| `STT_PORT` | `9100` | Porta do serviço STT |
| `GLOSSA_SERVICE_URL` | `http://127.0.0.1:5000/translate` | URL da API de tradução |
| `GLOSSA_TIMEOUT` | `10` | Timeout em segundos para chamar a API de tradução |
| `STT_LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `STT_PARTIAL_INTERVAL` | `0.5` | Intervalo mínimo (segundos) entre emissões de transcrições parciais |
| `STT_SESSION_TIMEOUT` | `300` | Tempo máximo de inatividade por sessão (segundos) |

### Protocolo WebSocket

O mobile deve se conectar ao endpoint `ws://<IP_DO_SERVIDOR>:9100/stt`.

#### Fluxo de comunicação

```
Mobile                          Servidor STT
  |                                  |
  |──── connect ──────────────────>  |
  |  <── session_started ──────────  |  (JSON com session_id e configurações)
  |                                  |
  |──── audio bytes (PCM) ────────>  |  (binário contínuo)
  |──── audio bytes (PCM) ────────>  |
  |  <── partial ──────────────────  |  (JSON — transcrição intermediária)
  |──── audio bytes (PCM) ────────>  |
  |  <── final ────────────────────  |  (JSON — transcrição final + tradução LIBRAS)
  |                                  |
  |──── close ─────────────────────> |
```

#### Formato do áudio esperado

| Propriedade | Valor |
|---|---|
| Formato | PCM bruto (sem cabeçalho WAV) |
| Taxa de amostragem | **16.000 Hz** |
| Canais | **Mono (1 canal)** |
| Bits por amostra | 16 bits (little-endian) |
| Tamanho do chunk recomendado | 8192 bytes (~256ms) |

> **Atenção:** Enviar áudio em qualquer outro formato vai produzir transcrições incorretas ou vazias. A conversão deve ser feita no mobile antes de enviar.

#### Mensagens recebidas do servidor

**`session_started`** — enviada logo após a conexão:
```json
{
  "type": "session_started",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "language": "pt-br",
  "sample_rate": 16000,
  "channels": 1,
  "version": "1.0.0",
  "timestamp": "2026-03-12T14:00:00.000000Z"
}
```

**`partial`** — transcrição intermediária (pode mudar enquanto o usuário fala):
```json
{
  "type": "partial",
  "session_id": "a1b2c3d4-...",
  "text": "quero água",
  "confidence": null,
  "timestamp": "2026-03-12T14:00:01.500000Z"
}
```

**`final`** — transcrição finalizada + resultado da tradução para LIBRAS:
```json
{
  "type": "final",
  "session_id": "a1b2c3d4-...",
  "text": "quero água",
  "confidence": 0.91,
  "timestamp": "2026-03-12T14:00:02.000000Z",
  "dispatch": {
    "target_url": "http://127.0.0.1:5000/translate",
    "request_sent": true,
    "response_status": 200,
    "response_body": {
      "success": true,
      "input": "quero água",
      "output": "QUERER ÁGUA",
      "method": "word_mapping",
      "confidence": 0.95
    },
    "duration_ms": 12.3,
    "error": null
  }
}
```

> O campo `dispatch.response_body.output` contém a tradução em Gloss LIBRAS que deve ser exibida na tela.

**`error`** — notificação de erro:
```json
{
  "type": "error",
  "session_id": "a1b2c3d4-...",
  "error_code": "PROCESSING_ERROR",
  "error_message": "Descrição do erro",
  "timestamp": "2026-03-12T14:00:03.000000Z"
}
```

#### Filtros automáticos do serviço STT

O servidor **não envia** para tradução transcrições que:
- São vazias ou contêm apenas espaços
- Têm menos de 3 caracteres
- Têm confiança inferior a 0.30 (quando disponível)

Nestes casos, `dispatch.request_sent` será `false` e `dispatch.error` conterá a razão.

### Exemplo de integração WebSocket (Android/Kotlin)

```kotlin
class STTIntegration {
    private lateinit var webSocket: WebSocket
    private val client = OkHttpClient()

    fun conectar(serverIp: String, onGloss: (String) -> Unit) {
        val request = Request.Builder()
            .url("ws://$serverIp:9100/stt")
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                val json = JSONObject(text)
                when (json.getString("type")) {
                    "final" -> {
                        val gloss = json
                            .optJSONObject("dispatch")
                            ?.optJSONObject("response_body")
                            ?.optString("output") ?: return
                        runOnUiThread { onGloss(gloss) }
                    }
                    "error" -> Log.e("STT", json.getString("error_message"))
                }
            }
        })
    }

    // Chamar em loop com chunks de áudio PCM 16kHz mono 16bit
    fun enviarAudio(pcmBytes: ByteArray) {
        webSocket.send(pcmBytes.toByteString())
    }

    fun desconectar() {
        webSocket.close(1000, "Sessão encerrada")
    }
}
```

### Exemplo de integração WebSocket (iOS/Swift)

```swift
import Foundation

class STTIntegration: NSObject, URLSessionWebSocketDelegate {
    private var webSocketTask: URLSessionWebSocketTask?
    var onGloss: ((String) -> Void)?

    func conectar(serverIp: String) {
        let url = URL(string: "ws://\(serverIp):9100/stt")!
        let session = URLSession(configuration: .default, delegate: self, delegateQueue: nil)
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        receberMensagens()
    }

    private func receberMensagens() {
        webSocketTask?.receive { [weak self] result in
            guard case .success(let message) = result,
                  case .string(let text) = message,
                  let data = text.data(using: .utf8),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  json["type"] as? String == "final",
                  let dispatch = json["dispatch"] as? [String: Any],
                  let body = dispatch["response_body"] as? [String: Any],
                  let output = body["output"] as? String else {
                self?.receberMensagens(); return
            }
            DispatchQueue.main.async { self?.onGloss?(output) }
            self?.receberMensagens()
        }
    }

    // Chamar em loop com chunks de áudio PCM 16kHz mono 16bit
    func enviarAudio(_ pcmBytes: Data) {
        let message = URLSessionWebSocketTask.Message.data(pcmBytes)
        webSocketTask?.send(message) { _ in }
    }

    func desconectar() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
    }
}
```

---

## 3. Captura de Áudio no Mobile

Para alimentar o STT corretamente, o mobile precisa capturar áudio no formato correto (PCM 16kHz mono 16-bit).

### Android (AudioRecord)

```kotlin
val sampleRate = 16000
val bufferSize = AudioRecord.getMinBufferSize(
    sampleRate,
    AudioFormat.CHANNEL_IN_MONO,
    AudioFormat.ENCODING_PCM_16BIT
)

val recorder = AudioRecord(
    MediaRecorder.AudioSource.MIC,
    sampleRate,
    AudioFormat.CHANNEL_IN_MONO,
    AudioFormat.ENCODING_PCM_16BIT,
    bufferSize
)

recorder.startRecording()

// Em uma coroutine/thread de I/O:
val buffer = ByteArray(8192)
while (gravando) {
    val bytesLidos = recorder.read(buffer, 0, buffer.size)
    if (bytesLidos > 0) {
        sttIntegration.enviarAudio(buffer.copyOf(bytesLidos))
    }
}
```

### iOS (AVAudioEngine)

```swift
let engine = AVAudioEngine()
let inputNode = engine.inputNode
// Formato necessário: 16kHz, mono, PCM
let format = AVAudioFormat(
    commonFormat: .pcmFormatInt16,
    sampleRate: 16000,
    channels: 1,
    interleaved: true
)!

inputNode.installTap(onBus: 0, bufferSize: 8192, format: format) { buffer, _ in
    guard let channelData = buffer.int16ChannelData else { return }
    let frameLength = Int(buffer.frameLength)
    let data = Data(bytes: channelData[0], count: frameLength * 2)
    sttIntegration.enviarAudio(data)
}

try engine.start()
```

> Se a taxa de amostragem nativa do dispositivo for diferente de 16kHz (comum no iOS que usa 44.1kHz), é necessário fazer **reamostração (resampling)** antes de enviar. Use `AVAudioConverter` no iOS ou `AudioTrack/resampler` no Android.

---

## 4. Monitoramento e Diagnóstico

### Health check do STT

```http
GET http://<IP>:9100/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-12T14:00:00Z",
  "components": {
    "api": {"status": "healthy", "porta": 9100},
    "vosk_model": {"status": "loaded", "sample_rate": 16000, "language": "pt-br"},
    "glossa_service": {"status": "configured", "url": "http://127.0.0.1:5000/translate"}
  }
}
```

`status` pode ser:
- `healthy` — modelo carregado, tudo funcionando
- `degraded` — serviço respondendo mas modelo não carregado

### Documentação interativa (Swagger)

Com o serviço STT rodando, acesse:
- `http://<IP>:9100/docs` — Swagger UI
- `http://<IP>:9100/redoc` — ReDoc

---

## 5. Estrutura do Projeto

```
ela_mvp/
├── api_simples.py           # Servidor Flask — API REST de tradução
├── direct_translator.py     # Motor de tradução PT-BR → Gloss LIBRAS
├── run_stt_service.py       # Entry point para iniciar o STT
├── requirements.txt         # Dependências Python do projeto raiz
├── models/
│   ├── word2vec_libras.model
│   └── vosk-model-small-pt-0.3/   # Modelo de reconhecimento de fala
└── stt_service/
    ├── configuracao.py          # Variáveis de configuração (env vars)
    ├── esquema_mensagens.py     # Schemas Pydantic das mensagens WebSocket
    ├── gateway_comunicacao.py   # FastAPI — servidor WebSocket
    ├── motor_stt_vosk.py        # Wrapper do Vosk para processamento de áudio
    ├── orquestrador_envio.py    # Decide quando e como enviar para tradução
    └── requirements.txt         # Dependências do microsserviço STT
```

### Responsabilidade de cada arquivo relevante

| Arquivo | O que faz |
|---|---|
| `api_simples.py` | Recebe `POST /translate`, executa tradução, retorna Gloss |
| `direct_translator.py` | Contém dicionário PT-BR → Gloss e lógica de tradução |
| `gateway_comunicacao.py` | Aceita conexões WebSocket, gerencia sessões, orquestra pipeline |
| `motor_stt_vosk.py` | Processa bytes de áudio PCM com o Vosk e retorna texto |
| `orquestrador_envio.py` | Recebe transcrição final, filtra, e chama a API de tradução via HTTP |
| `configuracao.py` | Centraliza todas as configurações via variáveis de ambiente |
| `esquema_mensagens.py` | Define os schemas JSON de todas as mensagens WebSocket |

---

## 6. Considerações para Deploy em Produção Mobile

1. **HTTPS / WSS:** Em produção, o mobile deve usar `https://` e `wss://`. Configure um proxy reverso (nginx ou Caddy) com certificado TLS na frente dos serviços Flask/FastAPI.

2. **CORS:** A API Flask já tem CORS habilitado para `*`. Para produção, restrinja `ORIGENS_PERMITIDAS` às origens do seu app.

3. **IP do servidor:** Durante desenvolvimento, use o IP local da máquina na mesma rede Wi-Fi. Evite `127.0.0.1` no mobile — esse endereço aponta para o próprio dispositivo.

4. **Permissões no mobile:**
   - Android: `RECORD_AUDIO` e `INTERNET` no `AndroidManifest.xml`
   - iOS: chave `NSMicrophoneUsageDescription` no `Info.plist`

5. **Reconexão automática:** O serviço STT não reconecta automaticamente. Implemente lógica de retry no mobile com backoff exponencial.

6. **Timeout de sessão:** Sessões WebSocket sem áudio por mais de `300s` (padrão) são encerradas. Envie pings ou reestabeleça a conexão se o usuário pausar o uso.

7. **Latência:** O Vosk roda localmente no servidor, sem chamadas externas. A latência principal é a rede mobile → servidor + chamada HTTP interna ao serviço de tradução (local).

---

## 7. Exemplo de Fluxo de Uso no App

```
1. Usuário abre tela de tradução por voz
2. App conecta ao WebSocket (ws://<servidor>:9100/stt)
3. App recebe "session_started" → exibe "Pronto para ouvir"
4. Usuário pressiona botão para falar
5. App inicia captura de áudio (PCM 16kHz mono) e envia em chunks
6. App recebe mensagens "partial" → exibe texto provisório na tela
7. Usuário termina de falar / faz pausa
8. App recebe mensagem "final" com campo dispatch.response_body.output
9. App exibe a tradução em Gloss LIBRAS (ex: "QUERER ÁGUA")
10. Usuário pode falar de novo (loop a partir do passo 5)
11. Ao sair da tela, app fecha a conexão WebSocket
```

---

## Contato e Referências

- Modelo Vosk pt-BR: https://alphacephei.com/vosk/models
- Documentação Vosk: https://alphacephei.com/vosk/
- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets/
- LIBRAS Gloss: notação textual dos sinais, cada palavra em maiúsculo representa um sinal
