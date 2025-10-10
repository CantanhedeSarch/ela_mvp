#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Testing Suite - ELA MVP v5.0
Suite de testes profissional para o sistema com Word2Vec
Autor: ELA Team
Data: Outubro 2025
"""

import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from professional_translator import ProfessionalLibrasTranslator, TranslationResult

class ProfessionalTestSuite:
    """Suite de testes profissional"""
    
    def __init__(self):
        self.translator = None
        self.test_results = []
        self.performance_metrics = {}
    
    def setup(self) -> bool:
        """Configuração inicial dos testes"""
        print("🔧 CONFIGURANDO AMBIENTE DE TESTE PROFISSIONAL")
        print("="*60)
        
        try:
            print("📝 Inicializando tradutor profissional...")
            self.translator = ProfessionalLibrasTranslator()
            print("✅ Tradutor inicializado com sucesso")
            
            # Verificar Word2Vec
            if self.translator.word2vec_engine.model:
                print("🧠 Word2Vec: Modelo carregado")
            else:
                print("⚠️ Word2Vec: Será treinado durante os testes")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            return False
    
    def run_basic_tests(self) -> None:
        """Executa testes básicos de funcionalidade"""
        print("\n🧪 TESTES BÁSICOS DE FUNCIONALIDADE")
        print("-"*60)
        
        basic_tests = [
            {
                "name": "Caso Principal Original",
                "input": "quero agua",
                "expected_contains": "QUERER",
                "min_confidence": 0.4
            },
            {
                "name": "Saudação Simples",
                "input": "bom dia",
                "expected_contains": "BOM DIA",
                "min_confidence": 0.8
            },
            {
                "name": "Agradecimento",
                "input": "obrigado",
                "expected_contains": "OBRIGADO",
                "min_confidence": 0.8
            },
            {
                "name": "Frase Complexa",
                "input": "eu gosto muito de você",
                "expected_contains": "EU",
                "min_confidence": 0.5
            },
            {
                "name": "Pergunta",
                "input": "como você está?",
                "expected_contains": "COMO",
                "min_confidence": 0.4
            }
        ]
        
        passed = 0
        total = len(basic_tests)
        
        for i, test in enumerate(basic_tests, 1):
            print(f"\n🔹 Teste {i}/{total}: {test['name']}")
            print(f"   Input: '{test['input']}'")
            
            start_time = time.time()
            result = self.translator.translate(test['input'])
            test_time = time.time() - start_time
            
            print(f"   Output: '{result.output_gloss}'")
            print(f"   Método: {result.method}")
            print(f"   Confiança: {result.confidence:.2%}")
            print(f"   Tempo: {test_time:.4f}s")
            
            # Verificar critérios
            contains_expected = test['expected_contains'] in result.output_gloss
            confidence_ok = result.confidence >= test['min_confidence']
            performance_ok = test_time < 1.0  # Máximo 1 segundo
            
            if contains_expected and confidence_ok and performance_ok:
                print("   ✅ PASSOU")
                passed += 1
            else:
                print("   ❌ FALHOU")
                if not contains_expected:
                    print(f"      - Não contém '{test['expected_contains']}'")
                if not confidence_ok:
                    print(f"      - Confiança baixa: {result.confidence:.2%} < {test['min_confidence']:.2%}")
                if not performance_ok:
                    print(f"      - Muito lento: {test_time:.4f}s > 1.0s")
            
            # Armazenar resultado
            self.test_results.append({
                "test_name": test['name'],
                "input": test['input'],
                "output": result.output_gloss,
                "confidence": result.confidence,
                "method": result.method,
                "processing_time": test_time,
                "passed": contains_expected and confidence_ok and performance_ok
            })
        
        print(f"\n📊 RESULTADO DOS TESTES BÁSICOS:")
        print(f"✅ Passou: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"❌ Falhou: {total-passed}/{total}")
    
    def run_word2vec_tests(self) -> None:
        """Testa funcionalidades específicas do Word2Vec"""
        print("\n🧠 TESTES DO WORD2VEC SEMÂNTICO")
        print("-"*60)
        
        if not self.translator.word2vec_engine.model:
            print("⚠️ Word2Vec não disponível - pulando testes semânticos")
            return
        
        semantic_tests = [
            {
                "word1": "agua",
                "word2": "beber",
                "context": "Palavras relacionadas"
            },
            {
                "word1": "casa",
                "word2": "lar",
                "context": "Sinônimos"
            },
            {
                "word1": "correr",
                "word2": "andar",
                "context": "Verbos de movimento"
            }
        ]
        
        for i, test in enumerate(semantic_tests, 1):
            print(f"\n🔹 Teste Semântico {i}: {test['context']}")
            
            similarity = self.translator.word2vec_engine.get_similarity(
                test['word1'], test['word2']
            )
            
            print(f"   '{test['word1']}' ↔ '{test['word2']}'")
            print(f"   Similaridade: {similarity:.4f}")
            
            if similarity > 0.3:
                print("   ✅ Boa similaridade semântica")
            elif similarity > 0.1:
                print("   ⚠️ Similaridade moderada")
            else:
                print("   ❌ Baixa similaridade")
            
            # Buscar palavras similares
            similar_words = self.translator.word2vec_engine.find_similar_words(
                test['word1'], topn=3
            )
            
            if similar_words:
                print(f"   Palavras similares a '{test['word1']}':")
                for word, sim in similar_words:
                    print(f"     - {word}: {sim:.4f}")
    
    def run_performance_tests(self) -> None:
        """Testes de performance"""
        print("\n⚡ TESTES DE PERFORMANCE")
        print("-"*60)
        
        # Teste de throughput
        print("🚀 Teste de Throughput:")
        
        test_texts = [
            "oi", "tchau", "obrigado", "por favor", "bom dia",
            "como vai", "tudo bem", "até logo", "boa noite"
        ]
        
        start_time = time.time()
        results = []
        
        for text in test_texts:
            result = self.translator.translate(text)
            results.append(result)
        
        total_time = time.time() - start_time
        throughput = len(test_texts) / total_time
        
        print(f"   📊 {len(test_texts)} traduções em {total_time:.4f}s")
        print(f"   📈 Throughput: {throughput:.2f} traduções/segundo")
        
        # Teste de latência
        print("\n⏱️ Teste de Latência:")
        
        latencies = []
        for text in ["teste rápido", "frase um pouco mais longa para teste"]:
            start = time.time()
            self.translator.translate(text)
            latency = time.time() - start
            latencies.append(latency)
            print(f"   '{text}': {latency:.4f}s")
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"   📊 Latência média: {avg_latency:.4f}s")
        
        # Armazenar métricas
        self.performance_metrics = {
            "throughput": throughput,
            "average_latency": avg_latency,
            "total_test_time": total_time
        }
    
    def run_quality_tests(self) -> None:
        """Testes de qualidade de tradução"""
        print("\n📊 TESTES DE QUALIDADE")
        print("-"*60)
        
        quality_tests = [
            {
                "input": "eu preciso de ajuda",
                "context": "Pedido de ajuda",
                "min_quality": 0.6
            },
            {
                "input": "onde fica o banheiro?",
                "context": "Pergunta de localização",
                "min_quality": 0.5
            },
            {
                "input": "meu nome é João",
                "context": "Apresentação pessoal",
                "min_quality": 0.7
            }
        ]
        
        quality_scores = []
        
        for i, test in enumerate(quality_tests, 1):
            print(f"\n🔹 Teste de Qualidade {i}: {test['context']}")
            print(f"   Input: '{test['input']}'")
            
            result = self.translator.translate(test['input'])
            analytics = self.translator.get_translation_analytics(test['input'])
            
            quality_score = analytics['translation_quality']['quality_score']
            quality_scores.append(quality_score)
            
            print(f"   Output: '{result.output_gloss}'")
            print(f"   Score de Qualidade: {quality_score:.2%}")
            print(f"   Método: {result.method}")
            
            if quality_score >= test['min_quality']:
                print("   ✅ Qualidade aceitável")
            else:
                print("   ⚠️ Qualidade abaixo do esperado")
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        print(f"\n📊 Qualidade média: {avg_quality:.2%}")
    
    def generate_report(self) -> None:
        """Gera relatório final dos testes"""
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DOS TESTES")
        print("="*60)
        
        # Estatísticas gerais
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t['passed'])
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print(f"   Total de testes: {total_tests}")
        print(f"   Testes aprovados: {passed_tests}")
        print(f"   Taxa de sucesso: {success_rate:.1%}")
        
        # Performance
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Throughput: {self.performance_metrics['throughput']:.2f} trad/s")
            print(f"   Latência média: {self.performance_metrics['average_latency']:.4f}s")
        
        # Métodos utilizados
        methods = {}
        for result in self.test_results:
            method = result['method']
            methods[method] = methods.get(method, 0) + 1
        
        print(f"\n🔧 MÉTODOS UTILIZADOS:")
        for method, count in methods.items():
            print(f"   {method}: {count} vezes")
        
        # Confiança média
        confidences = [r['confidence'] for r in self.test_results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        print(f"\n📈 CONFIANÇA MÉDIA: {avg_confidence:.1%}")
        
        # Conclusão
        print(f"\n🏆 CONCLUSÃO:")
        if success_rate >= 0.8:
            print("   ✅ SISTEMA APROVADO - Excelente performance")
        elif success_rate >= 0.6:
            print("   ⚠️ SISTEMA ACEITÁVEL - Melhorias recomendadas")
        else:
            print("   ❌ SISTEMA REPROVADO - Correções necessárias")
        
        # Salvar relatório
        self._save_report()
    
    def _save_report(self) -> None:
        """Salva relatório em arquivo"""
        report_data = {
            "timestamp": time.time(),
            "version": "5.0.0",
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for t in self.test_results if t['passed']),
                "success_rate": sum(1 for t in self.test_results if t['passed']) / len(self.test_results) if self.test_results else 0
            }
        }
        
        try:
            with open('logs/test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Relatório salvo em: logs/test_report.json")
        
        except Exception as e:
            print(f"\n⚠️ Erro ao salvar relatório: {e}")

def main():
    """Função principal dos testes"""
    print("🚀 ELA MVP v5.0 - SUITE DE TESTES PROFISSIONAL")
    print("="*60)
    
    # Inicializar suite
    suite = ProfessionalTestSuite()
    
    if not suite.setup():
        print("❌ Falha na configuração. Abortando testes.")
        sys.exit(1)
    
    try:
        # Executar testes
        suite.run_basic_tests()
        suite.run_word2vec_tests()
        suite.run_performance_tests()
        suite.run_quality_tests()
        
        # Gerar relatório
        suite.generate_report()
        
        print(f"\n🎉 TESTES CONCLUÍDOS COM SUCESSO!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()