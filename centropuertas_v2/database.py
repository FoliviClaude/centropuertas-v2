"""
database.py
============
Couche d'accès aux données de l'application. Toute l'interaction avec
SQLite passe par ce module : schéma des tables, fonctions CRUD, hachage
des mots de passe, et une fonction optionnelle pour peupler la base
avec des données de test.

Contrairement à un simple catalogue de texte libre, ce schéma est
relationnel : les clients, types d'intervention et collègues sont des
entités à part entière (avec un ID), référencées depuis les parts de
travail par clé étrangère. Cela permet de les gérer indépendamment
(page "Referencias") sans dupliquer ni désynchroniser les noms.

Multi-utilisateur (technicians) :
----------------------------------
Chaque parte appartient à un technicien (colonne `technician_name` sur
`parts_de_travail`). Les comptes de connexion vivent dans la table
`technicians` (login + mot de passe haché, jamais en clair). Les
catalogues `clients` / `interventions_types` / `collegues` restent en
revanche PARTAGÉS entre tous les techniciens (ce sont des données de
l'entreprise, pas des données personnelles) -- seuls les partes
eux-mêmes sont confidentiels et filtrés par technicien.
"""

from __future__ import annotations

import hashlib
import hmac
import os
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

# Identifiants d'un compte de démonstration créé automatiquement si la
# table "technicians" est vide (sinon personne ne pourrait jamais se
# connecter sur une base toute neuve). Bien visible ici pour qu'il soit
# facile à trouver et à supprimer/changer avant un usage réel.
LOGIN_PRUEBA = "admin"
PASSWORD_PRUEBA = "admin123"
NOMBRE_PRUEBA = "Administrador"

# Schéma SQL de "parts_de_travail", défini une seule fois et réutilisé
# à la fois par l'installation neuve et par la migration (rebuild) --
# pour ne jamais avoir deux définitions de la table qui divergent.
_SQL_TABLA_PARTS = """
    CREATE TABLE IF NOT EXISTS parts_de_travail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,                         -- 'YYYY-MM-DD'
        tipo_jornada TEXT NOT NULL DEFAULT 'Trabajo',
        horas_normales REAL NOT NULL DEFAULT 0,
        horas_extra REAL NOT NULL DEFAULT 0,
        dietas REAL NOT NULL DEFAULT 0,
        technician_name TEXT NOT NULL DEFAULT '',    -- proprietaire du parte
        id_client INTEGER REFERENCES clients(id) ON DELETE SET NULL,
        id_intervention INTEGER REFERENCES interventions_types(id) ON DELETE SET NULL,
        descripcion TEXT DEFAULT '',
        observaciones TEXT DEFAULT '',
        id_collegue INTEGER REFERENCES collegues(id) ON DELETE SET NULL,
        creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        UNIQUE (fecha, technician_name)
    )
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Context manager qui ouvre une connexion SQLite et la referme seule.

    Le mode WAL permet à plusieurs personnes de lire pendant qu'une
    autre écrit sans se bloquer mutuellement (utile en usage partagé,
    typiquement plusieurs techniciens connectés en même temps).
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
    Crée les tables si elles n'existent pas encore, migre le schéma si
    besoin, et insère les catalogues par défaut. Idempotent : peut être
    appelée à chaque démarrage sans danger.
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

        # --- technicians (comptes de connexion) -----------------------------
        # Mot de passe JAMAIS stocké en clair : PBKDF2-HMAC-SHA256 avec un
        # sel aléatoire propre à chaque compte (voir hash_password ci-dessous).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                nombre_display TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )

        # --- configurations ------------------------------------------------
        # Ligne unique (id=1) de paramètres globaux de l'application. Créée
        # AVANT "parts_de_travail" ci-dessous car la migration multi-
        # utilisateur (voir plus bas) a besoin de lire
        # configurations.nombre_trabajador pour attribuer l'historique
        # existant à un technicien.
        #
        # LIMITE CONNUE : cette table reste globale (une seule ligne
        # partagée), pas encore un paramétrage par technicien. En
        # pratique, "nombre_trabajador"/"empresa"/"nif_cif" (utilisés
        # dans l'en-tête du PDF) et le quota de vacances restent donc
        # communs à tout le monde tant que cette table n'est pas, elle
        # aussi, déclinée par technicien -- hors du périmètre demandé
        # ici (qui portait sur la confidentialité des partes), mais à
        # garder en tête pour une prochaine étape.
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
        # Migration légère : ajoute la colonne ci-dessous si la base
        # existait déjà avant son introduction (sinon "CREATE TABLE IF
        # NOT EXISTS" ne la crée pas sur une table déjà existante).
        _asegurar_columnas(conn, "configurations", {
            "nif_cif": "TEXT NOT NULL DEFAULT ''",
        })

        # --- parts_de_travail ----------------------------------------------
        # "ON DELETE SET NULL" : si on supprime un client/type/collègue
        # depuis "Referencias", les partes deja enregistres ne sont PAS
        # perdus -- seule la reference devient vide (l'historique reste
        # consultable, juste sans ce lien).
        #
        # "UNIQUE (fecha, technician_name)" (et non plus "fecha UNIQUE"
        # seul) : chaque technicien a droit à UN parte par jour, mais
        # deux techniciens différents peuvent chacun avoir le leur à la
        # même date -- indispensable en multi-utilisateur, sinon le
        # second technicien à enregistrer une date déjà prise écraserait
        # silencieusement le parte du premier.
        cur.execute(_SQL_TABLA_PARTS)

        # Migration plus lourde : bascule "parts_de_travail" vers le
        # schéma multi-utilisateur si une base pré-existante utilise
        # encore l'ancien schéma (sans technician_name). DOIT s'exécuter
        # avant la création des index ci-dessous, sinon l'index sur
        # technician_name échoue sur une table pas encore migrée.
        _migrar_parts_de_travail_multiusuario(conn)

        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_parts_fecha ON parts_de_travail(fecha)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_parts_technician ON parts_de_travail(technician_name)"
        )

        # Catalogue par défaut des types d'intervention (une seule fois).
        for nombre in TIPOS_INTERVENCION_DEFECTO:
            cur.execute(
                "INSERT OR IGNORE INTO interventions_types (nombre) VALUES (?)",
                (nombre,),
            )

        # Bootstrap : s'il n'existe encore AUCUN compte technicien (base
        # neuve), on en crée un de test -- sans ça, personne ne pourrait
        # jamais se connecter à une base fraîchement installée. À
        # changer/supprimer avant un usage réel (voir LEEME du projet).
        if conn.execute("SELECT COUNT(*) FROM technicians").fetchone()[0] == 0:
            hash_hex, salt_hex = hash_password(PASSWORD_PRUEBA)
            conn.execute(
                """INSERT INTO technicians (login, password_hash, password_salt, nombre_display)
                   VALUES (?, ?, ?, ?)""",
                (LOGIN_PRUEBA, hash_hex, salt_hex, NOMBRE_PRUEBA),
            )


def _asegurar_columnas(conn: sqlite3.Connection, tabla: str, columnas: dict[str, str]) -> None:
    """Ajoute des colonnes manquantes à une table déjà existante (migration légère)."""
    columnas_actuales = {fila["name"] for fila in conn.execute(f"PRAGMA table_info({tabla})")}
    for nombre, definicion_sql in columnas.items():
        if nombre not in columnas_actuales:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion_sql}")


def _migrar_parts_de_travail_multiusuario(conn: sqlite3.Connection) -> None:
    """
    Reconstruit "parts_de_travail" avec le schéma multi-utilisateur si
    une base pré-existante (créée avant l'introduction de
    "technician_name") est détectée.

    SQLite ne permet pas de modifier une contrainte UNIQUE avec un
    simple ALTER TABLE -- il faut reconstruire la table (renommer,
    recréer avec le bon schéma, recopier les données, supprimer
    l'ancienne). C'est le procédé standard documenté par SQLite pour
    ce genre de changement de contrainte.

    Les partes déjà enregistrés (forcément saisis par une seule
    personne, avant l'existence des comptes techniciens) sont
    attribués au nom déjà renseigné dans configurations.nombre_trabajador
    -- c'est la meilleure information disponible pour deviner "à qui"
    appartient l'historique existant, sans script externe.
    """
    colonnes = {f["name"] for f in conn.execute("PRAGMA table_info(parts_de_travail)")}
    if not colonnes or "technician_name" in colonnes:
        return  # table neuve (rien à migrer) ou déjà migrée

    fila_config = conn.execute(
        "SELECT nombre_trabajador FROM configurations WHERE id = 1"
    ).fetchone()
    nombre_historico = ((fila_config["nombre_trabajador"] if fila_config else "") or "Sin asignar").strip()

    conn.execute("ALTER TABLE parts_de_travail RENAME TO parts_de_travail_old")
    conn.execute(_SQL_TABLA_PARTS)
    conn.execute(
        """
        INSERT INTO parts_de_travail (
            id, fecha, tipo_jornada, horas_normales, horas_extra, dietas,
            technician_name, id_client, id_intervention, descripcion,
            observaciones, id_collegue, creado_en, actualizado_en
        )
        SELECT id, fecha, tipo_jornada, horas_normales, horas_extra, dietas,
               ?, id_client, id_intervention, descripcion, observaciones,
               id_collegue, creado_en, actualizado_en
        FROM parts_de_travail_old
        """,
        (nombre_historico,),
    )
    conn.execute("DROP TABLE parts_de_travail_old")
    # Les index sont recréés par l'appelant (init_db) juste après --
    # pas besoin de les dupliquer ici.


# ----------------------------------------------------------------------
# Mots de passe (PBKDF2-HMAC-SHA256, sel aléatoire par compte)
# ----------------------------------------------------------------------
# Pas de dépendance externe (bcrypt/passlib) : hashlib.pbkdf2_hmac fait
# partie de la bibliothèque standard de Python et évite les soucis de
# compilation de bcrypt sous Windows sans compilateur C installé. Le
# nombre d'itérations suit les recommandations OWASP actuelles pour
# PBKDF2-SHA256.
_PBKDF2_ITERACIONES = 600_000


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Retourne (hash_hex, salt_hex). Génère un sel aléatoire si non fourni."""
    if salt is None:
        salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERACIONES)
    return hash_bytes.hex(), salt.hex()


def _verificar_password(password: str, hash_guardado_hex: str, salt_hex: str) -> bool:
    """Comparaison en temps constant (hmac.compare_digest) pour éviter les attaques par timing."""
    salt = bytes.fromhex(salt_hex)
    hash_calculado, _ = hash_password(password, salt)
    return hmac.compare_digest(hash_calculado, hash_guardado_hex)


# ----------------------------------------------------------------------
# Technicians (comptes de connexion)
# ----------------------------------------------------------------------

def crear_technician(login: str, password: str, nombre_display: str) -> None:
    """Crée un compte technicien. `login` doit être unique (insensible à la casse)."""
    hash_hex, salt_hex = hash_password(password)
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO technicians (login, password_hash, password_salt, nombre_display)
               VALUES (?, ?, ?, ?)""",
            (login.strip().lower(), hash_hex, salt_hex, nombre_display.strip()),
        )


def get_technicians() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM technicians ORDER BY nombre_display COLLATE NOCASE"
        ).fetchall()


def verificar_credenciales(login: str, password: str) -> Optional[sqlite3.Row]:
    """
    Vérifie login + mot de passe. Renvoie la ligne "technicians"
    correspondante si valides et le compte actif, sinon None.

    Le message d'erreur envoyé à l'utilisateur (voir auth.py) ne doit
    JAMAIS distinguer "login inconnu" de "mot de passe incorrect" (pour
    ne pas révéler quels logins existent) -- cette fonction renvoie
    simplement None dans les deux cas, à dessein.
    """
    with get_connection() as conn:
        fila = conn.execute(
            "SELECT * FROM technicians WHERE login = ? AND activo = 1",
            (login.strip().lower(),),
        ).fetchone()
    if fila is None:
        return None
    if not _verificar_password(password, fila["password_hash"], fila["password_salt"]):
        return None
    return fila


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
# Parts de travail (CRUD) -- toujours filtrés/scopés par technician_name
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


def guardar_parte(fecha: str, technician_name: str, tipo_jornada: str,
                   horas_normales: float, horas_extra: float, dietas: float,
                   id_client: Optional[int], id_intervention: Optional[int],
                   descripcion: str, observaciones: str,
                   id_collegue: Optional[int]) -> None:
    """
    Crée ou met à jour (UPSERT par date + technicien) le parte d'un
    jour donné pour CE technicien. `technician_name` doit toujours être
    celui de l'utilisateur actuellement connecté (jamais une valeur
    reprise telle quelle d'un parte déjà chargé) : c'est ce qui
    garantit qu'un technicien ne peut jamais écrire par erreur -- ou
    par une donnée trafiquée -- dans les partes d'un collègue.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO parts_de_travail (
                fecha, technician_name, tipo_jornada, horas_normales, horas_extra, dietas,
                id_client, id_intervention, descripcion, observaciones, id_collegue
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fecha, technician_name) DO UPDATE SET
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
            (fecha, technician_name, tipo_jornada, horas_normales, horas_extra, dietas,
             id_client, id_intervention, descripcion, observaciones, id_collegue),
        )


def get_parte_por_fecha(fecha: str, technician_name: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            f"{_SELECT_PARTE_CON_NOMBRES} WHERE p.fecha = ? AND p.technician_name = ?",
            (fecha, technician_name),
        ).fetchone()


def eliminar_parte(parte_id: int, technician_name: str) -> None:
    """Le filtre technician_name empêche de supprimer le parte d'un autre technicien."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM parts_de_travail WHERE id = ? AND technician_name = ?",
            (parte_id, technician_name),
        )


def get_partes_mes(anio: int, mes: int, technician_name: str) -> list[sqlite3.Row]:
    patron = f"{anio:04d}-{mes:02d}-%"
    with get_connection() as conn:
        return conn.execute(
            f"{_SELECT_PARTE_CON_NOMBRES} WHERE p.fecha LIKE ? AND p.technician_name = ? ORDER BY p.fecha",
            (patron, technician_name),
        ).fetchall()


def buscar_partes(technician_name: str, anio: int | None = None, texto: str = "",
                   id_client: int | None = None,
                   id_collegue: int | None = None,
                   id_intervention: int | None = None) -> list[sqlite3.Row]:
    """
    Recherche flexible dans l'historique du technicien connecté (par
    année, mot-clé dans description/observations, et/ou client/
    collègue/type d'intervention précis). `technician_name` n'est
    jamais optionnel : impossible d'appeler cette fonction sans
    préciser de qui on consulte l'historique.
    """
    condiciones = ["p.technician_name = ?"]
    parametros: list = [technician_name]

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
    if id_intervention:
        condiciones.append("p.id_intervention = ?")
        parametros.append(id_intervention)

    where = f"WHERE {' AND '.join(condiciones)}"
    with get_connection() as conn:
        return conn.execute(
            f"{_SELECT_PARTE_CON_NOMBRES} {where} ORDER BY p.fecha DESC", parametros
        ).fetchall()


# ----------------------------------------------------------------------
# Agrégats pour le Dashboard -- toujours filtrés par technician_name
# ----------------------------------------------------------------------

def get_anios_disponibles(technician_name: str) -> list[int]:
    with get_connection() as conn:
        filas = conn.execute(
            """SELECT DISTINCT substr(fecha, 1, 4) AS anio FROM parts_de_travail
               WHERE technician_name = ? ORDER BY anio DESC""",
            (technician_name,),
        ).fetchall()
        return [int(f["anio"]) for f in filas]


def get_totales_anuales(anio: int, technician_name: str) -> dict:
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
            WHERE fecha LIKE ? AND technician_name = ?
            """,
            (f"{anio:04d}-%", technician_name),
        ).fetchone()
        return dict(fila)


def get_totales_por_mes(anio: int, technician_name: str) -> list[dict]:
    with get_connection() as conn:
        filas = conn.execute(
            """
            SELECT
                CAST(substr(fecha, 6, 2) AS INTEGER) AS mes,
                COALESCE(SUM(CASE WHEN tipo_jornada = 'Trabajo' THEN horas_normales END), 0) AS horas_normales,
                COALESCE(SUM(horas_extra), 0) AS horas_extra,
                COALESCE(SUM(dietas), 0) AS dietas
            FROM parts_de_travail
            WHERE fecha LIKE ? AND technician_name = ?
            GROUP BY mes
            ORDER BY mes
            """,
            (f"{anio:04d}-%", technician_name),
        ).fetchall()
        return [dict(f) for f in filas]


# ----------------------------------------------------------------------
# Données de test (optionnel -- n'est jamais appelé automatiquement par
# init_db(), pour que l'application démarre vide en usage normal). Le
# compte "admin" de démonstration (voir LOGIN_PRUEBA en tête de
# fichier), lui, EST créé automatiquement par init_db() s'il n'existe
# encore aucun technicien -- sinon personne ne pourrait se connecter.
# ----------------------------------------------------------------------

def poblar_datos_prueba() -> None:
    """
    Remplit la base avec deux comptes techniciens, quelques clients et
    des parts de travail fictifs répartis entre eux -- utile pour
    explorer l'application ou pour les tests automatisés. À appeler
    explicitement, par ex. :

        python -c "from database import init_db, poblar_datos_prueba; init_db(); poblar_datos_prueba()"
    """
    init_db()

    technicians_prueba = [
        # (login, password, nombre affiché)
        ("antonio", "antonio123", "Antonio"),
        ("manuel", "manuel123", "Manuel"),
    ]
    for login, password, nombre in technicians_prueba:
        with get_connection() as conn:
            existe = conn.execute(
                "SELECT 1 FROM technicians WHERE login = ?", (login,)
            ).fetchone()
        if not existe:
            crear_technician(login, password, nombre)

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

    # (fecha, technicien_proprietaire, tipo, horas, extra, dietas, cliente,
    #  tipo_intervencion, descripcion, observaciones, colega_tag)
    partes_prueba = [
        ("2026-06-02", "Antonio", "Trabajo", 8, 0, 1, "Comunidad Vecinos Los Almendros", "Instalación de puerta automática", "Instalación de puerta seccional en garaje comunitario.", "Sin incidencias.", "Manuel"),
        ("2026-06-03", "Antonio", "Trabajo", 8, 1, 1, "Nave Industrial Polígono Sur", "Mantenimiento mecánico", "Mantenimiento preventivo de puerta corredera industrial.", "Motor con ruido anómalo, pendiente de recambio.", None),
        ("2026-06-05", "Manuel", "Trabajo", 7, 0, 0, "Hotel Playa Dorada", "Ajuste/Cableado de sensores GEZE", "Ajuste de fotocélulas GEZE en puerta automática de acceso.", "Cables de los sensores GEZE cruzados en la instalación anterior.", None),
        ("2026-06-08", "Antonio", "Guardia", 4, 0, 0, None, None, "Guardia de fin de semana, sin avisos.", "", None),
        ("2026-06-15", "Manuel", "Vacaciones", 0, 0, 0, None, None, "", "", None),
        ("2026-07-02", "Manuel", "Trabajo", 8, 1, 1, "Hotel Playa Dorada", "Reset de placa de control", "Reset de placa de control y recalibración de encoder.", "Encoder descalibrado, recalibrado en la misma visita.", None),
        ("2026-07-20", "Antonio", "Trabajo", 8, 3, 1, "Nave Industrial Polígono Sur", "Resolución de averías", "Avería urgente: puerta bloqueada en apertura.", "Cables de sensores GEZE cruzados de nuevo, se recomienda revisar el cableado a fondo.", "Manuel"),
    ]

    for (fecha, tecnico, tipo, horas, extra, dietas, cliente, tipo_interv, desc, obs, colega) in partes_prueba:
        guardar_parte(
            fecha=fecha, technician_name=tecnico, tipo_jornada=tipo,
            horas_normales=horas, horas_extra=extra, dietas=dietas,
            id_client=clientes.get(cliente), id_intervention=tipos.get(tipo_interv),
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
    print(f"Techniciens enregistres : {[t['login'] for t in get_technicians()]}")
