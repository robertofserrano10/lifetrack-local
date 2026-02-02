from app.db.connection import get_connection


def create_patient(first_name, last_name, date_of_birth=None):
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
            dict(row) for row in rows
        ]


def get_patient_by_id(patient_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, first_name, last_name, date_of_birth FROM patients WHERE id = ?",
            (patient_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_patient(patient_id, first_name, last_name, date_of_birth=None):
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


def delete_patient(patient_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        return cur.rowcount > 0
