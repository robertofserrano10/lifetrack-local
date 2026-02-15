# scripts/test_phase_g26_snapshot_integrity_audit.py
# FASE G26 — Auditoría de integridad de snapshots (modo contable correcto)
# Solo lectura. No muta datos.

import json
import hashlib
import sqlite3
from typing import Any, Dict, List

DB_PATH = "storage/lifetrack.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _round2(x: float) -> float:
    return float(round(float(x), 2))


def main() -> None:
    print("=== TEST G26: SNAPSHOT INTEGRITY AUDIT (hash + internal consistency) ===")

    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, claim_id, snapshot_json, snapshot_hash, created_at
            FROM cms1500_snapshots
            ORDER BY id ASC
            """
        )
        rows = cur.fetchall()

        if not rows:
            print("INFO: No hay snapshots.")
            print("SNAPSHOT AUDIT PASSED ✅")
            return

        failures: List[str] = []
        legacy_drift: List[str] = []

        for r in rows:
            snap_id = int(r["id"])
            claim_id = int(r["claim_id"])
            stored_hash = str(r["snapshot_hash"])
            created_at = r["created_at"]

            try:
                snapshot = json.loads(r["snapshot_json"])
            except Exception as e:
                failures.append(
                    f"snapshot_id={snap_id} claim_id={claim_id} reason=INVALID_JSON error={e}"
                )
                continue

            # 1) Verificar claim_id interno
            meta_claim_id = snapshot.get("meta", {}).get("claim_id")
            if meta_claim_id != claim_id:
                failures.append(
                    f"snapshot_id={snap_id} claim_id={claim_id} reason=CLAIM_ID_MISMATCH meta={meta_claim_id}"
                )

            # 2) Verificar hash
            canonical = _canonical_json(snapshot)
            computed_hash = _sha256(canonical)
            if computed_hash != stored_hash:
                failures.append(
                    f"snapshot_id={snap_id} claim_id={claim_id} reason=HASH_MISMATCH"
                )

            # 3) Verificar consistencia interna de totals
            totals = snapshot.get("totals", {})
            try:
                tc = _round2(float(totals.get("total_charge", 0)))
                ap = _round2(float(totals.get("amount_paid", 0)))
                adj = _round2(float(totals.get("adjustments", 0)))
                bal = _round2(float(totals.get("balance_due", 0)))
            except Exception:
                failures.append(
                    f"snapshot_id={snap_id} claim_id={claim_id} reason=TOTALS_INVALID_TYPE"
                )
                continue

            expected_balance = _round2(tc - ap - adj)
            if bal != expected_balance:
                failures.append(
                    f"snapshot_id={snap_id} claim_id={claim_id} "
                    f"reason=INTERNAL_TOTALS_MISMATCH balance={bal} expected={expected_balance}"
                )

            # 4) Detectar drift histórico (informativo, NO FAIL)
            cur.execute(
                """
                SELECT COALESCE(SUM(c.amount),0)
                FROM charges c
                JOIN services s ON s.id=c.service_id
                WHERE s.claim_id=?
                """,
                (claim_id,),
            )
            db_total_charge = _round2(cur.fetchone()[0])

            if db_total_charge != tc:
                legacy_drift.append(
                    f"snapshot_id={snap_id} claim_id={claim_id} "
                    f"SNAP_total_charge={tc} DB_total_charge={db_total_charge}"
                )

        if failures:
            msg = ["FAIL: Snapshot audit detectó corrupción real:"] + failures
            raise ValueError("\n".join(msg))

        print(f"OK: snapshots auditados = {len(rows)}")
        print("OK: hash válidos")
        print("OK: consistencia interna de totals válida")

        if legacy_drift:
            print(f"INFO: legacy drift detectado en {len(legacy_drift)} snapshot(s)")
            for line in legacy_drift:
                print("  LEGACY_DRIFT:", line)

        print("SNAPSHOT AUDIT PASSED ✅")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
