from flask import Blueprint, render_template
from app.db.payments import get_payment_balance

payment_balance_bp = Blueprint("payment_balance", __name__)


@payment_balance_bp.route("/payments/<int:payment_id>/balance")
def payment_balance_view(payment_id):
    balance = get_payment_balance(payment_id)

    return render_template(
        "payments/balance.html",
        balance=balance,
    )
