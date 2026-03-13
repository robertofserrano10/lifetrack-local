from flask import Blueprint, render_template
import sqlite3

from app.config import DB_PATH
from app.security.auth import login_required, role_required


notes_print_bp = Blueprint(
    "notes_print",
    __name__,
    url_prefix="/admin/notes",
)


@notes_print_bp.route("/print/<int:note_id>")
@login_required
@role_required("ADMIN", "DRA")
def print_note(note_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            n.id,
            n.note_text,
            n.created_at,
            n.status,
            p.first_name,
            p.last_name,
            e.encounter_date
        FROM progress_notes n
        JOIN encounters e ON n.encounter_id = e.id
        JOIN patients p ON e.patient_id = p.id
        WHERE n.id = ?
        """,
        (note_id,),
    )

    note = cur.fetchone()

    conn.close()

    return render_template(
        "admin/note_print.html",
        note=note
    )