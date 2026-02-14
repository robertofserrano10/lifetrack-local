from datetime import datetime
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked


def create_charge(service_id: int, amount: float):
    with get_connection() as conn:
        cur = conn.cursor()

        # 1. Obtener claim_id del service
        cur.execute(
            """
            SELECT claim_id
            FROM services
            WHERE id = ?
            """,
            (service_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Service no existe")

        claim_id = row["claim_id"]

        # 2. Verificar bloqueo financiero
        if is_claim_locked(claim_id):
            raise ValueError("Claim está congelado por snapshot")

        # 3. Insertar charge
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

        # 1. Obtener service_id del charge
        cur.execute(
            """
            SELECT service_id
            FROM charges
            WHERE id = ?
            """,
            (charge_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Charge no existe")

        service_id = row["service_id"]

        # 2. Obtener claim_id desde services
        cur.execute(
            """
            SELECT claim_id
            FROM services
            WHERE id = ?
            """,
            (service_id,),
        )
        service_row = cur.fetchone()
        if not service_row:
            raise ValueError("Service no existe")

        claim_id = service_row["claim_id"]

        # 3. Verificar bloqueo financiero
        if is_claim_locked(claim_id):
            raise ValueError("Claim está congelado por snapshot")

        # 4. Actualizar
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

        # Verificar si tiene applications
        cur.execute(
            """
            SELECT 1
            FROM applications
            WHERE charge_id = ?
            LIMIT 1
            """,
            (charge_id,),
        )
        if cur.fetchone():
            raise ValueError("No se puede borrar: charge tiene applications")

        cur.execute(
            """
            DELETE FROM charges
            WHERE id = ?
            """,
            (charge_id,),
        )
        conn.commit()
        return cur.rowcount > 0
