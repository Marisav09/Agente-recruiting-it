# Este módulo define el router para el agente inteligente que busca talento en base a criterios específicos.

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
import pandas as pd
from app.services.agent import obtener_top_candidatos
from app.data.loader import cargar_dataset
from app.core.config import OUTPUT_CSV, DATA_CSV

router = APIRouter()

# Endpoint para buscar talento usando el agente inteligente
@router.get("/top-candidatos", response_model=List[Dict[str, Any]])
def buscar_top_talento(
    tecnologia: str = Query(..., description="Tecnología requerida (ej. Python, SQL)"),
    sueldo_maximo: float = Query(..., description="Presupuesto salarial máximo"),
    experiencia_minima: int = Query(0, description="Años mínimos de experiencia"),
    top_n: int = Query(10, description="Cantidad de candidatos a retornar")
):
    try:
        # 1. Intentamos leer el archivo enriquecido por ML
        try:
            df = pd.read_csv(OUTPUT_CSV, sep=',')
            # Si se leyó mal y metió todo en 1 columna, intentamos con punto y coma
            if len(df.columns) <= 1:
                df = pd.read_csv(OUTPUT_CSV, sep=';')
        except Exception:
            # Si el archivo final no existe o falla, usamos el base de respaldo
            df = cargar_dataset(csv_path=DATA_CSV)

        # 2. Verificación de seguridad: si sigue roto, lanzamos un error limpio
        if len(df.columns) <= 1:
            raise ValueError("El dataset no se pudo parsear correctamente. Verifica los separadores.")

        # 3. Corremos el motor del agente inteligente
        resultados = obtener_top_candidatos(
            df=df,
            tecnologia=tecnologia,
            sueldo_maximo=sueldo_maximo,
            experiencia_minima=experiencia_minima,
            top_n=top_n
        )
        
        return resultados

    except Exception as e:
        # Esto transforma el error de Python en un mensaje limpio para la web en vez de un 500 feo
        raise HTTPException(status_code=500, detail=f"Error interno del Agente: {str(e)}")