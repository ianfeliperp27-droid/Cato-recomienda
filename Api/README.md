# 🍽️ Cato-Recomienda

API REST + dashboard para descubrir y recomendar restaurantes cerca de la Universidad Católica de Colombia.

**Versión final 2026-1** — Arquitectura MVC, SOLID, patrones GoF, pruebas automatizadas y CI/CD.

> **Equipo:**  
> Daniel Fernando Blanco Sánchez (67001762) · Ian Felipe Ramos Páez (67001667)  
> Juan Pablo Pérez Acosta (67001752) · Leonardo Jiménez Castiblanco (67001662)  
> **Docente:** Andrés Torres — Universidad Católica de Colombia · 2026-1  
> **URL pública:** https://catorecomienda.azurewebsites.net

---

## Stack tecnológico

- **Backend:** FastAPI + SQLModel + SQLite
- **Auth:** JWT (PyJWT) + PBKDF2-HMAC-SHA256 con salt
- **Frontend:** HTML/CSS/JS estático con diseño Pop-Art
- **Pruebas:** pytest + httpx (14 tests de integración)
- **CI/CD:** GitHub Actions
- **Despliegue:** Azure App Service

---

## 🏗️ Arquitectura del Proyecto

```
Api/
├── main.py                  # Punto de entrada — registra routers
├── database.py              # Engine SQLite con Factory Pattern
├── .env                     # Variables de entorno (NO subir al repo)
├── .env.example             # Plantilla pública
├── .gitignore
├── startup.sh               # Gunicorn para Azure
├── requirements.txt
├── models/                  # MODELOS — esquemas SQLModel + Pydantic
│   ├── restaurante.py
│   └── usuario.py
├── repositories/            # LÓGICA DE NEGOCIO — toda consulta SQL aquí (SRP)
│   ├── restaurante.py
│   ├── categoria.py
│   ├── resena.py
│   └── usuario.py
├── routes/                  # CONTROLADORES — endpoints FastAPI
│   ├── restaurantes.py
│   ├── usuarios.py
│   └── vistas.py
├── services/
│   ├── auth.py              # JWT + PBKDF2 hashing
│   └── uploads.py
├── patterns/                # Patrones GoF
│   ├── factory.py
│   ├── observer.py
│   ├── strategy.py
│   ├── adapter.py
│   └── decorator.py
├── static/
│   └── dashboard.html
├── tests/
│   ├── conftest.py
│   └── test_main.py
└── .github/
    └── workflows/
        └── ci-cd.yml
```

---

## 📋 Requisitos Previos

- Python 3.11+, pip, Git

```bash
python --version
pip --version
git --version
```

---

## 🚀 Instalación Local

```bash
git clone https://github.com/ianfeliperp27-droid/Cato-recomienda.git
cd Cato-recomienda
git checkout main
cd Api
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# .\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

---

## ⚙️ Variables de Entorno

Crear `.env` dentro de `Api/`:

```env
DATABASE_URL=sqlite:///restaurantes.db
HTML_DIR=./static
SECRET_KEY=cato-recomienda-secret-2026
ENTORNO=desarrollo
```

> ⚠️ Nunca subir `.env` al repo. En producción generar SECRET_KEY con:
> `python -c "import secrets; print(secrets.token_urlsafe(64))"`

---

## ▶️ Ejecución de la Aplicación

```bash
# Desarrollo
uvicorn main:app --reload --port 8000

# Producción
gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 main:app
```

- App: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 🔌 Endpoints

### Públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Dashboard principal |
| GET | `/health` | Estado del servicio |
| GET | `/restaurantes/` | Listar (filtros: `?categoria=`, `?rating_min=`, `?ordenar=rating`) |
| GET | `/restaurantes/{id}` | Detalle |
| GET | `/restaurantes/categorias` | Categorías |
| GET | `/restaurantes/{id}/resenas` | Reseñas |

### Autenticación

| Método | Ruta | Body | Devuelve |
|--------|------|------|----------|
| POST | `/usuarios/registro` | `{ nombre, email, password }` | `{ usuario, token }` |
| POST | `/usuarios/login` | `{ email, password }` | `{ usuario, token }` |
| POST | `/usuarios/forgot-password` | `{ email }` | `{ mensaje }` |
| POST | `/usuarios/reset-password` | `{ token, nueva_password }` | `{ ok }` |

### Protegidos (`Authorization: Bearer <token>`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/restaurantes/` | Crear restaurante |
| PUT | `/restaurantes/{id}` | Editar |
| DELETE | `/restaurantes/{id}` | Eliminar |
| POST | `/restaurantes/{id}/resenas` | Crear reseña |
| POST | `/restaurantes/categorias` | Nueva categoría |

---

## 🧪 Ejecución de Pruebas

```bash
cd Api
pip install pytest httpx
pytest tests/ -v
```

**Resultado esperado: 14 passed.**

```
TestUsuarios::test_registro_usuario_exitoso        PASSED
TestUsuarios::test_registro_email_duplicado        PASSED
TestUsuarios::test_registro_campos_invalidos       PASSED
TestUsuarios::test_login_exitoso                   PASSED
TestUsuarios::test_login_credenciales_incorrectas  PASSED
TestRestaurantes::test_listar_restaurantes_publico PASSED
TestRestaurantes::test_crear_restaurante_exitoso   PASSED
TestRestaurantes::test_obtener_restaurante_inexistente PASSED
TestRestaurantes::test_eliminar_restaurante_inexistente PASSED
TestVistas::test_home_retorna_html                 PASSED
TestVistas::test_dashboard_accesible               PASSED
TestVistas::test_health_check                      PASSED
TestHTTPCompliance::test_ruta_inexistente          PASSED
TestHTTPCompliance::test_content_type_json_en_api  PASSED
14 passed in 1.54s
```

---

## 🔄 Pipeline CI/CD

`.github/workflows/ci-cd.yml` ejecuta en cada push a `main` o `APIs`:

1. Instala dependencias desde `Api/requirements.txt`
2. Corre pytest con SQLite en memoria
3. **Bloquea el deploy** si algún test falla (`needs: test`)
4. Dispara deploy automático solo si todos los tests pasan

---

## ☁️ Despliegue en Azure

### Variables requeridas en Azure App Service

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | `sqlite:///restaurantes.db` |
| `HTML_DIR` | `./static` |
| `SECRET_KEY` | cadena larga y aleatoria |
| `ENTORNO` | `produccion` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

### Startup Command

```
gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 main:app
```

### Deploy manual con ZIP

```bash
cd Api
zip -r ../deploy.zip . -x "*.db" "__pycache__/*" ".env" ".git/*"
az webapp deployment source config-zip -g catorecomienda2 -n catorecomienda --src ../deploy.zip
```

---

## 🎨 Patrones de Diseño GoF

| Patrón | Ubicación | Función |
|--------|-----------|---------|
| Factory Method | `patterns/factory.py` | Crea engine SQLite o PostgreSQL según `ENTORNO` |
| Adapter | `patterns/adapter.py` | Define `IRestauranteRepository` como interfaz (DIP) |
| Decorator | `patterns/decorator.py` | `LoggingRepositoryDecorator` envuelve el repo (OCP) |
| Observer | `patterns/observer.py` | Notifica eventos: crear restaurante, nueva reseña |
| Strategy | `patterns/strategy.py` | Pipeline de filtros intercambiables |

---

## ✅ SOLID aplicado

- **SRP:** rutas → repos → modelos. Las rutas no tienen `session.exec()` directo.
- **OCP:** nuevo filtro = nueva clase en `strategy.py`, sin modificar el resto.
- **LSP:** `LoggingRepositoryDecorator` sustituible donde se espera `IRestauranteRepository`.
- **ISP:** `IRestauranteRepository` solo expone métodos que las rutas realmente usan.
- **DIP:** las rutas dependen de la interfaz, no de la implementación concreta.

---

## 🎨 Diseño Visual

### Paleta de Colores

| Rol | Hex | Contraste WCAG |
|-----|-----|----------------|
| Primario (naranja) | `#FF6B35` | ≥ 4.5:1 sobre blanco |
| Secundario (azul oscuro) | `#1A1A2E` | ≥ 7:1 sobre blanco |
| Acento (dorado) | `#F5A623` | ≥ 3:1 sobre oscuro |
| Fondo | `#FFFFFF` | — |
| Texto | `#2C2C2C` | ≥ 7:1 sobre blanco |

### Patrón F de Lectura

- **F-top:** Logo + navegación + barra de búsqueda
- **Segunda franja:** Filtros de categoría y calificación
- **F-stem (izquierda):** Tarjetas con nombre y calificación en la parte superior
- **Zona derecha:** Información complementaria y filtros avanzados
