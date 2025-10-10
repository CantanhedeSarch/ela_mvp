#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tradutor Direto e Eficaz - PT-BR → LIBRAS
Sistema baseado em mapeamentos diretos e lógica simples
Outubro 2025
"""

import re
import pickle
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TranslationResult:
    input_text: str
    output_gloss: str
    confidence: float
    method: str

class DirectTranslator:
    """Tradutor direto baseado em mapeamentos e regras"""
    
    def __init__(self, mappings_path: str):
        self.mappings_path = mappings_path
        self.mappings = None
        self._load_mappings()
        self._create_word_dictionary()
        
    def _load_mappings(self):
        """Carrega mapeamentos dos dados"""
        try:
            with open(self.mappings_path, 'rb') as f:
                self.mappings = pickle.load(f)
            print("✅ Mapeamentos carregados")
        except Exception as e:
            print(f"❌ Erro ao carregar mapeamentos: {e}")
            raise
    
    def _create_word_dictionary(self):
        """Cria dicionário completo de traduções"""
        self.word_dict = {}
        
        # 1. Mapeamentos diretos conhecidos
        direct_mappings = {
            # Cumprimentos
            'oi': 'OI',
            'olá': 'OLÁ', 
            'alô': 'OLÁ',
            'bom dia': 'BOM DIA',
            'boa tarde': 'BOA TARDE',
            'boa noite': 'BOA NOITE',
            
            # Despedidas
            'tchau': 'TCHAU',
            'adeus': 'TCHAU',
            'até logo': 'TCHAU',
            'até mais': 'TCHAU',
            
            # Agradecimentos
            'obrigado': 'OBRIGADO',
            'obrigada': 'OBRIGADO',
            'valeu': 'OBRIGADO',
            'muito obrigado': 'MUITO OBRIGADO',
            
            # Pedidos
            'por favor': 'POR FAVOR',
            'pfv': 'POR FAVOR',
            'com licença': 'COM LICENÇA',
            'desculpa': 'DESCULPA',
            'desculpe': 'DESCULPA',
            
            # Pronomes
            'eu': 'EU',
            'você': 'VOCÊ',
            'ele': 'ELE',
            'ela': 'ELA',
            'nós': 'NÓS',
            'vocês': 'VOCÊS',
            'eles': 'ELES',
            'elas': 'ELAS',
            
            # Verbos comuns
            'quero': 'QUERER',
            'quer': 'QUERER',
            'queremos': 'QUERER',
            'querem': 'QUERER',
            'preciso': 'PRECISAR',
            'precisa': 'PRECISAR',
            'gosto': 'GOSTAR',
            'gosta': 'GOSTAR',
            'tenho': 'TER',
            'tem': 'TER',
            'temos': 'TER',
            'sou': 'SER',
            'é': 'SER',
            'somos': 'SER',
            'são': 'SER',
            'estou': 'ESTAR',
            'está': 'ESTAR',
            'estamos': 'ESTAR',
            'estão': 'ESTAR',
            'vou': 'IR',
            'vai': 'IR',
            'vamos': 'IR',
            'vão': 'IR',
            'faço': 'FAZER',
            'faz': 'FAZER',
            'fazemos': 'FAZER',
            'fazem': 'FAZER',
            
            # Substantivos comuns
            'água': 'ÁGUA',
            'casa': 'CASA',
            'trabalho': 'TRABALHO',
            'escola': 'ESCOLA',
            'família': 'FAMÍLIA',
            'amigo': 'AMIGO',
            'amiga': 'AMIGO',
            'comida': 'COMIDA',
            'bebida': 'BEBIDA',
            'dinheiro': 'DINHEIRO',
            'tempo': 'TEMPO',
            'dia': 'DIA',
            'noite': 'NOITE',
            'manhã': 'MANHÃ',
            'tarde': 'TARDE',
            'hora': 'HORA',
            'nome': 'NOME',
            'pessoa': 'PESSOA',
            'lugar': 'LUGAR',
            'cidade': 'CIDADE',
            'país': 'PAÍS',
            'mundo': 'MUNDO',
            
            # Adjetivos comuns
            'bom': 'BOM',
            'boa': 'BOM',
            'ruim': 'RUIM',
            'grande': 'GRANDE',
            'pequeno': 'PEQUENO',
            'novo': 'NOVO',
            'nova': 'NOVO',
            'velho': 'VELHO',
            'velha': 'VELHO',
            'bonito': 'BONITO',
            'bonita': 'BONITO',
            'feio': 'FEIO',
            'feia': 'FEIO',
            
            # Negações e afirmações
            'sim': 'SIM',
            'não': 'NÃO',
            'talvez': 'TALVEZ',
            
            # Preposições
            'em': 'EM',
            'de': 'DE',
            'para': 'PARA',
            'com': 'COM',
            'sem': 'SEM',
            'por': 'POR',
            'sobre': 'SOBRE',
            'entre': 'ENTRE',
            
            # Números básicos
            'um': '1',
            'uma': '1',
            'dois': '2',
            'duas': '2',
            'três': '3',
            'quatro': '4',
            'cinco': '5',
            'seis': '6',
            'sete': '7',
            'oito': '8',
            'nove': '9',
            'dez': '10'
        }
        
        # Adicionar mapeamentos diretos
        self.word_dict.update(direct_mappings)
        
        # 2. Adicionar mapeamentos dos dados
        if self.mappings and 'word_mappings' in self.mappings:
            for pt_word, libras_word in self.mappings['word_mappings'].items():
                if pt_word not in self.word_dict:  # Não sobrescrever mapeamentos diretos
                    self.word_dict[pt_word] = libras_word.upper()
        
        # 3. Adicionar palavras do vocabulário LIBRAS que são iguais em PT
        if self.mappings and 'libras_vocab' in self.mappings:
            for libras_word in self.mappings['libras_vocab'].keys():
                libras_lower = libras_word.lower()
                if libras_lower not in self.word_dict:
                    self.word_dict[libras_lower] = libras_word.upper()
        
        print(f"✅ Dicionário criado com {len(self.word_dict)} palavras")
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocessa o texto de entrada"""
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower().strip()
        
        # Remover pontuação
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espaços
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _translate_phrase(self, text: str) -> Optional[str]:
        """Tenta traduzir a frase completa"""
        # Verificar mapeamentos de frases completas
        if self.mappings and 'phrase_mappings' in self.mappings:
            if text in self.mappings['phrase_mappings']:
                return self.mappings['phrase_mappings'][text].upper()
        
        # Verificar no dicionário direto
        if text in self.word_dict:
            return self.word_dict[text]
        
        return None
    
    def _translate_words(self, text: str) -> List[str]:
        """Traduz palavra por palavra"""
        words = text.split()
        translated = []
        
        for word in words:
            if word in self.word_dict:
                translated.append(self.word_dict[word])
            else:
                # Tentar variações da palavra
                found = False
                
                # Tentar sem acentos básicos
                word_no_accent = (word.replace('á', 'a').replace('é', 'e')
                                      .replace('í', 'i').replace('ó', 'o')
                                      .replace('ú', 'u').replace('ç', 'c')
                                      .replace('ã', 'a').replace('õ', 'o'))
                
                if word_no_accent in self.word_dict:
                    translated.append(self.word_dict[word_no_accent])
                    found = True
                
                # Tentar buscar palavra similar no vocabulário LIBRAS (apenas se muito parecida)
                if not found and self.mappings and 'libras_vocab' in self.mappings:
                    for libras_word in self.mappings['libras_vocab'].keys():
                        # Só aceitar se a palavra for muito similar (diferença de 1 caractere ou menos)
                        if (len(word) > 3 and len(libras_word) > 3 and 
                            abs(len(word) - len(libras_word)) <= 1 and
                            (word in libras_word.lower() or libras_word.lower() in word)):
                            translated.append(libras_word.upper())
                            found = True
                            break
                
                # Se não encontrou, manter a palavra original em maiúsculas
                if not found:
                    translated.append(word.upper())
        
        return translated
    
    def translate(self, text: str) -> TranslationResult:
        """Traduz texto do português para LIBRAS"""
        if not text or not text.strip():
            return TranslationResult(
                input_text=text,
                output_gloss="",
                confidence=0.0,
                method="error"
            )
        
        # Preprocessar
        processed_text = self._preprocess_text(text)
        
        # 1. Tentar tradução de frase completa
        phrase_translation = self._translate_phrase(processed_text)
        if phrase_translation:
            return TranslationResult(
                input_text=text,
                output_gloss=phrase_translation,
                confidence=0.95,
                method="phrase_mapping"
            )
        
        # 2. Tradução palavra por palavra
        word_translations = self._translate_words(processed_text)
        result_gloss = ' '.join(word_translations)
        
        # Calcular confiança baseada em quantas palavras foram encontradas
        words = processed_text.split()
        found_count = sum(1 for word in words if word in self.word_dict)
        confidence = (found_count / len(words)) if words else 0.0
        
        return TranslationResult(
            input_text=text,
            output_gloss=result_gloss,
            confidence=confidence,
            method="word_mapping"
        )

if __name__ == "__main__":
    # Teste do tradutor
    try:
        translator = DirectTranslator('models/mappings.pkl')
        
        test_cases = [
            "quero agua",
            "bom dia",
            "olá",
            "obrigado",
            "eu gosto de você",
            "como vai?",
            "eu tenho sede",
            "você está bem?",
            "onde é o banheiro?",
            "quanto custa?",
            "casa",
            "trabalho",
            "família"
        ]
        
        print("\n🧪 TESTANDO NOVO TRADUTOR:")
        print("="*50)
        
        for text in test_cases:
            result = translator.translate(text)
            print(f"'{text}' → '{result.output_gloss}' ({result.method}, {result.confidence:.2f})")
    
    except Exception as e:
        print(f"❌ Erro: {e}")