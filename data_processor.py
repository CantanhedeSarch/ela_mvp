#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de dados para o sistema de tradução PT-BR → LIBRAS
Versão refatorada - Outubro 2025
"""

import pandas as pd
import re
import pickle
from collections import Counter
from typing import List, Tuple, Dict, Set

class DataProcessor:
    """Processador inteligente dos dados de treinamento"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.data = None
        self.pt_vocab = {}
        self.libras_vocab = {}
        self.word_mappings = {}
        self.phrase_mappings = {}
        
    def load_data(self) -> pd.DataFrame:
        """Carrega e processa os dados do CSV"""
        print("📊 Carregando dados...")
        self.data = pd.read_csv(self.csv_path)
        print(f"✅ {len(self.data)} amostras carregadas")
        return self.data
    
    def clean_text(self, text: str, is_libras: bool = False) -> str:
        """Limpa e normaliza texto"""
        if pd.isna(text):
            return ""
        
        text = str(text).strip()
        
        if is_libras:
            # Para LIBRAS: manter estrutura de gloss
            text = re.sub(r'\[PONTO\]|\[INTERROGAÇÃO\]|\[EXCLAMAÇÃO\]', '', text)
            text = re.sub(r'&', ' ', text)  # Separar palavras compostas
            text = re.sub(r'\s+', ' ', text)
        else:
            # Para PT-BR: normalização básica
            text = text.lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\d+', ' NUM ', text)
            text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_vocabularies(self) -> Tuple[Dict, Dict]:
        """Extrai vocabulários do PT-BR e LIBRAS"""
        print("📚 Extraindo vocabulários...")
        
        pt_words = []
        libras_words = []
        
        for _, row in self.data.iterrows():
            # Processar PT-BR
            pt_clean = self.clean_text(row['pt-br'], False)
            pt_words.extend(pt_clean.split())
            
            # Processar LIBRAS
            libras_clean = self.clean_text(row['libras-gloss'], True)
            libras_words.extend(libras_clean.split())
        
        # Criar vocabulários com frequências
        pt_counter = Counter(pt_words)
        libras_counter = Counter(libras_words)
        
        # Filtrar palavras muito raras (frequência < 2)
        self.pt_vocab = {word: freq for word, freq in pt_counter.items() if freq >= 2}
        self.libras_vocab = {word: freq for word, freq in libras_counter.items() if freq >= 2}
        
        print(f"✅ Vocabulário PT-BR: {len(self.pt_vocab)} palavras")
        print(f"✅ Vocabulário LIBRAS: {len(self.libras_vocab)} palavras")
        
        return self.pt_vocab, self.libras_vocab
    
    def create_mappings(self) -> Tuple[Dict, Dict]:
        """Cria mapeamentos inteligentes PT-BR → LIBRAS"""
        print("🔗 Criando mapeamentos...")
        
        word_mappings = {}
        phrase_mappings = {}
        
        for _, row in self.data.iterrows():
            pt_text = self.clean_text(row['pt-br'], False)
            libras_text = self.clean_text(row['libras-gloss'], True)
            
            pt_words = pt_text.split()
            libras_words = libras_text.split()
            
            # Mapeamento de frases completas
            if len(pt_words) <= 5 and len(libras_words) <= 5:
                phrase_mappings[pt_text] = libras_text
            
            # Mapeamentos de palavras individuais
            if len(pt_words) == 1 and len(libras_words) == 1:
                pt_word = pt_words[0]
                libras_word = libras_words[0]
                
                if pt_word not in word_mappings:
                    word_mappings[pt_word] = []
                word_mappings[pt_word].append(libras_word)
        
        # Consolidar mapeamentos de palavras (pegar o mais frequente)
        self.word_mappings = {}
        for pt_word, libras_list in word_mappings.items():
            counter = Counter(libras_list)
            self.word_mappings[pt_word] = counter.most_common(1)[0][0]
        
        self.phrase_mappings = phrase_mappings
        
        print(f"✅ {len(self.word_mappings)} mapeamentos de palavras")
        print(f"✅ {len(self.phrase_mappings)} mapeamentos de frases")
        
        return self.word_mappings, self.phrase_mappings
    
    def get_common_words(self, n: int = 100) -> Tuple[List[str], List[str]]:
        """Retorna as palavras mais comuns de cada vocabulário"""
        pt_common = [word for word, _ in Counter(self.pt_vocab).most_common(n)]
        libras_common = [word for word, _ in Counter(self.libras_vocab).most_common(n)]
        return pt_common, libras_common
    
    def save_mappings(self, filepath: str):
        """Salva mapeamentos em arquivo"""
        mappings_data = {
            'word_mappings': self.word_mappings,
            'phrase_mappings': self.phrase_mappings,
            'pt_vocab': self.pt_vocab,
            'libras_vocab': self.libras_vocab
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(mappings_data, f)
        
        print(f"✅ Mapeamentos salvos em {filepath}")
    
    def load_mappings(self, filepath: str):
        """Carrega mapeamentos de arquivo"""
        with open(filepath, 'rb') as f:
            mappings_data = pickle.load(f)
        
        self.word_mappings = mappings_data['word_mappings']
        self.phrase_mappings = mappings_data['phrase_mappings']
        self.pt_vocab = mappings_data['pt_vocab']
        self.libras_vocab = mappings_data['libras_vocab']
        
        print(f"✅ Mapeamentos carregados de {filepath}")

if __name__ == "__main__":
    # Processar dados
    processor = DataProcessor('data/pt-br2libras-gloss_sample_500.csv')
    processor.load_data()
    processor.extract_vocabularies()
    processor.create_mappings()
    
    # Salvar mapeamentos
    processor.save_mappings('models/mappings.pkl')
    
    # Mostrar algumas estatísticas
    print("\n📊 ESTATÍSTICAS:")
    print(f"PT-BR mais comuns: {list(processor.pt_vocab.keys())[:10]}")
    print(f"LIBRAS mais comuns: {list(processor.libras_vocab.keys())[:10]}")
    
    print("\n🔗 ALGUNS MAPEAMENTOS:")
    for i, (pt, libras) in enumerate(list(processor.word_mappings.items())[:10]):
        print(f"  {pt} → {libras}")