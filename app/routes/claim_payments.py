from flask import Blueprint, render_template
from app.db.connection import get_connection

claim_payments_bp = Blueprint("claim_payments", __name__)


@claim_payments_bp.route("/claims/<int:claim_id>/payments")
def claim_payments_view(claim_id):
    with get_connection() as conn:
        cur = conn.cursor()

        # Payments vinculados al claim vía applications → charges → services
        cur.execute("""
            SELECT DISTINCT p.*
            FROM payments p
            JOIN applications a ON a.payment_id = p.id
            JOIN charges c ON c.id = a.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            ORDER BY p.id DESC
        """, (claim_id,))
        payments = [dict(r) for r in cur.fetchall()]

        # Applications por charge
        cur.execute("""
            SELECT
                a.id AS application_id,
                a.amount_applied,
                a.payment_id,
                c.id AS charge_id
            FROM applications a
            JOIN charges c ON c.id = a.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            ORDER BY a.id
        """, (claim_id,))
        applications = [dict(r) for r in cur.fetchall()]

    return render_template(
        "claims/payments.html",
        claim_id=claim_id,
        payments=payments,
        applications=applications,
    )
