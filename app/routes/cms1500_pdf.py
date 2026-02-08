# app/routes/cms1500_pdf.py
# FASE C2 — Generación de PDF legal CMS-1500
# Solo lectura. No modifica datos. No genera snapshot.
# Motor: Playwright (Chromium)

from flask import Blueprint, render_template, make_response
import tempfile
import os
from playwright.sync_api import sync_playwright

# USAMOS EXACTAMENTE LAS MISMAS FUENTES QUE main.py
from app.views.cms1500_render import get_latest_snapshot_by_claim

cms1500_pdf_bp = Blueprint("cms1500_pdf", __name__)

@cms1500_pdf_bp.route("/cms1500/<int:claim_id>/pdf")
def cms1500_pdf(claim_id):
    """
    Genera PDF legal (Letter) del CMS-1500.
    Siempre usa snapshot existente.
    No recalcula. No escribe. No muta estado.
    """

    # 1) Obtener snapshot (igual que vista HTML)
    snapshot = get_latest_snapshot_by_claim(claim_id)
    if not snapshot:
        return "No hay snapshot para este claim", 404

    # 2) Renderizar HTML EXACTO
    html = render_template("cms1500.html", snapshot=snapshot)

    # 3) Generar PDF con Chromium
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "cms1500.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{html_path.replace(os.sep, '/')}")
            pdf_bytes = page.pdf(
                format="Letter",
                print_background=True
            )
            browser.close()

    # 4) Respuesta HTTP
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=CMS1500_claim_{claim_id}_snapshot.pdf"
    )

    return response
