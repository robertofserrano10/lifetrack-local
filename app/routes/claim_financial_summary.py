from flask import Blueprint, render_template
from app.db.balances import get_claim_balance
from app.db.connection import get_connection

claim_financial_summary_bp = Blueprint(
    "claim_financial_summary",
    __name__
)


@claim_financial_summary_bp.route("/claims/<int:claim_id>/financial")
def claim_financial_summary(claim_id):

    balance = get_claim_balance(claim_id)

    with get_connection() as conn:
        cur = conn.cursor()

        # Charges
        cur.execute("""
            SELECT c.*
            FROM charges c
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
        """, (claim_id,))
        charges = cur.fetchall()

        # Payments
        cur.execute("""
            SELECT p.*
            FROM payments p
            JOIN applications a ON a.payment_id = p.id
            JOIN charges c ON c.id = a.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            GROUP BY p.id
        """, (claim_id,))
        payments = cur.fetchall()

        # Applications
        cur.execute("""
            SELECT a.*
            FROM applications a
            JOIN charges c ON c.id = a.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
        """, (claim_id,))
        applications = cur.fetchall()

        # Adjustments
        cur.execute("""
            SELECT adj.*
            FROM adjustments adj
            JOIN charges c ON c.id = adj.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
        """, (claim_id,))
        adjustments = cur.fetchall()

    return render_template(
        "claims/financial_summary.html",
        claim_id=claim_id,
        balance=balance,
        charges=charges,
        payments=payments,
        applications=applications,
        adjustments=adjustments,
    )
