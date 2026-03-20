"""
CLAIM SCRUBBER — Fase BB
Valida un claim completo antes de generar el CMS-1500.
Replica el "claim scrubbing" que hacen los clearinghouses reales.

Retorna:
  {
    "ready": True/False,
    "errors": [...],    # Bloquean el envío
    "warnings": [...],  # No bloquean pero deben revisarse
  }
"""

import sqlite3
from app.config import DB_PATH


def scrub_claim(claim_id: int) -> dict:
    errors = []
    warnings = []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()

        # ─────────────────────────────────────────
        # 1. CLAIM existe
        # ─────────────────────────────────────────
        cur.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        claim = cur.fetchone()
        if not claim:
            return {"ready": False, "errors": ["Claim no existe."], "warnings": []}
        claim = dict(claim)

        # ─────────────────────────────────────────
        # 2. PACIENTE — campos críticos CMS-1500
        # ─────────────────────────────────────────
        cur.execute("SELECT * FROM patients WHERE id = ?", (claim["patient_id"],))
        patient = cur.fetchone()
        if not patient:
            errors.append("❌ Paciente no encontrado.")
        else:
            patient = dict(patient)
            if not patient.get("first_name") or not patient.get("last_name"):
                errors.append("❌ Casilla 2: Falta nombre completo del paciente.")
            if not patient.get("date_of_birth"):
                errors.append("❌ Casilla 3: Falta fecha de nacimiento del paciente.")
            if not patient.get("sex") or patient.get("sex") == "U":
                warnings.append("⚠️ Casilla 3: Sexo del paciente no especificado.")
            if not patient.get("address"):
                warnings.append("⚠️ Casilla 5: Falta dirección del paciente.")
            if not patient.get("city"):
                warnings.append("⚠️ Casilla 5: Falta ciudad del paciente.")
            if not patient.get("zip_code"):
                warnings.append("⚠️ Casilla 5: Falta ZIP del paciente.")

        # ─────────────────────────────────────────
        # 3. COVERAGE — campos críticos CMS-1500
        # ─────────────────────────────────────────
        cur.execute("SELECT * FROM coverages WHERE id = ?", (claim["coverage_id"],))
        coverage = cur.fetchone()
        if not coverage:
            errors.append("❌ Coverage no encontrada. El claim debe tener una cobertura.")
        else:
            coverage = dict(coverage)
            if not coverage.get("insurer_name"):
                errors.append("❌ Casilla 1: Falta nombre de la aseguradora.")
            if not coverage.get("plan_name"):
                errors.append("❌ Casilla 1: Falta nombre del plan médico.")
            if not coverage.get("policy_number"):
                errors.append("❌ Casilla 11: Falta número de póliza.")
            if not coverage.get("insured_id"):
                warnings.append("⚠️ Casilla 1a: Falta ID del asegurado.")
            if not coverage.get("insured_first_name") or not coverage.get("insured_last_name"):
                warnings.append("⚠️ Casilla 4: Falta nombre del asegurado principal.")
            if not coverage.get("insured_address"):
                warnings.append("⚠️ Casilla 7: Falta dirección del asegurado.")

        # ─────────────────────────────────────────
        # 4. DIAGNÓSTICOS — casilla 21
        # ─────────────────────────────────────────
        if not claim.get("diagnosis_1"):
            errors.append("❌ Casilla 21A: Falta al menos un diagnóstico ICD-10. Es requerido.")

        # ─────────────────────────────────────────
        # 5. SERVICES — casilla 24
        # ─────────────────────────────────────────
        cur.execute("""
            SELECT * FROM services WHERE claim_id = ? ORDER BY service_date ASC
        """, (claim_id,))
        services = [dict(s) for s in cur.fetchall()]

        if not services:
            errors.append("❌ Casilla 24: El claim no tiene ningún servicio (CPT). Es requerido.")
        else:
            for i, svc in enumerate(services, 1):
                if not svc.get("cpt_code"):
                    errors.append(f"❌ Casilla 24D[{i}]: Service #{svc['id']} no tiene código CPT.")
                if not svc.get("service_date"):
                    errors.append(f"❌ Casilla 24A[{i}]: Service #{svc['id']} no tiene fecha.")
                charge = svc.get("charge_amount_24f") or 0
                if float(charge) <= 0:
                    errors.append(f"❌ Casilla 24F[{i}]: Service #{svc['id']} tiene monto $0.00.")
                if not svc.get("units_24g") or int(svc.get("units_24g") or 0) <= 0:
                    warnings.append(f"⚠️ Casilla 24G[{i}]: Service #{svc['id']} tiene 0 unidades.")

        # ─────────────────────────────────────────
        # 6. CHARGES — verificar que existen
        # ─────────────────────────────────────────
        cur.execute("""
            SELECT SUM(ch.amount) as total
            FROM charges ch
            JOIN services s ON ch.service_id = s.id
            WHERE s.claim_id = ?
        """, (claim_id,))
        charge_total = cur.fetchone()["total"] or 0
        if float(charge_total) <= 0:
            errors.append("❌ Casilla 28: El claim no tiene charges registrados. Total = $0.00.")

        # ─────────────────────────────────────────
        # 7. PROVIDER SETTINGS — casillas 25, 31, 32, 33
        # ─────────────────────────────────────────
        cur.execute("SELECT * FROM provider_settings WHERE active = 1 ORDER BY id DESC LIMIT 1")
        ps = cur.fetchone()
        if not ps:
            errors.append("❌ Casillas 25/31/32/33: No hay Provider Settings configurado. Ve a Settings → Editar Provider.")
        else:
            ps = dict(ps)
            if not ps.get("billing_npi"):
                errors.append("❌ Casilla 33: Falta NPI del billing provider. Ve a Settings → Editar Provider.")
            if not ps.get("billing_tax_id"):
                errors.append("❌ Casilla 25: Falta Tax ID del billing provider. Ve a Settings → Editar Provider.")
            if not ps.get("billing_name"):
                errors.append("❌ Casilla 33: Falta nombre del billing provider. Ve a Settings → Editar Provider.")
            if not ps.get("facility_name"):
                warnings.append("⚠️ Casilla 32: Falta nombre de la facility. Ve a Settings → Editar Provider.")
            if not ps.get("facility_address"):
                warnings.append("⚠️ Casilla 32: Falta dirección de la facility.")

    finally:
        conn.close()

    return {
        "ready": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }