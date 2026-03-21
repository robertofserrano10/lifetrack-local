from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

from app.config import DB_PATH
from app.db.cms1500_snapshot import get_latest_snapshot_by_claim
from app.db.claims import get_claim_financial_status, create_claim

from app.security.auth import login_required, role_required


claims_list_bp = Blueprint(
    "claims_list",
    __name__,
    url_prefix="/admin",
)


@claims_list_bp.route("/claims")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION", "DRA")
def claims_list():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.id,
            c.claim_number,
            c.status,
            p.first_name,
            p.last_name
        FROM claims c
        JOIN patients p ON p.id = c.patient_id
        ORDER BY c.id DESC
    """)

    rows = cur.fetchall()

    claims = []

    for r in rows:

        snapshot = get_latest_snapshot_by_claim(r["id"])

        financial = get_claim_financial_status(r["id"])

        claims.append({
            "id": r["id"],
            "claim_number": r["claim_number"],
            "patient": f'{r["first_name"]} {r["last_name"]}',
            "status": r["status"],
            "financial_status": financial["status"],
            "locked": snapshot is not None,
            "snapshot_version": snapshot["version_number"] if snapshot else None
        })

    conn.close()

    return render_template(
        "admin/claims_list.html",
        claims=claims
    )


# =========================================================
# Claim create
# =========================================================
@claims_list_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR")
def claim_create():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Cargar datos para form
    cur.execute("SELECT id, first_name, last_name FROM patients ORDER BY last_name, first_name")
    patients = cur.fetchall()

    cur.execute("SELECT id, patient_id, insurer_name, plan_name, policy_number FROM coverages ORDER BY id")
    coverages = cur.fetchall()

    selected_patient_id = request.args.get("patient_id")

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        coverage_id = request.form.get("coverage_id")

        if not patient_id or not coverage_id:
            return render_template(
                "admin/claim_form.html",
                patients=patients,
                coverages=coverages,
                selected_patient_id=selected_patient_id,
                error="Patient and coverage are required."
            )

        try:
            claim_id = create_claim(int(patient_id), int(coverage_id))
        except Exception as e:
            return render_template(
                "admin/claim_form.html",
                patients=patients,
                coverages=coverages,
                selected_patient_id=selected_patient_id,
                error=f"Error creando claim: {e}"
            )

        conn.close()
        return redirect(url_for("claims_admin.claim_detail_admin", claim_id=claim_id))

    conn.close()
    return render_template(
        "admin/claim_form.html",
        patients=patients,
        coverages=coverages,
        selected_patient_id=selected_patient_id,
    )