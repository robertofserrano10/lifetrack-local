from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
from app.config import DB_PATH

from app.db.charges import create_charge
from app.db.payments import create_payment
from app.db.applications import create_application
from app.db.connection import get_connection
from app.security.auth import login_required, role_required


finances_admin_bp = Blueprint(
    "finances_admin",
    __name__,
    url_prefix="/admin/finances",
)


@finances_admin_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR")
def finances_dashboard():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # =========================
    # CHARGES
    # =========================
    cur.execute("""
        SELECT
            charges.id,
            charges.amount,
            services.service_date,
            services.cpt_code,
            claims.claim_number
        FROM charges
        JOIN services ON charges.service_id = services.id
        JOIN claims ON services.claim_id = claims.id
        ORDER BY charges.id DESC
    """)

    charges = cur.fetchall()

    # =========================
    # PAYMENTS (claim number derive from any application)
    # =========================
    cur.execute("""
        SELECT
            p.id,
            p.amount,
            p.method,
            p.reference,
            p.received_date AS payment_date,
            COALESCE(c.claim_number, '') AS claim_number
        FROM payments p
        LEFT JOIN applications a ON a.payment_id = p.id
        LEFT JOIN charges ch ON a.charge_id = ch.id
        LEFT JOIN services s ON ch.service_id = s.id
        LEFT JOIN claims c ON s.claim_id = c.id
        GROUP BY p.id
        ORDER BY p.id DESC
    """)

    payments = cur.fetchall()

    # =========================
    # ADJUSTMENTS
    # =========================
    cur.execute("""
        SELECT
            adjustments.id,
            adjustments.amount,
            adjustments.reason,
            claims.claim_number
        FROM adjustments
        JOIN charges ON adjustments.charge_id = charges.id
        JOIN services ON charges.service_id = services.id
        JOIN claims ON services.claim_id = claims.id
        ORDER BY adjustments.id DESC
    """)

    adjustments = cur.fetchall()

    conn.close()

    return render_template(
        "admin/finances_dashboard.html",
        charges=charges,
        payments=payments,
        adjustments=adjustments
    )


@finances_admin_bp.route("/charge/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def charge_create():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, claim_number FROM claims ORDER BY id DESC"
    )
    claims = cur.fetchall()
    cur.execute(
        "SELECT id, cpt_code, service_date FROM services ORDER BY id DESC"
    )
    services = cur.fetchall()

    error = None
    if request.method == "POST":
        service_id = request.form.get("service_id")
        amount = request.form.get("amount")
        if not service_id or not amount:
            error = "Service y monto son requeridos"
        else:
            try:
                create_charge(int(service_id), float(amount))
                return redirect(url_for("finances_admin.finances_dashboard"))
            except Exception as exc:
                error = str(exc)

    return render_template(
        "admin/charge_form.html",
        services=services,
        claims=claims,
        error=error,
    )


@finances_admin_bp.route("/payment/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def payment_create():
    error = None
    if request.method == "POST":
        amount = request.form.get("amount")
        method = request.form.get("method")
        reference = request.form.get("reference")
        received_date = request.form.get("received_date")

        if not all([amount, method, received_date]):
            error = "Monto, método y fecha son requeridos"
        else:
            try:
                create_payment(
                    float(amount),
                    method,
                    reference if reference else None,
                    received_date,
                )
                return redirect(url_for("finances_admin.finances_dashboard"))
            except Exception as exc:
                error = str(exc)

    return render_template("admin/payment_form.html", error=error)


@finances_admin_bp.route("/application/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def application_create():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, amount FROM payments ORDER BY id DESC")
    payments = cur.fetchall()
    cur.execute("SELECT charges.id, charges.amount, claims.claim_number FROM charges JOIN services ON charges.service_id = services.id JOIN claims ON services.claim_id = claims.id ORDER BY charges.id DESC")
    charges = cur.fetchall()

    error = None
    if request.method == "POST":
        payment_id = request.form.get("payment_id")
        charge_id = request.form.get("charge_id")
        amount_applied = request.form.get("amount_applied")

        if not payment_id or not charge_id or not amount_applied:
            error = "Payment, charge y monto aplicado son requeridos"
        else:
            try:
                create_application(int(payment_id), int(charge_id), float(amount_applied))
                return redirect(url_for("finances_admin.finances_dashboard"))
            except Exception as exc:
                error = str(exc)

    return render_template(
        "admin/application_form.html",
        payments=payments,
        charges=charges,
        error=error,
    )