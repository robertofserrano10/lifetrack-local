# scripts/test_snapshot_dx_pointer.py
import json
import hashlib
import sqlite3
from copy import deepcopy
from datetime import datetime

DB_PATH = "storage/lifetrack.db"

# ===== CONFIGURACIÓN DE PRUEBA =====
BASE_CLAIM_ID = 1        # claim existente del que clonar snapshot
TEST_CLAIM_ID = 9999     # claim_id aislado para pruebas
DX_POINTER_TEST = "AB"   # prueba: "AB", "A,C", "A C", None
# ==================================


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) Obtener último snapshot del claim base
    cur.execute(
        """
        SELECT snapshot_json
        FROM cms1500_snapshots
        WHERE claim_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (BASE_CLAIM_ID,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("No existe snapshot base para el claim indicado.")

    base_snapshot = json.loads(row["snapshot_json"])
    test_snapshot = deepcopy(base_snapshot)

    # 2) Ajustar metadata
    test_snapshot["meta"]["claim_id"] = TEST_CLAIM_ID
    test_snapshot["meta"]["created_at"] = datetime.utcnow().isoformat()
    test_snapshot["meta"]["version"] = "TEST-DX-POINTER"

    test_snapshot["claim"]["id"] = TEST_CLAIM_ID

    # 3) Modificar SOLO dx_pointer en servicios
    for s in test_snapshot.get("services", []):
        s["dx_pointer"] = DX_POINTER_TEST

    # 4) Canonicalizar + hash
    snapshot_json = canonical_json(test_snapshot)
    snapshot_hash = sha256(snapshot_json)

    # 5) Insertar snapshot de prueba
    cur.execute(
        """
        INSERT INTO cms1500_snapshots (claim_id, snapshot_json, snapshot_hash)
        VALUES (?, ?, ?)
        """,
        (TEST_CLAIM_ID, snapshot_json, snapshot_hash),
    )

    conn.commit()
    conn.close()

    print("SNAPSHOT DE PRUEBA INSERTADO")
    print(f"claim_id prueba: {TEST_CLAIM_ID}")
    print(f"dx_pointer usado: {DX_POINTER_TEST}")
    print(f"snapshot_hash: {snapshot_hash}")


if __name__ == "__main__":
    main()
