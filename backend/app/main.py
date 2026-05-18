# Punto de entrada principal para la aplicación FastAPI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- IMPORTANTE: Middleware de CORS
from app.routers.inventario import router as inventario_router
from app.routers.agente_router import router as agente_router  # <-- NUEVO: Tu nuevo router del agente

app = FastAPI(title="Recruit IT ETL Backend")


# CONFIGURACIÓN DE CORS (Habilita la conexión segura con el Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # El asterisco permite cualquier origen en etapa de desarrollo
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos: GET, POST, etc.
    allow_headers=["*"],  # Permite todos los encabezados HTTP
)

# Inclusión de los routers modulares
app.include_router(inventario_router, prefix="/api/inventario", tags=["inventario"])
app.include_router(agente_router, prefix="/api/agente", tags=["agente"])  # <-- NUEVO

# Ruta raíz para verificar que el backend está corriendo
@app.get("/")
def read_root():
    return {"message": "Recruit IT ETL backend is running"}
    