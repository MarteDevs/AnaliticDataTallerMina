import os
import sys
import pandas as pd

# Agregar el directorio raíz al path para poder importar src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.loader import load_data
from src.filter import get_unique_periods, filter_taller_mina, get_unique_minas, filter_by_mina
from src.report import generate_chart, generate_excel_report, MONTHS_ES

def main():
    # 1. Cargar base de datos
    try:
        df = load_data()
    except Exception as e:
        print(f"Error al cargar la base de datos: {e}")
        return

    # 2. Obtener periodos únicos (Año, Mes)
    periods = get_unique_periods(df)
    print(f"Se encontraron {len(periods)} períodos (año/mes) únicos en la base de datos.")
    
    # Filtrar períodos para procesar
    # Como el archivo se llama FEBRERO 2026 INFORME, procesaremos principalmente 2026.
    # Pero el usuario nos pide 'para todos' filtrando por mes y año.
    # Procesaremos todos los períodos disponibles desde 2025 en adelante (para no generar demasiados archivos viejos),
    # o ¿debemos procesar todo? Procesemos todo pero agrupado por carpetas para que quede ordenado.
    # Para evitar saturar el disco con miles de reportes viejos (desde 2020), procesaremos el año 2026
    # que es el año activo del informe (como se ve en FEBRERO 2026 INFORME.xlsx).
    # Procesaremos 2026 completo. Si hay períodos del 2026, los procesamos todos.
    # Mostremos los períodos del 2026:
    periods_2026 = [p for p in periods if p[0] == 2026]
    print(f"Períodos de 2026 a procesar: {periods_2026}")
    
    if not periods_2026:
        # Si no hay 2026 por algún motivo, procesamos el último año disponible
        last_year = max([p[0] for p in periods])
        periods_to_process = [p for p in periods if p[0] == last_year]
        print(f"No se detectaron datos de 2026. Procesando el último año disponible ({last_year}): {periods_to_process}")
    else:
        periods_to_process = periods_2026

    total_files_generated = 0
    
    # 3. Iterar por período
    for year, month in periods_to_process:
        month_name = MONTHS_ES.get(month, f"Mes_{month:02d}")
        print(f"\n==========================================")
        print(f"Procesando Período: {month_name} {year}")
        print(f"==========================================")
        
        # Filtrar por Taller Mina y período
        df_period = filter_taller_mina(df, year, month)
        
        if df_period.empty:
            print(f"Sin registros para Taller Mina en {month_name} {year}")
            continue
            
        print(f"Registros encontrados para Taller Mina: {len(df_period)}")
        
        # Obtener las minas (destinos) únicas para este período
        minas = get_unique_minas(df_period)
        print(f"Se encontraron {len(minas)} destinos/minas únicas en este período.")
        
        # Definir directorios de salida
        # d:\vps-program-proyects\AnalisisData\output\2026\2026_02_FEBRERO\
        period_dir_name = f"{year}_{month:02d}_{month_name}"
        output_excel_dir = os.path.join("output", str(year), period_dir_name)
        output_charts_dir = os.path.join(output_excel_dir, "graficos")
        
        # 4. Generar reportes por cada mina
        for mina in minas:
            # Filtrar datos de la mina
            df_mina = filter_by_mina(df_period, mina)
            
            if df_mina.empty:
                continue
                
            print(f"  - Generando reporte para: {mina} ({len(df_mina)} reg)...")
            
            # Generar gráfico
            chart_path = None
            try:
                chart_path = generate_chart(df_mina, year, month, mina, output_charts_dir)
            except Exception as e:
                print(f"    Error generando gráfico para {mina}: {e}")
            
            # Generar reporte de Excel
            try:
                generate_excel_report(df_mina, year, month, mina, output_excel_dir, chart_path)
                total_files_generated += 1
            except Exception as e:
                print(f"    Error generando reporte Excel para {mina}: {e}")

    print(f"\n==========================================")
    print(f"¡Proceso completado!")
    print(f"Total de reportes generados: {total_files_generated}")
    print(f"Los resultados están en la carpeta 'output/' organizada por Año/Período.")
    print(f"==========================================")

if __name__ == "__main__":
    main()
