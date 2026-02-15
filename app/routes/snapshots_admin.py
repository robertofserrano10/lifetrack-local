from flask import Blueprint, render_template
from app.db.cms1500_snapshot import list_snapshots_admin

snapshots_admin_bp = Blueprint(
    "snapshots_admin",
    __name__,
    url_prefix="/admin/snapshots",
)

@snapshots_admin_bp.route("/", methods=["GET"])
def snapshots_index():
    """
    Vista administrativa de snapshots CMS-1500.
    READ-ONLY.
    No recalcula nada.
    """
    snapshots = list_snapshots_admin()
    return render_template(
        "admin/snapshots_index.html",
        snapshots=snapshots,
    )

from app.db.cms1500_snapshot import get_snapshot_by_id
from flask import render_template, abort

# CORRECCIÓN: eliminar duplicación de prefijo
@snapshots_admin_bp.route("/<int:snapshot_id>")
def snapshot_detail(snapshot_id: int):

    snap = get_snapshot_by_id(snapshot_id)

    if not snap:
        abort(404)

    return render_template(
        "admin/snapshot_detail.html",
        snapshot=snap
    )
