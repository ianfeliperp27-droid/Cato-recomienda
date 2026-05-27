from sqlmodel import Session, select
from typing import List
from models.restaurante import Resena, ResenaCreate, Restaurante # <-- Verificar que use n si el modelo se llama Resena

class ResenaRepository: # <-- Cambiado de ReseñaRepository a ResenaRepository
    """
    Patron Repositorio para Reseña. Encapsula tambien el recalculo
    del promedio del restaurante, que antes vivia en la ruta.
    """

    def __init__(self, session: Session):
        self.session = session

    def listar_por_restaurante(self, restaurante_id: int) -> List[Resena]: # <-- Resena con n
        return self.session.exec(
            select(Resena).where(Resena.restaurante_id == restaurante_id) # <-- Resena con n
        ).all()

    def crear(
        self,
        restaurante: Restaurante,
        usuario_id: int,
        datos: ResenaCreate, # <-- ResenaCreate con n
    ) -> Resena: # <-- Resena con n
        resena = Resena( # <-- Resena con n
            usuario_id=usuario_id,
            restaurante_id=restaurante.id,
            puntuacion=datos.puntuacion,
            comentario=datos.comentario,
        )
        self.session.add(resena)
        self.session.commit()
        self.session.refresh(resena)
        return resena

    def recalcular_promedio(self, restaurante: Restaurante) -> float:
        todas = self.listar_por_restaurante(restaurante.id)
        if not todas:
            restaurante.promedio_calificacion = 0.0
        else:
            promedio = sum(r.puntuacion for r in todas) / len(todas)
            restaurante.promedio_calificacion = round(promedio, 2)
        self.session.add(restaurante)
        self.session.commit()
        self.session.refresh(restaurante) # <-- Aquí terminaba tu fragmento
        return restaurante.promedio_calificacion