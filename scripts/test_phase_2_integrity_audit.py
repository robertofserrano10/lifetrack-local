import sqlite3
import json
import hashlib

DB_PATH = "storage/lifetrack.db"


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=== PHASE 2 — GLOBAL SNAPSHOT INTEGRITY AUDIT ===\n")

    cur.execute("SELECT * FROM cms1500_snapshots ORDER BY id ASC")
    snapshots = cur.fetchall()

    if not snapshots:
        print("NO SNAPSHOTS FOUND")
        return

    hash_errors = 0
    financial_drift = 0

    for s in snapshots:
        snapshot_id = s["id"]
        claim_id = s["claim_id"]
        stored_hash = s["snapshot_hash"]
        snapshot_json = s["snapshot_json"]

        recalculated_hash = sha256(snapshot_json)

        if stored_hash != recalculated_hash:
            hash_errors += 1
            print(f"[HASH ERROR] Snapshot {snapshot_id} Claim {claim_id}")
            continue

        payload = json.loads(snapshot_json)
        snapshot_totals = payload.get("totals", {})

        # Recalculate live totals from DB
        cur.execute("""
            SELECT SUM(amount)
            FROM charges
            WHERE service_id IN (
                SELECT id FROM services WHERE claim_id = ?
            )
        """, (claim_id,))
        total_charge = cur.fetchone()[0] or 0.0

        cur.execute("""
            SELECT SUM(amount_applied)
            FROM applications
            WHERE charge_id IN (
                SELECT id FROM charges
                WHERE service_id IN (
                    SELECT id FROM services WHERE claim_id = ?
                )
            )
        """, (claim_id,))
        total_paid = cur.fetchone()[0] or 0.0

        cur.execute("""
            SELECT SUM(amount)
            FROM adjustments
            WHERE charge_id IN (
                SELECT id FROM charges
                WHERE service_id IN (
                    SELECT id FROM services WHERE claim_id = ?
                )
            )
        """, (claim_id,))
        total_adjustments = cur.fetchone()[0] or 0.0

        live_balance = round(total_charge - total_paid - total_adjustments, 2)

        snapshot_balance = round(float(snapshot_totals.get("balance_due", 0.0)), 2)

        if live_balance != snapshot_balance:
            financial_drift += 1
            print(f"[FINANCIAL DRIFT] Snapshot {snapshot_id} Claim {claim_id}")
            print(f"  Snapshot balance: {snapshot_balance}")
            print(f"  Live balance: {live_balance}")

    print("\n=== RESULT ===")

    if hash_errors == 0:
        print("NO HASH DRIFT")
    else:
        print(f"HASH ERRORS: {hash_errors}")

    if financial_drift == 0:
        print("NO FINANCIAL DRIFT")
    else:
        print(f"FINANCIAL DRIFT CASES: {financial_drift}")

    if hash_errors == 0 and financial_drift == 0:
        print("\nALL SNAPSHOTS VERIFIED")

    conn.close()


if __name__ == "__main__":
    main()