# Agente Recruiting IT

Este repositorio contiene la primera versión del proyecto **Recruiting IT**, con el foco inicial en la ingesta y el preprocesamiento del dataset.

## Estado actual

- Se creó una estructura backend organizada en `backend/app/` con:
  - `core/` para configuración
  - `data/` para carga, ETL y scripts de datos
  - `services/` para lógica de predicción, análisis y alertas
  - `routers/` para los endpoints de FastAPI
- Se movió el dataset original a `backend/data/job_applicant_dataset.csv`.
- Se implementó un pipeline de ETL que:
  - carga el CSV
  - genera columnas sintéticas (`años de experiencia`, `sueldo pretendido`)
  - marca el 10% de sueldos como nulos
  - completa los faltantes con un modelo `DecisionTreeRegressor`
  - guarda el resultado en `backend/data/job_applicant_dataset_final.csv`
- Se agregó un endpoint `/api/inventario/ejecutar` para ejecutar el proceso ETL desde FastAPI.
- Se agregó un endpoint `/api/inventario/preview` para obtener las primeras filas del dataset.

## Cómo ejecutar

1. Instala las dependencias:

```bash
cd "backend"
pip install -r ../requirements.txt
```

2. Ejecuta el ETL directamente:

```bash
cd "backend"
python -m app.data.datos
```

3. Ejecuta la API de FastAPI:

```bash
cd "backend"
uvicorn app.main:app --reload
```

4. Prueba los endpoints:

- Ejecutar el ETL:
  - `GET http://127.0.0.1:8000/api/inventario/ejecutar`
- Ver un preview del dataset:
  - `GET http://127.0.0.1:8000/api/inventario/preview?n=5`

## Estructura del proyecto

```text
backend/
  app/
    core/
      config.py
    data/
      datos.py
      etl.py
      loader.py
    routers/
      inventario.py
    services/
      prediccion.py
      analisis.py
      alertas.py
    main.py
  data/
    job_applicant_dataset.csv
    job_applicant_dataset_final.csv
requirements.txt
README.md
```

## Próximos pasos

Este es el inicio del proyecto. Los siguientes componentes a agregar pueden ser:

- un agente conversacional o de workflow que orqueste preguntas y acciones
- una capa de persistencia y versionado de datos
- más endpoints para análisis, métricas y visualización
- seguridad, autenticación y despliegue
- integración con modelos IA para recomendaciones de reclutamiento

## Notas

- Actualmente el repositorio incluye los datasets para que el flujo pueda ejecutarse de inmediato.
- En el futuro convendrá definir un `.gitignore` más estricto si se manejan datasets más grandes o sensibles.
