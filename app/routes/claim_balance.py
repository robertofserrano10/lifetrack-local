from flask import Blueprint, render_template
from app.db.balances import get_claim_balance

claim_balance_bp = Blueprint("claim_balance", __name__)


@claim_balance_bp.route("/claims/<int:claim_id>/balance", methods=["GET"])
def view_claim_balance(claim_id):
    balance = get_claim_balance(claim_id)
    return render_template(
        "claims/balance.html",
        balance=balance
    )
