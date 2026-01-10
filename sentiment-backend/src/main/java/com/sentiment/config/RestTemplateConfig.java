package com.sentiment.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * Configuración de RestTemplate para realizar peticiones HTTP
 * a la API Python (microservicio de Data Science).
 * Esta versión no requiere RestTemplateBuilder.
 */
@Configuration
public class RestTemplateConfig {
    // MODIFIED_BY_SCRIPT

    @Value("${sentiment.api.connection-timeout:5000}")
    private int connectionTimeout;

    @Value("${sentiment.api.read-timeout:10000}")
    private int readTimeout;

    /**
     * Bean de RestTemplate con timeouts configurados (sin RestTemplateBuilder)
     */
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(connectionTimeout);
        requestFactory.setReadTimeout(readTimeout);
        return new RestTemplate(requestFactory);
    }
}