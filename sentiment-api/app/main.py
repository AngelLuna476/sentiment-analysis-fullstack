# ============================================
# MAIN - API FASTAPI PRINCIPAL
# ============================================

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import time
from typing import List

# Importar schemas
from .schemas import (
    SentimentRequest,
    SentimentResponse,
    SentimentExplainRequest,
    SentimentExplainResponse,
    BatchSentimentRequest,
    BatchSentimentResponse,
    ThresholdConfig,
    ThresholdResponse,
    StatsResponse,
    HealthResponse,
    ErrorResponse
)

# Importar predictor
from .prediccion import inicializar_predictor, obtener_predictor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CREAR APLICACIÓN FASTAPI
# ============================================

app = FastAPI(
    title="Sentiment Analysis API",
    description="API REST para análisis de sentimientos en español con soporte multilingüe",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# CONFIGURAR CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# EVENTOS DE INICIO/CIERRE
# ============================================

@app.on_event("startup")
async def startup_event():
    """Se ejecuta al iniciar la aplicación"""
    try:
        logger.info("🚀 Iniciando Sentiment Analysis API...")
        inicializar_predictor()
        logger.info("✅ API iniciada correctamente")
    except Exception as e:
        logger.error(f"❌ Error al iniciar la API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Se ejecuta al cerrar la aplicación"""
    logger.info("👋 Cerrando Sentiment Analysis API...")


# ============================================
# MANEJADOR DE ERRORES GLOBAL
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Maneja todas las excepciones no capturadas"""
    logger.error(f"Error no capturado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================
# ENDPOINTS PRINCIPALES
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Sentiment Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "sentiment": "/sentiment (POST)",
            "sentiment_explain": "/sentiment/explain (POST)",
            "batch": "/sentiment/batch (POST)",
            "stats": "/stats (GET)",
            "threshold": "/threshold (POST)"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Verificar el estado de la API y del modelo.
    
    Returns:
        Estado de la API y si el modelo está cargado
    """
    try:
        predictor = obtener_predictor()
        modelo_info = predictor.obtener_info()
        
        return HealthResponse(
            status="healthy",
            service="Sentiment Analysis API",
            version="1.0.0",
            modelo_cargado=True,
            modelo_info=modelo_info
        )
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthResponse(
            status="unhealthy",
            service="Sentiment Analysis API",
            version="1.0.0",
            modelo_cargado=False,
            modelo_info=None
        )


# ============================================
# ENDPOINT: PREDICCIÓN SIMPLE
# ============================================

@app.post("/sentiment", response_model=SentimentResponse, tags=["Sentiment Analysis"])
async def analyze_sentiment(request: SentimentRequest):
    """
    Analizar el sentimiento de un texto.
    
    - **text**: Texto a analizar (mínimo 3 caracteres)
    - **idioma**: Código del idioma ('auto' para detección automática, 'es', 'en', 'pt', etc.)
    - **threshold**: Umbral de decisión personalizado (opcional, 0.0-1.0)
    
    Returns:
        Sentimiento predicho (Positivo/Negativo) con probabilidad
    """
    try:
        predictor = obtener_predictor()
        
        # Configurar threshold si se proporciona
        if request.threshold is not None:
            predictor.configurar_threshold(request.threshold)
        
        # Determinar si necesita traducción
        traducir = request.idioma != 'es'
        
        # Realizar predicción
        resultado = predictor.predecir(
            texto=request.text,
            traducir=traducir,
            idioma_origen=request.idioma
        )
        
        logger.info(f"Predicción exitosa: {resultado.prevision} ({resultado.probabilidad:.4f})")
        
        return resultado
        
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")


# ============================================
# ENDPOINT: PREDICCIÓN CON EXPLICABILIDAD
# ============================================

@app.post("/sentiment/explain", response_model=SentimentExplainResponse, tags=["Sentiment Analysis"])
async def analyze_sentiment_with_explanation(request: SentimentExplainRequest):
    """
    Analizar el sentimiento con explicación de palabras influyentes.
    
    - **text**: Texto a analizar
    - **idioma**: Código del idioma
    - **top_n**: Número de palabras más influyentes a retornar (1-20)
    
    Returns:
        Predicción con lista de palabras más importantes
    """
    try:
        predictor = obtener_predictor()
        
        # Determinar si necesita traducción
        traducir = request.idioma != 'es'
        
        # Realizar predicción con explicación
        resultado = predictor.predecir_con_explicacion(
            texto=request.text,
            top_n=request.top_n,
            traducir=traducir,
            idioma_origen=request.idioma
        )
        
        logger.info(f"Predicción con explicación exitosa: {resultado.prevision}")
        
        return resultado
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en predicción con explicación: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ============================================
# ENDPOINT: ANÁLISIS BATCH OPTIMIZADO (CORREGIDO)
# ============================================

@app.post("/sentiment/batch", tags=["Batch Processing"])
async def analyze_batch(request: dict):
    """
    Análisis batch optimizado - procesa múltiples textos
    
    - **textos**: Lista de textos a analizar
    - **idioma**: Código de idioma o 'auto' para detección automática
    
    Retorna estadísticas agregadas y resultados individuales
    """
    try:
        textos = request.get("textos", [])
        idioma = request.get("idioma", "auto")
        
        logger.info(f"📦 Recibida petición batch con {len(textos)} textos")
        
        if not textos or len(textos) == 0:
            raise HTTPException(
                status_code=400, 
                detail="La lista de textos está vacía"
            )
        
        if len(textos) > 1000:
            raise HTTPException(
                status_code=400, 
                detail=f"Máximo 1000 textos. Se recibieron {len(textos)}"
            )
        
        # Obtener el predictor
        predictor = obtener_predictor()
        
        logger.info(f"🔄 Iniciando procesamiento de {len(textos)} textos")
        start_time = time.time()
        
        # Procesar todos los textos
        resultados = []
        errores = 0
        
        for idx, texto_original in enumerate(textos, 1):
            try:
                # Validar que el texto no esté vacío
                if not texto_original or not texto_original.strip():
                    logger.warning(f"Texto {idx} está vacío, saltando...")
                    errores += 1
                    continue
                
                # Determinar si necesita traducción
                traducir = idioma != 'es' and idioma != 'auto'
                
                # Usar el método predecir del predictor
                resultado_pred = predictor.predecir(
                    texto=texto_original,
                    traducir=traducir,
                    idioma_origen=idioma if idioma != 'auto' else None
                )
                
                resultados.append({
                    "texto": texto_original[:200],  # Limitar longitud en respuesta
                    "prevision": resultado_pred.prevision,
                    "probabilidad": float(resultado_pred.probabilidad),
                    "confianza": resultado_pred.confianza,
                    "idioma_detectado": resultado_pred.idioma_detectado if hasattr(resultado_pred, 'idioma_detectado') else idioma
                })
                
                # Log cada 50 textos
                if idx % 50 == 0:
                    logger.info(f"Procesados {idx}/{len(textos)} textos...")
                    
            except Exception as e:
                logger.warning(f"Error procesando texto {idx}: {str(e)}")
                errores += 1
                continue
        
        elapsed_time = time.time() - start_time
        
        # Calcular estadísticas
        total = len(resultados)
        positivos = sum(1 for r in resultados if r["prevision"] == "Positivo")
        negativos = total - positivos
        porcentaje_positivos = (positivos / total * 100) if total > 0 else 0
        
        logger.info(f"✅ Batch completado en {elapsed_time:.2f}s")
        logger.info(f"   Total procesados: {total}")
        logger.info(f"   Positivos: {positivos} ({porcentaje_positivos:.1f}%)")
        logger.info(f"   Negativos: {negativos}")
        logger.info(f"   Errores: {errores}")
        
        return {
            "total": total,
            "positivos": positivos,
            "negativos": negativos,
            "porcentaje_positivos": round(porcentaje_positivos, 2),
            "resultados": resultados,
            "tiempo_procesamiento_segundos": round(elapsed_time, 2),
            "errores": errores
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en batch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando batch: {str(e)}"
        )


# ============================================
# ENDPOINT: ESTADÍSTICAS DEL MODELO
# ============================================

@app.get("/stats", response_model=StatsResponse, tags=["Model Info"])
async def get_model_stats():
    """
    Obtener estadísticas e información del modelo.
    
    Returns:
        Información sobre el modelo, métricas y funcionalidades
    """
    try:
        predictor = obtener_predictor()
        info = predictor.obtener_info()
        
        return StatsResponse(
            modelo_tipo=info['modelo_tipo'],
            clases=info['clases'],
            num_features=info['num_features'],
            threshold_actual=info['threshold_actual'],
            funcionalidades=[
                "Análisis de sentimiento binario (Positivo/Negativo)",
                "Soporte multilingüe con traducción automática",
                "Explicabilidad (palabras influyentes)",
                "Threshold personalizable",
                "Procesamiento batch",
                "Métricas de confianza"
            ]
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINT: CONFIGURAR THRESHOLD
# ============================================

@app.post("/threshold", response_model=ThresholdResponse, tags=["Configuration"])
async def configure_threshold(config: ThresholdConfig):
    """
    Configurar el umbral de decisión del modelo.
    
    - **threshold**: Nuevo umbral (0.0-1.0)
      - Valores < 0.5: Más predicciones positivas
      - Valores > 0.5: Más predicciones negativas
      - 0.5: Balanceado (default)
    
    Returns:
        Confirmación del cambio
    """
    try:
        predictor = obtener_predictor()
        threshold_anterior = predictor.threshold
        
        predictor.configurar_threshold(config.threshold)
        
        logger.info(f"Threshold actualizado: {threshold_anterior} -> {config.threshold}")
        
        return ThresholdResponse(
            threshold_anterior=threshold_anterior,
            threshold_nuevo=config.threshold,
            mensaje=f"Threshold actualizado correctamente de {threshold_anterior} a {config.threshold}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error configurando threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINT: EJEMPLO DE USO
# ============================================

@app.get("/examples", tags=["Examples"])
async def get_examples():
    """
    Obtener ejemplos de uso de la API.
    
    Returns:
        Ejemplos de requests para cada endpoint
    """
    return {
        "sentiment_simple": {
            "endpoint": "POST /sentiment",
            "example": {
                "text": "Este hotel es excelente, me encantó todo",
                "idioma": "es",
                "threshold": 0.5
            }
        },
        "sentiment_multilingue": {
            "endpoint": "POST /sentiment",
            "example": {
                "text": "This hotel is amazing, I loved everything",
                "idioma": "en"
            }
        },
        "sentiment_explain": {
            "endpoint": "POST /sentiment/explain",
            "example": {
                "text": "Servicio horrible, comida pésima, hotel sucio",
                "idioma": "es",
                "top_n": 5
            }
        },
        "sentiment_batch": {
            "endpoint": "POST /sentiment/batch",
            "example": {
                "textos": [
                    "Hotel excelente",
                    "Muy malo",
                    "Normal"
                ],
                "idioma": "es"
            }
        },
        "threshold_config": {
            "endpoint": "POST /threshold",
            "example": {
                "threshold": 0.3
            }
        }
    }


# ============================================
# EJECUTAR EN DESARROLLO
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )