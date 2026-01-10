# ============================================
# UTILS - FUNCIONES AUXILIARES
# ============================================

import re
import string
from typing import Dict, Optional
from deep_translator import GoogleTranslator
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# ============================================
# FUNCIONES DE LIMPIEZA DE TEXTO
# ============================================

def limpiar_texto(texto: str) -> str:
    """
    Limpia y preprocesa un texto para análisis de sentimiento.
    
    Args:
        texto: Texto a limpiar
        
    Returns:
        Texto limpio y procesado
    """
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Eliminar URLs
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto)
    
    # Eliminar menciones (@usuario)
    texto = re.sub(r'@\w+', '', texto)
    
    # Eliminar hashtags (#tema)
    texto = re.sub(r'#\w+', '', texto)
    
    # Eliminar números
    texto = re.sub(r'\d+', '', texto)
    
    # Eliminar puntuación
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    
    # Eliminar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto


# ============================================
# FUNCIONES DE TRADUCCIÓN
# ============================================

def traducir_texto(
    texto: str, 
    idioma_origen: str = 'auto',
    idioma_destino: str = 'es',
    max_reintentos: int = 3
) -> Dict[str, any]:
    """
    Traduce un texto al español usando Google Translate.
    
    Args:
        texto: Texto a traducir
        idioma_origen: Código del idioma origen ('auto' para detección automática)
        idioma_destino: Código del idioma destino (default: 'es')
        max_reintentos: Número máximo de intentos si falla
        
    Returns:
        Dict con resultado de la traducción
    """
    for intento in range(max_reintentos):
        try:
            # Detectar idioma si es 'auto'
            if idioma_origen == 'auto':
                # Intentar detectar el idioma
                try:
                    from langdetect import detect
                    idioma_detectado = detect(texto)
                except:
                    # Si falla la detección, asumir que ya está en español
                    idioma_detectado = 'es'
            else:
                idioma_detectado = idioma_origen
            
            # Si ya está en español, no traducir
            if idioma_detectado == 'es':
                return {
                    'texto_traducido': texto,
                    'idioma_detectado': 'es',
                    'traduccion_exitosa': True,
                    'error': None
                }
            
            # Traducir usando deep-translator
            traductor = GoogleTranslator(source=idioma_detectado, target=idioma_destino)
            texto_traducido = traductor.translate(texto)
            
            logger.info(f"Traducción exitosa: {idioma_detectado} -> {idioma_destino}")
            
            return {
                'texto_traducido': texto_traducido,
                'idioma_detectado': idioma_detectado,
                'traduccion_exitosa': True,
                'error': None
            }
            
        except Exception as e:
            logger.warning(f"Intento {intento + 1}/{max_reintentos} falló: {str(e)}")
            
            if intento == max_reintentos - 1:
                # Último intento falló, devolver texto original
                logger.error(f"Traducción falló después de {max_reintentos} intentos")
                return {
                    'texto_traducido': texto,
                    'idioma_detectado': 'unknown',
                    'traduccion_exitosa': False,
                    'error': str(e)
                }
    
    # No debería llegar aquí, pero por si acaso
    return {
        'texto_traducido': texto,
        'idioma_detectado': 'unknown',
        'traduccion_exitosa': False,
        'error': 'Error desconocido'
    }


def detectar_idioma(texto: str) -> Optional[str]:
    """
    Detecta el idioma de un texto.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        Código del idioma detectado o None si falla
    """
    try:
        from langdetect import detect
        return detect(texto)
    except Exception as e:
        logger.warning(f"Error detectando idioma: {str(e)}")
        return None


# ============================================
# FUNCIONES DE VALIDACIÓN
# ============================================

def validar_texto(texto: str, min_length: int = 3, max_length: int = 5000) -> Dict[str, any]:
    """
    Valida que un texto cumple con los requisitos mínimos.
    
    Args:
        texto: Texto a validar
        min_length: Longitud mínima permitida
        max_length: Longitud máxima permitida
        
    Returns:
        Dict con resultado de la validación
    """
    # Eliminar espacios en blanco
    texto = texto.strip()
    
    # Validar longitud
    if len(texto) < min_length:
        return {
            'valido': False,
            'error': f'El texto debe tener al menos {min_length} caracteres',
            'texto_limpio': texto
        }
    
    if len(texto) > max_length:
        return {
            'valido': False,
            'error': f'El texto no puede superar {max_length} caracteres',
            'texto_limpio': texto
        }
    
    # Validar que no esté vacío después de limpiar
    texto_limpio = limpiar_texto(texto)
    if len(texto_limpio) < 2:
        return {
            'valido': False,
            'error': 'El texto no contiene suficiente contenido significativo',
            'texto_limpio': texto_limpio
        }
    
    return {
        'valido': True,
        'error': None,
        'texto_limpio': texto_limpio
    }


# ============================================
# FUNCIONES DE FORMATO
# ============================================

def formatear_probabilidad(probabilidad: float) -> str:
    """
    Formatea una probabilidad como porcentaje.
    
    Args:
        probabilidad: Valor entre 0 y 1
        
    Returns:
        String formateado (ej: "95.42%")
    """
    return f"{probabilidad * 100:.2f}%"


def obtener_nivel_confianza(probabilidad: float) -> str:
    """
    Determina el nivel de confianza basado en la probabilidad.
    
    Args:
        probabilidad: Valor entre 0 y 1
        
    Returns:
        Nivel de confianza: "Muy Alta", "Alta", "Media", "Baja"
    """
    if probabilidad >= 0.90:
        return "Muy Alta"
    elif probabilidad >= 0.75:
        return "Alta"
    elif probabilidad >= 0.60:
        return "Media"
    else:
        return "Baja"