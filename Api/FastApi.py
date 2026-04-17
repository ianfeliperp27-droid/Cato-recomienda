from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Católica de Colombia",
    version="2.0.0"
)

# 1. Configuración de Rutas Dinámicas
# Esto asegura que Python encuentre los archivos sin importar dónde se ejecute
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. CORS: Evita bloqueos en el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Modelo de datos
class Restaurante(BaseModel):
    id: int
    nombre: str
    categoria: str
    rating: float
    activo: bool

restaurantes_db = []

# --- RUTAS PARA EL FRONTEND ---

@app.get("/", response_class=HTMLResponse)
def home():
    """Sirve la página de Login"""
    # Buscamos el archivo en la misma carpeta que este script
    path = os.path.join(BASE_DIR, "login.html")
    if not os.path.exists(path):
        return HTMLResponse(content=f"Error: No se encuentra login.html en {BASE_DIR}", status_code=404)
    return FileResponse(path)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Sirve el Dashboard principal"""
    # OJO: Verifica que el nombre sea exacto (cato-recomienda (1).html o dashboard.html)
    # Aquí lo buscamos como dashboard.html que es el estándar
    path = os.path.join(BASE_DIR, "dashboard.html")
    
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return HTMLResponse(content=f"Error: No se encuentra el archivo HTML del dashboard en {path}", status_code=404)

# --- RUTAS DE LA API ---

@app.get("/api/restaurantes")
def listar_restaurantes():
    return {"total": len(restaurantes_db), "restaurantes": restaurantes_db}

@app.post("/api/restaurantes")
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