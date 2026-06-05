import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from main import app
from database import get_session

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(engine):
    def get_session_override():
        with Session(engine) as session:
            yield session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()

class TestUsuarios:
    def test_registro_usuario_exitoso(self, client):
        response = client.post("/usuarios/registro", json={"nombre": "Test User", "email": "test@cato.com", "password": "Password123!"})
        assert response.status_code in (200, 201)

    def test_registro_email_duplicado(self, client):
        payload = {"nombre": "Dup", "email": "dup@cato.com", "password": "Abc12345!"}
        client.post("/usuarios/registro", json=payload)
        response = client.post("/usuarios/registro", json=payload)
        assert response.status_code in (400, 409, 422)

    def test_registro_campos_invalidos(self, client):
        response = client.post("/usuarios/registro", json={"nombre": "Solo nombre"})
        assert response.status_code == 422

    def test_login_exitoso(self, client):
        client.post("/usuarios/registro", json={"nombre": "Login Test", "email": "login@cato.com", "password": "Login123!"})
        response = client.post("/usuarios/login", json={"email": "login@cato.com", "password": "Login123!"})
        assert response.status_code == 200

    def test_login_credenciales_incorrectas(self, client):
        response = client.post("/usuarios/login", json={"email": "noexiste@cato.com", "password": "WrongPass999"})
        assert response.status_code in (401, 400, 404)

class TestRestaurantes:
    @pytest.fixture(autouse=True)
    def auth_headers(self, client):
        client.post("/usuarios/registro", json={"nombre": "Admin", "email": "admin_test@cato.com", "password": "Admin123!", "rol": "restaurante"})
        resp = client.post("/usuarios/login", json={"email": "admin_test@cato.com", "password": "Admin123!"})
        data = resp.json()
        token = data.get("access_token") or data.get("token", "")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def test_listar_restaurantes_publico(self, client):
        response = client.get("/restaurantes/")
        assert response.status_code == 200
        data = response.json()
        # Acepta lista directa o dict con clave 'restaurantes'
        assert isinstance(data, list) or "restaurantes" in data

    def test_crear_restaurante_exitoso(self, client):
        response = client.post("/restaurantes/", json={"nombre": "Restaurante Pytest", "descripcion": "Test", "direccion": "Calle 123", "categoria": "Colombiana", "calificacion": 4.5}, headers=self.headers)
        assert response.status_code in (200, 201)

    def test_obtener_restaurante_inexistente(self, client):
        response = client.get("/restaurantes/99999")
        assert response.status_code == 404

    def test_eliminar_restaurante_inexistente(self, client):
        response = client.delete("/restaurantes/99999", headers=self.headers)
        assert response.status_code in (404, 401, 403)

class TestVistas:
    def test_home_retorna_html(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_dashboard_accesible(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 200

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestHTTPCompliance:
    def test_ruta_inexistente(self, client):
        response = client.get("/ruta-absolutamente-inexistente-xyz")
        assert response.status_code == 404

    def test_content_type_json_en_api(self, client):
        response = client.get("/restaurantes/")
        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "")
