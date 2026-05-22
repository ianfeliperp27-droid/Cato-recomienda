from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from typing import Optional

from database import get_session
from models.restaurante import (
    Restaurante, RestauranteCreate, RestauranteUpdate,
    Categoria, CategoriaCreate,
    Resena, ResenaCreate,
)
from repositories.restaurante import RestauranteRepository
from patterns.decorator import LoggingRepositoryDecorator
from patterns.strategy import (
    BuscadorRestaurantes,
    FiltroPorCategoria, FiltroPorEstado,
    FiltroPorRating, OrdenarPorRating,
)
from patterns.observer import publicador
from services.auth import verificar_token


router = APIRouter(prefix="/restaurantes", tags=["restaurantes"])


def _repo(session: Session) -> LoggingRepositoryDecorator:
    """Helper que envuelve el repo concreto con el decorator de logging."""
    return LoggingRepositoryDecorator(RestauranteRepository(session))


def _usuario_actual(authorization: Optional[str] = Header(None)) -> dict:
    """Dependencia para extraer el usuario del JWT en el header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no enviado")
    token = authorization.split(" ", 1)[1]
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    return payload


# ---------------- LISTADO + FILTRADO (publico) ----------------

@router.get("/")
def listar(
    categoria: Optional[str] = None,
    activo: Optional[bool] = None,
    rating_min: Optional[float] = None,
    ordenar: Optional[str] = None,  # "rating" para ordenar por rating
    session: Session = Depends(get_session),
):
    """
    Lista de restaurantes. Aplica Strategy Pattern para los filtros
    cuando hay parametros. Sin parametros, devuelve todos.
    """
    repo = _repo(session)
    base = repo.obtener_todos()

    # Si no hay ningun filtro, devuelve todo
    if not (categoria or activo is not None or rating_min is not None or ordenar):
        return {"total": len(base), "restaurantes": base}

    estrategias = []

    if categoria:
        cat = session.exec(select(Categoria).where(Categoria.nombre == categoria)).first()
        if cat:
            estrategias.append(FiltroPorCategoria(cat.id))
        else:
            return {"total": 0, "restaurantes": []}

    if activo is not None:
        estrategias.append(FiltroPorEstado(activo))

    if rating_min is not None:
        estrategias.append(FiltroPorRating(rating_min))

    if ordenar == "rating":
        estrategias.append(OrdenarPorRating())

    buscador = BuscadorRestaurantes(estrategias)
    resultado = buscador.ejecutar(base)
    return {"total": len(resultado), "restaurantes": resultado}


@router.get("/categorias")
def listar_categorias(session: Session = Depends(get_session)):
    cats = session.exec(select(Categoria)).all()
    return {"total": len(cats), "categorias": cats}


@router.post("/categorias")
def crear_categoria(
    datos: CategoriaCreate,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(_usuario_actual),
):
    cat = Categoria(nombre=datos.nombre)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return cat


@router.get("/{id}")
def obtener(id: int, session: Session = Depends(get_session)):
    repo = _repo(session)
    r = repo.obtener_por_id(id)
    if not r:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return r


# ---------------- CRUD (requiere login) ----------------

@router.post("/")
def crear(
    datos: RestauranteCreate,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(_usuario_actual),
):
    repo = _repo(session)
    nuevo = repo.crear(datos)
    # Observer Pattern: notificar suscriptores
    publicador.notificar_creacion(nuevo)
    return nuevo


@router.put("/{id}")
def actualizar(
    id: int,
    datos: RestauranteUpdate,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(_usuario_actual),
):
    repo = _repo(session)
    actualizado = repo.actualizar(id, datos)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return actualizado


@router.delete("/{id}")
def eliminar(
    id: int,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(_usuario_actual),
):
    repo = _repo(session)
    eliminado = repo.eliminar(id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return {"ok": True, "eliminado": eliminado}


# ---------------- RESEÑAS ----------------

@router.get("/{id}/resenas")
def listar_resenas(id: int, session: Session = Depends(get_session)):
    r = session.get(Restaurante, id)
    if not r:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    resenas = session.exec(select(Resena).where(Resena.restaurante_id == id)).all()
    return {"total": len(resenas), "resenas": resenas}


@router.post("/{id}/resenas")
def crear_resena(
    id: int,
    datos: ResenaCreate,
    session: Session = Depends(get_session),
    usuario: dict = Depends(_usuario_actual),
):
    """
    Crea una reseña y recalcula el promedio del restaurante automaticamente.
    Notifica via Observer Pattern.
    """
    restaurante = session.get(Restaurante, id)
    if not restaurante:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")

    if datos.puntuacion < 1 or datos.puntuacion > 5:
        raise HTTPException(status_code=400, detail="La puntuacion debe estar entre 1 y 5")

    usuario_id = int(usuario["sub"])

    resena = Resena(
        usuario_id=usuario_id,
        restaurante_id=id,
        puntuacion=datos.puntuacion,
        comentario=datos.comentario,
    )
    session.add(resena)
    session.commit()
    session.refresh(resena)

    # Recalcular promedio
    todas = session.exec(select(Resena).where(Resena.restaurante_id == id)).all()
    if todas:
        promedio = sum(r.puntuacion for r in todas) / len(todas)
        restaurante.promedio_calificacion = round(promedio, 2)
        session.add(restaurante)
        session.commit()
        session.refresh(restaurante)

    # Observer: notificar nueva reseña
    publicador.notificar_resena(restaurante, resena)

    return {
        "ok": True,
        "resena": resena,
        "promedio_actualizado": restaurante.promedio_calificacion,
    }

