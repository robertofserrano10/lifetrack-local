from datetime import datetime
from app.db.connection import get_connection


def create_service(
    claim_id: int,
    service_date: str,
    cpt_code: str,
    units: int,
    diagnosis_code: str,
    description: str,
) -> int:
    """
    Crea un service asociado directamente a un claim.
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
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                service_date,
                cpt_code,
                units,
                diagnosis_code,
                description,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid
