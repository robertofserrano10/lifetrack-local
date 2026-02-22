import json
from datetime import datetime
from app.db.connection import get_connection
from scripts.test_phase_g39_snapshot_integrity_scanner import canonical_json, sha256


EXPORT_PATH = "exports/legal_audit_report.json"


def run_legal_audit_export():

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT s.id, s.claim_id, s.snapshot_json,
                   s.snapshot_hash, s.created_at,
                   c.status as claim_status
            FROM cms1500_snapshots s
            JOIN claims c ON c.id = s.claim_id
            ORDER BY s.id
        """)

        rows = cur.fetchall()

    report = []
    integrity_failures = []

    for row in rows:
        snapshot_id = row["id"]
        claim_id = row["claim_id"]
        stored_hash = row["snapshot_hash"]
        created_at = row["created_at"]
        claim_status = row["claim_status"]

        parsed = json.loads(row["snapshot_json"])
        recalculated_hash = sha256(canonical_json(parsed))

        valid = stored_hash == recalculated_hash

        if not valid:
            integrity_failures.append(snapshot_id)

        report.append({
            "snapshot_id": snapshot_id,
            "claim_id": claim_id,
            "created_at": created_at,
            "claim_status": claim_status,
            "snapshot_hash": stored_hash,
            "integrity_valid": valid,
        })

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_snapshots": len(report),
        "integrity_failures": integrity_failures,
        "snapshots": report,
    }

    with open(EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=== G40 LEGAL AUDIT EXPORT ===")
    print(f"Export file: {EXPORT_PATH}")
    print(f"Total snapshots: {len(report)}")

    if not integrity_failures:
        print("RESULT: AUDIT CLEAN ✅")
    else:
        print("RESULT: INTEGRITY FAILURES DETECTED ❌")
        print(integrity_failures)


if __name__ == "__main__":
    run_legal_audit_export()