from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

from app.config import DB_PATH
from app.db.progress_notes import create_note
from app.security.auth import login_required, role_required


notes_editor_admin_bp = Blueprint(
    "notes_editor_admin",
    __name__,
    url_prefix="/admin/notes",
)


@notes_editor_admin_bp.route("/create/<int:encounter_id>", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "DRA")
def create_note(encounter_id):

    if request.method == "POST":

        patient_name = request.form.get("patient_name")
        record_number = request.form.get("record_number")
        date_of_service = request.form.get("date_of_service")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        service_type = request.form.get("service_type")
        cpt_code = request.form.get("cpt_code")
        diagnosis_code = request.form.get("diagnosis_code")
        provider_name = request.form.get("provider_name")
        provider_credentials = request.form.get("provider_credentials")

        subjective = request.form.get("subjective")
        objective = request.form.get("objective")
        assessment = request.form.get("assessment")
        plan = request.form.get("plan")

        create_note(
            encounter_id,
            patient_name,
            record_number,
            date_of_service,
            start_time,
            end_time,
            service_type,
            cpt_code,
            diagnosis_code,
            provider_name,
            provider_credentials,
            subjective,
            objective,
            assessment,
            plan,
        )

        return redirect(url_for("progress_notes_admin.notes_by_encounter",
                                encounter_id=encounter_id))

    return render_template(
        "admin/note_editor.html",
        encounter_id=encounter_id
    )