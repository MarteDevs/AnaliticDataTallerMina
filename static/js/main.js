// Variables globales del estado
let activePeriods = [];
let allRecords = []; // Guardar registros cargados localmente para búsqueda y paginación
let currentTab = 'individual'; // individual | consolidated

// Estado de paginación
let currentPage = 1;
const recordsPerPage = 20;

// Caché de consolidado en cliente
const consolidatedCache = {};

// Elementos de la interfaz - Barra lateral
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const activeFilename = document.getElementById('active-filename');
const btnResetFile = document.getElementById('btn-reset-file');

const selectYear = document.getElementById('select-year');
const selectMonth = document.getElementById('select-month');
const selectMina = document.getElementById('select-mina');
const sidebarMinaGroup = document.getElementById('sidebar-mina-group');

const btnDownloadExcel = document.getElementById('btn-download-excel');
const btnDownloadPdf = document.getElementById('btn-download-pdf');
const btnDownloadConsolidated = document.getElementById('btn-download-consolidated');

const sidebarDownloadIndividual = document.getElementById('sidebar-download-individual');
const sidebarDownloadConsolidated = document.getElementById('sidebar-download-consolidated');
const currentDateIndicator = document.getElementById('current-date-indicator');

// Elementos de navegación de pestañas
const tabBtnIndividual = document.getElementById('tab-btn-individual');
const tabBtnConsolidated = document.getElementById('tab-btn-consolidated');
const viewIndividualSection = document.getElementById('view-individual-section');
const viewConsolidatedSection = document.getElementById('view-consolidated-section');

// Elementos - KPIs Vista Individual
const kpiTotalIgv = document.getElementById('kpi-total-igv');
const kpiTotalSinIgv = document.getElementById('kpi-total-sin-igv');
const kpiTotalCant = document.getElementById('kpi-total-cant');
const kpiTransacciones = document.getElementById('kpi-transacciones');

// Elementos - Visualizaciones y Tabla Individual
const chartPlaceholder = document.getElementById('chart-placeholder');
const chartImg = document.getElementById('chart-img');
const chartSkeleton = document.getElementById('chart-skeleton');
const highlightPlaceholder = document.getElementById('highlight-placeholder');
const highlightContent = document.getElementById('highlight-content');
const highlightProductName = document.getElementById('highlight-product-name');
const highlightProductCost = document.getElementById('highlight-product-cost');

const tablePlaceholder = document.getElementById('table-placeholder');
const tableContainer = document.getElementById('table-container');
const tableSkeleton = document.getElementById('table-skeleton');
const tableTbody = document.getElementById('table-tbody');
const tableSearch = document.getElementById('table-search');

// Elementos de Paginación
const paginationContainer = document.getElementById('pagination-container');
const paginationInfo = document.getElementById('pagination-info');
const btnPagePrev = document.getElementById('btn-page-prev');
const btnPageNext = document.getElementById('btn-page-next');

// Elementos - Vista Consolidada
const consolidatedMinasPlaceholder = document.getElementById('consolidated-minas-placeholder');
const minasCheckboxGrid = document.getElementById('minas-checkbox-grid');
const btnSelectAllMinas = document.getElementById('btn-select-all-minas');
const btnDeselectAllMinas = document.getElementById('btn-deselect-all-minas');
const minaSearch = document.getElementById('mina-search');

const consolidatedTablePlaceholder = document.getElementById('consolidated-table-placeholder');
const consolidatedTableContainer = document.getElementById('consolidated-table-container');
const consolidatedTableTbody = document.getElementById('consolidated-table-tbody');
const btnDownloadConsolidatedInline = document.getElementById('btn-download-consolidated-inline');

// Totales de tabla consolidada
const consolidatedTotalTrans = document.getElementById('consolidated-total-trans');
const consolidatedTotalSinIgv = document.getElementById('consolidated-total-sin-igv');
const consolidatedTotalConIgv = document.getElementById('consolidated-total-con-igv');

// Contenedor Toast
const toastContainer = document.getElementById('toast-container');

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupUploadHandlers();
    setupTabNavigation();
    setupFilterHandlers();
    setupSearchHandler();
    setupDownloadHandlers();
    setupConsolidatedActions();
    setupPaginationHandlers();
});

// Función Utilitaria: Debounce (para evitar sobrecarga de DOM en búsquedas)
function debounce(func, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

// Sistema de Notificaciones Toast Flotantes Premium
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fa-circle-info';
    if (type === 'success') iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-circle-xmark';
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass} toast-icon"></i>
        <div class="toast-message">${message}</div>
        <button class="toast-close" title="Cerrar"><i class="fa-solid fa-xmark"></i></button>
    `;
    
    // Acción del botón cerrar
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    });
    
    toastContainer.appendChild(toast);
    
    // Animación de entrada
    setTimeout(() => toast.classList.add('show'), 50);
    
    // Auto-eliminar tras 4.5 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }
    }, 4500);
}

// Carga inicial de filtros y metadatos
async function initApp() {
    try {
        currentDateIndicator.innerText = `Actualizado: ${new Date().toLocaleDateString()}`;
        const response = await fetch('/api/filters');
        const data = await response.json();
        
        if (data.error) {
            showToast(`Error al inicializar filtros: ${data.error}`, 'error');
            return;
        }
        
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
        
        window.allMinas = data.minas;
        
        // Resetear displays
        resetDashboard();
        resetConsolidatedView();
        
    } catch (e) {
        console.error("Error inicializando la app:", e);
        showToast("Error crítico inicializando la app.", "error");
    }
}

// --- NAVEGACIÓN ENTRE PESTAÑAS ---
function setupTabNavigation() {
    tabBtnIndividual.addEventListener('click', () => switchTab('individual'));
    tabBtnConsolidated.addEventListener('click', () => switchTab('consolidated'));
}

function switchTab(tab) {
    currentTab = tab;
    
    if (tab === 'individual') {
        tabBtnIndividual.classList.add('active');
        tabBtnConsolidated.classList.remove('active');
        viewIndividualSection.style.display = 'flex';
        viewConsolidatedSection.style.display = 'none';
        
        sidebarMinaGroup.style.display = 'block';
        sidebarDownloadIndividual.style.display = 'block';
        sidebarDownloadConsolidated.style.display = 'none';
        
        const year = selectYear.value;
        const month = selectMonth.value;
        const mina = selectMina.value;
        if (year && month && mina) {
            runAnalysis(year, month, mina);
        } else {
            resetDashboard();
        }
    } else {
        tabBtnIndividual.classList.remove('active');
        tabBtnConsolidated.classList.add('active');
        viewIndividualSection.style.display = 'none';
        viewConsolidatedSection.style.display = 'flex';
        
        sidebarMinaGroup.style.display = 'none';
        sidebarDownloadIndividual.style.display = 'none';
        sidebarDownloadConsolidated.style.display = 'block';
        
        const year = selectYear.value;
        const month = selectMonth.value;
        if (year && month) {
            renderMinasCheckboxes();
        } else {
            resetConsolidatedView();
        }
    }
}

// Limpiar Dashboard Individual al estado inicial
function resetDashboard() {
    kpiTotalIgv.innerText = "S/ 0.00";
    kpiTotalSinIgv.innerText = "S/ 0.00";
    kpiTotalCant.innerText = "0";
    kpiTransacciones.innerText = "0";
    
    chartPlaceholder.style.display = "flex";
    chartImg.style.display = "none";
    chartSkeleton.style.display = "none";
    chartImg.src = "";
    
    highlightPlaceholder.style.display = "flex";
    highlightContent.style.display = "none";
    
    tablePlaceholder.style.display = "flex";
    tableContainer.style.display = "none";
    tableSkeleton.style.display = "none";
    paginationContainer.style.display = "none";
    tableTbody.innerHTML = "";
    tableSearch.value = "";
    tableSearch.disabled = true;
    
    btnDownloadExcel.disabled = true;
    btnDownloadPdf.disabled = true;
}

// Limpiar Vista Consolidada al estado inicial
function resetConsolidatedView() {
    consolidatedMinasPlaceholder.style.display = "flex";
    minasCheckboxGrid.style.display = "none";
    minasCheckboxGrid.innerHTML = "";
    minaSearch.value = "";
    
    consolidatedTablePlaceholder.style.display = "flex";
    consolidatedTableContainer.style.display = "none";
    consolidatedTableTbody.innerHTML = "";
    
    consolidatedTotalTrans.innerText = "0";
    consolidatedTotalSinIgv.innerText = "S/ 0.00";
    consolidatedTotalConIgv.innerText = "S/ 0.00";
    
    btnDownloadConsolidated.disabled = true;
    btnDownloadConsolidatedInline.disabled = true;
}

// --- GESTIÓN DE CARGA DE ARCHIVOS ---
function setupUploadHandlers() {
    uploadZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
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
    
    btnResetFile.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/reset', { method: 'POST' });
            const data = await response.json();
            showToast(data.message, 'success');
            initApp();
        } catch (e) {
            console.error("Error al restaurar archivo por defecto:", e);
            showToast("Error al restaurar base de datos.", 'error');
        }
    });
}

async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    activeFilename.innerText = "Cargando...";
    activeFilename.style.color = "#f59e0b";
    showToast("Subiendo base de datos y pre-calculando...", 'info');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            activeFilename.style.color = "#10b981";
            initApp();
        } else {
            showToast(`Error al cargar: ${data.error}`, 'error');
            activeFilename.style.color = "#ef4444";
            initApp();
        }
    } catch (e) {
        console.error("Error subiendo archivo:", e);
        showToast("Ocurrió un error al subir el archivo.", 'error');
        initApp();
    }
}

// --- FILTROS REACTIVOS ---
function setupFilterHandlers() {
    selectYear.addEventListener('change', () => {
        const selectedYear = selectYear.value;
        resetDashboard();
        resetConsolidatedView();
        
        if (!selectedYear) {
            selectMonth.innerHTML = '<option value="">Selecciona mes</option>';
            selectMonth.disabled = true;
            selectMina.innerHTML = '<option value="">Selecciona mina</option>';
            selectMina.disabled = true;
            return;
        }
        
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
        
        selectMina.innerHTML = '<option value="">Selecciona mina</option>';
        selectMina.disabled = true;
    });
    
    selectMonth.addEventListener('change', () => {
        const selectedMonth = selectMonth.value;
        resetDashboard();
        resetConsolidatedView();
        
        if (!selectedMonth) {
            selectMina.innerHTML = '<option value="">Selecciona mina</option>';
            selectMina.disabled = true;
            return;
        }
        
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
        
        if (currentTab === 'consolidated') {
            renderMinasCheckboxes();
        }
    });
    
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

// --- RENDERING CHECKBOXES DE MINAS (VISTA CONSOLIDADA) ---
function renderMinasCheckboxes() {
    if (!window.allMinas || window.allMinas.length === 0) return;
    
    consolidatedMinasPlaceholder.style.display = "none";
    minasCheckboxGrid.innerHTML = "";
    minasCheckboxGrid.style.display = "grid";
    minaSearch.value = "";
    
    window.allMinas.forEach(mina => {
        const div = document.createElement('div');
        div.className = 'mina-checkbox-item';
        div.dataset.mina = mina;
        
        div.innerHTML = `
            <input type="checkbox" id="chk-${mina.replace(/\s+/g, '-')}" value="${mina}">
            <span title="${mina}">${mina}</span>
        `;
        
        div.addEventListener('click', (e) => {
            const chk = div.querySelector('input[type="checkbox"]');
            if (e.target !== chk) {
                chk.checked = !chk.checked;
            }
            
            if (chk.checked) {
                div.classList.add('checked');
            } else {
                div.classList.remove('checked');
            }
            
            updateConsolidatedSummary();
        });
        
        minasCheckboxGrid.appendChild(div);
    });
    
    consolidatedTablePlaceholder.style.display = "flex";
    consolidatedTableContainer.style.display = "none";
    consolidatedTableTbody.innerHTML = "";
    btnDownloadConsolidated.disabled = true;
    btnDownloadConsolidatedInline.disabled = true;
}

// Acciones grupales de selección de minas (con soporte de debounce en búsquedas)
function setupConsolidatedActions() {
    btnSelectAllMinas.addEventListener('click', () => {
        const items = minasCheckboxGrid.querySelectorAll('.mina-checkbox-item');
        items.forEach(item => {
            if (item.style.display !== 'none') {
                const chk = item.querySelector('input[type="checkbox"]');
                chk.checked = true;
                item.classList.add('checked');
            }
        });
        updateConsolidatedSummary();
    });
    
    btnDeselectAllMinas.addEventListener('click', () => {
        const items = minasCheckboxGrid.querySelectorAll('.mina-checkbox-item');
        items.forEach(item => {
            if (item.style.display !== 'none') {
                const chk = item.querySelector('input[type="checkbox"]');
                chk.checked = false;
                item.classList.remove('checked');
            }
        });
        updateConsolidatedSummary();
    });
    
    // Buscador interactivo de minas con debounce de 100ms
    minaSearch.addEventListener('input', debounce(() => {
        const query = minaSearch.value.toLowerCase().trim();
        const items = minasCheckboxGrid.querySelectorAll('.mina-checkbox-item');
        
        items.forEach(item => {
            const minaName = item.dataset.mina.toLowerCase();
            if (!query || minaName.includes(query)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }, 100));
}

// --- ACTUALIZAR RESUMEN PREVIO CONSOLIDADO (CON SOPORTE DE CACHÉ DE CLIENTE) ---
async function updateConsolidatedSummary() {
    const year = selectYear.value;
    const month = selectMonth.value;
    
    const selectedMinas = [];
    const checkeds = minasCheckboxGrid.querySelectorAll('input[type="checkbox"]:checked');
    checkeds.forEach(chk => selectedMinas.push(chk.value));
    
    if (selectedMinas.length === 0) {
        consolidatedTablePlaceholder.style.display = "flex";
        consolidatedTableContainer.style.display = "none";
        consolidatedTableTbody.innerHTML = "";
        btnDownloadConsolidated.disabled = true;
        btnDownloadConsolidatedInline.disabled = true;
        return;
    }
    
    // Generar llave de cache única
    const cacheKey = `${year}_${month}_${[...selectedMinas].sort().join(',')}`;
    
    // Verificar caché
    if (consolidatedCache[cacheKey]) {
        renderConsolidatedSummary(consolidatedCache[cacheKey]);
        return;
    }
    
    try {
        consolidatedTablePlaceholder.style.display = "none";
        consolidatedTableContainer.style.display = "block";
        consolidatedTableTbody.innerHTML = '<tr><td colspan="4" class="text-center">Calculando costos agregados...</td></tr>';
        
        const response = await fetch('/api/consolidated/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year, month, minas: selectedMinas })
        });
        
        const data = await response.json();
        
        if (data.error) {
            consolidatedTableTbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error: ${data.error}</td></tr>`;
            btnDownloadConsolidated.disabled = true;
            btnDownloadConsolidatedInline.disabled = true;
            return;
        }
        
        // Almacenar en caché local
        consolidatedCache[cacheKey] = data;
        
        renderConsolidatedSummary(data);
        
    } catch (e) {
        console.error("Error cargando resumen consolidado:", e);
        consolidatedTableTbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Ocurrió un error al calcular los montos.</td></tr>';
    }
}

// Pintar la tabla y totales consolidados
function renderConsolidatedSummary(data) {
    consolidatedTableTbody.innerHTML = "";
    
    if (data.rows.length === 0) {
        consolidatedTableTbody.innerHTML = '<tr><td colspan="4" class="text-center">No se encontraron movimientos para las áreas seleccionadas en este período.</td></tr>';
        btnDownloadConsolidated.disabled = true;
        btnDownloadConsolidatedInline.disabled = true;
        return;
    }
    
    data.rows.forEach(row => {
        const tr = document.createElement('tr');
        if (row.sin_datos) {
            tr.style.opacity = '0.55';
            tr.innerHTML = `
                <td><strong>${row.mina}</strong> <span class="badge" style="background-color: rgba(255,255,255,0.05); color: var(--text-muted); font-size: 0.72rem; padding: 2px 6px; margin-left: 8px; border: 1px solid rgba(255,255,255,0.08); border-radius: 4px;"><i class="fa-solid fa-ban"></i> Sin movimientos</span></td>
                <td class="text-center" style="color: var(--text-muted);">0</td>
                <td class="text-right" style="color: var(--text-muted);">S/ 0.00</td>
                <td class="text-right" style="color: var(--text-muted);">S/ 0.00</td>
            `;
        } else {
            tr.innerHTML = `
                <td><strong>${row.mina}</strong></td>
                <td class="text-center">${row.transacciones.toLocaleString('es-PE')}</td>
                <td class="text-right">S/ ${row.total_sin_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td class="text-right">S/ ${row.total_con_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            `;
        }
        consolidatedTableTbody.appendChild(tr);
    });
    
    consolidatedTotalTrans.innerText = data.totals.transacciones.toLocaleString('es-PE');
    consolidatedTotalSinIgv.innerText = `S/ ${data.totals.total_sin_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    consolidatedTotalConIgv.innerText = `S/ ${data.totals.total_con_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    btnDownloadConsolidated.disabled = false;
    btnDownloadConsolidatedInline.disabled = false;
}

// --- CONSULTAR ANÁLISIS INDIVIDUAL (CON SKELETONS SHIMMER) ---
async function runAnalysis(year, month, mina) {
    try {
        // ACTIVAR SKELETONS LOADERS
        kpiTotalIgv.innerHTML = '<span class="skeleton skeleton-kpi"></span>';
        kpiTotalSinIgv.innerHTML = '<span class="skeleton skeleton-kpi"></span>';
        kpiTotalCant.innerHTML = '<span class="skeleton" style="height:20px; width:40px;"></span>';
        kpiTransacciones.innerHTML = '<span class="skeleton" style="height:20px; width:40px;"></span>';
        
        chartPlaceholder.style.display = "none";
        chartImg.style.display = "none";
        chartSkeleton.style.display = "block";
        
        highlightPlaceholder.style.display = "none";
        highlightContent.style.display = "none";
        
        tablePlaceholder.style.display = "none";
        tableContainer.style.display = "none";
        tableSkeleton.style.display = "block";
        paginationContainer.style.display = "none";
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year, month, mina })
        });
        
        const data = await response.json();
        
        // APAGAR SKELETONS
        chartSkeleton.style.display = "none";
        tableSkeleton.style.display = "none";
        
        if (response.status === 404) {
            showToast(data.error, 'info');
            resetDashboard();
            return;
        }
        
        if (data.error) {
            showToast(`Error en análisis: ${data.error}`, 'error');
            resetDashboard();
            return;
        }
        
        // 1. Cargar KPIs
        kpiTotalIgv.innerText = `S/ ${data.metrics.total_con_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        kpiTotalSinIgv.innerText = `S/ ${data.metrics.total_sin_igv.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        kpiTotalCant.innerText = data.metrics.total_cant.toLocaleString('es-PE');
        kpiTransacciones.innerText = data.metrics.transacciones.toLocaleString('es-PE');
        
        // 2. Cargar Gráfico
        chartImg.style.display = "block";
        chartImg.src = `data:image/png;base64,${data.chart}`;
        
        // 3. Highlight Top
        highlightContent.style.display = "block";
        highlightProductName.innerText = data.metrics.top_prod_name;
        highlightProductCost.innerText = `S/ ${data.metrics.top_prod_monto.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        
        // 4. Cargar Tabla con Paginación
        allRecords = data.records;
        currentPage = 1;
        
        tableContainer.style.display = "block";
        tableSearch.disabled = false;
        tableSearch.value = "";
        
        renderTablePage();
        
        btnDownloadExcel.disabled = false;
        btnDownloadPdf.disabled = false;
        
    } catch (e) {
        console.error("Error al ejecutar análisis:", e);
        showToast("Error al cargar el análisis de datos.", 'error');
        resetDashboard();
    }
}

// --- PAGINACIÓN DE LA TABLA DETALLADA ---
function renderTablePage() {
    tableTbody.innerHTML = "";
    
    // Filtrar localmente en base al input
    const query = tableSearch.value.toLowerCase().trim();
    const filteredRecords = allRecords.filter(row => {
        return !query || 
               row.producto.toLowerCase().includes(query) || 
               row.observaciones.toLowerCase().includes(query) ||
               row.poot.includes(query);
    });
    
    if (filteredRecords.length === 0) {
        tableTbody.innerHTML = '<tr><td colspan="9" class="text-center">No se encontraron transacciones.</td></tr>';
        paginationContainer.style.display = "none";
        return;
    }
    
    // Calcular límites de página
    const totalRecords = filteredRecords.length;
    const totalPages = Math.ceil(totalRecords / recordsPerPage);
    
    // Asegurar que currentPage no se salga de rango
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
    
    const startIndex = (currentPage - 1) * recordsPerPage;
    const endIndex = startIndex + recordsPerPage;
    const pageRecords = filteredRecords.slice(startIndex, endIndex);
    
    // Pintar registros
    pageRecords.forEach(row => {
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
    
    // Configurar e interactuar con panel de paginación
    paginationContainer.style.display = "flex";
    paginationInfo.innerText = `Mostrando ${startIndex + 1}-${Math.min(endIndex, totalRecords)} de ${totalRecords} registros`;
    
    btnPagePrev.disabled = (currentPage === 1);
    btnPageNext.disabled = (currentPage >= totalPages);
}

// Configurar los botones Anterior y Siguiente
function setupPaginationHandlers() {
    btnPagePrev.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderTablePage();
        }
    });
    
    btnPageNext.addEventListener('click', () => {
        const query = tableSearch.value.toLowerCase().trim();
        const filteredRecords = allRecords.filter(row => {
            return !query || 
                   row.producto.toLowerCase().includes(query) || 
                   row.observaciones.toLowerCase().includes(query) ||
                   row.poot.includes(query);
        });
        const totalPages = Math.ceil(filteredRecords.length / recordsPerPage);
        
        if (currentPage < totalPages) {
            currentPage++;
            renderTablePage();
        }
    });
}

// --- BÚSQUEDA RÁPIDA EN TABLA INDIVIDUAL CON DEBOUNCE ---
function setupSearchHandler() {
    tableSearch.addEventListener('input', debounce(() => {
        currentPage = 1; // Reiniciar página en nueva búsqueda
        renderTablePage();
    }, 150));
}

// --- DESCARGAS AUTOMÁTICAS ---
function setupDownloadHandlers() {
    btnDownloadExcel.addEventListener('click', () => triggerDownload('/api/download/excel', 'xlsx'));
    btnDownloadPdf.addEventListener('click', () => triggerDownload('/api/download/pdf', 'pdf'));
    btnDownloadConsolidated.addEventListener('click', triggerConsolidatedDownload);
    btnDownloadConsolidatedInline.addEventListener('click', triggerConsolidatedDownload);
}

// Descarga de Reporte Individual
async function triggerDownload(url, ext) {
    const year = selectYear.value;
    const month = selectMonth.value;
    const mina = selectMina.value;
    
    if (!year || !month || !mina) return;
    
    btnDownloadExcel.disabled = true;
    btnDownloadPdf.disabled = true;
    showToast("Generando reporte individual de descarga...", 'info');
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year, month, mina })
        });
        
        if (!response.ok) {
            const err = await response.json();
            showToast(`Error al descargar: ${err.error}`, 'error');
            return;
        }
        
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        
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
        
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
        showToast("Reporte descargado con éxito.", 'success');
        
    } catch (e) {
        console.error("Error al descargar reporte individual:", e);
        showToast("Ocurrió un error al descargar el archivo.", 'error');
    } finally {
        btnDownloadExcel.disabled = false;
        btnDownloadPdf.disabled = false;
    }
}

// Descarga de Reporte Consolidado Multipágina
async function triggerConsolidatedDownload() {
    const year = selectYear.value;
    const month = selectMonth.value;
    
    const selectedMinas = [];
    const checkeds = minasCheckboxGrid.querySelectorAll('input[type="checkbox"]:checked');
    checkeds.forEach(chk => selectedMinas.push(chk.value));
    
    if (!year || !month || selectedMinas.length === 0) return;
    
    btnDownloadConsolidated.disabled = true;
    btnDownloadConsolidatedInline.disabled = true;
    
    const btnText = btnDownloadConsolidatedInline.innerHTML;
    btnDownloadConsolidatedInline.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generando PDF Consolidado...';
    showToast("Generando reporte multipágina consolidado... Esto puede tomar unos segundos.", 'info');
    
    try {
        const response = await fetch('/api/download/consolidated-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ year, month, minas: selectedMinas })
        });
        
        if (!response.ok) {
            const err = await response.json();
            showToast(`Error al consolidar: ${err.error}`, 'error');
            return;
        }
        
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `Reporte_Consolidado_${year}_${String(month).padStart(2, '0')}.pdf`;
        document.body.appendChild(a);
        a.click();
        
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
        showToast("Reporte consolidado descargado exitosamente.", 'success');
        
    } catch (e) {
        console.error("Error al descargar PDF consolidado:", e);
        showToast("Ocurrió un error al generar el consolidado.", 'error');
    } finally {
        btnDownloadConsolidated.disabled = false;
        btnDownloadConsolidatedInline.disabled = false;
        btnDownloadConsolidatedInline.innerHTML = btnText;
    }
}
