from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from dotenv import load_dotenv

load_dotenv()

from database import crear_tablas, engine
from models.restaurante import Categoria
from repositories.restaurante import RestauranteRepository
from routes.vistas import router as vistas_router
from routes.restaurantes import router as restaurantes_router
from routes.usuarios import router as usuarios_router

app = FastAPI(
    title="Cato-Recomienda API",
    description="API de restaurantes cercanos a la Universidad Católica de Colombia",
    version="4.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(vistas_router)
app.include_router(restaurantes_router)
app.include_router(usuarios_router)

@app.on_event("startup")
def startup():
    crear_tablas()
    with Session(engine) as session:
        # Seed categorias primero
        cats = session.exec(select(Categoria)).all()
        if not cats:
            for nombre in ["Hamburguesas", "Corrientazo", "Sushi", "Pizza", "Tacos"]:
                session.add(Categoria(nombre=nombre))
            session.commit()
        # Seed restaurantes
        repo = RestauranteRepository(session)
        repo.seed()
