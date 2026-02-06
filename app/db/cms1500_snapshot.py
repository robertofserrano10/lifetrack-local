import json
import hashlib
from datetime import datetime
from app.db.connection import get_connection


def generate_cms1500_snapshot(claim_id: int):
    """
    Genera un snapshot inmutable de la CMS-1500 para un claim.
    Snapshot = lectura fiel de DB, sin inventar datos.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # =========================
        # CLAIM
        # =========================
        cur.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        claim = cur.fetchone()
        if not claim:
            raise ValueError("Claim no existe")

        claim_data = dict(claim)

        # =========================
        # PATIENT (2–8 básicos)
        # =========================
        cur.execute("SELECT * FROM patients WHERE id = ?", (claim_data["patient_id"],))
        p = cur.fetchone()
        patient = {
            "first_name": p["first_name"] if p else None,
            "last_name": p["last_name"] if p else None,
            "date_of_birth": p["date_of_birth"] if p else None,
            "sex": None,
            "address": None,
            "city": None,
            "state": None,
            "zip": None,
            "insured_relationship": "self",
        }

        # =========================
        # INSURANCE / PAYER (1, 9–11 básicos)
        # =========================
        cur.execute("SELECT * FROM coverages WHERE id = ?", (claim_data["coverage_id"],))
        c = cur.fetchone()
        insurance = {
            "insurer_name": c["insurer_name"] if c else None,
            "plan_name": c["plan_name"] if c else None,
            "policy_number": c["policy_number"] if c else None,
            "group_number": c["group_number"] if c else None,
            "insured_id": c["insured_id"] if c else None,
            "start_date": c["start_date"] if c else None,
            "end_date": c["end_date"] if c else None,
        }

        # =========================
        # SERVICES (24A–24J) + Box 20 at service-level
        # =========================
        cur.execute(
            """
            SELECT *
            FROM services
            WHERE claim_id = ?
            ORDER BY service_date
            """,
            (claim_id,),
        )
        services = [dict(row) for row in cur.fetchall()]

        # Dx pointer (para render simple)
        for s in services:
            s["dx_pointer"] = "A" if s.get("diagnosis_code") else None

        # =========================
        # DIAGNOSES (21)
        # =========================
        diagnoses = {
            "A": services[0]["diagnosis_code"] if services else None,
            "B": None,
            "C": None,
            "D": None,
        }

        # =========================
        # TOTALS (28–30)
        # =========================
        cur.execute(
            """
            SELECT SUM(amount) AS total_charge
            FROM charges
            WHERE service_id IN (SELECT id FROM services WHERE claim_id = ?)
            """,
            (claim_id,),
        )
        total_charge = cur.fetchone()["total_charge"] or 0.0

        cur.execute(
            """
            SELECT SUM(amount_applied) AS amount_paid
            FROM applications
            WHERE charge_id IN (
                SELECT id FROM charges
                WHERE service_id IN (SELECT id FROM services WHERE claim_id = ?)
            )
            """,
            (claim_id,),
        )
        amount_paid = cur.fetchone()["amount_paid"] or 0.0

        cur.execute(
            """
            SELECT SUM(amount) AS total_adjustments
            FROM adjustments
            WHERE charge_id IN (
                SELECT id FROM charges
                WHERE service_id IN (SELECT id FROM services WHERE claim_id = ?)
            )
            """,
            (claim_id,),
        )
        total_adjustments = cur.fetchone()["total_adjustments"] or 0.0

        totals = {
            "total_charge": float(total_charge),
            "amount_paid": float(amount_paid),
            "total_adjustments": float(total_adjustments),
            "balance_due": float(total_charge - amount_paid - total_adjustments),
        }

        # =========================
        # PROVIDER SETTINGS (31–33) — desde DB
        # =========================
        cur.execute(
            """
            SELECT *
            FROM provider_settings
            WHERE active = 1
            ORDER BY id
            LIMIT 1
            """
        )
        ps = cur.fetchone()
        psd = dict(ps) if ps else None

        provider = {
            "signature": (psd.get("signature") if psd else "Signature on File"),
            "signature_date": (psd.get("signature_date") if psd else None),
            "facility": {
                "name": psd.get("facility_name") if psd else None,
                "address": psd.get("facility_address") if psd else None,
                "city": psd.get("facility_city") if psd else None,
                "state": psd.get("facility_state") if psd else None,
                "zip": psd.get("facility_zip") if psd else None,
            },
            "billing": {
                "name": psd.get("billing_name") if psd else None,
                "npi": psd.get("billing_npi") if psd else None,
                "tax_id": psd.get("billing_tax_id") if psd else None,
                "address": psd.get("billing_address") if psd else None,
                "city": psd.get("billing_city") if psd else None,
                "state": psd.get("billing_state") if psd else None,
                "zip": psd.get("billing_zip") if psd else None,
            },
        }

        # =========================
        # CLAIM-LEVEL CMS fields (17/19/22/23)
        # =========================
        claim_cms = {
            "box17_referring_provider": {
                "name": claim_data.get("referring_provider_name"),
                "npi": claim_data.get("referring_provider_npi"),
            },
            "box19_reserved_local_use": claim_data.get("reserved_local_use_19"),
            "box22_resubmission": {
                "code": claim_data.get("resubmission_code_22"),
                "original_ref_no": claim_data.get("original_ref_no_22"),
            },
            "box23_prior_authorization": claim_data.get("prior_authorization_23"),
        }

        # =========================
        # META
        # =========================
        meta = {
            "claim_status": claim_data.get("status"),
            "snapshot_version": "5.1",
            "timezone": "PR",
            "generated_by": "system",
        }

        snapshot = {
            "claim": claim_data,
            "patient": patient,
            "insurance": insurance,
            "diagnoses": diagnoses,
            "services": services,
            "totals": totals,
            "provider": provider,
            "claim_cms": claim_cms,
            "meta": meta,
            "generated_at": datetime.utcnow().isoformat(),
        }

        snapshot_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        snapshot_hash = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()

        cur.execute(
            """
            INSERT INTO cms1500_snapshots (claim_id, snapshot_json, snapshot_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (claim_id, snapshot_json, snapshot_hash, datetime.utcnow().isoformat()),
        )
        conn.commit()

        return {"hash": snapshot_hash, "snapshot": snapshot}
