#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Final - Sistema de Tradução PT-BR → LIBRAS
Versão simplificada e eficaz - Outubro 2025
"""

import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from direct_translator import DirectTranslator

# Configurar Flask
app = Flask(__name__)
CORS(app, origins="*")

# Variável global para o tradutor
translator = None

def initialize_translator():
    """Inicializa o tradutor direto"""
    global translator
    
    if translator is not None:
        return translator
    
    try:
        print("🚀 Inicializando tradutor direto...")
        translator = DirectTranslator('models/mappings.pkl')
        print("✅ Tradutor direto inicializado!")
        return translator
    except Exception as e:
        print(f"❌ Erro ao inicializar tradutor: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    """Documentação da API"""
    return jsonify({
        "name": "ELA MVP - Tradutor PT-BR → LIBRAS",
        "version": "4.0.0",
        "description": "Sistema direto e eficaz de tradução para LIBRAS",
        "status": "online",
        "features": [
            "Mapeamentos diretos otimizados",
            "808+ palavras no dicionário",
            "Tradução por frases e palavras",
            "Confiança calculada automaticamente"
        ],
        "endpoints": {
            "home": "GET /",
            "health": "GET /health",
            "translate": "POST /translate",
            "traduzir": "POST /traduzir"
        },
        "usage": {
            "method": "POST",
            "url": "/translate",
            "headers": {"Content-Type": "application/json"},
            "body": {"text": "texto para traduzir"}
        },
        "examples": [
            {"input": "quero agua", "output": "QUERER AGUA"},
            {"input": "bom dia", "output": "BOM DIA"},
            {"input": "obrigado", "output": "OBRIGADO"},
            {"input": "eu gosto de você", "output": "EU GOSTAR DE VOCÊ"}
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """Status de saúde"""
    global translator
    
    if translator is None:
        translator = initialize_translator()
    
    is_healthy = translator is not None
    
    status = {
        "status": "healthy" if is_healthy else "unhealthy",
        "version": "4.0.0",
        "timestamp": time.time(),
        "components": {
            "api": "ok",
            "translator": "ok" if is_healthy else "failed",
            "dictionary_size": len(translator.word_dict) if is_healthy else 0
        }
    }
    
    if is_healthy:
        # Teste rápido
        try:
            test_result = translator.translate("teste")
            status["test"] = {
                "input": "teste",
                "output": test_result.output_gloss,
                "confidence": test_result.confidence,
                "method": test_result.method
            }
        except Exception as e:
            status["test_error"] = str(e)
    
    return jsonify(status)

@app.route('/translate', methods=['POST'])
@app.route('/traduzir', methods=['POST'])
def translate():
    """Endpoint de tradução"""
    global translator
    
    # Validar Content-Type
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Content-Type deve ser application/json",
            "required_header": "Content-Type: application/json"
        }), 400
    
    # Obter dados
    try:
        data = request.get_json()
    except Exception:
        return jsonify({
            "success": False,
            "error": "JSON inválido",
            "example": {"text": "bom dia"}
        }), 400
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Corpo da requisição vazio",
            "example": {"text": "bom dia"}
        }), 400
    
    # Validar campo 'text'
    text = data.get('text', '').strip()
    if not text:
        return jsonify({
            "success": False,
            "error": "Campo 'text' é obrigatório",
            "example": {"text": "bom dia"}
        }), 400
    
    # Inicializar tradutor
    if translator is None:
        translator = initialize_translator()
    
    if translator is None:
        return jsonify({
            "success": False,
            "error": "Tradutor indisponível",
            "details": "Verifique o arquivo models/mappings.pkl"
        }), 503
    
    # Realizar tradução
    try:
        start_time = time.time()
        result = translator.translate(text)
        translation_time = time.time() - start_time
        
        response = {
            "success": True,
            "input": {
                "text": text,
                "language": "pt-br"
            },
            "output": {
                "gloss": result.output_gloss,
                "language": "libras-gloss"
            },
            "metadata": {
                "method": result.method,
                "confidence": round(result.confidence, 3),
                "translation_time": round(translation_time, 4),
                "model_version": "4.0.0",
                "timestamp": time.time()
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro na tradução: {str(e)}",
            "input": {"text": text}
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint não encontrado",
        "available": ["/", "/health", "/translate", "/traduzir"]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Método não permitido",
        "allowed_methods": ["GET", "POST"]
    }), 405

if __name__ == '__main__':
    print("🌟 ELA MVP v4.0 - Tradutor Direto e Eficaz")
    print("="*50)
    
    # Inicializar
    initialize_translator()
    
    print("\n📋 INFORMAÇÕES PARA TESTE:")
    print(f"🔗 URL: http://127.0.0.1:8083")
    print(f"📚 Docs: http://127.0.0.1:8083/")
    print(f"❤️ Health: http://127.0.0.1:8083/health")
    print(f"🔄 Traduzir: POST http://127.0.0.1:8083/translate")
    
    print("\n🧪 Exemplo Postman:")
    print("Método: POST")
    print("URL: http://127.0.0.1:8083/translate")
    print("Headers: Content-Type: application/json")
    print('Body: {"text": "quero agua"}')
    print('Resposta esperada: "QUERER AGUA"')
    
    print("\n🚀 Iniciando servidor...")
    
    app.run(
        host='127.0.0.1',
        port=8083,
        debug=False,
        threaded=True
    )