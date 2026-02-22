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