import os
import hmac
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

# --------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "cato-recomienda-secret-2026")
ALGORITHM = "HS256"
EXPIRACION_HORAS = 24


def crear_token(usuario_id: int, email: str, rol: str = "cliente") -> str:
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=EXPIRACION_HORAS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# --------------------------------------------------------------------
# Hashing de contrasenas
# Formato nuevo:  "pbkdf2$<iteraciones>$<salt_hex>$<hash_hex>"
# Formato viejo:  "<sha256_hex>"  (64 caracteres hex, sin separadores)
# --------------------------------------------------------------------

PBKDF2_ITERS = 120_000


def hash_password(password: str) -> str:
    """Genera un hash PBKDF2-HMAC-SHA256 con salt aleatorio."""
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERS
    )
    return f"pbkdf2${PBKDF2_ITERS}${salt.hex()}${derived.hex()}"


def _verify_pbkdf2(password: str, stored: str) -> bool:
    try:
        _, iters_str, salt_hex, hash_hex = stored.split("$")
        iters = int(iters_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iters
    )
    return hmac.compare_digest(derived, expected)


def _verify_legacy_sha256(password: str, stored: str) -> bool:
    """Compatibilidad con la primera version (sha256 sin sal)."""
    expected = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, stored)


def verify_password(password: str, stored: str) -> bool:
    """
    Verifica una contrasena contra un hash almacenado.
    Acepta tanto el formato nuevo como el formato legacy de la v1.
    """
    if stored.startswith("pbkdf2$"):
        return _verify_pbkdf2(password, stored)
    # Fallback: hash viejo de 64 hex (sha256 plano).
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower()):
        return _verify_legacy_sha256(password, stored)
    return False


def needs_rehash(stored: str) -> bool:
    """True si el hash almacenado deberia migrarse al formato nuevo."""
    return not stored.startswith("pbkdf2$")

# --------------------------------------------------------------------
# Dependencias FastAPI: extraer usuario y forzar rol admin
# --------------------------------------------------------------------

from typing import Optional as _Optional
from fastapi import Header, HTTPException, Depends, status


def usuario_actual(authorization: _Optional[str] = Header(None)) -> dict:
    """Devuelve el payload del JWT o lanza 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no enviado",
        )
    token = authorization.split(" ", 1)[1]
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        )
    return payload


def verificar_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    """
    Dependencia para endpoints que requieren rol admin.
    Si el payload del JWT no tiene rol == "admin", levanta 403.
    """
    if usuario.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilegios insuficientes. Solo administradores pueden ejecutar esta accion.",
        )
    return usuario
