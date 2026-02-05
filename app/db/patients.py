from datetime import datetime
from app.db.connection import get_connection


def create_patient(first_name: str, last_name: str, date_of_birth: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (first_name, last_name, date_of_birth, now, now),
        )
        conn.commit()
        return cur.lastrowid


def get_patient_by_id(patient_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_patient(patient_id: int, first_name: str, last_name: str, date_of_birth: str):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE patients
            SET first_name = ?, last_name = ?, date_of_birth = ?, updated_at = ?
            WHERE id = ?
            """,
            (first_name, last_name, date_of_birth, now, patient_id),
        )
        conn.commit()
        return cur.rowcount > 0
