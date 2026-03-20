"""
CHECK-IN — Fase BC
Pantalla operacional de recepción.
No toca finanzas, no crea claims, no genera cargos.
"""

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

        if not patient_id:
            error = "Debes seleccionar un paciente."
        else:
            created_by = session.get("username") or "recepcion"
            session_id = create_visit_session(
                patient_id=int(patient_id),
                appointment_date=appointment_date,
                notes=notes,
                created_by=created_by,
            )
            # Move to CHECKED_IN immediately
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
            "insurer": coverage["coverage"]["insurer_name"] if coverage["coverage"] else None,
            "plan": coverage["coverage"]["plan_name"] if coverage["coverage"] else None,
            "policy": coverage["coverage"]["policy_number"] if coverage["coverage"] else None,
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