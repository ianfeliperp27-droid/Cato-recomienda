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
    @abstractmethod
    def filtrar(self, categoria: Optional[str], activo: Optional[bool]) -> list:
        pass

