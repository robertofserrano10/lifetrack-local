from app.db.connection import get_connection


def get_charge_balance(charge_id: int) -> dict:
    """
    Calcula el balance de un charge:
    charge.amount - sum(applications.amount_applied)
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT amount FROM charges WHERE id = ?",
            (charge_id,),
        )
        charge = cur.fetchone()
        if not charge:
            raise ValueError("Charge no existe")

        total_charge = float(charge["amount"])

        cur.execute(
            """
            SELECT COALESCE(SUM(amount_applied), 0)
            FROM applications
            WHERE charge_id = ?
            """,
            (charge_id,),
        )
        total_applied = float(cur.fetchone()[0])

        return {
            "charge_id": charge_id,
            "total_charge": total_charge,
            "total_applied": total_applied,
            "balance": total_charge - total_applied,
        }


def get_claim_balance(claim_id: int) -> dict:
    """
    Calcula el balance total de un claim sumando balances de sus charges.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.id
            FROM charges c
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            """,
            (claim_id,),
        )
        charge_ids = [row["id"] for row in cur.fetchall()]

    balances = [get_charge_balance(cid) for cid in charge_ids]

    return {
        "claim_id": claim_id,
        "charges": balances,
        "total_charge": sum(b["total_charge"] for b in balances),
        "total_applied": sum(b["total_applied"] for b in balances),
        "balance_due": sum(b["balance"] for b in balances),
    }
