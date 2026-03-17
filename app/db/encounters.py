import sqlite3
from app.config import DB_PATH
from app.db.event_ledger import log_event


def get_all_encounters():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            e.encounter_date,
            e.status,
            e.provider_id,
            p.first_name,
            p.last_name,
            u.username AS provider_username
        FROM encounters e
        JOIN patients p ON p.id = e.patient_id
        LEFT JOIN users u ON u.id = e.provider_id
        ORDER BY e.encounter_date DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def create_encounter(patient_id: int, encounter_date: str, status: str = 'OPEN', provider_id: int | None = None) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO encounters (patient_id, provider_id, encounter_date, status, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (patient_id, provider_id, encounter_date, status),
    )
    conn.commit()
    encounter_id = cur.lastrowid
    conn.close()

    # Event audit trail for clinical encounter creation
    log_event(
        entity_type="encounter",
        entity_id=encounter_id,
        event_type="encounter_created",
        event_data={
            "patient_id": patient_id,
            "provider_id": provider_id,
            "encounter_date": encounter_date,
            "status": status,
        },
    )

    return encounter_id


def get_encounter_by_id(encounter_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.*, p.first_name, p.last_name, u.username AS provider_username
        FROM encounters e
        JOIN patients p ON p.id = e.patient_id
        LEFT JOIN users u ON u.id = e.provider_id
        WHERE e.id = ?
        """,
        (encounter_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_claims_by_patient(patient_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, claim_number, status
        FROM claims
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
