import json
import hashlib
from app.db.connection import get_connection


def canonical_json(data):
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run_snapshot_integrity_scan():

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, claim_id, snapshot_json, snapshot_hash
            FROM cms1500_snapshots
            ORDER BY id
        """)

        rows = cur.fetchall()

    total = 0
    failures = []

    for row in rows:
        total += 1

        snapshot_id = row["id"]
        claim_id = row["claim_id"]
        stored_hash = row["snapshot_hash"]

        parsed = json.loads(row["snapshot_json"])
        recalculated_hash = sha256(canonical_json(parsed))

        if stored_hash != recalculated_hash:
            failures.append({
                "snapshot_id": snapshot_id,
                "claim_id": claim_id,
                "stored_hash": stored_hash,
                "recalculated_hash": recalculated_hash,
            })

    print("=== G39 SNAPSHOT INTEGRITY SCAN ===")
    print(f"Total snapshots scanned: {total}")

    if not failures:
        print("RESULT: ALL SNAPSHOTS VALID ✅")
    else:
        print("RESULT: INTEGRITY FAILURES DETECTED ❌")
        for f in failures:
            print(f)


if __name__ == "__main__":
    run_snapshot_integrity_scan()