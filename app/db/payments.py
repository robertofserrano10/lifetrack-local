from datetime import datetime
from app.db.connection import get_connection

ALLOWED_METHODS = {"cash", "check", "eft", "other"}


def create_payment(amount: float, method: str, reference: str | None = None, received_date: str | None = None) -> int:
    """
    Crea un payment y devuelve su ID.
    - amount: monto recibido (ej. 150.00)
    - method: cash | check | eft | other
    - reference: opcional (ej. EOB-123, #cheque)
    - received_date: YYYY-MM-DD opcional; si None, usa hoy (UTC)
    """
    if amount is None or float(amount) <= 0:
        raise ValueError("amount debe ser > 0")
    if method not in ALLOWED_METHODS:
        raise ValueError(f"method inválido. Use uno de: {sorted(ALLOWED_METHODS)}")

    if received_date is None:
        received_date = datetime.utcnow().date().isoformat()

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO payments (amount, method, reference, received_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (float(amount), method, reference, received_date, now, now),
        )
        conn.commit()
        return cur.lastrowid


def get_payment_by_id(payment_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_payments(limit: int = 50):
    """
    Lista payments recientes (para debug/admin).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM payments
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        return [dict(r) for r in cur.fetchall()]


def update_payment(payment_id: int, amount: float, method: str, reference: str | None, received_date: str) -> bool:
    if amount is None or float(amount) <= 0:
        raise ValueError("amount debe ser > 0")
    if method not in ALLOWED_METHODS:
        raise ValueError(f"method inválido. Use uno de: {sorted(ALLOWED_METHODS)}")

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE payments
            SET amount = ?, method = ?, reference = ?, received_date = ?, updated_at = ?
            WHERE id = ?
            """,
            (float(amount), method, reference, received_date, now, int(payment_id)),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_payment(payment_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM payments WHERE id = ?", (int(payment_id),))
        conn.commit()
        return cur.rowcount > 0
