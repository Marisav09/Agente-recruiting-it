# Predicción de sueldos pretendidos para postulantes con 
# datos faltantes

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from app.core.config import RANDOM_STATE
from app.data.loader import cargar_dataset, guardar_dataset
from app.data.etl import asignar_experiencia
from app.data.etl import calcular_sueldo

# Nivel del candidato (0: Junior, 1: Mid, 2: Senior) a partir del texto del resume
def extraer_nivel(texto):
    texto = str(texto).lower()
    if 'senior' in texto:
        return 2
    if 'mid' in texto:
        return 1
    return 0

# Función principal para enriquecer el dataset
def enriquecer_dataset(df=None):
    np.random.seed(RANDOM_STATE)
    if df is None:
        df = cargar_dataset()
    else:
        df = df.copy()

# Asignamos años de experiencia y sueldos pretendidos, con un 10% de sueldos faltantes para simular la realidad
    df['años de experiencia'] = df.apply(asignar_experiencia, axis=1)
    df['sueldo pretendido'] = df.apply(calcular_sueldo, axis=1)

    mascara_nulos = np.random.choice([True, False], size=len(df), p=[0.10, 0.90])
    df.loc[mascara_nulos, 'sueldo pretendido'] = np.nan

# Codificamos el nivel del candidato para usarlo como feature en el modelo de imputación
    df['nivel_codificado'] = df['Resume'].apply(extraer_nivel)
    df['años de experiencia'] = pd.to_numeric(df['años de experiencia'], errors='coerce').fillna(0).astype(int)

    df_entrenamiento = df[df['sueldo pretendido'].notnull()].copy()
    df_faltantes = df[df['sueldo pretendido'].isnull()].copy()
# Si hay sueldos faltantes, entrenamos un modelo de regresión para imputarlos
    if len(df_faltantes) > 0:
        modelo = DecisionTreeRegressor(random_state=RANDOM_STATE, max_depth=5)
        X_train = df_entrenamiento[['años de experiencia', 'nivel_codificado']]
        y_train = df_entrenamiento['sueldo pretendido']
        X_missing = df_faltantes[['años de experiencia', 'nivel_codificado']]
        modelo.fit(X_train, y_train)
        df.loc[df['sueldo pretendido'].isnull(), 'sueldo pretendido'] = np.round(modelo.predict(X_missing), 2)

# Guardamos el dataset con sueldos pretendidos y eliminamos columnas auxiliares
    df['sueldo_estimado_por_IA'] = mascara_nulos
    df = df.drop(columns=['Race', 'experiencia', 'sueldo', 'nivel_codificado'], errors='ignore')
    guardar_dataset(df)
    return df
# Si ejecutamos este módulo directamente, se procesará el dataset y se guardará el resultado
if __name__ == "__main__":
    enriquecer_dataset()
