from flask import Blueprint, render_template, abort
from app.db.claims import (
    get_claim_by_id,
    get_claim_financial_status,
    get_claim_operational_status,
    ALLOWED_STATUSES,
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
