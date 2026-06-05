import logging
from typing import Optional

import jwt
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel

from database import get_session
from models.usuario import UsuarioCreate, UsuarioLogin
from repositories.usuario import UsuarioRepository
from services.auth import (
    crear_token,
    SECRET_KEY, ALGORITHM,
)

logger = logging.getLogger("CatoRecomienda.Auth")

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


# -------- Schemas para los nuevos endpoints --------

class ForgotPasswordIn(BaseModel):
    email: str


class ResetPasswordIn(BaseModel):
    token: str
    nueva_password: str


# -------- Helpers de tokens de recuperacion --------

RESET_EXPIRACION_MIN = 30


def _crear_token_reset(usuario_id: int, email: str) -> str:
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "scope": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_EXPIRACION_MIN),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _verificar_token_reset(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    if payload.get("scope") != "password_reset":
        return None
    return payload


# -------- Endpoints --------

@router.post("/registro")
def registro(datos: UsuarioCreate, session: Session = Depends(get_session)):
    if len(datos.password) < 6:
        raise HTTPException(status_code=400, detail="La contrasena debe tener al menos 6 caracteres")

    repo = UsuarioRepository(session)
    if repo.obtener_por_email(datos.email):
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


@router.post("/forgot-password")
def forgot_password(datos: ForgotPasswordIn, session: Session = Depends(get_session)):
    """
    Solicita un token de recuperacion. Devuelve siempre el mismo mensaje
    (no revela si el email existe). En produccion deberia enviar correo;
    aqui se simula con un log + token en el response para pruebas.
    """
    repo = UsuarioRepository(session)
    usuario = repo.obtener_por_email(datos.email)

    mensaje_publico = (
        "Si el correo esta registrado, recibiras un enlace de recuperacion "
        "en los proximos minutos."
    )

    if not usuario:
        # No revelar la inexistencia del usuario.
        logger.info(f"[FORGOT] Intento para email inexistente: {datos.email}")
        return {"ok": True, "mensaje": mensaje_publico}

    token_reset = _crear_token_reset(usuario.id, usuario.email)

    # Simulacion del envio (en produccion: SMTP / SendGrid / Azure Comm).
    logger.info(
        f"[FORGOT] Token de reset generado para {usuario.email} | "
        f"reset_url=/reset-password?token={token_reset}"
    )

    response = {"ok": True, "mensaje": mensaje_publico}

    # Modo desarrollo: incluye el token para poder probar el flujo sin SMTP.
    import os
    if os.getenv("ENTORNO", "desarrollo") != "produccion":
        response["debug_token"] = token_reset

    return response


@router.post("/reset-password")
def reset_password(datos: ResetPasswordIn, session: Session = Depends(get_session)):
    payload = _verificar_token_reset(datos.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Token invalido o expirado")

    if len(datos.nueva_password) < 6:
        raise HTTPException(status_code=400, detail="La contrasena debe tener al menos 6 caracteres")

    repo = UsuarioRepository(session)
    usuario = repo.obtener_por_id(int(payload["sub"]))
    if not usuario or usuario.email != payload["email"]:
        raise HTTPException(status_code=400, detail="Token invalido")

    repo.actualizar_password(usuario, datos.nueva_password)
    return {"ok": True, "mensaje": "Contrasena actualizada correctamente"}

@router.post("/seed-admin")
def seed_admin(session: Session = Depends(get_session)):
    """Endpoint temporal para crear el primer admin. Eliminar después."""
    import os
    if os.getenv("ENTORNO") == "produccion":
        raise HTTPException(status_code=404, detail="No existe")

    repo = UsuarioRepository(session)

    if repo.obtener_por_email("admin@cato.com"):
        return {"ok": True, "mensaje": "Admin ya existe"}

    from models.usuario import UsuarioCreate

    datos = UsuarioCreate(
        nombre="Admin Cato",
        email="admin@cato.com",
        password="Admin2026!"
    )

    usuario = repo.crear(datos)
    usuario.rol = "admin"

    session.add(usuario)
    session.commit()

    return {
        "ok": True,
        "email": "admin@cato.com",
        "password": "Admin2026!"
    }

