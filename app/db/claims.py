from datetime import datetime
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked


# ============================================================
# ESTADOS OPERACIONALES PERMITIDOS
# ============================================================

ALLOWED_STATUSES = {
    "DRAFT",
    "READY",
    "SUBMITTED",
    "DENIED",
    "PAID",
}

VALID_TRANSITIONS = {
    "DRAFT": {"READY"},
    "READY": {"SUBMITTED"},
    "SUBMITTED": {"DENIED", "PAID"},
    "DENIED": {"READY"},
    "PAID": set(),  # terminal
}


# ============================================================
# CORE CLAIM CRUD
# ============================================================

def create_claim(patient_id: int, coverage_id: int) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO claims (
                patient_id, coverage_id, status,
                created_at, updated_at
            )
            VALUES (?, ?, 'DRAFT', ?, ?)
            """,
            (patient_id, coverage_id, now, now),
        )
        conn.commit()
        return cur.lastrowid


def get_claim_by_id(claim_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_claims_by_patient(patient_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM claims WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


# ============================================================
# TRANSICIÓN OPERACIONAL CONTROLADA (PERSISTENTE)
# ============================================================

def update_claim_operational_status(claim_id: int, new_status: str) -> bool:
    """
    Cambia el estado operacional persistido.
    Reglas:
    - Debe existir el claim.
    - new_status debe estar en ALLOWED_STATUSES.
    - Debe respetar VALID_TRANSITIONS.
    - No permite cambio si claim está congelado por snapshot.
    """

    if new_status not in ALLOWED_STATUSES:
        raise ValueError("Estado inválido")

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT status FROM claims WHERE id = ?", (claim_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Claim no existe")

        current_status = row["status"]

        if is_claim_locked(claim_id):
            raise ValueError("Claim está congelado por snapshot")

        if new_status not in VALID_TRANSITIONS.get(current_status, set()):
            raise ValueError(
                f"Transición inválida: {current_status} → {new_status}"
            )

        cur.execute(
            """
            UPDATE claims
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_status, datetime.utcnow().isoformat(), claim_id),
        )
        conn.commit()
        return cur.rowcount > 0


# ============================================================
# CMS UPDATE (RESPETA BLOQUEO)
# ============================================================

def update_claim_cms_fields(
    claim_id: int,
    referring_provider_name: str | None = None,
    referring_provider_npi: str | None = None,
    reserved_local_use_19: str | None = None,
    resubmission_code_22: str | None = None,
    original_ref_no_22: str | None = None,
    prior_authorization_23: str | None = None,
) -> bool:

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


# ============================================================
# DELETE CONTROLADO
# ============================================================

def delete_claim(claim_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()

        if is_claim_locked(claim_id):
            raise ValueError(
                "No se puede borrar: claim está congelado por snapshot"
            )

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
            raise ValueError(
                "No se puede borrar: claim tiene services asociados"
            )

        cur.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
        conn.commit()
        return cur.rowcount > 0


# ============================================================
# ESTADO FINANCIERO DERIVADO
# ============================================================

def get_claim_financial_status(claim_id: int) -> dict:

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id FROM claims WHERE id = ?", (claim_id,))
        if not cur.fetchone():
            raise ValueError("Claim no existe")

        cur.execute(
            """
            SELECT COALESCE(SUM(c.amount), 0)
            FROM charges c
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            """,
            (claim_id,),
        )
        total_charge = float(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COALESCE(SUM(a.amount_applied), 0)
            FROM applications a
            JOIN charges c ON c.id = a.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            """,
            (claim_id,),
        )
        total_applied = float(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COALESCE(SUM(ad.amount), 0)
            FROM adjustments ad
            JOIN charges c ON c.id = ad.charge_id
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            """,
            (claim_id,),
        )
        total_adjustments = float(cur.fetchone()[0])

        balance_due = total_charge - total_applied - total_adjustments

        if balance_due > 0:
            status = "OPEN"
        elif balance_due == 0:
            status = "PAID"
        else:
            status = "OVERPAID"

        return {
            "claim_id": claim_id,
            "total_charge": total_charge,
            "total_applied": total_applied,
            "total_adjustments": total_adjustments,
            "balance_due": balance_due,
            "status": status,
        }


# ============================================================
# ESTADO OPERACIONAL DERIVADO
# ============================================================

def get_claim_operational_status(claim_id: int) -> dict:

    claim = get_claim_by_id(claim_id)
    if not claim:
        raise ValueError("Claim no existe")

    locked = is_claim_locked(claim_id)
    financial = get_claim_financial_status(claim_id)

    # DERIVED OPERATIONAL STATUS (NO PERSISTENTE)
    if not locked:
        derived_status = "DRAFT"
    else:
        if financial["balance_due"] > 0:
            derived_status = "READY"
        elif financial["balance_due"] == 0:
            derived_status = "PAID"
        else:
            derived_status = "OVERPAID"

    return {
        "claim_id": claim_id,
        "persisted_status": claim["status"],
        "operational_status": derived_status,
        "locked": locked,
        "financial_status": financial["status"],
        "balance_due": financial["balance_due"],
    }
