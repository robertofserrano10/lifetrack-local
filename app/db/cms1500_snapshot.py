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

        # Claim
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

        # Services + Charges
        cur.execute(
            """
            SELECT
                s.id,
                s.claim_id,
                s.service_date,
                s.cpt_code,
                s.units,
                s.diagnosis_code,
                s.description,
                s.created_at,
                s.updated_at,
                c.amount AS charge_amount
            FROM services s
            LEFT JOIN charges c ON c.service_id = s.id
            WHERE s.claim_id = ?
            ORDER BY s.service_date
            """,
            (claim_id,),
        )

        services = []
        total_charge = 0.0

        for row in cur.fetchall():
            service = dict(row)
            amount = service.get("charge_amount") or 0.0
            total_charge += amount
            services.append(service)

        totals = {
            "total_charge": round(total_charge, 2),
            "amount_paid": 0.0,
            "balance_due": round(total_charge, 2),
        }

        provider = {
            "signature": "Dra. Laurangélica Cruz Rodríguez",
            "signature_date": datetime.utcnow().date().isoformat(),
            "billing": {
                "name": "Dra. Laurangélica Cruz Rodríguez",
                "npi": "1234567890",
            },
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
            "snapshot": snapshot
        }
