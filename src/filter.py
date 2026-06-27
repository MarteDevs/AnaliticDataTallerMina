import pandas as pd

def get_unique_periods(df, date_col='FechaMovimiento'):
    """
    Retorna una lista de tuplas (año, mes) ordenadas cronológicamente.
    """
    if date_col not in df.columns:
        raise ValueError(f"La columna de fecha '{date_col}' no existe en el DataFrame.")
        
    df_temp = df.copy()
    df_temp['Year'] = df_temp[date_col].dt.year
    df_temp['Month'] = df_temp[date_col].dt.month
    
    # Eliminar nulos en fechas
    df_temp = df_temp.dropna(subset=['Year', 'Month'])
    
    unique_periods = df_temp.groupby(['Year', 'Month']).size().index.tolist()
    # Las tuplas vienen como (Year, Month)
    return sorted(unique_periods, key=lambda x: (x[0], x[1]))

def filter_taller_mina(df, year, month, date_col='FechaMovimiento'):
    """
    Filtra los datos por:
    - Area == 'Taller Mina'
    - Año y Mes especificados
    """
    df_filtered = df[df['Area'] == 'Taller Mina'].copy()
    
    # Extraer año y mes
    df_filtered['Year'] = df_filtered[date_col].dt.year
    df_filtered['Month'] = df_filtered[date_col].dt.month
    
    # Filtrar por año y mes
    df_filtered = df_filtered[(df_filtered['Year'] == year) & (df_filtered['Month'] == month)]
    
    return df_filtered

def get_unique_minas(df_filtered, col_destino='AreaPediDestino'):
    """
    Retorna la lista de destinos únicos (minas) de un conjunto ya filtrado.
    """
    if col_destino not in df_filtered.columns:
        return []
    # Retornar los valores únicos no nulos ordenados
    return sorted(df_filtered[col_destino].dropna().unique().tolist())

def filter_by_mina(df_filtered, mina, col_destino='AreaPediDestino'):
    """
    Filtra el dataframe por una mina específica.
    """
    return df_filtered[df_filtered[col_destino] == mina]
