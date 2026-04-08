from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Católica de Colombia",
    version="2.0.0"
)

# Definición del modelo
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
    # Usamos ruta relativa a la carpeta Api para Azure
    return FileResponse("Api/login.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    # Esta es la ruta a la que debe redirigir tu login.html
    return FileResponse("Api/DashBoard.html")

# --- RUTAS DE LA API ---

@app.get("/restaurantes", summary="Listar todos los restaurantes")
def listar_restaurantes():
    return {"total": len(restaurantes_db), "restaurantes": restaurantes_db}

@app.post("/restaurantes", summary="Crear un restaurante")
def crear_restaurante(restaurante: Restaurante):
    for r in restaurantes_db:
        if r["id"] == restaurante.id:
            raise HTTPException(status_code=400, detail=f"Ya existe un restaurante con id={restaurante.id}")
    restaurantes_db.append(restaurante.model_dump())
    return {"mensaje": "Restaurante creado exitosamente", "restaurante": restaurante}

@app.get("/restaurantes/buscar/filtro", summary="Filtrar por categoria o estado")
def filtrar_restaurantes(
    categoria: Optional[str] = None,
    activo: Optional[bool] = None
):
    resultados = restaurantes_db
    if categoria:
        resultados = [r for r in resultados if r["categoria"].lower() == categoria.lower()]
    if activo is not None:
        resultados = [r for r in resultados if r["activo"] == activo]
    
    return {"total": len(resultados), "restaurantes": resultados}

# --- CARGA DE DATOS ---

@app.on_event("startup")
def cargar_datos_prueba():
    # Solo cargamos si la lista está vacía para evitar duplicados en reinicios
    if not restaurantes_db:
        datos = [
            {"id": 1, "nombre": "El Corral Universitario", "categoria": "Hamburguesas", "rating": 4.5, "activo": True},
            {"id": 2, "nombre": "Punto Rojo Express",       "categoria": "Corrientazo",  "rating": 4.1, "activo": True},
            {"id": 3, "nombre": "Sushi Nikkei UCC",         "categoria": "Sushi",        "rating": 4.8, "activo": False},
            {"id": 4, "nombre": "La Mazorca Criolla",       "categoria": "Corrientazo",  "rating": 3.9, "activo": True},
            {"id": 5, "nombre": "Pizza Hub Norte",          "categoria": "Pizza",        "rating": 4.2, "activo": True},
        ]
        restaurantes_db.extend(datos)