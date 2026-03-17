import json
from datetime import datetime, timezone
from app.db.connection import get_connection


def _ensure_performed_by_column():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(event_ledger)")
        cols = [r["name"] for r in cur.fetchall()]
        if "performed_by" not in cols:
            conn.execute("ALTER TABLE event_ledger ADD COLUMN performed_by TEXT")
            conn.commit()


def _get_current_username() -> str | None:
    """Lee el usuario activo de la sesion de Flask si existe."""
    try:
        from flask import session
        username = session.get("username")
        if username:
            return username
        # Si no esta en sesion, lo buscamos por user_id
        user_id = session.get("user_id")
        if user_id:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                row = cur.fetchone()
                if row:
                    return row["username"]
    except Exception:
        pass
    return None


def log_event(
    entity_type: str,
    entity_id: int,
    event_type: str,
    event_data: dict | None = None,
    performed_by: str | None = None,
):
    _ensure_performed_by_column()

    # Si no se paso performed_by, intentar obtenerlo de la sesion
    if performed_by is None:
        performed_by = _get_current_username()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO event_ledger (
                entity_type,
                entity_id,
                event_type,
                event_data,
                performed_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entity_type,
            entity_id,
            event_type,
            json.dumps(event_data) if event_data else None,
            performed_by,
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()


def list_events_admin(
    limit: int = 50,
    offset: int = 0,
    entity_type: str | None = None,
    entity_id: int | None = None,
    claim_id: int | None = None,
) -> list[dict]:
    _ensure_performed_by_column()

    with get_connection() as conn:
        cur = conn.cursor()

        if entity_type and entity_id is not None:
            cur.execute("""
                SELECT id, entity_type, entity_id, event_type,
                       event_data, performed_by, created_at
                FROM event_ledger
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (entity_type, entity_id, limit, offset))

        elif claim_id is not None:
            cur.execute("""
                SELECT id, entity_type, entity_id, event_type,
                       event_data, performed_by, created_at
                FROM event_ledger
                WHERE entity_type = 'claim' AND entity_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (claim_id, limit, offset))

        else:
            cur.execute("""
                SELECT id, entity_type, entity_id, event_type,
                       event_data, performed_by, created_at
                FROM event_ledger
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        rows = cur.fetchall()
        return [dict(r) for r in rows]


def count_events_admin(
    entity_type: str | None = None,
    entity_id: int | None = None,
    claim_id: int | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.cursor()

        if claim_id is not None:
            cur.execute("""
                SELECT COUNT(*) AS n FROM event_ledger
                WHERE entity_type='claim' AND entity_id = ?
            """, (claim_id,))
        else:
            cur.execute("SELECT COUNT(*) AS n FROM event_ledger")

        return int(cur.fetchone()["n"])