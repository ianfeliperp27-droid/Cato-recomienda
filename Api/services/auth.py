import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

