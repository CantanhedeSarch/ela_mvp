#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Simples - Sistema de Tradução PT-BR → LIBRAS
Versão funcional e testada - Outubro 2025
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from direct_translator import DirectTranslator
import traceback

app = Flask(__name__)
CORS(app)

# Inicializar tradutor globalmente
try:
    print("🚀 Inicializando tradutor...")
    tradutor = DirectTranslator('models/mappings.pkl')
    print("✅ Tradutor pronto!")
except Exception as e:
    print(f"❌ Erro ao inicializar: {e}")
    tradutor = None

@app.route('/', methods=['GET'])
def home():
    """Página inicial"""
    return {
        "name": "ELA MVP - Tradutor PT-BR → LIBRAS",
        "version": "4.0",
        "status": "online" if tradutor else "offline",
        "examples": [
            {"input": "quero agua", "output": "QUERER AGUA"},
            {"input": "bom dia", "output": "BOM DIA"},
            {"input": "obrigado", "output": "OBRIGADO"}
        ],
        "usage": "POST /translate com {\"text\": \"sua frase\"}"
    }

@app.route('/translate', methods=['POST'])
def translate():
    """Traduzir texto"""
    if not tradutor:
        return {"error": "Tradutor indisponível"}, 503
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return {"error": "Campo 'text' obrigatório"}, 400
        
        texto = data['text'].strip()
        if not texto:
            return {"error": "Texto vazio"}, 400
        
        resultado = tradutor.translate(texto)
        
        return {
            "success": True,
            "input": texto,
            "output": resultado.output_gloss,
            "method": resultado.method,
            "confidence": round(resultado.confidence, 2)
        }
        
    except Exception as e:
        print(f"❌ Erro na tradução: {e}")
        traceback.print_exc()
        return {"error": f"Erro: {str(e)}"}, 500

if __name__ == '__main__':
    print("\n🌟 ELA MVP v4.0 - API Simples")
    print("="*40)
    print("🔗 URL: http://127.0.0.1:5000")
    print("📋 Teste: POST /translate")
    print('📝 Body: {"text": "quero agua"}')
    print("\n🚀 Iniciando...")
    
    app.run(host='127.0.0.1', port=5000, debug=True)