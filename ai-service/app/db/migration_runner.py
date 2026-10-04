"""
Migration runner for SQLite.

Reads numbered SQL files from app/db/migrations/ and applies them in order.
Records applied versions in a _migrations table. Idempotent: re-running
skips already-applied migrations.
"""
import logging
import os
import re
import sqlite3

logger = logging.getLogger(__name__)

_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            version INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _applied_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT version FROM _migrations").fetchall()
    return {r[0] for r in rows}


def _discover_migrations(migrations_dir: str) -> list[tuple[int, str, str]]:
    """Returns sorted list of (version, filename, full_path)."""
    pattern = re.compile(r"^(\d+)_.+\.sql$")
    results = []
    if not os.path.isdir(migrations_dir):
        return results
    for fname in sorted(os.listdir(migrations_dir)):
        m = pattern.match(fname)
        if m:
            version = int(m.group(1))
            results.append((version, fname, os.path.join(migrations_dir, fname)))
    return results


def run_migrations(conn: sqlite3.Connection, migrations_dir: str | None = None) -> int:
    """
    Apply pending migrations. Returns count of newly applied migrations.
    """
    if migrations_dir is None:
        migrations_dir = _MIGRATIONS_DIR

    _ensure_migrations_table(conn)
    applied = _applied_versions(conn)
    migrations = _discover_migrations(migrations_dir)

    count = 0
    for version, fname, path in migrations:
        if version in applied:
            continue
        logger.info("Applying migration %d: %s", version, fname)
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO _migrations (version, filename) VALUES (?, ?)",
            (version, fname),
        )
        conn.commit()
        count += 1

    return count


def open_db(db_path: str) -> sqlite3.Connection:
    """
    Open a SQLite connection with WAL mode and foreign keys enabled.
    Runs pending migrations automatically.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    return conn
