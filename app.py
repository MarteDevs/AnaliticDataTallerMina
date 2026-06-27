import os
import io
import base64
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

from src.loader import load_data
from src.filter import get_unique_periods, filter_taller_mina, get_unique_minas, filter_by_mina
from src.report import clean_filename, MONTHS_ES
from main import run_generation_pipeline

app = Flask(__name__)
app.secret_key = "analisis_data_secret_key"

# Configuración de archivos
DEFAULT_FILE_PATH = r"d:\vps-program-proyects\AnalisisData\FEBRERO 2026  INFORME.xlsx"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Estado del archivo cargado
CURRENT_FILE_PATH = DEFAULT_FILE_PATH
OUTPUT_DIR = "output"

def get_current_df():
    """
    Retorna el dataframe limpio del archivo activo.
    """
    global CURRENT_FILE_PATH
    if not os.path.exists(CURRENT_FILE_PATH):
        CURRENT_FILE_PATH = DEFAULT_FILE_PATH
    return load_data(CURRENT_FILE_PATH)

def get_file_paths(year, month, mina):
    """
    Retorna las rutas en disco para el Excel, PDF y Gráfico pre-generados.
    """
    month_name = MONTHS_ES.get(month, f"Mes_{month:02d}")
    period_dir_name = f"{year}_{month:02d}_{month_name}"
    clean_mina = clean_filename(mina)
    
    excel_filename = f"Reporte_{clean_mina}_{year}_{month:02d}.xlsx"
    pdf_filename = f"Reporte_{clean_mina}_{year}_{month:02d}.pdf"
    chart_filename = f"chart_{clean_mina}_{year}_{month:02d}.png"
    
    excel_path = os.path.join(OUTPUT_DIR, str(year), period_dir_name, excel_filename)
    pdf_path = os.path.join(OUTPUT_DIR, str(year), period_dir_name, pdf_filename)
    chart_path = os.path.join(OUTPUT_DIR, str(year), period_dir_name, "graficos", chart_filename)
    
    return excel_path, pdf_path, chart_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global CURRENT_FILE_PATH
    if 'file' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
        
    file = request.files['file']
    if file.filename == '':
        CURRENT_FILE_PATH = DEFAULT_FILE_PATH
        # Pre-generar de forma síncrona al subir archivo
        run_generation_pipeline(CURRENT_FILE_PATH, OUTPUT_DIR)
        return jsonify({"message": "Usando archivo por defecto", "filename": "FEBRERO 2026  INFORME.xlsx"})
        
    if file and file.filename.endswith(('.xlsx', '.xls')):
        filename = secure_filename(file.filename)
        dest_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(dest_path)
        CURRENT_FILE_PATH = dest_path
        
        try:
            total_generated = run_generation_pipeline(CURRENT_FILE_PATH, OUTPUT_DIR)
            if total_generated == 0:
                CURRENT_FILE_PATH = DEFAULT_FILE_PATH
                run_generation_pipeline(CURRENT_FILE_PATH, OUTPUT_DIR)
                return jsonify({"error": "El archivo subido no contiene datos válidos del área 'Taller Mina' para procesar."}), 400
        except Exception as e:
            CURRENT_FILE_PATH = DEFAULT_FILE_PATH
            run_generation_pipeline(CURRENT_FILE_PATH, OUTPUT_DIR)
            return jsonify({"error": f"Error al procesar el archivo Excel: {str(e)}"}), 400
            
        return jsonify({
            "message": f"Archivo cargado con éxito. Se generaron {total_generated} reportes en disco.",
            "filename": filename
        })
    else:
        return jsonify({"error": "Formato de archivo no válido (debe ser .xlsx o .xls)"}), 400

@app.route('/api/reset', methods=['POST'])
def reset_file():
    global CURRENT_FILE_PATH
    CURRENT_FILE_PATH = DEFAULT_FILE_PATH
    run_generation_pipeline(CURRENT_FILE_PATH, OUTPUT_DIR)
    return jsonify({"message": "Restaurado al archivo local por defecto y regenerada la base de datos", "filename": "FEBRERO 2026  INFORME.xlsx"})

@app.route('/api/filters', methods=['GET'])
def get_filters():
    try:
        df = get_current_df()
        periods = get_unique_periods(df)
        
        years_dict = {}
        for year, month in periods:
            if year not in years_dict:
                years_dict[year] = []
            years_dict[year].append({
                "month_num": month,
                "month_name": MONTHS_ES.get(month, f"Mes {month}")
            })
            
        years_list = []
        for y in sorted(years_dict.keys(), reverse=True):
            years_list.append({
                "year": y,
                "months": years_dict[y]
            })
            
        df_taller = df[df['Area'] == 'Taller Mina']
        minas = sorted(df_taller['AreaPediDestino'].dropna().unique().tolist())
        
        return jsonify({
            "periods": years_list,
            "minas": minas,
            "filename": os.path.basename(CURRENT_FILE_PATH)
        })
    except Exception as e:
        return jsonify({"error": f"Error al obtener filtros: {str(e)}"}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    year = int(data.get('year'))
    month = int(data.get('month'))
    mina = data.get('mina')
    
    try:
        df = get_current_df()
        
        # 1. Filtrar por Taller Mina y fecha
        df_period = filter_taller_mina(df, year, month)
        if df_period.empty:
            return jsonify({"error": f"No hay movimientos registrados en {MONTHS_ES.get(month)} del {year}"}), 404
            
        # 2. Filtrar por la mina seleccionada
        df_mina = filter_by_mina(df_period, mina)
        if df_mina.empty:
            return jsonify({"error": f"No hay consumos para la mina '{mina}' en este período."}), 404
            
        # 3. Calcular métricas clave
        total_sin_igv = df_mina['Total'].sum()
        total_con_igv = df_mina['TOTAL  IGV'].sum()
        total_cant = df_mina['Cantidad'].sum()
        num_transacciones = len(df_mina)
        
        # Producto con mayor gasto
        df_prod_gasto = df_mina.groupby('DescProducto')['TOTAL  IGV'].sum().reset_index()
        if not df_prod_gasto.empty:
            top_prod_row = df_prod_gasto.sort_values(by='TOTAL  IGV', ascending=False).iloc[0]
            top_prod_name = top_prod_row['DescProducto']
            top_prod_monto = top_prod_row['TOTAL  IGV']
        else:
            top_prod_name = "N/A"
            top_prod_monto = 0.0
            
        # 4. Obtener gráfico pre-generado en disco
        _, _, chart_path = get_file_paths(year, month, mina)
        chart_base64 = ""
        
        if os.path.exists(chart_path):
            with open(chart_path, "rb") as image_file:
                chart_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        else:
            # Fallback en caliente por si el gráfico no se pre-generó
            print(f"Advertencia: Gráfico no encontrado en {chart_path}. Generando en memoria...")
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            df_grouped = df_mina.groupby('DescProducto')['TOTAL  IGV'].sum().reset_index()
            df_grouped = df_grouped.sort_values(by='TOTAL  IGV', ascending=False).head(10)
            
            sns.set_theme(style="whitegrid")
            fig, ax = plt.subplots(figsize=(9, 4.5))
            colors = sns.color_palette("Blues_r", len(df_grouped))
            bars = sns.barplot(x='TOTAL  IGV', y='DescProducto', data=df_grouped, palette=colors, ax=ax, hue='DescProducto', legend=False)
            
            ax.set_title(f"Top Productos por Gasto (TOTAL + IGV)\n{mina} - {MONTHS_ES[month]} {year}", fontsize=11, fontweight='bold', color='#1F4E78')
            ax.set_xlabel("Monto Acumulado (S/)", fontsize=9, fontweight='bold', color='#4F5B66')
            ax.set_ylabel("", fontsize=9)
            
            for bar in bars.patches:
                width = bar.get_width()
                if width > 0:
                    ax.text(width + (df_grouped['TOTAL  IGV'].max() * 0.01), bar.get_y() + bar.get_height()/2, f"S/ {width:,.2f}", va='center', ha='left', fontsize=8, fontweight='bold', color='#1F4E78')
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
        
        # 5. Formatear transacciones para tabla
        df_sorted = df_mina.sort_values(by='FechaMovimiento')
        records = []
        for _, row in df_sorted.iterrows():
            f_date = row.get('FechaMovimiento')
            records.append({
                "fecha": f_date.strftime('%d/%m/%Y') if pd.notna(f_date) else "",
                "poot": str(row.get('Numero', '')),
                "producto": str(row.get('DescProducto', '')),
                "unidad": str(row.get('Unidad', '')),
                "cantidad": float(row.get('Cantidad', 0)),
                "precio": float(row.get('Precio', 0.0)),
                "total": float(row.get('Total', 0.0)),
                "total_igv": float(row.get('TOTAL  IGV', 0.0)),
                "observaciones": str(row.get('Observaciones', '')) if not pd.isna(row.get('Observaciones')) else ""
            })
            
        return jsonify({
            "metrics": {
                "total_sin_igv": total_sin_igv,
                "total_con_igv": total_con_igv,
                "total_cant": total_cant,
                "transacciones": num_transacciones,
                "top_prod_name": top_prod_name,
                "top_prod_monto": top_prod_monto
            },
            "chart": chart_base64,
            "records": records
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al analizar datos: {str(e)}"}), 500

@app.route('/api/download/excel', methods=['POST'])
def download_excel():
    data = request.json
    year = int(data.get('year'))
    month = int(data.get('month'))
    mina = data.get('mina')
    
    excel_path, _, _ = get_file_paths(year, month, mina)
    
    if os.path.exists(excel_path):
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=os.path.basename(excel_path),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        return jsonify({"error": "El reporte Excel pre-generado no existe para esta mina y período."}), 404

@app.route('/api/download/pdf', methods=['POST'])
def download_pdf():
    data = request.json
    year = int(data.get('year'))
    month = int(data.get('month'))
    mina = data.get('mina')
    
    _, pdf_path, _ = get_file_paths(year, month, mina)
    
    if os.path.exists(pdf_path):
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype="application/pdf"
        )
    else:
        return jsonify({"error": "El reporte PDF pre-generado no existe para esta mina y período."}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
