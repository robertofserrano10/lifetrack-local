"""
reset_to_production.py — P1-1: Limpieza de base de datos para producción

ADVERTENCIA: Este script elimina TODOS los datos de pacientes,
claims y expedientes. Usalo SOLO para limpiar datos de prueba
antes del primer uso en produccion. Esta accion NO se puede deshacer.
"""

import os
import sys
import sqlite3

# Ruta a la DB (relativa al directorio raíz del proyecto)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "storage", "lifetrack.db")

# Orden de borrado respetando FK constraints (dependientes primero)
TABLES_TO_CLEAR = [
    "cms1500_snapshots",
    "applications",
    "adjustments",
    "charges",
    "services",
    "payments",
    "claims",
    "progress_notes",
    "encounters",
    "visit_sessions",
    "appointments",
    "coverages",
    "patients",
    "event_ledger",
]

# Tablas que se conservan intactas
TABLES_PRESERVED = ["users", "provider_settings"]


def main():
    print()
    print("=" * 65)
    print("  ADVERTENCIA: Este script elimina TODOS los datos de pacientes,")
    print("  claims y expedientes. Usalo SOLO para limpiar datos de prueba")
    print("  antes del primer uso en produccion. Esta accion NO se puede deshacer.")
    print("=" * 65)
    print()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: No se encontro la base de datos en: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    # Contar registros antes de borrar
    print("Registros que seran eliminados:")
    print("-" * 40)
    counts = {}
    total = 0
    for table in TABLES_TO_CLEAR:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
        except sqlite3.OperationalError:
            count = 0
            print(f"  {table:<25}  (tabla no existe, omitida)")
            counts[table] = None
            continue
        counts[table] = count
        total += count
        print(f"  {table:<25}  {count:>6} registro(s)")

    print("-" * 40)
    print(f"  {'TOTAL':<25}  {total:>6} registro(s)")
    print()

    # Mostrar lo que se conserva
    print("Tablas que se conservan intactas:")
    for table in TABLES_PRESERVED:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table:<25}  {count:>6} registro(s)  [CONSERVADO]")
        except sqlite3.OperationalError:
            print(f"  {table:<25}  (tabla no existe)")
    print()

    if total == 0:
        print("No hay datos de prueba. La base de datos ya esta limpia.")
        conn.close()
        sys.exit(0)

    # Confirmación
    respuesta = input('Escribe SI para confirmar: ').strip()
    if respuesta != "SI":
        print()
        print("Operacion cancelada. No se elimino ningun dato.")
        conn.close()
        sys.exit(0)

    print()
    print("Eliminando datos...")
    print("-" * 40)

    deleted = {}
    for table in TABLES_TO_CLEAR:
        if counts.get(table) is None:
            deleted[table] = 0
            continue
        try:
            cur.execute(f"DELETE FROM {table}")
            deleted[table] = cur.rowcount
            print(f"  {table:<25}  {deleted[table]:>6} registro(s) eliminados")
        except sqlite3.OperationalError as e:
            print(f"  {table:<25}  ERROR: {e}")
            deleted[table] = 0

    # Resetear secuencias de autoincrement
    tables_existing = [t for t in TABLES_TO_CLEAR if counts.get(t) is not None]
    if tables_existing:
        placeholders = ",".join(f"'{t}'" for t in tables_existing)
        try:
            cur.execute(
                f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})"
            )
        except sqlite3.OperationalError:
            # sqlite_sequence no existe si nunca se insertó nada con AUTOINCREMENT
            pass

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    print("-" * 40)
    total_deleted = sum(v for v in deleted.values())
    print(f"  {'TOTAL ELIMINADOS':<25}  {total_deleted:>6} registro(s)")
    print()
    print("Secuencias de autoincrement reseteadas.")
    print()
    print("Base de datos lista para produccion.")
    print()


if __name__ == "__main__":
    main()
