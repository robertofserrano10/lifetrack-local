import os
import sqlite3
from typing import Any, Dict, Optional

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from werkzeug.security import check_password_hash

from app.views.cms1500_render import get_latest_snapshot_by_claim
from app.utils.snapshot_hash import compute_snapshot_hash

from app.routes.patients import patients_bp
from app.routes.coverages import coverages_bp
from app.routes.provider_settings import provider_settings_bp
from app.routes.cms1500_pdf import cms1500_pdf_bp
from app.routes.claim_balance import claim_balance_bp
from app.routes.charge_balance import charge_balance_bp
from app.routes.claim_payments import claim_payments_bp
from app.routes.claim_adjustments import claim_adjustments_bp
from app.routes.claim_financial_summary import claim_financial_summary_bp
from app.routes.payment_balance import payment_balance_bp
from app.routes.claims_overview import claims_overview_bp
from app.routes.snapshots_admin import snapshots_admin_bp
from app.routes.claims_admin import claims_admin_bp
from app.routes.events_admin import events_admin_bp
from app.routes.admin_dashboard import dashboard_admin_bp
from app.routes.admin_claims_list import claims_list_bp
from app.routes.admin_patients import patients_admin_bp
from app.routes.admin_services import services_admin_bp
from app.routes.admin_finances import finances_admin_bp
from app.routes.admin_reports import reports_admin_bp
from app.routes.admin_settings import settings_admin_bp
from app.routes.admin_encounters import encounters_admin_bp
from app.routes.admin_clinical import clinical_admin_bp
from app.routes.admin_progress_notes import progress_notes_admin_bp
from app.routes.admin_notes_editor import notes_editor_admin_bp
from app.routes.admin_checkin import checkin_bp
from app.routes.admin_eob import eob_bp
from app.routes.admin_appointments import appointments_bp

app = Flask(__name__)
app.secret_key = "dev-secret-key"

DB_PATH = os.path.join("storage", "lifetrack.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user() -> Optional[Dict[str, Any]]:
    user_id = session.get("user_id")
    if not user_id:
        return None

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if not row:
            session.pop("user_id", None)
            return None

        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
        }
    finally:
        conn.close()


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


# =========================
# HOME
# =========================
@app.route("/")
def home():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return redirect(url_for("admin_dashboard.dashboard"))


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if not row:
            return render_template(
                "login.html",
                error="Credenciales inválidas",
            )

        if not check_password_hash(row["password_hash"], password):
            return render_template(
                "login.html",
                error="Credenciales inválidas",
            )

        session["user_id"] = row["id"]
        session["role"] = row["role"]   # ← CAMBIO APLICADO

        return redirect(url_for("home"))
    finally:
        conn.close()


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)  # ← limpiar rol también
    return redirect(url_for("login"))


# =========================
# BLUEPRINTS
# =========================
app.register_blueprint(patients_bp)
app.register_blueprint(coverages_bp)
app.register_blueprint(provider_settings_bp)
app.register_blueprint(claim_balance_bp)
app.register_blueprint(charge_balance_bp)
app.register_blueprint(claim_payments_bp)
app.register_blueprint(claim_adjustments_bp)
app.register_blueprint(claim_financial_summary_bp)
app.register_blueprint(payment_balance_bp)
app.register_blueprint(claims_overview_bp)
app.register_blueprint(snapshots_admin_bp)
app.register_blueprint(claims_admin_bp)
app.register_blueprint(events_admin_bp)
app.register_blueprint(cms1500_pdf_bp)
app.register_blueprint(dashboard_admin_bp)
app.register_blueprint(claims_list_bp)
app.register_blueprint(patients_admin_bp)
app.register_blueprint(services_admin_bp)
app.register_blueprint(finances_admin_bp)
app.register_blueprint(reports_admin_bp)
app.register_blueprint(settings_admin_bp)
app.register_blueprint(encounters_admin_bp)
app.register_blueprint(clinical_admin_bp)
app.register_blueprint(progress_notes_admin_bp)
app.register_blueprint(notes_editor_admin_bp)
app.register_blueprint(checkin_bp)
app.register_blueprint(eob_bp)
app.register_blueprint(appointments_bp)

# =========================
# PATIENT SEARCH (global)
# =========================
@app.route("/admin/patient-search")
def patient_search():
    if not session.get("user_id"):
        return jsonify([]), 401
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    like = f"%{q}%"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT id, first_name, last_name, date_of_birth
               FROM patients
               WHERE first_name LIKE ? OR last_name LIKE ? OR date_of_birth LIKE ?
               ORDER BY last_name, first_name
               LIMIT 8""",
            (like, like, like),
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


# =========================
# CMS1500 VIEW
# =========================
@app.route("/cms1500/<int:claim_id>")
def cms1500_view(claim_id):
    snapshot = get_latest_snapshot_by_claim(claim_id)
    if not snapshot:
        return "No hay snapshot para este claim", 404

    snapshot_hash = compute_snapshot_hash(snapshot)

    return render_template(
        "cms1500.html",
        snapshot=snapshot,
        snapshot_hash=snapshot_hash,
    )


print("LifeTrack local iniciado")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)