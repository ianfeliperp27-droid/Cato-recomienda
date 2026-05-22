from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database import get_session
from models.usuario import UsuarioCreate, UsuarioLogin
from repositories.usuario import UsuarioRepository
from services.auth import crear_token


router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("/registro")
def registro(datos: UsuarioCreate, session: Session = Depends(get_session)):
    repo = UsuarioRepository(session)
    existente = repo.obtener_por_email(datos.email)
    if existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    usuario = repo.crear(datos)
    token = crear_token(usuario.id, usuario.email, usuario.rol)
    return {
        "ok": True,
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
        },
        "token": token,
    }


@router.post("/login")
def login(datos: UsuarioLogin, session: Session = Depends(get_session)):
    repo = UsuarioRepository(session)
    usuario = repo.verificar_password(datos.email, datos.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    if usuario.baneado or not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo o baneado")
    token = crear_token(usuario.id, usuario.email, usuario.rol)
    return {
        "ok": True,
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
        },
        "token": token,
    }
