import json
import hashlib
from datetime import datetime
from app.db.connection import get_connection


def generate_cms1500_snapshot(claim_id: int):
    """
    Genera un snapshot inmutable de la CMS-1500 para un claim.
    Calcula totales reales (28–30) desde charges, applications y adjustments.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        # -----------------
        # Claim
        # -----------------
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

        # -----------------
        # Services
        # -----------------
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
        services = [dict(row) for row in cur.fetchall()]

        service_ids = [s["id"] for s in services]

        # -----------------
        # Charges
        # -----------------
        if service_ids:
            q_marks = ",".join("?" for _ in service_ids)
            cur.execute(
                f"""
                SELECT id, service_id, amount
                FROM charges
                WHERE service_id IN ({q_marks})
                """,
                service_ids,
            )
            charges = [dict(r) for r in cur.fetchall()]
        else:
            charges = []

        charge_ids = [c["id"] for c in charges]

        total_charge = sum(c["amount"] for c in charges)

        # -----------------
        # Applications (Payments applied)
        # -----------------
        if charge_ids:
            q_marks = ",".join("?" for _ in charge_ids)
            cur.execute(
                f"""
                SELECT amount_applied
                FROM applications
                WHERE charge_id IN ({q_marks})
                """,
                charge_ids,
            )
            applications = [r["amount_applied"] for r in cur.fetchall()]
        else:
            applications = []

        amount_paid = sum(applications)

        # -----------------
        # Adjustments
        # -----------------
        if charge_ids:
            q_marks = ",".join("?" for _ in charge_ids)
            cur.execute(
                f"""
                SELECT amount
                FROM adjustments
                WHERE charge_id IN ({q_marks})
                """,
                charge_ids,
            )
            adjustments = [r["amount"] for r in cur.fetchall()]
        else:
            adjustments = []

        total_adjustments = sum(adjustments)

        balance_due = total_charge - amount_paid - total_adjustments

        # -----------------
        # Provider (placeholder fijo por ahora)
        # -----------------
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

        totals = {
            "total_charge": float(total_charge),
            "amount_paid": float(amount_paid),
            "total_adjustments": float(total_adjustments),
            "balance_due": float(balance_due),
        }

        snapshot = {
            "claim": claim_data,
            "services": services,
            "totals": totals,
            "provider": provider,
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
            ) VALUES (?, ?, ?, ?)
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
