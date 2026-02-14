from datetime import datetime
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked


def create_claim(patient_id: int, coverage_id: int) -> int:
    """
    Crea un claim en estado 'draft' y devuelve su ID.
    """
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO claims (
                patient_id, coverage_id, status,
                created_at, updated_at
            )
            VALUES (?, ?, 'draft', ?, ?)
            """,
            (patient_id, coverage_id, now, now),
        )
        conn.commit()
        return cur.lastrowid


def get_claim_by_id(claim_id: int):
    """
    Devuelve un claim por ID o None.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
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


def update_claim_cms_fields(
    claim_id: int,
    referring_provider_name: str | None = None,
    referring_provider_npi: str | None = None,
    reserved_local_use_19: str | None = None,
    resubmission_code_22: str | None = None,
    original_ref_no_22: str | None = None,
    prior_authorization_23: str | None = None,
) -> bool:
    """
    Actualiza campos CMS-1500 a nivel CLAIM:
    17, 19, 22, 23. Todo es nullable.
    """

    # 🔒 BLOQUEO FINANCIERO
    if is_claim_locked(claim_id):
        raise ValueError("Claim está congelado por snapshot")

    now = datetime.utcnow().isoformat()

    sql = """
    UPDATE claims
    SET
        referring_provider_name = ?,
        referring_provider_npi = ?,
        reserved_local_use_19 = ?,
        resubmission_code_22 = ?,
        original_ref_no_22 = ?,
        prior_authorization_23 = ?,
        updated_at = ?
    WHERE id = ?
    """

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            sql,
            (
                referring_provider_name,
                referring_provider_npi,
                reserved_local_use_19,
                resubmission_code_22,
                original_ref_no_22,
                prior_authorization_23,
                now,
                claim_id,
            ),
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


def delete_claim(claim_id: int) -> bool:
    """
    REGLAS:
    - No permite borrar si el claim tiene snapshot.
    - No permite borrar si tiene services asociados.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        # 🔒 Bloqueo por snapshot
        if is_claim_locked(claim_id):
            raise ValueError("No se puede borrar: claim está congelado por snapshot")

        # 🔎 Verificar si tiene services
        cur.execute(
            """
            SELECT 1
            FROM services
            WHERE claim_id = ?
            LIMIT 1
            """,
            (claim_id,),
        )
        if cur.fetchone():
            raise ValueError("No se puede borrar: claim tiene services asociados")

        cur.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
        conn.commit()
        return cur.rowcount > 0
