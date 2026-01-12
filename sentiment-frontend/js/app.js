// ============================================
// CONFIGURACIÓN
// ============================================
const API_URL = 'https://sentiment-api-jald-c32.up.railway.app';


// ============================================
// DATOS DE SESIÓN
// ============================================
let sessionData = {
    analisis: [],
    estadisticas: {
        total: 0,
        positivos: 0,
        negativos: 0,
        promedioConfianza: 0
    }
};

// ============================================
// ELEMENTOS DEL DOM
// ============================================
const comentario = document.getElementById('comentario');
const charCount = document.getElementById('charCount');
const threshold = document.getElementById('threshold');
const thresholdDisplay = document.getElementById('thresholdDisplay');
const idioma = document.getElementById('idioma');
const btnAnalizar = document.getElementById('btnAnalizar');
const resultCard = document.getElementById('resultCard');
const errorCard = document.getElementById('errorCard');
const toggleAdvanced = document.getElementById('toggleAdvanced');
const advancedContent = document.getElementById('advancedContent');
const historyCard = document.getElementById('historyCard');
const historyList = document.getElementById('historyList');
const emptyHistory = document.getElementById('emptyHistory');

// ============================================
// NAVEGACIÓN ENTRE SECCIONES
// ============================================
const navBtns = document.querySelectorAll('.nav-btn');
const sections = {
    analizar: document.querySelector('.card:first-of-type'),
    estadisticas: document.getElementById('statsCard'),
    historial: document.getElementById('historyCard'),
    comparador: document.getElementById('comparatorCard'),
    explicabilidad: document.getElementById('explainCard'),
    batch: document.getElementById('batchCard')
};

// Inicializar navegación
navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const section = btn.dataset.section;
        
        // Remover active de todos los botones
        navBtns.forEach(b => b.classList.remove('active'));
        
        // Agregar active al botón clickeado
        btn.classList.add('active');
        
        // Ocultar todas las secciones
        Object.values(sections).forEach(s => {
            if (s) s.style.display = 'none';
        });
        
        // Mostrar la sección seleccionada
        if (sections[section]) {
            sections[section].style.display = 'block';
            sections[section].scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        // Mostrar el resultado si está en analizar
        if (section === 'analizar' && resultCard.style.display === 'block') {
            resultCard.style.display = 'block';
        }
    });
});

// Función para cambiar de sección programáticamente
function cambiarSeccion(nombreSeccion) {
    const btn = document.querySelector(`.nav-btn[data-section="${nombreSeccion}"]`);
    if (btn) btn.click();
}
document.addEventListener("DOMContentLoaded", () => {
    const tipoAnalisis = document.getElementById("tipoAnalisis");

    tipoAnalisis.addEventListener("change", (e) => {
        if (e.target.value === "batch") {
            // Usar la función ya existente
            cambiarSeccion("batch");
        } else if (e.target.value === "comparator") {
            cambiarSeccion("comparador");
        }
    });
});


// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    actualizarEstadisticas();
    console.log('✅ Sentiment Analysis Frontend cargado');
    console.log(`📡 API URL: ${API_URL}`);
});

// ============================================
// CONTADOR DE CARACTERES
// ============================================
comentario.addEventListener('input', () => {
    const count = comentario.value.length;
    charCount.textContent = count;
    charCount.style.color = count > 5000 ? '#ef4444' : '#6b7280';
});

// ============================================
// THRESHOLD SLIDER
// ============================================
threshold.addEventListener('input', (e) => {
    thresholdDisplay.textContent = parseFloat(e.target.value).toFixed(2);
});

// ============================================
// OPCIONES AVANZADAS
// ============================================
toggleAdvanced.addEventListener('click', () => {
    const arrow = toggleAdvanced.querySelector('.arrow');
    advancedContent.classList.toggle('show');
    arrow.classList.toggle('rotated');
});

// ============================================
// FUNCIÓN PRINCIPAL: ANALIZAR
// ============================================
btnAnalizar.addEventListener('click', async () => {
    const texto = comentario.value.trim();
    
    if (!texto) {
        mostrarError('Por favor, ingresa un comentario para analizar.');
        return;
    }
    
    if (texto.length < 3) {
        mostrarError('El comentario debe tener al menos 3 caracteres.');
        return;
    }
    
    if (texto.length > 5000) {
        mostrarError('El comentario no puede superar los 5000 caracteres.');
        return;
    }
    
    mostrarLoader(true);
    ocultarResultado();
    ocultarError();
    
    const datos = {
        text: texto,
        idioma: idioma.value,
        threshold: parseFloat(threshold.value)
    };
    
    try {
        const response = await fetch(`${API_URL}/sentiment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `Error ${response.status}`);
        }
        
        const resultado = await response.json();
        mostrarResultado(resultado, datos);
        guardarEnHistorial(resultado, datos);
        
    } catch (error) {
        console.error('Error:', error);
        mostrarError(`Error al conectar con el servidor: ${error.message}`);
    } finally {
        mostrarLoader(false);
    }
});

// ============================================
// MOSTRAR RESULTADO
// ============================================
function mostrarResultado(resultado, config) {
    const esPositivo = resultado.prevision === 'Positivo';
    const emoji = esPositivo ? '😊' : '😔';
    const color = esPositivo ? 'positivo' : 'negativo';
    
    document.getElementById('resultEmoji').textContent = emoji;
    document.getElementById('resultSentiment').textContent = resultado.prevision;
    document.getElementById('resultSentiment').className = `result-sentiment ${color}`;
    document.getElementById('resultProbability').textContent = `${(resultado.probabilidad * 100).toFixed(2)}%`;
    document.getElementById('resultConfidence').textContent = resultado.confianza || getNivelConfianza(resultado.probabilidad);
    document.getElementById('resultText').textContent = resultado.texto;
    document.getElementById('resultIdioma').textContent = config.idioma;
    document.getElementById('resultThreshold').textContent = config.threshold.toFixed(2);
    
    resultCard.style.display = 'block';
    setTimeout(() => resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
}

// ============================================
// GUARDAR EN HISTORIAL
// ============================================
function guardarEnHistorial(resultado, config) {
    const analisis = {
        id: Date.now(),
        texto: resultado.texto,
        prevision: resultado.prevision,
        probabilidad: resultado.probabilidad,
        confianza: resultado.confianza || getNivelConfianza(resultado.probabilidad),
        idioma: config.idioma,
        threshold: config.threshold,
        timestamp: new Date().toLocaleString()
    };
    
    sessionData.analisis.unshift(analisis);
    if (sessionData.analisis.length > 10) sessionData.analisis.pop();
    
    actualizarEstadisticas();
    actualizarHistorial();
}

// Habilitar botón de historial
document.querySelector('.nav-btn[data-section="historial"]').classList.remove('disabled');

// ============================================
// ACTUALIZAR ESTADÍSTICAS
// ============================================
function actualizarEstadisticas() {
    const stats = sessionData.estadisticas;
    const analisis = sessionData.analisis;
    
    stats.total = analisis.length;
    stats.positivos = analisis.filter(a => a.prevision === 'Positivo').length;
    stats.negativos = analisis.filter(a => a.prevision === 'Negativo').length;
    
    if (stats.total > 0) {
        const sumaProb = analisis.reduce((sum, a) => sum + a.probabilidad, 0);
        stats.promedioConfianza = (sumaProb / stats.total * 100).toFixed(2);
    } else {
        stats.promedioConfianza = 0;
    }
    
    document.getElementById('statTotal').textContent = stats.total;
    document.getElementById('statPositivos').textContent = stats.positivos;
    document.getElementById('statNegativos').textContent = stats.negativos;
    document.getElementById('statPromedio').textContent = `${stats.promedioConfianza}%`;
    
    actualizarGrafico();
}

// ============================================
// ACTUALIZAR GRÁFICO
// ============================================
function actualizarGrafico() {
    const canvas = document.getElementById('sentimentChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const stats = sessionData.estadisticas;
    
    canvas.width = 300;
    canvas.height = 300;
    
    const total = stats.positivos + stats.negativos;
    if (total === 0) {
        ctx.fillStyle = '#e5e7eb';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#6b7280';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Sin datos', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    const positivos = stats.positivos / total;
    const negativos = stats.negativos / total;
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 100;
    
    // Positivos
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, 0, positivos * 2 * Math.PI);
    ctx.closePath();
    ctx.fill();
    
    // Negativos
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, positivos * 2 * Math.PI, 2 * Math.PI);
    ctx.closePath();
    ctx.fill();
    
    // Círculo blanco central
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.6, 0, 2 * Math.PI);
    ctx.fill();
    
    // Texto
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(total, centerX, centerY - 10);
    ctx.font = '14px Arial';
    ctx.fillText('análisis', centerX, centerY + 15);
}

// ============================================
// ACTUALIZAR HISTORIAL
// ============================================
function actualizarHistorial() {
    if (sessionData.analisis.length === 0) {
        historyCard.style.display = 'none';
        emptyHistory.style.display = 'block';
        historyList.innerHTML = '';
        return;
    }
    
    historyCard.style.display = 'block';
    emptyHistory.style.display = 'none';
    
    historyList.innerHTML = sessionData.analisis.map(a => {
        const esPositivo = a.prevision === 'Positivo';
        const emoji = esPositivo ? '😊' : '😔';
        const color = esPositivo ? 'positivo' : 'negativo';
        
        return `
            <div class="history-item">
                <div class="history-emoji">${emoji}</div>
                <div class="history-details">
                    <div class="history-sentiment ${color}">${a.prevision}</div>
                    <div class="history-text">${a.texto}</div>
                    <div class="history-meta">
                        <span>📊 ${(a.probabilidad * 100).toFixed(2)}%</span>
                        <span>🎚️ Threshold: ${a.threshold}</span>
                        <span>🕐 ${a.timestamp}</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn-icon" onclick="reAnalizarTexto('${a.texto.replace(/'/g, "\\'")}', ${a.threshold})" title="Re-analizar">
                        🔄
                    </button>
                    <button class="btn-icon" onclick="eliminarDelHistorial(${a.id})" title="Eliminar">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// RE-ANALIZAR TEXTO
// ============================================
window.reAnalizarTexto = function(texto, thresholdValue) {
    comentario.value = texto;
    threshold.value = thresholdValue;
    thresholdDisplay.textContent = thresholdValue.toFixed(2);
    charCount.textContent = texto.length;
    comentario.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

// ============================================
// ELIMINAR DEL HISTORIAL
// ============================================
window.eliminarDelHistorial = function(id) {
    sessionData.analisis = sessionData.analisis.filter(a => a.id !== id);
    actualizarEstadisticas();
    actualizarHistorial();
};

// ============================================
// LIMPIAR HISTORIAL
// ============================================
document.getElementById('btnLimpiarHistorial').addEventListener('click', () => {
    if (confirm('¿Estás seguro de que quieres limpiar todo el historial?')) {
        sessionData.analisis = [];
        actualizarEstadisticas();
        actualizarHistorial();
    }
});

// ============================================
// COMPARADOR DE THRESHOLD
// ============================================
const comparatorText = document.getElementById('comparatorText');
const btnComparar = document.getElementById('btnComparar');
const comparatorCard = document.getElementById('comparatorCard');
const comparisonResults = document.getElementById('comparisonResults');

// Mostrar comparador si hay análisis
btnAnalizar.addEventListener('click', () => {
    setTimeout(() => {
        if (sessionData.analisis.length > 0) {
            document.querySelector('.nav-btn[data-section="comparador"]').classList.remove('disabled');
        }
    }, 1000);
});

btnComparar.addEventListener('click', async () => {
    const texto = comparatorText.value.trim();
    
    if (!texto || texto.length < 3) {
        mostrarError('Por favor, ingresa un texto válido para comparar.');
        return;
    }
    
    const btnText = btnComparar.querySelector('.btn-text');
    const btnLoader = btnComparar.querySelector('.btn-loader');
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';
    btnComparar.disabled = true;
    
    const thresholds = [0.3, 0.5, 0.7];
    
    try {
        const promesas = thresholds.map(t => 
            fetch(`${API_URL}/sentiment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: texto, idioma: 'auto', threshold: t })
            }).then(r => r.json())
        );
        
        const resultados = await Promise.all(promesas);
        
        resultados.forEach((resultado, index) => {
            const t = thresholds[index];
            const id = `result_${String(t).replace('.', '')}`;
            const elem = document.getElementById(id);
            const esPositivo = resultado.prevision === 'Positivo';
            
            elem.innerHTML = `
                <div class="comp-sentiment ${esPositivo ? 'positivo' : 'negativo'}">
                    ${esPositivo ? '😊' : '😔'} ${resultado.prevision}
                </div>
                <div class="comp-probability">
                    ${(resultado.probabilidad * 100).toFixed(2)}%
                </div>
            `;
        });
        
        comparisonResults.style.display = 'block';
        setTimeout(() => comparisonResults.scrollIntoView({ behavior: 'smooth' }), 100);
        
    } catch (error) {
        mostrarError('Error al comparar thresholds: ' + error.message);
    } finally {
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
        btnComparar.disabled = false;
    }
});

// ============================================
// FUNCIONES AUXILIARES
// ============================================
function getNivelConfianza(probabilidad) {
    if (probabilidad >= 0.9) return 'Muy Alta';
    if (probabilidad >= 0.75) return 'Alta';
    if (probabilidad >= 0.6) return 'Media';
    return 'Baja';
}

function mostrarError(mensaje) {
    document.getElementById('errorMessage').textContent = mensaje;
    errorCard.style.display = 'block';
    setTimeout(() => errorCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
}

function ocultarResultado() {
    resultCard.style.display = 'none';
}

function ocultarError() {
    errorCard.style.display = 'none';
}

function mostrarLoader(mostrar) {
    const btnText = btnAnalizar.querySelector('.btn-text');
    const btnLoader = btnAnalizar.querySelector('.btn-loader');
    
    if (mostrar) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        btnAnalizar.disabled = true;
    } else {
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
        btnAnalizar.disabled = false;
    }
}

// ============================================
// BOTONES DE ACCIÓN
// ============================================

document.getElementById('btnDescartar').addEventListener('click', () => {
    ocultarResultado();
    comentario.value = '';
    charCount.textContent = '0';
    comentario.focus();
});

document.getElementById('btnCerrarError').addEventListener('click', ocultarError);

// ============================================
// ENLACES DEL FOOTER
// ============================================
document.getElementById('linkDocs').addEventListener('click', (e) => {
    e.preventDefault();
    window.open('http://localhost:8000/docs', '_blank');
});

document.getElementById('linkGithub').addEventListener('click', (e) => {
    e.preventDefault();
    alert('🔗 Link de GitHub próximamente...');
});

document.getElementById('linkAPI').addEventListener('click', (e) => {
    e.preventDefault();
    window.open('http://localhost:8080/api/health', '_blank');
});


// ============================================
// EXPLICABILIDAD
// ============================================
const explainCard = document.getElementById('explainCard');
let ultimoTextoAnalizado = '';
let ultimoResultado = null;

// Habilitar explicabilidad después de un análisis
btnAnalizar.addEventListener('click', () => {
    setTimeout(() => {
        if (sessionData.analisis.length > 0) {
            const navBtn = document.querySelector('.nav-btn[data-section="explicabilidad"]');
            if (navBtn) navBtn.classList.remove('disabled');
        }
    }, 1000);
});

// Botón para ver explicabilidad desde resultado
document.getElementById('btnGuardar').addEventListener('click', async () => {
    if (!ultimoTextoAnalizado) {
        alert('⚠️ No hay análisis para explicar. Realiza un análisis primero.');
        return;
    }
    
    await mostrarExplicabilidad(ultimoTextoAnalizado);
});

// Función para mostrar explicabilidad
async function mostrarExplicabilidad(texto) {
    try {
        // Cambiar a la sección de explicabilidad
        cambiarSeccion('explicabilidad');
        
        // Mostrar loader en la card
        const explainContent = document.getElementById('explainContent');
        explainContent.innerHTML = '<div style="text-align: center; padding: 40px;"><span class="spinner"></span> Analizando palabras...</div>';
        
        // Llamar al endpoint
        const response = await fetch(`${API_URL}/sentiment/explain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: texto,
                idioma: 'auto',
                topN: 10
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Error response:', errorData);
            throw new Error(errorData.detail || `Error HTTP ${response.status} al obtener explicabilidad`);
        }
        
        const resultado = await response.json();
        
        // Log para debug
        console.log('Resultado de explicabilidad:', resultado);
        
        // Validar que la respuesta tenga los datos necesarios
        if (!resultado) {
            throw new Error('Respuesta vacía del servidor');
        }
        
        mostrarResultadoExplicabilidad(resultado);
        
    } catch (error) {
        console.error('Error en mostrarExplicabilidad:', error);
        mostrarError('Error al obtener explicabilidad: ' + error.message);
    }
}

// Función para mostrar resultado de explicabilidad
function mostrarResultadoExplicabilidad(resultado) {
    const explainText = document.getElementById('explainText');
    const topWords = document.getElementById('topWords');
    
    // Resaltar palabras en el texto
    let textoResaltado = resultado.texto;
    
    // Adaptar estructura: aceptar array o objeto con índices numéricos
    let palabrasArray = [];
    if (Array.isArray(resultado.palabrasImportantes)) {
        palabrasArray = resultado.palabrasImportantes.map(p => ({
            palabra: p.palabra,
            importancia: p.importancia ?? p.peso ?? 0
        }));
    } else if (typeof resultado.palabrasImportantes === 'object' && resultado.palabrasImportantes !== null) {
        palabrasArray = Object.values(resultado.palabrasImportantes).map(p => ({
            palabra: p.palabra,
            importancia: p.importancia ?? p.peso ?? 0
        }));
    }

    
    
    // Ordenar palabras por importancia
    const palabrasOrdenadas = [...palabrasArray].sort(
        (a, b) => b.importancia - a.importancia
    );
    
    // Resaltar cada palabra en el texto
    palabrasOrdenadas.forEach(palabra => {
        if (!palabra.palabra || palabra.importancia === undefined) {
            console.warn('Palabra incompleta:', palabra);
            return;
        }
        
        const regex = new RegExp(`\\b${palabra.palabra}\\b`, 'gi');
        const clase = resultado.prevision === 'Positivo' ? 'positive' : 'negative';
        const importanciaPortcentaje = (typeof palabra.importancia === 'number') 
            ? palabra.importancia * 10 
            : 0;
        
        textoResaltado = textoResaltado.replace(
            regex, 
            `<span class="word-highlight ${clase}" title="Importancia: ${importanciaPortcentaje.toFixed(1)}%">${palabra.palabra}</span>`
        );
    });
    
    const explainContent = document.getElementById('explainContent');
    if (!explainContent) {
        console.error('Elemento explainContent no encontrado');
        mostrarError('Error: No se puede mostrar explicabilidad');
        return;
    }
    
    // Limpiar contenido anterior
    explainContent.innerHTML = '';
    
    // Construir HTML con los elementos necesarios
    explainContent.innerHTML = `
        <div class="explain-text" id="explainText">
            ${textoResaltado}
        </div>
        
        <div class="top-words">
            <h3>🎯 Palabras más influyentes:</h3>
            <div class="words-grid" id="topWords">
                ${palabrasOrdenadas.map((palabra, index) => {
                    const esPositivo = resultado.prevision === 'Positivo';
                    const importanciaPortcentaje = (typeof palabra.importancia === 'number') 
                        ? palabra.importancia * 10 
                        : 0;
                    
                    return `
                        <div class="word-item ${esPositivo ? 'positive' : 'negative'}">
                            <div>
                                <span style="color: #9ca3af; font-size: 12px;">#${index + 1}</span>
                                <span class="word-name">${palabra.palabra}</span>
                            </div>
                            <span class="word-score">${importanciaPortcentaje.toFixed(1)}%</span>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
    
    // Agregar info adicional
    const infoDiv = document.createElement('div');
    infoDiv.className = 'explain-info';
    infoDiv.innerHTML = `
        <div style="background: #f0f9ff; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <p style="margin-bottom: 10px;"><strong>📊 Resultado:</strong> 
                <span style="color: ${resultado.prevision === 'Positivo' ? '#10b981' : '#ef4444'}; font-weight: 700;">
                    ${resultado.prevision}
                </span> 
                (${(resultado.probabilidad * 100).toFixed(2)}%)
            </p>
            <p><strong>💡 Interpretación:</strong> Las palabras resaltadas son las que más influyeron en la decisión del modelo. 
            Las palabras en <span class="word-highlight positive">verde</span> contribuyen a un sentimiento positivo, 
            mientras que las <span class="word-highlight negative">rojas</span> indican sentimiento negativo.</p>
        </div>
    `;
    
    explainContent.appendChild(infoDiv);
}


// Guardar texto del último análisis
const analisisOriginal = btnAnalizar.onclick;
btnAnalizar.addEventListener('click', async function(e) {
    const texto = comentario.value.trim();
    if (texto.length >= 3) {
        ultimoTextoAnalizado = texto;
    }
});



// ============================================
// ANÁLISIS BATCH (CSV)
// ============================================
const batchCard = document.getElementById('batchCard');
const btnBatch = document.getElementById('btnBatch');
const batchLoader = document.getElementById('batchLoader');
const batchResults = document.getElementById('batchResults');
const csvFileInput = document.getElementById('csvFile');
const btnSelectFile = document.getElementById('btnSelectFile');
const fileName = document.getElementById('fileName');

// Manejar clic en botón personalizado
btnSelectFile.addEventListener('click', () => {
    csvFileInput.click();
});

// Actualizar nombre del archivo seleccionado
csvFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    
    if (file) {
        fileName.textContent = `✅ ${file.name}`;
        fileName.classList.add('selected');
    } else {
        fileName.textContent = 'Ningún archivo seleccionado';
        fileName.classList.remove('selected');
    }
});

let resultadosBatch = [];

btnBatch.addEventListener('click', async () => {
    const file = csvFileInput.files[0];
    
    if (!file) {
        mostrarError('Por favor selecciona un archivo CSV');
        return;
    }
    
    if (!file.name.endsWith('.csv')) {
        mostrarError('El archivo debe ser formato CSV');
        return;
    }
    
    await procesarCSV(file);
});

async function procesarCSV(file) {
    try {
        // Mostrar loader
        batchLoader.style.display = 'block';
        batchResults.style.display = 'none';
        btnBatch.disabled = true;
        
        // Inicializar barra de progreso
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('batchProgress');
        progressBar.style.width = '0%';
        progressText.textContent = '';
        
        // Fase 1: Leer archivo (0-20%)
        animarProgreso(progressBar, 0, 20, 500);
        const textos = await leerCSV(file);
        
        if (textos.length === 0) {
            throw new Error('El archivo CSV está vacío o no tiene columna "texto"');
        }
        
        if (textos.length > 1000) {
            throw new Error('Máximo 1000 filas. Tu archivo tiene ' + textos.length);
        }
        
        // Fase 2: Preparar datos (20-30%)
        animarProgreso(progressBar, 20, 30, 300);
        progressText.textContent = `Preparando ${textos.length} textos...`;
        
        await esperar(300);
        
        // Preparar request
        const idioma = document.getElementById('batchIdioma').value;
        const request = {
            textos: textos,
            idioma: idioma
        };
        
        // Fase 3: Enviar al servidor (30-70%)
        animarProgreso(progressBar, 30, 70, 500);
        progressText.textContent = `Analizando ${textos.length} textos...`;
        
        // Enviar al backend
        const response = await fetch(`${API_URL}/sentiment/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al procesar el archivo');
        }
        
        // Fase 4: Procesar respuesta (70-90%)
        animarProgreso(progressBar, 70, 90, 400);
        progressText.textContent = 'Procesando resultados...';
        
        const resultado = await response.json();
        resultadosBatch = resultado.resultados;
        
        await esperar(300);
        
        // Fase 5: Finalizar (90-100%)
        animarProgreso(progressBar, 90, 100, 300);
        progressText.textContent = '¡Completado!';
        
        await esperar(400);
        
        // Mostrar resultados
        mostrarResultadosBatch(resultado);
        
        // Habilitar navegación a batch
        document.querySelector('.nav-btn[data-section="batch"]').classList.remove('disabled');
        
    } catch (error) {
        console.error('Error procesando CSV:', error);
        mostrarError('Error: ' + error.message);
    } finally {
        batchLoader.style.display = 'none';
        btnBatch.disabled = false;
    }
}

// Función auxiliar para animar la barra de progreso
function animarProgreso(progressBar, desde, hasta, duracion) {
    const inicio = Date.now();
    const diferencia = hasta - desde;
    
    return new Promise(resolve => {
        function actualizar() {
            const transcurrido = Date.now() - inicio;
            const progreso = Math.min(transcurrido / duracion, 1);
            const valorActual = desde + (diferencia * progreso);
            
            progressBar.style.width = valorActual + '%';
            
            if (progreso < 1) {
                requestAnimationFrame(actualizar);
            } else {
                resolve();
            }
        }
        
        actualizar();
    });
}

// Función auxiliar para esperar
function esperar(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function leerCSV(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            try {
                const texto = e.target.result;
                const lineas = texto.split('\n').filter(l => l.trim());
                
                if (lineas.length < 2) {
                    reject(new Error('CSV vacío o sin datos'));
                    return;
                }
                
                // Parsear header
                const header = lineas[0].split(',').map(h => h.trim().toLowerCase());
                const indiceTexto = header.indexOf('texto');
                
                if (indiceTexto === -1) {
                    reject(new Error('El CSV debe tener una columna llamada "texto"'));
                    return;
                }
                
                // Extraer textos
                const textos = [];
                for (let i = 1; i < lineas.length; i++) {
                    const columnas = lineas[i].split(',');
                    if (columnas[indiceTexto] && columnas[indiceTexto].trim()) {
                        textos.push(columnas[indiceTexto].trim().replace(/^"|"$/g, ''));
                    }
                }
                
                resolve(textos);
                
            } catch (error) {
                reject(error);
            }
        };
        
        reader.onerror = () => reject(new Error('Error al leer el archivo'));
        reader.readAsText(file);
    });
}

function mostrarResultadosBatch(resultado) {
    // Calcular porcentaje si no viene del backend
    const porcentaje = resultado.porcentajePositivos != null 
        ? resultado.porcentajePositivos 
        : (resultado.total > 0 ? (resultado.positivos * 100.0 / resultado.total) : 0);
    
    const porcentajeNegativos = 100 - porcentaje;
    
    // Actualizar estadísticas VISIBLES
    document.getElementById('batchTotal').textContent = resultado.total;
    document.getElementById('batchPositivos').textContent = resultado.positivos;
    document.getElementById('batchNegativos').textContent = resultado.negativos;
    document.getElementById('batchPorcentaje').textContent = porcentaje.toFixed(2) + '%';
    
    // Generar mensaje descriptivo
    const mensajeElement = document.getElementById('batchMessage');
    if (mensajeElement) {
        mensajeElement.innerHTML = `
            Se procesaron un total de <strong>${resultado.total}</strong> textos, 
            de los cuales <strong>${porcentaje.toFixed(2)}%</strong> son positivos 
            (<strong>${resultado.positivos}</strong> textos) y 
            <strong>${porcentajeNegativos.toFixed(2)}%</strong> son negativos 
            (<strong>${resultado.negativos}</strong> textos).
            Los resultados detallados de cada texto se encuentran en los archivos descargables
            en los botones arriba de los resultados.
        `;
    }
    
    // Dibujar gráfico de pastel
    dibujarGraficoBatch(resultado.positivos, resultado.negativos, porcentaje);
    
    // Llenar tabla OCULTA (solo para descargas)
    const tbody = document.getElementById('batchTableBody');
    tbody.innerHTML = '';
    
    resultado.resultados.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.texto}</td>
            <td>${item.prevision}</td>
            <td>${(item.probabilidad * 100).toFixed(2)}%</td>
            <td>${item.confianza}</td>
        `;
        tbody.appendChild(tr);
    });
    
    // Mostrar resultados
    batchResults.style.display = 'block';
    
    // Scroll suave hacia los resultados
    setTimeout(() => {
        batchResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

// Función para dibujar el gráfico de pastel
function dibujarGraficoBatch(positivos, negativos, porcentajePositivos) {
    const canvas = document.getElementById('batchChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Limpiar canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const total = positivos + negativos;
    if (total === 0) {
        // Mostrar mensaje si no hay datos
        ctx.fillStyle = '#e5e7eb';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#6b7280';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Sin datos', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 120;
    
    // Calcular ángulos
    const positivosAngle = (positivos / total) * 2 * Math.PI;
    
    // Dibujar sector POSITIVO (verde)
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + positivosAngle);
    ctx.closePath();
    ctx.fill();
    
    // Dibujar sector NEGATIVO (rojo)
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, -Math.PI / 2 + positivosAngle, -Math.PI / 2 + 2 * Math.PI);
    ctx.closePath();
    ctx.fill();
    
    // Dibujar círculo blanco central (efecto donut)
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.6, 0, 2 * Math.PI);
    ctx.fill();
    
    // Dibujar texto en el centro
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total, centerX, centerY - 10);
    
    ctx.font = '14px Arial';
    ctx.fillStyle = '#6b7280';
    ctx.fillText('textos', centerX, centerY + 15);
    
    // Dibujar etiquetas con porcentajes
    if (positivos > 0) {
        const posAngle = -Math.PI / 2 + positivosAngle / 2;
        const posX = centerX + Math.cos(posAngle) * (radius * 0.75);
        const posY = centerY + Math.sin(posAngle) * (radius * 0.75);
        
        ctx.fillStyle = 'white';
        ctx.font = 'bold 16px Arial';
        ctx.fillText(`${porcentajePositivos.toFixed(1)}%`, posX, posY);
        ctx.font = '12px Arial';
        ctx.fillText(`${positivos}`, posX, posY + 18);
    }
    
    if (negativos > 0) {
        const negAngle = -Math.PI / 2 + positivosAngle + ((2 * Math.PI - positivosAngle) / 2);
        const negX = centerX + Math.cos(negAngle) * (radius * 0.82); // ← Cambié 0.75 a 0.85
        const negY = centerY + Math.sin(negAngle) * (radius * 0.82); // ← Cambié 0.75 a 0.85
    
        ctx.fillStyle = 'white';
        ctx.font = 'bold 16px Arial'; 
        ctx.fillText(`${(100 - porcentajePositivos).toFixed(1)}%`, negX, negY);
        ctx.font = 'bold 14px Arial'; // 
        ctx.fillText(`${negativos}`, negX, negY + 18); 
    }
}


// Descargar resultados como CSV
document.getElementById('btnDownloadCSV').addEventListener('click', () => {
    if (resultadosBatch.length === 0) {
        mostrarError('No hay resultados para descargar');
        return;
    }
    
    let csv = 'numero,texto,sentimiento,probabilidad,confianza\n';
    
    resultadosBatch.forEach((item, index) => {
        const probabilidadPorcentaje = (item.probabilidad * 100).toFixed(2);
        csv += `${index + 1},"${item.texto.replace(/"/g, '""')}","${item.prevision}","${probabilidadPorcentaje}%","${item.confianza}"\n`;
    });
    
    descargarArchivo(csv, 'resultados_batch.csv', 'text/csv');
});

// Descargar resultados como JSON
document.getElementById('btnDownloadJSON').addEventListener('click', () => {
    if (resultadosBatch.length === 0) {
        mostrarError('No hay resultados para descargar');
        return;
    }
    
    const datosExportacion = resultadosBatch.map((item, index) => ({
        numero: index + 1,
        texto: item.texto,
        sentimiento: item.prevision,
        probabilidad: `${(item.probabilidad * 100).toFixed(2)}%`,
        confianza: item.confianza
    }));
    
    const json = JSON.stringify({
        fecha: new Date().toISOString(),
        total: resultadosBatch.length,
        positivos: resultadosBatch.filter(r => r.prevision === 'Positivo').length,
        negativos: resultadosBatch.filter(r => r.prevision === 'Negativo').length,
        resultados: datosExportacion
    }, null, 2);
    
    descargarArchivo(json, 'resultados_batch.json', 'application/json');
});

function descargarArchivo(contenido, nombreArchivo, tipoMIME) {
    const blob = new Blob([contenido], { type: tipoMIME });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombreArchivo;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}


// ============================================
// ATAJO: Ctrl + Enter
// ============================================
comentario.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') btnAnalizar.click();
});
