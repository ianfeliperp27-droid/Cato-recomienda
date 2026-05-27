from sqlmodel import Session, select
from typing import List, Optional
from models.restaurante import Categoria, CategoriaCreate


class CategoriaRepository:
    """
    Patron Repositorio para Categoria. Las rutas no deben hacer
    select/commit; deben llamar metodos de este repositorio.
    """

    def __init__(self, session: Session):
        self.session = session

    def obtener_todas(self) -> List[Categoria]:
        return self.session.exec(select(Categoria)).all()

    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        return self.session.exec(
            select(Categoria).where(Categoria.nombre == nombre)
        ).first()

    def obtener_por_id(self, id: int) -> Optional[Categoria]:
        return self.session.get(Categoria, id)

    def crear(self, datos: CategoriaCreate) -> Categoria:
        cat = Categoria(nombre=datos.nombre)
        self.session.add(cat)
        self.session.commit()
        self.session.refresh(cat)
        return cat

    def seed(self, nombres: List[str]) -> None:
        if self.obtener_todas():
            return
        for nombre in nombres:
            self.session.add(Categoria(nombre=nombre))
        self.session.commit()

