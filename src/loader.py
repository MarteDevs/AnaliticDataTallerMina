import pandas as pd
import unicodedata
import os

def clean_column_name(col):
    """
    Limpia los nombres de las columnas removiendo caracteres unicode problemáticos.
    """
    nfkd_form = unicodedata.normalize('NFKD', str(col))
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
    # Reemplazar espacios y caracteres no deseados
    clean_name = "".join([c if c.isalnum() or c in ["_", " ", "-"] else "" for c in only_ascii])
    return clean_name.strip()

def load_data(file_path=None):
    """
    Carga y limpia la hoja 'BASE DE DATOS' del archivo Excel.
    """
    if file_path is None:
        file_path = r"d:\vps-program-proyects\AnalisisData\FEBRERO 2026  INFORME.xlsx"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el archivo Excel en {file_path}")
        
    print(f"Cargando archivo: {file_path} ...")
    df = pd.read_excel(file_path, sheet_name="BASE DE DATOS")
    
    # Limpiar columnas
    original_cols = df.columns.tolist()
    df.columns = [clean_column_name(c) for c in df.columns]
    
    # Asegurar que FechaMovimiento y F_2 sean datetime
    for col in ['FechaMovimiento', 'F_2']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    print(f"Datos cargados exitosamente. Total registros: {len(df)}")
    return df
