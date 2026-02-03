import sqlite3
from pathlib import Path

# Asegurar carpeta storage
Path("storage").mkdir(exist_ok=True)

# Leer schema
with open("storage/schema.sql", encoding="utf-8") as f:
    schema = f.read()

# Crear base de datos
conn = sqlite3.connect("storage/lifetrack.db")
conn.executescript(schema)
conn.close()

print("Base de datos creada correctamente")
