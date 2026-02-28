from flask import Blueprint, render_template, request
from app.db.event_ledger import list_events_admin, count_events_admin

events_admin_bp = Blueprint(
    "events_admin",
    __name__,
    url_prefix="/admin/events",
)

@events_admin_bp.route("/", methods=["GET"])
def events_index():
    page_raw = request.args.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1
    if page < 1:
        page = 1

    claim_id_raw = request.args.get("claim_id", "").strip()
    claim_id = int(claim_id_raw) if claim_id_raw.isdigit() else None

    per_page = 25
    offset = (page - 1) * per_page

    total = count_events_admin(claim_id=claim_id)
    events = list_events_admin(limit=per_page, offset=offset, claim_id=claim_id)

    has_prev = page > 1
    has_next = (offset + per_page) < total

    return render_template(
        "admin/events_index.html",
        events=events,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
        claim_id=claim_id_raw,
        total=total,
    )