# ============================================
# SCHEMAS - MODELOS DE DATOS (PYDANTIC)
# ============================================

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime


# ============================================
# REQUEST SCHEMAS
# ============================================

class SentimentRequest(BaseModel):
    """Request para análisis de sentimiento simple"""
    text: str = Field(..., min_length=3, max_length=5000, description="Texto a analizar")
    idioma: str = Field(default="auto", description="Código del idioma (auto, es, en, pt, etc.)")
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Umbral de decisión (0.0-1.0)")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('El texto no puede estar vacío')
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Este hotel es excelente, me encantó todo",
                "idioma": "es",
                "threshold": 0.5
            }
        }
    }


class SentimentExplainRequest(BaseModel):
    """Request para análisis con explicabilidad"""
    text: str = Field(..., min_length=3, max_length=5000, description="Texto a analizar")
    idioma: str = Field(default="auto", description="Código del idioma")
    top_n: int = Field(default=5, ge=1, le=20, description="Número de palabras influyentes")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('El texto no puede estar vacío')
        return v.strip()


class BatchSentimentRequest(BaseModel):
    """Request para análisis de múltiples textos"""
    texts: List[str] = Field(..., min_length=1, max_length=100, description="Lista de textos")
    idioma: str = Field(default="auto", description="Código del idioma")
    
    @field_validator('texts')
    @classmethod
    def validate_texts(cls, v):
        if not v:
            raise ValueError('La lista de textos no puede estar vacía')
        return [t.strip() for t in v if t and t.strip()]


class ThresholdConfig(BaseModel):
    """Configuración de threshold"""
    threshold: float = Field(..., ge=0.0, le=1.0, description="Nuevo threshold (0.0-1.0)")


# ============================================
# RESPONSE SCHEMAS
# ============================================

class SentimentResponse(BaseModel):
    """Response para análisis de sentimiento simple"""
    prevision: str = Field(..., description="Sentimiento predicho (Positivo/Negativo)")
    probabilidad: float = Field(..., description="Confianza de la predicción (0-1)")
    texto: str = Field(..., description="Texto analizado")
    idioma_detectado: Optional[str] = Field(None, description="Idioma detectado del texto")
    confianza: Optional[str] = Field(None, description="Nivel de confianza (Muy Alta/Alta/Media/Baja)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "prevision": "Positivo",
                "probabilidad": 0.95,
                "texto": "Este hotel es excelente",
                "idioma_detectado": "es",
                "confianza": "Muy Alta"
            }
        }
    }


class PalabraImportante(BaseModel):
    """Palabra con su importancia en la predicción"""
    palabra: str
    importancia: float
    sentimiento: str


class SentimentExplainResponse(BaseModel):
    """Response para análisis con explicabilidad"""
    sentimiento: str
    prevision: str
    probabilidad: float
    texto: str
    palabras_influyentes: List[str]
    palabras_importantes: List[PalabraImportante]
    idioma_detectado: Optional[str] = None
    confianza: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sentimiento": "Positivo",
                "prevision": "Positivo",
                "probabilidad": 0.95,
                "texto": "Este hotel es excelente",
                "palabras_influyentes": ["excelente", "hotel"],
                "palabras_importantes": [
                    {"palabra": "excelente", "importancia": 0.85, "sentimiento": "Positivo"},
                    {"palabra": "hotel", "importancia": 0.12, "sentimiento": "Positivo"}
                ],
                "idioma_detectado": "es",
                "confianza": "Muy Alta"
            }
        }
    }


class BatchItemResponse(BaseModel):
    """Un item del batch response"""
    prevision: str
    probabilidad: float
    texto: str
    confianza: str


class BatchSentimentResponse(BaseModel):
    """Response para análisis batch"""
    predicciones: List[SentimentResponse]
    total: int
    exitosos: int
    fallidos: int


class StatsResponse(BaseModel):
    """Response para estadísticas del modelo"""
    modelo_tipo: str
    clases: List[str]
    num_features: int
    threshold_actual: float
    funcionalidades: List[str]


class HealthResponse(BaseModel):
    """Response para health check"""
    status: str
    service: str
    version: str
    modelo_cargado: bool
    modelo_info: Optional[Dict] = None


class ThresholdResponse(BaseModel):
    """Response al configurar threshold"""
    threshold_anterior: float
    threshold_nuevo: float
    mensaje: str


class ErrorResponse(BaseModel):
    """Response para errores"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "detail": "El texto no puede estar vacío",
                "timestamp": "2024-12-25T10:30:00"
            }
        }
    }