from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlmodel import Session

from database import get_session
from models.restaurante import (
    RestauranteCreate, RestauranteUpdate,
    CategoriaCreate, ResenaCreate,
)
from repositories.restaurante import RestauranteRepository
from repositories.categoria import CategoriaRepository
from repositories.resena import ResenaRepository
from patterns.decorator import LoggingRepositoryDecorator
from patterns.strategy import (
    BuscadorRestaurantes,
    FiltroPorCategoria, FiltroPorEstado,
    FiltroPorRating, OrdenarPorRating,
)
from patterns.observer import publicador
from services.auth import usuario_actual, verificar_admin
from services.uploads import guardar_imagen, eliminar_imagen_si_local


router = APIRouter(prefix="/restaurantes", tags=["restaurantes"])


# -------- Helpers --------

def _repo(session: Session) -> LoggingRepositoryDecorator:
    """Repo concreto envuelto en el decorator de logging (OCP)."""
    return LoggingRepositoryDecorator(RestauranteRepository(session))


# -------- Listado publico con filtros (Strategy) --------

@router.get("/")
def listar(
    categoria: Optional[str] = None,
    activo: Optional[bool] = None,
    rating_min: Optional[float] = None,
    ordenar: Optional[str] = None,  # "rating"
    session: Session = Depends(get_session),
):
    repo = _repo(session)
    base = repo.obtener_todos()

    if not (categoria or activo is not None or rating_min is not None or ordenar):
        return {"total": len(base), "restaurantes": base}

    estrategias = []

    if categoria:
        cat_repo = CategoriaRepository(session)
        cat = cat_repo.obtener_por_nombre(categoria)
        if not cat:
            return {"total": 0, "restaurantes": []}
        estrategias.append(FiltroPorCategoria(cat.id))

    if activo is not None:
        estrategias.append(FiltroPorEstado(activo))

    if rating_min is not None:
        estrategias.append(FiltroPorRating(rating_min))

    if ordenar == "rating":
        estrategias.append(OrdenarPorRating())

    resultado = BuscadorRestaurantes(estrategias).ejecutar(base)
    return {"total": len(resultado), "restaurantes": resultado}


# -------- Categorias --------

@router.get("/categorias")
def listar_categorias(session: Session = Depends(get_session)):
    cats = CategoriaRepository(session).obtener_todas()
    return {"total": len(cats), "categorias": cats}


@router.post("/categorias")
def crear_categoria(
    datos: CategoriaCreate,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(usuario_actual),
):
    return CategoriaRepository(session).crear(datos)


# -------- Detalle --------

@router.get("/{id}")
def obtener(id: int, session: Session = Depends(get_session)):
    r = _repo(session).obtener_por_id(id)
    if not r:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return r


# -------- Crear (JSON tradicional, sin foto local) --------

@router.post("/")
def crear(
    datos: RestauranteCreate,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(usuario_actual),
):
    nuevo = _repo(session).crear(datos)
    publicador.notificar_creacion(nuevo)
    return nuevo


# -------- Crear con upload de imagen (multipart/form-data) --------

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def crear_con_imagen(
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None),
    ciudad: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    categoria_id: Optional[int] = Form(None),
    horario: Optional[str] = Form(None),
    precio_prom: Optional[str] = Form(None),
    activo: bool = Form(True),
    imagen: UploadFile = File(...),
    session: Session = Depends(get_session),
    _usuario: dict = Depends(usuario_actual),
):
    """
    Crea un restaurante recibiendo metadatos via Form y la imagen via
    UploadFile. El archivo se valida (extension, tamaño), se guarda en
    static/uploads/ via streaming (no carga el binario completo en RAM)
    y la URL local resultante se persiste en BD.
    """
    try:
        url_foto = guardar_imagen(imagen)
    finally:
        await imagen.close()

    datos = RestauranteCreate(
        nombre=nombre,
        descripcion=descripcion,
        direccion=direccion,
        ciudad=ciudad,
        telefono=telefono,
        categoria_id=categoria_id,
        horario=horario,
        precio_prom=precio_prom,
        activo=activo,
        foto=url_foto,
    )

    nuevo = _repo(session).crear(datos)
    publicador.notificar_creacion(nuevo)
    return {"status": "success", "data": nuevo}


# -------- Actualizar --------

@router.put("/{id}")
def actualizar(
    id: int,
    datos: RestauranteUpdate,
    session: Session = Depends(get_session),
    _usuario: dict = Depends(usuario_actual),
):
    actualizado = _repo(session).actualizar(id, datos)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return actualizado


# -------- Eliminar (SOLO ADMIN) --------

@router.delete("/{id}")
def eliminar(
    id: int,
    session: Session = Depends(get_session),
    _admin: dict = Depends(verificar_admin),
):
    """
    Endpoint restringido. Requiere JWT valido CON rol=='admin'.
    El cascade_delete configurado en el modelo + PRAGMA foreign_keys=ON
    en database.py garantiza que las resenas asociadas tambien se
    eliminen sin violar integridad referencial.
    Tambien borra el archivo fisico de la imagen local si aplica.
    """
    eliminado = _repo(session).eliminar(id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )
    # Cleanup del archivo fisico (no rompe si no existe o si la URL es externa).
    eliminar_imagen_si_local(eliminado.foto)
    return {"ok": True, "eliminado": eliminado}


# -------- Resenas --------

@router.get("/{id}/resenas")
def listar_resenas(id: int, session: Session = Depends(get_session)):
    repo = _repo(session)
    restaurante = repo.obtener_por_id(id)
    if not restaurante:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    resenas = ResenaRepository(session).listar_por_restaurante(id)
    return {"total": len(resenas), "resenas": resenas}


@router.post("/{id}/resenas")
def crear_resena(
    id: int,
    datos: ResenaCreate,
    session: Session = Depends(get_session),
    usuario: dict = Depends(usuario_actual),
):
    repo = _repo(session)
    restaurante = repo.obtener_por_id(id)
    if not restaurante:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")

    if datos.puntuacion < 1 or datos.puntuacion > 5:
        raise HTTPException(status_code=400, detail="La puntuacion debe estar entre 1 y 5")

    resena_repo = ResenaRepository(session)
    resena = resena_repo.crear(restaurante, int(usuario["sub"]), datos)
    promedio = resena_repo.recalcular_promedio(restaurante)

    publicador.notificar_resena(restaurante, resena)

    return {
        "ok": True,
        "resena": resena,
        "promedio_actualizado": promedio,
    }