package com.sentiment.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

/**
 * Modelo para almacenar análisis de sentimiento en memoria
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SentimentAnalysis {
    
    private Long id;
    private String texto;
    private String prevision;
    private Double probabilidad;
    private String confianza;
    private String idioma;
    private Double threshold;
    private LocalDateTime fechaAnalisis;
    
    // Constructor sin ID (se genera automáticamente)
    public SentimentAnalysis(String texto, String prevision, Double probabilidad, 
                           String confianza, String idioma, Double threshold) {
        this.id = System.currentTimeMillis();
        this.texto = texto;
        this.prevision = prevision;
        this.probabilidad = probabilidad;
        this.confianza = confianza;
        this.idioma = idioma;
        this.threshold = threshold;
        this.fechaAnalisis = LocalDateTime.now();
    }
}
