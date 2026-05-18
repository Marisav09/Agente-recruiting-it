# Rutas para el módulo de inventario (ETL, análisis, alertas)

from fastapi import APIRouter, HTTPException
from app.data.loader import cargar_dataset, guardar_dataset
from app.services.prediccion import enriquecer_dataset
from app.services.analisis import resumen_estadistico
from app.services.alertas import verificar_alertas

router = APIRouter()


@router.get("/ejecutar")
def ejecutar_etl():
    try:
        df = cargar_dataset()
        df_final = enriquecer_dataset(df)
        output_path = guardar_dataset(df_final)

        return {
            "message": "Dataset procesado y guardado con éxito",
            "output_path": str(output_path),
            "resumen": resumen_estadistico(df_final),
            "alertas": verificar_alertas(df_final),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/preview")
def preview_dataset(n: int = 5):
    """Devuelve las primeras `n` filas del dataset como lista de registros JSON."""
    try:
        df = cargar_dataset()
        preview = df.head(n)
        return {"preview": preview.to_dict(orient="records"), "filas_mostradas": len(preview)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
