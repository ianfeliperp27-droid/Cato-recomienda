from sqlmodel import Session, select
from typing import Optional
from models import Restaurante, RestauranteCreate, RestauranteUpdate


class RestauranteRepository:

    def __init__(self, session: Session):
        self.session = session

    def obtener_todos(self) -> list:
        return self.session.exec(select(Restaurante)).all()

    def obtener_por_id(self, id: int):
        return self.session.get(Restaurante, id)

    def filtrar(self, categoria: Optional[str] = None, activo: Optional[bool] = None) -> list:
        query = select(Restaurante)
        if categoria:
            query = query.where(Restaurante.categoria == categoria)
        if activo is not None:
            query = query.where(Restaurante.activo == activo)
        return self.session.exec(query).all()

    def crear(self, datos: RestauranteCreate):
        restaurante = Restaurante(
            nombre=datos.nombre,
            categoria=datos.categoria,
            rating=datos.rating,
            activo=datos.activo
        )
        self.session.add(restaurante)
        self.session.commit()
        self.session.refresh(restaurante)
        return restaurante

    def actualizar(self, id: int, datos: RestauranteUpdate):
        r = self.session.get(Restaurante, id)
        if not r:
            return None
        campos = datos.dict(exclude_unset=True)
        for campo, valor in campos.items():
            setattr(r, campo, valor)
        self.session.commit()
        self.session.refresh(r)
        return r

    def eliminar(self, id: int):
        r = self.session.get(Restaurante, id)
        if not r:
            return None
        self.session.delete(r)
        self.session.commit()
        return r

    def seed(self):
        if self.obtener_todos():
            return
        datos_iniciales = [
            RestauranteCreate(nombre="El Corral Universitario", categoria="Hamburguesas", rating=4.5, activo=True),
            RestauranteCreate(nombre="Punto Rojo Express",      categoria="Corrientazo",  rating=4.1, activo=True),
            RestauranteCreate(nombre="Sushi Nikkei UCC",        categoria="Sushi",        rating=4.8, activo=False),
            RestauranteCreate(nombre="La Mazorca Criolla",      categoria="Corrientazo",  rating=3.9, activo=True),
            RestauranteCreate(nombre="Pizza Hub Norte",         categoria="Pizza",        rating=4.2, activo=True),
        ]
        for d in datos_iniciales:
            self.crear(d)
