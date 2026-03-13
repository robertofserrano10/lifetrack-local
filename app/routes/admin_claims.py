from flask import Blueprint, render_template, request, redirect, url_for, abort
import sqlite3

from app.config import DB_PATH
from app.security.auth import login_required, role_required


claims_admin_bp = Blueprint(
    "claims_admin",
    __name__,
    url_prefix="/admin/claims",
)


# =========================================================
# Create claim
# =========================================================
@claims_admin_bp.route("/create/<int:coverage_id>", methods=["GET","POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def create_claim(coverage_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            p.id as patient_id,
            p.first_name,
            p.last_name,
            c.insurer_name
        FROM coverages c
        JOIN patients p ON p.id = c.patient_id
        WHERE c.id = ?
        """,
        (coverage_id,),
    )

    coverage = cur.fetchone()

    if not coverage:
        conn.close()
        abort(404)

    if request.method == "POST":

        claim_number = request.form.get("claim_number")

        cur.execute(
            """
            INSERT INTO claims (
                patient_id,
                coverage_id,
                claim_number,
                status
            )
            VALUES (?,?,?,?)
            """,
            (
                coverage["patient_id"],
                coverage_id,
                claim_number,
                "draft"
            ),
        )

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "patients_admin.patient_detail",
                patient_id=coverage["patient_id"]
            )
        )

    conn.close()

    return render_template(
        "admin/claim_create.html",
        coverage=coverage
    )