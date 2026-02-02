import sqlite3
from .config import DB_PATH


def get_connection():
    """
    Devuelve una conexión a la base de datos SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# PATIENTS - CREATE
# =========================
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


# =========================
# PATIENTS - READ (LIST)
# =========================
def list_patients():
    """
    Devuelve una lista de todos los pacientes.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, first_name, last_name, date_of_birth FROM patients ORDER BY id"
        )
        rows = cur.fetchall()

        return [
            {
                "id": row["id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "date_of_birth": row["date_of_birth"],
            }
            for row in rows
        ]


# =========================
# PATIENTS - READ (BY ID)
# =========================
def get_patient_by_id(patient_id: int):
    """
    Devuelve un paciente por ID o None si no existe.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, first_name, last_name, date_of_birth FROM patients WHERE id = ?",
            (patient_id,),
        )
        row = cur.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "date_of_birth": row["date_of_birth"],
        }


# =========================
# PATIENTS - UPDATE
# =========================
def update_patient(
    patient_id: int,
    first_name: str,
    last_name: str,
    date_of_birth: str | None = None,
) -> bool:
    """
    Actualiza un paciente.
    Devuelve True si se actualizó, False si no existe.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE patients
            SET first_name = ?, last_name = ?, date_of_birth = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (first_name, last_name, date_of_birth, patient_id),
        )
        conn.commit()
        return cur.rowcount > 0


# =========================
# PATIENTS - DELETE
# =========================
def delete_patient(patient_id: int) -> bool:
    """
    Elimina un paciente por ID.
    Devuelve True si se eliminó, False si no existe.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM patients WHERE id = ?",
            (patient_id,),
        )
        conn.commit()
        return cur.rowcount > 0
