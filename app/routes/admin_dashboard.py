from flask import Blueprint, render_template
import sqlite3

from app.config import DB_PATH

dashboard_admin_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/admin",
)

@dashboard_admin_bp.route("/dashboard")
def dashboard():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM claims")
    total_claims = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM claims WHERE status='SUBMITTED'")
    submitted = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM claims WHERE status='PAID'")
    paid = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM cms1500_snapshots")
    snapshots = cur.fetchone()[0]

    conn.close()

    stats = {
        "total_claims": total_claims,
        "submitted": submitted,
        "paid": paid,
        "snapshots": snapshots,
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats
    )