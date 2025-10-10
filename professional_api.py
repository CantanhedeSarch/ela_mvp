#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional API - ELA MVP v5.0
API empresarial para tradução PT-BR → LIBRAS com Word2Vec
Autor: ELA Team
Data: Outubro 2025
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, InternalServerError
from professional_translator import ProfessionalLibrasTranslator, TranslationResult

# Configurar logging profissional
Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurar Flask profissional
app = Flask(__name__)
app.config.update({
    'JSON_SORT_KEYS': False,
    'JSONIFY_PRETTYPRINT_REGULAR': True,
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max
})

CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"])

# Instância global do tradutor
translator: Optional[ProfessionalLibrasTranslator] = None

class APIError(Exception):
    """Classe personalizada para erros da API"""
    def __init__(self, message: str, status_code: int = 400, payload: Optional[Dict] = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

def initialize_translator() -> ProfessionalLibrasTranslator:
    """Inicializa tradutor profissional"""
    global translator
    
    if translator is not None:
        return translator
    
    try:
        logger.info("Inicializando tradutor profissional...")
        translator = ProfessionalLibrasTranslator()
        logger.info("Tradutor profissional inicializado com sucesso")
        return translator
    
    except Exception as e:
        logger.error(f"Erro ao inicializar tradutor: {e}")
        raise APIError("Erro interno do servidor: tradutor não disponível", 503)

@app.before_request
def before_request():
    """Middleware executado antes de cada request"""
    g.start_time = time.time()
    g.request_id = f"{int(time.time())}-{id(request)}"
    
    logger.info(f"Request {g.request_id}: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Middleware executado após cada request"""
    total_time = time.time() - g.start_time
    
    logger.info(f"Request {g.request_id} completado em {total_time:.4f}s - Status: {response.status_code}")
    
    # Adicionar headers profissionais
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Processing-Time'] = f"{total_time:.4f}s"
    response.headers['X-API-Version'] = "5.0.0"
    
    return response

@app.errorhandler(APIError)
def handle_api_error(error):
    """Handler para erros personalizados da API"""
    response = {
        "success": False,
        "error": {
            "message": error.message,
            "code": error.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(g, 'request_id', 'unknown')
        }
    }
    
    if error.payload:
        response["error"]["details"] = error.payload
    
    return jsonify(response), error.status_code

@app.errorhandler(400)
def handle_bad_request(error):
    """Handler para bad requests"""
    return handle_api_error(APIError("Requisição inválida", 400))

@app.errorhandler(500)
def handle_internal_error(error):
    """Handler para erros internos"""
    logger.error(f"Erro interno: {error}")
    return handle_api_error(APIError("Erro interno do servidor", 500))

def validate_translation_request(data: Dict[str, Any]) -> str:
    """Valida requisição de tradução"""
    if not data:
        raise APIError("Body da requisição não pode estar vazio")
    
    if 'text' not in data:
        raise APIError("Campo 'text' é obrigatório", payload={"required_fields": ["text"]})
    
    text = data['text']
    
    if not isinstance(text, str):
        raise APIError("Campo 'text' deve ser uma string")
    
    text = text.strip()
    if not text:
        raise APIError("Texto não pode estar vazio")
    
    if len(text) > 10000:
        raise APIError("Texto muito longo (máximo 10.000 caracteres)", payload={"max_length": 10000})
    
    return text

@app.route('/', methods=['GET'])
def api_documentation():
    """Documentação profissional da API"""
    return jsonify({
        "api": {
            "name": "ELA MVP Professional Translation API",
            "version": "5.0.0",
            "description": "API empresarial para tradução PT-BR → LIBRAS com Word2Vec",
            "status": "online",
            "timestamp": datetime.utcnow().isoformat()
        },
        "features": {
            "word2vec_integration": "Análise semântica avançada",
            "professional_logging": "Logs estruturados e rastreamento",
            "quality_analytics": "Métricas de qualidade da tradução",
            "performance_monitoring": "Monitoramento de performance",
            "error_handling": "Tratamento robusto de erros"
        },
        "endpoints": {
            "documentation": {
                "method": "GET",
                "url": "/",
                "description": "Esta documentação"
            },
            "health": {
                "method": "GET", 
                "url": "/health",
                "description": "Status de saúde do sistema"
            },
            "translate": {
                "method": "POST",
                "url": "/translate",
                "description": "Tradução principal",
                "body": {
                    "text": "string (obrigatório)",
                    "include_analytics": "boolean (opcional)",
                    "quality_threshold": "float (opcional, 0.0-1.0)"
                }
            },
            "batch": {
                "method": "POST",
                "url": "/translate/batch",
                "description": "Tradução em lote",
                "body": {
                    "texts": ["array de strings (obrigatório)"],
                    "include_analytics": "boolean (opcional)"
                }
            }
        },
        "examples": {
            "simple_translation": {
                "request": {
                    "method": "POST",
                    "url": "/translate",
                    "body": {"text": "quero agua"}
                },
                "response": {
                    "output_gloss": "QUERER AGUA [PONTO]",
                    "confidence": 0.85,
                    "method": "semantic_word2vec"
                }
            }
        },
        "support": {
            "documentation": "README_FINAL.md",
            "postman_collection": "ELA_MVP_Postman_v5.json",
            "logs": "logs/api.log"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check profissional"""
    start_time = time.time()
    
    try:
        # Verificar tradutor
        translator_instance = initialize_translator()
        
        # Teste rápido de tradução
        test_result = translator_instance.translate("teste")
        
        # Verificar Word2Vec
        word2vec_status = "available" if translator_instance.word2vec_engine.model else "training_needed"
        
        response_time = time.time() - start_time
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "5.0.0",
            "components": {
                "translator": {
                    "status": "operational",
                    "word_dict_size": len(translator_instance.word_dict),
                    "phrase_mappings": len(translator_instance.phrase_mappings)
                },
                "word2vec_engine": {
                    "status": word2vec_status,
                    "vocabulary_size": len(translator_instance.word2vec_engine.vocabulary)
                },
                "api": {
                    "status": "operational",
                    "response_time": f"{response_time:.4f}s"
                }
            },
            "test": {
                "input": "teste",
                "output": test_result.output_gloss,
                "confidence": test_result.confidence,
                "method": test_result.method
            },
            "metrics": {
                "uptime": "active",
                "request_id": g.request_id
            }
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "request_id": g.request_id
        }), 503

@app.route('/translate', methods=['POST'])
def translate_text():
    """Endpoint principal de tradução"""
    try:
        # Validar requisição
        data = request.get_json()
        text = validate_translation_request(data)
        
        # Opções avançadas
        include_analytics = data.get('include_analytics', False)
        quality_threshold = data.get('quality_threshold', 0.0)
        
        # Inicializar tradutor
        translator_instance = initialize_translator()
        
        # Realizar tradução
        result = translator_instance.translate(text)
        
        # Verificar qualidade mínima
        if result.confidence < quality_threshold:
            raise APIError(
                f"Qualidade da tradução abaixo do threshold ({result.confidence:.2%} < {quality_threshold:.2%})",
                422,
                {"actual_confidence": result.confidence, "required_threshold": quality_threshold}
            )
        
        # Construir resposta
        response = {
            "success": True,
            "translation": {
                "input": {
                    "text": result.input_text,
                    "language": "pt-br"
                },
                "output": {
                    "gloss": result.output_gloss,
                    "language": "libras-gloss"
                },
                "metadata": {
                    "method": result.method,
                    "confidence": round(result.confidence, 4),
                    "processing_time": round(result.processing_time, 4),
                    "quality_score": round(result.quality_score or result.confidence, 4),
                    "semantic_context": result.semantic_context
                }
            },
            "system": {
                "version": "5.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": g.request_id
            }
        }
        
        # Adicionar analytics se solicitado
        if include_analytics:
            analytics = translator_instance.get_translation_analytics(text)
            response["analytics"] = analytics
        
        # Adicionar similaridades Word2Vec se disponíveis
        if result.word_similarities:
            response["translation"]["word_similarities"] = result.word_similarities
        
        return jsonify(response)
    
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Erro na tradução: {e}")
        raise APIError("Erro interno durante tradução", 500)

@app.route('/translate/batch', methods=['POST'])
def translate_batch():
    """Tradução em lote profissional"""
    try:
        data = request.get_json()
        
        if not data or 'texts' not in data:
            raise APIError("Campo 'texts' é obrigatório para tradução em lote")
        
        texts = data['texts']
        
        if not isinstance(texts, list):
            raise APIError("Campo 'texts' deve ser um array")
        
        if len(texts) > 100:
            raise APIError("Máximo 100 textos por lote", payload={"max_batch_size": 100})
        
        include_analytics = data.get('include_analytics', False)
        
        # Inicializar tradutor
        translator_instance = initialize_translator()
        
        # Processar lote
        results = []
        total_start_time = time.time()
        
        for i, text in enumerate(texts):
            try:
                if not isinstance(text, str) or not text.strip():
                    results.append({
                        "index": i,
                        "success": False,
                        "error": "Texto inválido ou vazio"
                    })
                    continue
                
                result = translator_instance.translate(text.strip())
                
                translation_data = {
                    "index": i,
                    "success": True,
                    "translation": {
                        "input": result.input_text,
                        "output": result.output_gloss,
                        "confidence": round(result.confidence, 4),
                        "method": result.method
                    }
                }
                
                if include_analytics:
                    analytics = translator_instance.get_translation_analytics(text)
                    translation_data["analytics"] = analytics
                
                results.append(translation_data)
                
            except Exception as e:
                logger.error(f"Erro na tradução do item {i}: {e}")
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        total_time = time.time() - total_start_time
        successful_translations = sum(1 for r in results if r.get('success', False))
        
        return jsonify({
            "success": True,
            "batch_result": {
                "total_items": len(texts),
                "successful_translations": successful_translations,
                "failed_translations": len(texts) - successful_translations,
                "processing_time": round(total_time, 4),
                "average_time_per_item": round(total_time / len(texts), 4)
            },
            "results": results,
            "system": {
                "version": "5.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": g.request_id
            }
        })
    
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Erro na tradução em lote: {e}")
        raise APIError("Erro interno durante tradução em lote", 500)

if __name__ == '__main__':
    print("🚀 ELA MVP v5.0 - API PROFISSIONAL")
    print("="*50)
    print("🔗 URL: http://127.0.0.1:9000")
    print("📚 Docs: http://127.0.0.1:9000/")
    print("❤️ Health: http://127.0.0.1:9000/health")
    print("🔄 Translate: POST http://127.0.0.1:9000/translate")
    print("📦 Batch: POST http://127.0.0.1:9000/translate/batch")
    print("\n🧪 Recursos avançados:")
    print("• Word2Vec semântico")
    print("• Analytics de qualidade")
    print("• Tradução em lote")
    print("• Logging profissional")
    print("• Monitoramento de performance")
    print("\n🚀 Iniciando servidor...")
    
    # Inicializar tradutor
    initialize_translator()
    
    app.run(
        host='127.0.0.1',
        port=9000,
        debug=False,
        threaded=True
    )