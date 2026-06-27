// Variables globales del estado
let activePeriods = [];
let allRecords = []; // Guardar registros cargados localmente para búsqueda

// Elementos de la interfaz
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const activeFilename = document.getElementById('active-filename');
const btnResetFile = document.getElementById('btn-reset-file');

const selectYear = document.getElementById('select-year');
const selectMonth = document.getElementById('select-month');
const selectMina = document.getElementById('select-mina');

const btnDownloadExcel = document.getElementById('btn-download-excel');
const btnDownloadPdf = document.getElementById('btn-download-pdf');

const currentDateIndicator = document.getElementById('current-date-indicator');

// KPIs
const kpiTotalIgv = document.getElementById('kpi-total-igv');
const kpiTotalSinIgv = document.getElementById('kpi-total-sin-igv');
const kpiTotalCant = document.getElementById('kpi-total-cant');
const kpiTransacciones = document.getElementById('kpi-transacciones');

// Visualizaciones y Tabla
const chartPlaceholder = document.getElementById('chart-placeholder');
const chartImg = document.getElementById('chart-img');
const highlightPlaceholder = document.getElementById('highlight-placeholder');
const highlightContent = document.getElementById('highlight-content');
const highlightProductName = document.getElementById('highlight-product-name');
const highlightProductCost = document.getElementById('highlight-product-cost');

const tablePlaceholder = document.getElementById('table-placeholder');
const tableContainer = document.getElementById('table-container');
const tableTbody = document.getElementById('table-tbody');
const tableSearch = document.getElementById('table-search');

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupUploadHandlers();
    setupFilterHandlers();
    setupSearchHandler();
    setupDownloadHandlers();
});

// Carga inicial de filtros y metadatos
async function initApp() {
    try {
        currentDateIndicator.innerText = `Actualizado: ${new Date().toLocaleDateString()}`;
        const response = await fetch('/api/filters');
        const data = await response.json();
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Cargar metadatos
        activeFilename.innerText = data.filename;
        activePeriods = data.periods;
        
        // Llenar selector de años
        selectYear.innerHTML = '<option value="">Selecciona año</option>';
        activePeriods.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.year;
            opt.innerText = p.year;
            selectYear.appendChild(opt);
        });
        
        // Resetear selectores dependientes
        selectMonth.innerHTML = '<option value="">Selecciona mes</option>';
        selectMonth.disabled = true;
        selectMina.innerHTML = '<option value="">Selecciona mina</option>';
        selectMina.disabled = true;
        
        // Llenar el selector de minas (permanente o por período)
        // Guardamos las minas para llenarlas después
        window.allMinas = data.minas;
        
        // Limpiar Dashboard
        resetDashboard();
        
    } catch (e) {
        console.error("Error inicializando la app:", e);
    }
}

// Limpiar Dashboard al estado inicial
function resetDashboard() {
    kpiTotalIgv.innerText = "S/ 0.00";
    kpiTotalSinIgv.innerText = "S/ 0.00";
    kpiTotalCant.innerText = "0";
    kpiTransacciones.innerText = "0";
    
    chartPlaceholder.style.display = "flex";
    chartImg.style.display = "none";
    chartImg.src = "";
    
    highlightPlaceholder.style.display = "flex";
    highlightContent.style.display = "none";
    
    tablePlaceholder.style.display = "flex";
    tableContainer.style.display = "none";
    tableTbody.innerHTML = "";
    tableSearch.value = "";
    tableSearch.disabled = true;
    
    btnDownloadExcel.disabled = true;
    btnDownloadPdf.disabled = true;
}

// --- GESTIÓN DE CARGA DE ARCHIVOS ---
function setupUploadHandlers() {
    // Clic en zona de subida abre selector
    uploadZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    // Drag and Drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    // Resetear a archivo local por defecto
    btnResetFile.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/reset', { method: 'POST' });
            const data = await response.json();
            alert(data.message);
            initApp();
        } catch (e) {
            console.error("Error al restaurar archivo por defecto:", e);
        }
    });
}

async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Mostrar feedback de carga
    activeFilename.innerText = "Cargando...";
    activeFilename.style.color = "#f59e0b";
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
            activeFilename.style.color = "#10b981";
            initApp();
        } else {
            alert(`Error: ${data.error}`);
            initApp(); // Recargar el estado actual para restaurar
        }
    } catch (e) {
        console.error("Error subiendo archivo:", e);
        alert("Ocurrió un error al subir el archivo.");
        initApp();
    }
}

// --- FILTROS REACTIVOS ---
function setupFilterHandlers() {
    // Al cambiar Año
    selectYear.addEventListener('change', () => {
        const selectedYear = selectYear.value;
        resetDashboard();
        
        if (!selectedYear) {
            selectMonth.innerHTML = '<option value="">Selecciona mes</option>';
            selectMonth.disabled = true;
            selectMina.innerHTML = '<option value="">Selecciona mina</option>';
            selectMina.disabled = true;
            return;
        }
        
        // Buscar meses del año seleccionado
        const period = activePeriods.find(p => p.year == selectedYear);
        if (period) {
            selectMonth.innerHTML = '<option value="">Selecciona mes</option>';
            period.months.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.month_num;
                opt.innerText = m.month_name;
                selectMonth.appendChild(opt);
            });
            selectMonth.disabled = false;
        }
        
        // Resetear mina
        selectMina.innerHTML = '<option value="">Selecciona mina</option>';
        selectMina.disabled = true;
    });
    
    // Al cambiar Mes
    selectMonth.addEventListener('change', () => {
        const selectedMonth = selectMonth.value;
        resetDashboard();
        
        if (!selectedMonth) {
            selectMina.innerHTML = '<option value="">Selecciona mina</option>';
            selectMina.disabled = true;
            return;
        }
        
        // Llenar selector de minas (usamos todas las minas disponibles para Taller Mina)
        selectMina.innerHTML = '<option value="">Selecciona mina</option>';
        if (window.allMinas && window.allMinas.length > 0) {
            window.allMinas.forEach(mina => {
                const opt = document.createElement('option');
                opt.value = mina;
                opt.innerText = mina;
                selectMina.appendChild(opt);
            });
            selectMina.disabled = false;
        }
    });
    
    // Al cambiar Mina -> Ejecutar Análisis
    selectMina.addEventListener('change', () => {
        const year = selectYear.value;
        const month = selectMonth.value;
        const mina = selectMina.value;
        
        if (year && month && mina) {
            runAnalysis(year, month, mina);
        } else {
            resetDashboard();
        }
    });
}

// --- CONSULTAR ANÁLISIS ---
async function runAnalysis(year, month, mina) {
    try {
        // Feedback de espera
        kpiTotalIgv.innerText = "Calculando...";
        kpiTotalSinIgv.innerText = "Calculando...";
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year, month, mina })
        });
        
        const data = await response.json();
        
        if (response.status === 404) {
            alert(data.error);
            resetDashboard();
            return;
        }
        
        if (data.error) {
            alert(`Error en análisis: ${data.error}`);
            resetDashboard();
            return;
        }
        
        // 1. Cargar KPIs
        kpiTotalIgv.innerText = `S/ ${data.metrics.total_con_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        kpiTotalSinIgv.innerText = `S/ ${data.metrics.total_sin_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        kpiTotalCant.innerText = data.metrics.total_cant.toLocaleString('es-PE');
        kpiTransacciones.innerText = data.metrics.transacciones.toLocaleString('es-PE');
        
        // 2. Cargar Gráfico
        chartPlaceholder.style.display = "none";
        chartImg.style.display = "block";
        chartImg.src = `data:image/png;base64,${data.chart}`;
        
        // 3. Highlight Producto Top
        highlightPlaceholder.style.display = "none";
        highlightContent.style.display = "block";
        highlightProductName.innerText = data.metrics.top_prod_name;
        highlightProductCost.innerText = `S/ ${data.metrics.top_prod_monto.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        
        // 4. Cargar Tabla
        allRecords = data.records;
        renderTable(allRecords);
        tablePlaceholder.style.display = "none";
        tableContainer.style.display = "block";
        tableSearch.disabled = false;
        tableSearch.value = "";
        
        // Habilitar descargas
        btnDownloadExcel.disabled = false;
        btnDownloadPdf.disabled = false;
        
    } catch (e) {
        console.error("Error al ejecutar análisis:", e);
        alert("Error al cargar el análisis de datos.");
        resetDashboard();
    }
}

// Renderizar tabla de datos
function renderTable(records) {
    tableTbody.innerHTML = "";
    
    if (records.length === 0) {
        tableTbody.innerHTML = '<tr><td colspan="9" class="text-center">No se encontraron transacciones con el término buscado.</td></tr>';
        return;
    }
    
    records.forEach(row => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td class="text-center">${row.fecha}</td>
            <td class="text-center">${row.poot}</td>
            <td>${row.producto}</td>
            <td class="text-center">${row.unidad}</td>
            <td class="text-center">${row.cantidad.toLocaleString('es-PE')}</td>
            <td class="text-right">S/ ${row.precio.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-right">S/ ${row.total.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-right">S/ ${row.total_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td>${row.observaciones}</td>
        `;
        
        tableTbody.appendChild(tr);
    });
}

// --- BÚSQUEDA RÁPIDA EN TABLA ---
function setupSearchHandler() {
    tableSearch.addEventListener('input', () => {
        const query = tableSearch.value.toLowerCase().trim();
        
        if (!query) {
            renderTable(allRecords);
            return;
        }
        
        const filtered = allRecords.filter(row => {
            return row.producto.toLowerCase().includes(query) || 
                   row.observaciones.toLowerCase().includes(query) ||
                   row.poot.includes(query);
        });
        
        renderTable(filtered);
    });
}

// --- DESCARGAS AUTOMÁTICAS ---
function setupDownloadHandlers() {
    // Descargar Excel
    btnDownloadExcel.addEventListener('click', () => triggerDownload('/api/download/excel', 'xlsx'));
    
    // Descargar PDF
    btnDownloadPdf.addEventListener('click', () => triggerDownload('/api/download/pdf', 'pdf'));
}

async function triggerDownload(url, ext) {
    const year = selectYear.value;
    const month = selectMonth.value;
    const mina = selectMina.value;
    
    if (!year || !month || !mina) return;
    
    // Deshabilitar botones durante la generación
    btnDownloadExcel.disabled = true;
    btnDownloadPdf.disabled = true;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year, month, mina })
        });
        
        if (!response.ok) {
            const err = await response.json();
            alert(`Error al generar descarga: ${err.error}`);
            btnDownloadExcel.disabled = false;
            btnDownloadPdf.disabled = false;
            return;
        }
        
        // Obtener el blob binario del archivo
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        
        // Crear un enlace invisible y simular clic
        const a = document.createElement('a');
        a.href = blobUrl;
        
        // Obtener el nombre del archivo del encabezado content-disposition si existe
        const disposition = response.headers.get('content-disposition');
        let filename = `Reporte_${mina.replace(/\s+/g, '_')}_${year}_${month}.${ext}`;
        if (disposition && disposition.indexOf('attachment') !== -1) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) { 
                filename = matches[1].replace(/['"]/g, '');
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Limpiar
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
        
    } catch (e) {
        console.error("Error al descargar archivo:", e);
        alert("Ocurrió un error al descargar el archivo de reporte.");
    } finally {
        // Habilitar de nuevo
        btnDownloadExcel.disabled = false;
        btnDownloadPdf.disabled = false;
    }
}
