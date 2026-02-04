from datetime import datetime
from app.db.connection import get_connection


def create_adjustment(
    charge_id: int,
    amount: float,
    reason: str = None,
) -> int:
    """
    Crea un adjustment (write-off, deductible, no cubierto, etc).
    """
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO adjustments (
                charge_id,
                amount,
                reason,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                charge_id,
                float(amount),
                reason,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_adjustments_by_charge(charge_id: int):
    """
    Lista todos los adjustments de un charge.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM adjustments
            WHERE charge_id = ?
            ORDER BY id
            """,
            (charge_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
