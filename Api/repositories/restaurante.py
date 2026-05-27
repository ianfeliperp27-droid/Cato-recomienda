from sqlmodel import Session, select
from typing import List, Optional
from models.restaurante import Restaurante, RestauranteCreate, RestauranteUpdate
from patterns.adapter import IRestauranteRepository


class RestauranteRepository(IRestauranteRepository):
    """
    Patron Repositorio. Implementa la interface IRestauranteRepository
    (DIP: las rutas dependen de la abstraccion, no de esta clase).

    El filtrado se hace via Strategy Pattern fuera del repo, por eso
    aqui NO hay metodo filtrar() (era codigo muerto, se elimino).
    """

    def __init__(self, session: Session):
        self.session = session

    def obtener_todos(self) -> List[Restaurante]:
        return self.session.exec(select(Restaurante)).all()

    def obtener_por_id(self, id: int) -> Optional[Restaurante]:
        return self.session.get(Restaurante, id)

    def crear(self, datos: RestauranteCreate) -> Restaurante:
        r = Restaurante(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            direccion=datos.direccion,
            ciudad=datos.ciudad,
            telefono=datos.telefono,
            categoria_id=datos.categoria_id,
            foto=datos.foto,
            horario=datos.horario,
            precio_prom=datos.precio_prom,
            activo=datos.activo,
        )
        self.session.add(r)
        self.session.commit()
        self.session.refresh(r)
        return r

    def actualizar(
        self, id: int, datos: RestauranteUpdate
    ) -> Optional[Restaurante]:
        r = self.session.get(Restaurante, id)
        if not r:
            return None
        for campo, valor in datos.dict(exclude_unset=True).items():
            setattr(r, campo, valor)
        self.session.commit()
        self.session.refresh(r)
        return r

    def eliminar(self, id: int) -> Optional[Restaurante]:
        r = self.session.get(Restaurante, id)
        if not r:
            return None
        self.session.delete(r)
        self.session.commit()
        return r

    def seed(self) -> None:
        if self.obtener_todos():
            return
        datos = [
            RestauranteCreate(
                nombre="El Corral Universitario",
                descripcion="Las mejores hamburguesas cerca de la Catolica.",
                direccion="Calle 47 #13-37, La Candelaria",
                ciudad="Bogota", telefono="3001234567",
                categoria_id=1,
                foto="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
                horario="Lun-Vie 11am-9pm",
                precio_prom="$18.000 - $35.000", activo=True,
            ),
            RestauranteCreate(
                nombre="Punto Rojo Express",
                descripcion="Corrientazo completo al mejor precio.",
                direccion="Carrera 13 #45-20, Bogota",
                ciudad="Bogota", telefono="3007654321",
                categoria_id=2,
                foto="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
                horario="Lun-Sab 11:30am-3pm",
                precio_prom="$10.000 - $16.000", activo=True,
            ),
            RestauranteCreate(
                nombre="Sushi Nikkei UCC",
                descripcion="Fusion japonesa-peruana.",
                direccion="Avenida 19 #118-30, Bogota",
                ciudad="Bogota", telefono="3009876543",
                categoria_id=3,
                foto="https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=800",
                horario="Mar-Dom 12pm-10pm",
                precio_prom="$25.000 - $60.000", activo=False,
            ),
            RestauranteCreate(
                nombre="La Mazorca Criolla",
                descripcion="Comida casera y economica.",
                direccion="Calle 46 #14-10, Bogota",
                ciudad="Bogota", telefono="3001112233",
                categoria_id=2,
                foto="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800",
                horario="Lun-Vie 11am-3pm",
                precio_prom="$9.000 - $14.000", activo=True,
            ),
            RestauranteCreate(
                nombre="Pizza Hub Norte",
                descripcion="Pizzas artesanales con masa madre.",
                direccion="Carrera 15 #48-55, Bogota",
                ciudad="Bogota", telefono="3004445566",
                categoria_id=4,
                foto="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
                horario="Lun-Dom 12pm-11pm",
                precio_prom="$20.000 - $45.000", activo=True,
            ),
        ]
        for d in datos:
            self.crear(d)