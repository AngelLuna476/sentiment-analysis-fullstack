# ============================================
# PREDICCION - LÓGICA DEL MODELO
# ============================================

import joblib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from .utils import (
    limpiar_texto,
    traducir_texto,
    validar_texto,
    obtener_nivel_confianza
)
from .schemas import (
    SentimentResponse,
    SentimentExplainResponse,
    ThresholdConfig,
    BatchSentimentResponse
)

# Configurar logging
logger = logging.getLogger(__name__)

# ============================================
# CLASE PRINCIPAL - PREDICTOR DE SENTIMIENTOS
# ============================================

class SentimentPredictor:
    """
    Clase para manejar predicciones de sentimiento.
    Carga el modelo y vectorizador una sola vez al inicializar.
    """
    
    def __init__(self, model_path: str = None, vectorizer_path: str = None):
        """
        Inicializa el predictor cargando el modelo y vectorizador.
        
        Args:
            model_path: Ruta al archivo .pkl del modelo
            vectorizer_path: Ruta al archivo .pkl del vectorizador
        """
        # Rutas por defecto
        if model_path is None:
            model_path = Path(__file__).parent.parent / "modelos_serializados" / "sentiment_model.pkl"
        if vectorizer_path is None:
            vectorizer_path = Path(__file__).parent.parent / "modelos_serializados" / "tfidf_vectorizer.pkl"
        
        # Convertir a Path si es string
        self.model_path = Path(model_path)
        self.vectorizer_path = Path(vectorizer_path)
        
        # Cargar modelo y vectorizador
        self._cargar_modelo()
        self._cargar_vectorizador()
        
        # Configuración de threshold por defecto
        self.threshold = 0.5
        
        logger.info("✅ SentimentPredictor inicializado correctamente")
    
    def _cargar_modelo(self):
        """Carga el modelo serializado."""
        try:
            self.modelo = joblib.load(self.model_path)
            logger.info(f"✅ Modelo cargado desde: {self.model_path}")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise
    
    def _cargar_vectorizador(self):
        """Carga el vectorizador TF-IDF serializado."""
        try:
            self.vectorizador = joblib.load(self.vectorizer_path)
            logger.info(f"✅ Vectorizador cargado desde: {self.vectorizer_path}")
        except Exception as e:
            logger.error(f"❌ Error cargando vectorizador: {e}")
            raise
    
    # ============================================
    # PREDICCIÓN BÁSICA
    # ============================================
    
    def predecir(
        self,
        texto: str,
        traducir: bool = False,
        idioma_origen: str = 'auto'
    ) -> SentimentResponse:
        """
        Realiza predicción de sentimiento básica.
        
        Args:
            texto: Texto a analizar
            traducir: Si True, intenta traducir al español
            idioma_origen: Código de idioma origen ('auto' para detección)
            
        Returns:
            SentimentResponse con la predicción
        """
        # Validar texto
        validacion = validar_texto(texto)
        if not validacion['valido']:
            raise ValueError(validacion['error'])
        
        texto_original = texto
        idioma_detectado = 'es'
        
        # Traducir si es necesario
        if traducir and idioma_origen != 'es':
            resultado_traduccion = traducir_texto(
                texto=texto,
                idioma_origen=idioma_origen,
                idioma_destino='es'
            )
            
            if resultado_traduccion['traduccion_exitosa']:
                texto = resultado_traduccion['texto_traducido']
                idioma_detectado = resultado_traduccion['idioma_detectado']
                logger.info(f"Texto traducido de {idioma_detectado} a español")
        
        # Limpiar texto
        texto_limpio = limpiar_texto(texto)
        
        # Vectorizar
        texto_vectorizado = self.vectorizador.transform([texto_limpio])
        
        # Predecir
        prediccion = self.modelo.predict(texto_vectorizado)[0]
        probabilidades = self.modelo.predict_proba(texto_vectorizado)[0]
        
        # Obtener probabilidad de la clase predicha
        clase_positiva_idx = list(self.modelo.classes_).index('Positivo')
        clase_negativa_idx = list(self.modelo.classes_).index('Negativo')
        
        prob_positivo = probabilidades[clase_positiva_idx]
        prob_negativo = probabilidades[clase_negativa_idx]
        
        # Aplicar threshold personalizado si está configurado
        if self.threshold != 0.5:
            if prob_positivo >= self.threshold:
                prediccion = 'Positivo'
            else:
                prediccion = 'Negativo'
        
        # Probabilidad de la clase predicha
        probabilidad = prob_positivo if prediccion == 'Positivo' else prob_negativo
        
        logger.info(f"Predicción: {prediccion} ({probabilidad:.4f})")
        
        return SentimentResponse(
            prevision=prediccion,
            probabilidad=round(float(probabilidad), 4),
            texto=texto_original,
            idioma_detectado=idioma_detectado if traducir else None,
            confianza=obtener_nivel_confianza(probabilidad)
        )
    
    # ============================================
    # PREDICCIÓN CON EXPLICABILIDAD
    # ============================================
    
    def predecir_con_explicacion(
        self,
        texto: str,
        top_n: int = 5,
        traducir: bool = False,
        idioma_origen: str = 'auto'
    ) -> SentimentExplainResponse:
        """
        Realiza predicción con explicación de palabras importantes.
        
        Args:
            texto: Texto a analizar
            top_n: Número de palabras más importantes a retornar
            traducir: Si True, intenta traducir al español
            idioma_origen: Código de idioma origen
            
        Returns:
            SentimentExplainResponse con predicción y explicación
        """
        # Obtener predicción básica
        prediccion_basica = self.predecir(texto, traducir, idioma_origen)
        
        # Limpiar texto para obtener features
        texto_limpio = limpiar_texto(
            prediccion_basica.texto if not traducir 
            else traducir_texto(prediccion_basica.texto)['texto_traducido']
        )
        
        # Vectorizar
        texto_vectorizado = self.vectorizador.transform([texto_limpio])
        
        # Obtener palabras importantes
        feature_names = self.vectorizador.get_feature_names_out()
        texto_array = texto_vectorizado.toarray()[0]
        
        # Obtener índices de features no-cero (palabras presentes)
        indices_presentes = texto_array.nonzero()[0]
        
        # Obtener coeficientes del modelo (solo funciona con modelos lineales)
        try:
            if hasattr(self.modelo, 'feature_log_prob_'):
                # Para Naive Bayes
                clase_positiva_idx = list(self.modelo.classes_).index('Positivo')
                coeficientes = self.modelo.feature_log_prob_[clase_positiva_idx]
            elif hasattr(self.modelo, 'coef_'):
                # Para Logistic Regression
                coeficientes = self.modelo.coef_[0]
            else:
                coeficientes = None
        except:
            coeficientes = None
        
        # Calcular importancia de palabras presentes
        palabras_importantes = []
        palabras_influyentes_lista = []
        
        if coeficientes is not None:
            for idx in indices_presentes:
                palabra = feature_names[idx]
                peso = float(coeficientes[idx])
                tf_idf_valor = float(texto_array[idx])
                importancia = abs(peso * tf_idf_valor)
                
                palabras_importantes.append({
                    'palabra': palabra,
                    'importancia': round(importancia, 4),
                    'sentimiento': 'Positivo' if peso > 0 else 'Negativo'
                })
            
            # Ordenar por importancia
            palabras_importantes.sort(key=lambda x: x['importancia'], reverse=True)
            palabras_influyentes_lista = [p['palabra'] for p in palabras_importantes[:top_n]]
            palabras_importantes = palabras_importantes[:top_n]
        
        return SentimentExplainResponse(
            sentimiento=prediccion_basica.prevision,
            prevision=prediccion_basica.prevision,
            probabilidad=prediccion_basica.probabilidad,
            texto=prediccion_basica.texto,
            palabras_influyentes=palabras_influyentes_lista,
            palabras_importantes=palabras_importantes,
            idioma_detectado=prediccion_basica.idioma_detectado,
            confianza=prediccion_basica.confianza
        )
    
    # ============================================
    # PREDICCIÓN BATCH
    # ============================================
    
    def predecir_batch(
        self,
        textos: List[str],
        traducir: bool = False
    ) -> BatchSentimentResponse:
        """
        Realiza predicción en múltiples textos.
        
        Args:
            textos: Lista de textos a analizar
            traducir: Si True, intenta traducir cada texto
            
        Returns:
            BatchSentimentResponse con todas las predicciones
        """
        resultados = []
        exitosos = 0
        fallidos = 0
        
        for texto in textos:
            try:
                prediccion = self.predecir(texto, traducir=traducir)
                resultados.append(prediccion)
                exitosos += 1
            except Exception as e:
                logger.error(f"Error prediciendo texto: {e}")
                fallidos += 1
                # Agregar resultado con error
                resultados.append(SentimentResponse(
                    prevision="Error",
                    probabilidad=0.0,
                    texto=texto,
                    confianza="Baja"
                ))
        
        return BatchSentimentResponse(
            predicciones=resultados,
            total=len(textos),
            exitosos=exitosos,
            fallidos=fallidos
        )
    
    # ============================================
    # CONFIGURACIÓN DE THRESHOLD
    # ============================================
    
    def configurar_threshold(self, threshold: float):
        """
        Configura el threshold de decisión.
        
        Args:
            threshold: Valor entre 0 y 1
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold debe estar entre 0 y 1")
        
        self.threshold = threshold
        logger.info(f"Threshold configurado a: {threshold}")
    
    # ============================================
    # INFORMACIÓN DEL MODELO
    # ============================================
    
    def obtener_info(self) -> Dict:
        """
        Obtiene información sobre el modelo cargado.
        
        Returns:
            Dict con información del modelo
        """
        return {
            "modelo_tipo": type(self.modelo).__name__,
            "clases": list(self.modelo.classes_),
            "num_features": len(self.vectorizador.get_feature_names_out()),
            "threshold_actual": self.threshold,
            "modelo_path": str(self.model_path),
            "vectorizador_path": str(self.vectorizer_path)
        }


# ============================================
# INSTANCIA GLOBAL (SE CREA AL INICIAR LA API)
# ============================================

# Esta variable se inicializará en main.py al arrancar la aplicación
predictor: Optional[SentimentPredictor] = None


def inicializar_predictor():
    """
    Inicializa el predictor global.
    Esta función se llama al arrancar la aplicación.
    """
    global predictor
    predictor = SentimentPredictor()
    return predictor


def obtener_predictor() -> SentimentPredictor:
    """
    Obtiene la instancia del predictor.
    
    Returns:
        Instancia de SentimentPredictor
        
    Raises:
        RuntimeError: Si el predictor no ha sido inicializado
    """
    if predictor is None:
        raise RuntimeError("El predictor no ha sido inicializado")
    return predictor