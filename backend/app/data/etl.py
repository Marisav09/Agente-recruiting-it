# ETL del dataset de postulantes
from typing import Tuple
from app.data.loader import cargar_dataset, guardar_dataset
from app.core.config import RANDOM_STATE
import numpy as np

# asignar años de experiencia y codificar niveles, utilizando un modelo de regresión para imputar valores faltantes de sueldos pretendidos.
def asignar_experiencia(row):
    resume = str(row.get('Resume', '')).lower()
    edad = row.get('Age', 0)

    if 'senior-level' in resume or 'senior' in resume:
        return np.random.randint(10, max(11, int(edad) - 21))
    elif 'mid-level' in resume or 'mid' in resume:
        return np.random.randint(4, 10)
    return np.random.randint(0, 4)

# Calculo del sueldo pretendido basado en años de experiencia y un componente aleatorio
def calcular_sueldo(row):
    base = 40000
    plus_experiencia = row['años de experiencia'] * 4500
    variacion = np.random.randint(-5000, 5001)
    return base + plus_experiencia + variacion

def ejecutar_etl(csv_path: str | None = None, output_path: str | None = None) -> Tuple[object, str]:
    """Ejecuta el flujo ETL completo: carga, enriquece y guarda.

    Retorna el DataFrame resultante y la ruta de salida.
    """
    from app.services.prediccion import enriquecer_dataset

    df = cargar_dataset(csv_path)
    df_final = enriquecer_dataset(df)
    ruta_guardado = guardar_dataset(df_final, output_path)
    return df_final, ruta_guardado


__all__ = ["ejecutar_etl", "asignar_experiencia", "calcular_sueldo"]
