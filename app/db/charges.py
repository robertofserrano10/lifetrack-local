from datetime import datetime
from app.db.connection import get_connection


def create_charge(service_id: int, amount: float):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO charges (
                service_id,
                amount,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?)
            """,
            (
                service_id,
                amount,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_charge_by_id(charge_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM charges
            WHERE id = ?
            """,
            (charge_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_charge_by_service(service_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM charges
            WHERE service_id = ?
            """,
            (service_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_charge(charge_id: int, amount: float):
    with get_connection() as conn:
        cur = conn.cursor()

        # === HARDENING: no permitir modificar si tiene movimiento financiero ===
        cur.execute(
            """
            SELECT COUNT(*)
            FROM applications
            WHERE charge_id = ?
            """,
            (charge_id,),
        )
        if cur.fetchone()[0] > 0:
            raise ValueError("No se puede modificar un charge con aplicaciones registradas")

        cur.execute(
            """
            SELECT COUNT(*)
            FROM adjustments
            WHERE charge_id = ?
            """,
            (charge_id,),
        )
        if cur.fetchone()[0] > 0:
            raise ValueError("No se puede modificar un charge con adjustments registrados")

        cur.execute(
            """
            UPDATE charges
            SET amount = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                amount,
                datetime.utcnow().isoformat(),
                charge_id,
            ),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_charge(charge_id: int):
    with get_connection() as conn:
        cur = conn.cursor()

        # No permitir borrar si tiene applications
        cur.execute(
            "SELECT 1 FROM applications WHERE charge_id = ? LIMIT 1",
            (charge_id,),
        )
        if cur.fetchone():
            raise ValueError("No se puede borrar: charge tiene applications")

        # No permitir borrar si tiene adjustments
        cur.execute(
            "SELECT 1 FROM adjustments WHERE charge_id = ? LIMIT 1",
            (charge_id,),
        )
        if cur.fetchone():
            raise ValueError("No se puede borrar: charge tiene adjustments")

        cur.execute(
            """
            DELETE FROM charges
            WHERE id = ?
            """,
            (charge_id,),
        )
        conn.commit()
        return cur.rowcount > 0

