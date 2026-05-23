from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.core.config import DATA_CSV, OUTPUT_CSV
from app.data.loader import cargar_dataset
from app.services.agent import obtener_top_candidatos

router = APIRouter()

IT_PROFILES = [
    {"nombre": "AI Researcher", "categoria": "Inteligencia Artificial"},
    {"nombre": "AI Specialist", "categoria": "Inteligencia Artificial"},
    {"nombre": "Machine Learning Engineer", "categoria": "Inteligencia Artificial"},
    {"nombre": "Data Analyst", "categoria": "Datos y Analytics"},
    {"nombre": "Database Administrator", "categoria": "Datos y Analytics"},
    {"nombre": "Cloud Architect", "categoria": "Infraestructura"},
    {"nombre": "Cybersecurity Analyst", "categoria": "Seguridad"},
    {"nombre": "Software Engineer", "categoria": "Desarrollo"},
    {"nombre": "Web Developer", "categoria": "Desarrollo"},
    {"nombre": "Systems Analyst", "categoria": "Producto y Sistemas"},
    {"nombre": "Business Analyst", "categoria": "Producto y Sistemas"},
    {"nombre": "UX Designer", "categoria": "Producto y Sistemas"},
    {"nombre": "Robotics Engineer", "categoria": "Ingeniería Avanzada"},
]


def _leer_dataset() -> pd.DataFrame:
    try:
        df = pd.read_csv(OUTPUT_CSV, sep=",")
        if len(df.columns) <= 1:
            df = pd.read_csv(OUTPUT_CSV, sep=";")
    except Exception:
        df = cargar_dataset(csv_path=DATA_CSV)

    if len(df.columns) <= 1:
        raise ValueError("El dataset no se pudo parsear correctamente. Verifica los separadores.")

    return df


@router.get("/perfiles-it", response_model=List[Dict[str, Any]])
def listar_perfiles_it():
    """Devuelve perfiles IT curados para alimentar el selector del frontend."""
    return IT_PROFILES


@router.get("/estadisticas", response_model=Dict[str, Any])
def obtener_estadisticas():
    """Devuelve métricas visuales para la landing."""
    try:
        df = _leer_dataset()
        perfiles_it = {perfil["nombre"] for perfil in IT_PROFILES}
        df_it = df[df["Job Roles"].isin(perfiles_it)].copy()
        base = df_it if not df_it.empty else df

        roles = (
            base["Job Roles"]
            .value_counts()
            .head(8)
            .reset_index()
            .rename(columns={"Job Roles": "rol", "count": "cantidad"})
            .to_dict(orient="records")
        )

        categorias = []
        for categoria in sorted({perfil["categoria"] for perfil in IT_PROFILES}):
            nombres = [perfil["nombre"] for perfil in IT_PROFILES if perfil["categoria"] == categoria]
            categorias.append(
                {
                    "categoria": categoria,
                    "cantidad": int(df[df["Job Roles"].isin(nombres)].shape[0]),
                }
            )

        return {
            "total_candidatos": int(df.shape[0]),
            "total_it": int(df_it.shape[0]),
            "sueldo_promedio_it": round(float(df_it["sueldo pretendido"].mean()), 2) if not df_it.empty else 0,
            "experiencia_promedio_it": round(float(df_it["años de experiencia"].mean()), 1) if not df_it.empty else 0,
            "roles_mas_ofertados": roles,
            "categorias": categorias,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno de estadísticas: {str(e)}")


@router.get("/top-candidatos", response_model=List[Dict[str, Any]])
def buscar_top_talento(
    tecnologia: str = Query(..., description="Tecnología requerida o perfil IT"),
    sueldo_maximo: float = Query(..., description="Presupuesto salarial máximo"),
    experiencia_minima: int = Query(0, description="Años mínimos de experiencia"),
    top_n: int = Query(5, description="Cantidad de candidatos a retornar"),
):
    try:
        df = _leer_dataset()
        return obtener_top_candidatos(
            df=df,
            tecnologia=tecnologia,
            sueldo_maximo=sueldo_maximo,
            experiencia_minima=experiencia_minima,
            top_n=top_n,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del Agente: {str(e)}")
