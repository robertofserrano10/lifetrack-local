# CMS-1500 Snapshot — Operación e Invariantes

## Alcance
Este documento describe el comportamiento inmutable del CMS-1500 Snapshot en LifeTrack.

## Invariantes
- El CMS-1500 se genera exclusivamente desde un snapshot existente.
- El snapshot es inmutable.
- No se recalcula información.
- No se muta estado.
- No se escriben datos.
- HTML y PDF representan el mismo snapshot.

## Flujo
1. GET /cms1500/<claim_id>
   - Renderiza HTML desde snapshot.
2. GET /cms1500/<claim_id>/pdf
   - Renderiza el MISMO HTML.
   - Genera PDF Letter mediante Chromium (Playwright).

## Archivos críticos (NO TOCAR)
- app/templates/cms1500.html
- app/routes/cms1500_pdf.py
- app/views/cms1500_render.py
- app/static/css/cms1500_print.css

## Validación visual
- HTML y PDF deben coincidir visualmente.
- Cualquier cambio visual requiere nueva fase explícita.

## Cumplimiento
- Diseño alineado a CMS-1500 NUCC.
- Uso de "Signature on File" en casillas 12 y 13.
