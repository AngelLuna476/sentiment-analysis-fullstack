package com.sentiment.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SentimentExplainResponse {
    
    private String prevision;
    private String sentimiento;
    private Double probabilidad;
    private String texto;
    
    @JsonProperty("palabrasImportantes")
    @JsonAlias("palabras_importantes")
    private List<PalabraImportante> palabrasImportantes;
    
    @JsonProperty("palabrasInfluyentes")
    @JsonAlias("palabras_influyentes")
    private List<String> palabrasInfluyentes;
    
    @JsonProperty("idiomaDetectado")
    @JsonAlias("idioma_detectado")
    private String idiomaDetectado;
    
    private String confianza;
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PalabraImportante {
        private String palabra;
        private Double importancia;
        private String sentimiento;
    }
}