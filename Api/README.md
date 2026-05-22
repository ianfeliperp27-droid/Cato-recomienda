# Cato-Recomienda 🦆

API REST + dashboard Pop-Art para descubrir restaurantes cerca de la Universidad Católica de Colombia.

## Stack

- **Backend:** FastAPI + SQLModel + SQLite (con migración prevista a PostgreSQL en producción)
- **Auth:** JWT (PyJWT) + SHA256
- **Frontend:** HTML/CSS/JS puro estilo Pop-Art con fuente Bangers
- **Patrones de diseño:** Factory Method, Adapter, Decorator, Observer, Strategy

## Estructura

```
Api/
├── FastApi.py              ← Entry point
├── database.py             ← Engine con Factory Pattern
├── .env                    ← DATABASE_URL, HTML_DIR, SECRET_KEY
├── startup.sh              ← Gunicorn para Azure
├── requirements.txt
├── models/                 ← SQLModel tables y DTOs
├── repositories/           ← Acceso a datos
├── routes/                 ← Endpoints HTTP
├── services/               ← Lógica auxiliar (auth/JWT)
├── patterns/               ← Los 5 patrones de diseño
└── static/                 ← Dashboard HTML
```

## Correr en local

```bash
cd Api
pip install -r requirements.txt
uvicorn FastApi:app --reload
```

Visita http://127.0.0.1:8000

## Endpoints clave

### Públicos
- `GET /` — Dashboard
- `GET /health` — Health check
- `GET /restaurantes/` — Lista (acepta `?categoria=`, `?activo=`, `?rating_min=`, `?ordenar=rating`)
- `GET /restaurantes/{id}` — Detalle
- `GET /restaurantes/categorias` — Lista de categorías
- `GET /restaurantes/{id}/resenas` — Reseñas del restaurante

### Auth
- `POST /usuarios/registro` — `{ nombre, email, password }` → `{ usuario, token }`
- `POST /usuarios/login` — `{ email, password }` → `{ usuario, token }`

### Protegidos (header `Authorization: Bearer <token>`)
- `POST /restaurantes/` — Crear restaurante
- `PUT /restaurantes/{id}` — Editar
- `DELETE /restaurantes/{id}` — Eliminar
- `POST /restaurantes/{id}/resenas` — `{ puntuacion: 1-5, comentario }` (recalcula promedio automáticamente)
- `POST /restaurantes/categorias` — Nueva categoría

## Deploy a Azure App Service

### Opción A: subir solo el contenido de `Api/` a wwwroot

1. En el portal Azure, configurar:
   - **Stack:** Python 3.11
   - **Startup command:** `bash startup.sh`
   - **Variables de entorno:**
     - `DATABASE_URL=sqlite:///restaurantes.db`
     - `SECRET_KEY=<algo-largo-y-aleatorio>`
     - `HTML_DIR=./static`
     - `ENTORNO=desarrollo` (o `produccion` cuando se migre a PG)

2. Subir solo el contenido de `Api/` (no la carpeta completa) a la raíz del repo de deploy.

### Opción B: subir el repo completo con `Api/` adentro

`startup.sh` detecta automáticamente si existe `Api/` y entra ahí. No requiere cambios.

### Comando manual de deploy via ZIP

```bash
cd Api
zip -r ../deploy.zip . -x "*.db" "__pycache__/*"
az webapp deployment source config-zip \
  -g catorecomienda2 \
  -n catorecomienda \
  --src ../deploy.zip
```

## Patrones de diseño aplicados

| Patrón | Ubicación | Función |
|--------|-----------|---------|
| **Factory Method** | `patterns/factory.py` | Crea engine SQLite o PostgreSQL según `ENTORNO` |
| **Adapter** | `patterns/adapter.py` | Define `IRestauranteRepository` como interfaz |
| **Decorator** | `patterns/decorator.py` | `LoggingRepositoryDecorator` envuelve el repo |
| **Observer** | `patterns/observer.py` | Notifica eventos (crear restaurante, nueva reseña) |
| **Strategy** | `patterns/strategy.py` | Pipeline de filtros intercambiables |

Ver el documento `Taller_Patrones_Cato-Recomienda.docx` para detalles, diagramas UML y análisis SOLID.

## Equipo

- Daniel Fernando Blanco Sánchez — 67001762
- Ian Felipe Ramos Páez — 67001667
- Juan Pablo Pérez Acosta — 67001752
- Leonardo Jiménez Castiblanco — 67001662

Docente: Diego Iván Oliveros Acosta
Universidad Católica de Colombia — 2026-1
