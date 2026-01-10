package com.sentiment.dto;

public class StatsResponse {
    private Long total;
    private Long positivos;
    private Long negativos;
    private Double porcentajePositivos;

    // Constructor vacío
    public StatsResponse() {
    }

    // Constructor con todos los campos
    public StatsResponse(Long total, Long positivos, Long negativos, Double porcentajePositivos) {
        this.total = total;
        this.positivos = positivos;
        this.negativos = negativos;
        this.porcentajePositivos = porcentajePositivos;
    }

    // Getters y Setters
    public Long getTotal() {
        return total;
    }

    public void setTotal(Long total) {
        this.total = total;
    }

    public Long getPositivos() {
        return positivos;
    }

    public void setPositivos(Long positivos) {
        this.positivos = positivos;
    }

    public Long getNegativoS() {
        return negativos;
    }

    public void setNegativos(Long negativos) {
        this.negativos = negativos;
    }

    public Double getPorcentajePositivos() {
        return porcentajePositivos;
    }

    public void setPorcentajePositivos(Double porcentajePositivos) {
        this.porcentajePositivos = porcentajePositivos;
    }
}