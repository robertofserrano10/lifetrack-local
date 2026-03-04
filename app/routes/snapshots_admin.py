from flask import Blueprint, render_template, abort, jsonify, request

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
    snapshots = list_snapshots_admin()
    return render_template(
        "admin/snapshots_index.html",
        snapshots=snapshots,
    )


@snapshots_admin_bp.route("/<int:snapshot_id>", methods=["GET"])
def snapshot_detail(snapshot_id: int):

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
# G44 — Snapshot API
# =========================================================

@snapshots_admin_bp.route("/api", methods=["GET"])
def snapshots_api():

    snapshots = list_snapshots_admin()

    return jsonify(snapshots)


@snapshots_admin_bp.route("/api/<int:snapshot_id>", methods=["GET"])
def snapshot_api(snapshot_id: int):

    snap = get_snapshot_by_id(snapshot_id)

    if not snap:
        abort(404)

    return jsonify(snap)


# =========================================================
# G45 — Snapshot Diff Auditoría
# =========================================================

def _flatten(prefix, obj, out):

    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten(f"{prefix}.{k}" if prefix else k, v, out)

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _flatten(f"{prefix}[{i}]", v, out)

    else:
        out[prefix] = obj


@snapshots_admin_bp.route("/diff", methods=["GET"])
def snapshot_diff():

    """
    Compara dos snapshots y muestra los cambios.
    Uso:
    /admin/snapshots/diff?a=1&b=2
    """

    a = request.args.get("a", type=int)
    b = request.args.get("b", type=int)

    if not a or not b:
        return "Parámetros requeridos: a y b", 400

    snap_a = get_snapshot_by_id(a)
    snap_b = get_snapshot_by_id(b)

    if not snap_a or not snap_b:
        abort(404)

    flat_a = {}
    flat_b = {}

    _flatten("", snap_a["snapshot"], flat_a)
    _flatten("", snap_b["snapshot"], flat_b)

    keys = set(flat_a.keys()) | set(flat_b.keys())

    diff = []

    for k in sorted(keys):

        va = flat_a.get(k)
        vb = flat_b.get(k)

        if va != vb:

            diff.append(
                {
                    "field": k,
                    "version_a": va,
                    "version_b": vb,
                }
            )

    return render_template(
        "admin/snapshot_diff.html",
        snapshot_a=snap_a,
        snapshot_b=snap_b,
        diff=diff,
    )