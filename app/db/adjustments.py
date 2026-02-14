from datetime import datetime
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked


def create_adjustment(
    charge_id: int,
    amount: float,
    reason: str = None,
) -> int:
    """
    Crea un adjustment (write-off, deductible, no cubierto, etc).

    REGLAS:
    - Charge debe existir.
    - amount debe ser > 0.
    - No se permite si el claim está congelado por snapshot.
    """

    if amount is None or float(amount) <= 0:
        raise ValueError("amount debe ser > 0")

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Validar que el charge exista y obtener claim_id
        cur.execute(
            """
            SELECT s.claim_id
            FROM charges c
            JOIN services s ON s.id = c.service_id
            WHERE c.id = ?
            """,
            (charge_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Charge no existe")

        claim_id = row["claim_id"]

        # 2) Bloqueo financiero por snapshot
        if is_claim_locked(claim_id):
            raise ValueError("Claim está congelado por snapshot")

        # 3) Insertar adjustment
        cur.execute(
            """
            INSERT INTO adjustments (charge_id, amount, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (charge_id, float(amount), reason, now),
        )
        conn.commit()
        return cur.lastrowid


def list_adjustments_by_charge(charge_id: int):
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
        return [dict(r) for r in cur.fetchall()]
