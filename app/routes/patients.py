from flask import Blueprint, redirect, url_for

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/patients/<int:patient_id>/edit", methods=["GET"])
def edit_patient(patient_id):
    # Redirect to the admin route which handles GET and POST
    return redirect(url_for("patients_admin.patient_edit", patient_id=patient_id))