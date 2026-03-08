from flask import Blueprint, render_template
import sqlite3
from app.config import DB_PATH

from app.security.auth import login_required, role_required


services_admin_bp = Blueprint(
    "services_admin",
    __name__,
    url_prefix="/admin/services",
)


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