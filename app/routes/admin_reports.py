from flask import Blueprint, render_template
import sqlite3
from app.config import DB_PATH


reports_admin_bp = Blueprint(
    "reports_admin",
    __name__,
    url_prefix="/admin/reports",
)


@reports_admin_bp.route("/")
def reports_dashboard():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # =========================
    # Total Patients
    # =========================
    cur.execute("SELECT COUNT(*) AS total FROM patients")
    total_patients = cur.fetchone()["total"]

    # =========================
    # Total Claims
    # =========================
    cur.execute("SELECT COUNT(*) AS total FROM claims")
    total_claims = cur.fetchone()["total"]

    # =========================
    # Total Charges
    # =========================
    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM charges")
    total_charges = cur.fetchone()["total"]

    # =========================
    # Total Payments
    # =========================
    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM payments")
    total_payments = cur.fetchone()["total"]

    # =========================
    # Total Adjustments
    # =========================
    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM adjustments")
    total_adjustments = cur.fetchone()["total"]

    conn.close()

    return render_template(
        "admin/reports_dashboard.html",
        total_patients=total_patients,
        total_claims=total_claims,
        total_charges=total_charges,
        total_payments=total_payments,
        total_adjustments=total_adjustments,
    )