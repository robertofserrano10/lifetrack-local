import json
import hashlib
from datetime import datetime
from app.db.connection import get_connection


def generate_cms1500_snapshot(claim_id: int):
    """
    Genera un snapshot inmutable de la CMS-1500 para un claim.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        # =========================
        # CLAIM
        # =========================
        cur.execute(
            """
            SELECT id, patient_id, coverage_id, status
            FROM claims
            WHERE id = ?
            """,
            (claim_id,),
        )
        claim = cur.fetchone()
        if not claim:
            raise ValueError("Claim no existe")

        claim_data = dict(claim)

        # =========================
        # PATIENT (Casillas 2–8)
        # =========================
        cur.execute(
            """
            SELECT first_name, last_name, date_of_birth
            FROM patients
            WHERE id = ?
            """,
            (claim_data["patient_id"],),
        )
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
        # INSURANCE / PAYER (1, 9–11)
        # =========================
        cur.execute(
            """
            SELECT insurer_name, plan_name, policy_number,
                   group_number, insured_id, start_date, end_date
            FROM coverages
            WHERE id = ?
            """,
            (claim_data["coverage_id"],),
        )
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
        # SERVICES (24A–24J)
        # =========================
        cur.execute(
            """
            SELECT
                id,
                claim_id,
                service_date,
                cpt_code,
                units,
                diagnosis_code,
                description,
                created_at,
                updated_at
            FROM services
            WHERE claim_id = ?
            ORDER BY service_date
            """,
            (claim_id,),
        )
        raw_services = [dict(row) for row in cur.fetchall()]

        services = []
        for s in raw_services:
            s["dx_pointer"] = "A"
            services.append(s)

        # =========================
        # DIAGNOSES (Casilla 21)
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
            WHERE service_id IN (
                SELECT id FROM services WHERE claim_id = ?
            )
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
                WHERE service_id IN (
                    SELECT id FROM services WHERE claim_id = ?
                )
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
                WHERE service_id IN (
                    SELECT id FROM services WHERE claim_id = ?
                )
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
        # PROVIDER (31–33) desde provider_settings
        # =========================
        from app.db.provider_settings import get_active_provider_settings

        ps = get_active_provider_settings()

        provider = {
            "signature": ps["signature"] if ps else "Signature on File",
            "signature_date": ps["signature_date"] if ps else None,
            "facility": {
                "name": ps["facility_name"] if ps else None,
                "address": ps["facility_address"] if ps else None,
                "city": ps["facility_city"] if ps else None,
                "state": ps["facility_state"] if ps else None,
                "zip": ps["facility_zip"] if ps else None,
            },
            "billing": {
                "name": ps["billing_name"] if ps else None,
                "npi": ps["billing_npi"] if ps else None,
                "tax_id": ps["billing_tax_id"] if ps else None,
                "address": ps["billing_address"] if ps else None,
                "city": ps["billing_city"] if ps else None,
                "state": ps["billing_state"] if ps else None,
                "zip": ps["billing_zip"] if ps else None,
            },
        }


        # =========================
        # META
        # =========================
        meta = {
            "claim_status": claim_data["status"],
            "snapshot_version": "4.4",
            "timezone": "PR",
            "generated_by": "system",
        }

        # =========================
        # SNAPSHOT FINAL
        # =========================
        snapshot = {
            "claim": claim_data,
            "patient": patient,
            "insurance": insurance,
            "diagnoses": diagnoses,
            "services": services,
            "totals": totals,
            "provider": provider,
            "meta": meta,
            "generated_at": datetime.utcnow().isoformat(),
        }

        snapshot_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        snapshot_hash = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()

        cur.execute(
            """
            INSERT INTO cms1500_snapshots (
                claim_id,
                snapshot_json,
                snapshot_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                claim_id,
                snapshot_json,
                snapshot_hash,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        return {
            "hash": snapshot_hash,
            "snapshot": snapshot,
        }
