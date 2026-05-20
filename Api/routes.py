from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session
import os

from database import get_session
from models import RestauranteCreate, RestauranteUpdate
from repository import RestauranteRepository

router = APIRouter()
HTML_DIR = os.getenv("HTML_DIR", ".")

def get_repo(session: Session = Depends(get_session)):
    return RestauranteRepository(session)

@router.get("/", response_class=HTMLResponse)
def home():
    with open(f"{HTML_DIR}/login.html", "r") as f:
        return f.read()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open(f"{HTML_DIR}/dashboard.html", "r") as f:
        return f.read()

@router.get("/restaurantes")
def listar(repo=Depends(get_repo)):
    restaurantes = repo.obtener_todos()
    return {"total": len(restaurantes), "restaurantes": restaurantes}

@router.get("/restaurantes/buscar/filtro")
def filtrar(categoria: str = None, activo: bool = None, repo=Depends(get_repo)):
    resultados = repo.filtrar(categoria=categoria, activo=activo)
    if not resultados:
        raise HTTPException(status_code=404, detail="Sin resultados")
    return {"total": len(resultados), "restaurantes": resultados}

@router.get("/restaurantes/{id}")
def obtener(id: int, repo=Depends(get_repo)):
    r = repo.obtener_por_id(id)
    if not r:
        raise HTTPException(status_code=404, detail=f"id={id} no encontrado")
    return r

@router.post("/restaurantes")
def crear(datos: RestauranteCreate, repo=Depends(get_repo)):
    r = repo.crear(datos)
    return {"mensaje": "Restaurante creado", "restaurante": r}

@router.put("/restaurantes/{id}")
def actualizar(id: int, datos: RestauranteUpdate, repo=Depends(get_repo)):
    r = repo.actualizar(id, datos)
    if not r:
        raise HTTPException(status_code=404, detail=f"id={id} no encontrado")
    return {"mensaje": "Actualizado", "restaurante": r}

@router.delete("/restaurantes/{id}")
def eliminar(id: int, repo=Depends(get_repo)):
    r = repo.eliminar(id)
    if not r:
        raise HTTPException(status_code=404, detail=f"id={id} no encontrado")
    return {"mensaje": f"Restaurante '{r.nombre}' eliminado"}