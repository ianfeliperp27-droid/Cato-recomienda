from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from dotenv import load_dotenv

load_dotenv()

from database import crear_tablas, engine
from repositories.categoria import CategoriaRepository
from repositories.restaurante import RestauranteRepository
from routes.vistas import router as vistas_router
from routes.restaurantes import router as restaurantes_router
from routes.usuarios import router as usuarios_router


CATEGORIAS_SEED = ["Hamburguesas", "Corrientazo", "Sushi", "Pizza", "Tacos"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Reemplaza a @app.on_event('startup') (deprecated en FastAPI >=0.110)."""
    crear_tablas()
    with Session(engine) as session:
        CategoriaRepository(session).seed(CATEGORIAS_SEED)
        RestauranteRepository(session).seed()
    yield
    # nada que cerrar al apagar


app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Catolica de Colombia",
    version="4.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(vistas_router)
app.include_router(restaurantes_router)
app.include_router(usuarios_router)

