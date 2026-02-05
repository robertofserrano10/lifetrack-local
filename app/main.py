from flask import Flask, render_template, request, redirect, url_for
from app.views.cms1500_render import get_latest_snapshot_by_claim
from app.routes.patients import patients_bp
from app.db.patients import update_patient

app = Flask(__name__)

# Registrar blueprint de pacientes
app.register_blueprint(patients_bp)


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
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    date_of_birth = request.form.get("date_of_birth")

    update_patient(
        patient_id=patient_id,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
    )

    # 🔴 AQUÍ ESTABA EL ERROR
    # Como es Blueprint → patients.edit_patient
    return redirect(url_for("patients.edit_patient", patient_id=patient_id))


print("LifeTrack local iniciado")

app.run(host="127.0.0.1", port=5000, debug=True)
