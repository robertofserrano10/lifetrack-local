from flask import Blueprint, redirect, url_for
import sqlite3
from datetime import datetime

from app.config import DB_PATH
from app.security.auth import login_required, role_required


notes_sign_admin_bp = Blueprint(
    "notes_sign_admin",
    __name__,
    url_prefix="/admin/notes",
)


@notes_sign_admin_bp.route("/sign/<int:note_id>")
@login_required
@role_required("ADMIN", "DRA")
def sign_note(note_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        UPDATE progress_notes
        SET
            status = 'SIGNED',
            signed = 1,
            signed_at = ?
        WHERE id = ?
    """, (datetime.utcnow(), note_id))

    conn.commit()

    cur.execute("""
        SELECT encounter_id
        FROM progress_notes
        WHERE id = ?
    """, (note_id,))

    encounter_id = cur.fetchone()["encounter_id"]

    conn.close()

    return redirect(
        url_for(
            "progress_notes_admin.notes_by_encounter",
            encounter_id=encounter_id
        )
    )