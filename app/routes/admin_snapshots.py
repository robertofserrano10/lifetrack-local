from flask import Blueprint, render_template
import sqlite3
from app.config import DB_PATH

snapshots_admin_bp = Blueprint(
    "snapshots_admin",
    __name__,
    url_prefix="/admin/snapshots",
)

@snapshots_admin_bp.route("/")
def snapshots_list():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            cms1500_snapshots.id AS snapshot_id,
            cms1500_snapshots.version_number,
            cms1500_snapshots.created_at,
            cms1500_snapshots.snapshot_hash,
            claims.claim_number
        FROM cms1500_snapshots
        JOIN claims ON cms1500_snapshots.claim_id = claims.id
        ORDER BY cms1500_snapshots.created_at DESC
    """)

    snapshots = cur.fetchall()

    conn.close()

    return render_template(
        "admin/snapshots_index.html",
        snapshots=snapshots
    )