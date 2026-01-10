
# ============================================
# FUNCIÓN MULTILINGÜE PARA BACK-END
# ============================================

from googletrans import Translator
import re
import string
import joblib

# Cargar modelo y vectorizador
modelo = joblib.load('sentiment_model.pkl')
vectorizador = joblib.load('tfidf_vectorizer.pkl')
translator = Translator()

def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto)
    texto = re.sub(r'@\w+', '', texto)
    texto = re.sub(r'#\w+', '', texto)
    texto = re.sub(r'\d+', '', texto)
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def predecir_sentimiento_api(texto, idioma='auto'):
    '''
    Endpoint para predicción multilingüe

    Args:
        texto (str): Texto a analizar
        idioma (str): Código ISO del idioma ('auto' para detección)

    Returns:
        dict: {
            "prevision": "Positivo" o "Negativo",
            "probabilidad": float (0-1),
            "idioma_detectado": str,
            "traduccion_exitosa": bool
        }
    '''

    # Traducir si no es español
    if idioma != 'es':
        try:
            traduccion = translator.translate(texto, src=idioma, dest='es')
            texto_es = traduccion.text
            idioma_detectado = traduccion.src
            traduccion_ok = True
        except:
            texto_es = texto
            idioma_detectado = 'desconocido'
            traduccion_ok = False
    else:
        texto_es = texto
        idioma_detectado = 'es'
        traduccion_ok = True

    # Predecir
    texto_limpio = limpiar_texto(texto_es)
    texto_vectorizado = vectorizador.transform([texto_limpio])
    prediccion = modelo.predict(texto_vectorizado)[0]
    probabilidades = modelo.predict_proba(texto_vectorizado)[0]

    prob = probabilidades[1] if prediccion == 'Positivo' else probabilidades[0]

    return {
        "prevision": prediccion,
        "probabilidad": float(prob),
        "idioma_detectado": idioma_detectado,
        "traduccion_exitosa": traduccion_ok
    }

# Ejemplo de uso
resultado = predecir_sentimiento_api("This hotel is amazing!", idioma='auto')
print(resultado)
# Output: {"prevision": "Positivo", "probabilidad": 0.95, ...}
