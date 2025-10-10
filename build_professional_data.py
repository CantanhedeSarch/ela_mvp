#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Data Builder - ELA MVP v5.0
Constrói dados profissionais para o sistema de tradução
Autor: ELA Team
Data: Outubro 2025
"""

import pandas as pd
import pickle
import re
import logging
from pathlib import Path
from typing import Dict, List, Set

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfessionalDataBuilder:
    """Construtor profissional de dados de treinamento"""
    
    def __init__(self):
        self.word_dict = {}
        self.phrase_mappings = {}
        self.vocabulary = set()
    
    def build_from_csv(self, csv_path: str = 'data/pt-br2libras-gloss_sample_500.csv') -> None:
        """Constrói dados a partir do CSV"""
        logger.info("🔧 Construindo dados profissionais...")
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"📊 Carregado {len(df)} registros do CSV")
            
            # Processar cada linha
            for idx, row in df.iterrows():
                pt_text = str(row['pt-br']).strip().lower()
                libras_gloss = str(row['libras-gloss']).strip().upper()
                
                if pd.isna(pt_text) or pd.isna(libras_gloss):
                    continue
                
                # Limpar textos
                pt_clean = self._clean_text(pt_text)
                libras_clean = self._clean_gloss(libras_gloss)
                
                # Adicionar mapeamento de frase completa
                self.phrase_mappings[pt_clean] = libras_clean
                
                # Extrair mapeamentos palavra-palavra quando possível
                self._extract_word_mappings(pt_clean, libras_clean)
                
                # Adicionar ao vocabulário
                self.vocabulary.update(pt_clean.split())
                self.vocabulary.update(libras_clean.split())
            
            # Adicionar mapeamentos essenciais
            self._add_essential_mappings()
            
            logger.info(f"✅ Dados construídos:")
            logger.info(f"   📝 {len(self.word_dict)} mapeamentos de palavras")
            logger.info(f"   💬 {len(self.phrase_mappings)} mapeamentos de frases")
            logger.info(f"   📚 {len(self.vocabulary)} palavras no vocabulário")
            
        except Exception as e:
            logger.error(f"❌ Erro ao construir dados: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Limpa texto português"""
        # Remover pontuação e caracteres especiais
        text = re.sub(r'[^\w\s]', ' ', text)
        # Normalizar espaços
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _clean_gloss(self, gloss: str) -> str:
        """Limpa gloss LIBRAS"""
        # Remover colchetes e normalizar
        gloss = re.sub(r'\[([^\]]+)\]', r'\\1', gloss)
        gloss = re.sub(r'\s+', ' ', gloss)
        return gloss.strip()
    
    def _extract_word_mappings(self, pt_text: str, libras_gloss: str) -> None:
        """Extrai mapeamentos palavra-palavra"""
        pt_words = pt_text.split()
        libras_words = libras_gloss.split()
        
        # Para frases simples (1-3 palavras), criar mapeamentos diretos
        if len(pt_words) <= 3 and len(libras_words) <= 5:
            for i, pt_word in enumerate(pt_words):
                if i < len(libras_words) and len(pt_word) > 2:
                    # Verificar se é um bom mapeamento
                    libras_word = libras_words[i]
                    if self._is_good_mapping(pt_word, libras_word):
                        self.word_dict[pt_word] = libras_word
    
    def _is_good_mapping(self, pt_word: str, libras_word: str) -> bool:
        """Verifica se um mapeamento é válido"""
        # Evitar mapeamentos óbvios demais ou muito diferentes
        if len(pt_word) < 2 or len(libras_word) < 2:
            return False
        
        # Palavras muito similares (podem ser cognatos)
        if pt_word.upper() == libras_word:
            return True
        
        # Evitar palavras de função muito comuns
        stop_words = {'de', 'da', 'do', 'em', 'na', 'no', 'a', 'o', 'e', 'ou', 'se', 'que'}
        if pt_word in stop_words:
            return False
        
        return True
    
    def _add_essential_mappings(self) -> None:
        """Adiciona mapeamentos essenciais"""
        essential_words = {
            'quero': 'QUERER',
            'agua': 'AGUA',
            'água': 'AGUA',
            'beber': 'BEBER',
            'comer': 'COMER',
            'casa': 'CASA',
            'bom': 'BOM',
            'dia': 'DIA',
            'noite': 'NOITE',
            'obrigado': 'OBRIGADO',
            'obrigada': 'OBRIGADO',
            'por': 'POR',
            'favor': 'FAVOR',
            'oi': 'OI',
            'tchau': 'TCHAU',
            'como': 'COMO',
            'vai': 'VAI',
            'você': 'VOCÊ',
            'eu': 'EU',
            'meu': 'MEU',
            'nome': 'NOME',
            'gosto': 'GOSTAR',
            'muito': 'MUITO',
            'onde': 'ONDE',
            'fica': 'FICAR',
            'banheiro': 'BANHEIRO',
            'preciso': 'PRECISAR',
            'ajuda': 'AJUDA',
            'tudo': 'TUDO',
            'bem': 'BEM',
            'até': 'ATÉ',
            'logo': 'LOGO',
            'boa': 'BOA'
        }
        
        # Adicionar apenas se não existir
        for pt, libras in essential_words.items():
            if pt not in self.word_dict:
                self.word_dict[pt] = libras
        
        # Mapeamentos de frases essenciais
        essential_phrases = {
            'bom dia': 'BOM DIA',
            'boa noite': 'BOA NOITE',
            'boa tarde': 'BOA TARDE',
            'por favor': 'POR FAVOR',
            'muito obrigado': 'MUITO OBRIGADO',
            'como vai': 'COMO VAI',
            'tudo bem': 'TUDO BEM',
            'até logo': 'ATÉ LOGO',
            'quero agua': 'QUERER AGUA',
            'preciso de ajuda': 'PRECISAR AJUDA'
        }
        
        for pt, libras in essential_phrases.items():
            if pt not in self.phrase_mappings:
                self.phrase_mappings[pt] = libras
    
    def save_mappings(self, output_path: str = 'translation_mappings.pkl') -> None:
        """Salva mapeamentos em arquivo"""
        try:
            data = {
                'word_dict': self.word_dict,
                'phrase_mappings': self.phrase_mappings,
                'vocabulary': list(self.vocabulary)
            }
            
            with open(output_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"💾 Mapeamentos salvos em: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mapeamentos: {e}")
            raise
    
    def generate_statistics(self) -> Dict:
        """Gera estatísticas dos dados"""
        stats = {
            'total_words': len(self.word_dict),
            'total_phrases': len(self.phrase_mappings),
            'vocabulary_size': len(self.vocabulary),
            'coverage_analysis': self._analyze_coverage()
        }
        return stats
    
    def _analyze_coverage(self) -> Dict:
        """Analisa cobertura dos mapeamentos"""
        # Palavras mais comuns
        word_freq = {}
        for phrase in self.phrase_mappings.keys():
            for word in phrase.split():
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top 20 palavras mais comuns
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Calcular cobertura
        covered_words = set(self.word_dict.keys())
        all_words = set(word_freq.keys())
        coverage_rate = len(covered_words) / len(all_words) if all_words else 0
        
        return {
            'coverage_rate': coverage_rate,
            'top_words': top_words,
            'covered_top_words': [(w, f) for w, f in top_words if w in covered_words],
            'missing_top_words': [(w, f) for w, f in top_words if w not in covered_words]
        }

def main():
    """Função principal"""
    print("🚀 ELA PROFESSIONAL DATA BUILDER v5.0")
    print("="*60)
    
    # Criar builder
    builder = ProfessionalDataBuilder()
    
    # Construir dados
    builder.build_from_csv()
    
    # Salvar mapeamentos
    builder.save_mappings()
    
    # Mostrar estatísticas
    stats = builder.generate_statistics()
    
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   📝 Palavras mapeadas: {stats['total_words']}")
    print(f"   💬 Frases mapeadas: {stats['total_phrases']}")
    print(f"   📚 Vocabulário total: {stats['vocabulary_size']}")
    print(f"   📈 Taxa de cobertura: {stats['coverage_analysis']['coverage_rate']:.1%}")
    
    print(f"\n🔝 TOP 10 PALAVRAS MAIS COMUNS:")
    for word, freq in stats['coverage_analysis']['top_words'][:10]:
        status = "✅" if word in builder.word_dict else "❌"
        print(f"   {status} {word}: {freq} vezes")
    
    print(f"\n🎉 DADOS PROFISSIONAIS CONSTRUÍDOS COM SUCESSO!")

if __name__ == "__main__":
    main()