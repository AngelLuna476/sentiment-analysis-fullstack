
# ============================================
# FUNCIÓN DE EXPLICABILIDAD PARA PRODUCCIÓN
# ============================================

def predecir_con_explicacion(texto, modelo, vectorizador, top_features=5):
    """
    Predice sentimiento con explicación de palabras influyentes.

    Returns:
        {
            "prevision": "Positivo" o "Negativo",
            "probabilidad": float,
            "palabras_influyentes": [
                {"palabra": str, "influencia": float},
                ...
            ]
        }
    """
    import re
    import string

    # Limpiar texto
    texto_limpio = texto.lower()
    texto_limpio = re.sub(r'http\S+|www\S+|https\S+', '', texto_limpio)
    texto_limpio = re.sub(r'@\w+|#\w+|\d+', '', texto_limpio)
    texto_limpio = texto_limpio.translate(str.maketrans('', '', string.punctuation))
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()

    # Vectorizar
    texto_vec = vectorizador.transform([texto_limpio])

    # Predecir
    prediccion = modelo.predict(texto_vec)[0]
    probabilidades = modelo.predict_proba(texto_vec)[0]

    # Obtener coeficientes
    if hasattr(modelo, 'feature_log_prob_'):
        coef = modelo.feature_log_prob_[1] - modelo.feature_log_prob_[0]
    else:
        coef = modelo.coef_[0]

    # Features presentes
    feature_names = vectorizador.get_feature_names_out()
    indices = texto_vec.nonzero()[1]

    # Calcular influencias
    palabras_influyentes = []
    for idx in indices:
        influencia = texto_vec[0, idx] * coef[idx]
        palabras_influyentes.append({
            "palabra": feature_names[idx],
            "influencia": float(influencia)
        })

    # Ordenar por influencia absoluta
    palabras_influyentes.sort(key=lambda x: abs(x['influencia']), reverse=True)

    return {
        "prevision": prediccion,
        "probabilidad": float(probabilidades[1] if prediccion == 'Positivo' else probabilidades[0]),
        "palabras_influyentes": palabras_influyentes[:top_features]
    }
