import json
from app.db.connection import get_connection


def get_latest_snapshot_by_claim(claim_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT snapshot_json
            FROM cms1500_snapshots
            WHERE claim_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (claim_id,),
        )
        row = cur.fetchone()
        return json.loads(row["snapshot_json"]) if row else None
