from flask import Blueprint, render_template
import sqlite3
from app.config import DB_PATH

from app.security.auth import login_required, role_required


finances_admin_bp = Blueprint(
    "finances_admin",
    __name__,
    url_prefix="/admin/finances",
)


@finances_admin_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR")
def finances_dashboard():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # =========================
    # CHARGES
    # =========================
    cur.execute("""
        SELECT
            charges.id,
            charges.amount,
            services.service_date,
            services.cpt_code,
            claims.claim_number
        FROM charges
        JOIN services ON charges.service_id = services.id
        JOIN claims ON services.claim_id = claims.id
        ORDER BY charges.id DESC
    """)

    charges = cur.fetchall()

    # =========================
    # PAYMENTS
    # =========================
    cur.execute("""
        SELECT
            payments.id,
            payments.amount,
            payments.method,
            payments.reference,
            payments.received_date
        FROM payments
        ORDER BY payments.id DESC
    """)

    payments = cur.fetchall()

    # =========================
    # ADJUSTMENTS
    # =========================
    cur.execute("""
        SELECT
            adjustments.id,
            adjustments.amount,
            adjustments.reason,
            claims.claim_number
        FROM adjustments
        JOIN charges ON adjustments.charge_id = charges.id
        JOIN services ON charges.service_id = services.id
        JOIN claims ON services.claim_id = claims.id
        ORDER BY adjustments.id DESC
    """)

    adjustments = cur.fetchall()

    conn.close()

    return render_template(
        "admin/finances_dashboard.html",
        charges=charges,
        payments=payments,
        adjustments=adjustments
    )