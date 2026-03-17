from flask import Blueprint, render_template, redirect, url_for, abort, request

from app.db.progress_notes import (
    get_notes_by_encounter,
    get_note_by_id,
    get_addendums_by_note,
    sign_note,
    addendum_note,
)
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


@progress_notes_admin_bp.route("/view/<int:note_id>")
@login_required
@role_required("ADMIN", "DRA")
def note_detail(note_id):
    note = get_note_by_id(note_id)
    if not note:
        abort(404)
    addendums = get_addendums_by_note(note_id)
    return render_template("admin/note_detail.html", note=note, addendums=addendums)


@progress_notes_admin_bp.route("/sign/<int:note_id>", methods=["POST"])
@login_required
@role_required("ADMIN", "DRA")
def note_sign(note_id):
    note = get_note_by_id(note_id)
    if not note:
        abort(404)
    sign_note(note_id)
    return redirect(url_for("progress_notes_admin.note_detail", note_id=note_id))


@progress_notes_admin_bp.route("/addendum/<int:note_id>", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "DRA")
def note_addendum(note_id):
    original = get_note_by_id(note_id)
    if not original:
        abort(404)

    if not original["signed"]:
        abort(400, "Solo se puede agregar un addendum a una nota firmada.")

    if request.method == "POST":
        addendum_text = request.form.get("addendum_text", "").strip()
        if not addendum_text:
            return render_template(
                "admin/note_addendum.html",
                original=original,
                error="El addendum no puede estar vacío."
            )
        addendum_note(note_id, addendum_text)
        return redirect(url_for("progress_notes_admin.note_detail", note_id=note_id))

    return render_template("admin/note_addendum.html", original=original)