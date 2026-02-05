from app.db.connection import get_connection
from datetime import datetime


def get_provider_settings():
    """
    Devuelve el único registro activo de provider_settings.
    Si no existe, crea uno por defecto.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM provider_settings
            WHERE active = 1
            LIMIT 1
            """
        )
        row = cur.fetchone()

        if row:
            return dict(row)

        # Si no existe, crear uno por defecto
        now = datetime.utcnow().isoformat()

        cur.execute(
            """
            INSERT INTO provider_settings (
                signature,
                active,
                created_at,
                updated_at
            )
            VALUES (?, 1, ?, ?)
            """,
            ("Signature on File", now, now),
        )

        conn.commit()

        cur.execute(
            """
            SELECT *
            FROM provider_settings
            WHERE active = 1
            LIMIT 1
            """
        )

        return dict(cur.fetchone())


def update_provider_settings(**fields):
    """
    Actualiza el registro activo de provider_settings.
    """
    if not fields:
        return

    with get_connection() as conn:
        cur = conn.cursor()

        assignments = []
        values = []

        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            values.append(value)

        assignments.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())

        values.append(1)  # active = 1

        sql = f"""
        UPDATE provider_settings
        SET {", ".join(assignments)}
        WHERE active = ?
        """

        cur.execute(sql, values)
        conn.commit()
