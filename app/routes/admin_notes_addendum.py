from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

from app.config import DB_PATH
from app.security.auth import login_required, role_required


notes_addendum_admin_bp = Blueprint(
    "notes_addendum_admin",
    __name__,
    url_prefix="/admin/notes",
)


@notes_addendum_admin_bp.route("/addendum/<int:note_id>", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "DRA")
def add_addendum(note_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, encounter_id, status
        FROM progress_notes
        WHERE id = ?
    """, (note_id,))

    note = cur.fetchone()

    if not note or note["status"] != "SIGNED":
        conn.close()
        return redirect("/admin/encounters")

    if request.method == "POST":

        addendum_text = request.form.get("addendum_text")

        cur.execute("""
            INSERT INTO progress_note_addendums (
                note_id,
                addendum_text
            )
            VALUES (?,?)
        """, (note_id, addendum_text))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "progress_notes_admin.notes_by_encounter",
                encounter_id=note["encounter_id"]
            )
        )

    conn.close()

    return render_template(
        "admin/note_addendum.html",
        note_id=note_id
    )