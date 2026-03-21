"""
CHECK-IN — Fase BC / BI-3
Pantalla operacional de recepción.
No toca finanzas directas excepto registrar copago como payment no-aplicado.
"""

import json
from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from app.config import DB_PATH
from app.db.visit_sessions import (
    create_visit_session,
    update_visit_status,
    get_sessions_today,
    get_session_by_id,
    check_patient_coverage,
)
from app.db.patients import get_all_patients, get_patient_by_id
from app.db.payments import create_payment
from app.security.auth import login_required, role_required


checkin_bp = Blueprint("checkin", __name__, url_prefix="/admin/checkin")


@checkin_bp.route("/")
@login_required
@role_required("ADMIN", "RECEPCION")
def checkin_home():
    """Pantalla principal de recepción — lista de hoy."""
    today = datetime.now().strftime("%Y-%m-%d")
    sessions = get_sessions_today(today)

    # Separar por status para mostrar ordenado
    waiting   = [s for s in sessions if s["status"] in ("CHECKED_IN", "WAITING")]
    in_session= [s for s in sessions if s["status"] == "IN_SESSION"]
    completed = [s for s in sessions if s["status"] == "COMPLETED"]
    cancelled = [s for s in sessions if s["status"] == "CANCELLED"]

    return render_template(
        "admin/checkin_home.html",
        today=today,
        waiting=waiting,
        in_session=in_session,
        completed=completed,
        cancelled=cancelled,
        total=len(sessions),
    )


@checkin_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "RECEPCION")
def checkin_new():
    """Registrar llegada de paciente."""
    patients = get_all_patients()
    today = datetime.now().strftime("%Y-%m-%d")
    error = None
    patient_info = None
    coverage_info = None

    # Si viene con patient_id preseleccionado, cargar info
    preselect = request.args.get("patient_id") or request.form.get("patient_id")
    if preselect:
        patient_info = get_patient_by_id(int(preselect))
        if patient_info:
            coverage_info = check_patient_coverage(int(preselect))

    if request.method == "POST" and request.form.get("action") == "checkin":
        patient_id = request.form.get("patient_id")
        appointment_date = request.form.get("appointment_date") or today
        notes = request.form.get("notes") or None

        # BI-3 fields
        eligibility_verified = 1 if request.form.get("eligibility_verified") else 0
        copago_amount_raw = request.form.get("copago_amount") or "0"
        copago_method = request.form.get("copago_method") or "cash"
        referral_on_file = 1 if request.form.get("referral_on_file") else 0
        hipaa_signed = 1 if request.form.get("hipaa_signed") else 0
        consent_signed = 1 if request.form.get("consent_signed") else 0

        try:
            copago_amount = float(copago_amount_raw)
            if copago_amount < 0:
                copago_amount = 0.0
        except ValueError:
            copago_amount = 0.0

        if not patient_id:
            error = "Debes seleccionar un paciente."
        elif not eligibility_verified:
            error = "Debes verificar la elegibilidad del paciente antes de hacer check-in."
            if not patient_info:
                patient_info = get_patient_by_id(int(patient_id))
                coverage_info = check_patient_coverage(int(patient_id))
        else:
            created_by = session.get("username") or "recepcion"

            # Registrar copago como payment no-aplicado
            copago_payment_id = None
            if copago_amount > 0:
                copago_payment_id = create_payment(
                    amount=copago_amount,
                    method=copago_method,
                    reference=f"Copago check-in — {appointment_date}",
                    received_date=appointment_date,
                )

            documents_signed = json.dumps({
                "hipaa": bool(hipaa_signed),
                "consent": bool(consent_signed),
            })

            session_id = create_visit_session(
                patient_id=int(patient_id),
                appointment_date=appointment_date,
                notes=notes,
                created_by=created_by,
                eligibility_verified=eligibility_verified,
                copago_amount=copago_amount,
                copago_payment_id=copago_payment_id,
                referral_on_file=referral_on_file,
                documents_signed=documents_signed,
            )
            update_visit_status(session_id, "CHECKED_IN")
            update_visit_status(session_id, "WAITING")
            return redirect(url_for("checkin.checkin_home"))

    return render_template(
        "admin/checkin_new.html",
        patients=patients,
        today=today,
        preselect=preselect,
        patient_info=patient_info,
        coverage_info=coverage_info,
        error=error,
    )


@checkin_bp.route("/patient-info")
@login_required
@role_required("ADMIN", "RECEPCION")
def checkin_patient_info():
    """AJAX — devuelve info del paciente para preview en el form."""
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return {"error": "No patient_id"}, 400

    patient = get_patient_by_id(int(patient_id))
    if not patient:
        return {"error": "Not found"}, 404

    coverage = check_patient_coverage(int(patient_id))

    # Check missing fields for 1500
    warnings = []
    if not patient.get("sex") or patient.get("sex") == "U":
        warnings.append("Sexo no especificado")
    if not patient.get("address"):
        warnings.append("Falta dirección")
    if not patient.get("date_of_birth"):
        warnings.append("Falta fecha de nacimiento")

    cov_data = coverage["coverage"]
    return {
        "patient": {
            "id": patient["id"],
            "name": f"{patient['last_name']}, {patient['first_name']}",
            "dob": patient.get("date_of_birth", "—"),
            "phone": patient.get("phone", "—"),
            "address": patient.get("address", "—"),
        },
        "coverage": {
            "has_coverage": coverage["has_coverage"],
            "expired": coverage.get("expired", False),
            "insurer": cov_data["insurer_name"] if cov_data else None,
            "plan": cov_data["plan_name"] if cov_data else None,
            "policy": cov_data["policy_number"] if cov_data else None,
            "referral_required": bool(cov_data.get("referral_required", 0)) if cov_data else False,
        },
        "warnings": warnings,
    }


@checkin_bp.route("/<int:session_id>/status", methods=["POST"])
@login_required
@role_required("ADMIN", "RECEPCION", "DRA")
def update_status(session_id):
    """Cambiar status de una visita."""
    new_status = request.form.get("status")
    if new_status:
        update_visit_status(session_id, new_status)
    return redirect(url_for("checkin.checkin_home"))