# database.py
# Responsabilidad: SOLO configuracion de la base de datos
# Principios SOLID aplicados:
#   S — unica razon de cambio: la BD
#   D — lee la URL desde variables de entorno, no hardcodeada

import os
from sqlmodel import SQLModel, Session, create_engine

# D: depende de variable de entorno, no de valor hardcodeado
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///restaurantes.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # necesario para SQLite
)


def crear_tablas():
    """Crea todas las tablas definidas en los modelos."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Generador de sesiones — usado como dependencia en FastAPI."""
    with Session(engine) as session:
        yield session