from flask import Blueprint, render_template
import sqlite3

from app.config import DB_PATH
from app.security.auth import login_required, role_required

dashboard_admin_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/admin",
)

@dashboard_admin_bp.route("/dashboard")
def dashboard():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM claims")
    total_claims = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM claims WHERE status='SUBMITTED'")
    submitted = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM claims WHERE status='PAID'")
    paid = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM cms1500_snapshots")
    snapshots = cur.fetchone()[0]

    conn.close()

    stats = {
        "total_claims": total_claims,
        "submitted": submitted,
        "paid": paid,
        "snapshots": snapshots,
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats
    )


@dashboard_admin_bp.route("/ux-dashboard")
@login_required
@role_required("ADMIN", "DRA", "FACTURADOR")
def ux_dashboard():
    ux_todos = [
        "Mejorar formularios con estados y ayuda al usuario",
        "Agregar microcopy para flujo de encounters/services",
        "Destacar eventos de auditoría y filtros avanzados",
        "Agregar atajos de navegación y feedback visual",
    ]
    return render_template("admin/ux_dashboard.html", ux_todos=ux_todos)


@dashboard_admin_bp.route("/doctor-dashboard")
@login_required
@role_required("ADMIN", "DRA")
def doctor_dashboard():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Summary numbers
    cur.execute("SELECT COUNT(*) FROM encounters")
    total_encounters = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM services")
    total_services = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM claims WHERE status='SUBMITTED'")
    submitted_claims = cur.fetchone()[0]

    # Provider-focused metrics
    cur.execute(
        """
        SELECT
            u.id,
            u.username,
            COALESCE(COUNT(DISTINCT e.id), 0) AS encounter_count,
            COALESCE(SUM(CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END), 0) AS service_count
        FROM users u
        LEFT JOIN encounters e ON e.provider_id = u.id
        LEFT JOIN claims c ON c.patient_id = e.patient_id
        LEFT JOIN services s ON s.claim_id = c.id
        WHERE u.role IN ('DRA', 'ADMIN')
        GROUP BY u.id
        ORDER BY encounter_count DESC
        """,
    )
    provider_rows = cur.fetchall()

    conn.close()

    return render_template(
        "admin/doctor_dashboard.html",
        total_encounters=total_encounters,
        total_services=total_services,
        submitted_claims=submitted_claims,
        provider_rows=provider_rows,
    )
