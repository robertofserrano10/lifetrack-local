from datetime import datetime
from app.db.connection import get_connection


def create_service(
    claim_id: int,
    service_date: str,
    cpt_code: str,
    units: int,
    diagnosis_code: str,
    description: str,
    outside_lab_20: int = 0,
    lab_charges_20: float | None = None,
) -> int:
    """
    Crea un service asociado a un claim.
    Box 20 (outside lab + lab charges) es service-level.
    """
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO services (
                claim_id,
                service_date,
                cpt_code,
                units,
                diagnosis_code,
                description,
                outside_lab_20,
                lab_charges_20,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                service_date,
                cpt_code,
                int(units),
                diagnosis_code,
                description,
                int(outside_lab_20),
                lab_charges_20,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def update_service_box20(
    service_id: int,
    outside_lab_20: int,
    lab_charges_20: float | None,
) -> bool:
    """
    Actualiza Box 20 a nivel service.
    """
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE services
            SET outside_lab_20 = ?, lab_charges_20 = ?, updated_at = ?
            WHERE id = ?
            """,
            (int(outside_lab_20), lab_charges_20, now, service_id),
        )
        conn.commit()
        return cur.rowcount > 0
