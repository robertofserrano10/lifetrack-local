import os

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Ruta absoluta al archivo SQLite
DB_PATH = os.path.join(BASE_DIR, "storage", "lifetrack.db")
