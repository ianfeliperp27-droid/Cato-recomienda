"""
Patron Adapter / Interface.

Define el contrato que toda implementacion concreta de
RestauranteRepository debe cumplir. Permite que las rutas dependan
de esta abstraccion (DIP) en lugar de la clase concreta.

NOTA: el metodo filtrar() existia en la v1 pero fue eliminado porque
quedo como codigo muerto cuando los filtros pasaron a aplicarse via
Strategy Pattern en la capa de rutas.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IRestauranteRepository(ABC):
    @abstractmethod
    def obtener_todos(self) -> list:
        pass

    @abstractmethod
    def obtener_por_id(self, id: int):
        pass

    @abstractmethod
    def crear(self, datos) -> object:
        pass

    @abstractmethod
    def actualizar(self, id: int, datos) -> Optional[object]:
        pass

    @abstractmethod
    def eliminar(self, id: int) -> Optional[object]:
        pass

