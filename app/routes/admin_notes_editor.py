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

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.first_name,
            p.last_name,
            e.encounter_date
        FROM encounters e
        JOIN patients p ON p.id = e.patient_id
        WHERE e.id = ?
        LIMIT 1
    """, (encounter_id,))

    encounter = cur.fetchone()

    if request.method == "POST":

        subjective = request.form.get("subjective")
        objective = request.form.get("objective")
        assessment = request.form.get("assessment")
        plan = request.form.get("plan")

        suicidal = request.form.get("suicidal")
        homicidal = request.form.get("homicidal")
        risk = request.form.get("risk")

        functioning_social = request.form.get("functioning_social")
        functioning_occupational = request.form.get("functioning_occupational")
        functioning_family = request.form.get("functioning_family")

        medications = request.form.get("medications")
        adherence = request.form.get("adherence")

        note_text = f"""
PATIENT: {encounter['first_name']} {encounter['last_name']}
SERVICE DATE: {encounter['encounter_date']}

--------------------------------------

S — SUBJECTIVE
{subjective}

--------------------------------------

O — OBJECTIVE
{objective}

--------------------------------------

A — ASSESSMENT
{assessment}

--------------------------------------

P — PLAN
{plan}

--------------------------------------

RISK ASSESSMENT
Suicidal ideation: {suicidal}
Homicidal ideation: {homicidal}
Current risk: {risk}

--------------------------------------

FUNCTIONING
Social: {functioning_social}
Occupational: {functioning_occupational}
Family: {functioning_family}

--------------------------------------

MEDICATIONS
Current medications: {medications}
Adherence: {adherence}

--------------------------------------

PROVIDER SIGNATURE
Signature on File
"""

        cur.execute("""
            INSERT INTO progress_notes (
                encounter_id,
                note_text
            )
            VALUES (?,?)
        """, (encounter_id, note_text))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "progress_notes_admin.notes_by_encounter",
                encounter_id=encounter_id
            )
        )

    conn.close()

    return render_template(
        "admin/note_editor.html",
        encounter=encounter,
        encounter_id=encounter_id
    )