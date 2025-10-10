#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask para Postman - Sistema de Tradução PT-BR → LIBRAS
Versão funcional com Direct Translator - Outubro 2025
"""

import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Inicializar Flask
app = Flask(__name__)
CORS(app, origins="*")

# Variáveis globais
translator = None
app_version = "4.0.0"

def initialize_translator():
    """Inicializa o tradutor direto"""
    global translator
    
    if translator is not None:
        return translator
    
    try:
        print("🚀 Inicializando tradutor direto para Postman...")
        
        from direct_translator import DirectTranslator
        
        translator = DirectTranslator('models/mappings.pkl')
        
        print("✅ Tradutor direto inicializado com sucesso!")
        return translator
        
    except Exception as e:
        print(f"❌ Erro ao inicializar tradutor: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    """Página inicial - Documentação para Postman"""
    return jsonify({
        "message": "🌟 API de Tradução PT-BR → LIBRAS v3.0",
        "status": "online",
        "version": app_version,
        "description": "Sistema híbrido de tradução automática para LIBRAS",
        "endpoints": {
            "home": {
                "url": "/",
                "method": "GET",
                "description": "Esta página de documentação"
            },
            "health": {
                "url": "/health",
                "method": "GET", 
                "description": "Status de saúde da API"
            },
            "translate": {
                "url": "/translate",
                "method": "POST",
                "description": "Traduzir texto do português para LIBRAS",
                "content_type": "application/json",
                "body_example": {
                    "text": "bom dia"
                },
                "response_example": {
                    "success": True,
                    "input": {"text": "bom dia", "language": "pt-br"},
                    "output": {"gloss": "BOM DIA", "language": "libras-gloss"},
                    "metadata": {
                        "method": "rule_based",
                        "confidence": 0.95,
                        "translation_time": 0.001,
                        "model_version": "3.0.0"
                    }
                }
            },
            "traduzir": {
                "url": "/traduzir",
                "method": "POST",
                "description": "Mesmo que /translate (endpoint em português)"
            }
        },
        "test_examples": [
            {"text": "bom dia"},
            {"text": "boa tarde"},
            {"text": "olá"},
            {"text": "obrigado"},
            {"text": "por favor"},
            {"text": "eu"},
            {"text": "você"},
            {"text": "casa"}
        ],
        "timestamp": time.time()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Status de saúde da API"""
    global translator
    
    if translator is None:
        translator = initialize_translator()
    
    is_healthy = translator is not None
    
    status = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "version": app_version,
        "components": {
            "api": "ok",
            "translator": "ok" if is_healthy else "failed",
            "model": "ok" if (is_healthy and translator.model) else "failed",
            "mappings": "ok" if (is_healthy and translator.mappings) else "failed"
        }
    }
    
    if is_healthy:
        try:
            # Teste rápido
            test_result = translator.translate("teste")
            status["test_translation"] = {
                "input": "teste",
                "output": test_result.output_gloss,
                "method": test_result.method,
                "confidence": test_result.confidence
            }
        except Exception as e:
            status["test_error"] = str(e)
    
    return jsonify(status)

@app.route('/translate', methods=['POST'])
@app.route('/traduzir', methods=['POST'])
def translate():
    """Endpoint de tradução"""
    global translator
    
    # Verificar Content-Type
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Content-Type deve ser application/json",
            "expected_header": "Content-Type: application/json",
            "example_body": {"text": "bom dia"}
        }), 400
    
    # Obter dados JSON
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "JSON inválido",
            "details": str(e),
            "example_body": {"text": "bom dia"}
        }), 400
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Corpo da requisição vazio",
            "example_body": {"text": "bom dia"}
        }), 400
    
    # Verificar campo 'text'
    text = data.get('text', '').strip()
    if not text:
        return jsonify({
            "success": False,
            "error": "Campo 'text' é obrigatório e não pode estar vazio",
            "received_data": data,
            "example_body": {"text": "bom dia"}
        }), 400
    
    # Inicializar tradutor se necessário
    if translator is None:
        translator = initialize_translator()
    
    if translator is None:
        return jsonify({
            "success": False,
            "error": "Tradutor não disponível",
            "details": "Verifique se o arquivo de mapeamentos está presente",
            "required_files": [
                "models/mappings.pkl"
            ]
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
                "model_version": app_version,
                "timestamp": time.time()
            }
        }
        
        # Adicionar informações extras se solicitado
        if data.get('debug', False):
            response["debug"] = {
                "word_dict_size": len(translator.word_dict),
                "input_normalized": text.lower().strip()
            }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro durante tradução: {str(e)}",
            "input": {"text": text, "language": "pt-br"},
            "timestamp": time.time()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Endpoint não encontrado"""
    return jsonify({
        "success": False,
        "error": "Endpoint não encontrado",
        "available_endpoints": ["/", "/health", "/translate", "/traduzir"],
        "tip": "Acesse / para ver a documentação completa"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Método não permitido"""
    return jsonify({
        "success": False,
        "error": "Método HTTP não permitido",
        "allowed_methods": {
            "/": ["GET"],
            "/health": ["GET"],
            "/translate": ["POST"],
            "/traduzir": ["POST"]
        }
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Erro interno"""
    return jsonify({
        "success": False,
        "error": "Erro interno do servidor",
        "message": "Verifique os logs do servidor"
    }), 500

if __name__ == '__main__':
    print("🌟 API para Postman - Tradução PT-BR → LIBRAS v3.0")
    print("="*60)
    
    # Inicializar tradutor
    initialize_translator()
    
    # Informações para Postman
    print("\n📋 INFORMAÇÕES PARA POSTMAN:")
    print("="*60)
    print("🔗 URL Base: http://127.0.0.1:8082")
    print("\n📚 Endpoints disponíveis:")
    print("  GET  http://127.0.0.1:8082/        (documentação)")
    print("  GET  http://127.0.0.1:8082/health  (status)")
    print("  POST http://127.0.0.1:8082/translate")
    print("  POST http://127.0.0.1:8082/traduzir")
    
    print("\n🧪 Exemplo de teste no Postman:")
    print("  Método: POST")
    print("  URL: http://127.0.0.1:8082/translate")
    print("  Headers: Content-Type: application/json")
    print("  Body (raw JSON):")
    print('    {"text": "bom dia"}')
    
    print("\n🚀 Iniciando servidor...")
    
    app.run(
        host='127.0.0.1',
        port=8082,
        debug=False,
        threaded=True
    )