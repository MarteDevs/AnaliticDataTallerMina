import os
import sys
import shutil
import pandas as pd

# Agregar el directorio raíz al path para poder importar src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.loader import load_data
from src.filter import get_unique_periods, filter_taller_mina, get_unique_minas, filter_by_mina
from src.report import generate_chart, generate_excel_report, generate_pdf_report, MONTHS_ES

DEFAULT_FILE_PATH = r"d:\vps-program-proyects\AnalisisData\FEBRERO 2026  INFORME.xlsx"

def run_generation_pipeline(file_path=DEFAULT_FILE_PATH, output_dir="output"):
    """
    Ejecuta la pre-generación completa de reportes en disco (Excel, PDF y Gráficos).
    Limpia la carpeta de salida especificada antes de iniciar.
    """
    print(f"\n==========================================")
    print(f"Iniciando Pipeline de Generación Completa")
    print(f"Archivo Origen: {file_path}")
    print(f"Directorio Salida: {output_dir}")
    print(f"==========================================")
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
            print("Directorio de salida limpio exitosamente.")
        except Exception as e:
            print(f"Advertencia: No se pudo limpiar completamente el directorio de salida: {e}")
            
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        df = load_data(file_path)
    except Exception as e:
        print(f"Error crítico cargando base de datos: {e}")
        return 0

    periods = get_unique_periods(df)
    periods_2026 = [p for p in periods if p[0] == 2026]
    if not periods_2026:
        last_year = max([p[0] for p in periods]) if periods else 2026
        periods_to_process = [p for p in periods if p[0] == last_year]
    else:
        periods_to_process = periods_2026
        
    print(f"Períodos a pre-generar: {periods_to_process}")
    
    total_excels_generated = 0
    total_pdfs_generated = 0
    
    for year, month in periods_to_process:
        month_name = MONTHS_ES.get(month, f"Mes_{month:02d}")
        df_period = filter_taller_mina(df, year, month)
        
        if df_period.empty:
            continue
            
        minas = get_unique_minas(df_period)
        
        period_dir_name = f"{year}_{month:02d}_{month_name}"
        output_excel_dir = os.path.join(output_dir, str(year), period_dir_name)
        output_charts_dir = os.path.join(output_excel_dir, "graficos")
        
        os.makedirs(output_excel_dir, exist_ok=True)
        os.makedirs(output_charts_dir, exist_ok=True)
        
        for mina in minas:
            df_mina = filter_by_mina(df_period, mina)
            if df_mina.empty:
                continue
                
            chart_path = None
            try:
                chart_path = generate_chart(df_mina, year, month, mina, output_charts_dir)
            except Exception as e:
                print(f"  [Gráfico Error] {mina}: {e}")
                
            try:
                generate_excel_report(df_mina, year, month, mina, output_excel_dir, chart_path)
                total_excels_generated += 1
            except Exception as e:
                print(f"  [Excel Error] {mina}: {e}")
                
            try:
                generate_pdf_report(df_mina, year, month, mina, output_excel_dir, chart_path)
                total_pdfs_generated += 1
            except Exception as e:
                print(f"  [PDF Error] {mina}: {e}")
                
    print(f"\n==========================================")
    print(f"Pipeline Completado con Éxito")
    print(f"Excels Creados: {total_excels_generated}")
    print(f"PDFs Creados: {total_pdfs_generated}")
    print(f"==========================================")
    
    return total_excels_generated

if __name__ == "__main__":
    run_generation_pipeline(DEFAULT_FILE_PATH, "output")
