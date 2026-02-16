from flask import Blueprint, render_template, abort, request, redirect, url_for
from app.db.claims import (
    get_claim_by_id,
    get_claim_financial_status,
    get_claim_operational_status,
    update_claim_operational_status,
    VALID_TRANSITIONS,
)
from app.db.cms1500_snapshot import get_latest_snapshot_by_claim

claims_admin_bp = Blueprint(
    "claims_admin",
    __name__,
    url_prefix="/admin/claims",
)

@claims_admin_bp.route("/<int:claim_id>", methods=["GET", "POST"])
def claim_detail_admin(claim_id: int):

    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    # POST = transición operacional controlada
    if request.method == "POST":
        new_status = request.form.get("new_status")
        if new_status:
            update_claim_operational_status(claim_id, new_status)
        return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))

    financial = get_claim_financial_status(claim_id)
    operational = get_claim_operational_status(claim_id)
    latest_snapshot = get_latest_snapshot_by_claim(claim_id)

    # Calcular transiciones válidas si NO está locked
    transitions = []
    if not operational["locked"]:
        current = operational["persisted_status"]
        transitions = sorted(list(VALID_TRANSITIONS.get(current, set())))

    return render_template(
        "admin/claim_detail.html",
        claim=claim,
        financial=financial,
        operational=operational,
        latest_snapshot=latest_snapshot,
        transitions=transitions,
    )
