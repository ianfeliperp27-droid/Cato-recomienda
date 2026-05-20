# models.py
# Responsabilidad: SOLO define la entidad de dominio
# Principio SOLID aplicado: S (Single Responsibility), L (Liskov)

from sqlmodel import Field, SQLModel
from typing import Optional


# Entidad de base de datos
class Restaurante(SQLModel, table=True):
    id:        Optional[int] = Field(default=None, primary_key=True)
    nombre:    str
    categoria: str
    rating:    float
    activo:    bool = True


# DTO de entrada — separa el modelo de BD del modelo de entrada
# Principio L: no mezcla tabla con validacion de entrada
class RestauranteCreate(SQLModel):
    nombre:    str
    categoria: str
    rating:    float
    activo:    bool = True


# DTO de actualizacion
class RestauranteUpdate(SQLModel):
    nombre:    Optional[str]   = None
    categoria: Optional[str]   = None
    rating:    Optional[float] = None
    activo:    Optional[bool]  = None