from datetime import datetime
from app.db.connection import get_connection
from app.db.event_ledger import log_event


def create_patient(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    sex: str = "U",
    marital_status: str = None,
    employment_status: str = None,
    student_status: str = None,
) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO patients (
                first_name, last_name, date_of_birth,
                sex, marital_status, employment_status, student_status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, date_of_birth,
              sex, marital_status, employment_status, student_status,
              now, now))
        conn.commit()
        patient_id = cur.lastrowid

    log_event(
        entity_type="patient",
        entity_id=patient_id,
        event_type="patient_created",
        event_data={"name": f"{first_name} {last_name}"},
    )
    return patient_id


def get_patient_by_id(patient_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_patient(
    patient_id: int,
    first_name: str,
    last_name: str,
    date_of_birth: str,
    sex: str = "U",
    marital_status: str = None,
    employment_status: str = None,
    student_status: str = None,
):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE patients
            SET first_name = ?, last_name = ?, date_of_birth = ?,
                sex = ?, marital_status = ?, employment_status = ?,
                student_status = ?, updated_at = ?
            WHERE id = ?
        """, (first_name, last_name, date_of_birth,
              sex, marital_status, employment_status, student_status,
              now, patient_id))
        conn.commit()
        updated = cur.rowcount > 0

    if updated:
        log_event(
            entity_type="patient",
            entity_id=patient_id,
            event_type="patient_updated",
            event_data={"name": f"{first_name} {last_name}"},
        )
    return updated


def get_all_patients():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, first_name, last_name, date_of_birth, sex
            FROM patients ORDER BY last_name, first_name
        """)
        rows = cur.fetchall()
        return [dict(r) for r in rows]