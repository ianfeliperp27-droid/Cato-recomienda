from sqlmodel import Session, select
from models.usuario import Usuario, UsuarioCreate
from services.auth import hash_password, verify_password, needs_rehash


class UsuarioRepository:
    """
    Patron Repositorio. Toda consulta SQL sobre Usuario vive aqui,
    no en las rutas. Las rutas solo orquestan.
    """

    def __init__(self, session: Session):
        self.session = session

    # ----- Lecturas -----

    def obtener_por_email(self, email: str):
        return self.session.exec(
            select(Usuario).where(Usuario.email == email)
        ).first()

    def obtener_por_id(self, id: int):
        return self.session.get(Usuario, id)

    # ----- Escrituras -----

    def crear(self, datos: UsuarioCreate) -> Usuario:
        usuario = Usuario(
            nombre=datos.nombre,
            email=datos.email,
            password=hash_password(datos.password),
            rol=datos.rol,
        )
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def verificar_password(self, email: str, password: str):
        """
        Devuelve el Usuario si las credenciales son validas, None en caso
        contrario. Si el hash almacenado esta en el formato viejo (SHA256
        sin sal), lo migra automaticamente al nuevo formato PBKDF2.
        """
        usuario = self.obtener_por_email(email)
        if not usuario:
            return None
        if not verify_password(password, usuario.password):
            return None
        if needs_rehash(usuario.password):
            usuario.password = hash_password(password)
            self.session.add(usuario)
            self.session.commit()
            self.session.refresh(usuario)
        return usuario

    def actualizar_password(self, usuario: Usuario, nueva: str) -> Usuario:
        usuario.password = hash_password(nueva)
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

