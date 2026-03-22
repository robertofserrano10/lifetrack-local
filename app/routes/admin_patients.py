from flask import Blueprint, render_template, abort, request, redirect, url_for
import sqlite3
from datetime import date
from app.config import DB_PATH

from app.db.patients import create_patient, get_patient_by_id, update_patient
from app.security.auth import login_required, role_required

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


patients_admin_bp = Blueprint(
    "patients_admin",
    __name__,
    url_prefix="/admin/patients",
)


# =========================================================
# Patients list
# =========================================================
@patients_admin_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def patients_list():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            first_name,
            last_name,
            date_of_birth,
            sex,
            created_at
        FROM patients
        ORDER BY last_name, first_name
        """
    )

    patients = cur.fetchall()

    conn.close()

    return render_template(
        "admin/patients_list.html",
        patients=patients,
    )


# =========================================================
# Patient create
# =========================================================
@patients_admin_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def patient_create():

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()

        if not first_name or not last_name or not date_of_birth:
            return render_template("admin/patient_form.html", error="Nombre, apellido y fecha de nacimiento son requeridos.")

        patient_id = create_patient(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            sex=request.form.get("sex", "U"),
            marital_status=request.form.get("marital_status") or None,
            employment_status=request.form.get("employment_status") or None,
            student_status=request.form.get("student_status") or None,
            address=request.form.get("address") or None,
            city=request.form.get("city") or None,
            state=request.form.get("state") or None,
            zip_code=request.form.get("zip_code") or None,
            phone=request.form.get("phone") or None,
        )

        return redirect(url_for("patients_admin.patient_detail", patient_id=patient_id))

    return render_template("admin/patient_form.html")


# =========================================================
# Patient edit
# =========================================================
@patients_admin_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def patient_edit(patient_id: int):
    patient = get_patient_by_id(patient_id)
    if not patient:
        abort(404)

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()

        if not first_name or not last_name or not date_of_birth:
            return render_template("admin/patient_form.html", patient=patient,
                                   error="Nombre, apellido y fecha de nacimiento son requeridos.")

        update_patient(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            sex=request.form.get("sex", "U"),
            marital_status=request.form.get("marital_status") or None,
            employment_status=request.form.get("employment_status") or None,
            student_status=request.form.get("student_status") or None,
            address=request.form.get("address") or None,
            city=request.form.get("city") or None,
            state=request.form.get("state") or None,
            zip_code=request.form.get("zip_code") or None,
            phone=request.form.get("phone") or None,
        )
        return redirect(url_for("patients_admin.patient_detail", patient_id=patient_id))

    return render_template("admin/patient_form.html", patient=patient)


# =========================================================
# Patient detail
# =========================================================
@patients_admin_bp.route("/<int:patient_id>")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def patient_detail(patient_id: int):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # patient
    cur.execute(
        """
        SELECT *
        FROM patients
        WHERE id = ?
        """,
        (patient_id,),
    )

    patient = cur.fetchone()

    if not patient:
        conn.close()
        abort(404)

    # coverages
    cur.execute(
        """
        SELECT
            id,
            insurer_name,
            plan_name,
            policy_number,
            start_date
        FROM coverages
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,),
    )

    coverages = cur.fetchall()

    # claims
    cur.execute(
        """
        SELECT
            id,
            claim_number,
            status,
            created_at
        FROM claims
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,),
    )

    claims = cur.fetchall()

    # encounters
    cur.execute(
        """
        SELECT
            id,
            encounter_date,
            status,
            provider_id,
            created_at
        FROM encounters
        WHERE patient_id = ?
        ORDER BY encounter_date DESC
        """,
        (patient_id,),
    )

    encounters = cur.fetchall()

    # services (all services for this patient via claim relationship)
    cur.execute(
        """
        SELECT
            s.id,
            s.claim_id,
            s.service_date,
            s.cpt_code,
            s.units_24g,
            s.charge_amount_24f,
            c.claim_number
        FROM services s
        JOIN claims c ON c.id = s.claim_id
        WHERE c.patient_id = ?
        ORDER BY s.service_date DESC
        """,
        (patient_id,),
    )

    services = cur.fetchall()

    # timeline (union encounters/services/claims)
    cur.execute(
        """
        SELECT 'encounter' as item_type, id as item_id, encounter_date as item_date, status as item_status, NULL as item_code
        FROM encounters WHERE patient_id = ?
        UNION ALL
        SELECT 'service', s.id, s.service_date, s.cpt_code, s.units_24g
        FROM services s
        JOIN claims c ON c.id = s.claim_id
        WHERE c.patient_id = ?
        UNION ALL
        SELECT 'claim', id, created_at, status, NULL
        FROM claims WHERE patient_id = ?
        ORDER BY item_date DESC
        """,
        (patient_id, patient_id, patient_id),
    )

    timeline = cur.fetchall()

    conn.close()

    return render_template(
        "admin/patient_detail.html",
        patient=patient,
        coverages=coverages,
        claims=claims,
        encounters=encounters,
        services=services,
        timeline=timeline,
    )

# =========================================================
# Consent: HIPAA Authorization (printable)
# =========================================================
@patients_admin_bp.route("/<int:patient_id>/consent/hipaa")
@login_required
@role_required("ADMIN", "RECEPCION", "FACTURADOR")
def consent_hipaa(patient_id: int):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        abort(404)

    cur.execute(
        """
        SELECT insurer_name, plan_name, policy_number
        FROM coverages
        WHERE patient_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (patient_id,),
    )
    coverage = cur.fetchone()
    conn.close()

    today = date.today()
    print_date = f"{today.day} de {MESES_ES[today.month]} de {today.year}"
    return render_template(
        "admin/consent_hipaa.html",
        patient=patient,
        coverage=coverage,
        print_date=print_date,
    )


# =========================================================
# Consent: Informed Consent (printable)
# =========================================================
@patients_admin_bp.route("/<int:patient_id>/consent/informado")
@login_required
@role_required("ADMIN", "RECEPCION", "FACTURADOR")
def consent_informado(patient_id: int):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        abort(404)

    cur.execute(
        """
        SELECT insurer_name, plan_name, policy_number
        FROM coverages
        WHERE patient_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (patient_id,),
    )
    coverage = cur.fetchone()
    conn.close()

    today = date.today()
    print_date = f"{today.day} de {MESES_ES[today.month]} de {today.year}"
    return render_template(
        "admin/consent_informado.html",
        patient=patient,
        coverage=coverage,
        print_date=print_date,
    )


# =========================================================
# Clinical Timeline
# =========================================================
@patients_admin_bp.route("/<int:patient_id>/timeline")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION", "DRA")
def patient_timeline(patient_id: int):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Patient
    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        abort(404)

    # Encounters ordered by date desc
    cur.execute("""
        SELECT e.*, u.username AS provider_username
        FROM encounters e
        LEFT JOIN users u ON u.id = e.provider_id
        WHERE e.patient_id = ?
        ORDER BY e.encounter_date DESC
    """, (patient_id,))
    encounters_raw = cur.fetchall()

    # Build timeline: each encounter with its notes and claim
    timeline = []
    for enc in encounters_raw:
        enc_dict = dict(enc)

        # Notes for this encounter (no addendums)
        cur.execute("""
            SELECT * FROM progress_notes
            WHERE encounter_id = ? AND parent_note_id IS NULL
            ORDER BY created_at ASC
        """, (enc_dict["id"],))
        enc_dict["notes"] = cur.fetchall()

        # Claim linked to this patient (match by date proximity or just get all)
        cur.execute("""
            SELECT id, claim_number, status
            FROM claims
            WHERE patient_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (patient_id,))
        claim = cur.fetchone()
        enc_dict["claim"] = dict(claim) if claim else None

        timeline.append(enc_dict)

    conn.close()

    return render_template(
        "admin/clinical_timeline.html",
        patient=patient,
        timeline=timeline,
    )