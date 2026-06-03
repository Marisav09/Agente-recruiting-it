# Informe de Evaluacion y Exposicion - Recruit IT

## 1. Introduccion

### Presentacion del proyecto

Recruit IT es un sistema experto orientado a la seleccion inicial de candidatos para perfiles IT. El sistema permite ingresar un stack tecnico o perfil buscado, un presupuesto salarial maximo y una experiencia minima esperada. A partir de esos datos, consulta una base local de candidatos, realiza una preseleccion vectorial con ChromaDB y devuelve un ranking priorizado con score, match tecnico, ajuste salarial, juicio del agente y justificacion.

El proyecto esta implementado como una aplicacion web simple compuesta por:

- Backend con FastAPI.
- Procesamiento de datos con Pandas.
- Scoring de candidatos mediante reglas explicables.
- Busqueda semantica/vectorial con ChromaDB y embeddings.
- Frontend HTML, CSS y JavaScript servido desde FastAPI.
- Dataset local de 10.000 candidatos.

### Integrantes y roles

Completar durante la exposicion:

- Integrante 1: backend, FastAPI y endpoints.
- Integrante 2: procesamiento de datos, Pandas y dataset.
- Integrante 3: logica del agente, scoring y busqueda semantica.
- Integrante 4: frontend, demo y documentacion.

### Problema elegido

En procesos de seleccion de personal IT, comparar rapidamente muchos candidatos puede ser lento y subjetivo. Un recruiter debe revisar CVs, experiencia, pretension salarial y compatibilidad tecnica con el stack solicitado. Si el volumen de candidatos es alto, la evaluacion manual puede producir inconsistencias, omisiones y demoras.

Recruit IT busca resolver ese problema mediante un agente que:

- filtra candidatos relevantes por similitud con el stack tecnico buscado;
- evalua experiencia minima;
- compara sueldo pretendido contra presupuesto maximo;
- genera un score combinado;
- explica por que un candidato debe ser recomendado, evaluado o descartado.

### Relevancia en el mundo real

El problema es relevante porque muchas empresas reciben grandes volumenes de postulaciones. Un sistema como Recruit IT no reemplaza la decision humana, pero ayuda a construir una primera shortlist objetiva y repetible. Esto permite ahorrar tiempo, reducir sesgos operativos y justificar por que ciertos candidatos fueron priorizados.

### Origen y caracteristicas del dataset

El dataset usado se encuentra en:

- `backend/data/job_applicant_dataset.csv`
- `backend/data/job_applicant_dataset_final.csv`

El dataset final contiene 10.000 registros, por lo que cumple el requisito minimo de 5.000 registros indicado en la consigna.

Columnas principales:

- `Job Applicant Name`: nombre del candidato.
- `Age`, `Gender`, `Ethnicity`: datos demograficos.
- `Resume`: resumen del perfil profesional.
- `Job Roles`: rol laboral asociado.
- `Job Description`: descripcion del puesto.
- `Best Match`: marca de compatibilidad del dataset.
- `años de experiencia`: experiencia generada o enriquecida.
- `sueldo pretendido`: salario esperado.
- `sueldo_estimado_por_IA`: indica si el salario fue imputado.

El origen del dataset debe presentarse como dataset local preparado para el trabajo practico. En caso de que provenga de una fuente externa, conviene mencionar la fuente exacta durante la exposicion.

## 2. Arquitectura del Sistema

### Vista general de arquitectura

El sistema se organiza en cuatro capas:

1. Capa de datos:
   - Carga CSV con Pandas.
   - Enriquecimiento del dataset.
   - Generacion de columnas de experiencia y salario.

2. Capa semantica/vectorial:
   - Embeddings con `all-MiniLM-L6-v2`.
   - Base vectorial ChromaDB en `data/chroma_db`.
   - Coleccion `candidates` con 10.000 CVs vectorizados.
   - Coleccion `tech_ecosystem` con una base semantica de tecnologias.

3. Capa del agente:
   - Preseleccion de candidatos similares con ChromaDB.
   - Evaluacion con reglas de negocio.
   - Generacion de score, juicio y justificacion.

4. Capa API y frontend:
   - FastAPI expone endpoints REST.
   - Frontend consume endpoints relativos.
   - La interfaz permite escribir el stack tecnico, presupuesto y experiencia.

Archivos principales:

- `backend/app/main.py`: inicializa FastAPI y sirve el frontend.
- `backend/app/routers/agente_router.py`: endpoints del agente.
- `backend/app/services/agent.py`: scoring y ranking.
- `backend/app/services/tech_knowledge.py`: base semantica de tecnologias.
- `backend/scripts/precompute_embeddings.py`: precomputo e ingesta de embeddings a ChromaDB.
- `frontend/index.html`: interfaz de usuario.

## 3. Capa de Datos con Pandas

### Carga del dataset

La carga de datos se realiza principalmente en `backend/app/data/loader.py`, usando Pandas:

- `cargar_dataset()`: lee el CSV original.
- `guardar_dataset()`: persiste el dataset procesado.

El router del agente intenta leer primero `job_applicant_dataset_final.csv`. Si no puede parsearlo correctamente, usa el dataset original como fallback. Esto permite que la API siga funcionando aunque el CSV final no este disponible.

### Limpieza y normalizacion

El proyecto maneja datos faltantes y normalizacion en varias etapas:

- Lectura tolerante del CSV con separadores alternativos.
- Conversion de columnas numericas como experiencia y salario.
- Uso de `fillna` al preparar textos para embeddings.
- Generacion de valores de experiencia cuando el dataset no los trae explicitamente.
- Imputacion de salarios faltantes mediante un modelo de regresion.

### Transformaciones realizadas

En `backend/app/services/prediccion.py` se realizan transformaciones importantes:

- Asignacion de años de experiencia a partir del texto del resume y la edad.
- Calculo inicial de sueldo pretendido segun experiencia.
- Simulacion de salarios faltantes.
- Codificacion de nivel del candidato: junior, mid o senior.
- Imputacion de sueldos faltantes con `DecisionTreeRegressor`.
- Generacion de la columna `sueldo_estimado_por_IA`.

Estas transformaciones agregan valor porque el agente necesita comparar candidatos no solo por texto, sino tambien por experiencia y salario.

### Metricas generadas

El sistema genera metricas en distintos lugares:

- `Score`: puntaje total del candidato.
- `MatchTecnico`: porcentaje de ajuste tecnico.
- `AjusteSalarial`: porcentaje de ajuste al presupuesto.
- `Juicio`: decision del agente (`Recomendar`, `Evaluar`, `Descartar`).
- Estadisticas generales del dataset en `/api/agente/estadisticas`.
- Estimacion de mercado laboral en `/api/agente/mercado-laboral`.

## 4. Logica del Agente

### Como toma decisiones

El agente implementado en `backend/app/services/agent.py` toma decisiones en dos etapas:

1. Preseleccion vectorial:
   - Se construye una consulta textual con el stack tecnico y experiencia minima.
   - Se genera un embedding de la consulta con `SentenceTransformer`.
   - Se consulta ChromaDB usando `query_embeddings`.
   - Se recuperan candidatos cercanos semanticamente desde la coleccion `candidates`.

2. Evaluacion final:
   - Se calcula similitud tecnica.
   - Se evalua experiencia minima.
   - Se evalua si el sueldo pretendido entra en el presupuesto.
   - Se genera score total.
   - Se asigna un juicio final.
   - Se arma una justificacion textual.

### Reglas implementadas

El score total combina dos grandes componentes:

- Match tecnico y experiencia: hasta 60 puntos.
- Ajuste salarial: hasta 40 puntos.

Reglas principales:

- Si el stack buscado aparece en `Resume`, `Job Roles` o `Job Description`, se considera match exacto.
- Si no aparece literalmente, se usa similitud vectorial como respaldo.
- Si el candidato cumple la experiencia minima, suma el bonus completo de experiencia.
- Si no cumple, suma puntaje parcial proporcional.
- Si el salario pretendido esta dentro del presupuesto, obtiene el maximo ajuste salarial.
- Si se excede levemente, puede obtener puntaje parcial.
- Si excede demasiado, no suma por salario.

### Ejemplo de evaluacion

Caso:

- Stack tecnico: `cybersecurity`
- Presupuesto: `75000`
- Experiencia minima: `8`

Resultado esperado:

- El sistema recupera perfiles como `Cybersecurity Analyst`.
- Detecta match exacto porque el stack aparece en el rol del candidato.
- Evalua experiencia y salario.
- Devuelve candidatos con match tecnico alto y justificacion.

Ejemplo de justificacion:

```text
Match semantico: match exacto: cybersecurity aparece en el perfil del candidato
Similitud tecnica: 100%
OK Experiencia: 8 años (requeria 8)
OK Salario: $73,134 (presupuesto: $75,000)
```

## 5. Busqueda Vectorial y ChromaDB

El proyecto incorpora una mejora relevante sobre una busqueda por texto exacto: usa embeddings y ChromaDB para recuperar candidatos semanticamente cercanos al stack ingresado.

### Embeddings

El script `backend/scripts/precompute_embeddings.py`:

- Lee el dataset final.
- Toma el campo `Resume` de cada candidato.
- Genera embeddings con `all-MiniLM-L6-v2`.
- Guarda embeddings en `backend/data/embeddings/resume_embeddings.npy`.
- Inserta documentos, embeddings y metadata en ChromaDB.

### Base vectorial

La base se guarda en:

```text
data/chroma_db
```

Colecciones:

- `candidates`: 10.000 candidatos vectorizados.
- `tech_ecosystem`: base semantica de tecnologias.

La coleccion `candidates` contiene:

- id del candidato (`cand_0`, `cand_1`, etc.);
- documento textual del CV;
- metadata con indice, nombre, rol, experiencia y salario;
- embedding de 384 dimensiones.

### Ventaja tecnica

La ventaja es que el sistema no necesita recorrer los 10.000 registros completos para cada consulta. Primero recupera un subconjunto de candidatos relevantes con ChromaDB y luego aplica el scoring explicable sobre esa preseleccion.

## 6. API con FastAPI

### Estructura general

La API se inicializa en:

```text
backend/app/main.py
```

Routers:

- `backend/app/routers/agente_router.py`
- `backend/app/routers/inventario.py`

### Endpoints principales

#### `GET /`

Sirve el frontend `frontend/index.html`.

#### `GET /api/agente/estadisticas`

Devuelve metricas generales:

- total de candidatos;
- total de perfiles IT;
- sueldo promedio;
- experiencia promedio;
- roles mas ofertados;
- categorias.

#### `GET /api/agente/top-candidatos`

Endpoint principal del agente.

Parametros:

- `tecnologia`: stack tecnico o perfil buscado.
- `sueldo_maximo`: presupuesto salarial maximo.
- `experiencia_minima`: años minimos requeridos.
- `top_n`: cantidad de candidatos a devolver.

Respuesta:

- lista de candidatos ordenados por score;
- score total;
- match tecnico;
- ajuste salarial;
- juicio;
- justificacion.

#### `GET /api/agente/mercado-laboral`

Devuelve una estimacion salarial por stack y experiencia. Puede usar fuente online si hay credenciales de Adzuna o fallback local con el dataset.

#### `GET /api/inventario/preview`

Devuelve una muestra del dataset original.

#### `GET /api/inventario/ejecutar`

Endpoint previsto para ejecutar el ETL. En el estado actual del codigo, este endpoint requiere ajuste porque algunas llamadas pasan parametros a `enriquecer_dataset`, pero la funcion esta definida sin parametros.

### Validacion de datos

FastAPI valida parametros mediante `Query`, por ejemplo:

- `tecnologia: str = Query(...)`
- `sueldo_maximo: float = Query(...)`
- `experiencia_minima: int = Query(0)`
- `top_n: int = Query(5)`

Tambien se usan `response_model` con tipos como `List[Dict[str, Any]]` y `Dict[str, Any]`.

Punto a mejorar: el proyecto no define modelos Pydantic propios para request/response. Para una version mas robusta, se podrian crear clases como `CandidateResponse`, `MarketResponse` o `SearchRequest`.

## 7. Frontend y Demo Visual

El frontend esta en:

```text
frontend/index.html
```

Caracteristicas:

- Campo de texto libre para ingresar stack tecnico.
- Inputs para presupuesto maximo y experiencia minima.
- Boton para analizar talento.
- Panel de mercado laboral.
- Tarjetas visuales para el Top 5.
- Barras de match tecnico y ajuste salarial.
- Justificacion por candidato.
- Panel de roles frecuentes.

La interfaz consume:

- `/api/agente/top-candidatos`
- `/api/agente/mercado-laboral`
- `/api/agente/estadisticas`

## 8. Demo en Vivo Recomendada

### Paso 1: levantar servidor

Desde la raiz o carpeta backend, ejecutar:

```bash
uvicorn app.main:app --reload
```

Si se ejecuta desde la raiz, ajustar el comando segun estructura:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Paso 2: abrir documentacion

Abrir:

```text
http://localhost:8000/docs
```

### Paso 3: probar endpoints

#### Ejemplo normal

```text
GET /api/agente/top-candidatos?tecnologia=Python&sueldo_maximo=120000&experiencia_minima=3&top_n=5
```

Explicacion:

- Se busca un perfil Python.
- Se exige al menos 3 años de experiencia.
- Se limita el salario a 120.000.
- El agente devuelve los mejores 5 candidatos.

#### Ejemplo limite

```text
GET /api/agente/top-candidatos?tecnologia=cybersecurity&sueldo_maximo=75000&experiencia_minima=8&top_n=5
```

Explicacion:

- La experiencia minima es alta.
- El presupuesto es ajustado.
- El sistema debe priorizar candidatos que cumplan ambas restricciones.

#### Ejemplo critico

```text
GET /api/agente/top-candidatos?tecnologia=React&sueldo_maximo=30000&experiencia_minima=10&top_n=5
```

Explicacion:

- Presupuesto bajo y experiencia alta.
- Es probable que el agente devuelva candidatos con menor ajuste o juicio `Evaluar`/`Descartar`.
- Sirve para mostrar como el sistema reacciona ante condiciones dificiles.

#### Endpoint de estadisticas

```text
GET /api/agente/estadisticas
```

Sirve para mostrar el tamaño de la base y la composicion de roles.

#### Endpoint de mercado

```text
GET /api/agente/mercado-laboral?tecnologia=Python&sueldo_maximo=120000&experiencia_minima=3&fuente=auto
```

Sirve para explicar si el presupuesto esta alineado con el mercado segun datos online o fallback local.

## 9. Criterios de Evaluacion y Como los Cubre el Proyecto

### Manejo de Pandas

Nivel esperado: bueno a excelente.

El proyecto no solo carga CSV, sino que:

- lee dataset con Pandas;
- genera columnas nuevas;
- imputa salarios;
- calcula experiencia;
- genera metricas para estadisticas;
- crea scores y porcentajes.

Mejora pendiente:

- robustecer el endpoint ETL para que la regeneracion del dataset final funcione desde la API.
- documentar mejor limpieza de nulos y normalizacion.

### Logica del Agente

Nivel esperado: excelente.

El agente:

- toma decisiones con scoring;
- usa reglas explicables;
- combina match tecnico, experiencia y salario;
- usa ChromaDB para preseleccion vectorial;
- devuelve juicio y justificacion.

Esto supera un simple filtro porque produce una decision interpretable.

### Arquitectura FastAPI

Nivel esperado: bueno.

Fortalezas:

- API funcional con routers separados.
- Documentacion automatica en `/docs`.
- Endpoints organizados por agente e inventario.
- Uso de `Query` y `response_model`.
- Manejo de errores con `HTTPException`.

Mejoras:

- agregar modelos Pydantic propios;
- validar rangos de `sueldo_maximo`, `top_n` y `experiencia_minima`;
- corregir endpoint ETL;
- limpiar archivos generados y scripts experimentales.

### Exposicion y demo

Nivel esperado: excelente si se ensaya la demo.

El sistema tiene una interfaz visual y endpoints demostrables. Conviene mostrar primero `/docs`, luego el frontend, y finalmente explicar una tarjeta de candidato.

### Trabajo en equipo

Completar con evidencia real:

- roles de cada integrante;
- commits o ramas;
- division de tareas;
- integracion final.

## 10. Desafios Tecnicos Encontrados

### Manejo de datos

- El dataset requiere columnas enriquecidas para experiencia y salario.
- Algunos salarios faltantes se imputan con un modelo.
- Es necesario asegurar que el CSV final tenga el mismo orden que los embeddings en ChromaDB.

### Diseño del agente

- Un simple match por palabra exacta no alcanza.
- Se incorporo ChromaDB para recuperar candidatos semanticamente cercanos.
- Se mantuvo una logica explicable para que el recruiter entienda la decision.

### Problemas con la API y ChromaDB

- La coleccion `candidates` debe estar cargada antes de buscar.
- ChromaDB puede tener conflictos si una coleccion se crea con distinta embedding function.
- El primer arranque puede tardar por carga de modelos.

## 11. Mejoras Futuras

### Machine Learning real

El proyecto ya incluye un modelo simple (`DecisionTreeRegressor`) para imputacion de salarios. Futuras mejoras:

- modelo supervisado para predecir compatibilidad candidato-puesto;
- clasificacion de candidatos recomendados/no recomendados;
- feedback loop del recruiter para mejorar el ranking;
- aprendizaje de ponderaciones.

### Escalabilidad

Mejoras posibles:

- mover ChromaDB a servicio persistente;
- separar backend y frontend;
- paginacion de resultados;
- cache de modelos y queries frecuentes;
- contenedorizacion con Docker;
- despliegue en Render, Railway o similar.

### Integracion real

Posibles integraciones:

- ATS reales;
- LinkedIn o portales de empleo;
- APIs salariales;
- autenticacion de recruiters;
- guardado de shortlists.

## 12. Estado Actual y Pendientes

### Implementado

- Backend FastAPI.
- Frontend funcional.
- Dataset de 10.000 candidatos.
- ChromaDB cargado con candidatos.
- Busqueda por stack tecnico escrito por el usuario.
- Scoring explicable.
- Endpoint de mercado laboral.
- Estadisticas visuales.

### Pendiente

- Corregir definitivamente el endpoint ETL.
- Limpiar codigo legacy dentro de `agent.py`.
- Eliminar o documentar scripts manuales de validacion.
- Sacar `__pycache__` del control de versiones.
- Agregar modelos Pydantic propios.
- Agregar tests automatizados.

## 13. Conclusion

Recruit IT implementa un sistema experto aplicado a seleccion de talento IT. Combina procesamiento de datos con Pandas, API REST con FastAPI, una interfaz web simple y busqueda vectorial con ChromaDB. El agente no solo devuelve datos, sino que toma decisiones justificadas mediante un score compuesto por similitud tecnica, experiencia y ajuste salarial.

El valor principal del sistema esta en transformar una base grande de candidatos en una shortlist explicable. Esto lo vuelve util para un contexto real de recruiting, donde el tiempo de revision y la consistencia de criterios son factores clave.

Como mejora futura, el sistema podria incorporar modelos supervisados, integracion con fuentes reales, despliegue en la nube y validaciones mas robustas. Aun asi, el proyecto ya cumple los puntos centrales de la consigna: manejo de datos, logica de agente, API funcional, demo en vivo y dashboard visual.

## 14. Guion Breve para Exposicion de 15-20 Minutos

### Minutos 0-3: Introduccion

- Presentar integrantes y roles.
- Explicar problema: seleccion de candidatos IT con muchos CVs.
- Mostrar dataset de 10.000 registros.
- Justificar relevancia.

### Minutos 3-8: Arquitectura

- Mostrar estructura del proyecto.
- Explicar Pandas y dataset final.
- Explicar embeddings y ChromaDB.
- Explicar agente y scoring.
- Explicar FastAPI y endpoints.

### Minutos 8-15: Demo

- Abrir `/docs`.
- Probar `/api/agente/estadisticas`.
- Probar `/api/agente/top-candidatos` con Python.
- Probar caso limite con cybersecurity.
- Mostrar frontend y explicar tarjetas.

### Minutos 15-20: Cierre

- Desafios tecnicos.
- Mejoras futuras.
- Reflexion: sistema experto como apoyo a decision humana.

