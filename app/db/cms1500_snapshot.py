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

        services = []
        for row in cur.fetchall():
            svc = dict(row)

            # Dx Pointer (Casilla 24E) — FASE 3.3
            svc["dx_pointer"] = "A" if svc.get("diagnosis_code") else None

            services.append(svc)

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
        # PROVIDER (31–33)
        # =========================
        provider = {
            "signature": "Dra. Laurangélica Cruz Rodríguez",
            "signature_date": datetime.utcnow().date().isoformat(),
            "facility": {
                "name": "Consulta Psicológica",
                "address": "123 Calle Principal",
                "city": "San Juan",
                "state": "PR",
                "zip": "00901",
            },
            "billing": {
                "name": "Dra. Laurangélica Cruz Rodríguez",
                "npi": "1234567890",
                "tax_id": "XX-XXXXXXX",
                "address": "123 Calle Principal",
                "city": "San Juan",
                "state": "PR",
                "zip": "00901",
            },
        }

        # =========================
        # META (Control interno)
        # =========================
        meta = {
            "claim_status": claim_data["status"],
            "snapshot_version": "3.3",
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
