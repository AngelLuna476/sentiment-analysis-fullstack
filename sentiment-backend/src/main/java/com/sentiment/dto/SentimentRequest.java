package com.sentiment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO para recibir peticiones de análisis de sentimiento
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SentimentRequest {
    
    /**
     * Texto a analizar (mínimo 3 caracteres, máximo 5000)
     */
    @NotBlank(message = "El texto no puede estar vacío")
    @Size(min = 3, max = 5000, message = "El texto debe tener entre 3 y 5000 caracteres")
    private String text;
    
    /**
     * Código del idioma (default: "auto" para detección automática)
     * Opciones: "auto", "es", "en", "pt", "fr", etc.
     */
    private String idioma = "auto";
    
    /**
     * Threshold personalizado (opcional, entre 0.0 y 1.0)
     */
    private Double threshold;
}