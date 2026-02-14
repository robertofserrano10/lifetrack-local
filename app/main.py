from flask import Flask, render_template

from app.views.cms1500_render import get_latest_snapshot_by_claim
from app.utils.snapshot_hash import compute_snapshot_hash  # ← AÑADIDO

from app.routes.patients import patients_bp
from app.routes.coverages import coverages_bp
from app.routes.provider_settings import provider_settings_bp
from app.routes.cms1500_pdf import cms1500_pdf_bp  # FASE C2 — PDF CMS-1500
from app.routes.claim_balance import claim_balance_bp

app = Flask(__name__)

# Blueprints existentes
app.register_blueprint(patients_bp)
app.register_blueprint(coverages_bp)
app.register_blueprint(provider_settings_bp)
app.register_blueprint(claim_balance_bp)

# Blueprint PDF (FASE C2)
app.register_blueprint(cms1500_pdf_bp)

@app.route("/cms1500/<int:claim_id>")
def cms1500_view(claim_id):
    snapshot = get_latest_snapshot_by_claim(claim_id)
    if not snapshot:
        return "No hay snapshot para este claim", 404

    snapshot_hash = compute_snapshot_hash(snapshot)  # ← AÑADIDO

    return render_template(
        "cms1500.html",
        snapshot=snapshot,
        snapshot_hash=snapshot_hash,  # ← AÑADIDO
    )

print("LifeTrack local iniciado")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
