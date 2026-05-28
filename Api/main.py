"""
main.py — Cato-Recomienda v3.1 · Estructuras: Dict · Pila · Lista · Heap
Universidad Católica de Colombia · Team Data Structure

Cambios sobre la versión anterior:
  ① Instancias globales: DiccionarioRestaurantes, PilaHistorial,
      ListaCategorias, HeapRecomendaciones.
  ② lifespan: carga automática desde SQLite al arrancar.
  ③ Hook: actualizar_estructuras_nuevo_restaurante() para sincronía real.
  ④ Router /estructuras con 4 endpoints de evaluación académica.
  ⑤ Sirve estructuras.html desde /static/.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, APIRouter, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from dotenv import load_dotenv

load_dotenv()

from database import crear_tablas, engine
from repositories.categoria import CategoriaRepository
from repositories.restaurante import RestauranteRepository
from routes.vistas import router as vistas_router
from routes.restaurantes import router as restaurantes_router
from routes.usuarios import router as usuarios_router

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTAR LAS CUATRO ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
from estructuras_v2 import (
    DiccionarioRestaurantes,
    PilaHistorial,
    ListaCategorias,
    HeapRecomendaciones,
)

# ══════════════════════════════════════════════════════════════════════════════
# INSTANCIAS GLOBALES EN MEMORIA RAM
#
# TEORÍA — ¿por qué globales?
# Estas estructuras viven en el proceso Python durante toda la vida del
# servidor. Al recibir una petición HTTP cualquier módulo puede importarlas
# directamente sin abrir una conexión a SQLite → latencia ≈ O(1).
# Son el "caché de aplicación" de Cato-Recomienda.
# ══════════════════════════════════════════════════════════════════════════════
diccionario_restaurantes = DiccionarioRestaurantes()
"""Hash map {id → datos}: búsqueda O(1) para cualquier restaurante."""

pila_historial = PilaHistorial(capacidad_max=200)
"""Pila LIFO del historial de acciones de la API."""

lista_categorias = ListaCategorias()
"""Lista enlazada de restaurantes agrupados por categoría."""

heap_recomendaciones = HeapRecomendaciones()
"""Max-Heap de restaurantes ordenados por calificación descendente."""


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES DE CARGA
# ══════════════════════════════════════════════════════════════════════════════

def _normalizar_restaurante(r, categoria: str = "General") -> dict:
    """Convierte un ORM SQLModel en el dict estándar usado por las estructuras."""
    return {
        "id":           r.id,
        "nombre":       r.nombre,
        "categoria":    categoria,
        "descripcion":  r.descripcion or "",
        "direccion":    r.direccion or "",
        "ciudad":       r.ciudad or "",
        "calificacion": r.promedio_calificacion,
        "precio_prom":  r.precio_prom or "—",
        "activo":       r.activo,
        "foto":         r.foto or "",
    }


def _cargar_estructuras_desde_bd(session: Session) -> None:
    """
    Lee todos los registros de SQLite e inyecta cada restaurante y usuario
    en las cuatro estructuras de datos en RAM.

    Se llama UNA SOLA VEZ durante el startup del servidor.
    Complejidad total: O(n) para dict/pila/lista + O(n) para heapify → O(n).
    """
    from models.restaurante import Restaurante, Categoria
    from models.usuario import Usuario

    # ── Cargar restaurantes ──────────────────────────────────────────────────
    restaurantes_orm = session.exec(select(Restaurante)).all()
    restaurantes_normalizados = []

    for r in restaurantes_orm:
        # Resolver categoría
        nombre_cat = "General"
        if r.categoria_rel:
            nombre_cat = r.categoria_rel.nombre
        elif r.categoria_id:
            cat = session.get(Categoria, r.categoria_id)
            if cat:
                nombre_cat = cat.nombre

        dato = _normalizar_restaurante(r, nombre_cat)

        # 1. Diccionario → O(1) por inserción
        diccionario_restaurantes.insertar_restaurante(r.id, dato)

        # 2. Lista enlazada → O(1) insertar al frente (orden más reciente primero)
        lista_categorias.agregar_al_frente(nombre_cat, dato)

        # 3. Heap → se precarga aquí, heapify se llama después (O(n) total)
        restaurantes_normalizados.append(dato)

    # Construir el heap de una sola vez → O(n) con heapify
    heap_recomendaciones.reconstruir(restaurantes_normalizados)

    # ── Cargar usuarios ──────────────────────────────────────────────────────
    usuarios_orm = session.exec(select(Usuario)).all()
    for u in usuarios_orm:
        diccionario_restaurantes.insertar_usuario(u.id, {
            "id":     u.id,
            "nombre": u.nombre,
            "email":  u.email,
            "rol":    u.rol,
            "activo": u.activo,
        })

    pila_historial.apilar(
        "startup",
        f"{len(restaurantes_orm)} restaurantes y {len(usuarios_orm)} usuarios "
        f"cargados en estructuras de datos.",
    )
    print(
        f"[Cato-Recomienda] Estructuras inicializadas: "
        f"{len(restaurantes_orm)} restaurantes · "
        f"{len(usuarios_orm)} usuarios."
    )


def actualizar_estructuras_nuevo_restaurante(restaurante, categoria: str = "General") -> None:
    """
    Sincroniza las cuatro estructuras cuando se crea un nuevo restaurante.
    Llamar desde routes/restaurantes.py tras la persistencia en BD.

    Ejemplo de uso en routes/restaurantes.py:
    ─────────────────────────────────────────
        from main import actualizar_estructuras_nuevo_restaurante

        # dentro de crear() / crear_con_imagen():
        nuevo = _repo(session).crear(datos)
        actualizar_estructuras_nuevo_restaurante(nuevo, nombre_categoria)
    ─────────────────────────────────────────
    """
    dato = _normalizar_restaurante(restaurante, categoria)

    diccionario_restaurantes.insertar_restaurante(restaurante.id, dato)
    lista_categorias.agregar_al_frente(categoria, dato)
    heap_recomendaciones.insertar(
        restaurante.id,
        restaurante.nombre,
        restaurante.promedio_calificacion,
        dato,
    )
    pila_historial.apilar(
        "nuevo_restaurante",
        f"Restaurante '{restaurante.nombre}' (id={restaurante.id}) "
        f"insertado en estructuras RAM.",
    )


# ══════════════════════════════════════════════════════════════════════════════
# LIFESPAN — reemplaza @app.on_event('startup')
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIAS_SEED = ["Hamburguesas", "Corrientazo", "Sushi", "Pizza", "Tacos"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()
    with Session(engine) as session:
        CategoriaRepository(session).seed(CATEGORIAS_SEED)
        RestauranteRepository(session).seed()
        _cargar_estructuras_desde_bd(session)

    yield


# ══════════════════════════════════════════════════════════════════════════════
# APLICACIÓN FASTAPI
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Cato-Recomienda API",
    description="Estructuras de Datos: Diccionario · Pila · Lista · Heap",
    version="3.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(vistas_router)
app.include_router(restaurantes_router)
app.include_router(usuarios_router)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER /estructuras — Endpoints de Evaluación Académica
# ══════════════════════════════════════════════════════════════════════════════

router_est = APIRouter(prefix="/estructuras", tags=["Estructuras de Datos"])


@router_est.get("/diccionario", summary="Estado del Diccionario (Hash Map)")
def get_diccionario(
    tipo: str = Query("restaurantes", description="'restaurantes' o 'usuarios'"),
):
    """
    Retorna el mapa completo clave → valor del diccionario global.

    TEORÍA:
    • Python dict = tabla hash con open addressing.
    • Búsqueda y escritura O(1) promedio — ideal para índice de acceso rápido.
    • La clave es el ID entero del restaurante/usuario.
    """
    pila_historial.apilar("consulta_diccionario", f"tipo={tipo}")
    if tipo == "usuarios":
        return {
            "estructura": "Diccionario — Hash Map",
            "tipo": "usuarios",
            **diccionario_restaurantes.estadisticas(),
            "datos": diccionario_restaurantes.snapshot_usuarios(),
        }
    return {
        "estructura": "Diccionario — Hash Map",
        "tipo": "restaurantes",
        **diccionario_restaurantes.estadisticas(),
        "datos": diccionario_restaurantes.snapshot_restaurantes(),
        "nota_teorica": (
            "Hash Map: clave = id (entero), valor = dict con datos del restaurante. "
            "Búsqueda O(1). Python dict maneja colisiones con open addressing "
            "y mantiene factor de carga < 2/3."
        ),
    }


@router_est.get("/pila/historial", summary="Estado de la Pila LIFO de historial")
def get_pila():
    """
    Retorna el historial de acciones de la API en orden LIFO.

    TEORÍA:
    • Pila LIFO: el índice 0 del resultado = tope (acción más reciente).
    • push O(1), pop O(1) sobre arreglo dinámico (Python list).
    • La capacidad máxima previene desbordamiento de RAM.
    """
    return {
        "estructura": "Pila — Stack LIFO",
        **pila_historial.snapshot(),
    }


@router_est.post("/pila/desapilar", summary="Desapilar (pop) del historial")
def desapilar():
    """
    Retira el elemento del tope de la pila (pop). O(1).
    Simula la operación undo sobre el historial de acciones.
    """
    elemento = pila_historial.desapilar()
    if not elemento:
        return {"ok": False, "mensaje": "La pila está vacía."}
    return {
        "ok": True,
        "elemento_retirado": elemento,
        "nuevo_tamanio": pila_historial.tamanio(),
    }


@router_est.get("/lista/datos", summary="Estado de la Lista Enlazada por categorías")
def get_lista(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría específica"),
    ordenar: bool = Query(False, description="Ordenar todos por calificación descendente"),
):
    """
    Retorna los elementos almacenados en la lista enlazada.

    TEORÍA:
    • Lista enlazada: nodos con puntero al siguiente. Sin índice directo.
    • Recorrido O(n) por categoría; inserción al frente O(1).
    • Cada categoría es una cadena de nodos independiente.
    """
    pila_historial.apilar("consulta_lista", f"categoria={categoria}")
    if categoria:
        datos = lista_categorias.obtener_por_categoria(categoria)
        return {
            "estructura": "Lista Enlazada",
            "categoria": categoria,
            "total": len(datos),
            "datos": datos,
        }
    if ordenar:
        datos = lista_categorias.todos_ordenados_por_calificacion()
        return {
            "estructura": "Lista Enlazada",
            "modo": "todos ordenados por calificación",
            "total": len(datos),
            "datos": datos,
        }
    return {
        "estructura": "Lista Enlazada",
        **lista_categorias.snapshot(),
    }


@router_est.get("/heap/prioridad", summary="Estado del Max-Heap de recomendaciones")
def get_heap(k: int = Query(5, ge=1, le=50, description="Top-K a extraer")):
    """
    Retorna el árbol binario del heap como arreglo y el Top-K.

    TEORÍA:
    • Max-Heap: raíz (índice 0) = restaurante con mayor calificación.
    • Para nodo i: padre = (i-1)//2, hijo_izq = 2i+1, hijo_der = 2i+2.
    • heappush/heappop O(log n). Top-K O(k log n).
    • Python heapq = min-heap; usamos valores negados para max-heap.
    """
    pila_historial.apilar("consulta_heap", f"top_k={k}")
    snap = heap_recomendaciones.snapshot()
    snap["top_k_solicitado"] = heap_recomendaciones.top_k(k)
    return {
        "estructura": "Max-Heap (Binary Heap)",
        **snap,
    }


@router_est.get("/resumen", summary="Resumen global de las cuatro estructuras")
def get_resumen():
    """Vista rápida del estado de todas las estructuras en RAM."""
    return {
        "diccionario": {
            "total_restaurantes": diccionario_restaurantes.total_restaurantes(),
            "total_usuarios":     diccionario_restaurantes.total_usuarios(),
        },
        "pila": {
            "tamanio":  pila_historial.tamanio(),
            "tope":     pila_historial.ver_tope(),
        },
        "lista": {
            "total":      lista_categorias.total(),
            "categorias": lista_categorias.categorias_disponibles(),
        },
        "heap": {
            "tamanio": heap_recomendaciones.tamanio(),
            "maximo":  heap_recomendaciones.ver_maximo(),
        },
    }


app.include_router(router_est)

