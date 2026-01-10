# Modelo de Análisis de Sentimientos

## 📊 Información del Modelo

- **Tipo de Modelo:** Naive Bayes
- **Fecha de Entrenamiento:** 2026-01-01 20:48:41
- **F1-Score:** 0.9652

## 📈 Métricas de Evaluación (Test Set)

- **Accuracy:** 0.9387
- **Precision:** 0.9693
- **Recall:** 0.9612
- **F1-Score:** 0.9652

## 📦 Archivos Necesarios

1. **sentiment_model.pkl** - Modelo entrenado
2. **tfidf_vectorizer.pkl** - Vectorizador TF-IDF
3. **model_metadata.json** - Metadata del modelo

## 🔧 Cómo Usar en Python

```python
import joblib

# Cargar modelo y vectorizador
modelo = joblib.load('modelos_serializados/sentiment_model.pkl')
vectorizador = joblib.load('modelos_serializados/tfidf_vectorizer.pkl')

# Función de limpieza (copiar del notebook)
def limpiar_texto(texto):
    import re
    import string
    texto = texto.lower()
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto)
    texto = re.sub(r'@\w+', '', texto)
    texto = re.sub(r'#\w+', '', texto)
    texto = re.sub(r'\d+', '', texto)
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

# Hacer predicción
texto_nuevo = "Este hotel es excelente"
texto_limpio = limpiar_texto(texto_nuevo)
texto_vectorizado = vectorizador.transform([texto_limpio])
prediccion = modelo.predict(texto_vectorizado)[0]
probabilidad = modelo.predict_proba(texto_vectorizado)[0]

print(f"Predicción: {prediccion}")
print(f"Probabilidades: Negativo={probabilidad[0]:.2%}, Positivo={probabilidad[1]:.2%}")
```

## 📋 Formato de Respuesta Esperado (JSON)

```json
{
  "prevision": "Positivo",
  "probabilidad": 0.95
}
```

## ⚠️ Importante

- El texto debe ser limpiado ANTES de vectorizar
- El vectorizador espera una lista de strings: `[texto]`
- Las clases son: "Negativo" y "Positivo"
- El orden de probabilidades es: [prob_negativo, prob_positivo]

## 🔄 Preprocesamiento Requerido

El texto debe pasar por las siguientes transformaciones:
1. Convertir a minúsculas
2. Eliminar URLs
3. Eliminar menciones y hashtags
4. Eliminar números
5. Eliminar puntuación
6. Eliminar espacios múltiples

Usar la función `limpiar_texto()` proporcionada arriba.
