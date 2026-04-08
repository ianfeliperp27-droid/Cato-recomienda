from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
 
app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Católica de Colombia",
    version="2.0.0"
)
 
# ─────────────────────────────────────────
# A. MODELO DE DATOS (Pydantic)
# ─────────────────────────────────────────
 
class Restaurante(BaseModel):
    id: int
    nombre: str
    categoria: str        # ej: "Corrientazo", "Pizza", "Sushi"
    rating: float         # 0.0 a 5.0
    activo: bool          # True si está abierto actualmente
 
# Base de datos temporal (lista en memoria)
restaurantes_db: list = []
 
 
# ─────────────────────────────────────────
# B. RUTAS (Routing)
# ─────────────────────────────────────────
 
# Página de inicio
@app.get("/", response_class=HTMLResponse)
def home():
    with open("login.html", "r") as f:
        return f.read()
 
 
# B.1 GET total — devuelve todos los restaurantes
@app.get("/restaurantes", summary="Listar todos los restaurantes")
def listar_restaurantes():
    return {"total": len(restaurantes_db), "restaurantes": restaurantes_db}
 
 
# B.2 POST — crea un nuevo restaurante
@app.post("/restaurantes", summary="Crear un restaurante")
def crear_restaurante(restaurante: Restaurante):
    for r in restaurantes_db:
        if r["id"] == restaurante.id:
            raise HTTPException(status_code=400, detail=f"Ya existe un restaurante con id={restaurante.id}")
    restaurantes_db.append(restaurante.model_dump())
    return {"mensaje": "Restaurante creado exitosamente", "restaurante": restaurante}
 
 
# B.3 GET por ID (Path Parameter) + B.4 Error 404
@app.get("/restaurantes/{id}", summary="Buscar restaurante por ID")
def obtener_restaurante(id: int):
    for r in restaurantes_db:
        if r["id"] == id:
            return r
    raise HTTPException(status_code=404, detail=f"Restaurante con id={id} no encontrado")
 
 
# B.5 GET con filtro (Query Parameter)
@app.get("/restaurantes/buscar/filtro", summary="Filtrar restaurantes por categoria o estado")
def filtrar_restaurantes(
    categoria: Optional[str] = None,
    activo: Optional[bool] = None
):
    resultados = restaurantes_db
 
    if categoria:
        resultados = [r for r in resultados if r["categoria"].lower() == categoria.lower()]
 
    if activo is not None:
        resultados = [r for r in resultados if r["activo"] == activo]
 
    if not resultados:
        raise HTTPException(status_code=404, detail="No se encontraron restaurantes con ese filtro")
 
    return {"total": len(resultados), "restaurantes": resultados}
 
 
# ─────────────────────────────────────────
# DATOS DE PRUEBA
# ─────────────────────────────────────────
 
@app.on_event("startup")
def cargar_datos_prueba():
    datos = [
        {"id": 1, "nombre": "El Corral Universitario", "categoria": "Hamburguesas", "rating": 4.5, "activo": True},
        {"id": 2, "nombre": "Punto Rojo Express",      "categoria": "Corrientazo",  "rating": 4.1, "activo": True},
        {"id": 3, "nombre": "Sushi Nikkei UCC",        "categoria": "Sushi",        "rating": 4.8, "activo": False},
        {"id": 4, "nombre": "La Mazorca Criolla",      "categoria": "Corrientazo",  "rating": 3.9, "activo": True},
        {"id": 5, "nombre": "Pizza Hub Norte",         "categoria": "Pizza",        "rating": 4.2, "activo": True},
    ]
    restaurantes_db.extend(datos)