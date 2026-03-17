from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash
from app.config import DB_PATH
from app.db.provider_settings import get_provider_settings, update_provider_settings
from app.security.auth import login_required, role_required


settings_admin_bp = Blueprint(
    "settings_admin",
    __name__,
    url_prefix="/admin/settings",
)


@settings_admin_bp.route("/")
@login_required
@role_required("ADMIN")
def settings_dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, role, active, created_at
        FROM users ORDER BY username
    """)
    users = cur.fetchall()
    conn.close()
    ps = get_provider_settings()
    return render_template("admin/settings_dashboard.html", users=users, ps=ps)


@settings_admin_bp.route("/provider", methods=["GET", "POST"])
@login_required
@role_required("ADMIN")
def provider_edit():
    if request.method == "POST":
        fields = {
            "signature":        request.form.get("signature"),
            "signature_date":   request.form.get("signature_date"),
            "facility_name":    request.form.get("facility_name"),
            "facility_address": request.form.get("facility_address"),
            "facility_city":    request.form.get("facility_city"),
            "facility_state":   request.form.get("facility_state"),
            "facility_zip":     request.form.get("facility_zip"),
            "billing_name":     request.form.get("billing_name"),
            "billing_npi":      request.form.get("billing_npi"),
            "billing_tax_id":   request.form.get("billing_tax_id"),
            "billing_address":  request.form.get("billing_address"),
            "billing_city":     request.form.get("billing_city"),
            "billing_state":    request.form.get("billing_state"),
            "billing_zip":      request.form.get("billing_zip"),
        }
        fields = {k: v for k, v in fields.items() if v is not None}
        update_provider_settings(**fields)
        return redirect(url_for("settings_admin.provider_edit"))

    ps = get_provider_settings()
    return render_template("admin/provider_edit.html", ps=ps)


@settings_admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN")
def user_create():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role     = request.form.get("role", "").strip()

        if not username or not password or not role:
            error = "Todos los campos son requeridos."
        else:
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, role, active)
                    VALUES (?, ?, ?, 1)
                    """,
                    (username, generate_password_hash(password), role)
                )
                conn.commit()
                conn.close()
                return redirect(url_for("settings_admin.settings_dashboard"))
            except sqlite3.IntegrityError:
                error = f"El usuario '{username}' ya existe."
            except Exception as e:
                error = str(e)

    return render_template("admin/user_form.html", error=error)


@settings_admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("ADMIN")
def user_toggle(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT active FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        new_status = 0 if row[0] else 1
        cur.execute("UPDATE users SET active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for("settings_admin.settings_dashboard"))