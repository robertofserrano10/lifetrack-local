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
        # SERVICES DEL CLAIM
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
        services = [dict(row) for row in cur.fetchall()]

        # =========================
        # DX POINTER (CASILLA 21)
        # =========================

        # 1. Diagnósticos únicos (máx 4)
        diagnosis_list = []
        for s in services:
            code = s["diagnosis_code"]
            if code and code not in diagnosis_list:
                diagnosis_list.append(code)
            if len(diagnosis_list) == 4:
                break

        # 2. Mapear A/B/C/D
        labels = ["A", "B", "C", "D"]
        dx_map = {}
        for i, code in enumerate(diagnosis_list):
            dx_map[labels[i]] = code

        diagnoses = {
            "A": dx_map.get("A"),
            "B": dx_map.get("B"),
            "C": dx_map.get("C"),
            "D": dx_map.get("D"),
        }

        # =========================
        # SERVICES SNAPSHOT (24A–24J)
        # =========================
        snapshot_services = []

        for s in services:
            dx_pointer = None
            for label, code in dx_map.items():
                if s["diagnosis_code"] == code:
                    dx_pointer = label
                    break

            snapshot_services.append({
                "service_date": s["service_date"],   # 24A
                "pos": "11",                          # 24B (Office)
                "emg": "N",                           # 24C
                "cpt_code": s["cpt_code"],            # 24D
                "dx_pointer": dx_pointer,              # 24E ✅
                "charges": None,                       # 24F (pendiente tarifas)
                "units": s["units"],                   # 24G
            })

        # =========================
        # TOTALES (28–30)
        # =========================
        totals = {
            "total_units": sum(s["units"] for s in services),
            "total_charge": None,   # 28
            "amount_paid": 0.00,    # 29
            "balance_due": None     # 30
        }

        # =========================
        # PROVIDER (24J)
        # =========================
        provider = {
    # Casilla 31
    "signature": "Dra. Laurangélica Cruz Rodríguez",
    "signature_date": datetime.utcnow().date().isoformat(),

    # Casilla 32 – Facility / Lugar de servicio
    "facility": {
        "name": "Consulta Psicológica",
        "address": "123 Calle Principal",
        "city": "San Juan",
        "state": "PR",
        "zip": "00901"
    },

    # Casilla 33 – Billing Provider
    "billing": {
        "name": "Dra. Laurangélica Cruz Rodríguez",
        "npi": "1234567890",
        "tax_id": "XX-XXXXXXX",
        "address": "123 Calle Principal",
        "city": "San Juan",
        "state": "PR",
        "zip": "00901"
    }
}


        # =========================
        # SNAPSHOT FINAL
        # =========================
        snapshot = {
            "claim": claim_data,
            "diagnoses": diagnoses,
            "services": snapshot_services,
            "totals": totals,
            "provider": provider,
            "generated_at": datetime.utcnow().isoformat()
        }

        snapshot_json = json.dumps(
            snapshot,
            ensure_ascii=False,
            sort_keys=True
        )

        snapshot_hash = hashlib.sha256(
            snapshot_json.encode("utf-8")
        ).hexdigest()

        # =========================
        # PERSISTENCIA INMUTABLE
        # =========================
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
