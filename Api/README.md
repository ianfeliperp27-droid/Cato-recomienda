# Cato-Recomienda 🦆

API REST + dashboard Pop-Art para descubrir restaurantes cerca de la Universidad Católica de Colombia.

**Versión 4.1** — Refactor con auditoría SOLID, hashing seguro, recuperación de contraseña.

## Stack

- **Backend:** FastAPI + SQLModel + SQLite (con migración prevista a PostgreSQL en producción)
- **Auth:** JWT (PyJWT) + PBKDF2-HMAC-SHA256 con salt (con compatibilidad hacia atrás para usuarios v1 que tenían SHA256 plano)
- **Frontend:** HTML/CSS/JS puro estilo Pop-Art con fuente Bangers
- **Patrones de diseño:** Factory Method, Adapter, Decorator, Observer, Strategy
- **Repositorios:** Restaurante, Categoría, Reseña, Usuario

## Cambios respecto a v4.0

- **SRP estricto:** las rutas ya no contienen `session.exec()`/SQL directo. Se crearon `repositories/categoria.py` y `repositories/resena.py`.
- **Código muerto eliminado:** `static/login.html` huérfano, método `filtrar()` en `RestauranteRepository`, `OrdenarPorNombre` en strategy, ruta `/login`, dependencia `requests` no usada, `FastApi.gitignore` mal formado.
- **Hashing seguro:** PBKDF2 con salt aleatorio reemplaza al SHA256 plano. Los hashes viejos de la BD se migran automáticamente la siguiente vez que el usuario hace login.
- **Lifespan moderno:** `FastApi.py` usa `lifespan` en lugar de `@app.on_event("startup")` (deprecated desde FastAPI 0.110).
- **Flujo "olvidé contraseña":** endpoints `/usuarios/forgot-password` y `/usuarios/reset-password` con token JWT de 30 min.
- **UX:** dashboard con link "¿Olvidaste tu contraseña?", sub-vistas de recuperación y reset, campo de confirmar contraseña con validación en vivo, mejor feedback de errores.
- **`.gitignore` real** (no el script shell que lo crea) + `.env.example` como plantilla pública.

## Estructura

```
Api/
├── FastApi.py              ← Entry point (con lifespan)
├── database.py             ← Engine con Factory Pattern
├── .env                    ← DATABASE_URL, HTML_DIR, SECRET_KEY  (NO subir)
├── .env.example            ← Plantilla pública
├── .gitignore              ← Excluye .env, *.db, __pycache__
├── startup.sh              ← Gunicorn para Azure
├── requirements.txt
├── models/                 ← SQLModel tables y DTOs
│   ├── restaurante.py
│   └── usuario.py
├── repositories/           ← Toda consulta SQL vive aquí
│   ├── restaurante.py
│   ├── categoria.py        ← (nuevo)
│   ├── resena.py           ← (nuevo)
│   └── usuario.py
├── routes/                 ← Endpoints HTTP (sin SQL directo)
│   ├── restaurantes.py
│   ├── usuarios.py         ← + forgot/reset
│   └── vistas.py
├── services/
│   └── auth.py             ← JWT + hashing PBKDF2 (con fallback legacy)
├── patterns/               ← Los 5 patrones de diseño
│   ├── adapter.py
│   ├── decorator.py
│   ├── factory.py
│   ├── observer.py
│   └── strategy.py
└── static/
    └── dashboard.html      ← Pop-Art con auth integrada
```

## Correr en local

```bash
cd Api
cp .env.example .env       # primera vez
pip install -r requirements.txt
uvicorn FastApi:app --reload
```

Visita http://127.0.0.1:8000

## Endpoints

### Públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Dashboard |
| GET | `/health` | Health check |
| GET | `/restaurantes/` | Lista (acepta `?categoria=`, `?activo=`, `?rating_min=`, `?ordenar=rating`) |
| GET | `/restaurantes/{id}` | Detalle |
| GET | `/restaurantes/categorias` | Lista de categorías |
| GET | `/restaurantes/{id}/resenas` | Reseñas del restaurante |

### Autenticación

| Método | Ruta | Body | Devuelve |
|--------|------|------|----------|
| POST | `/usuarios/registro` | `{ nombre, email, password }` | `{ usuario, token }` |
| POST | `/usuarios/login` | `{ email, password }` | `{ usuario, token }` |
| POST | `/usuarios/forgot-password` | `{ email }` | `{ mensaje, debug_token? }` |
| POST | `/usuarios/reset-password` | `{ token, nueva_password }` | `{ ok }` |

> **Nota:** `forgot-password` devuelve siempre el mismo mensaje (no revela si el email existe). En modo `ENTORNO=desarrollo` también devuelve `debug_token` para poder probar el flujo sin SMTP.

### Protegidos (header `Authorization: Bearer <token>`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/restaurantes/` | Crear restaurante |
| PUT | `/restaurantes/{id}` | Editar |
| DELETE | `/restaurantes/{id}` | Eliminar |
| POST | `/restaurantes/{id}/resenas` | Crear reseña (recalcula promedio) |
| POST | `/restaurantes/categorias` | Nueva categoría |

## Deploy a Azure App Service

### Variables de entorno requeridas

| Variable | Desarrollo | Producción |
|----------|-----------|------------|
| `DATABASE_URL` | `sqlite:///restaurantes.db` | `postgresql://user:pass@host/db` |
| `HTML_DIR` | `./static` | `./static` |
| `SECRET_KEY` | cualquiera | **largo y aleatorio** — generar con `python -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `ENTORNO` | `desarrollo` | `produccion` |

⚠️ En `produccion`, el endpoint de forgot-password **no** devuelve `debug_token` en la respuesta. Conectar un servicio de correo real para enviarlo.

### Comando de deploy

```bash
cd Api
zip -r ../deploy.zip . -x "*.db" "__pycache__/*" ".env" ".git/*"
az webapp deployment source config-zip \
  -g catorecomienda2 \
  -n catorecomienda \
  --src ../deploy.zip
```

## Patrones de diseño aplicados

| Patrón | Ubicación | Función |
|--------|-----------|---------|
| **Factory Method** | `patterns/factory.py` | Crea engine SQLite o PostgreSQL según `ENTORNO` |
| **Adapter** | `patterns/adapter.py` | Define `IRestauranteRepository` como interfaz (DIP) |
| **Decorator** | `patterns/decorator.py` | `LoggingRepositoryDecorator` envuelve el repo (OCP) |
| **Observer** | `patterns/observer.py` | Notifica eventos (crear restaurante, nueva reseña) |
| **Strategy** | `patterns/strategy.py` | Pipeline de filtros intercambiables |

## SOLID aplicado en esta versión

- **SRP:** rutas → repos → modelos. Cada capa hace una sola cosa. Las rutas ya no tienen `session.exec()`.
- **OCP:** agregar un nuevo filtro = crear una clase nueva en `strategy.py`; no se modifica el resto.
- **LSP:** `LoggingRepositoryDecorator` es sustituible donde se espera `IRestauranteRepository`.
- **ISP:** la interfaz `IRestauranteRepository` solo expone los métodos que las rutas realmente usan; `filtrar()` se eliminó cuando dejó de usarse.
- **DIP:** las rutas dependen de la interfaz `IRestauranteRepository` (vía `Depends`), no de la implementación concreta.

## Equipo

- Daniel Fernando Blanco Sánchez — 67001762
- Ian Felipe Ramos Páez — 67001667
- Juan Pablo Pérez Acosta — 67001752
- Leonardo Jiménez Castiblanco — 67001662

Docente: Andrés Torres — Universidad Católica de Colombia — 2026-1
