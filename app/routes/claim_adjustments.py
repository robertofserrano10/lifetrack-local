from flask import Blueprint, render_template
from app.db.connection import get_connection

claim_adjustments_bp = Blueprint("claim_adjustments", __name__)

@claim_adjustments_bp.route("/claims/<int:claim_id>/adjustments")
def claim_adjustments_view(claim_id):

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                adj.id,
                adj.charge_id,
                adj.amount,
                adj.reason,
                adj.created_at
            FROM adjustments adj
            JOIN charges c ON c.id = adj.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            ORDER BY adj.id DESC
        """, (claim_id,))

        adjustments = [dict(r) for r in cur.fetchall()]

    return render_template(
        "claims/adjustments.html",
        claim_id=claim_id,
        adjustments=adjustments,
    )
