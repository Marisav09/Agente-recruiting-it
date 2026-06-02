# Recruit IT

Recruit IT es un agente de seleccion de talento IT. Permite buscar candidatos por perfil tecnico, experiencia minima y presupuesto salarial, y devuelve un ranking priorizado con score, match tecnico, ajuste salarial y una justificacion breve.

El proyecto combina una API en FastAPI, un frontend HTML estatico y un dataset local de candidatos procesado con Pandas.

## Problema que resuelve

En procesos de recruiting IT suele ser dificil comparar rapidamente candidatos con criterios consistentes. Recruit IT ayuda a preseleccionar perfiles compatibles usando senales simples y explicables:

- cercania entre el perfil buscado y el CV/rol del candidato,
- experiencia minima requerida,
- pretension salarial frente al presupuesto maximo,
- ranking final para armar una shortlist.

## Funcionalidades principales

Funcionalidades actuales:

- Selector de perfiles IT curados.
- Busqueda de candidatos por tecnologia o perfil IT.
- Filtro por presupuesto salarial maximo.
- Filtro por experiencia minima.
- Ranking Top N de candidatos, con `top_n` configurable desde la API.
- Frontend orientado a mostrar Top 5.
- Score total, match tecnico, ajuste salarial, juicio y justificacion.
- Estadisticas generales para alimentar metricas visuales.
- Lectura de dataset local desde CSV.

Funcionalidades planificadas o posibles:

- Busqueda avanzada por lista de habilidades tecnicas.
- Explicaciones mas detalladas por skill.
- Persistencia de busquedas o shortlists.
- Autenticacion y roles de usuario.
- Integracion con bases externas de candidatos.
- Despliegue en produccion.

## Tecnologias utilizadas

- Python
- FastAPI
- Uvicorn
- Pandas
- NumPy
- scikit-learn
- HTML, CSS y JavaScript embebido
- Dataset CSV local

No hay `package.json` ni build frontend. El frontend actual es un archivo HTML servido por FastAPI.

## Estructura del proyecto

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── data/
│   │   │   ├── datos.py
│   │   │   ├── etl.py
│   │   │   └── loader.py
│   │   ├── routers/
│   │   │   ├── agente_router.py
│   │   │   └── inventario.py
│   │   ├── services/
│   │   │   ├── agent.py
│   │   │   ├── alertas.py
│   │   │   ├── analisis.py
│   │   │   └── prediccion.py
│   │   └── main.py
│   └── data/
│       ├── job_applicant_dataset.csv
│       └── job_applicant_dataset_final.csv
├── frontend/
│   └── index.html
├── requirements.txt
└── README.md
```

## Requisitos previos

- Python 3.11 recomendado.
- `pip`.
- Navegador web.

No se requiere Node.js para ejecutar el frontend actual.

## Instalacion

Desde la raiz del proyecto:

```powershell
cd C:\Users\Usuario\Agente-recruiting-it
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

En macOS/Linux, la activacion del entorno seria:

```bash
source .venv/bin/activate
```

## Ejecucion del backend

Desde la raiz del proyecto:

```powershell
cd backend
uvicorn app.main:app --reload
```

La API queda disponible en:

```text
http://127.0.0.1:8000
```

La documentacion interactiva de FastAPI queda disponible en:

```text
http://127.0.0.1:8000/docs
```

## Ejecucion o apertura del frontend

El backend sirve el frontend desde la ruta raiz:

```text
http://127.0.0.1:8000/
```

Esa es la forma recomendada de probar la interfaz, porque `frontend/index.html` consulta endpoints relativos como `/api/agente/top-candidatos`.

## Uso basico

1. Levantar el backend con Uvicorn.
2. Abrir `http://127.0.0.1:8000/`.
3. Elegir un perfil IT.
4. Indicar presupuesto maximo.
5. Indicar experiencia minima.
6. Ejecutar la busqueda.
7. Revisar el Top 5 de candidatos priorizados.

Ejemplo directo por API:

```text
http://127.0.0.1:8000/api/agente/top-candidatos?tecnologia=Machine%20Learning%20Engineer&sueldo_maximo=95000&experiencia_minima=3&top_n=5
```

## Endpoints principales

### Frontend

- `GET /`
  - Sirve `frontend/index.html`.

### Agente de recruiting

- `GET /api/agente/perfiles-it`
  - Devuelve perfiles IT curados para el selector del frontend.

- `GET /api/agente/estadisticas`
  - Devuelve metricas generales del dataset y roles mas ofertados.

- `GET /api/agente/top-candidatos`
  - Devuelve candidatos ordenados por score.
  - Parametros:
    - `tecnologia`: perfil o tecnologia buscada.
    - `sueldo_maximo`: presupuesto salarial maximo.
    - `experiencia_minima`: anos minimos de experiencia.
    - `top_n`: cantidad de candidatos a retornar.

Ejemplo:

```text
GET /api/agente/top-candidatos?tecnologia=Python&sueldo_maximo=80000&experiencia_minima=3&top_n=10
```

### Inventario / datos

- `GET /api/inventario/preview?n=5`
  - Devuelve una vista previa del dataset original.

- `GET /api/inventario/ejecutar`
  - Endpoint previsto para ejecutar el flujo ETL desde FastAPI.
  - El dataset final ya esta incluido, por lo que no es necesario ejecutarlo para usar la aplicacion.

## Dataset utilizado

Los datos estan en:

```text
backend/data/job_applicant_dataset.csv
backend/data/job_applicant_dataset_final.csv
```

El CSV final actual tiene 10.000 registros y 11 columnas, incluyendo:

- `Job Applicant Name`
- `Age`
- `Gender`
- `Ethnicity`
- `Resume`
- `Job Roles`
- `Job Description`
- `Best Match`
- `años de experiencia`
- `sueldo pretendido`
- `sueldo_estimado_por_IA`

La carga de datos se realiza con Pandas en `backend/app/data/loader.py`. El router del agente intenta leer primero `job_applicant_dataset_final.csv`; si no puede, usa el dataset original como fallback.

## Criterios de ranking o scoring

El scoring esta implementado en:

```text
backend/app/services/agent.py
```

La funcion principal evalua:

- Match tecnico:
  - suma puntos si la tecnologia/perfil aparece en `Resume` o `Job Roles`,
  - suma puntos segun cumplimiento de experiencia minima.

- Ajuste salarial:
  - suma puntos si el sueldo pretendido esta dentro del presupuesto,
  - otorga puntaje parcial si el exceso salarial es pequeno.

- Score total:
  - combina match tecnico y ajuste salarial.

- Juicio:
  - `Recomendar` para candidatos con score alto y match tecnico,
  - `Evaluar` para candidatos intermedios,
  - `Descartar` para candidatos con menor ajuste.

El proyecto tambien incluye un modulo de enriquecimiento de datos en `backend/app/services/prediccion.py`, que usa `DecisionTreeRegressor` para imputar sueldos faltantes en el dataset procesado. Esto no es IA generativa; es un modelo clasico de machine learning aplicado al preprocesamiento.

## Estado actual del proyecto

Implementado:

- API FastAPI funcional.
- Frontend HTML servido desde FastAPI.
- Dataset local incluido.
- Endpoints de agente para perfiles, estadisticas y ranking.
- Scoring explicable por tecnologia/perfil, experiencia y salario.
- Visualizacion del Top 5 desde el frontend.

Pendiente o mejorable:

- Busqueda semantica o por multiples skills.
- Validacion mas robusta de parametros.
- Tests automatizados.
- Manejo de errores mas detallado en frontend.
- Mejor documentacion del origen del dataset.
- Ajuste del flujo ETL si se desea regenerar el CSV final desde endpoints.

## Proximas mejoras posibles

- Agregar filtro por habilidades multiples.
- Incorporar ponderaciones configurables por recruiter.
- Mostrar desglose mas detallado por candidato.
- Guardar shortlists y consultas previas.
- Agregar autenticacion.
- Preparar despliegue con configuracion de produccion.
- Agregar tests unitarios e integrales.
