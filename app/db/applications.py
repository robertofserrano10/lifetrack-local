from datetime import datetime
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked


def create_application(
    payment_id: int,
    charge_id: int,
    amount_applied: float,
) -> int:
    """
    Aplica un pago a un charge específico.
    Representa una línea de un EOB.

    VALIDACIONES:
    - No permite aplicar más de lo disponible en el payment.
    - No permite aplicar más que el balance actual del charge.
    - No permite aplicar si el claim está congelado por snapshot.
    """

    if amount_applied is None or float(amount_applied) <= 0:
        raise ValueError("amount_applied debe ser > 0")

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()

        # =========================
        # 1. Obtener claim_id del charge
        # =========================
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

        # =========================
        # 2. Verificar bloqueo financiero
        # =========================
        if is_claim_locked(claim_id):
            raise ValueError("Claim está congelado por snapshot")

        # =========================
        # 3. VALIDAR PAYMENT DISPONIBLE
        # =========================
        cur.execute(
            "SELECT amount FROM payments WHERE id = ?",
            (payment_id,),
        )
        payment_row = cur.fetchone()
        if not payment_row:
            raise ValueError("Payment no existe")

        total_payment = float(payment_row["amount"])

        cur.execute(
            """
            SELECT COALESCE(SUM(amount_applied), 0)
            FROM applications
            WHERE payment_id = ?
            """,
            (payment_id,),
        )
        already_applied_payment = float(cur.fetchone()[0])

        available_payment = total_payment - already_applied_payment

        if float(amount_applied) > available_payment:
            raise ValueError("No hay suficiente monto disponible en el payment")

        # =========================
        # 4. VALIDAR BALANCE DEL CHARGE
        # =========================
        cur.execute(
            "SELECT amount FROM charges WHERE id = ?",
            (charge_id,),
        )
        charge_row = cur.fetchone()
        if not charge_row:
            raise ValueError("Charge no existe")

        total_charge = float(charge_row["amount"])

        cur.execute(
            """
            SELECT COALESCE(SUM(amount_applied), 0)
            FROM applications
            WHERE charge_id = ?
            """,
            (charge_id,),
        )
        already_applied_charge = float(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM adjustments
            WHERE charge_id = ?
            """,
            (charge_id,),
        )
        total_adjustments = float(cur.fetchone()[0])

        current_balance = total_charge - already_applied_charge - total_adjustments

        if float(amount_applied) > current_balance:
            raise ValueError("No se puede aplicar más del balance actual del charge")

        # =========================
        # 5. INSERTAR APPLICATION
        # =========================
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
