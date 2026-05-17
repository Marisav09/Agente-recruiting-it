# Predicción de sueldos pretendidos para postulantes con 
# datos faltantes

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from app.core.config import RANDOM_STATE


def asignar_experiencia(row):
    resume = str(row.get('Resume', '')).lower()
    edad = row.get('Age', 0)

    if 'senior-level' in resume or 'senior' in resume:
        return np.random.randint(10, max(11, int(edad) - 21))
    elif 'mid-level' in resume or 'mid' in resume:
        return np.random.randint(4, 10)
    return np.random.randint(0, 4)


def calcular_sueldo(row):
    base = 40000
    plus_experiencia = row['años de experiencia'] * 4500
    variacion = np.random.randint(-5000, 5001)
    return base + plus_experiencia + variacion


def extraer_nivel(texto):
    texto = str(texto).lower()
    if 'senior' in texto:
        return 2
    if 'mid' in texto:
        return 1
    return 0


def enriquecer_dataset(df):
    np.random.seed(RANDOM_STATE)
    df = df.copy()

    df['años de experiencia'] = df.apply(asignar_experiencia, axis=1)
    df['sueldo pretendido'] = df.apply(calcular_sueldo, axis=1)

    mascara_nulos = np.random.choice([True, False], size=len(df), p=[0.10, 0.90])
    df.loc[mascara_nulos, 'sueldo pretendido'] = np.nan

    df['nivel_codificado'] = df['Resume'].apply(extraer_nivel)
    df['años de experiencia'] = pd.to_numeric(df['años de experiencia'], errors='coerce').fillna(0).astype(int)

    df_entrenamiento = df[df['sueldo pretendido'].notnull()].copy()
    df_faltantes = df[df['sueldo pretendido'].isnull()].copy()

    if len(df_faltantes) > 0:
        modelo = DecisionTreeRegressor(random_state=RANDOM_STATE, max_depth=5)
        X_train = df_entrenamiento[['años de experiencia', 'nivel_codificado']]
        y_train = df_entrenamiento['sueldo pretendido']
        X_missing = df_faltantes[['años de experiencia', 'nivel_codificado']]
        modelo.fit(X_train, y_train)
        df.loc[df['sueldo pretendido'].isnull(), 'sueldo pretendido'] = np.round(modelo.predict(X_missing), 2)

    df['sueldo_estimado_por_IA'] = mascara_nulos
    df = df.drop(columns=['Race', 'experiencia', 'sueldo', 'nivel_codificado'], errors='ignore')
    return df
