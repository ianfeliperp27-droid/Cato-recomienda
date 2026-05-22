import logging
from typing import Optional
from patterns.adapter import IRestauranteRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CatoRecomienda")

class LoggingRepositoryDecorator(IRestauranteRepository):
    def __init__(self, repositorio: IRestauranteRepository):
        self._repo = repositorio

    def obtener_todos(self) -> list:
        logger.info("[GET] Listando todos los restaurantes")
        resultado = self._repo.obtener_todos()
        logger.info(f"[GET] Retornando {len(resultado)} restaurantes")
        return resultado

    def obtener_por_id(self, id: int):
        logger.info(f"[GET] Buscando restaurante id={id}")
        resultado = self._repo.obtener_por_id(id)
        if resultado:
            logger.info(f"[GET] Encontrado: {resultado.nombre}")
        else:
            logger.warning(f"[GET] id={id} no encontrado")
        return resultado

    def crear(self, datos) -> object:
        logger.info(f"[POST] Creando restaurante: {datos.nombre}")
        resultado = self._repo.crear(datos)
        logger.info(f"[POST] Creado con id={resultado.id}")
        return resultado

    def actualizar(self, id: int, datos) -> Optional[object]:
        logger.info(f"[PUT] Actualizando id={id}")
        resultado = self._repo.actualizar(id, datos)
        if resultado:
            logger.info(f"[PUT] Actualizado exitosamente")
        else:
            logger.warning(f"[PUT] id={id} no encontrado")
        return resultado

    def eliminar(self, id: int) -> Optional[object]:
        logger.info(f"[DELETE] Eliminando id={id}")
        resultado = self._repo.eliminar(id)
        if resultado:
            logger.info(f"[DELETE] Eliminado: {resultado.nombre}")
        else:
            logger.warning(f"[DELETE] id={id} no encontrado")
        return resultado

    def filtrar(self, categoria: Optional[str] = None, activo: Optional[bool] = None) -> list:
        logger.info(f"[FILTRO] categoria={categoria} activo={activo}")
        resultado = self._repo.filtrar(categoria, activo)
        logger.info(f"[FILTRO] {len(resultado)} resultados")
        return resultado

