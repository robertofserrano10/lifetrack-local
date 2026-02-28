import json
from datetime import datetime
from app.db.connection import get_connection


def log_event(entity_type: str, entity_id: int, event_type: str, event_data: dict | None = None):

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO event_ledger (
                entity_type,
                entity_id,
                event_type,
                event_data,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            entity_type,
            entity_id,
            event_type,
            json.dumps(event_data) if event_data else None,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
def list_events_admin(limit: int = 50, offset: int = 0, claim_id: int | None = None) -> list[dict]:
    with get_connection() as conn:
        cur = conn.cursor()

        if claim_id is not None:
            cur.execute(
                """
                SELECT id, entity_type, entity_id, event_type, event_data, created_at
                FROM event_ledger
                WHERE entity_type = 'claim' AND entity_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (claim_id, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT id, entity_type, entity_id, event_type, event_data, created_at
                FROM event_ledger
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        rows = cur.fetchall()
        return [dict(r) for r in rows]


def count_events_admin(claim_id: int | None = None) -> int:
    with get_connection() as conn:
        cur = conn.cursor()

        if claim_id is not None:
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM event_ledger
                WHERE entity_type='claim' AND entity_id = ?
                """,
                (claim_id,),
            )
        else:
            cur.execute("SELECT COUNT(*) AS n FROM event_ledger")

        return int(cur.fetchone()["n"])