# scripts/test_phase_g28_snapshot_import_verify.py
# FASE G28 — Snapshot Import (Verificación de integridad)
# SOLO LECTURA. No escribe en DB.

import json
import hashlib
import os
import sys


def _canonical_json(data):
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    print("=== TEST G28: SNAPSHOT IMPORT VERIFY ===")

    if len(sys.argv) < 2:
        print("Uso:")
        print("python -m scripts.test_phase_g28_snapshot_import_verify exports/claim_X_snapshot_export.json")
        return

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        raise ValueError(f"Archivo no existe: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "snapshot" not in payload:
        raise ValueError("Archivo inválido: no contiene 'snapshot'")

    if "snapshot_hash" not in payload:
        raise ValueError("Archivo inválido: no contiene 'snapshot_hash'")

    snapshot = payload["snapshot"]
    stored_hash = payload["snapshot_hash"]

    canonical = _canonical_json(snapshot)
    computed_hash = _sha256(canonical)

    if computed_hash != stored_hash:
        raise ValueError(
            f"HASH_MISMATCH stored={stored_hash} computed={computed_hash}"
        )

    print("OK: JSON válido")
    print("OK: snapshot presente")
    print("OK: hash coincide")
    print("SNAPSHOT IMPORT VERIFY PASSED ✅")


if __name__ == "__main__":
    main()
