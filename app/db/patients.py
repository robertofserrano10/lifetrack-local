from datetime import datetime
from app.db.connection import get_connection
from app.db.event_ledger import log_event


def _ensure_patient_address_columns():
    """Migración automática — agrega columnas de dirección si no existen."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(patients)")
        cols = [r["name"] for r in cur.fetchall()]
        for col in ["address", "city", "state", "zip_code", "phone"]:
            if col not in cols:
                conn.execute(f"ALTER TABLE patients ADD COLUMN {col} TEXT")
        conn.commit()


def create_patient(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    sex: str = "U",
    marital_status: str = None,
    employment_status: str = None,
    student_status: str = None,
    address: str = None,
    city: str = None,
    state: str = None,
    zip_code: str = None,
    phone: str = None,
) -> int:
    _ensure_patient_address_columns()
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO patients (
                first_name, last_name, date_of_birth,
                sex, marital_status, employment_status, student_status,
                address, city, state, zip_code, phone,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            first_name, last_name, date_of_birth,
            sex, marital_status, employment_status, student_status,
            address, city, state, zip_code, phone,
            now, now
        ))
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
    _ensure_patient_address_columns()
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
    address: str = None,
    city: str = None,
    state: str = None,
    zip_code: str = None,
    phone: str = None,
):
    _ensure_patient_address_columns()
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE patients SET
                first_name = ?, last_name = ?, date_of_birth = ?,
                sex = ?, marital_status = ?, employment_status = ?,
                student_status = ?, address = ?, city = ?,
                state = ?, zip_code = ?, phone = ?, updated_at = ?
            WHERE id = ?
        """, (
            first_name, last_name, date_of_birth,
            sex, marital_status, employment_status, student_status,
            address, city, state, zip_code, phone,
            now, patient_id
        ))
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