from flask import Blueprint, render_template

from app.db.progress_notes import get_notes_by_encounter
from app.security.auth import login_required, role_required


progress_notes_admin_bp = Blueprint(
    "progress_notes_admin",
    __name__,
    url_prefix="/admin/notes",
)


@progress_notes_admin_bp.route("/<int:encounter_id>")
@login_required
@role_required("ADMIN", "DRA")
def notes_by_encounter(encounter_id):

    notes = get_notes_by_encounter(encounter_id)

    return render_template(
        "admin/notes_list.html",
        notes=notes,
        encounter_id=encounter_id
    )