"""
APPOINTMENTS — Fase BI-2
Agenda clínica: lista, nueva cita, cambio de status.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from app.db.appointments import (
    create_appointment,
    get_appointments_by_date,
    update_appointment_status,
    get_upcoming_appointments,
    SERVICE_TYPES,
    VALID_STATUSES,
)
from app.db.patients import get_all_patients
from app.security.auth import login_required, role_required


appointments_bp = Blueprint("appointments", __name__, url_prefix="/admin/appointments")


@appointments_bp.route("/")
@login_required
@role_required("ADMIN", "RECEPCION", "DRA", "FACTURADOR")
def appointments_list():
    today = datetime.now().strftime("%Y-%m-%d")
    today_appts = get_appointments_by_date(today)
    upcoming = [a for a in get_upcoming_appointments(days=30) if a["scheduled_date"] != today]

    # Agrupar upcoming por fecha
    upcoming_by_date = {}
    for a in upcoming:
        d = a["scheduled_date"]
        upcoming_by_date.setdefault(d, []).append(a)

    return render_template(
        "admin/appointments_list.html",
        today=today,
        today_appts=today_appts,
        upcoming_by_date=upcoming_by_date,
        valid_statuses=VALID_STATUSES,
    )


@appointments_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "RECEPCION", "DRA")
def appointments_new():
    patients = get_all_patients()
    today = datetime.now().strftime("%Y-%m-%d")
    error = None

    # Prellenar patient_id si viene por query string (ej. desde perfil de paciente)
    preselect = request.args.get("patient_id") or request.form.get("patient_id")

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        scheduled_date = request.form.get("scheduled_date")
        scheduled_time = request.form.get("scheduled_time")
        service_type = request.form.get("service_type")
        notes = request.form.get("notes") or None

        if not patient_id:
            error = "Debes seleccionar un paciente."
        elif not scheduled_date:
            error = "La fecha es requerida."
        elif not scheduled_time:
            error = "La hora es requerida."
        elif not service_type:
            error = "El tipo de servicio es requerido."
        else:
            created_by = session.get("username") or "sistema"
            create_appointment(
                patient_id=int(patient_id),
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                service_type=service_type,
                notes=notes,
                created_by=created_by,
            )
            return redirect(url_for("appointments.appointments_list"))

    return render_template(
        "admin/appointment_form.html",
        patients=patients,
        today=today,
        preselect=preselect,
        service_types=SERVICE_TYPES,
        error=error,
    )


@appointments_bp.route("/<int:appointment_id>/status", methods=["POST"])
@login_required
@role_required("ADMIN", "RECEPCION", "DRA", "FACTURADOR")
def appointments_update_status(appointment_id):
    new_status = request.form.get("status")
    if new_status and new_status in VALID_STATUSES:
        update_appointment_status(appointment_id, new_status)
    return redirect(url_for("appointments.appointments_list"))
