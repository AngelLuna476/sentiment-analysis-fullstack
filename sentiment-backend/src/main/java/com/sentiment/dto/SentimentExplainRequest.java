package com.sentiment.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor

public class SentimentExplainRequest {
    @NotBlank(message = "El texto no puede estar vacío")
    @Size(min = 3, max = 5000, message = "El texto debe tener entre 3 y 5000 caracteres")
    private String text;
    
    private String idioma = "auto";
    
    @Min(value = 1, message = "top_n debe ser al menos 1")
    @Max(value = 20, message = "top_n no puede ser mayor a 20")
    private Integer topN = 5;
}
