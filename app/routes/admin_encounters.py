import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session as flask_session

from app.db.encounters import get_all_encounters, create_encounter, get_encounter_by_id, get_claims_by_patient, mark_ready_for_billing
from app.db.services import create_service
from app.db.progress_notes import get_notes_by_encounter
from app.db.claims import create_claim
from app.security.auth import login_required, role_required
from app.db.connection import get_connection


encounters_admin_bp = Blueprint(
    "encounters_admin",
    __name__,
    url_prefix="/admin/encounters",
)


@encounters_admin_bp.route("/")
@login_required
@role_required("ADMIN", "DRA")
def encounters_list():

    encounters = get_all_encounters()

    return render_template(
        "admin/encounters_list.html",
        encounters=encounters
    )


@encounters_admin_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "DRA")
def encounter_create():

    # Load patients and providers for select
    from app.db.patients import get_all_patients
    patients = get_all_patients()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE role IN ('DRA', 'ADMIN') ORDER BY username")
    providers = cur.fetchall()
    conn.close()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        encounter_date = request.form.get("encounter_date")
        provider_id = request.form.get("provider_id")

        if not patient_id or not encounter_date:
            return render_template(
                "admin/encounter_form.html",
                error="Patient and date are required.",
                patients=patients,
                providers=providers,
            )

        try:
            encounter_id = create_encounter(
                int(patient_id),
                encounter_date,
                provider_id=int(provider_id) if provider_id else None,
            )
            return redirect(url_for("encounters_admin.encounter_detail", encounter_id=encounter_id))
        except Exception as e:
            return render_template(
                "admin/encounter_form.html",
                error=str(e),
                patients=patients,
                providers=providers,
            )

    return render_template("admin/encounter_form.html", patients=patients, providers=providers)


@encounters_admin_bp.route("/<int:encounter_id>")
@login_required
@role_required("ADMIN", "DRA", "FACTURADOR")
def encounter_detail(encounter_id: int):

    encounter = get_encounter_by_id(encounter_id)

    if not encounter:
        return "Encounter not found", 404

    # claims for patient
    claims = get_claims_by_patient(encounter["patient_id"])

    # services of claims via db query in existing route or via model
    from app.db.connection import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.*, c.claim_number
        FROM services s
        JOIN claims c ON c.id = s.claim_id
        WHERE c.patient_id = ?
        ORDER BY s.service_date DESC
        """,
        (encounter["patient_id"],),
    )
    services = cur.fetchall()
    conn.close()

    notes = get_notes_by_encounter(encounter_id)
    rfb_error = request.args.get("rfb_error", "")

    # Determine blocking reason for Ready for Billing UI
    has_signed_note = any(n["signed"] for n in notes)
    rfb_blocking = None
    if not has_signed_note:
        rfb_blocking = "No hay nota de progreso firmada para este encounter."

    # Claim linked to this specific encounter (if any)
    encounter_claim = None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM claims WHERE encounter_id = ? LIMIT 1",
            (encounter_id,),
        ).fetchone()
        if row:
            encounter_claim = dict(row)

    return render_template(
        "admin/encounter_detail.html",
        encounter=encounter,
        claims=claims,
        services=services,
        notes=notes,
        rfb_error=rfb_error,
        rfb_blocking=rfb_blocking,
        encounter_claim=encounter_claim,
    )


@encounters_admin_bp.route("/<int:encounter_id>/service/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "DRA")
def encounter_add_service(encounter_id: int):

    encounter = get_encounter_by_id(encounter_id)
    if not encounter:
        return "Encounter not found", 404

    claims = get_claims_by_patient(encounter["patient_id"])

    if request.method == "POST":
        claim_id = request.form.get("claim_id")
        service_date = request.form.get("service_date")
        cpt_code = request.form.get("cpt_code")
        units = request.form.get("units")
        charge_amount = request.form.get("charge_amount")

        if not claim_id or not service_date or not cpt_code or not units or not charge_amount:
            return render_template(
                "admin/encounter_service_form.html",
                encounter=encounter,
                claims=claims,
                error="Todos los campos son requeridos"
            )

        try:
            create_service(
                claim_id=int(claim_id),
                service_date=service_date,
                cpt_code=cpt_code,
                units=int(units),
                diagnosis_code="",
                description="",
                charge_amount_24f=float(charge_amount),
            )
            return redirect(url_for("encounters_admin.encounter_detail", encounter_id=encounter_id))
        except Exception as e:
            return render_template(
                "admin/encounter_service_form.html",
                encounter=encounter,
                claims=claims,
                error=str(e),
            )

    return render_template(
        "admin/encounter_service_form.html",
        encounter=encounter,
        claims=claims,
    )


@encounters_admin_bp.route("/<int:encounter_id>/ready-for-billing", methods=["POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def encounter_ready_for_billing(encounter_id: int):
    marked_by = flask_session.get("username", "unknown")
    try:
        mark_ready_for_billing(encounter_id, marked_by)
        return redirect(url_for("encounters_admin.encounter_detail", encounter_id=encounter_id))
    except ValueError as e:
        return redirect(url_for(
            "encounters_admin.encounter_detail",
            encounter_id=encounter_id,
            rfb_error=str(e),
        ))


@encounters_admin_bp.route("/<int:encounter_id>/create-claim", methods=["POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def encounter_create_claim(encounter_id: int):
    encounter = get_encounter_by_id(encounter_id)
    if not encounter:
        return "Encounter no encontrado", 404

    if not encounter["ready_for_billing"]:
        return redirect(url_for(
            "encounters_admin.encounter_detail",
            encounter_id=encounter_id,
            rfb_error="El encounter debe estar marcado como Ready for Billing antes de crear un claim.",
        ))

    # Verificar que no existe ya un claim para este encounter
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM claims WHERE encounter_id = ? LIMIT 1",
            (encounter_id,),
        ).fetchone()
        if existing:
            return redirect(url_for("claims_admin.claim_detail_admin", claim_id=existing["id"]))

    # Obtener la cobertura activa más reciente del paciente
    patient_id = encounter["patient_id"]
    with get_connection() as conn:
        coverage_row = conn.execute(
            """
            SELECT id FROM coverages
            WHERE patient_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,),
        ).fetchone()

    if not coverage_row:
        return redirect(url_for(
            "encounters_admin.encounter_detail",
            encounter_id=encounter_id,
            rfb_error="El paciente no tiene cobertura registrada. Agregue una cobertura antes de crear el claim.",
        ))

    coverage_id = coverage_row["id"]
    claim_id = create_claim(patient_id, coverage_id, encounter_id=encounter_id)

    return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))