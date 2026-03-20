from flask import Blueprint, render_template, session as flask_session
import sqlite3
from datetime import datetime
from app.config import DB_PATH
from app.security.auth import login_required, role_required

dashboard_admin_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/admin",
)


def _get_role():
    return flask_session.get("role", "")


@dashboard_admin_bp.route("/dashboard")
@login_required
def dashboard():
    role = _get_role()
    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if role == "RECEPCION":
        # ── RECEPCIÓN: pacientes de hoy, sala de espera
        try:
            cur.execute("""
                SELECT vs.*, p.first_name, p.last_name
                FROM visit_sessions vs
                JOIN patients p ON p.id = vs.patient_id
                WHERE vs.appointment_date = ?
                ORDER BY vs.created_at ASC
            """, (today,))
            sessions_today = [dict(r) for r in cur.fetchall()]
        except Exception:
            sessions_today = []

        waiting   = [s for s in sessions_today if s["status"] in ("CHECKED_IN","WAITING")]
        in_session= [s for s in sessions_today if s["status"] == "IN_SESSION"]
        completed = [s for s in sessions_today if s["status"] == "COMPLETED"]

        cur.execute("SELECT COUNT(*) AS n FROM patients")
        total_patients = cur.fetchone()["n"]

        conn.close()
        return render_template("admin/dashboard_recepcion.html",
            today=today,
            waiting=waiting,
            in_session=in_session,
            completed=completed,
            total_patients=total_patients,
        )

    elif role == "DRA":
        # ── DOCTORA: notas sin firmar, encounters de hoy
        try:
            cur.execute("""
                SELECT vs.*, p.first_name, p.last_name
                FROM visit_sessions vs
                JOIN patients p ON p.id = vs.patient_id
                WHERE vs.appointment_date = ?
                AND vs.status IN ('CHECKED_IN','WAITING','IN_SESSION')
                ORDER BY vs.created_at ASC
            """, (today,))
            pacientes_hoy = [dict(r) for r in cur.fetchall()]
        except Exception:
            pacientes_hoy = []

        cur.execute("""
            SELECT pn.*, p.first_name, p.last_name
            FROM progress_notes pn
            JOIN encounters e ON e.id = pn.encounter_id
            JOIN patients p ON p.id = e.patient_id
            WHERE pn.signed = 0 AND pn.parent_note_id IS NULL
            ORDER BY pn.created_at DESC
            LIMIT 10
        """)
        notas_sin_firmar = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT e.*, p.first_name, p.last_name
            FROM encounters e
            JOIN patients p ON p.id = e.patient_id
            WHERE e.encounter_date = ?
            ORDER BY e.id DESC
        """, (today,))
        encounters_hoy = [dict(r) for r in cur.fetchall()]

        conn.close()
        return render_template("admin/dashboard_dra.html",
            today=today,
            pacientes_hoy=pacientes_hoy,
            notas_sin_firmar=notas_sin_firmar,
            encounters_hoy=encounters_hoy,
        )

    elif role == "FACTURADOR":
        # ── FACTURADOR: claims pendientes, errores scrubber, pagos
        cur.execute("SELECT COUNT(*) AS n FROM claims WHERE status='DRAFT'")
        draft = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM claims WHERE status='SUBMITTED'")
        submitted = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM claims WHERE status='PAID'")
        paid = cur.fetchone()["n"]

        cur.execute("""
            SELECT c.id, c.claim_number, c.status,
                   p.first_name, p.last_name
            FROM claims c
            JOIN patients p ON p.id = c.patient_id
            WHERE c.status = 'DRAFT'
            ORDER BY c.id DESC
            LIMIT 10
        """)
        claims_draft = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT SUM(ch.amount) AS total
            FROM charges ch
            JOIN services s ON ch.service_id = s.id
            JOIN claims c ON c.id = s.claim_id
            WHERE c.status NOT IN ('PAID', 'DENIED')
        """)
        row = cur.fetchone()
        pendiente_cobro = row["total"] if row["total"] else 0.0

        conn.close()
        return render_template("admin/dashboard_facturador.html",
            today=today,
            draft=draft,
            submitted=submitted,
            paid=paid,
            claims_draft=claims_draft,
            pendiente_cobro=pendiente_cobro,
        )

    else:
        # ── ADMIN: resumen general
        cur.execute("SELECT COUNT(*) AS n FROM claims")
        total_claims = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM claims WHERE status='SUBMITTED'")
        submitted = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM claims WHERE status='PAID'")
        paid = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM cms1500_snapshots")
        snapshots = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM patients")
        total_patients = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM users WHERE active=1")
        total_users = cur.fetchone()["n"]

        cur.execute("""
            SELECT SUM(ch.amount) AS total
            FROM charges ch
            JOIN services s ON ch.service_id = s.id
            JOIN claims c ON c.id = s.claim_id
            WHERE c.status NOT IN ('PAID', 'DENIED')
        """)
        row = cur.fetchone()
        pendiente_cobro = row["total"] if row["total"] else 0.0

        cur.execute("""
            SELECT c.id, c.claim_number, c.status,
                   p.first_name, p.last_name
            FROM claims c
            JOIN patients p ON p.id = c.patient_id
            WHERE c.status = 'DRAFT'
            ORDER BY c.id DESC LIMIT 5
        """)
        claims_draft = [dict(r) for r in cur.fetchall()]

        conn.close()
        return render_template("admin/dashboard_admin.html",
            today=today,
            total_claims=total_claims,
            submitted=submitted,
            paid=paid,
            snapshots=snapshots,
            total_patients=total_patients,
            total_users=total_users,
            pendiente_cobro=pendiente_cobro,
            claims_draft=claims_draft,
        )


@dashboard_admin_bp.route("/ux-dashboard")
@login_required
@role_required("ADMIN", "DRA", "FACTURADOR")
def ux_dashboard():
    return render_template("admin/ux_dashboard.html", ux_todos=[])


@dashboard_admin_bp.route("/doctor-dashboard")
@login_required
@role_required("ADMIN", "DRA")
def doctor_dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("SELECT COUNT(*) AS n FROM encounters")
    total_encounters = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM services")
    total_services = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM claims WHERE status='SUBMITTED'")
    submitted_claims = cur.fetchone()["n"]

    cur.execute("""
        SELECT u.id, u.username,
               COALESCE(COUNT(DISTINCT e.id),0) AS encounter_count
        FROM users u
        LEFT JOIN encounters e ON e.provider_id = u.id
        WHERE u.role IN ('DRA','ADMIN')
        GROUP BY u.id
        ORDER BY encounter_count DESC
    """)
    provider_rows = cur.fetchall()
    conn.close()

    return render_template("admin/doctor_dashboard.html",
        total_encounters=total_encounters,
        total_services=total_services,
        submitted_claims=submitted_claims,
        provider_rows=provider_rows,
    )