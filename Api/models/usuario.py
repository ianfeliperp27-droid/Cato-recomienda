from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import field_validator


ROLES_VALIDOS = {"user", "admin", "cliente"}  # "cliente" se acepta por compat con BD v4.0


class Usuario(SQLModel, table=True):
    id:       Optional[int] = Field(default=None, primary_key=True)
    nombre:   str
    email:    str = Field(index=True, unique=True)
    password: str
    rol:      str = Field(default="user")
    avatar:   Optional[str] = None
    activo:   bool = True
    baneado:  bool = False


class UsuarioCreate(SQLModel):
    nombre:   str
    email:    str
    password: str
    rol:      str = "user"

    @field_validator("rol")
    @classmethod
    def _rol_valido(cls, v: str) -> str:
        if v not in ROLES_VALIDOS:
            raise ValueError(f"rol debe ser uno de {sorted(ROLES_VALIDOS)}")
        # Normalizamos cliente -> user en nuevas inserciones, pero la BD vieja queda intacta.
        return "user" if v == "cliente" else v


class UsuarioLogin(SQLModel):
    email:    str
    password: str


def es_admin(rol: str) -> bool:
    """Helper unico para evaluar privilegios."""
    return rol == "admin"
