"""
database/db.py
================
Capa de acceso a datos de la aplicacion. Toda la interaccion con SQLite
pasa por este modulo: aqui se define el esquema de tablas y las funciones
CRUD (crear/leer/actualizar/borrar) que usan las paginas de la interfaz.

Mantener el SQL en un unico sitio facilita cambiar el motor de base de
datos en el futuro (por ejemplo a PostgreSQL) sin tocar la interfaz.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# Ruta fisica del fichero .db dentro de la carpeta "data/" del proyecto.
# Se calcula relativa a este archivo para que funcione sin importar desde
# donde se lance streamlit.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "partes.db"

# Tipos de jornada permitidos en un parte diario. Se usa como catalogo
# fijo en los desplegables del formulario para evitar valores libres.
TIPOS_JORNADA = ["Trabajo", "Vacaciones", "Baja", "Guardia", "Festivo"]

# Nombres de los meses en espanol, usados en filtros y en el PDF.
MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Nombres de los dias en espanol. Se usan en vez de strftime("%A") para
# no depender de que el sistema operativo tenga instalado el locale
# es_ES (en Windows suele fallar con LC_ALL si no esta presente).
DIAS_ES = [
    "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo",
]


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Context manager que abre una conexion a SQLite y la cierra sola.

    Usar `with get_connection() as conn:` evita tener que acordarse de
    cerrar la conexion en cada funcion y asegura que los cambios se
    guardan (commit) o se deshacen (rollback) correctamente ante errores.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL permite que varias personas lean mientras otra escribe, sin
    # bloquearse entre si. Importante en el modo "servidor - cliente",
    # donde varios companeros pueden guardar partes casi a la vez desde
    # sus navegadores contra la misma base de datos.
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Crea las tablas si no existen todavia. Se llama una vez al arrancar
    la app (ver app.py). Usar "CREATE TABLE IF NOT EXISTS" hace que sea
    seguro llamarla en cada arranque sin borrar datos existentes.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # --- Perfil del trabajador -----------------------------------
        # Tabla de una sola fila (id fijo = 1) con los datos que antes
        # se escribian a mano en la cabecera de cada hoja del Excel.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS perfil (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nombre_trabajador TEXT NOT NULL DEFAULT '',
                empresa TEXT NOT NULL DEFAULT 'Centropuertas',
                horas_jornada_estandar REAL NOT NULL DEFAULT 8.0,
                dias_vacaciones_anuales INTEGER NOT NULL DEFAULT 22
            )
            """
        )
        # Aseguramos que exista la fila unica de perfil.
        cur.execute(
            "INSERT OR IGNORE INTO perfil (id, nombre_trabajador) VALUES (1, '')"
        )

        # --- Catalogo de companeros -------------------------------------
        # Se rellena automaticamente segun se van escribiendo partes,
        # para poder ofrecer un desplegable de sugerencias en el
        # formulario en vez de tener que escribir el nombre cada vez.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS companeros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            )
            """
        )

        # --- Catalogo de clientes -----------------------------------------
        # Mismo mecanismo que companeros: se rellena solo y alimenta el
        # desplegable de sugerencias de "Cliente" en el formulario.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            )
            """
        )

        # --- Partes de trabajo diarios ------------------------------------
        # Tabla principal: un registro por dia trabajado (o de
        # vacaciones/baja/guardia). "fecha" es UNIQUE porque solo puede
        # haber un parte por dia.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS partes_diarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL UNIQUE,               -- 'YYYY-MM-DD'
                tipo_jornada TEXT NOT NULL DEFAULT 'Trabajo',
                horas_jornada REAL NOT NULL DEFAULT 0,
                horas_extra REAL NOT NULL DEFAULT 0,
                dietas REAL NOT NULL DEFAULT 0,           -- nº de dietas del dia
                cliente TEXT DEFAULT '',                  -- nombre del cliente/obra
                direccion TEXT DEFAULT '',                -- direccion/ubicacion del trabajo
                numero_trabajo TEXT DEFAULT '',           -- Nº de obra/parte
                trabajo_realizado TEXT DEFAULT '',
                observaciones TEXT DEFAULT '',
                companero TEXT DEFAULT '',
                creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_partes_fecha ON partes_diarios(fecha)"
        )

        _asegurar_columnas(conn, "partes_diarios", {
            "cliente": "TEXT DEFAULT ''",
            "direccion": "TEXT DEFAULT ''",
        })


def _asegurar_columnas(conn: sqlite3.Connection, tabla: str, columnas: dict[str, str]) -> None:
    """
    Anade columnas nuevas a una tabla ya existente si todavia no las
    tiene (migracion ligera). Necesario porque "CREATE TABLE IF NOT
    EXISTS" no modifica una tabla que un usuario ya creo con una
    version anterior de la app -- sin esto, quien ya tuviera partes
    guardados antes de añadir "cliente"/"direccion" se encontraria con
    un error al arrancar.
    """
    columnas_actuales = {fila["name"] for fila in conn.execute(f"PRAGMA table_info({tabla})")}
    for nombre, definicion_sql in columnas.items():
        if nombre not in columnas_actuales:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion_sql}")


# ----------------------------------------------------------------------
# Perfil
# ----------------------------------------------------------------------

def get_perfil() -> sqlite3.Row:
    """Devuelve la fila (unica) con los datos del perfil del trabajador."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM perfil WHERE id = 1").fetchone()


def update_perfil(nombre_trabajador: str, empresa: str,
                   horas_jornada_estandar: float,
                   dias_vacaciones_anuales: int) -> None:
    """Actualiza los datos de perfil/ajustes (siempre la fila id=1)."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE perfil
               SET nombre_trabajador = ?,
                   empresa = ?,
                   horas_jornada_estandar = ?,
                   dias_vacaciones_anuales = ?
             WHERE id = 1
            """,
            (nombre_trabajador, empresa, horas_jornada_estandar,
             dias_vacaciones_anuales),
        )


# ----------------------------------------------------------------------
# Companeros (catalogo de sugerencias)
# ----------------------------------------------------------------------

def get_companeros() -> list[str]:
    """Lista de nombres de companeros usados anteriormente, ordenados A-Z."""
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT nombre FROM companeros ORDER BY nombre COLLATE NOCASE"
        ).fetchall()
        return [f["nombre"] for f in filas]


def _registrar_companero(conn: sqlite3.Connection, nombre: str) -> None:
    """Inserta el nombre en el catalogo si no existe ya (uso interno)."""
    nombre = (nombre or "").strip()
    if nombre:
        conn.execute(
            "INSERT OR IGNORE INTO companeros (nombre) VALUES (?)", (nombre,)
        )


# ----------------------------------------------------------------------
# Clientes (catalogo de sugerencias)
# ----------------------------------------------------------------------

def get_clientes() -> list[str]:
    """Lista de nombres de clientes usados anteriormente, ordenados A-Z."""
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT nombre FROM clientes ORDER BY nombre COLLATE NOCASE"
        ).fetchall()
        return [f["nombre"] for f in filas]


def _registrar_cliente(conn: sqlite3.Connection, nombre: str) -> None:
    """Inserta el cliente en el catalogo si no existe ya (uso interno)."""
    nombre = (nombre or "").strip()
    if nombre:
        conn.execute(
            "INSERT OR IGNORE INTO clientes (nombre) VALUES (?)", (nombre,)
        )


# ----------------------------------------------------------------------
# Partes diarios (CRUD)
# ----------------------------------------------------------------------

def guardar_parte(fecha: str, tipo_jornada: str, horas_jornada: float,
                   horas_extra: float, dietas: float, cliente: str,
                   direccion: str, numero_trabajo: str,
                   trabajo_realizado: str, observaciones: str,
                   companero: str) -> None:
    """
    Crea o actualiza el parte de un dia concreto (UPSERT por fecha).

    Como cada dia solo puede tener un parte, si ya existe uno para esa
    fecha lo sobrescribimos en vez de duplicarlo; asi el formulario de
    "Nuevo Parte Diario" tambien sirve para corregir un dia ya guardado.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO partes_diarios (
                fecha, tipo_jornada, horas_jornada, horas_extra, dietas,
                cliente, direccion, numero_trabajo, trabajo_realizado,
                observaciones, companero
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET
                tipo_jornada = excluded.tipo_jornada,
                horas_jornada = excluded.horas_jornada,
                horas_extra = excluded.horas_extra,
                dietas = excluded.dietas,
                cliente = excluded.cliente,
                direccion = excluded.direccion,
                numero_trabajo = excluded.numero_trabajo,
                trabajo_realizado = excluded.trabajo_realizado,
                observaciones = excluded.observaciones,
                companero = excluded.companero,
                actualizado_en = datetime('now', 'localtime')
            """,
            (fecha, tipo_jornada, horas_jornada, horas_extra, dietas,
             cliente, direccion, numero_trabajo, trabajo_realizado,
             observaciones, companero),
        )
        _registrar_companero(conn, companero)
        _registrar_cliente(conn, cliente)


def get_parte_por_fecha(fecha: str) -> sqlite3.Row | None:
    """Recupera el parte de una fecha exacta, o None si no existe."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM partes_diarios WHERE fecha = ?", (fecha,)
        ).fetchone()


def eliminar_parte(parte_id: int) -> None:
    """Borra un parte por su id (usado desde 'Visualizar Mes')."""
    with get_connection() as conn:
        conn.execute("DELETE FROM partes_diarios WHERE id = ?", (parte_id,))


def get_partes_mes(anio: int, mes: int) -> list[sqlite3.Row]:
    """Todos los partes de un mes concreto, ordenados por fecha."""
    patron = f"{anio:04d}-{mes:02d}-%"
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM partes_diarios WHERE fecha LIKE ? ORDER BY fecha",
            (patron,),
        ).fetchall()


def buscar_partes(anio: int | None = None, texto: str = "",
                   companero: str = "", cliente: str = "") -> list[sqlite3.Row]:
    """
    Busqueda flexible en el historial completo, usada en 'Visualizar Mes'.

    - `anio`: si se indica, limita la busqueda a ese año.
    - `texto`: busca coincidencias (case-insensitive) en el trabajo
      realizado y en las observaciones -- p.ej. para localizar un fallo
      mecanico recurrente por palabra clave.
    - `companero`: filtra por el nombre exacto de companero asignado.
    - `cliente`: filtra por el nombre exacto de cliente -- p.ej. para
      ver todas las instalaciones hechas para un cliente concreto.
    """
    condiciones = []
    parametros: list = []

    if anio:
        condiciones.append("fecha LIKE ?")
        parametros.append(f"{anio:04d}-%")
    if texto:
        condiciones.append("(trabajo_realizado LIKE ? OR observaciones LIKE ?)")
        comodin = f"%{texto}%"
        parametros.extend([comodin, comodin])
    if companero:
        condiciones.append("companero = ?")
        parametros.append(companero)
    if cliente:
        condiciones.append("cliente = ?")
        parametros.append(cliente)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    consulta = f"SELECT * FROM partes_diarios {where} ORDER BY fecha DESC"

    with get_connection() as conn:
        return conn.execute(consulta, parametros).fetchall()


# ----------------------------------------------------------------------
# Agregados para el Dashboard Anual
# ----------------------------------------------------------------------

def get_anios_disponibles() -> list[int]:
    """Años distintos que tienen al menos un parte registrado."""
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT DISTINCT substr(fecha, 1, 4) AS anio "
            "FROM partes_diarios ORDER BY anio DESC"
        ).fetchall()
        return [int(f["anio"]) for f in filas]


def get_totales_anuales(anio: int) -> dict:
    """
    Sumatorio anual de horas, extras, dietas y dias especiales.
    Es el calculo equivalente a la hoja "TOTALES" del Excel original,
    pero derivado directamente de los partes diarios (sin formulas
    manuales que se puedan romper).
    """
    with get_connection() as conn:
        fila = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Trabajo'
                                   THEN horas_jornada END), 0) AS horas_totales,
                COALESCE(SUM(horas_extra), 0) AS horas_extra,
                COALESCE(SUM(dietas), 0) AS dietas,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Vacaciones'
                                   THEN 1 END), 0) AS dias_vacaciones,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Baja'
                                   THEN 1 END), 0) AS dias_baja,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Guardia'
                                   THEN 1 END), 0) AS dias_guardia,
                COUNT(*) AS total_partes
            FROM partes_diarios
            WHERE fecha LIKE ?
            """,
            (f"{anio:04d}-%",),
        ).fetchone()
        return dict(fila)


def get_totales_por_mes(anio: int) -> list[dict]:
    """
    Igual que `get_totales_anuales` pero desglosado mes a mes; es la
    fuente de datos de los graficos de barras/lineas del dashboard.
    """
    with get_connection() as conn:
        filas = conn.execute(
            """
            SELECT
                CAST(substr(fecha, 6, 2) AS INTEGER) AS mes,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Trabajo'
                                   THEN horas_jornada END), 0) AS horas_totales,
                COALESCE(SUM(horas_extra), 0) AS horas_extra,
                COALESCE(SUM(dietas), 0) AS dietas
            FROM partes_diarios
            WHERE fecha LIKE ?
            GROUP BY mes
            ORDER BY mes
            """,
            (f"{anio:04d}-%",),
        ).fetchall()
        return [dict(f) for f in filas]
