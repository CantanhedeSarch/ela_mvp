"""
Cliente de Teste WebSocket para o Microsserviço STT
===================================================

Script simples para testar conectividade e protocolo do serviço STT.
Envia um arquivo de áudio WAV PCM mono 16kHz via WebSocket e
exibe as transcrições recebidas.

Uso:
    python test_client.py <arquivo_audio.wav>

Requisitos:
    pip install websocket-client pydub
"""

import sys
import json
import asyncio
import websockets
from pathlib import Path


async def testar_stt_service(url: str, arquivo_audio: Path):
    """
    Conecta ao serviço STT e envia áudio para transcrição.
    
    Args:
        url: URL do WebSocket (ex: ws://localhost:9100/stt)
        arquivo_audio: Caminho do arquivo WAV PCM mono 16kHz
    """
    print(f"🔌 Conectando a {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✓ Conexão estabelecida")
            
            # Recebe mensagem de sessão iniciada
            mensagem = await websocket.recv()
            dados = json.loads(mensagem)
            print(f"\n📨 Sessão iniciada:")
            print(f"   Session ID: {dados['session_id']}")
            print(f"   Language: {dados['language']}")
            print(f"   Sample Rate: {dados['sample_rate']}Hz")
            print(f"   Version: {dados['version']}\n")
            
            # Lê arquivo de áudio
            print(f"📂 Lendo áudio de: {arquivo_audio}")
            with open(arquivo_audio, 'rb') as f:
                # Pula header WAV (44 bytes) para obter dados PCM puros
                f.seek(44)
                audio_data = f.read()
            
            print(f"📊 Bytes de áudio: {len(audio_data)}")
            print(f"⏱️  Duração aproximada: {len(audio_data) / (16000 * 2):.2f}s")
            
            # Envia áudio em chunks de 8192 bytes (configuração do serviço)
            chunk_size = 8192
            total_chunks = len(audio_data) // chunk_size
            
            print(f"\n📡 Enviando {total_chunks} chunks de áudio...\n")
            
            # Task para receber mensagens do servidor
            async def receber_mensagens():
                while True:
                    try:
                        mensagem = await websocket.recv()
                        dados = json.loads(mensagem)
                        
                        tipo = dados.get('type')
                        
                        if tipo == 'partial':
                            print(f"💬 Parcial: {dados['text']}")
                        
                        elif tipo == 'final':
                            print(f"\n✅ Final: {dados['text']}")
                            print(f"   Confiança: {dados.get('confidence', 'N/A')}")
                            
                            # Exibe resultado do dispatch
                            dispatch = dados.get('dispatch')
                            if dispatch:
                                print(f"\n📤 Dispatch para glossa:")
                                print(f"   URL: {dispatch['target_url']}")
                                print(f"   Status: {dispatch['response_status']}")
                                print(f"   Duração: {dispatch['duration_ms']:.1f}ms")
                                if dispatch.get('response_body'):
                                    print(f"   Resposta: {dispatch['response_body']}")
                        
                        elif tipo == 'error':
                            print(f"\n❌ Erro: {dados['error_message']}")
                            print(f"   Código: {dados['error_code']}")
                    
                    except websockets.exceptions.ConnectionClosed:
                        break
            
            # Task para enviar áudio
            async def enviar_audio():
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await websocket.send(chunk)
                    
                    # Pequena pausa para simular streaming real
                    await asyncio.sleep(0.1)
                
                print("\n✓ Áudio enviado completamente")
                
                # Aguarda um pouco para receber últimas mensagens
                await asyncio.sleep(2)
            
            # Executa envio e recepção em paralelo
            await asyncio.gather(
                enviar_audio(),
                receber_mensagens()
            )
    
    except ConnectionRefusedError:
        print(f"\n❌ Erro: Não foi possível conectar a {url}")
        print("   Verifique se o serviço STT está rodando.")
    
    except FileNotFoundError:
        print(f"\n❌ Erro: Arquivo não encontrado: {arquivo_audio}")
    
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Ponto de entrada do script.
    """
    if len(sys.argv) < 2:
        print("Uso: python test_client.py <arquivo_audio.wav>")
        print("\nO arquivo deve ser WAV PCM mono 16kHz")
        print("Você pode converter com: ffmpeg -i input.wav -ar 16000 -ac 1 output.wav")
        sys.exit(1)
    
    arquivo_audio = Path(sys.argv[1])
    url = "ws://localhost:9100/stt"
    
    print("=" * 60)
    print("Cliente de Teste - Microsserviço STT")
    print("=" * 60)
    
    asyncio.run(testar_stt_service(url, arquivo_audio))


if __name__ == "__main__":
    main()
