package com.sentiment.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class BatchResponse {
    private Long total;
    private Long positivos;
    private Long negativos;
    private Double porcentajePositivos;  // ← IMPORTANTE: Este campo debe existir
    private List<SentimentResponse> resultados;
    
    // Constructor adicional para calcular el porcentaje automáticamente
    public BatchResponse(Long total, Long positivos, Long negativos, List<SentimentResponse> resultados) {
        this.total = total;
        this.positivos = positivos;
        this.negativos = negativos;
        this.resultados = resultados;
        
        // Calcular porcentaje automáticamente
        if (total > 0) {
            this.porcentajePositivos = (positivos * 100.0) / total;
        } else {
            this.porcentajePositivos = 0.0;
        }
    }
}