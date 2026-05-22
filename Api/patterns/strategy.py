from abc import ABC, abstractmethod
from typing import List, Optional


class FiltroStrategy(ABC):
    @abstractmethod
    def filtrar(self, restaurantes: list) -> list:
        pass


class FiltroPorCategoria(FiltroStrategy):
    """
    Filtra restaurantes por categoria_id.
    Recibe el id resuelto (la traduccion nombre -> id la hace el repo).
    """
    def __init__(self, categoria_id: int):
        self.categoria_id = categoria_id

    def filtrar(self, restaurantes: list) -> list:
        return [r for r in restaurantes if r.categoria_id == self.categoria_id]


class FiltroPorEstado(FiltroStrategy):
    def __init__(self, activo: bool):
        self.activo = activo

    def filtrar(self, restaurantes: list) -> list:
        return [r for r in restaurantes if r.activo == self.activo]


class FiltroPorRating(FiltroStrategy):
    def __init__(self, rating_minimo: float):
        self.rating_minimo = rating_minimo

    def filtrar(self, restaurantes: list) -> list:
        return [r for r in restaurantes if r.promedio_calificacion >= self.rating_minimo]


class OrdenarPorRating(FiltroStrategy):
    def filtrar(self, restaurantes: list) -> list:
        return sorted(restaurantes, key=lambda r: r.promedio_calificacion, reverse=True)


class OrdenarPorNombre(FiltroStrategy):
    def filtrar(self, restaurantes: list) -> list:
        return sorted(restaurantes, key=lambda r: r.nombre.lower())


class BuscadorRestaurantes:
    """
    Contexto del patron Strategy. Aplica una pipeline de estrategias en orden.
    """
    def __init__(self, estrategias: List[FiltroStrategy]):
        self._estrategias = estrategias

    def ejecutar(self, restaurantes: list) -> list:
        resultado = restaurantes
        for estrategia in self._estrategias:
            resultado = estrategia.filtrar(resultado)
        return resultado

