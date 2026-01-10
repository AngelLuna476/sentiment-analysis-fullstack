package com.sentiment.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO para retornar respuestas de análisis de sentimiento
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SentimentResponse {
    
    /**
     * Sentimiento predicho: "Positivo" o "Negativo"
     */
    private String prevision;
    
    /**
     * Probabilidad de la predicción (0.0 - 1.0)
     */
    private Double probabilidad;
    
    /**
     * Texto analizado
     */
    private String texto;
    
    /**
     * Idioma detectado (opcional)
     */
    private String idiomaDetectado;
    
    /**
     * Nivel de confianza: "Muy Alta", "Alta", "Media", "Baja"
     */
    private String confianza;
    
    /**
     * Timestamp de la respuesta
     */
    private Long timestamp;
    
    /**
     * Constructor para respuestas simples
     */
    public SentimentResponse(String prevision, Double probabilidad, String texto) {
        this.prevision = prevision;
        this.probabilidad = probabilidad;
        this.texto = texto;
        this.timestamp = System.currentTimeMillis();
    }
}