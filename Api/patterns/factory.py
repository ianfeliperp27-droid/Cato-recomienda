import os
from sqlmodel import create_engine
from abc import ABC, abstractmethod

class DatabaseFactory(ABC):
    @abstractmethod
    def crear_engine(self):
        pass

class SQLiteFactory(DatabaseFactory):
    def crear_engine(self):
        url = os.getenv("DATABASE_URL", "sqlite:///restaurantes.db")
        return create_engine(url, connect_args={"check_same_thread": False})

class PostgreSQLFactory(DatabaseFactory):
    def crear_engine(self):
        url = os.getenv("DATABASE_URL")
        return create_engine(url)

def get_database_factory() -> DatabaseFactory:
    entorno = os.getenv("ENTORNO", "desarrollo")
    if entorno == "produccion":
        return PostgreSQLFactory()
    return SQLiteFactory()

