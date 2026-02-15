from flask import Flask, render_template

from app.views.cms1500_render import get_latest_snapshot_by_claim
from app.utils.snapshot_hash import compute_snapshot_hash  # ← AÑADIDO

from app.routes.patients import patients_bp
from app.routes.coverages import coverages_bp
from app.routes.provider_settings import provider_settings_bp
from app.routes.cms1500_pdf import cms1500_pdf_bp  # FASE C2 — PDF CMS-1500
from app.routes.claim_balance import claim_balance_bp
from app.routes.charge_balance import charge_balance_bp
from app.routes.claim_payments import claim_payments_bp
from app.routes.claim_adjustments import claim_adjustments_bp
from app.routes.claim_financial_summary import claim_financial_summary_bp
from app.routes.payment_balance import payment_balance_bp
from app.routes.claims_overview import claims_overview_bp

app = Flask(__name__)

# Blueprints existentes
app.register_blueprint(patients_bp)
app.register_blueprint(coverages_bp)
app.register_blueprint(provider_settings_bp)
app.register_blueprint(claim_balance_bp)
app.register_blueprint(charge_balance_bp)
app.register_blueprint(claim_payments_bp)
app.register_blueprint(claim_adjustments_bp)
app.register_blueprint(claim_financial_summary_bp)
app.register_blueprint(payment_balance_bp)
app.register_blueprint(claims_overview_bp)

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
