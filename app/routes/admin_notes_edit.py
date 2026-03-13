from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

from app.config import DB_PATH
from app.security.auth import login_required, role_required


notes_edit_admin_bp = Blueprint(
    "notes_edit_admin",
    __name__,
    url_prefix="/admin/notes",
)


@notes_edit_admin_bp.route("/edit/<int:note_id>", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "DRA")
def edit_note(note_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM progress_notes
        WHERE id = ?
    """, (note_id,))

    note = cur.fetchone()

    if not note or note["status"] != "DRAFT":
        conn.close()
        return redirect("/admin/encounters")

    if request.method == "POST":

        note_text = request.form.get("note_text")

        cur.execute("""
            UPDATE progress_notes
            SET note_text = ?
            WHERE id = ?
        """, (note_text, note_id))

        conn.commit()

        encounter_id = note["encounter_id"]

        conn.close()

        return redirect(
            url_for(
                "progress_notes_admin.notes_by_encounter",
                encounter_id=encounter_id
            )
        )

    conn.close()

    return render_template(
        "admin/note_edit.html",
        note=note
    )