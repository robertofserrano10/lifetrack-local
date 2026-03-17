from flask import Blueprint, render_template, redirect, url_for
from app.security.auth import login_required, role_required
from app.db.progress_notes import get_all_notes
from app.db.encounters import get_all_encounters

clinical_admin_bp = Blueprint(
    "clinical_admin",
    __name__,
    url_prefix="/admin/clinical",
)


@clinical_admin_bp.route("/")
@login_required
@role_required("ADMIN", "DRA")
def clinical_home():
    encounters = get_all_encounters()
    return render_template("admin/clinical_dashboard.html", encounters=encounters)


@clinical_admin_bp.route("/notes")
@login_required
@role_required("ADMIN", "DRA")
def clinical_notes():
    notes = get_all_notes()
    return render_template("admin/clinical_notes.html", notes=notes)


@clinical_admin_bp.route("/redirect")
@login_required
@role_required("ADMIN", "DRA")
def clinical_redirect():
    return redirect(url_for("clinical_admin.clinical_home"))
