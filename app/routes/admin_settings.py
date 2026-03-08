from flask import Blueprint, render_template
import sqlite3
from app.config import DB_PATH

from app.security.auth import login_required, role_required


settings_admin_bp = Blueprint(
    "settings_admin",
    __name__,
    url_prefix="/admin/settings",
)


@settings_admin_bp.route("/")
@login_required
@role_required("ADMIN")
def settings_dashboard():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            username,
            role,
            active,
            created_at
        FROM users
        ORDER BY username
        """
    )

    users = cur.fetchall()

    conn.close()

    return render_template(
        "admin/settings_dashboard.html",
        users=users
    )