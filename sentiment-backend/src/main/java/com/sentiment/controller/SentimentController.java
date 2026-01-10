package com.sentiment.controller;


import com.sentiment.dto.BatchRequest;
import com.sentiment.dto.BatchResponse;
import com.sentiment.dto.SentimentExplainRequest;
import com.sentiment.dto.SentimentExplainResponse;
import com.sentiment.dto.SentimentRequest;
import com.sentiment.dto.SentimentResponse;
import com.sentiment.dto.StatsResponse;
import com.sentiment.service.SentimentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.MediaType;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class SentimentController {
    
    private final SentimentService sentimentService;
    
    @GetMapping("/")
    public ResponseEntity<String> root() {
        return ResponseEntity.ok("Sentiment Analysis Backend - Running on port 8080");
    }
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "sentiment-backend");
        return ResponseEntity.ok(response);
    }
    
    @PostMapping("/sentiment")
    public ResponseEntity<SentimentResponse> analyzeSentiment(@Valid @RequestBody SentimentRequest request) {
        SentimentResponse response = sentimentService.analyzeSentiment(request);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/sentiment/explain")
    public ResponseEntity<SentimentExplainResponse> analyzeSentimentWithExplanation(
            @Valid @RequestBody SentimentExplainRequest request) {
        SentimentExplainResponse response = sentimentService.analyzeSentimentWithExplanation(request);
        return ResponseEntity.ok(response);
    }

    /**
    * Obtener estadísticas de análisis realizados
    * 
    * @return Estadísticas agregadas
    */
    @GetMapping("/stats")
    public ResponseEntity<StatsResponse> getStatistics() {
        StatsResponse stats = sentimentService.getStatistics();
        return ResponseEntity.ok(stats);
    }


    /**
    * Analizar múltiples textos en batch
    * Soporta hasta 1000 textos por request
    * 
    * @param request Lista de textos a analizar
    * @return Resultados y estadísticas agregadas
    */
    @PostMapping("/sentiment/batch")
    public ResponseEntity<?> analyzeBatch(@Valid @RequestBody BatchRequest request) {
    
        // Validación
        if (request.getTextos() == null || request.getTextos().isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "La lista de textos no puede estar vacía"));
        }
    
        if (request.getTextos().size() > 1000) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Máximo 1000 textos por request"));
        }
    
        BatchResponse response = sentimentService.analyzeBatch(request);
        return ResponseEntity.ok(response);
    }

    /**
    * Analizar archivo CSV
    * Soporta archivos hasta 10MB
    * 
    * @param file Archivo CSV con columna 'texto'
    * @param idioma Idioma de los textos (opcional)
    * @param threshold Umbral de decisión (opcional)
    * @return Resultados y estadísticas agregadas
    */
    @PostMapping(value = "/sentiment/batch/csv", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity<?> analyzeCsv(
        @RequestParam("file") MultipartFile file,
        @RequestParam(defaultValue = "auto") String idioma,
        @RequestParam(defaultValue = "0.5") Double threshold) {

    try {
        // Validar archivo
        if (file.isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "El archivo está vacío"));
        }
    
        if (file.getSize() > 10 * 1024 * 1024) { // 10MB
            return ResponseEntity.badRequest()
                .body(Map.of("error", "El archivo no puede superar 10MB"));
        }
    
        // Leer CSV con mejor manejo de formato
        List<String> textos = new ArrayList<>();
        int lineNumber = 0;
        
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
        
            String line;
            boolean isFirstLine = true;
        
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                
                // Saltar header (primera línea)
                if (isFirstLine) {
                    isFirstLine = false;
                    System.out.println("Header detectado: " + line);
                    continue;
                }
                
                // Limpiar la línea
                line = line.trim();
                
                // Ignorar líneas vacías
                if (line.isEmpty()) {
                    continue;
                }
                
                // Remover comillas si existen (al inicio y al final)
                if (line.startsWith("\"") && line.endsWith("\"") && line.length() > 1) {
                    line = line.substring(1, line.length() - 1);
                }
                
                // Reemplazar comillas dobles escapadas
                line = line.replace("\"\"", "\"");
                
                // Validar que el texto no esté vacío después de limpiar
                if (!line.trim().isEmpty()) {
                    textos.add(line.trim());
                    System.out.println("Línea " + lineNumber + ": " + line.substring(0, Math.min(50, line.length())));
                }
            }
        }
        
        System.out.println("Total de textos extraídos: " + textos.size());
    
        if (textos.isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of(
                    "error", "El CSV no contiene textos válidos",
                    "detalle", "Verifica que tu CSV tenga una columna 'texto' con datos",
                    "lineas_procesadas", lineNumber
                ));
        }
    
        // Analizar
        BatchRequest batchRequest = new BatchRequest(textos, idioma, threshold);
        BatchResponse response = sentimentService.analyzeBatch(batchRequest);
    
        return ResponseEntity.ok(response);
    
    } catch (IOException e) {
        e.printStackTrace();
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Map.of("error", "Error al procesar el archivo: " + e.getMessage()));
    } catch (Exception e) {
        e.printStackTrace();
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Map.of("error", "Error inesperado: " + e.getMessage()));
    }
}


}