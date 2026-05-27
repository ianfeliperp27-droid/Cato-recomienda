from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime


class Categoria(SQLModel, table=True):
    id:     Optional[int] = Field(default=None, primary_key=True)
    nombre: str

    restaurantes: List["Restaurante"] = Relationship(back_populates="categoria_rel")


class Restaurante(SQLModel, table=True):
    id:                    Optional[int] = Field(default=None, primary_key=True)
    nombre:                str
    descripcion:           Optional[str] = None
    direccion:             Optional[str] = None
    ciudad:                Optional[str] = None
    telefono:              Optional[str] = None
    categoria_id:          Optional[int] = Field(default=None, foreign_key="categoria.id")
    promedio_calificacion: float = 0.0
    activo:                bool = True
    foto:                  Optional[str] = None
    horario:               Optional[str] = None
    precio_prom:           Optional[str] = None

    categoria_rel: Optional[Categoria] = Relationship(back_populates="restaurantes")

    # cascade_delete=True hace que SQLModel borre la relacion en memoria.
    # Para que SQLite tambien lo aplique a nivel BD, las FK de Resena y
    # Multimedia se declaran con sa_relationship_kwargs en su lado y con
    # ON DELETE CASCADE via foreign_key + sa_column. Aqui activamos el
    # lado Python; en database.py habilitamos foreign_keys=ON en SQLite.
    resenas: List["Resena"] = Relationship(
        back_populates="restaurante",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    multimedia: List["Multimedia"] = Relationship(
        back_populates="restaurante",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Resena(SQLModel, table=True):
    id:             Optional[int] = Field(default=None, primary_key=True)
    usuario_id:     int = Field(foreign_key="usuario.id")
    restaurante_id: int = Field(
        foreign_key="restaurante.id",
        sa_column_kwargs={"nullable": False},
    )
    puntuacion:     int
    comentario:     Optional[str] = None
    fecha:          datetime = Field(default_factory=datetime.utcnow)

    restaurante: Optional[Restaurante] = Relationship(back_populates="resenas")


class Multimedia(SQLModel, table=True):
    id:             Optional[int] = Field(default=None, primary_key=True)
    restaurante_id: Optional[int] = Field(default=None, foreign_key="restaurante.id")
    resena_id:      Optional[int] = Field(default=None, foreign_key="resena.id")
    url:            str
    tipo:           str = "foto"

    restaurante: Optional[Restaurante] = Relationship(back_populates="multimedia")


# ---------------- DTOs ----------------

class RestauranteCreate(SQLModel):
    nombre:       str
    descripcion:  Optional[str] = None
    direccion:    Optional[str] = None
    ciudad:       Optional[str] = None
    telefono:     Optional[str] = None
    categoria_id: Optional[int] = None
    foto:         Optional[str] = None
    horario:      Optional[str] = None
    precio_prom:  Optional[str] = None
    activo:       bool = True


class RestauranteUpdate(SQLModel):
    nombre:       Optional[str]   = None
    descripcion:  Optional[str]   = None
    direccion:    Optional[str]   = None
    ciudad:       Optional[str]   = None
    telefono:     Optional[str]   = None
    categoria_id: Optional[int]   = None
    foto:         Optional[str]   = None
    horario:      Optional[str]   = None
    precio_prom:  Optional[str]   = None
    activo:       Optional[bool]  = None


class ResenaCreate(SQLModel):
    restaurante_id: int
    puntuacion:     int
    comentario:     Optional[str] = None


class CategoriaCreate(SQLModel):
    nombre: str

