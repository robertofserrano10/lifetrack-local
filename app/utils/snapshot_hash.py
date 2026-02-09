# app/utils/snapshot_hash.py
# FASE E2 — Hash de Snapshot CMS-1500
# Solo lectura. No muta datos.

import json
import hashlib

def compute_snapshot_hash(snapshot: dict) -> str:
    """
    Calcula un hash SHA-256 estable del snapshot CMS-1500.
    El orden de claves se normaliza para consistencia.
    """

    normalized = json.dumps(
        snapshot,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
