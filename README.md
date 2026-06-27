# 📊 AnalisisData: Control de Consumos y Costos - Taller Mina

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](#)
[![Developer](https://img.shields.io/badge/developer-Marco_Polo-orange.svg)](#)

Una plataforma interactiva premium diseñada para procesar, analizar y exportar métricas de consumo de equipos y áreas destino en operaciones mineras, específicamente enfocada en el área de **Taller Mina**. 

La aplicación permite cargar archivos de consumo en formato Excel (.xlsx), estructurar la información por períodos (Año/Mes), calcular indicadores financieros de forma automática e interactiva, y exportar reportes ejecutivos en formatos PDF y Excel de alta fidelidad.

---

## 🌟 Características Principales

* **Carga Dinámica de Datos:** Sistema de arrastrar y soltar (drag & drop) para subir archivos de consumo de operaciones de forma inmediata.
* **Dashboard Individual de Consumo:**
  * Indicadores clave (KPIs) en tiempo real: Gastos con IGV, Gastos sin IGV, Cantidad consumida y Número de transacciones.
  * Tarjeta ejecutiva con el producto líder en costo.
  * Gráfico de barras horizontal animado que muestra la distribución de gastos por producto para la mina seleccionada.
  * Tabla interactiva y paginada en el cliente (bloques de 20 registros) para evitar lag en el navegador.
  * Buscador rápido con *debounce* integrado.
* **Reporte Consolidado por Lotes:**
  * Pestaña premium que permite filtrar y seleccionar múltiples minas destino en simultáneo mediante una cuadrícula de checkboxes.
  * Buscador reactivo para buscar minas o equipos específicos y marcarlos por lotes.
  * Tabla resumen consolidada dinámica que muestra el rendimiento y coste de todas las minas seleccionadas de forma integrada.
  * Identificación clara ("Sin movimientos") de las minas seleccionadas que no registraron gastos en el período.
* **Exportación de Reportes Premium:**
  * **Excel Corporativo:** Fórmulas de suma pre-calculadas en Python (compatibles con la vista protegida de Microsoft Office) y formateo de celdas con colores e íconos.
  * **PDF Ejecutivo Individual:** Reporte estético horizontal que incluye cabecera corporativa, KPI cards, gráficos y listado de transacciones estructurado.
  * **PDF Consolidado Multipágina:** Reporte consolidado que genera de forma automática una portada ejecutiva resumen y páginas consecutivas de detalles y gráficos de todas las minas que reportaron movimientos.

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, Flask (Framework web), Pandas (Procesamiento de datos).
* **Generación de Reportes:** FPDF2 (PDFs corporativos), XlsxWriter (Excels formateados), Matplotlib / Seaborn (Gráficos estadísticos).
* **Frontend:** HTML5, CSS3 (Glassmorphic dark mode, Shimmer skeleton loaders), Javascript Vanilla (Paginación, Caché local, Debouncing y Toasts).

---

## 🚀 Instalación y Uso Local

Sigue estos pasos para levantar la aplicación en tu entorno de desarrollo local:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/AnalisisData.git
   cd AnalisisData
   ```

2. **Crear y activar un entorno virtual (Python 3.10+ recomendado):**
   * **En Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **En Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Instalar dependencias:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Ejecutar el servidor de desarrollo:**
   ```bash
   python app.py
   ```

5. **Acceder a la aplicación:**
   Abre tu navegador e ingresa a [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## 🌐 Despliegue en Producción

El proyecto está optimizado para producción. Incluye una plantilla de configuración de **PM2** (`ecosystem.config.js`) y soporte para servidores WSGI como **Gunicorn** en entornos Linux.

Para ver las instrucciones detalladas de despliegue paso a paso, configuración de proxy reverso con Nginx y certificados SSL HTTPS gratuitos, consulta la guía:
👉 **[Guía de Despliegue (DEPLOY.md)](./DEPLOY.md)**

---

## 📁 Estructura del Proyecto

```text
AnalisisData/
├── app.py                  # Servidor Flask principal y API Endpoints
├── main.py                 # Pipeline de generación síncrona por lotes
├── requirements.txt        # Librerías y dependencias del proyecto
├── ecosystem.config.js     # Configuración de despliegue para PM2
├── DEPLOY.md               # Guía paso a paso para desplegar en VPS
├── README.md               # Documentación general del repositorio
├── src/
│   ├── filter.py           # Funciones de lógica de filtrado de datos
│   └── report.py           # Motores de generación de PDF y Excel
├── templates/
│   └── index.html          # Interfaz de usuario (HTML5)
├── static/
│   ├── css/
│   │   └── style.css       # Estilos visuales (Modo oscuro y glassmorphism)
│   └── js/
│       └── main.js         # Interactividad frontend (Paginación, Cache, etc.)
└── uploads/                # Directorio de subida temporal de archivos
```

---

## 🧑‍💻 Desarrollador

* **Marco Polo** - *Desarrollador Principal & Arquitectura de Software*
  * GitHub: [@MarteDevs](https://github.com/MarteDevs) *(o tu perfil real)*

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Para más detalles, consulta el archivo LICENSE.
