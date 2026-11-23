"""SQLite access. The database is rebuilt from the seed scripts; it is never committed."""
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
CHARTS_DIR = DATA_DIR / "charts"
DB_PATH = RUNTIME_DIR / "demo.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # screens can read while an agent run writes
    return conn


def reset(path: Path = DB_PATH) -> sqlite3.Connection:
    for p in (path, path.with_name(path.name + "-wal"), path.with_name(path.name + "-shm")):
        if p.exists():
            p.unlink()
    conn = connect(path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn
