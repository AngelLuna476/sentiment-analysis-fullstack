
import streamlit as st
import joblib
import re
import string
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Sentimientos",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FUNCIONES AUXILIARES
# ============================================

@st.cache_resource
def cargar_modelo():
    """Carga el modelo y vectorizador (se cachea para eficiencia)"""
    try:
        modelo = joblib.load('modelos_serializados/sentiment_model.pkl')
        vectorizador = joblib.load('modelos_serializados/tfidf_vectorizer.pkl')
        return modelo, vectorizador
    except Exception as e:
        st.error(f"Error al cargar el modelo: {e}")
        return None, None

def limpiar_texto(texto):
    """Limpia el texto para análisis"""
    texto = texto.lower()
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto)
    texto = re.sub(r'@\w+', '', texto)
    texto = re.sub(r'#\w+', '', texto)
    texto = re.sub(r'\d+', '', texto)
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def predecir_sentimiento(texto, modelo, vectorizador, threshold=0.5):
    """Predice el sentimiento con threshold personalizable"""
    texto_limpio = limpiar_texto(texto)

    if len(texto_limpio) < 3:
        return None, "Texto demasiado corto"

    texto_vec = vectorizador.transform([texto_limpio])
    prediccion = modelo.predict(texto_vec)[0]
    probabilidades = modelo.predict_proba(texto_vec)[0]

    prob_positivo = probabilidades[1]

    if prob_positivo > threshold:
        prediccion_final = "Positivo"
        prob_final = prob_positivo
    else:
        prediccion_final = "Negativo"
        prob_final = probabilidades[0]

    return {
        'prediccion': prediccion_final,
        'probabilidad': prob_final,
        'prob_positivo': prob_positivo,
        'prob_negativo': probabilidades[0]
    }, None

def obtener_palabras_influyentes(texto, modelo, vectorizador, top_n=5):
    """Obtiene las palabras más influyentes"""
    texto_limpio = limpiar_texto(texto)
    texto_vec = vectorizador.transform([texto_limpio])

    # Obtener coeficientes
    if hasattr(modelo, 'feature_log_prob_'):
        coef = modelo.feature_log_prob_[1] - modelo.feature_log_prob_[0]
    else:
        coef = modelo.coef_[0]

    feature_names = vectorizador.get_feature_names_out()
    indices = texto_vec.nonzero()[1]

    palabras = []
    for idx in indices:
        influencia = texto_vec[0, idx] * coef[idx]
        palabras.append({
            'palabra': feature_names[idx],
            'influencia': float(influencia)
        })

    palabras.sort(key=lambda x: abs(x['influencia']), reverse=True)
    return palabras[:top_n]

# ============================================
# CARGAR MODELO
# ============================================

modelo, vectorizador = cargar_modelo()

if modelo is None or vectorizador is None:
    st.error("⚠️ No se pudo cargar el modelo. Asegúrate de que los archivos .pkl están en la carpeta 'modelos_serializados/'")
    st.stop()

# ============================================
# INTERFAZ PRINCIPAL
# ============================================

# Header
st.title("💬 Análisis de Sentimientos")
st.markdown("### Analiza el sentimiento de textos en tiempo real")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")

    # Threshold
    threshold = st.slider(
        "Umbral de decisión (Threshold)",
        min_value=0.1,
        max_value=0.9,
        value=0.5,
        step=0.1,
        help="Ajusta el umbral para clasificar como Positivo"
    )

    st.info(f"📊 Threshold actual: {threshold:.1f}")

    if threshold < 0.4:
        st.warning("🔍 Threshold bajo: Más sensible, detecta más positivos")
    elif threshold > 0.6:
        st.warning("🔒 Threshold alto: Más conservador, solo positivos claros")
    else:
        st.success("✅ Threshold balanceado")

    st.markdown("---")

    # Explicabilidad
    mostrar_explicacion = st.checkbox("Mostrar explicabilidad", value=True)

    if mostrar_explicacion:
        num_palabras = st.slider("Palabras influyentes", 3, 10, 5)

    st.markdown("---")

    # Info del modelo
    st.header("📊 Info del Modelo")
    st.metric("Modelo", "Naive Bayes")
    st.metric("F1-Score", "96.52%")
    st.metric("Accuracy", "93.87%")

    st.markdown("---")
    st.markdown("**Desarrollado por:** Equipo H12-25-L-31")
    st.markdown("**Dataset:** Punta Cana Reviews")

# Tabs principales
tab1, tab2, tab3 = st.tabs(["🔍 Análisis Simple", "📊 Análisis Batch", "📈 Estadísticas"])

# ============================================
# TAB 1: ANÁLISIS SIMPLE
# ============================================

with tab1:
    st.header("Analiza un texto")

    # Input de texto
    texto_input = st.text_area(
        "Escribe o pega tu texto aquí:",
        height=150,
        placeholder="Ejemplo: Este hotel es excelente, me encantó la comida y el servicio..."
    )

    # Ejemplos rápidos
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Ejemplo Positivo"):
            texto_input = "Este hotel es excelente, las habitaciones son limpias y el personal muy amable"

    with col2:
        if st.button("📝 Ejemplo Negativo"):
            texto_input = "Hotel horrible, todo sucio y el servicio pésimo"

    with col3:
        if st.button("📝 Ejemplo Ambiguo"):
            texto_input = "El hotel está bien, tiene cosas buenas pero también algunos problemas"

    st.markdown("---")

    # Botón de análisis
    if st.button("🚀 Analizar Sentimiento", type="primary", use_container_width=True):
        if not texto_input or len(texto_input.strip()) < 3:
            st.warning("⚠️ Por favor, escribe un texto para analizar")
        else:
            with st.spinner("Analizando..."):
                resultado, error = predecir_sentimiento(texto_input, modelo, vectorizador, threshold)

                if error:
                    st.error(f"❌ Error: {error}")
                else:
                    # Resultados
                    st.success("✅ Análisis completado")

                    # Métricas principales
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        sentimiento = resultado['prediccion']
                        color = "🟢" if sentimiento == "Positivo" else "🔴"
                        st.metric(
                            "Sentimiento",
                            f"{color} {sentimiento}",
                            delta=None
                        )

                    with col2:
                        prob = resultado['probabilidad']
                        st.metric(
                            "Probabilidad",
                            f"{prob:.1%}",
                            delta=None
                        )

                    with col3:
                        if prob >= 0.9:
                            confianza = "Muy Alta"
                        elif prob >= 0.75:
                            confianza = "Alta"
                        elif prob >= 0.6:
                            confianza = "Media"
                        else:
                            confianza = "Baja"
                        st.metric("Confianza", confianza)

                    st.markdown("---")

                    # Gráfico de probabilidades
                    st.subheader("📊 Distribución de Probabilidades")

                    fig = go.Figure(data=[
                        go.Bar(
                            x=['Negativo', 'Positivo'],
                            y=[resultado['prob_negativo'], resultado['prob_positivo']],
                            marker_color=['#e74c3c', '#2ecc71'],
                            text=[f"{resultado['prob_negativo']:.1%}", f"{resultado['prob_positivo']:.1%}"],
                            textposition='auto',
                        )
                    ])

                    fig.update_layout(
                        yaxis_title="Probabilidad",
                        yaxis_range=[0, 1],
                        height=300,
                        showlegend=False
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Explicabilidad
                    if mostrar_explicacion:
                        st.markdown("---")
                        st.subheader("💡 Explicabilidad")
                        st.markdown("**Palabras más influyentes en esta predicción:**")

                        palabras = obtener_palabras_influyentes(texto_input, modelo, vectorizador, num_palabras)

                        if palabras:
                            palabras_pos = [p for p in palabras if p['influencia'] > 0]
                            palabras_neg = [p for p in palabras if p['influencia'] < 0]

                            col1, col2 = st.columns(2)

                            with col1:
                                if palabras_pos:
                                    st.markdown("**✅ Palabras Positivas:**")
                                    for p in palabras_pos:
                                        st.markdown(f"- `{p['palabra']}` (influencia: {p['influencia']:+.3f})")
                                else:
                                    st.info("No hay palabras con influencia positiva")

                            with col2:
                                if palabras_neg:
                                    st.markdown("**❌ Palabras Negativas:**")
                                    for p in palabras_neg:
                                        st.markdown(f"- `{p['palabra']}` (influencia: {p['influencia']:+.3f})")
                                else:
                                    st.info("No hay palabras con influencia negativa")

# ============================================
# TAB 2: ANÁLISIS BATCH
# ============================================

with tab2:
    st.header("Análisis de múltiples textos")

    st.markdown("""
    Analiza varios textos a la vez. Ingresa un texto por línea.
    """)

    textos_batch = st.text_area(
        "Textos (uno por línea):",
        height=200,
        placeholder="Este hotel es excelente\nEl servicio es horrible\nLa comida está bien"
    )

    if st.button("🚀 Analizar Todos", type="primary"):
        if textos_batch:
            lineas = [l.strip() for l in textos_batch.split('\n') if l.strip()]

            if lineas:
                resultados = []

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, texto in enumerate(lineas):
                    resultado, error = predecir_sentimiento(texto, modelo, vectorizador, threshold)

                    if not error and resultado:
                        resultados.append({
                            'Texto': texto[:50] + '...' if len(texto) > 50 else texto,
                            'Sentimiento': resultado['prediccion'],
                            'Probabilidad': f"{resultado['probabilidad']:.1%}"
                        })

                    progress_bar.progress((i + 1) / len(lineas))
                    status_text.text(f"Procesando {i + 1}/{len(lineas)}...")

                progress_bar.empty()
                status_text.empty()

                # Mostrar resultados
                st.success(f"✅ {len(resultados)} textos analizados")

                df_resultados = pd.DataFrame(resultados)
                st.dataframe(df_resultados, use_container_width=True)

                # Estadísticas
                col1, col2 = st.columns(2)

                with col1:
                    positivos = sum(1 for r in resultados if r['Sentimiento'] == 'Positivo')
                    st.metric("Positivos", positivos)

                with col2:
                    negativos = len(resultados) - positivos
                    st.metric("Negativos", negativos)

                # Gráfico
                fig = go.Figure(data=[
                    go.Pie(
                        labels=['Positivo', 'Negativo'],
                        values=[positivos, negativos],
                        marker_colors=['#2ecc71', '#e74c3c']
                    )
                ])

                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

                # Descargar resultados
                csv = df_resultados.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar Resultados (CSV)",
                    data=csv,
                    file_name=f"analisis_sentimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

# ============================================
# TAB 3: ESTADÍSTICAS
# ============================================

with tab3:
    st.header("📈 Estadísticas del Modelo")

    st.markdown("""
    ### Información del Modelo

    **Modelo:** Naive Bayes (MultinomialNB)
    **Vectorización:** TF-IDF (5000 features, bigramas)
    **Dataset:** Punta Cana Hotels Reviews (33K+ reseñas)
    **Idioma:** Español
    """)

    st.markdown("---")

    # Métricas del modelo
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Accuracy", "93.87%", delta="+2.3%")

    with col2:
        st.metric("Precision", "96.93%", delta="+1.1%")

    with col3:
        st.metric("Recall", "96.12%", delta="+0.8%")

    with col4:
        st.metric("F1-Score", "96.52%", delta="+1.5%")

    st.markdown("---")

    # Gráfico de métricas
    st.subheader("Comparación de Modelos")

    modelos_data = pd.DataFrame({
        'Modelo': ['Naive Bayes', 'Logistic Regression'],
        'Accuracy': [0.9387, 0.9274],
        'Precision': [0.9693, 0.9880],
        'Recall': [0.9612, 0.9291],
        'F1-Score': [0.9652, 0.9577]
    })

    fig = go.Figure()

    for metrica in ['Accuracy', 'Precision', 'Recall', 'F1-Score']:
        fig.add_trace(go.Bar(
            name=metrica,
            x=modelos_data['Modelo'],
            y=modelos_data[metrica],
            text=modelos_data[metrica].apply(lambda x: f'{x:.2%}'),
            textposition='auto'
        ))

    fig.update_layout(
        barmode='group',
        height=400,
        yaxis_title="Score",
        yaxis_range=[0.9, 1.0]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Funcionalidades
    st.subheader("✨ Funcionalidades Implementadas")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        - ✅ Predicción de sentimiento
        - ✅ Threshold personalizable
        - ✅ Explicabilidad (palabras influyentes)
        - ✅ Análisis batch
        """)

    with col2:
        st.markdown("""
        - ✅ Soporte multilingüe
        - ✅ Interfaz interactiva
        - ✅ Exportación de resultados
        - ✅ Visualizaciones dinámicas
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>💬 <b>Análisis de Sentimientos v1.0</b></p>
    <p>Desarrollado con ❤️ usando Streamlit y scikit-learn</p>
    <p>Equipo: H12-25-L-Equipo 31 | Dataset: Punta Cana Hotels Reviews</p>
</div>
""", unsafe_allow_html=True)
