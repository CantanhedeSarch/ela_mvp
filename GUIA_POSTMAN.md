# 🚀 GUIA DE TESTE NO POSTMAN - ELA MVP v4.0

## ✅ **API RODANDO EM:** `http://127.0.0.1:8082`

---

## 📋 **CONFIGURAÇÃO NO POSTMAN**

### **1. TESTE DE DOCUMENTAÇÃO (GET)**
```
Método: GET
URL: http://127.0.0.1:8082/
Headers: (nenhum necessário)
Body: (vazio)
```
**Resultado esperado:** Documentação da API em JSON

---

### **2. TESTE DE SAÚDE (GET)**
```
Método: GET
URL: http://127.0.0.1:8082/health
Headers: (nenhum necessário)
Body: (vazio)
```
**Resultado esperado:** Status da API e informações do sistema

---

### **3. TRADUÇÃO PRINCIPAL (POST)**
```
Método: POST
URL: http://127.0.0.1:8082/translate
Headers: 
  Content-Type: application/json
Body (raw JSON):
  {"text": "quero agua"}
```
**Resultado esperado:**
```json
{
  "success": true,
  "input": {
    "text": "quero agua",
    "language": "pt-br"
  },
  "output": {
    "gloss": "QUERER AGUA",
    "language": "libras-gloss"
  },
  "metadata": {
    "method": "word_mapping",
    "confidence": 0.5,
    "translation_time": 0.001,
    "model_version": "4.0.0",
    "timestamp": 1728477123.456
  }
}
```

---

## 🧪 **CASOS DE TESTE RECOMENDADOS**

### **Teste 1: Caso Principal**
```json
{"text": "quero agua"}
```
**Esperado:** `"QUERER AGUA"`

### **Teste 2: Saudação**
```json
{"text": "bom dia"}
```
**Esperado:** `"BOM DIA"`

### **Teste 3: Agradecimento**
```json
{"text": "obrigado"}
```
**Esperado:** `"OBRIGADO"`

### **Teste 4: Frase Complexa**
```json
{"text": "eu gosto de você"}
```
**Esperado:** `"EU GOSTAR DE VOCÊ"`

### **Teste 5: Despedida**
```json
{"text": "tchau"}
```
**Esperado:** `"TCHAU"`

### **Teste 6: Com Debug**
```json
{"text": "oi", "debug": true}
```
**Esperado:** Resposta com informações de debug

---

## ❌ **TESTES DE ERRO**

### **Teste 7: Texto Vazio**
```json
{"text": ""}
```
**Esperado:** Erro 400

### **Teste 8: Campo Ausente**
```json
{"nome": "teste"}
```
**Esperado:** Erro 400

### **Teste 9: JSON Inválido**
```
Body: texto inválido
```
**Esperado:** Erro 400

---

## 📊 **ENDPOINT ALTERNATIVO**

### **Tradução em Português (POST)**
```
Método: POST
URL: http://127.0.0.1:8082/traduzir
Headers: 
  Content-Type: application/json
Body (raw JSON):
  {"text": "por favor"}
```

---

## 🔧 **IMPORTAR COLEÇÃO POSTMAN**

Se você tiver o arquivo `ELA_MVP_Postman_Collection.json`, pode importá-lo diretamente no Postman:

1. Abrir Postman
2. File → Import
3. Selecionar `ELA_MVP_Postman_Collection.json`
4. Todos os testes estarão prontos!

---

## 🏆 **RESULTADOS ESPERADOS**

### ✅ **Sucessos:**
- Status 200 para requests válidos
- Campo `"success": true`
- Tradução correta no campo `output.gloss`
- Metadados com confiança e método

### ❌ **Erros:**
- Status 400 para requests inválidos
- Campo `"success": false`
- Mensagem de erro descritiva

---

## 🎯 **VERIFICAÇÃO RÁPIDA**

**API está funcionando se:**
1. ✅ GET `/` retorna documentação
2. ✅ GET `/health` retorna status "healthy"
3. ✅ POST `/translate` com `{"text": "quero agua"}` retorna `"QUERER AGUA"`

---

**🌟 ELA MVP v4.0 - PRONTO PARA TESTE NO POSTMAN!**