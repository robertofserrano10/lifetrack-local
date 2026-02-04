from datetime import datetime
from app.db.connection import get_connection


def create_application(
    payment_id: int,
    charge_id: int,
    amount_applied: float,
) -> int:
    """
    Aplica un pago a un charge específico.
    Representa una línea de un EOB.
    """
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO applications (
                payment_id,
                charge_id,
                amount_applied,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                payment_id,
                charge_id,
                float(amount_applied),
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_applications_by_charge(charge_id: int):
    """
    Lista todas las aplicaciones asociadas a un charge.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM applications
            WHERE charge_id = ?
            ORDER BY id
            """,
            (charge_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
