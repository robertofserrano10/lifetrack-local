from flask import Blueprint, render_template, abort
import sqlite3
from app.config import DB_PATH

from app.security.auth import login_required, role_required


patients_admin_bp = Blueprint(
    "patients_admin",
    __name__,
    url_prefix="/admin/patients",
)


# =========================================================
# Patients list
# =========================================================
@patients_admin_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def patients_list():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            first_name,
            last_name,
            date_of_birth,
            sex,
            created_at
        FROM patients
        ORDER BY last_name, first_name
        """
    )

    patients = cur.fetchall()

    conn.close()

    return render_template(
        "admin/patients_list.html",
        patients=patients,
    )


# =========================================================
# Patient detail
# =========================================================
@patients_admin_bp.route("/<int:patient_id>")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def patient_detail(patient_id: int):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # patient
    cur.execute(
        """
        SELECT *
        FROM patients
        WHERE id = ?
        """,
        (patient_id,),
    )

    patient = cur.fetchone()

    if not patient:
        conn.close()
        abort(404)

    # coverages
    cur.execute(
        """
        SELECT
            id,
            insurer_name,
            plan_name,
            policy_number,
            start_date
        FROM coverages
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,),
    )

    coverages = cur.fetchall()

    # claims
    cur.execute(
        """
        SELECT
            id,
            claim_number,
            status,
            created_at
        FROM claims
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,),
    )

    claims = cur.fetchall()

    conn.close()

    return render_template(
        "admin/patient_detail.html",
        patient=patient,
        coverages=coverages,
        claims=claims,
    )