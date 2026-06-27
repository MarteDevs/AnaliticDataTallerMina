import os
import io
import base64
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

from src.loader import load_data
from src.filter import get_unique_periods, filter_taller_mina, get_unique_minas, filter_by_mina
from src.report import clean_filename, MONTHS_ES, generate_chart, generate_excel_report, generate_pdf_report, generate_consolidated_pdf_report
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
    Retorna las rutas en disco para el Excel, PDF y Gráfico pre-generados o bajo demanda.
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
            # Generar en disco (auto-guardado) para que esté listo para los reportes
            print(f"Gráfico no encontrado en {chart_path}. Generando y guardando bajo demanda...")
            try:
                os.makedirs(os.path.dirname(chart_path), exist_ok=True)
                # Llamada al graficador
                generate_chart(df_mina, year, month, mina, os.path.dirname(chart_path))
                if os.path.exists(chart_path):
                    with open(chart_path, "rb") as image_file:
                        chart_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Error generando gráfico bajo demanda: {e}")
                
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
    
    excel_path, _, chart_path = get_file_paths(year, month, mina)
    
    if not os.path.exists(excel_path):
        print(f"Reporte Excel no encontrado en {excel_path}. Generando en caliente...")
        try:
            df = get_current_df()
            df_period = filter_taller_mina(df, year, month)
            df_mina = filter_by_mina(df_period, mina)
            
            if df_mina.empty:
                return jsonify({"error": "No hay datos para esta mina y período."}), 404
                
            # Generar gráfico si no existe
            if not os.path.exists(chart_path):
                os.makedirs(os.path.dirname(chart_path), exist_ok=True)
                generate_chart(df_mina, year, month, mina, os.path.dirname(chart_path))
                
            # Generar Excel
            os.makedirs(os.path.dirname(excel_path), exist_ok=True)
            generate_excel_report(df_mina, year, month, mina, os.path.dirname(excel_path), chart_path)
        except Exception as e:
            print(f"Error generando Excel bajo demanda: {e}")
            return jsonify({"error": f"Error al generar Excel: {str(e)}"}), 500
            
    if os.path.exists(excel_path):
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=os.path.basename(excel_path),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        return jsonify({"error": "El reporte Excel no existe y no pudo ser generado."}), 404

@app.route('/api/download/pdf', methods=['POST'])
def download_pdf():
    data = request.json
    year = int(data.get('year'))
    month = int(data.get('month'))
    mina = data.get('mina')
    
    _, pdf_path, chart_path = get_file_paths(year, month, mina)
    
    if not os.path.exists(pdf_path):
        print(f"Reporte PDF no encontrado en {pdf_path}. Generando en caliente...")
        try:
            df = get_current_df()
            df_period = filter_taller_mina(df, year, month)
            df_mina = filter_by_mina(df_period, mina)
            
            if df_mina.empty:
                return jsonify({"error": "No hay datos para esta mina y período."}), 404
                
            # Generar gráfico si no existe
            if not os.path.exists(chart_path):
                os.makedirs(os.path.dirname(chart_path), exist_ok=True)
                generate_chart(df_mina, year, month, mina, os.path.dirname(chart_path))
                
            # Generar PDF
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            generate_pdf_report(df_mina, year, month, mina, os.path.dirname(pdf_path), chart_path)
        except Exception as e:
            print(f"Error generando PDF bajo demanda: {e}")
            return jsonify({"error": f"Error al generar PDF: {str(e)}"}), 500
            
    if os.path.exists(pdf_path):
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype="application/pdf"
        )
    else:
        return jsonify({"error": "El reporte PDF no existe y no pudo ser generado."}), 404

@app.route('/api/consolidated/summary', methods=['POST'])
def get_consolidated_summary():
    data = request.json
    year = int(data.get('year'))
    month = int(data.get('month'))
    minas = data.get('minas', [])
    
    if not minas:
        return jsonify({"error": "No se seleccionó ninguna mina."}), 400
        
    try:
        df = get_current_df()
        df_period = filter_taller_mina(df, year, month)
        
        if df_period.empty:
            return jsonify({"error": f"No hay movimientos registrados en {MONTHS_ES.get(month)} del {year}"}), 404
            
        summary_rows = []
        total_trans = 0
        total_sin_igv = 0.0
        total_con_igv = 0.0
        
        for mina in minas:
            df_mina = filter_by_mina(df_period, mina)
            if df_mina.empty:
                continue
                
            n_trans = len(df_mina)
            t_sin = float(df_mina['Total'].sum())
            t_con = float(df_mina['TOTAL  IGV'].sum())
            
            total_trans += n_trans
            total_sin_igv += t_sin
            total_con_igv += t_con
            
            summary_rows.append({
                "mina": mina,
                "transacciones": n_trans,
                "total_sin_igv": t_sin,
                "total_con_igv": t_con
            })
            
        return jsonify({
            "rows": summary_rows,
            "totals": {
                "transacciones": total_trans,
                "total_sin_igv": total_sin_igv,
                "total_con_igv": total_con_igv
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al calcular resumen consolidado: {str(e)}"}), 500

@app.route('/api/download/consolidated-pdf', methods=['POST'])
def download_consolidated_pdf():
    data = request.json
    year = int(data.get('year'))
    month = int(data.get('month'))
    minas = data.get('minas', [])
    
    if not minas:
        return jsonify({"error": "No se seleccionó ninguna mina."}), 400
        
    try:
        df = get_current_df()
        df_period = filter_taller_mina(df, year, month)
        
        if df_period.empty:
            return jsonify({"error": f"No hay datos registrados en {MONTHS_ES.get(month)} del {year}"}), 404
            
        # Determinar directorio del período
        month_name = MONTHS_ES.get(month, f"Mes_{month:02d}")
        period_dir_name = f"{year}_{month:02d}_{month_name}"
        consolidated_dir = os.path.join(OUTPUT_DIR, str(year), period_dir_name)
        
        # Generar reporte PDF consolidado
        pdf_path = generate_consolidated_pdf_report(df_period, year, month, minas, consolidated_dir)
        
        if os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=os.path.basename(pdf_path),
                mimetype="application/pdf"
            )
        else:
            return jsonify({"error": "No se pudo generar el reporte PDF consolidado."}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al generar reporte consolidado: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
