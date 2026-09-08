"""
SQLite database connection and lifecycle manager.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from app.core.config import settings
from app.core.logging import logger
from app.db.schema import SCHEMA_SQL


def get_db_path() -> Path:
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        rel_or_abs = db_url.replace("sqlite:///", "")
        path = Path(rel_or_abs)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return Path("./data/fact_layer.db")


def init_db() -> None:
    """Initialize database tables, pragmas and indexes."""
    db_path = get_db_path()
    logger.info(f"Initializing SQLite database at: {db_path.resolve()}")
    
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    logger.info("Database schema initialized successfully.")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide a thread-safe transactional database connection."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
