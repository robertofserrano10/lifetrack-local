from flask import Blueprint, render_template
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked

claims_overview_bp = Blueprint("claims_overview", __name__)


@claims_overview_bp.route("/claims/overview")
def claims_overview():
    """
    Vista administrativa consolidada de todos los claims.
    Solo lectura.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                c.id AS claim_id,
                p.first_name,
                p.last_name
            FROM claims c
            JOIN patients p ON p.id = c.patient_id
            ORDER BY c.id
        """)
        claims = cur.fetchall()

        data = []

        for row in claims:
            claim_id = row["claim_id"]

            # Totales financieros
            cur.execute("""
                SELECT COALESCE(SUM(ch.amount), 0)
                FROM charges ch
                JOIN services s ON s.id = ch.service_id
                WHERE s.claim_id = ?
            """, (claim_id,))
            total_charge = float(cur.fetchone()[0])

            cur.execute("""
                SELECT COALESCE(SUM(a.amount_applied), 0)
                FROM applications a
                JOIN charges ch ON ch.id = a.charge_id
                JOIN services s ON s.id = ch.service_id
                WHERE s.claim_id = ?
            """, (claim_id,))
            total_applied = float(cur.fetchone()[0])

            cur.execute("""
                SELECT COALESCE(SUM(ad.amount), 0)
                FROM adjustments ad
                JOIN charges ch ON ch.id = ad.charge_id
                JOIN services s ON s.id = ch.service_id
                WHERE s.claim_id = ?
            """, (claim_id,))
            total_adjustments = float(cur.fetchone()[0])

            balance_due = total_charge - total_applied - total_adjustments

            data.append({
                "claim_id": claim_id,
                "patient": f"{row['first_name']} {row['last_name']}",
                "total_charge": total_charge,
                "total_applied": total_applied,
                "total_adjustments": total_adjustments,
                "balance_due": balance_due,
                "locked": is_claim_locked(claim_id),
            })

    return render_template(
        "claims/overview.html",
        claims=data
    )
