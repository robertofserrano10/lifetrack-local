import json
import hashlib
from app.db.connection import get_connection
from app.db.pre_cms import get_claim_with_services


def _compute_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def generate_cms1500_snapshot(claim_id: int) -> dict:
    """
    Genera y persiste un snapshot CMS-1500 para un claim válido.
    Devuelve el snapshot creado.
    """
    data = get_claim_with_services(claim_id)
    if not data:
        raise ValueError("Claim no existe")

    claim = data["claim"]
    services = data["services"]

    # Totales mínimos (se pueden extender luego)
    total_units = sum(s["units"] for s in services)

    snapshot_payload = {
        "claim": {
            "id": claim["id"],
            "patient_id": claim["patient_id"],
            "coverage_id": claim["coverage_id"],
            "status": claim["status"],
            "created_at": claim["created_at"],
        },
        "services": services,
        "totals": {
            "total_units": total_units
        },
        "version": "cms1500_v1"
    }

    snapshot_hash = _compute_hash(snapshot_payload)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cms1500_snapshots (
                claim_id,
                snapshot_json,
                snapshot_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                claim_id,
                json.dumps(snapshot_payload),
                snapshot_hash,
            ),
        )
        conn.commit()

    return {
        "claim_id": claim_id,
        "snapshot": snapshot_payload,
        "hash": snapshot_hash,
    }


def get_snapshots_by_claim(claim_id: int):
    """
    Devuelve todos los snapshots de un claim (histórico).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, claim_id, snapshot_json, snapshot_hash, created_at
            FROM cms1500_snapshots
            WHERE claim_id = ?
            ORDER BY created_at
            """,
            (claim_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
