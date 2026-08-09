"""
database.py
============
Couche d'accès aux données de l'application. Toute l'interaction avec
SQLite passe par ce module : schéma des tables, fonctions CRUD, et une
fonction optionnelle pour peupler la base avec des données de test.

Contrairement à un simple catalogue de texte libre, ce schéma est
relationnel : les clients, types d'intervention et collègues sont des
entités à part entière (avec un ID), référencées depuis les parts de
travail par clé étrangère. Cela permet de les gérer indépendamment
(page "Referencias") sans dupliquer ni désynchroniser les noms.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

# ----------------------------------------------------------------------
# Emplacement physique du fichier .db, relatif à ce module (fonctionne
# quel que soit le répertoire depuis lequel Streamlit est lancé).
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "centropuertas.db"

# Types de journée possibles pour un part de travail. Catalogue fixe
# (pas une table à part) car ce sont des valeurs stables et rarement
# amenées à changer -- contrairement aux clients/types d'intervention
# qui, eux, ont leur propre table gérable depuis "Referencias".
TIPOS_JORNADA = ["Trabajo", "Vacaciones", "Baja", "Guardia", "Festivo"]

# Catalogue par défaut des types d'intervention, propre au métier des
# portes automatiques. Inséré une seule fois au premier lancement ;
# l'utilisateur peut ensuite en ajouter/modifier/supprimer depuis la
# page "Referencias".
TIPOS_INTERVENCION_DEFECTO = [
    "Instalación de puerta automática",
    "Ajuste/Cableado de sensores GEZE",
    "Reset de placa de control",
    "Mantenimiento mecánico",
    "Resolución de averías",
]


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Context manager qui ouvre une connexion SQLite et la referme seule.

    Le mode WAL permet à plusieurs personnes de lire pendant qu'une
    autre écrit sans se bloquer mutuellement (utile en usage partagé).
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row  # accès aux colonnes par nom
    conn.execute("PRAGMA foreign_keys = ON")
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
    Crée les tables si elles n'existent pas encore et insère les
    catalogues par défaut (types d'intervention, ligne de config).
    Idempotent : peut être appelée à chaque démarrage sans danger.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # --- clients ---------------------------------------------------
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                direccion TEXT DEFAULT '',
                telefono TEXT DEFAULT '',
                notas TEXT DEFAULT ''
            )
            """
        )

        # --- interventions_types ----------------------------------------
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS interventions_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            )
            """
        )

        # --- collegues ---------------------------------------------------
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS collegues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            )
            """
        )

        # --- parts_de_travail ----------------------------------------------
        # "ON DELETE SET NULL" : si on supprime un client/type/collègue
        # depuis "Referencias", les partes deja enregistres ne sont PAS
        # perdus -- seule la reference devient vide (l'historique reste
        # consultable, juste sans ce lien).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS parts_de_travail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL UNIQUE,                  -- 'YYYY-MM-DD'
                tipo_jornada TEXT NOT NULL DEFAULT 'Trabajo',
                horas_normales REAL NOT NULL DEFAULT 0,
                horas_extra REAL NOT NULL DEFAULT 0,
                dietas REAL NOT NULL DEFAULT 0,
                id_client INTEGER REFERENCES clients(id) ON DELETE SET NULL,
                id_intervention INTEGER REFERENCES interventions_types(id) ON DELETE SET NULL,
                descripcion TEXT DEFAULT '',
                observaciones TEXT DEFAULT '',
                id_collegue INTEGER REFERENCES collegues(id) ON DELETE SET NULL,
                creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_parts_fecha ON parts_de_travail(fecha)"
        )

        # --- configurations ------------------------------------------------
        # Ligne unique (id=1) de paramètres globaux de l'application.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                idioma TEXT NOT NULL DEFAULT 'es',
                anio_actual INTEGER NOT NULL,
                horas_convenio_anual REAL NOT NULL DEFAULT 1780,
                dias_vacaciones_anuales INTEGER NOT NULL DEFAULT 22,
                nombre_trabajador TEXT NOT NULL DEFAULT '',
                empresa TEXT NOT NULL DEFAULT 'Centropuertas',
                nif_cif TEXT NOT NULL DEFAULT ''
            )
            """
        )
        cur.execute(
            "INSERT OR IGNORE INTO configurations (id, anio_actual) VALUES (1, ?)",
            (__import__("datetime").date.today().year,),
        )

        # Catalogue par défaut des types d'intervention (une seule fois).
        for nombre in TIPOS_INTERVENCION_DEFECTO:
            cur.execute(
                "INSERT OR IGNORE INTO interventions_types (nombre) VALUES (?)",
                (nombre,),
            )

        # Migration légère : ajoute la colonne ci-dessus si la base
        # existait déjà avant son introduction (sinon "CREATE TABLE IF
        # NOT EXISTS" ne la crée pas sur une table déjà existante).
        _asegurar_columnas(conn, "configurations", {
            "nif_cif": "TEXT NOT NULL DEFAULT ''",
        })


def _asegurar_columnas(conn: sqlite3.Connection, tabla: str, columnas: dict[str, str]) -> None:
    """Ajoute des colonnes manquantes à une table déjà existante (migration légère)."""
    columnas_actuales = {fila["name"] for fila in conn.execute(f"PRAGMA table_info({tabla})")}
    for nombre, definicion_sql in columnas.items():
        if nombre not in columnas_actuales:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion_sql}")


# ----------------------------------------------------------------------
# Configuration globale
# ----------------------------------------------------------------------

def get_configuracion() -> sqlite3.Row:
    """Retourne la ligne unique de configuration globale (id=1)."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM configurations WHERE id = 1").fetchone()


def actualizar_configuracion(idioma: str, anio_actual: int,
                              horas_convenio_anual: float,
                              dias_vacaciones_anuales: int,
                              nombre_trabajador: str, empresa: str,
                              nif_cif: str) -> None:
    """Met à jour la configuration globale (toujours la ligne id=1)."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE configurations
               SET idioma = ?, anio_actual = ?, horas_convenio_anual = ?,
                   dias_vacaciones_anuales = ?, nombre_trabajador = ?, empresa = ?,
                   nif_cif = ?
             WHERE id = 1
            """,
            (idioma, anio_actual, horas_convenio_anual, dias_vacaciones_anuales,
             nombre_trabajador, empresa, nif_cif),
        )


def actualizar_idioma(idioma: str) -> None:
    """Raccourci pour ne changer que la langue (utilisé par le sélecteur)."""
    with get_connection() as conn:
        conn.execute("UPDATE configurations SET idioma = ? WHERE id = 1", (idioma,))


# ----------------------------------------------------------------------
# Referencias : clients
# ----------------------------------------------------------------------

def get_clients() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM clients ORDER BY nombre COLLATE NOCASE").fetchall()


def crear_client(nombre: str, direccion: str, telefono: str, notas: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clients (nombre, direccion, telefono, notas) VALUES (?, ?, ?, ?)",
            (nombre.strip(), direccion.strip(), telefono.strip(), notas.strip()),
        )


def actualizar_client(client_id: int, nombre: str, direccion: str,
                       telefono: str, notas: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE clients SET nombre = ?, direccion = ?, telefono = ?, notas = ?
               WHERE id = ?""",
            (nombre.strip(), direccion.strip(), telefono.strip(), notas.strip(), client_id),
        )


def eliminar_client(client_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))


# ----------------------------------------------------------------------
# Referencias : types d'intervention
# ----------------------------------------------------------------------

def get_interventions_types() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM interventions_types ORDER BY nombre COLLATE NOCASE"
        ).fetchall()


def crear_intervention_type(nombre: str) -> None:
    with get_connection() as conn:
        conn.execute("INSERT INTO interventions_types (nombre) VALUES (?)", (nombre.strip(),))


def actualizar_intervention_type(tipo_id: int, nombre: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE interventions_types SET nombre = ? WHERE id = ?",
            (nombre.strip(), tipo_id),
        )


def eliminar_intervention_type(tipo_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM interventions_types WHERE id = ?", (tipo_id,))


# ----------------------------------------------------------------------
# Referencias : collègues
# ----------------------------------------------------------------------

def get_collegues() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM collegues ORDER BY nombre COLLATE NOCASE").fetchall()


def crear_collegue(nombre: str) -> None:
    with get_connection() as conn:
        conn.execute("INSERT INTO collegues (nombre) VALUES (?)", (nombre.strip(),))


def actualizar_collegue(collegue_id: int, nombre: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE collegues SET nombre = ? WHERE id = ?", (nombre.strip(), collegue_id))


def eliminar_collegue(collegue_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM collegues WHERE id = ?", (collegue_id,))


# ----------------------------------------------------------------------
# Parts de travail (CRUD)
# ----------------------------------------------------------------------

# Requête de base qui joint les 3 tables de référence pour récupérer
# directement les noms lisibles (et pas seulement les ID) -- réutilisée
# par plusieurs fonctions de lecture ci-dessous.
_SELECT_PARTE_CON_NOMBRES = """
    SELECT
        p.*,
        c.nombre AS cliente_nombre,
        it.nombre AS intervencion_nombre,
        co.nombre AS collegue_nombre
    FROM parts_de_travail p
    LEFT JOIN clients c ON c.id = p.id_client
    LEFT JOIN interventions_types it ON it.id = p.id_intervention
    LEFT JOIN collegues co ON co.id = p.id_collegue
"""


def guardar_parte(fecha: str, tipo_jornada: str, horas_normales: float,
                   horas_extra: float, dietas: float,
                   id_client: Optional[int], id_intervention: Optional[int],
                   descripcion: str, observaciones: str,
                   id_collegue: Optional[int]) -> None:
    """Crée ou met à jour (UPSERT par date) le parte d'un jour donné."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO parts_de_travail (
                fecha, tipo_jornada, horas_normales, horas_extra, dietas,
                id_client, id_intervention, descripcion, observaciones, id_collegue
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET
                tipo_jornada = excluded.tipo_jornada,
                horas_normales = excluded.horas_normales,
                horas_extra = excluded.horas_extra,
                dietas = excluded.dietas,
                id_client = excluded.id_client,
                id_intervention = excluded.id_intervention,
                descripcion = excluded.descripcion,
                observaciones = excluded.observaciones,
                id_collegue = excluded.id_collegue,
                actualizado_en = datetime('now', 'localtime')
            """,
            (fecha, tipo_jornada, horas_normales, horas_extra, dietas,
             id_client, id_intervention, descripcion, observaciones, id_collegue),
        )


def get_parte_por_fecha(fecha: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            f"{_SELECT_PARTE_CON_NOMBRES} WHERE p.fecha = ?", (fecha,)
        ).fetchone()


def eliminar_parte(parte_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM parts_de_travail WHERE id = ?", (parte_id,))


def get_partes_mes(anio: int, mes: int) -> list[sqlite3.Row]:
    patron = f"{anio:04d}-{mes:02d}-%"
    with get_connection() as conn:
        return conn.execute(
            f"{_SELECT_PARTE_CON_NOMBRES} WHERE p.fecha LIKE ? ORDER BY p.fecha", (patron,)
        ).fetchall()


def buscar_partes(anio: int | None = None, texto: str = "",
                   id_client: int | None = None,
                   id_collegue: int | None = None) -> list[sqlite3.Row]:
    """
    Recherche flexible dans tout l'historique : par année, mot-clé
    (dans description/observations) et/ou client/collègue précis.
    """
    condiciones = []
    parametros: list = []

    if anio:
        condiciones.append("p.fecha LIKE ?")
        parametros.append(f"{anio:04d}-%")
    if texto:
        condiciones.append("(p.descripcion LIKE ? OR p.observaciones LIKE ?)")
        comodin = f"%{texto}%"
        parametros.extend([comodin, comodin])
    if id_client:
        condiciones.append("p.id_client = ?")
        parametros.append(id_client)
    if id_collegue:
        condiciones.append("p.id_collegue = ?")
        parametros.append(id_collegue)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    with get_connection() as conn:
        return conn.execute(
            f"{_SELECT_PARTE_CON_NOMBRES} {where} ORDER BY p.fecha DESC", parametros
        ).fetchall()


# ----------------------------------------------------------------------
# Agrégats pour le Dashboard
# ----------------------------------------------------------------------

def get_anios_disponibles() -> list[int]:
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT DISTINCT substr(fecha, 1, 4) AS anio FROM parts_de_travail ORDER BY anio DESC"
        ).fetchall()
        return [int(f["anio"]) for f in filas]


def get_totales_anuales(anio: int) -> dict:
    with get_connection() as conn:
        fila = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Trabajo' THEN horas_normales END), 0) AS horas_normales,
                COALESCE(SUM(horas_extra), 0) AS horas_extra,
                COALESCE(SUM(dietas), 0) AS dietas,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Vacaciones' THEN 1 END), 0) AS dias_vacaciones,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Baja' THEN 1 END), 0) AS dias_baja,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Guardia' THEN 1 END), 0) AS dias_guardia,
                COUNT(*) AS total_partes
            FROM parts_de_travail
            WHERE fecha LIKE ?
            """,
            (f"{anio:04d}-%",),
        ).fetchone()
        return dict(fila)


def get_totales_por_mes(anio: int) -> list[dict]:
    with get_connection() as conn:
        filas = conn.execute(
            """
            SELECT
                CAST(substr(fecha, 6, 2) AS INTEGER) AS mes,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Trabajo' THEN horas_normales END), 0) AS horas_normales,
                COALESCE(SUM(horas_extra), 0) AS horas_extra,
                COALESCE(SUM(dietas), 0) AS dietas
            FROM parts_de_travail
            WHERE fecha LIKE ?
            GROUP BY mes
            ORDER BY mes
            """,
            (f"{anio:04d}-%",),
        ).fetchall()
        return [dict(f) for f in filas]


# ----------------------------------------------------------------------
# Données de test (optionnel -- n'est jamais appelé automatiquement par
# init_db(), pour que l'application démarre vide en usage normal).
# ----------------------------------------------------------------------

def poblar_datos_prueba() -> None:
    """
    Remplit la base avec quelques clients, collègues et parts de
    travail fictifs, utile pour explorer l'application ou pour les
    tests automatisés. À appeler explicitement, par ex. :

        python -c "from database import init_db, poblar_datos_prueba; init_db(); poblar_datos_prueba()"
    """
    init_db()

    clientes_prueba = [
        ("Comunidad Vecinos Los Almendros", "Calle Olivo 14, Sevilla", "954 111 222", ""),
        ("Nave Industrial Polígono Sur", "Polígono Sur, Nave 12, Sevilla", "954 333 444", "Acceso solo en horario de mañana"),
        ("Hotel Playa Dorada", "Paseo Marítimo 3, Málaga", "952 555 666", ""),
    ]
    colegas_prueba = ["Antonio", "Manuel"]

    with get_connection() as conn:
        for nombre, direccion, telefono, notas in clientes_prueba:
            conn.execute(
                "INSERT OR IGNORE INTO clients (nombre, direccion, telefono, notas) VALUES (?, ?, ?, ?)",
                (nombre, direccion, telefono, notas),
            )
        for nombre in colegas_prueba:
            conn.execute("INSERT OR IGNORE INTO collegues (nombre) VALUES (?)", (nombre,))

    clientes = {c["nombre"]: c["id"] for c in get_clients()}
    colegas = {c["nombre"]: c["id"] for c in get_collegues()}
    tipos = {t["nombre"]: t["id"] for t in get_interventions_types()}

    partes_prueba = [
        ("2026-06-02", "Trabajo", 8, 0, 1, "Comunidad Vecinos Los Almendros", "Instalación de puerta automática", "Instalación de puerta seccional en garaje comunitario.", "Sin incidencias.", "Antonio"),
        ("2026-06-03", "Trabajo", 8, 1, 1, "Nave Industrial Polígono Sur", "Mantenimiento mecánico", "Mantenimiento preventivo de puerta corredera industrial.", "Motor con ruido anómalo, pendiente de recambio.", "Antonio"),
        ("2026-06-05", "Trabajo", 7, 0, 0, "Hotel Playa Dorada", "Ajuste/Cableado de sensores GEZE", "Ajuste de fotocélulas GEZE en puerta automática de acceso.", "", "Manuel"),
        ("2026-06-08", "Guardia", 4, 0, 0, None, None, "Guardia de fin de semana, sin avisos.", "", None),
        ("2026-06-15", "Vacaciones", 0, 0, 0, None, None, "", "", None),
        ("2026-07-02", "Trabajo", 8, 1, 1, "Hotel Playa Dorada", "Reset de placa de control", "Reset de placa de control y recalibración de encoder.", "Encoder descalibrado, recalibrado en la misma visita.", "Manuel"),
        ("2026-07-20", "Trabajo", 8, 3, 1, "Nave Industrial Polígono Sur", "Resolución de averías", "Avería urgente: puerta bloqueada en apertura.", "Aviso fuera de horario, resuelto en el día.", "Antonio"),
    ]

    for (fecha, tipo, horas, extra, dietas, cliente, tipo_interv, desc, obs, colega) in partes_prueba:
        guardar_parte(
            fecha=fecha, tipo_jornada=tipo, horas_normales=horas, horas_extra=extra,
            dietas=dietas, id_client=clientes.get(cliente), id_intervention=tipos.get(tipo_interv),
            descripcion=desc, observaciones=obs, id_collegue=colegas.get(colega),
        )


if __name__ == "__main__":
    # Execution directe ("python database.py") : cree le schema et
    # affiche un resume, pratique pour verifier rapidement l'etat de
    # la base sans passer par l'application.
    init_db()
    config = get_configuracion()
    print(f"Base de donnees prete : {DB_PATH}")
    print(f"Annee courante configuree : {config['anio_actual']}")
    print(f"Types d'intervention : {[t['nombre'] for t in get_interventions_types()]}")
