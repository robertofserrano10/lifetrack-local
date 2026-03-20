"""
EOB — Explanation of Benefits Processing — Fase BE
Flujo guiado para registrar el pago del seguro.
No toca lógica financiera existente — usa las funciones ya probadas.
"""

from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
from app.config import DB_PATH
from app.db.payments import create_payment
from app.db.applications import create_application
from app.db.adjustments import create_adjustment
from app.db.claims import get_claim_by_id
from app.db.balances import get_claim_balance
from app.db.event_ledger import log_event
from app.security.auth import login_required, role_required


eob_bp = Blueprint("eob", __name__, url_prefix="/admin/eob")


@eob_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR")
def eob_list():
    """Lista de claims listos para procesar EOB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.id, c.claim_number, c.status,
            p.first_name, p.last_name,
            cov.insurer_name,
            COALESCE(SUM(ch.amount), 0) AS total_charge,
            COALESCE(SUM(ap.amount_applied), 0) AS total_paid
        FROM claims c
        JOIN patients p ON p.id = c.patient_id
        LEFT JOIN coverages cov ON cov.id = c.coverage_id
        LEFT JOIN services s ON s.claim_id = c.id
        LEFT JOIN charges ch ON ch.service_id = s.id
        LEFT JOIN applications ap ON ap.charge_id = ch.id
        WHERE c.status IN ('SUBMITTED', 'READY', 'DRAFT')
        GROUP BY c.id
        ORDER BY c.id DESC
    """)
    claims = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template("admin/eob_list.html", claims=claims)


@eob_bp.route("/claim/<int:claim_id>", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def eob_process(claim_id):
    """Procesar EOB para un claim específico."""
    claim = get_claim_by_id(claim_id)
    if not claim:
        return "Claim no encontrado", 404

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Obtener services y charges del claim
    cur.execute("""
        SELECT
            s.id AS service_id,
            s.service_date,
            s.cpt_code,
            s.units_24g,
            s.charge_amount_24f,
            ch.id AS charge_id,
            ch.amount AS charge_amount,
            COALESCE(SUM(ap.amount_applied), 0) AS paid_so_far,
            COALESCE(SUM(adj.amount), 0) AS adjusted_so_far
        FROM services s
        JOIN charges ch ON ch.service_id = s.id
        LEFT JOIN applications ap ON ap.charge_id = ch.id
        LEFT JOIN adjustments adj ON adj.charge_id = ch.id
        WHERE s.claim_id = ?
        GROUP BY ch.id
        ORDER BY s.service_date ASC
    """, (claim_id,))
    service_lines = [dict(r) for r in cur.fetchall()]

    # Patient and coverage info
    cur.execute("""
        SELECT p.first_name, p.last_name, cov.insurer_name, cov.plan_name, cov.policy_number
        FROM claims c
        JOIN patients p ON p.id = c.patient_id
        LEFT JOIN coverages cov ON cov.id = c.coverage_id
        WHERE c.id = ?
    """, (claim_id,))
    info = dict(cur.fetchone() or {})
    conn.close()

    error = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "process_eob":
            try:
                received_date = request.form.get("received_date")
                method = request.form.get("method", "eft")
                reference = request.form.get("reference") or None
                eob_number = request.form.get("eob_number") or None

                total_payment = 0.0
                line_data = []

                # Collect all line data first
                for svc in service_lines:
                    charge_id = svc["charge_id"]
                    paid = request.form.get(f"paid_{charge_id}", "0") or "0"
                    adjustment = request.form.get(f"adjustment_{charge_id}", "0") or "0"
                    adj_reason = request.form.get(f"adj_reason_{charge_id}", "Ajuste contractual")

                    paid_f = float(paid)
                    adj_f = float(adjustment)

                    line_data.append({
                        "charge_id": charge_id,
                        "paid": paid_f,
                        "adjustment": adj_f,
                        "adj_reason": adj_reason,
                    })
                    total_payment += paid_f

                # Only create payment if there's something to pay
                payment_id = None
                if total_payment > 0:
                    payment_id = create_payment(
                        amount=total_payment,
                        method=method,
                        reference=reference or eob_number,
                        received_date=received_date,
                    )

                # Process each line
                for line in line_data:
                    if line["paid"] > 0 and payment_id:
                        create_application(
                            payment_id=payment_id,
                            charge_id=line["charge_id"],
                            amount_applied=line["paid"],
                        )
                    if line["adjustment"] > 0:
                        create_adjustment(
                            charge_id=line["charge_id"],
                            amount=line["adjustment"],
                            reason=line["adj_reason"],
                        )

                # Log EOB event
                log_event(
                    entity_type="claim",
                    entity_id=claim_id,
                    event_type="eob_processed",
                    event_data={
                        "total_paid": total_payment,
                        "eob_number": eob_number,
                        "payment_id": payment_id,
                    },
                )

                success = f"EOB procesado. Total pagado: ${total_payment:.2f}"

                # Redirect back to claim
                return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))

            except Exception as e:
                error = str(e)

    # Calculate balance per line
    for svc in service_lines:
        balance = svc["charge_amount"] - svc["paid_so_far"] - svc["adjusted_so_far"]
        svc["balance"] = round(balance, 2)

    total_charge = sum(s["charge_amount"] for s in service_lines)
    total_paid = sum(s["paid_so_far"] for s in service_lines)
    total_adjusted = sum(s["adjusted_so_far"] for s in service_lines)
    total_balance = total_charge - total_paid - total_adjusted

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "admin/eob_process.html",
        claim=claim,
        info=info,
        service_lines=service_lines,
        total_charge=total_charge,
        total_paid=total_paid,
        total_adjusted=total_adjusted,
        total_balance=total_balance,
        today=today,
        error=error,
        success=success,
    )