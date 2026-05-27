import os
import uuid
import shutil
from typing import Optional

from fastapi import UploadFile, HTTPException, status


EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "webp"}

# Limite blando de 5 MB. SpooledTemporaryFile de Starlette mantiene en
# memoria archivos pequeños y vuelca a disco los grandes, pero igual
# rechazamos archivos enormes para evitar abuso.
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# Directorios. UPLOAD_DIR es el path en disco; URL_PREFIX es la ruta
# publica servida por StaticFiles.
UPLOAD_DIR = os.path.join("static", "uploads")
URL_PREFIX = "/static/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _extraer_extension(filename: Optional[str]) -> str:
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no tiene extension reconocible.",
        )
    ext = filename.rsplit(".", 1)[-1].lower().strip()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension no permitida. Permitidas: {sorted(EXTENSIONES_PERMITIDAS)}",
        )
    return ext


def guardar_imagen(archivo: UploadFile) -> str:
    """
    Guarda el archivo subido en static/uploads/<uuid>.<ext> usando
    streaming a disco. Devuelve la URL estatica relativa para persistir
    en BD (ej. '/static/uploads/abc123.jpg').

    Levanta HTTPException si la extension no es valida o si el archivo
    excede MAX_BYTES.
    """
    ext = _extraer_extension(archivo.filename)
    nombre_final = f"{uuid.uuid4().hex}.{ext}"
    ruta_destino = os.path.join(UPLOAD_DIR, nombre_final)

    # Validacion de tamaño usando seek/tell sobre el SpooledTemporaryFile.
    archivo.file.seek(0, os.SEEK_END)
    tamano = archivo.file.tell()
    archivo.file.seek(0)
    if tamano > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el limite de {MAX_BYTES // (1024*1024)} MB.",
        )

    # Streaming a disco. shutil.copyfileobj usa un buffer fijo (default
    # 64 KB) y NO carga el archivo entero en RAM.
    with open(ruta_destino, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)

    return f"{URL_PREFIX}/{nombre_final}"


def eliminar_imagen_si_local(url: Optional[str]) -> None:
    """
    Borra el archivo fisico si la url es local (comienza con URL_PREFIX).
    Util al eliminar un restaurante para no dejar archivos huerfanos.
    No levanta si el archivo no existe.
    """
    if not url or not url.startswith(URL_PREFIX + "/"):
        return
    nombre = url[len(URL_PREFIX) + 1 :]
    # Defensa contra path traversal aunque el nombre venga del propio backend.
    if "/" in nombre or "\\" in nombre or ".." in nombre:
        return
    ruta = os.path.join(UPLOAD_DIR, nombre)
    try:
        os.remove(ruta)
    except FileNotFoundError:
        pass
    except OSError:
        # Permisos u otra causa: no rompemos la eliminacion del registro.
        pass
