# app/routes/cms1500_pdf.py
# FASE C2 — Generación de PDF legal CMS-1500
# G42 — Export legal con hash visible + auditoría
# Solo lectura. No modifica datos. No genera snapshot.
# Motor: Playwright (Chromium)

from flask import Blueprint, render_template, make_response
import tempfile
import os
from playwright.sync_api import sync_playwright

from app.views.cms1500_render import get_latest_snapshot_by_claim
from app.db.event_ledger import log_event
from app.utils.snapshot_hash import compute_snapshot_hash


cms1500_pdf_bp = Blueprint("cms1500_pdf", __name__)


@cms1500_pdf_bp.route("/cms1500/<int:claim_id>/pdf")
def cms1500_pdf(claim_id):

    """
    Genera PDF legal (Letter) del CMS-1500.

    REGLAS:
    - Usa snapshot congelado
    - No recalcula datos vivos
    - No genera snapshot
    - Incluye hash visible
    - Registra auditoría
    """

    # -------------------------
    # Obtener snapshot
    # -------------------------

    snapshot_record = get_latest_snapshot_by_claim(claim_id)

    if not snapshot_record:
        return "No hay snapshot para este claim", 404

    # Compatibilidad con dos formatos posibles
    if isinstance(snapshot_record, dict) and "snapshot" in snapshot_record:
        snapshot = snapshot_record["snapshot"]
        snapshot_hash = snapshot_record.get(
            "snapshot_hash",
            compute_snapshot_hash(snapshot),
        )
    else:
        snapshot = snapshot_record
        snapshot_hash = compute_snapshot_hash(snapshot)

    # -------------------------
    # Render HTML
    # -------------------------

    html = render_template(
        "cms1500.html",
        snapshot=snapshot,
        snapshot_hash=snapshot_hash,
    )

    # -------------------------
    # Generar PDF
    # -------------------------

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
                print_background=True,
            )

            browser.close()

    # -------------------------
    # Auditoría export
    # -------------------------

    try:
        log_event(
            entity_type="claim",
            entity_id=claim_id,
            event_type="snapshot_pdf_exported",
            event_data={
                "snapshot_hash": snapshot_hash
            },
        )
    except Exception:
        pass

    # -------------------------
    # Respuesta HTTP
    # -------------------------

    response = make_response(pdf_bytes)

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        f"attachment; filename=CMS1500_claim_{claim_id}_snapshot.pdf"
    )

    return response