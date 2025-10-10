#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug do sistema profissional
"""

import pickle
import os

def debug_mappings():
    print("🔍 DEBUG DOS MAPEAMENTOS")
    print("="*50)
    
    # Verificar arquivos
    files_to_check = [
        'translation_mappings.pkl',
        'word_mappings.pkl',
        'libras_mappings.pkl'
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            print(f"✅ {filename} existe")
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                print(f"   📊 Conteúdo: {type(data)}")
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            print(f"   📝 {key}: {len(value)} itens")
                        elif isinstance(value, list):
                            print(f"   📝 {key}: {len(value)} itens")
                        else:
                            print(f"   📝 {key}: {type(value)}")
            except Exception as e:
                print(f"   ❌ Erro ao ler: {e}")
        else:
            print(f"❌ {filename} não existe")
    
    print("\n🧪 TESTE DE CARREGAMENTO DIRETO")
    print("-"*50)
    
    try:
        from professional_translator import ProfessionalLibrasTranslator
        translator = ProfessionalLibrasTranslator()
        
        print(f"📊 Word dict: {len(translator.word_dict)} palavras")
        print(f"📊 Phrase mappings: {len(translator.phrase_mappings)} frases")
        
        # Mostrar algumas palavras
        if translator.word_dict:
            print("\n🔤 PRIMEIRAS 10 PALAVRAS:")
            for i, (pt, libras) in enumerate(list(translator.word_dict.items())[:10]):
                print(f"   {pt} → {libras}")
        
        # Testar tradução simples
        print("\n🧪 TESTE DE TRADUÇÃO:")
        test_words = ['quero', 'agua', 'bom', 'dia', 'obrigado']
        for word in test_words:
            if word in translator.word_dict:
                print(f"   ✅ {word} → {translator.word_dict[word]}")
            else:
                print(f"   ❌ {word} não encontrado")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_mappings()