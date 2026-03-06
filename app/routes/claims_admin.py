from flask import Blueprint, render_template, abort, request, redirect, url_for

from app.db.claims import (
    get_claim_by_id,
    get_claim_financial_status,
    get_claim_operational_status,
    update_claim_operational_status,
    VALID_TRANSITIONS,
)

from app.db.cms1500_snapshot import (
    get_latest_snapshot_by_claim,
    generate_cms1500_snapshot,
)

from app.db.event_ledger import log_event

# H3.3 — lectura directa de servicios
import sqlite3
from app.config import DB_PATH


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

    # =========================================================
    # H3.3 — SERVICES LIST FOR CLAIM
    # =========================================================
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            service_date,
            cpt_code,
            units_24g,
            charge_amount_24f
        FROM services
        WHERE claim_id = ?
        ORDER BY service_date
        """,
        (claim_id,),
    )

    services = cur.fetchall()

    conn.close()

    return render_template(
        "admin/claim_detail.html",
        claim=claim,
        financial=financial,
        operational=operational,
        latest_snapshot=latest_snapshot,
        allowed_transitions=allowed_transitions,
        services=services,
    )


@claims_admin_bp.route("/<int:claim_id>/transition", methods=["POST"])
def claim_transition(claim_id: int):

    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    # =========================================================
    # G41 — HTTP SNAPSHOT LOCK ENFORCEMENT
    # =========================================================
    existing_snapshot = get_latest_snapshot_by_claim(claim_id)

    new_status = request.form.get("new_status")
    if not new_status:
        abort(400)

    # Si ya existe snapshot, bloquear cambios que no sean resubmission controlado
    if existing_snapshot:

        if new_status not in VALID_TRANSITIONS.get(claim["status"], set()):
            return "Transition blocked: claim frozen by snapshot", 400

    previous_status = claim["status"]

    allowed = VALID_TRANSITIONS.get(previous_status, set())

    if new_status not in allowed:
        return f"Transition blocked: invalid transition {previous_status} -> {new_status}", 400

    # ---------------------------------------------------------
    # 1️⃣ Cambiar status
    # ---------------------------------------------------------
    try:
        update_claim_operational_status(claim_id, new_status)
    except Exception as e:
        return f"Transition blocked: {str(e)}", 400

    # ---------------------------------------------------------
    # 2️⃣ Generar snapshot automático
    # ---------------------------------------------------------
    if previous_status != "SUBMITTED" and new_status == "SUBMITTED":

        existing_snapshot = get_latest_snapshot_by_claim(claim_id)

        if not existing_snapshot:
            try:
                generate_cms1500_snapshot(claim_id)
            except Exception as e:
                return f"Transition blocked: snapshot generation failed ({str(e)})", 400

    # ---------------------------------------------------------
    # Auditoría
    # ---------------------------------------------------------
    try:
        log_event(
            entity_type="claim",
            entity_id=claim_id,
            event_type="claim_status_transition",
            event_data={"from": previous_status, "to": new_status},
        )
    except Exception:
        pass

    return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))