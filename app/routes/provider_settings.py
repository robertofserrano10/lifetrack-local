from flask import Blueprint, render_template, request, redirect, url_for

from app.db.provider_settings import get_provider_settings, update_provider_settings

provider_settings_bp = Blueprint("provider_settings", __name__)


@provider_settings_bp.route("/provider/edit", methods=["GET"])
def edit_provider_settings():
    ps = get_provider_settings()
    return render_template("provider/edit.html", ps=ps)


@provider_settings_bp.route("/provider/edit", methods=["POST"])
def update_provider_settings_view():
    # =========================
    # MAPEO / NORMALIZACIÓN
    # =========================
    # Si el template viejo envía provider_name/provider_npi/provider_tax_id,
    # lo traducimos a billing_* para que no rompa.
    billing_name = request.form.get("billing_name") or request.form.get("provider_name")
    billing_npi = request.form.get("billing_npi") or request.form.get("provider_npi")
    billing_tax_id = request.form.get("billing_tax_id") or request.form.get("provider_tax_id")

    fields = {
        # Signatures
        "signature": request.form.get("signature"),
        "signature_date": request.form.get("signature_date"),

        # Facility (32)
        "facility_name": request.form.get("facility_name"),
        "facility_address": request.form.get("facility_address"),
        "facility_city": request.form.get("facility_city"),
        "facility_state": request.form.get("facility_state"),
        "facility_zip": request.form.get("facility_zip"),

        # Billing (33)
        "billing_name": billing_name,
        "billing_npi": billing_npi,
        "billing_tax_id": billing_tax_id,
        "billing_address": request.form.get("billing_address"),
        "billing_city": request.form.get("billing_city"),
        "billing_state": request.form.get("billing_state"),
        "billing_zip": request.form.get("billing_zip"),
    }

    # Remover None para no pisar campos si vienen vacíos por accidente
    fields = {k: v for k, v in fields.items() if v is not None}

    update_provider_settings(**fields)
    return redirect(url_for("provider_settings.edit_provider_settings"))
