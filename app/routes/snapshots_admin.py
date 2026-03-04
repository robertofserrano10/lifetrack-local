from flask import Blueprint, render_template, abort, jsonify

from app.db.cms1500_snapshot import (
    list_snapshots_admin,
    get_snapshot_by_id,
    verify_snapshot_integrity,
)


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
    """
    snapshots = list_snapshots_admin()
    return render_template(
        "admin/snapshots_index.html",
        snapshots=snapshots,
    )


@snapshots_admin_bp.route("/<int:snapshot_id>", methods=["GET"])
def snapshot_detail(snapshot_id: int):
    """
    Vista detalle de un snapshot CMS-1500.
    READ-ONLY.
    """
    snap = get_snapshot_by_id(snapshot_id)
    if not snap:
        abort(404)

    return render_template(
        "admin/snapshot_detail.html",
        snapshot=snap,
    )


# =========================================================
# G43 — Snapshot Integrity Verification
# =========================================================

@snapshots_admin_bp.route("/<int:snapshot_id>/verify", methods=["GET"])
def snapshot_verify(snapshot_id: int):
    result = verify_snapshot_integrity(snapshot_id)

    snap = get_snapshot_by_id(snapshot_id)
    if not snap:
        abort(404)

    return render_template(
        "admin/snapshot_detail.html",
        snapshot=snap,
        integrity=result,
    )


# =========================================================
# G44 — SNAPSHOT API
# =========================================================

@snapshots_admin_bp.route("/api", methods=["GET"])
def snapshots_api():
    """
    Devuelve listado JSON de snapshots.
    Usado por futura UI.
    """
    snapshots = list_snapshots_admin()
    return jsonify(snapshots)


@snapshots_admin_bp.route("/api/<int:snapshot_id>", methods=["GET"])
def snapshot_api(snapshot_id: int):
    """
    Devuelve snapshot específico en JSON.
    """
    snap = get_snapshot_by_id(snapshot_id)
    if not snap:
        abort(404)

    return jsonify(snap)