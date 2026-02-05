from app.db.connection import get_connection


def get_active_provider_settings():
    """
    Devuelve el provider_settings activo (active = 1) o None.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM provider_settings
            WHERE active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        return dict(row) if row else None
