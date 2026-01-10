package com.sentiment.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

/**
 * DTO para recibir múltiples textos para análisis batch
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BatchRequest {
    
    private List<String> textos;
    private String idioma = "auto";
    private Double threshold = 0.5;
}
