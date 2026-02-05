from flask import Flask, render_template

from app.views.cms1500_render import get_latest_snapshot_by_claim

from app.routes.patients import patients_bp
from app.routes.coverages import coverages_bp
from app.routes.provider_settings import provider_settings_bp

app = Flask(__name__)

app.register_blueprint(patients_bp)
app.register_blueprint(coverages_bp)
app.register_blueprint(provider_settings_bp)


@app.route("/cms1500/<int:claim_id>")
def cms1500_view(claim_id):
    snapshot = get_latest_snapshot_by_claim(claim_id)
    if not snapshot:
        return "No hay snapshot para este claim", 404
    return render_template("cms1500.html", snapshot=snapshot)


print("LifeTrack local iniciado")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
