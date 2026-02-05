from flask import Flask, render_template, request, redirect, url_for

# =========================
# Vistas CMS-1500
# =========================
from app.views.cms1500_render import get_latest_snapshot_by_claim

# =========================
# Blueprints
# =========================
from app.routes.patients import patients_bp
from app.routes.coverages import coverages_bp

# =========================
# DB actions
# =========================
from app.db.patients import update_patient
from app.db.coverages import update_coverage


app = Flask(__name__)

# =========================
# Registrar Blueprints
# =========================
app.register_blueprint(patients_bp)
app.register_blueprint(coverages_bp)

# =========================
# CMS-1500 Snapshot View
# =========================
@app.route("/cms1500/<int:claim_id>")
def cms1500_view(claim_id):
    snapshot = get_latest_snapshot_by_claim(claim_id)
    if not snapshot:
        return "No hay snapshot para este claim", 404
    return render_template("cms1500.html", snapshot=snapshot)

# =========================
# POST — Guardar Paciente
# =========================
@app.route("/patients/<int:patient_id>/edit", methods=["POST"])
def update_patient_view(patient_id):
    update_patient(
        patient_id=patient_id,
        first_name=request.form.get("first_name"),
        last_name=request.form.get("last_name"),
        date_of_birth=request.form.get("date_of_birth"),
    )

    # Blueprint-safe redirect
    return redirect(url_for("patients.edit_patient", patient_id=patient_id))

# =========================
# POST — Guardar Cobertura
# =========================
@app.route("/coverages/<int:coverage_id>/edit", methods=["POST"])
def update_coverage_view(coverage_id):
    update_coverage(
        coverage_id=coverage_id,
        insurer_name=request.form.get("insurer_name"),
        plan_name=request.form.get("plan_name"),
        policy_number=request.form.get("policy_number"),
        group_number=request.form.get("group_number"),
        insured_id=request.form.get("insured_id"),
        start_date=request.form.get("start_date"),
        end_date=request.form.get("end_date"),
    )

    # Blueprint-safe redirect
    return redirect(url_for("coverages.edit_coverage", coverage_id=coverage_id))


print("LifeTrack local iniciado")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
