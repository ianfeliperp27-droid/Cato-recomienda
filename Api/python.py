
 
# Si queremos cambiar a Postgres en produccion hay que:
#  1. Editar este archivo
#  2. Cambiar el connect_args
#  3. Posiblemente romper el modo desarrollo
3.4 Despues (con Factory Method)
# patterns/factory.py - Con Factory Method
class DatabaseFactory(ABC):
        @abstractmethod
            def crear_engine(self): pass
             
             class SQLiteFactory(DatabaseFactory):
                    def crear_engine(self):
                                url = os.getenv("DATABASE_URL", "sqlite:///restaurantes.db")
                                        return create_engine(url, connect_args={"check_same_thread": False})
                                         
                                         class PostgreSQLFactory(DatabaseFactory):
                                                def crear_engine(self):
                                                            return create_engine(os.getenv("DATABASE_URL"))
                                                             
                                                             def get_database_factory() -> DatabaseFactory:
                                                                    if os.getenv("ENTORNO") == "produccion":
                                                                                return PostgreSQLFactory()
                                                                                    return SQLiteFactory()
                                                                                     
                                                                                     # database.py:
                                                                                     engine = get_database_factory().crear_engine()
                                                                                