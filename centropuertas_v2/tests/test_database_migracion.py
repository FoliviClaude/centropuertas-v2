"""
tests/test_database_migracion.py
=================================
Teste la migration multi-entreprise (_migrar_a_multiempresa) contre une
base locale ephemere (fichier libsql), jamais contre la vraie base
Turso : database._client est remplace par un client local le temps du
test (monkeypatch), donc aucun secret Turso n'est necessaire pour
lancer ces tests.
"""

from __future__ import annotations

import libsql_client
import pytest

import database as db


@pytest.fixture
def client_local(tmp_path, monkeypatch):
    """Client libsql sur un fichier temporaire, branche a la place de database._client."""
    chemin_db = tmp_path / "test.db"
    client = libsql_client.create_client_sync(f"file:{chemin_db}")
    client.execute("PRAGMA foreign_keys = ON")
    monkeypatch.setattr(db, "_client", lambda: client)
    yield client
    client.close()


def test_init_db_base_neuve_cree_une_seule_empresa_bootstrap(client_local):
    db.init_db()

    empresas = db.get_empresas()
    assert len(empresas) == 1
    assert empresas[0]["nombre"] == "Centropuertas"

    empresa_id = empresas[0]["id"]
    for tabla in ("technicians", "clients", "interventions_types", "collegues", "configurations"):
        filas = client_local.execute(f"SELECT empresa_id FROM {tabla}").rows
        assert all(f["empresa_id"] == empresa_id for f in filas)


def test_init_db_es_idempotente(client_local):
    db.init_db()
    db.init_db()  # ne doit ni dupliquer l'empresa bootstrap, ni echouer

    assert len(db.get_empresas()) == 1


def test_migracion_atribuye_datos_existentes_a_la_empresa_bootstrap(client_local):
    """
    Simule une base de production existante (creee AVANT l'introduction
    d'"empresas") : schema + donnees dans leur etat pre-migration, puis
    verifie que init_db() attribue tout a une entreprise bootstrap qui
    reprend le nom deja configure -- sans rien perdre ni dupliquer.
    """
    client_local.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            direccion TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            notas TEXT DEFAULT ''
        )
    """)
    client_local.execute("""
        CREATE TABLE interventions_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    client_local.execute("""
        CREATE TABLE collegues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    client_local.execute("""
        CREATE TABLE technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            nombre_display TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'technicien',
            activo INTEGER NOT NULL DEFAULT 1,
            creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    client_local.execute("""
        CREATE TABLE configurations (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            idioma TEXT NOT NULL DEFAULT 'es',
            anio_actual INTEGER NOT NULL,
            horas_convenio_anual REAL NOT NULL DEFAULT 1780,
            dias_vacaciones_anuales INTEGER NOT NULL DEFAULT 22,
            nombre_trabajador TEXT NOT NULL DEFAULT '',
            empresa TEXT NOT NULL DEFAULT 'Centropuertas',
            nif_cif TEXT NOT NULL DEFAULT ''
        )
    """)
    client_local.execute(db._SQL_TABLA_PARTS)

    hash_hex, salt_hex = db.hash_password("secreto123")
    client_local.execute(
        """INSERT INTO technicians (login, password_hash, password_salt, nombre_display, role)
           VALUES ('antonio', ?, ?, 'Antonio', 'technicien')""",
        [hash_hex, salt_hex],
    )
    client_local.execute("""INSERT INTO configurations (id, anio_actual, empresa, nif_cif)
           VALUES (1, 2026, 'Mi Empresa SL', 'B12345678')""")
    client_local.execute(
        """INSERT INTO parts_de_travail (fecha, technician_name, tipo_jornada, horas_normales)
           VALUES ('2026-01-15', 'Antonio', 'Trabajo', 8)"""
    )

    db.init_db()

    empresas = db.get_empresas()
    assert len(empresas) == 1
    assert empresas[0]["nombre"] == "Mi Empresa SL"
    assert empresas[0]["nif_cif"] == "B12345678"
    empresa_id = empresas[0]["id"]

    technicien = client_local.execute("SELECT * FROM technicians WHERE login = 'antonio'").rows[0]
    assert technicien["empresa_id"] == empresa_id

    parte = client_local.execute("SELECT * FROM parts_de_travail WHERE fecha = '2026-01-15'").rows[
        0
    ]
    assert parte["empresa_id"] == empresa_id
    assert parte["technician_id"] == technicien["id"]
