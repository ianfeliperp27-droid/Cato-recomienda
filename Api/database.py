import os
from sqlmodel import SQLModel, Session
from dotenv import load_dotenv
from patterns.factory import get_database_factory

load_dotenv()

engine = get_database_factory().crear_engine()

def crear_tablas():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
