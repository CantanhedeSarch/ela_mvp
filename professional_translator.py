#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Word2Vec Translator - ELA MVP v5.0
Sistema profissional de tradução PT-BR → LIBRAS com Word2Vec
Autor: ELA Team
Data: Outubro 2025
"""

import numpy as np
import pandas as pd
import pickle
import logging
import re
import time
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import warnings

# Configurar logging profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/translator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suprimir warnings
warnings.filterwarnings('ignore')

@dataclass
class TranslationResult:
    """Classe profissional para resultados de tradução"""
    input_text: str
    output_gloss: str
    confidence: float
    method: str
    processing_time: float
    word_similarities: Optional[Dict[str, float]] = None
    semantic_context: Optional[str] = None
    quality_score: Optional[float] = None

class LibrasTokenizer:
    """Tokenizador profissional para LIBRAS"""
    
    def __init__(self):
        self.gloss_patterns = {
            'markers': r'\[(PONTO|INTERROGAÇÃO|EXCLAMAÇÃO)\]',
            'connectors': r'&',
            'classifiers': r'CL-\w+',
            'pronouns': r'IX-\w+',
            'aspects': r'(REPETIR|CONTÍNUO|FINALIZAR)'
        }
    
    def tokenize(self, text: str) -> List[str]:
        """Tokeniza texto em tokens LIBRAS"""
        # Normalizar texto
        text = text.upper().strip()
        
        # Dividir por espaços mantendo marcadores
        tokens = re.findall(r'\[[\w]+\]|\w+(?:&\w+)*', text)
        
        return tokens
    
    def normalize_gloss(self, gloss: str) -> str:
        """Normaliza gloss LIBRAS para padrão profissional"""
        # Adicionar marcadores se necessário
        if not gloss.endswith(('[PONTO]', '[INTERROGAÇÃO]', '[EXCLAMAÇÃO]')):
            if '?' in gloss:
                gloss = gloss.replace('?', '') + ' [INTERROGAÇÃO]'
            elif '!' in gloss:
                gloss = gloss.replace('!', '') + ' [EXCLAMAÇÃO]'
            else:
                gloss += ' [PONTO]'
        
        return gloss.strip()

class Word2VecSemanticEngine:
    """Motor semântico profissional com Word2Vec"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path or 'models/word2vec_libras.model'
        self.vocabulary = set()
        
    def train_model(self, corpus: List[List[str]], **kwargs) -> None:
        """Treina modelo Word2Vec profissional"""
        logger.info("Iniciando treinamento do modelo Word2Vec...")
        
        # Parâmetros profissionais para Word2Vec
        default_params = {
            'vector_size': 300,
            'window': 5,
            'min_count': 2,
            'workers': 4,
            'sg': 1,  # Skip-gram
            'hs': 0,  # Negative sampling
            'negative': 5,
            'alpha': 0.025,
            'epochs': 100
        }
        
        # Atualizar com parâmetros customizados
        params = {**default_params, **kwargs}
        
        # Treinar modelo
        self.model = Word2Vec(corpus, **params)
        
        # Salvar modelo
        Path(self.model_path).parent.mkdir(exist_ok=True)
        self.model.save(self.model_path)
        
        # Atualizar vocabulário
        self.vocabulary = set(self.model.wv.key_to_index.keys())
        
        logger.info(f"Modelo treinado com {len(self.vocabulary)} palavras")
    
    def load_model(self) -> bool:
        """Carrega modelo Word2Vec existente"""
        try:
            if Path(self.model_path).exists():
                self.model = Word2Vec.load(self.model_path)
                self.vocabulary = set(self.model.wv.key_to_index.keys())
                logger.info(f"Modelo carregado: {len(self.vocabulary)} palavras")
                return True
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo: {e}")
        
        return False
    
    def get_similarity(self, word1: str, word2: str) -> float:
        """Calcula similaridade semântica entre palavras"""
        if not self.model or word1 not in self.vocabulary or word2 not in self.vocabulary:
            return 0.0
        
        try:
            return self.model.wv.similarity(word1, word2)
        except Exception:
            return 0.0
    
    def find_similar_words(self, word: str, topn: int = 5) -> List[Tuple[str, float]]:
        """Encontra palavras similares"""
        if not self.model or word not in self.vocabulary:
            return []
        
        try:
            return self.model.wv.most_similar(word, topn=topn)
        except Exception:
            return []
    
    def get_word_vector(self, word: str) -> Optional[np.ndarray]:
        """Obtém vetor de uma palavra"""
        if not self.model or word not in self.vocabulary:
            return None
        
        try:
            return self.model.wv[word]
        except Exception:
            return None

class ProfessionalLibrasTranslator:
    """Tradutor profissional PT-BR → LIBRAS com Word2Vec"""
    
    def __init__(self, mappings_path: str = 'translation_mappings.pkl'):
        self.mappings_path = mappings_path
        self.tokenizer = LibrasTokenizer()
        self.word2vec_engine = Word2VecSemanticEngine()
        self.word_dict = {}
        self.phrase_mappings = {}
        self.gloss_patterns = {}
        self.confidence_thresholds = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
        
        # Inicializar sistema
        self._initialize_system()
    
    def _initialize_system(self) -> None:
        """Inicializa sistema profissional"""
        logger.info("Inicializando sistema profissional de tradução...")
        
        # Carregar mapeamentos
        self._load_mappings()
        
        # Treinar ou carregar modelo Word2Vec
        self._ensure_word2vec_model()
        
        # Configurar padrões LIBRAS
        self._setup_libras_patterns()
        
        logger.info("Sistema inicializado com sucesso")
    
    def _load_mappings(self) -> None:
        """Carrega mapeamentos de tradução"""
        try:
            with open(self.mappings_path, 'rb') as f:
                data = pickle.load(f)
                self.word_dict = data.get('word_dict', {})
                self.phrase_mappings = data.get('phrase_mappings', {})
            
            logger.info(f"Mapeamentos carregados: {len(self.word_dict)} palavras, "
                       f"{len(self.phrase_mappings)} frases")
        
        except Exception as e:
            logger.error(f"Erro ao carregar mapeamentos: {e}")
            raise
    
    def _ensure_word2vec_model(self) -> None:
        """Garante que o modelo Word2Vec existe"""
        if not self.word2vec_engine.load_model():
            logger.info("Modelo Word2Vec não encontrado. Treinando novo modelo...")
            self._train_word2vec_if_needed()

    def _train_word2vec_if_needed(self) -> None:
        """Treina Word2Vec se necessário"""
        try:
            # Carregar dados para treinamento
            df = pd.read_csv('data/pt-br2libras-gloss_sample_500.csv')
            
            # Preparar corpus
            corpus = []
            for _, row in df.iterrows():
                pt_tokens = self.tokenizer.tokenize(row['pt-br'])
                libras_tokens = self.tokenizer.tokenize(row['libras-gloss'])
                corpus.extend([pt_tokens, libras_tokens])
            
            # Treinar modelo
            self.word2vec_engine.train_model(corpus)
            
        except Exception as e:
            logger.warning(f"Erro ao treinar Word2Vec: {e}")
    
    def _setup_libras_patterns(self) -> None:
        """Configura padrões LIBRAS profissionais"""
        self.gloss_patterns = {
            'question_words': ['QUEM', 'QUE', 'QUANDO', 'ONDE', 'COMO', 'PORQUE'],
            'temporal_markers': ['ONTEM', 'HOJE', 'AMANHÃ', 'AGORA', 'DEPOIS'],
            'aspect_markers': ['JÁ', 'AINDA', 'SEMPRE', 'NUNCA'],
            'modal_verbs': ['PODER', 'DEVER', 'QUERER', 'PRECISAR']
        }
    
    def translate(self, text: str) -> TranslationResult:
        """Tradução profissional com múltiplas estratégias"""
        import time
        start_time = time.time()
        
        logger.info(f"Traduzindo: '{text}'")
        
        # Normalizar entrada
        normalized_text = self._normalize_input(text)
        
        # Estratégia 1: Mapeamento de frases completas
        phrase_result = self._translate_phrase(normalized_text)
        if phrase_result:
            processing_time = time.time() - start_time
            return TranslationResult(
                input_text=text,
                output_gloss=phrase_result,
                confidence=0.95,
                method="phrase_mapping",
                processing_time=processing_time,
                semantic_context="complete_phrase"
            )
        
        # Estratégia 2: Tradução com Word2Vec semântico
        semantic_result = self._translate_with_word2vec(normalized_text)
        if semantic_result:
            processing_time = time.time() - start_time
            return TranslationResult(
                input_text=text,
                output_gloss=semantic_result.output_gloss,
                confidence=semantic_result.confidence,
                method=semantic_result.method,
                processing_time=processing_time,
                word_similarities=semantic_result.word_similarities,
                semantic_context=semantic_result.semantic_context,
                quality_score=semantic_result.quality_score
            )
        
        # Estratégia 3: Mapeamento palavra-por-palavra melhorado
        word_result = self._translate_word_by_word(normalized_text)
        processing_time = time.time() - start_time
        
        return TranslationResult(
            input_text=text,
            output_gloss=word_result.output_gloss,
            confidence=word_result.confidence,
            method=word_result.method,
            processing_time=processing_time,
            word_similarities=word_result.word_similarities,
            semantic_context=word_result.semantic_context,
            quality_score=word_result.quality_score
        )
    
    def _normalize_input(self, text: str) -> str:
        """Normaliza texto de entrada"""
        # Remover pontuação desnecessária
        text = re.sub(r'[^\w\s\?\!]', '', text)
        return text.lower().strip()
    
    def _translate_phrase(self, text: str) -> Optional[str]:
        """Traduz frases completas mapeadas"""
        return self.phrase_mappings.get(text)
    
    def _translate_with_word2vec(self, text: str) -> Optional[TranslationResult]:
        """Tradução semântica com Word2Vec"""
        if not self.word2vec_engine.model:
            return None
        
        words = text.split()
        translated_words = []
        similarities = {}
        total_confidence = 0
        
        for word in words:
            # Tentar mapeamento direto primeiro
            if word in self.word_dict:
                translated_words.append(self.word_dict[word])
                similarities[word] = 1.0
                total_confidence += 1.0
            else:
                # Buscar palavra semanticamente similar
                best_match = self._find_semantic_match(word)
                if best_match:
                    translated_words.append(best_match[0])
                    similarities[word] = best_match[1]
                    total_confidence += best_match[1]
                else:
                    translated_words.append(word.upper())
                    similarities[word] = 0.3
                    total_confidence += 0.3
        
        # Calcular confiança média
        confidence = total_confidence / len(words) if words else 0
        
        # Normalizar resultado para LIBRAS
        output_gloss = self.tokenizer.normalize_gloss(' '.join(translated_words))
        
        return TranslationResult(
            input_text=text,
            output_gloss=output_gloss,
            confidence=confidence,
            method="semantic_word2vec",
            processing_time=0,  # Será preenchido depois
            word_similarities=similarities,
            semantic_context="word2vec_enhanced"
        )
    
    def _find_semantic_match(self, word: str) -> Optional[Tuple[str, float]]:
        """Encontra correspondência semântica para uma palavra"""
        best_match = None
        best_similarity = 0
        
        # Buscar em palavras conhecidas
        for known_word in self.word_dict.keys():
            similarity = self.word2vec_engine.get_similarity(word, known_word)
            if similarity > best_similarity and similarity > 0.6:
                best_similarity = similarity
                best_match = (self.word_dict[known_word], similarity)
        
        return best_match
    
    def _translate_word_by_word(self, text: str) -> TranslationResult:
        """Tradução palavra-por-palavra melhorada"""
        words = text.split()
        translated_words = []
        confidence_scores = []
        
        for word in words:
            if word in self.word_dict:
                translated_words.append(self.word_dict[word])
                confidence_scores.append(1.0)
            else:
                # Tentar variações da palavra
                variations = self._get_word_variations(word)
                found = False
                
                for variation in variations:
                    if variation in self.word_dict:
                        translated_words.append(self.word_dict[variation])
                        confidence_scores.append(0.8)
                        found = True
                        break
                
                if not found:
                    translated_words.append(word.upper())
                    confidence_scores.append(0.3)
        
        # Calcular confiança média
        confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Normalizar para LIBRAS
        output_gloss = self.tokenizer.normalize_gloss(' '.join(translated_words))
        
        return TranslationResult(
            input_text=text,
            output_gloss=output_gloss,
            confidence=confidence,
            method="enhanced_word_mapping",
            processing_time=0,
            quality_score=self._calculate_quality_score(confidence, len(words))
        )
    
    def _get_word_variations(self, word: str) -> List[str]:
        """Gera variações de uma palavra"""
        variations = [word]
        
        # Remover acentos e caracteres especiais
        variations.append(re.sub(r'[áàâã]', 'a', word))
        variations.append(re.sub(r'[éêë]', 'e', word))
        variations.append(re.sub(r'[íîï]', 'i', word))
        variations.append(re.sub(r'[óôõ]', 'o', word))
        variations.append(re.sub(r'[úûü]', 'u', word))
        variations.append(re.sub(r'ç', 'c', word))
        
        # Remover sufixos comuns
        if word.endswith('ando'):
            variations.append(word[:-4] + 'ar')
        elif word.endswith('endo'):
            variations.append(word[:-4] + 'er')
        elif word.endswith('indo'):
            variations.append(word[:-4] + 'ir')
        
        return list(set(variations))
    
    def _calculate_quality_score(self, confidence: float, word_count: int) -> float:
        """Calcula score de qualidade da tradução"""
        # Penalizar traduções muito curtas ou muito longas
        length_penalty = 1.0
        if word_count < 2:
            length_penalty = 0.8
        elif word_count > 10:
            length_penalty = 0.9
        
        return confidence * length_penalty
    
    def get_translation_analytics(self, text: str) -> Dict:
        """Retorna análise detalhada da tradução"""
        result = self.translate(text)
        
        analytics = {
            'input_analysis': {
                'word_count': len(text.split()),
                'character_count': len(text),
                'complexity': 'simple' if len(text.split()) <= 3 else 'complex'
            },
            'translation_quality': {
                'confidence': result.confidence,
                'method': result.method,
                'quality_score': result.quality_score or result.confidence
            },
            'semantic_analysis': {
                'word_similarities': result.word_similarities,
                'context': result.semantic_context
            },
            'performance': {
                'processing_time': result.processing_time,
                'words_per_second': len(text.split()) / result.processing_time if result.processing_time > 0 else float('inf')
            }
        }
        
        return analytics

# Função de conveniência para uso direto
def translate_text(text: str, translator: Optional[ProfessionalLibrasTranslator] = None) -> TranslationResult:
    """Função de conveniência para tradução rápida"""
    if translator is None:
        translator = ProfessionalLibrasTranslator()
    
    return translator.translate(text)

if __name__ == "__main__":
    # Exemplo de uso profissional
    translator = ProfessionalLibrasTranslator()
    
    # Testes profissionais
    test_cases = [
        "quero agua",
        "bom dia como você está",
        "eu gosto muito de você",
        "onde você trabalha?",
        "obrigado pela ajuda"
    ]
    
    print("🚀 SISTEMA PROFISSIONAL DE TRADUÇÃO - ELA MVP v5.0")
    print("="*60)
    
    for test in test_cases:
        result = translator.translate(test)
        analytics = translator.get_translation_analytics(test)
        
        print(f"\n📝 Input: '{result.input_text}'")
        print(f"🎯 Output: '{result.output_gloss}'")
        print(f"🔍 Método: {result.method}")
        print(f"📊 Confiança: {result.confidence:.2%}")
        print(f"⚡ Tempo: {result.processing_time:.4f}s")
        
        if result.word_similarities:
            print(f"🧠 Similaridades: {result.word_similarities}")