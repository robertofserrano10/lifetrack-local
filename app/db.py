import sqlite3
from .config import DB_PATH


def get_connection():
    """
    Devuelve una conexión a la base de datos SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_patient(first_name: str, last_name: str, date_of_birth: str | None = None) -> int:
    """
    Inserta un paciente y devuelve su ID.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (first_name, last_name, date_of_birth) VALUES (?, ?, ?)",
            (first_name, last_name, date_of_birth),
        )
        conn.commit()
        return cur.lastrowid


def list_patients():
    """
    Devuelve una lista de todos los pacientes registrados.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, first_name, last_name, date_of_birth FROM patients ORDER BY id"
        )
        rows = cur.fetchall()

        patients = []
        for row in rows:
            patients.append({
                "id": row["id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "date_of_birth": row["date_of_birth"],
            })

        return patients
