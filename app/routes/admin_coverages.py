from flask import Blueprint, render_template, request, redirect, url_for, abort
import sqlite3

from app.config import DB_PATH
from app.security.auth import login_required, role_required


coverages_admin_bp = Blueprint(
    "coverages_admin",
    __name__,
    url_prefix="/admin/coverages",
)


# =========================================================
# Create coverage
# =========================================================
@coverages_admin_bp.route("/create/<int:patient_id>", methods=["GET","POST"])
@login_required
@role_required("ADMIN", "RECEPCION", "FACTURADOR")
def create_coverage(patient_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, first_name, last_name
        FROM patients
        WHERE id = ?
        """,
        (patient_id,),
    )

    patient = cur.fetchone()

    if not patient:
        conn.close()
        abort(404)

    if request.method == "POST":

        insurer_name = request.form.get("insurer_name")
        plan_name = request.form.get("plan_name")
        policy_number = request.form.get("policy_number")
        start_date = request.form.get("start_date")

        cur.execute(
            """
            INSERT INTO coverages (
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                start_date
            )
            VALUES (?,?,?,?,?)
            """,
            (patient_id, insurer_name, plan_name, policy_number, start_date),
        )

        conn.commit()
        conn.close()

        return redirect(
            url_for("patients_admin.patient_detail", patient_id=patient_id)
        )

    conn.close()

    return render_template(
        "admin/coverage_create.html",
        patient=patient
    )