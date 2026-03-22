import sqlite3
from datetime import datetime, timezone
from app.config import DB_PATH
from app.db.event_ledger import log_event


def _table_has_column(conn, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return column in [r[1] for r in cur.fetchall()]


def _ensure_ready_for_billing_columns():
    conn = sqlite3.connect(DB_PATH)
    try:
        if not _table_has_column(conn, "encounters", "ready_for_billing"):
            conn.execute("ALTER TABLE encounters ADD COLUMN ready_for_billing INTEGER DEFAULT 0")
        if not _table_has_column(conn, "encounters", "ready_for_billing_at"):
            conn.execute("ALTER TABLE encounters ADD COLUMN ready_for_billing_at TEXT")
        if not _table_has_column(conn, "encounters", "ready_for_billing_by"):
            conn.execute("ALTER TABLE encounters ADD COLUMN ready_for_billing_by TEXT")
        conn.commit()
    finally:
        conn.close()


def mark_ready_for_billing(encounter_id: int, marked_by: str):
    _ensure_ready_for_billing_columns()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()

        # Load encounter
        cur.execute("SELECT * FROM encounters WHERE id = ?", (encounter_id,))
        encounter = cur.fetchone()
        if not encounter:
            raise ValueError("Encounter no encontrado")

        # Validate: signed progress note exists
        cur.execute(
            "SELECT id FROM progress_notes WHERE encounter_id = ? AND signed = 1 LIMIT 1",
            (encounter_id,),
        )
        if not cur.fetchone():
            raise ValueError("La nota de progreso no ha sido firmada. Debe firmar la nota antes de marcar Ready for Billing.")

        # Validate: referral requirement via coverage
        patient_id = encounter["patient_id"]
        encounter_date = encounter["encounter_date"]

        cur.execute(
            """
            SELECT c.referral_required
            FROM coverages c
            WHERE c.patient_id = ?
            ORDER BY c.id DESC
            LIMIT 1
            """,
            (patient_id,),
        )
        coverage = cur.fetchone()

        if coverage and coverage["referral_required"]:
            cur.execute(
                """
                SELECT referral_on_file
                FROM visit_sessions
                WHERE patient_id = ? AND appointment_date = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (patient_id, encounter_date),
            )
            vs = cur.fetchone()
            referral_on_file = vs["referral_on_file"] if vs else 0
            if not referral_on_file:
                raise ValueError("El plan requiere referido pero no hay referido registrado (referral_on_file = 0). Actualice el check-in antes de continuar.")

        # All validations passed — mark ready
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            UPDATE encounters
            SET ready_for_billing = 1,
                ready_for_billing_at = ?,
                ready_for_billing_by = ?
            WHERE id = ?
            """,
            (now, marked_by, encounter_id),
        )
        conn.commit()
    finally:
        conn.close()

    log_event(
        entity_type="encounter",
        entity_id=encounter_id,
        event_type="ready_for_billing_marked",
        event_data={"marked_by": marked_by},
    )


def get_all_encounters():
    _ensure_ready_for_billing_columns()

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
    _ensure_ready_for_billing_columns()
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
    _ensure_ready_for_billing_columns()
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
    _ensure_ready_for_billing_columns()
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
