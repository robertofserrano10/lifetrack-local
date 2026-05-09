from flask import Blueprint, render_template
from app.db.payments import get_payment_balance
from app.security.auth import login_required, role_required

payment_balance_bp = Blueprint("payment_balance", __name__)


@payment_balance_bp.route("/payments/<int:payment_id>/balance")
@login_required
@role_required("ADMIN", "FACTURADOR")
def payment_balance_view(payment_id):
    balance = get_payment_balance(payment_id)

    return render_template(
        "payments/balance.html",
        balance=balance,
    )
