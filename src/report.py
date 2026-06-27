import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import xlsxwriter
from fpdf import FPDF

MONTHS_ES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
    7: "JULIO", 8: "AGOSTO", 9: "SETIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

MONTHS_ES_SHORT = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Oct", 11: "Nov", 12: "Dic"
}

def clean_filename(name):
    """
    Limpia un nombre para que sea seguro usarlo como nombre de archivo.
    """
    clean_name = "".join([c if c.isalnum() or c in ["_", " ", "-"] else "" for c in name])
    return clean_name.strip().replace(" ", "_")

def generate_chart(df_mina, year, month, mina_name, output_dir):
    """
    Genera un gráfico estilizado de los productos más consumidos por monto total.
    Retorna la ruta de la imagen del gráfico.
    """
    if df_mina.empty or len(df_mina) == 0:
        return None
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Agrupar por producto y sumar total
    df_grouped = df_mina.groupby('DescProducto')['TOTAL  IGV'].sum().reset_index()
    df_grouped = df_grouped.sort_values(by='TOTAL  IGV', ascending=False).head(10)
    
    if len(df_grouped) == 0:
        return None
        
    # Configuración de estilo premium de seaborn
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Crear paleta de colores elegantes
    colors = sns.color_palette("Blues_r", len(df_grouped))
    
    bars = sns.barplot(
        x='TOTAL  IGV', 
        y='DescProducto', 
        data=df_grouped, 
        palette=colors,
        ax=ax,
        hue='DescProducto',
        legend=False
    )
    
    # Título y etiquetas
    ax.set_title(f"Top 10 Productos por Gasto (TOTAL + IGV)\n{mina_name} - {MONTHS_ES[month]} {year}", fontsize=12, fontweight='bold', color='#1F4E78')
    ax.set_xlabel("Monto Acumulado (S/)", fontsize=10, fontweight='bold', color='#4F5B66')
    ax.set_ylabel("", fontsize=10)
    
    # Ajustar etiquetas de texto y formato
    for bar in bars.patches:
        width = bar.get_width()
        if width > 0:
            ax.text(
                width + (df_grouped['TOTAL  IGV'].max() * 0.01), 
                bar.get_y() + bar.get_height()/2, 
                f"S/ {width:,.2f}", 
                va='center', 
                ha='left', 
                fontsize=8, 
                fontweight='bold',
                color='#1F4E78'
            )
            
    plt.tight_layout()
    
    # Guardar gráfico
    filename = f"chart_{clean_filename(mina_name)}_{year}_{month:02d}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filepath

def generate_excel_report(df_mina, year, month, mina_name, output_dir, chart_path=None):
    """
    Genera un reporte de Excel formateado al estilo de la plantilla del usuario.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"Reporte_{clean_filename(mina_name)}_{year}_{month:02d}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    # Crear un workbook y una worksheet
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('REPORTE')
    
    # --- Definir Formatos ---
    # Colores corporativos: Azul Oscuro (#1F4E78), Azul Claro/Celeste (#DDEBF7), Gris Claro (#F2F2F2)
    
    title_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 16,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter'
    })
    
    subtitle_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 14,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'font_color': '#4F5B66'
    })
    
    filter_label_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 11,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'bg_color': '#F2F2F2',
        'border': 1,
        'border_color': '#D9D9D9'
    })
    
    filter_val_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 11,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#D9D9D9'
    })
    
    header_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 11,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'font_color': '#FFFFFF',
        'bg_color': '#1F4E78',
        'border': 1,
        'border_color': '#D9D9D9'
    })
    
    # Formatos de celdas de datos
    cell_text_left = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#EAEAEA'
    })
    
    cell_text_center = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#EAEAEA'
    })
    
    cell_date = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#EAEAEA',
        'num_format': 'dd/mm/yyyy'
    })
    
    cell_integer = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#EAEAEA',
        'num_format': '#,##0'
    })
    
    cell_currency = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#EAEAEA',
        'num_format': '"S/" #,##0.00'
    })
    
    # Formatos del Total General
    total_label_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'bg_color': '#DDEBF7',
        'top': 1,
        'bottom': 6,  # Doble línea abajo
        'border_color': '#A6A6A6'
    })
    
    total_currency_format = workbook.add_format({
        'font_name': 'Calibri',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'bg_color': '#DDEBF7',
        'top': 1,
        'bottom': 6,  # Doble línea abajo
        'border_color': '#A6A6A6',
        'num_format': '"S/" #,##0.00'
    })
    
    total_cell_blank = workbook.add_format({
        'bg_color': '#DDEBF7',
        'top': 1,
        'bottom': 6,
        'border_color': '#A6A6A6'
    })

    # --- Configurar Estructura de la Hoja ---
    # Títulos y Cabeceras
    worksheet.write('C2', f"TALLER MINA - {MONTHS_ES[month]} - {year}", title_format)
    worksheet.write('C3', f"{mina_name.upper()}", subtitle_format)
    
    # Filtros laterales
    worksheet.write('A5', 'Comprobante', filter_label_format)
    worksheet.write('B5', 'POOT', filter_val_format)
    
    worksheet.write('A6', 'Area', filter_label_format)
    worksheet.write('B6', 'Taller Mina', filter_val_format)
    
    worksheet.write('A7', 'FechaMovimiento', filter_label_format)
    worksheet.write('B7', MONTHS_ES_SHORT[month], filter_val_format)
    
    worksheet.write('A8', 'Años', filter_label_format)
    worksheet.write('B8', year, filter_val_format)

    # Columnas mapeadas:
    # A -> AreaPediDestino
    # B -> Años (F_2)
    # C -> F_2
    # D -> POOT (Numero)
    # E -> DescProducto
    # F -> Observaciones
    # G -> MED (Unidad)
    # H -> CANT (Cantidad)
    # I -> PRECIO. (Precio)
    # J -> TOTAL. (Total)
    # K -> TOTALES + IGV (TOTAL  IGV)
    
    headers = [
        'AreaPediDestino', 
        'Años (F_2)', 
        'F_2', 
        'POOT', 
        'DescProducto', 
        'Observaciones', 
        'MED', 
        'CANT', 
        'PRECIO.', 
        'TOTAL.', 
        'TOTALES + IGV'
    ]
    
    # Escribir Cabecera de Tabla (Fila 10, que es index 9 en xlsxwriter)
    for col_idx, header in enumerate(headers):
        worksheet.write(9, col_idx, header, header_format)
        
    # Escribir Filas de Datos (Fila 11 en adelante, index 10)
    start_row = 10
    current_row = start_row
    
    # Asegurar ordenación cronológica por fecha
    df_sorted = df_mina.sort_values(by='FechaMovimiento')
    
    for idx, row in df_sorted.iterrows():
        # Obtener valores
        dest = str(row.get('AreaPediDestino', ''))
        anio = year
        # Fecha corta F_2 o FechaMovimiento
        f2_date = row.get('FechaMovimiento')
        poot = row.get('Numero', '')
        desc_prod = str(row.get('DescProducto', ''))
        obs = str(row.get('Observaciones', '')) if not pd.isna(row.get('Observaciones')) else ""
        med = str(row.get('Unidad', ''))
        cant = row.get('Cantidad', 0)
        precio = row.get('Precio', 0.0)
        total = row.get('Total', 0.0)
        total_igv = row.get('TOTAL  IGV', 0.0)
        
        # Escribir valores en la fila actual
        worksheet.write(current_row, 0, dest, cell_text_left)
        worksheet.write(current_row, 1, anio, cell_text_center)
        
        if pd.notna(f2_date):
            worksheet.write_datetime(current_row, 2, f2_date, cell_date)
        else:
            worksheet.write(current_row, 2, "", cell_text_center)
            
        worksheet.write(current_row, 3, poot, cell_text_center)
        worksheet.write(current_row, 4, desc_prod, cell_text_left)
        worksheet.write(current_row, 5, obs, cell_text_left)
        worksheet.write(current_row, 6, med, cell_text_center)
        worksheet.write(current_row, 7, cant, cell_integer)
        worksheet.write(current_row, 8, precio, cell_currency)
        worksheet.write(current_row, 9, total, cell_currency)
        worksheet.write(current_row, 10, total_igv, cell_currency)
        
        current_row += 1

    # Escribir fila de Total General
    # Columnas:
    # A: "Total general", combinada de A a G o simplemente en A
    worksheet.write(current_row, 0, "Total general", total_label_format)
    # Llenar con formato de blanco las columnas de B a G
    for col_idx in range(1, 7):
        worksheet.write(current_row, col_idx, "", total_cell_blank)
        
    # Calcular valores sumados en Python para escribirlos como pre-calculados (evita mostrar 0 en Vista Protegida de Excel)
    val_cant = float(df_mina['Cantidad'].sum())
    val_precio = float(df_mina['Precio'].sum())
    val_total = float(df_mina['Total'].sum())
    val_total_igv = float(df_mina['TOTAL  IGV'].sum())

    # CANT
    worksheet.write_formula(current_row, 7, f"=SUM(H{start_row+1}:H{current_row})", total_label_format, val_cant)
    
    # PRECIO., TOTAL., TOTALES + IGV tienen sumas en la captura
    worksheet.write_formula(current_row, 8, f"=SUM(I{start_row+1}:I{current_row})", total_currency_format, val_precio)
    worksheet.write_formula(current_row, 9, f"=SUM(J{start_row+1}:J{current_row})", total_currency_format, val_total)
    worksheet.write_formula(current_row, 10, f"=SUM(K{start_row+1}:K{current_row})", total_currency_format, val_total_igv)
    
    # Ajustar el ancho de las columnas dinámicamente
    for col_idx, header in enumerate(headers):
        # Determinar el ancho máximo combinando datos y cabeceras
        max_len = len(header)
        for row_idx in range(start_row, current_row):
            val = df_sorted.iloc[row_idx - start_row].iloc[col_idx] if col_idx < len(df_sorted.columns) else ""
            max_len = max(max_len, len(str(val)))
        
        # Ajustes de ancho específicos
        if col_idx == 4:  # DescProducto
            worksheet.set_column(col_idx, col_idx, 35)
        elif col_idx == 5:  # Observaciones
            worksheet.set_column(col_idx, col_idx, 30)
        elif col_idx == 0:  # AreaPediDestino
            worksheet.set_column(col_idx, col_idx, 25)
        else:
            worksheet.set_column(col_idx, col_idx, max(max_len + 3, 10))
            
    # Insertar el gráfico si existe
    if chart_path and os.path.exists(chart_path):
        # Insertar gráfico a la derecha de la tabla de datos, por ejemplo, en la columna M fila 5
        worksheet.insert_image('M5', chart_path, {'x_scale': 0.85, 'y_scale': 0.85})
        
    writer.close()
    print(f"Reporte generado exitosamente: {filepath}")
    return filepath

def safe_text(txt):
    if not isinstance(txt, str):
        txt = str(txt)
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U'
    }
    for k, v in replacements.items():
        txt = txt.replace(k, v)
    return txt.encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def __init__(self, title_text, subtitle_text, year, month):
        super().__init__(orientation='landscape', unit='mm', format='A4')
        self.title_text = title_text
        self.subtitle_text = subtitle_text
        self.year = year
        self.month = month
        
    def header(self):
        # Dibujar banner superior
        self.set_fill_color(31, 78, 120) # #1F4E78
        self.rect(0, 0, 297, 25, 'F')
        
        # Título
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 14)
        self.text(15, 11, safe_text(self.title_text))
        
        # Subtítulo
        self.set_font('helvetica', 'I', 11)
        self.text(15, 18, safe_text(f"{self.subtitle_text} | Reporte Generado Dinamicamente"))
        
        # Fecha a la derecha
        self.set_font('helvetica', '', 9)
        self.text(250, 15, safe_text(f"Periodo: {MONTHS_ES[self.month]} {self.year}"))
        
        self.ln(22) # Espacio para el contenido
        
    def footer(self):
        self.set_y(-15)
        self.set_fill_color(240, 240, 240)
        self.rect(0, 210 - 15, 297, 15, 'F')
        
        self.set_text_color(100, 100, 100)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, safe_text(f"Pagina {self.page_no()} | Reporte de Taller Mina"), 0, 0, 'C')

def generate_pdf_report(df_mina, year, month, mina_name, output_dir, chart_path=None):
    os.makedirs(output_dir, exist_ok=True)
    filename = f"Reporte_{clean_filename(mina_name)}_{year}_{month:02d}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Ordenar por fecha
    df_sorted = df_mina.sort_values(by='FechaMovimiento')
    
    title_text = f"REPORTE DE CONSUMOS - TALLER MINA"
    subtitle_text = f"MINA: {mina_name.upper()}"
    
    pdf = PDF(title_text, subtitle_text, year, month)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    
    # 1. Bloque de Info de Filtros y Gráfico
    # Si hay gráfico, colocamos filtros a la izquierda y el gráfico a la derecha
    start_y = pdf.get_y()
    
    # Cuadro de filtros
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(15, start_y, 90, 43, 'F')
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(15, start_y, 90, 43, 'D')
    
    pdf.set_y(start_y + 3)
    pdf.set_x(18)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(31, 78, 120)
    pdf.cell(0, 5, safe_text("PARAMETROS DEL INFORME"), 0, 1)
    pdf.ln(1)
    
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    
    filters = [
        ("Area de Origen:", "Taller Mina"),
        ("Comprobante:", "POOT"),
        ("Mes Movimiento:", f"{MONTHS_ES[month]}"),
        ("Ano Movimiento:", f"{year}")
    ]
    
    for label, val in filters:
        pdf.set_x(18)
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(32, 5, safe_text(label), 0, 0)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(0, 5, safe_text(val), 0, 1)
        
    # Totales acumulados rápidos
    total_cant = df_mina['Cantidad'].sum()
    total_monto = df_mina['Total'].sum()
    total_igv = df_mina['TOTAL  IGV'].sum()
    
    pdf.set_fill_color(230, 240, 250)
    pdf.rect(15, start_y + 46, 90, 25, 'F')
    pdf.rect(15, start_y + 46, 90, 25, 'D')
    
    pdf.set_y(start_y + 48)
    pdf.set_x(18)
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_text_color(31, 78, 120)
    pdf.cell(35, 5, safe_text("Total Cantidad:"), 0, 0)
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 5, f"{total_cant:,.0f} UND", 0, 1)
    
    pdf.set_x(18)
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_text_color(31, 78, 120)
    pdf.cell(35, 5, safe_text("Total (Sin IGV):"), 0, 0)
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 5, f"S/ {total_monto:,.2f}", 0, 1)
    
    pdf.set_x(18)
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_text_color(31, 78, 120)
    pdf.cell(35, 5, safe_text("Total (Con IGV):"), 0, 0)
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 5, f"S/ {total_igv:,.2f}", 0, 1)
    
    # Insertar el gráfico
    if chart_path and os.path.exists(chart_path):
        # Insertar gráfico a la derecha. Tamaño aproximado: 162mm de ancho y 71mm de alto
        pdf.image(chart_path, x=120, y=start_y, w=162, h=71)
        pdf.set_y(start_y + 75)
    else:
        pdf.set_y(start_y + 75)
        
    pdf.ln(3)
    
    # 2. Título de la tabla de movimientos
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(31, 78, 120)
    pdf.cell(0, 6, safe_text("DETALLE DE MOVIMIENTOS Y CONSUMOS"), 0, 1)
    pdf.ln(1)
    
    # 3. Dibujar tabla
    headers = ["Fecha", "POOT", "Descripcion del Producto", "Unidad", "Cant", "Precio", "Total", "Total + IGV"]
    col_widths = [22, 22, 98, 17, 15, 31, 31, 31] # Total 267mm
    
    # Cabecera de la tabla
    pdf.set_font('helvetica', 'B', 8.5)
    pdf.set_fill_color(31, 78, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(220, 220, 220)
    
    for i, header in enumerate(headers):
        align = 'C' if i in [0, 1, 3, 4] else ('R' if i >= 5 else 'L')
        pdf.cell(col_widths[i], 6, safe_text(header), 1, 0, align, fill=True)
    pdf.ln()
    
    # Filas de datos
    pdf.set_font('helvetica', '', 7.5)
    pdf.set_text_color(33, 33, 33)
    
    fill = False
    for idx, row in df_sorted.iterrows():
        # Controlar salto de página manual para no romper celdas
        if pdf.get_y() > 175: # El alto útil es 210mm, descontando 15mm de margen inferior
            pdf.add_page()
            # Redibujar cabeceras
            pdf.set_font('helvetica', 'B', 8.5)
            pdf.set_fill_color(31, 78, 120)
            pdf.set_text_color(255, 255, 255)
            for i, header in enumerate(headers):
                align = 'C' if i in [0, 1, 3, 4] else ('R' if i >= 5 else 'L')
                pdf.cell(col_widths[i], 6, safe_text(header), 1, 0, align, fill=True)
            pdf.ln()
            pdf.set_font('helvetica', '', 7.5)
            pdf.set_text_color(33, 33, 33)
            
        f2_date = row.get('FechaMovimiento')
        date_str = f2_date.strftime('%d/%m/%Y') if pd.notna(f2_date) else ""
        poot = str(row.get('Numero', ''))
        desc_prod = str(row.get('DescProducto', ''))
        med = str(row.get('Unidad', ''))
        cant = row.get('Cantidad', 0)
        precio = row.get('Precio', 0.0)
        total = row.get('Total', 0.0)
        row_total_igv = row.get('TOTAL  IGV', 0.0)
        
        # Color de fondo alterno
        if fill:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        # Dibujar celdas
        pdf.cell(col_widths[0], 5.5, safe_text(date_str), 1, 0, 'C', fill=True)
        pdf.cell(col_widths[1], 5.5, safe_text(poot), 1, 0, 'C', fill=True)
        
        # Limitar longitud de descripción del producto para que no se desborde
        if len(desc_prod) > 52:
            desc_prod = desc_prod[:49] + "..."
        pdf.cell(col_widths[2], 5.5, safe_text(desc_prod), 1, 0, 'L', fill=True)
        
        pdf.cell(col_widths[3], 5.5, safe_text(med), 1, 0, 'C', fill=True)
        pdf.cell(col_widths[4], 5.5, f"{cant:,.0f}", 1, 0, 'C', fill=True)
        pdf.cell(col_widths[5], 5.5, f"S/ {precio:,.2f}", 1, 0, 'R', fill=True)
        pdf.cell(col_widths[6], 5.5, f"S/ {total:,.2f}", 1, 0, 'R', fill=True)
        pdf.cell(col_widths[7], 5.5, f"S/ {row_total_igv:,.2f}", 1, 0, 'R', fill=True)
        pdf.ln()
        
        fill = not fill

    # Fila de Total General
    if pdf.get_y() > 180:
        pdf.add_page()
        # Redibujar cabeceras por si acaso
        pdf.set_font('helvetica', 'B', 8.5)
        pdf.set_fill_color(31, 78, 120)
        pdf.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            align = 'C' if i in [0, 1, 3, 4] else ('R' if i >= 5 else 'L')
            pdf.cell(col_widths[i], 6, safe_text(header), 1, 0, align, fill=True)
        pdf.ln()
        
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(221, 235, 247) # Celeste claro #DDEBF7
    pdf.set_text_color(31, 78, 120)
    
    # Escribir la etiqueta del total cubriendo las primeras 4 columnas (22+22+98+17 = 159mm)
    pdf.cell(159, 6, safe_text("Total general"), 1, 0, 'L', fill=True)
    
    # Escribir cantidad total
    pdf.cell(col_widths[4], 6, f"{total_cant:,.0f}", 1, 0, 'C', fill=True)
    
    # Escribir precios, totales
    total_precio = df_mina['Precio'].sum()
    pdf.cell(col_widths[5], 6, f"S/ {total_precio:,.2f}", 1, 0, 'R', fill=True)
    pdf.cell(col_widths[6], 6, f"S/ {total_monto:,.2f}", 1, 0, 'R', fill=True)
    pdf.cell(col_widths[7], 6, f"S/ {total_igv:,.2f}", 1, 0, 'R', fill=True)
    pdf.ln()
    
    pdf.output(filepath)
    print(f"Reporte PDF generado exitosamente: {filepath}")
    return filepath

