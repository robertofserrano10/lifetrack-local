from flask import Blueprint, render_template, request, redirect, url_for, abort
import sqlite3
from app.config import DB_PATH

from app.security.auth import login_required, role_required


services_admin_bp = Blueprint(
    "services_admin",
    __name__,
    url_prefix="/admin/services",
)


# =========================================================
# Services list
# =========================================================
@services_admin_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def services_list():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            services.id,
            services.service_date,
            services.cpt_code,
            services.units_24g,
            services.charge_amount_24f,
            claims.claim_number,
            patients.first_name,
            patients.last_name
        FROM services
        JOIN claims ON services.claim_id = claims.id
        JOIN patients ON claims.patient_id = patients.id
        ORDER BY services.service_date DESC
        """
    )

    services = cur.fetchall()

    conn.close()

    return render_template(
        "admin/services_list.html",
        services=services
    )


# =========================================================
# Create service
# =========================================================
@services_admin_bp.route("/create/<int:claim_id>", methods=["GET","POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def create_service(claim_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            claims.id,
            claims.claim_number,
            patients.id as patient_id,
            patients.first_name,
            patients.last_name
        FROM claims
        JOIN patients ON claims.patient_id = patients.id
        WHERE claims.id = ?
        """,
        (claim_id,),
    )

    claim = cur.fetchone()

    if not claim:
        conn.close()
        abort(404)

    if request.method == "POST":

        service_date = request.form.get("service_date")
        cpt_code = request.form.get("cpt_code")
        units = request.form.get("units")
        charge_amount = request.form.get("charge_amount")

        cur.execute(
            """
            INSERT INTO services (
                claim_id,
                service_date,
                cpt_code,
                units_24g,
                charge_amount_24f
            )
            VALUES (?,?,?,?,?)
            """,
            (
                claim_id,
                service_date,
                cpt_code,
                units,
                charge_amount
            ),
        )

        service_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO charges (
                service_id,
                amount
            )
            VALUES (?,?)
            """,
            (
                service_id,
                charge_amount
            ),
        )

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "patients_admin.patient_detail",
                patient_id=claim["patient_id"]
            )
        )

    conn.close()

    return render_template(
        "admin/service_create.html",
        claim=claim
    )