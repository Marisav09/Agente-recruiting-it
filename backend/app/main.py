# Archivo principal de la aplicación FastAPI
from fastapi import FastAPI
from app.routers.inventario import router as inventario_router

app = FastAPI(title="Recruit IT ETL Backend")
app.include_router(inventario_router, prefix="/api/inventario", tags=["inventario"])


@app.get("/")
def read_root():
    return {"message": "Recruit IT ETL backend is running"}
