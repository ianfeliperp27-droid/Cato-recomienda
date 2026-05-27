from sqlmodel import SQLModel, Session
from sqlalchemy import event
from dotenv import load_dotenv

from patterns.factory import get_database_factory

load_dotenv()

engine = get_database_factory().crear_engine()


# Activar foreign keys en SQLite en cada conexion del pool.
if engine.url.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def crear_tablas():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
