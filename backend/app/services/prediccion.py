import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

from app.core.config import ADZUNA_APP_ID, ADZUNA_APP_KEY, RANDOM_STATE
from app.data.loader import cargar_dataset, guardar_dataset
from app.services.mercado import estimar_mercado_online

YEARS_COL = "a\u00f1os de experiencia"
SALARY_COL = "sueldo pretendido"
ADZUNA_COLUMNS = [
    "adzuna_mediana",
    "adzuna_p25",
    "adzuna_p75",
    "adzuna_muestra",
]
FEATURES = [
    YEARS_COL,
    "nivel_codificado",
    *ADZUNA_COLUMNS,
]


def asignar_experiencia(row):
    resume = str(row.get("Resume", "")).lower()
    edad = pd.to_numeric(row.get("Age", 0), errors="coerce")
    edad = int(edad) if pd.notna(edad) else 0

    if "senior-level" in resume or "senior" in resume:
        return np.random.randint(10, max(11, edad - 21))
    if "mid-level" in resume or "mid" in resume:
        return np.random.randint(4, 10)
    return np.random.randint(0, 4)


def calcular_sueldo(row):
    base = 40000
    plus_experiencia = row[YEARS_COL] * 4500
    variacion = np.random.randint(-5000, 5001)
    return base + plus_experiencia + variacion


def extraer_nivel(texto):
    texto = str(texto).lower()
    if "senior" in texto:
        return 2
    if "mid" in texto:
        return 1
    return 0


def agregar_datos_adzuna(df):
    df = df.copy()

    for column in ADZUNA_COLUMNS:
        df[column] = 0.0
    df["adzuna_muestra"] = 0

    cache = {}
    adzuna_disponible = bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)

    for idx, row in df.iterrows():
        rol = str(row.get("Job Roles", "") or "").strip()
        experiencia = pd.to_numeric(row.get(YEARS_COL, 0), errors="coerce")
        experiencia = int(experiencia) if pd.notna(experiencia) else 0

        key = (rol.lower(), experiencia // 3)

        if key not in cache:
            if not adzuna_disponible or not rol:
                cache[key] = {
                    "mediana": 0.0,
                    "p25": 0.0,
                    "p75": 0.0,
                    "muestra": 0,
                }
            else:
                try:
                    mercado = estimar_mercado_online(
                        stack=rol,
                        experiencia_minima=experiencia,
                    )
                    banda = mercado.get("banda_objetivo", {})
                    cache[key] = {
                        "mediana": float(banda.get("mediana") or 0),
                        "p25": float(banda.get("p25") or 0),
                        "p75": float(banda.get("p75") or 0),
                        "muestra": int(banda.get("muestra") or 0),
                    }
                except Exception:
                    cache[key] = {
                        "mediana": 0.0,
                        "p25": 0.0,
                        "p75": 0.0,
                        "muestra": 0,
                    }

        datos = cache[key]
        df.at[idx, "adzuna_mediana"] = datos["mediana"]
        df.at[idx, "adzuna_p25"] = datos["p25"]
        df.at[idx, "adzuna_p75"] = datos["p75"]
        df.at[idx, "adzuna_muestra"] = datos["muestra"]

    return df


def enriquecer_dataset(df=None):
    np.random.seed(RANDOM_STATE)
    df = cargar_dataset() if df is None else df.copy()

    df[YEARS_COL] = df.apply(asignar_experiencia, axis=1)
    df[SALARY_COL] = df.apply(calcular_sueldo, axis=1)

    mascara_nulos = np.random.choice([True, False], size=len(df), p=[0.10, 0.90])
    df.loc[mascara_nulos, SALARY_COL] = np.nan

    df["nivel_codificado"] = df["Resume"].apply(extraer_nivel)
    df[YEARS_COL] = pd.to_numeric(df[YEARS_COL], errors="coerce").fillna(0).astype(int)
    df = agregar_datos_adzuna(df)

    for column in FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df_entrenamiento = df[df[SALARY_COL].notnull()].copy()
    df_faltantes = df[df[SALARY_COL].isnull()].copy()

    if len(df_faltantes) > 0:
        modelo = DecisionTreeRegressor(random_state=RANDOM_STATE, max_depth=5)
        x_train = df_entrenamiento[FEATURES]
        y_train = df_entrenamiento[SALARY_COL]
        x_missing = df_faltantes[FEATURES]
        modelo.fit(x_train, y_train)
        df.loc[df[SALARY_COL].isnull(), SALARY_COL] = np.round(modelo.predict(x_missing), 2)

    df["sueldo_estimado_por_IA"] = mascara_nulos
    return df.drop(columns=["Race", "experiencia", "sueldo", "nivel_codificado"], errors="ignore")


if __name__ == "__main__":
    guardar_dataset(enriquecer_dataset())
