import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("CatoRecomienda.Observer")


class RestauranteObserver(ABC):
    @abstractmethod
    def on_restaurante_creado(self, restaurante) -> None:
        pass

    def on_resena_creada(self, restaurante, resena) -> None:
        # Opcional: no todos los observers necesitan reaccionar a reseñas
        pass


class AuditoriaObserver(RestauranteObserver):
    def on_restaurante_creado(self, restaurante) -> None:
        logger.info(
            f"[AUDITORIA] Nuevo restaurante: '{restaurante.nombre}' "
            f"categoria_id={restaurante.categoria_id} "
            f"promedio={restaurante.promedio_calificacion}"
        )

    def on_resena_creada(self, restaurante, resena) -> None:
        logger.info(
            f"[AUDITORIA] Nueva reseña en '{restaurante.nombre}' "
            f"puntuacion={resena.puntuacion}"
        )


class ValidadorRatingObserver(RestauranteObserver):
    def on_restaurante_creado(self, restaurante) -> None:
        rating = restaurante.promedio_calificacion
        if rating < 0.0 or rating > 5.0:
            logger.warning(f"[VALIDADOR] Rating fuera de rango: {rating}")
        else:
            logger.info(f"[VALIDADOR] Rating valido: {rating}")

    def on_resena_creada(self, restaurante, resena) -> None:
        if resena.puntuacion < 1 or resena.puntuacion > 5:
            logger.warning(f"[VALIDADOR] Puntuacion invalida: {resena.puntuacion}")
        else:
            logger.info(f"[VALIDADOR] Puntuacion valida: {resena.puntuacion}")


class EstadisticasObserver(RestauranteObserver):
    _total_restaurantes = 0
    _total_resenas = 0

    def on_restaurante_creado(self, restaurante) -> None:
        EstadisticasObserver._total_restaurantes += 1
        logger.info(
            f"[ESTADISTICAS] Total restaurantes: "
            f"{EstadisticasObserver._total_restaurantes}"
        )

    def on_resena_creada(self, restaurante, resena) -> None:
        EstadisticasObserver._total_resenas += 1
        logger.info(
            f"[ESTADISTICAS] Total reseñas: "
            f"{EstadisticasObserver._total_resenas}"
        )


class RestaurantePublicador:
    def __init__(self):
        self._observers: list = []

    def suscribir(self, observer: RestauranteObserver) -> None:
        self._observers.append(observer)

    def notificar_creacion(self, restaurante) -> None:
        for observer in self._observers:
            observer.on_restaurante_creado(restaurante)

    def notificar_resena(self, restaurante, resena) -> None:
        for observer in self._observers:
            observer.on_resena_creada(restaurante, resena)


publicador = RestaurantePublicador()
publicador.suscribir(AuditoriaObserver())
publicador.suscribir(ValidadorRatingObserver())
publicador.suscribir(EstadisticasObserver())


