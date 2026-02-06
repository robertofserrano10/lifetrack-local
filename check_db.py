import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "storage" / "lifetrack.db"
SCHEMA_PATH = BASE_DIR / "storage" / "schema.sql"

def main():
    print("DB PATH:", DB_PATH)
    print("SCHEMA PATH:", SCHEMA_PATH)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No existe schema.sql en {SCHEMA_PATH}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)

    print("Base de datos creada correctamente con todas las tablas.")

if __name__ == "__main__":
    main()
