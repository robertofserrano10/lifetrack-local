from app.db.connection import get_connection


def create_claim(patient_id: int, coverage_id: int) -> int:
    """
    Crea un claim en estado 'draft' y devuelve su ID.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO claims (patient_id, coverage_id, status)
            VALUES (?, ?, 'draft')
            """,
            (patient_id, coverage_id),
        )
        conn.commit()
        return cur.lastrowid


def get_claim_by_id(claim_id: int):
    """
    Devuelve un claim por ID o None.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM claims WHERE id = ?",
            (claim_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_claims_by_patient(patient_id: int):
    """
    Lista claims de un paciente.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM claims WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def add_service_to_claim(service_id: int, claim_id: int) -> bool:
    """
    Asocia un service a un claim (setea services.claim_id).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE services
            SET claim_id = ?, updated_at = datetime('now')
            WHERE id = ? AND claim_id IS NULL
            """,
            (claim_id, service_id),
        )
        conn.commit()
        return cur.rowcount > 0


def list_services_by_claim(claim_id: int):
    """
    Lista services asociados a un claim.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM services WHERE claim_id = ? ORDER BY id",
            (claim_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
