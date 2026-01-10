package com.sentiment.service;

import com.sentiment.dto.SentimentRequest;
import com.sentiment.dto.SentimentResponse;
import com.sentiment.dto.BatchRequest;
import com.sentiment.dto.BatchResponse;
import com.sentiment.dto.SentimentExplainRequest;
import com.sentiment.dto.SentimentExplainResponse;
import com.sentiment.dto.StatsResponse;
import com.sentiment.model.SentimentAnalysis;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpEntity;
import org.springframework.core.ParameterizedTypeReference;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;


@Service
@Slf4j
public class SentimentService {
    
    private final RestTemplate restTemplate;
    private final String pythonApiUrl;
    
    // Historial en memoria
    private final List<SentimentAnalysis> historial = new ArrayList<>();
    
    public SentimentService(RestTemplate restTemplate, 
                           @Value("${sentiment.api.url}") String pythonApiUrl) {
        this.restTemplate = restTemplate;
        this.pythonApiUrl = pythonApiUrl;
    }
    
    // ============================================
    // ANÁLISIS INDIVIDUAL
    // ============================================
    
    public SentimentResponse analyzeSentiment(SentimentRequest request) {
        log.info("Analizando sentimiento: {}", request.getText().substring(0, Math.min(50, request.getText().length())));
        
        Map<String, Object> pythonRequest = new HashMap<>();
        pythonRequest.put("text", request.getText());
        pythonRequest.put("idioma", request.getIdioma() != null ? request.getIdioma() : "auto");
        if (request.getThreshold() != null) {
            pythonRequest.put("threshold", request.getThreshold());
        }
        
        String url = pythonApiUrl + "/sentiment";
        SentimentResponse response = restTemplate.postForObject(url, pythonRequest, SentimentResponse.class);
        
        log.info("Resultado: {} ({}%)", response.getPrevision(), response.getProbabilidad() * 100);
        
        // Guardar en historial
        guardarEnHistorial(request, response);
        
        return response;
    }
    
    // ============================================
    // ANÁLISIS CON EXPLICABILIDAD
    // ============================================
    
    public SentimentExplainResponse analyzeSentimentWithExplanation(SentimentExplainRequest request) {
        log.info("Analizando con explicabilidad: {}", 
                request.getText().substring(0, Math.min(50, request.getText().length())));
        
        Map<String, Object> pythonRequest = new HashMap<>();
        pythonRequest.put("text", request.getText());
        pythonRequest.put("idioma", request.getIdioma() != null ? request.getIdioma() : "auto");
        pythonRequest.put("top_n", request.getTopN() != null ? request.getTopN() : 5);
        
        String url = pythonApiUrl + "/sentiment/explain";
        SentimentExplainResponse response = restTemplate.postForObject(url, pythonRequest, SentimentExplainResponse.class);
        
        log.info("Resultado con explicación: {} con {} palabras", 
                 response.getPrevision(), 
                 response.getPalabrasImportantes() != null ? response.getPalabrasImportantes().size() : 0);
        
        return response;
    }
    
    // ============================================
    // ANÁLISIS BATCH OPTIMIZADO
    // ============================================
    
    public BatchResponse analyzeBatch(BatchRequest request) {
        log.info("📦 Iniciando análisis batch de {} textos", request.getTextos().size());
        
        long startTime = System.currentTimeMillis();
        
        // Enviar TODOS los textos de una vez a la API Python
        Map<String, Object> pythonRequest = new HashMap<>();
        pythonRequest.put("textos", request.getTextos());
        pythonRequest.put("idioma", request.getIdioma() != null ? request.getIdioma() : "auto");
        
        String url = pythonApiUrl + "/sentiment/batch";
        
        try {
            // Hacer UNA SOLA llamada con todos los textos usando ParameterizedTypeReference
            ResponseEntity<Map<String, Object>> responseEntity = restTemplate.exchange(
                url,
                HttpMethod.POST,
                new HttpEntity<>(pythonRequest),
                new ParameterizedTypeReference<Map<String, Object>>() {}
            );
            
            Map<String, Object> pythonResponse = responseEntity.getBody();
            
            if (pythonResponse == null || !pythonResponse.containsKey("resultados")) {
                throw new RuntimeException("Respuesta inválida de la API Python");
            }
            
            // Procesar respuesta
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> resultadosPython = (List<Map<String, Object>>) pythonResponse.get("resultados");
            
            List<SentimentResponse> resultados = resultadosPython.stream()
                .map(this::convertirResultado)
                .collect(Collectors.toList());
            
            // Calcular estadísticas
            long total = resultados.size();
            long positivos = resultados.stream()
                    .filter(r -> "Positivo".equals(r.getPrevision()))
                    .count();
            long negativos = total - positivos;
            double porcentajePositivos = total > 0 ? (positivos * 100.0 / total) : 0.0;
            
            long endTime = System.currentTimeMillis();
            long duration = endTime - startTime;
            
            log.info("✅ Batch completado en {}ms: Total={}, Positivos={}, Negativos={}, Porcentaje={}%", 
                     duration, total, positivos, negativos, String.format("%.2f", porcentajePositivos));
            
            // Guardar en historial (solo algunos para no saturar memoria)
            if (resultados.size() <= 100) {
                resultados.forEach(r -> {
                    SentimentRequest req = new SentimentRequest();
                    req.setText(r.getTexto());
                    req.setIdioma(request.getIdioma());
                    req.setThreshold(0.5);
                    guardarEnHistorial(req, r);
                });
            }
            
            return new BatchResponse(total, positivos, negativos, porcentajePositivos, resultados);
            
        } catch (Exception e) {
            log.error("❌ Error en análisis batch", e);
            throw new RuntimeException("Error al procesar batch: " + e.getMessage());
        }
    }
    
    // Método auxiliar para convertir respuesta de Python a Java
    private SentimentResponse convertirResultado(Map<String, Object> resultado) {
        SentimentResponse response = new SentimentResponse();
        response.setPrevision((String) resultado.get("prevision"));
        
        Object probabilidad = resultado.get("probabilidad");
        if (probabilidad instanceof Number) {
            response.setProbabilidad(((Number) probabilidad).doubleValue());
        }
        
        response.setTexto((String) resultado.get("texto"));
        response.setConfianza((String) resultado.get("confianza"));
        response.setIdiomaDetectado((String) resultado.get("idioma_detectado"));
        
        return response;
    }
    
    // ============================================
    // ESTADÍSTICAS
    // ============================================
    
    public StatsResponse getStatistics() {
        long total = historial.size();
        long positivos = historial.stream()
                .filter(a -> "Positivo".equals(a.getPrevision()))
                .count();
        long negativos = total - positivos;
        double porcentajePositivos = total > 0 ? (positivos * 100.0 / total) : 0.0;
        
        return new StatsResponse(total, positivos, negativos, porcentajePositivos);
    }
    
    // ============================================
    // GESTIÓN DE HISTORIAL
    // ============================================
    
    private void guardarEnHistorial(SentimentRequest request, SentimentResponse response) {
        SentimentAnalysis analisis = new SentimentAnalysis(
            null,
            request.getText(),
            response.getPrevision(),
            response.getProbabilidad(),
            response.getConfianza(),
            request.getIdioma(),
            request.getThreshold(),
            LocalDateTime.now()
        );
        
        historial.add(0, analisis); // Agregar al inicio
        
        // Mantener solo los últimos 1000
        if (historial.size() > 1000) {
            historial.remove(historial.size() - 1);
        }
        
        log.debug("✅ Análisis guardado en historial. Total: {}", historial.size());
    }
}