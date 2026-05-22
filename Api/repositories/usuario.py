from sqlmodel import Session, select
from models.usuario import Usuario, UsuarioCreate
import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class UsuarioRepository:
    def __init__(self, session: Session):
        self.session = session

    def obtener_por_email(self, email: str):
        return self.session.exec(select(Usuario).where(Usuario.email == email)).first()

    def crear(self, datos: UsuarioCreate):
        usuario = Usuario(
            nombre=datos.nombre,
            email=datos.email,
            password=hash_password(datos.password),
            rol=datos.rol
        )
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def verificar_password(self, email: str, password: str):
        usuario = self.obtener_por_email(email)
        if not usuario:
            return None
        if usuario.password == hash_password(password):
            return usuario
        return None

