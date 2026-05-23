from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.routers.agente_router import router as agente_router
from app.routers.inventario import router as inventario_router

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="Recruit IT ETL Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventario_router, prefix="/api/inventario", tags=["inventario"])
app.include_router(agente_router, prefix="/api/agente", tags=["agente"])


@app.get("/")
def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")
