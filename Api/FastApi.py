from fastapi import FastAPI
from sqlmodel import Session
from dotenv import load_dotenv

load_dotenv()

from database import crear_tablas, engine
from repository import RestauranteRepository
from routes import router

app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Católica de Colombia",
    version="3.0.0"
)

app.include_router(router)

@app.on_event("startup")
def startup():
    crear_tablas()
    with Session(engine) as session:
        repo = RestauranteRepository(session)
        repo.seed()
