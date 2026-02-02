import sqlite3
from .config import DB_PATH


def get_connection():
    """
    Devuelve una conexión a la base de datos SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
# PATIENTS
# ======================================================
def create_patient(first_name: str, last_name: str, date_of_birth: str | None = None) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (first_name, last_name, date_of_birth) VALUES (?, ?, ?)",
            (first_name, last_name, date_of_birth),
        )
        conn.commit()
        return cur.lastrowid


def list_patients():
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


def get_patient_by_id(patient_id: int):
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


def update_patient(
    patient_id: int,
    first_name: str,
    last_name: str,
    date_of_birth: str | None = None,
) -> bool:
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


def delete_patient(patient_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        return cur.rowcount > 0


# ======================================================
# COVERAGES
# ======================================================
def create_coverage(
    patient_id: int,
    insurer_name: str,
    plan_name: str | None,
    policy_number: str | None,
    group_number: str | None,
    insured_id: str | None,
    start_date: str | None,
    end_date: str | None,
) -> int:
    """
    Crea una cobertura asociada a un paciente y devuelve su ID.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO coverages (
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_coverages_by_patient(patient_id: int):
    """
    Devuelve todas las coberturas de un paciente.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date
            FROM coverages
            WHERE patient_id = ?
            ORDER BY id
            """,
            (patient_id,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row["id"],
                "patient_id": row["patient_id"],
                "insurer_name": row["insurer_name"],
                "plan_name": row["plan_name"],
                "policy_number": row["policy_number"],
                "group_number": row["group_number"],
                "insured_id": row["insured_id"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
            }
            for row in rows
        ]


def get_coverage_by_id(coverage_id: int):
    """
    Devuelve una cobertura por ID o None si no existe.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date
            FROM coverages
            WHERE id = ?
            """,
            (coverage_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "patient_id": row["patient_id"],
            "insurer_name": row["insurer_name"],
            "plan_name": row["plan_name"],
            "policy_number": row["policy_number"],
            "group_number": row["group_number"],
            "insured_id": row["insured_id"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
        }
