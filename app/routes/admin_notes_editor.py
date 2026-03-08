from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

from app.config import DB_PATH
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

        note_text = request.form.get("note_text")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO progress_notes (
                encounter_id,
                note_text
            )
            VALUES (?,?)
        """, (encounter_id, note_text))

        conn.commit()
        conn.close()

        return redirect(url_for("progress_notes_admin.notes_by_encounter",
                                encounter_id=encounter_id))

    return render_template(
        "admin/note_editor.html",
        encounter_id=encounter_id
    )