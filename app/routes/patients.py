from flask import Blueprint, render_template
from app.db.patients import get_patient_by_id

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/patients/<int:patient_id>/edit", methods=["GET"])
def edit_patient(patient_id):
    patient = get_patient_by_id(patient_id)
    if not patient:
        return "Paciente no encontrado", 404

    # IMPORTANTE: ruta correcta del template
    return render_template(
        "patients/edit.html",
        patient=patient
    )
