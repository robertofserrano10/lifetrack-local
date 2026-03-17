from flask import Blueprint, render_template, abort, request, redirect, url_for

from app.db.claims import (
    get_claim_by_id,
    get_claim_financial_status,
    get_claim_operational_status,
    update_claim_operational_status,
    VALID_TRANSITIONS,
)
from app.db.financial_lock import is_claim_locked
from app.db.cms1500_snapshot import generate_cms1500_snapshot

from app.db.cms1500_snapshot import (
    get_latest_snapshot_by_claim,
    generate_cms1500_snapshot,
    list_snapshots_admin,
)

from app.db.event_ledger import log_event, list_events_admin
from app.db.services import create_service
from app.db.charges import create_charge
from app.db.connection import get_connection

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
    # H3.3 — SERVICES, CHARGES, PAYMENTS, APPLICATIONS
    # =========================================================
    conn = get_connection()
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

    cur.execute(
        """
        SELECT ch.*
        FROM charges ch
        JOIN services s ON ch.service_id = s.id
        WHERE s.claim_id = ?
        ORDER BY ch.id DESC
        """,
        (claim_id,),
    )
    charges = cur.fetchall()

    cur.execute(
        """
        SELECT p.*
        FROM payments p
        JOIN applications a ON a.payment_id = p.id
        JOIN charges c ON c.id = a.charge_id
        JOIN services s ON s.id = c.service_id
        WHERE s.claim_id = ?
        GROUP BY p.id
        ORDER BY p.id DESC
        """,
        (claim_id,),
    )
    payments = cur.fetchall()

    cur.execute(
        """
        SELECT a.*
        FROM applications a
        JOIN charges c ON c.id = a.charge_id
        JOIN services s ON s.id = c.service_id
        WHERE s.claim_id = ?
        ORDER BY a.id DESC
        """,
        (claim_id,),
    )
    applications = cur.fetchall()

    conn.close()

    # =========================================================
    # H3.4 — SNAPSHOTS FOR CLAIM
    # =========================================================
    all_snaps = list_snapshots_admin()

    claim_snapshots = [
        s for s in all_snaps
        if s["claim_id"] == claim_id
    ]

    # =========================================================
    # H3.5 — EVENT LEDGER FOR CLAIM
    # =========================================================
    claim_events = list_events_admin(limit=50, offset=0, claim_id=claim_id)
    locked = is_claim_locked(claim_id)

    return render_template(
        "admin/claim_detail.html",
        claim=claim,
        financial=financial,
        operational=operational,
        latest_snapshot=latest_snapshot,
        allowed_transitions=allowed_transitions,
        services=services,
        charges=charges,
        payments=payments,
        applications=applications,
        snapshots=claim_snapshots,
        events=claim_events,
        locked=locked,
    )


@claims_admin_bp.route("/<int:claim_id>/cms1500")
def claim_cms1500(claim_id: int):
    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    latest_snapshot = get_latest_snapshot_by_claim(claim_id)
    if not latest_snapshot:
        return "No hay snapshot CMS1500 disponible. Bloquee el claim primero.", 400

    return render_template(
        "admin/cms1500_form.html",
        snapshot=latest_snapshot,
    )


@claims_admin_bp.route("/<int:claim_id>/service/new", methods=["GET", "POST"])
def claim_add_service(claim_id: int):
    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    error = None
    if request.method == "POST":
        service_date = request.form.get("service_date")
        cpt_code = request.form.get("cpt_code")
        units = request.form.get("units")
        charge_amount = request.form.get("charge_amount")

        if not service_date or not cpt_code or not units or not charge_amount:
            error = "Todos los campos son requeridos"
        else:
            try:
                service_id = create_service(
                    claim_id=int(claim_id),
                    service_date=service_date,
                    cpt_code=cpt_code,
                    units=int(units),
                    diagnosis_code="",
                    description="",
                    charge_amount_24f=float(charge_amount),
                )
                create_charge(service_id=service_id, amount=float(charge_amount))
                return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))
            except Exception as exc:
                error = str(exc)

    return render_template(
        "admin/claim_add_service.html",
        claim=claim,
        error=error,
    )


@claims_admin_bp.route("/<int:claim_id>/lock", methods=["POST"])
def claim_lock(claim_id: int):
    claim = get_claim_by_id(claim_id)
    if not claim:
        abort(404)

    if is_claim_locked(claim_id):
        return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))

    try:
        generate_cms1500_snapshot(claim_id)
        log_event(
            entity_type="claim",
            entity_id=claim_id,
            event_type="claim_manual_lock",
            event_data={"by": "admin", "claim_status": claim["status"]},
        )
    except Exception as exc:
        return f"No se pudo bloquear el claim: {str(exc)}", 400

    return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))


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