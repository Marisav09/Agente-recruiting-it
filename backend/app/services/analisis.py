# Métricas base del dataset

def resumen_estadistico(df):
    return {
        "filas": len(df),
        "columnas": df.shape[1],
        "nombres_columnas": list(df.columns),
    }
