import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from app.core.config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_COUNTRY,
    ADZUNA_LOCATION,
    ADZUNA_TIMEOUT_SECONDS,
)


logger = logging.getLogger("recruit_it.mercado")

EXPERIENCE_BANDS = [
    {"nombre": "Junior", "min": 0, "max": 2},
    {"nombre": "Semi Senior", "min": 3, "max": 5},
    {"nombre": "Senior", "min": 6, "max": 9},
    {"nombre": "Expert", "min": 10, "max": 99},
]


def _normalizar_texto(value: Any) -> str:
    return str(value or "").lower().strip()


def _banda_para_experiencia(anios: float) -> Dict[str, Any]:
    for banda in EXPERIENCE_BANDS:
        if banda["min"] <= anios <= banda["max"]:
            return banda
    return EXPERIENCE_BANDS[-1]


def _resumen_salarial(df: pd.DataFrame) -> Dict[str, float]:
    sueldos = pd.to_numeric(df["sueldo pretendido"], errors="coerce").dropna()
    if sueldos.empty:
        return {
            "min": 0,
            "p25": 0,
            "mediana": 0,
            "promedio": 0,
            "p75": 0,
            "max": 0,
        }

    return {
        "min": round(float(sueldos.min()), 2),
        "p25": round(float(sueldos.quantile(0.25)), 2),
        "mediana": round(float(sueldos.median()), 2),
        "promedio": round(float(sueldos.mean()), 2),
        "p75": round(float(sueldos.quantile(0.75)), 2),
        "max": round(float(sueldos.max()), 2),
    }


def _resumen_desde_valores(valores: List[float]) -> Dict[str, float]:
    if not valores:
        return {
            "min": 0,
            "p25": 0,
            "mediana": 0,
            "promedio": 0,
            "p75": 0,
            "max": 0,
        }

    serie = pd.Series(valores, dtype="float64")
    return {
        "min": round(float(serie.min()), 2),
        "p25": round(float(serie.quantile(0.25)), 2),
        "mediana": round(float(serie.median()), 2),
        "promedio": round(float(serie.mean()), 2),
        "p75": round(float(serie.quantile(0.75)), 2),
        "max": round(float(serie.max()), 2),
    }


def _filtrar_por_stack(df: pd.DataFrame, stack: str) -> pd.DataFrame:
    stack_normalizado = _normalizar_texto(stack)
    if not stack_normalizado:
        return df.iloc[0:0].copy()

    roles = df.get("Job Roles", pd.Series("", index=df.index)).map(_normalizar_texto)
    resumes = df.get("Resume", pd.Series("", index=df.index)).map(_normalizar_texto)
    descripciones = df.get("Job Description", pd.Series("", index=df.index)).map(_normalizar_texto)

    mask = (
        roles.str.contains(stack_normalizado, regex=False)
        | resumes.str.contains(stack_normalizado, regex=False)
        | descripciones.str.contains(stack_normalizado, regex=False)
    )
    return df[mask].copy()


def _estado_presupuesto(resumen: Dict[str, float], sueldo_maximo: float | None) -> Dict[str, Any]:
    presupuesto = float(sueldo_maximo) if sueldo_maximo is not None else None
    if presupuesto is None or presupuesto <= 0:
        return {
            "estado": "sin_presupuesto",
            "sueldo_maximo": presupuesto,
            "diferencia_vs_mediana": None,
        }

    mediana = resumen["mediana"]
    diferencia_vs_mediana = round(presupuesto - mediana, 2)
    if presupuesto >= resumen["p75"]:
        estado = "competitivo"
    elif presupuesto >= mediana:
        estado = "alineado"
    elif presupuesto >= resumen["p25"]:
        estado = "ajustado"
    else:
        estado = "bajo_mercado"

    return {
        "estado": estado,
        "sueldo_maximo": presupuesto,
        "diferencia_vs_mediana": diferencia_vs_mediana,
    }


def _consulta_adzuna_histogram(stack: str, experiencia_minima: int) -> Dict[str, Any]:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("[mercado] Adzuna omitido: faltan ADZUNA_APP_ID y/o ADZUNA_APP_KEY.")
        raise RuntimeError("Faltan ADZUNA_APP_ID y ADZUNA_APP_KEY.")

    banda = _banda_para_experiencia(float(experiencia_minima))
    seniority_query = "" if banda["nombre"] == "Semi Senior" else banda["nombre"]
    query = " ".join(part for part in [stack, seniority_query] if part).strip()

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": query,
        "content-type": "application/json",
    }
    if ADZUNA_LOCATION:
        for index, location_part in enumerate(part.strip() for part in ADZUNA_LOCATION.split(",") if part.strip()):
            params[f"location{index}"] = location_part

    url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/histogram?{urlencode(params)}"
    safe_params = {
        **params,
        "app_id": f"{ADZUNA_APP_ID[:4]}..." if ADZUNA_APP_ID else "",
        "app_key": "***",
    }
    logger.warning(
        "[mercado] Consultando Adzuna histogram: country=%s query=%r seniority=%s params=%s",
        ADZUNA_COUNTRY,
        query,
        banda["nombre"],
        safe_params,
    )

    try:
        with urlopen(url, timeout=ADZUNA_TIMEOUT_SECONDS) as response:
            import json

            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"No se pudo consultar Adzuna: {exc}") from exc

    histogram = payload.get("histogram", {}) or {}
    logger.warning(
        "[mercado] Respuesta Adzuna: buckets=%s preview=%s",
        len(histogram),
        list(histogram.items())[:6],
    )

    valores = []
    for salario, cantidad in histogram.items():
        try:
            valores.extend([float(salario)] * int(cantidad))
        except (TypeError, ValueError):
            continue

    resumen = _resumen_desde_valores(valores)
    logger.warning(
        "[mercado] Adzuna procesado: muestra=%s min=%s p25=%s mediana=%s p75=%s max=%s",
        len(valores),
        resumen["min"],
        resumen["p25"],
        resumen["mediana"],
        resumen["p75"],
        resumen["max"],
    )

    return {
        "query": query,
        "histogram": histogram,
        "muestra": len(valores),
        **resumen,
    }


def estimar_mercado_online(
    stack: str,
    experiencia_minima: int = 0,
    sueldo_maximo: float | None = None,
) -> Dict[str, Any]:
    banda_objetivo = _banda_para_experiencia(float(experiencia_minima))
    resumen = _consulta_adzuna_histogram(stack, experiencia_minima)

    return {
        "stack": stack,
        "fuente": "adzuna_api",
        "pais": ADZUNA_COUNTRY,
        "ubicacion": ADZUNA_LOCATION or None,
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "muestra_total": resumen["muestra"],
        "banda_objetivo": {
            "seniority": banda_objetivo["nombre"],
            "experiencia_min": banda_objetivo["min"],
            "experiencia_max": None if banda_objetivo["max"] == 99 else banda_objetivo["max"],
            "muestra": resumen["muestra"],
            "query": resumen["query"],
            "min": resumen["min"],
            "p25": resumen["p25"],
            "mediana": resumen["mediana"],
            "promedio": resumen["promedio"],
            "p75": resumen["p75"],
            "max": resumen["max"],
        },
        "comparacion_presupuesto": _estado_presupuesto(resumen, sueldo_maximo),
        "bandas": [],
        "histogram": resumen["histogram"],
    }


def estimar_mercado_laboral(
    df: pd.DataFrame,
    stack: str,
    experiencia_minima: int = 0,
    sueldo_maximo: float | None = None,
) -> Dict[str, Any]:
    """Calcula rangos salariales observados para un stack y seniority.

    La fuente es el dataset local del proyecto. No scrapea sitios externos en tiempo
    real, para mantener la API deterministica y sin dependencias de terceros.
    """
    columnas_requeridas = {"sueldo pretendido", "años de experiencia"}
    faltantes = columnas_requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas para estimar mercado: {', '.join(sorted(faltantes))}")

    df_stack = _filtrar_por_stack(df, stack)
    if df_stack.empty:
        df_stack = df[df.get("Job Roles", pd.Series("", index=df.index)).map(_normalizar_texto).str.contains("engineer|developer|analyst|architect|data|cloud|cyber|software", regex=True)].copy()
        logger.warning(
            "[mercado] Dataset local: stack=%r sin match exacto, usando fallback IT general. muestra=%s",
            stack,
            int(df_stack.shape[0]),
        )
    else:
        logger.warning(
            "[mercado] Dataset local: stack=%r match local. muestra=%s",
            stack,
            int(df_stack.shape[0]),
        )

    df_stack["años de experiencia"] = pd.to_numeric(df_stack["años de experiencia"], errors="coerce").fillna(0)
    df_stack["sueldo pretendido"] = pd.to_numeric(df_stack["sueldo pretendido"], errors="coerce")

    banda_objetivo = _banda_para_experiencia(float(experiencia_minima))
    df_banda = df_stack[
        (df_stack["años de experiencia"] >= banda_objetivo["min"])
        & (df_stack["años de experiencia"] <= banda_objetivo["max"])
    ].copy()
    base_objetivo = df_banda if not df_banda.empty else df_stack
    resumen_objetivo = _resumen_salarial(base_objetivo)
    logger.warning(
        "[mercado] Dataset local procesado: seniority=%s muestra_banda=%s mediana=%s p25=%s p75=%s",
        banda_objetivo["nombre"],
        int(base_objetivo.shape[0]),
        resumen_objetivo["mediana"],
        resumen_objetivo["p25"],
        resumen_objetivo["p75"],
    )

    bandas: List[Dict[str, Any]] = []
    for banda in EXPERIENCE_BANDS:
        df_segmento = df_stack[
            (df_stack["años de experiencia"] >= banda["min"])
            & (df_stack["años de experiencia"] <= banda["max"])
        ]
        resumen = _resumen_salarial(df_segmento)
        bandas.append(
            {
                "seniority": banda["nombre"],
                "experiencia_min": banda["min"],
                "experiencia_max": None if banda["max"] == 99 else banda["max"],
                "muestra": int(df_segmento.shape[0]),
                **resumen,
            }
        )

    return {
        "stack": stack,
        "fuente": "dataset_local",
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "muestra_total": int(df_stack.shape[0]),
        "banda_objetivo": {
            "seniority": banda_objetivo["nombre"],
            "experiencia_min": banda_objetivo["min"],
            "experiencia_max": None if banda_objetivo["max"] == 99 else banda_objetivo["max"],
            "muestra": int(base_objetivo.shape[0]),
            **resumen_objetivo,
        },
        "comparacion_presupuesto": _estado_presupuesto(resumen_objetivo, sueldo_maximo),
        "bandas": bandas,
    }


def obtener_estimacion_mercado(
    df: pd.DataFrame,
    stack: str,
    experiencia_minima: int = 0,
    sueldo_maximo: float | None = None,
    fuente: str = "auto",
) -> Dict[str, Any]:
    if fuente not in {"auto", "online", "local"}:
        raise ValueError("La fuente debe ser 'auto', 'online' o 'local'.")

    if fuente in {"auto", "online"}:
        try:
            return estimar_mercado_online(
                stack=stack,
                experiencia_minima=experiencia_minima,
                sueldo_maximo=sueldo_maximo,
            )
        except Exception as exc:
            if fuente == "online":
                logger.warning("[mercado] Adzuna fallo con fuente=online: %s", exc)
                raise

            logger.warning("[mercado] Adzuna no disponible, usando fallback local. motivo=%s", exc)
            fallback = estimar_mercado_laboral(
                df=df,
                stack=stack,
                experiencia_minima=experiencia_minima,
                sueldo_maximo=sueldo_maximo,
            )
            fallback["fallback_de"] = "adzuna_api"
            fallback["motivo_fallback"] = str(exc)
            return fallback

    return estimar_mercado_laboral(
        df=df,
        stack=stack,
        experiencia_minima=experiencia_minima,
        sueldo_maximo=sueldo_maximo,
    )
