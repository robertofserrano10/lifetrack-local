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

@claims_admin_bp.route("/<int:claim_id>")
def claim_detail_admin(claim_id: int):

    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    financial = get_claim_financial_status(claim_id)
    operational = get_claim_operational_status(claim_id)
    latest_snapshot = get_latest_snapshot_by_claim(claim_id)

    allowed_transitions = []
    if not operational["locked"]:
        current = claim["status"]
        allowed_transitions = sorted(list(VALID_TRANSITIONS.get(current, set())))

    return render_template(
        "admin/claim_detail.html",
        claim=claim,
        financial=financial,
        operational=operational,
        latest_snapshot=latest_snapshot,
        allowed_transitions=allowed_transitions,
    )


@claims_admin_bp.route("/<int:claim_id>/transition", methods=["POST"])
def claim_transition(claim_id: int):

    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    new_status = request.form.get("new_status")
    if not new_status:
        abort(400)

    try:
        update_claim_operational_status(claim_id, new_status)
    except Exception as e:
        return f"Transition blocked: {str(e)}", 400

    return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))
