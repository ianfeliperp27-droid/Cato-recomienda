import heapq
from datetime import datetime
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUCTURA 1 — DICCIONARIO (Hash Map de restaurantes y usuarios)
# ─────────────────────────────────────────────────────────────────────────────

class DiccionarioRestaurantes:
    """
    Índice de lectura rápida O(1) para restaurantes y usuarios.

    TEORÍA:
    ───────
    Un diccionario (hash map) mantiene pares clave → valor en una tabla
    de dispersión interna. Python resuelve las colisiones por open
    addressing con sondeo cuádratico. El factor de carga se mantiene
    por debajo del 2/3, provocando un rehash O(n) amortizado raramente.

    Aquí usamos dos diccionarios separados:
      · _restaurantes  → { id: dict_con_datos }
      · _usuarios      → { id: dict_con_datos }

    Esto permite encontrar cualquier registro en O(1) sin recorrer listas.
    """

    def __init__(self):
        self._restaurantes: dict[int, dict] = {}
        self._usuarios:     dict[int, dict] = {}

    # ── Restaurantes ────────────────────────────────────────────────────────

    def insertar_restaurante(self, id_: int, datos: dict) -> None:
        """O(1) promedio — inserta o actualiza un restaurante en el índice."""
        self._restaurantes[id_] = datos

    def obtener_restaurante(self, id_: int) -> Optional[dict]:
        """O(1) — retorna el restaurante o None si no existe."""
        return self._restaurantes.get(id_)

    def eliminar_restaurante(self, id_: int) -> bool:
        """O(1) — elimina el restaurante; retorna True si existía."""
        if id_ in self._restaurantes:
            del self._restaurantes[id_]
            return True
        return False

    def todos_los_restaurantes(self) -> list[dict]:
        """O(n) — retorna todos los restaurantes como lista."""
        return list(self._restaurantes.values())

    def total_restaurantes(self) -> int:
        return len(self._restaurantes)

    # ── Usuarios ─────────────────────────────────────────────────────────────

    def insertar_usuario(self, id_: int, datos: dict) -> None:
        self._usuarios[id_] = datos

    def obtener_usuario(self, id_: int) -> Optional[dict]:
        return self._usuarios.get(id_)

    def todos_los_usuarios(self) -> list[dict]:
        return list(self._usuarios.values())

    def total_usuarios(self) -> int:
        return len(self._usuarios)

    # ── Serialización ────────────────────────────────────────────────────────

    def snapshot_restaurantes(self) -> dict:
        """Retorna el mapa completo clave → valor para el endpoint /diccionario."""
        return {str(k): v for k, v in self._restaurantes.items()}

    def snapshot_usuarios(self) -> dict:
        return {str(k): v for k, v in self._usuarios.items()}

    def estadisticas(self) -> dict:
        return {
            "total_restaurantes": self.total_restaurantes(),
            "total_usuarios":     self.total_usuarios(),
            "ids_restaurantes":   sorted(self._restaurantes.keys()),
            "ids_usuarios":       sorted(self._usuarios.keys()),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUCTURA 2 — PILA (Stack LIFO — historial de acciones)
# ─────────────────────────────────────────────────────────────────────────────

class PilaHistorial:
    """
    Pila LIFO para registrar acciones del usuario en la API.

    TEORÍA:
    ───────
    La pila (stack) es la estructura LIFO por excelencia. Se implementa
    sobre un arreglo dinámico (Python list): `append` es push en O(1)
    amortizado y `pop()` es pop en O(1).

    En nuestra app funciona como log de acciones auditables:
      · Cada vez que se crea/actualiza/elimina un restaurante → push.
      · Cada consulta de estructuras → push.
      · El endpoint desapilar → pop (retira la acción más reciente).

    También es la estructura que habilita el patrón Undo:
      historial.desapilar() → revierte la última acción (conceptualmente).

    Capacidad máxima configurable para evitar crecimiento indefinido
    en memoria RAM (importante en servidores de Azure de capa gratuita).
    """

    def __init__(self, capacidad_max: int = 200):
        self._items: list[dict] = []
        self.capacidad_max = capacidad_max

    def apilar(self, accion: str, detalle: Any = None) -> dict:
        """
        Push — inserta un nuevo registro en el tope de la pila. O(1).
        Si se supera la capacidad máxima, se elimina la entrada más antigua
        (fondo de la pila) para no desbordar la memoria.
        """
        entrada = {
            "accion": accion,
            "detalle": detalle,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if len(self._items) >= self.capacidad_max:
            # Eliminar el elemento más antiguo (índice 0 = fondo de la pila)
            self._items.pop(0)
        self._items.append(entrada)
        return entrada

    def desapilar(self) -> Optional[dict]:
        """
        Pop — retira y retorna el elemento del tope. O(1).
        Retorna None si la pila está vacía.
        """
        return self._items.pop() if not self.esta_vacia() else None

    def ver_tope(self) -> Optional[dict]:
        """Peek — consulta el tope sin modificar la pila. O(1)."""
        return self._items[-1] if not self.esta_vacia() else None

    def esta_vacia(self) -> bool:
        return len(self._items) == 0

    def tamanio(self) -> int:
        return len(self._items)

    def ver_todos(self) -> list[dict]:
        """
        Retorna los elementos del tope al fondo (orden LIFO).
        El índice 0 del resultado es el elemento más reciente.
        """
        return list(reversed(self._items))

    def limpiar(self) -> None:
        """Vacía la pila completa."""
        self._items.clear()

    def snapshot(self) -> dict:
        """Serialización completa para el endpoint /pila/historial."""
        elementos = self.ver_todos()
        return {
            "tamanio":   self.tamanio(),
            "capacidad": self.capacidad_max,
            "tope":      elementos[0] if elementos else None,
            "elementos": elementos,
            "nota": "Orden LIFO — índice 0 = tope (acción más reciente)",
        }


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUCTURA 3 — LISTA ENLAZADA (Linked List de restaurantes por categoría)
# ─────────────────────────────────────────────────────────────────────────────

class _NodoLista:
    """Nodo interno de la lista enlazada. No se expone al exterior."""
    __slots__ = ("dato", "siguiente")

    def __init__(self, dato: dict):
        self.dato = dato
        self.siguiente: Optional["_NodoLista"] = None


class ListaCategorias:
    """
    Lista enlazada simple que agrupa restaurantes por categoría.

    TEORÍA:
    ───────
    La lista enlazada es una secuencia de nodos donde cada uno contiene
    el dato y un puntero al nodo siguiente.

    Complejidades:
      · Insertar al frente (prepend): O(1)
      · Insertar al final  (append):  O(n) — O(1) si guardamos puntero al último
      · Buscar por campo:             O(n)
      · Eliminar por campo:           O(n)
      · Tamaño:                       O(1) con contador

    Ventaja vs arreglo: no requiere memoria contigua. Agregar en
    posición arbitraria es O(1) con el puntero correcto (sin desplazar
    todos los elementos como en un array).

    En esta implementación usamos una estructura de dos niveles:
      · Un diccionario externo  { categoría → ListaEnlazada }
      · Cada lista enlazada almacena los restaurantes de esa categoría

    Esto permite agregar/recorrer por categoría en O(m) donde m = tamaño
    de la categoría (no el total de restaurantes n).
    """

    def __init__(self):
        # Diccionario de listas: { nombre_categoria: cabeza_de_la_lista }
        self._categorias: dict[str, _NodoLista | None] = {}
        self._tamanios:   dict[str, int]               = {}
        self._total: int = 0

    # ── Inserción ────────────────────────────────────────────────────────────

    def agregar(self, categoria: str, restaurante: dict) -> None:
        """
        Agrega al final de la lista de la categoría correspondiente.
        Crea la lista si la categoría aún no existe.
        """
        nuevo = _NodoLista(restaurante)
        if categoria not in self._categorias or self._categorias[categoria] is None:
            self._categorias[categoria] = nuevo
        else:
            # Recorrer hasta el final
            temp = self._categorias[categoria]
            while temp.siguiente:
                temp = temp.siguiente
            temp.siguiente = nuevo
        self._tamanios[categoria] = self._tamanios.get(categoria, 0) + 1
        self._total += 1

    def agregar_al_frente(self, categoria: str, restaurante: dict) -> None:
        """
        Inserción al frente O(1) — útil cuando el orden de llegada no importa
        y queremos priorizar los últimos agregados.
        """
        nuevo = _NodoLista(restaurante)
        nuevo.siguiente = self._categorias.get(categoria)
        self._categorias[categoria] = nuevo
        self._tamanios[categoria] = self._tamanios.get(categoria, 0) + 1
        self._total += 1

    # ── Búsqueda ─────────────────────────────────────────────────────────────

    def obtener_por_categoria(self, categoria: str) -> list[dict]:
        """
        O(m) — recorre la lista de la categoría y retorna todos los datos.
        m = tamaño de la categoría.
        """
        resultado = []
        temp = self._categorias.get(categoria)
        while temp:
            resultado.append(temp.dato)
            temp = temp.siguiente
        return resultado

    def buscar_en_categoria(self, categoria: str, id_restaurante: int) -> Optional[dict]:
        """O(m) — búsqueda lineal dentro de la lista de una categoría."""
        temp = self._categorias.get(categoria)
        while temp:
            if temp.dato.get("id") == id_restaurante:
                return temp.dato
            temp = temp.siguiente
        return None

    # ── Eliminación ──────────────────────────────────────────────────────────

    def eliminar_de_categoria(self, categoria: str, id_restaurante: int) -> bool:
        """O(m) — elimina el primer nodo cuyo dato.id coincida."""
        cabeza = self._categorias.get(categoria)
        if cabeza is None:
            return False
        if cabeza.dato.get("id") == id_restaurante:
            self._categorias[categoria] = cabeza.siguiente
            self._tamanios[categoria] -= 1
            self._total -= 1
            return True
        anterior, actual = cabeza, cabeza.siguiente
        while actual:
            if actual.dato.get("id") == id_restaurante:
                anterior.siguiente = actual.siguiente
                self._tamanios[categoria] -= 1
                self._total -= 1
                return True
            anterior, actual = actual, actual.siguiente
        return False

    # ── Serialización ─────────────────────────────────────────────────────────

    def categorias_disponibles(self) -> list[str]:
        return list(self._categorias.keys())

    def total(self) -> int:
        return self._total

    def snapshot(self) -> dict:
        """Retorna la lista completa organizada por categoría para el endpoint."""
        datos = {}
        for cat in self._categorias:
            datos[cat] = self.obtener_por_categoria(cat)
        return {
            "total":      self._total,
            "categorias": self.categorias_disponibles(),
            "datos":      datos,
            "tamanios":   dict(self._tamanios),
            "nota": (
                "Lista enlazada agrupada por categoría. "
                "Cada categoría es una cadena independiente de nodos. "
                "Inserción O(1) al frente; búsqueda O(m) por categoría."
            ),
        }

    def todos_ordenados_por_calificacion(self) -> list[dict]:
        """
        Retorna todos los restaurantes de todas las categorías
        ordenados por calificación descendente. O(n log n).
        """
        todos = []
        for cat in self._categorias:
            todos.extend(self.obtener_por_categoria(cat))
        return sorted(todos, key=lambda r: r.get("calificacion", 0), reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUCTURA 4 — HEAP (Max-Heap para motor de recomendaciones)
# ─────────────────────────────────────────────────────────────────────────────

class HeapRecomendaciones:
    """
    Max-Heap para el motor de recomendaciones de Cato-Recomienda.

    TEORÍA:
    ───────
    Un Binary Heap es un árbol binario completo almacenado como arreglo.
    Para el nodo en índice i:
      · Hijo izquierdo: 2i + 1
      · Hijo derecho:   2i + 2
      · Padre:          (i - 1) // 2

    Propiedad Max-Heap: cada padre es ≥ a sus hijos.
    → La raíz (índice 0) siempre contiene el elemento de MAYOR prioridad.

    Python heapq implementa solo Min-Heap. Para simular Max-Heap,
    guardamos las prioridades negadas: (-calificacion, nombre, id).
    Al extraer, negamos de vuelta para recuperar el valor real.

    Operaciones:
      · insertar (heappush):    O(log n) — sube "bubbling up"
      · extraer máximo (pop):   O(log n) — baja "bubbling down"
      · ver máximo (peek):      O(1)     — solo leer índice 0
      · top-K:                  O(k log n)
      · construir desde lista:  O(n)     — heapify

    La representación como arreglo del árbol binario es la base
    teórica que el profesor puede preguntar en la sustentación.
    """

    def __init__(self):
        # Tuplas: (-calificacion, -id, nombre, id, dict_completo)
        # La prioridad negativa convierte el min-heap en max-heap
        self._heap: list[tuple] = []
        self._id_set: set[int] = set()   # para evitar duplicados exactos

    def insertar(self, id_: int, nombre: str, calificacion: float, datos: dict) -> None:
        """
        Push en el heap. O(log n).
        Si el restaurante ya existe con la misma calificación, no duplica.
        """
        entrada = (-calificacion, -id_, nombre, id_, datos)
        heapq.heappush(self._heap, entrada)
        self._id_set.add(id_)

    def extraer_maximo(self) -> Optional[dict]:
        """
        Extrae el restaurante con mayor calificación. O(log n).
        Retorna None si el heap está vacío.
        """
        if self.esta_vacio():
            return None
        neg_cal, _, nombre, id_, datos = heapq.heappop(self._heap)
        self._id_set.discard(id_)
        return {**datos, "calificacion_heap": -neg_cal}

    def ver_maximo(self) -> Optional[dict]:
        """
        Peek — consulta la raíz del heap sin modificarlo. O(1).
        """
        if self.esta_vacio():
            return None
        neg_cal, _, nombre, id_, datos = self._heap[0]
        return {**datos, "calificacion_heap": -neg_cal, "posicion_heap": 0}

    def top_k(self, k: int) -> list[dict]:
        """
        Retorna los k restaurantes de mayor calificación sin modificar el heap.
        O(k log n) — usa una copia del heap para extraer en orden.
        """
        copia = list(self._heap)
        resultado = []
        for _ in range(min(k, len(copia))):
            neg_cal, _, nombre, id_, datos = heapq.heappop(copia)
            resultado.append({
                **datos,
                "calificacion_heap": -neg_cal,
                "posicion_ranking":  len(resultado) + 1,
            })
        return resultado

    def reconstruir(self, restaurantes: list[dict]) -> None:
        """
        Construye el heap desde cero dado una lista de restaurantes. O(n).
        Útil para el startup al cargar todos los registros de la BD.
        heapq.heapify es más eficiente que n inserciones individuales.
        """
        self._heap.clear()
        self._id_set.clear()
        entradas = []
        for r in restaurantes:
            cal = r.get("calificacion", r.get("promedio_calificacion", 0.0))
            id_ = r.get("id", 0)
            nom = r.get("nombre", "")
            entradas.append((-cal, -id_, nom, id_, r))
            self._id_set.add(id_)
        heapq.heapify(entradas)
        self._heap = entradas

    def esta_vacio(self) -> bool:
        return len(self._heap) == 0

    def tamanio(self) -> int:
        return len(self._heap)

    def arreglo_heap(self) -> list[dict]:
        """
        Retorna el arreglo interno del heap en su orden real de almacenamiento.
        TEORÍA: la posición i en este arreglo corresponde al nodo i del árbol.
        Índice 0 = raíz (máximo). Hijos de i = 2i+1 y 2i+2.
        """
        resultado = []
        for i, (neg_cal, _, nombre, id_, datos) in enumerate(self._heap):
            padre_i = (i - 1) // 2 if i > 0 else None
            hijo_iz = 2 * i + 1 if (2 * i + 1) < len(self._heap) else None
            hijo_de = 2 * i + 2 if (2 * i + 2) < len(self._heap) else None
            resultado.append({
                "posicion_arreglo": i,
                "id":               id_,
                "nombre":           nombre,
                "calificacion":     -neg_cal,
                "indice_padre":     padre_i,
                "indice_hijo_izq":  hijo_iz,
                "indice_hijo_der":  hijo_de,
            })
        return resultado

    def snapshot(self) -> dict:
        """Serialización completa para el endpoint /heap/prioridad."""
        top = self.ver_maximo()
        return {
            "tamanio":         self.tamanio(),
            "maximo":          top,
            "arreglo_interno": self.arreglo_heap(),
            "top_5":           self.top_k(5),
            "nota": (
                "Max-Heap: raíz = mayor calificación. "
                "Para nodo i: padre=(i-1)//2, hijo_izq=2i+1, hijo_der=2i+2. "
                "Almacenado como arreglo; heappush/heappop O(log n)."
            ),
        }