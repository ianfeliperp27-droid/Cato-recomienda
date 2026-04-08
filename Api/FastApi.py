from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Católica de Colombia",
    version="2.0.0"
)

# 1. CORS: Evita bloqueos en el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Archivos Estáticos
if os.path.exists("Api"):
    app.mount("/static", StaticFiles(directory="Api"), name="static")

# Modelo de datos
class Restaurante(BaseModel):
    id: int
    nombre: str
    categoria: str
    rating: float
    activo: bool

restaurantes_db: list = []

# --- RUTAS PARA EL FRONTEND ---

@app.get("/", response_class=HTMLResponse)
def home():
    """Sirve la página de Login"""
    path = "Api/login.html"
    if not os.path.exists(path):
        return HTMLResponse(content=f"Error: No se encuentra {path} en el servidor", status_code=404)
    return FileResponse(path)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Sirve el Dashboard principal"""
    # Intentamos primero en la carpeta Api
    path_api = "Api/DashBoard.html"
    path_root = "DashBoard.html"
    
    if os.path.exists(path_api):
        return FileResponse(path_api)
    elif os.path.exists(path_root):
        return FileResponse(path_root)
    else:
        # Si falla, te mostrará este mensaje en el navegador en lugar de Error 500
        return HTMLResponse(content="Error: No se encuentra DashBoard.html. Revisa mayúsculas.", status_code=404)

# --- RUTAS DE LA API ---

@app.get("/restaurantes")
def listar_restaurantes():
    return {"total": len(restaurantes_db), "restaurantes": restaurantes_db}

@app.post("/restaurantes")
def crear_restaurante(restaurante: Restaurante):
    restaurantes_db.append(restaurante.model_dump())
    return {"mensaje": "Creado", "restaurante": restaurante}

# --- CARGA DE DATOS ---

@app.on_event("startup")
def cargar_datos_prueba():
    if not restaurantes_db:
        datos = [
            {"id": 1, "nombre": "El Corral Universitario", "categoria": "Hamburguesas", "rating": 4.5, "activo": True},
            {"id": 2, "nombre": "Punto Rojo Express",       "categoria": "Corrientazo",  "rating": 4.1, "activo": True},
            {"id": 3, "nombre": "Sushi Nikkei UCC",         "categoria": "Sushi",        "rating": 4.8, "activo": False},
            {"id": 4, "nombre": "La Mazorca Criolla",       "categoria": "Corrientazo",  "rating": 3.9, "activo": True},
            {"id": 5, "nombre": "Pizza Hub Norte",          "categoria": "Pizza",        "rating": 4.2, "activo": True},
        ]
        restaurantes_db.extend(datos)