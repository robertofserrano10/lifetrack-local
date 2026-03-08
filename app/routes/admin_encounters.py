from flask import Blueprint, render_template

from app.db.encounters import get_all_encounters
from app.security.auth import login_required, role_required


encounters_admin_bp = Blueprint(
    "encounters_admin",
    __name__,
    url_prefix="/admin/encounters",
)


@encounters_admin_bp.route("/")
@login_required
@role_required("ADMIN", "DRA")
def encounters_list():

    encounters = get_all_encounters()

    return render_template(
        "admin/encounters_list.html",
        encounters=encounters
    )