# ETL del dataset de postulantes
from typing import Tuple
from app.data.loader import cargar_dataset, guardar_dataset
from app.services.prediccion import enriquecer_dataset


def ejecutar_etl(csv_path: str | None = None, output_path: str | None = None) -> Tuple[object, str]:
    """Ejecuta el flujo ETL completo: carga, enriquece y guarda.

    Retorna el DataFrame resultante y la ruta de salida.
    """
    df = cargar_dataset(csv_path)
    df_final = enriquecer_dataset(df)
    ruta_guardado = guardar_dataset(df_final, output_path)
    return df_final, ruta_guardado


__all__ = ["ejecutar_etl"]
