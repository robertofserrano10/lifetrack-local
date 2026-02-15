# scripts/test_phase_g27_snapshot_export.py
# FASE G27 — Exportación oficial auditable de snapshot CMS-1500
# Solo lectura. No muta datos.

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "storage/lifetrack.db"
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def export_latest_snapshot(claim_id: int) -> dict:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, snapshot_json, snapshot_hash, created_at
            FROM cms1500_snapshots
            WHERE claim_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (claim_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("No existe snapshot para este claim")

        snapshot = json.loads(row["snapshot_json"])

        export_payload = {
            "export_meta": {
                "exported_at": datetime.utcnow().isoformat(),
                "snapshot_id": row["id"],
                "claim_id": claim_id,
            },
            "snapshot_hash": row["snapshot_hash"],
            "snapshot": snapshot,
        }

        filename = EXPORT_DIR / f"claim_{claim_id}_snapshot_export.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                export_payload,
                f,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )

        return {
            "file": str(filename),
            "snapshot_id": row["id"],
            "snapshot_hash": row["snapshot_hash"],
        }

    finally:
        conn.close()


def main():
    print("=== TEST G27: SNAPSHOT EXPORT ===")

    claim_id = int(input("Claim ID para exportar: ").strip())
    result = export_latest_snapshot(claim_id)

    print("EXPORT OK:")
    print(result)


if __name__ == "__main__":
    main()
