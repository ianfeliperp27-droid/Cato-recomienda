from sqlmodel import Field, SQLModel
from typing import Optional


class Usuario(SQLModel, table=True):
    id:       Optional[int] = Field(default=None, primary_key=True)
    nombre:   str
    email:    str
    password: str
    rol:      str = "cliente"
    avatar:   Optional[str] = None
    activo:   bool = True
    baneado:  bool = False


class UsuarioCreate(SQLModel):
    nombre:   str
    email:    str
    password: str
    rol:      str = "cliente"


class UsuarioLogin(SQLModel):
    email:    str
    password: str

