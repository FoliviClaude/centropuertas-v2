"""Persistencia SQLite para Snap."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "snap.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT NOT NULL UNIQUE,
            long_url TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


def save_url(short_code: str, long_url: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO urls (short_code, long_url) VALUES (?, ?)",
        (short_code, long_url),
    )
    conn.commit()
    conn.close()


def get_url(short_code: str) -> str | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT long_url FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    conn.close()
    return row["long_url"] if row else None


def code_exists(short_code: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    conn.close()
    return row is not None


def list_urls() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT short_code, long_url, created_at FROM urls ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows
