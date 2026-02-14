from flask import Blueprint, render_template
from app.db.balances import get_charge_balance
from app.db.charges import get_charge_by_id

charge_balance_bp = Blueprint("charge_balance", __name__)


@charge_balance_bp.route("/charges/<int:charge_id>/balance")
def charge_balance_view(charge_id):

    charge = get_charge_by_id(charge_id)
    if not charge:
        return "Charge no encontrado", 404

    balance = get_charge_balance(charge_id)

    return render_template(
        "charges/balance.html",
        charge=charge,
        balance=balance
    )
