from flask import Blueprint, render_template
import sqlite3

from app.config import DB_PATH
from app.db.cms1500_snapshot import get_latest_snapshot_by_claim
from app.db.claims import get_claim_financial_status

from app.security.auth import login_required, role_required


claims_list_bp = Blueprint(
    "claims_list",
    __name__,
    url_prefix="/admin",
)


@claims_list_bp.route("/claims")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION", "DRA")
def claims_list():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.id,
            c.claim_number,
            c.status,
            p.first_name,
            p.last_name
        FROM claims c
        JOIN patients p ON p.id = c.patient_id
        ORDER BY c.id DESC
    """)

    rows = cur.fetchall()

    claims = []

    for r in rows:

        snapshot = get_latest_snapshot_by_claim(r["id"])

        financial = get_claim_financial_status(r["id"])

        claims.append({
            "id": r["id"],
            "claim_number": r["claim_number"],
            "patient": f'{r["first_name"]} {r["last_name"]}',
            "status": r["status"],
            "financial_status": financial["status"],
            "locked": snapshot is not None,
            "snapshot_version": snapshot["version_number"] if snapshot else None
        })

    conn.close()

    return render_template(
        "admin/claims_list.html",
        claims=claims
    )