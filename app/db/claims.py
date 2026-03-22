from datetime import datetime, timezone
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked
from app.db.event_ledger import log_event


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

def _ensure_encounter_id_column():
    """Migración automática — agrega columna encounter_id a claims si no existe."""
    with get_connection() as conn:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(claims)")]
        if "encounter_id" not in cols:
            conn.execute(
                "ALTER TABLE claims ADD COLUMN encounter_id INTEGER REFERENCES encounters(id)"
            )
            conn.commit()


def create_claim(patient_id: int, coverage_id: int, encounter_id: int | None = None) -> int:
    _ensure_encounter_id_column()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO claims (
                patient_id, coverage_id, encounter_id, status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, 'DRAFT', ?, ?)
            """,
            (patient_id, coverage_id, encounter_id, now, now),
        )
        claim_id = cur.lastrowid

        # Se asigna claim_number automático para evitar valor None en interfaces
        claim_number = f"CLM{claim_id:06d}"
        cur.execute(
            "UPDATE claims SET claim_number = ? WHERE id = ?",
            (claim_number, claim_id),
        )

        conn.commit()
        return claim_id


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

    if new_status not in ALLOWED_STATUSES:
        raise ValueError("Estado inválido")

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT status FROM claims WHERE id = ?", (claim_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Claim no existe")

        current_status = row["status"]

        # HARD FREEZE CHECK
        if is_claim_locked(claim_id):
            from app.db.event_ledger import log_event

            log_event(
                entity_type="claim",
                entity_id=claim_id,
                event_type="freeze_blocked_transition",
                event_data={
                    "attempted_new_status": new_status,
                    "current_status": current_status,
                },
           )

            raise ValueError("Claim congelado por snapshot — transición bloqueada")

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
            (new_status, datetime.now(timezone.utc).isoformat(), claim_id),
        )
        conn.commit()
        from app.db.event_ledger import log_event

        log_event(
            entity_type="claim",
            entity_id=claim_id,
            event_type="operational_transition",
            event_data={
                "from": current_status,
                "to": new_status,
            },
        )

        return cur.rowcount > 0


# ============================================================
# CMS UPDATE (RESPETA BLOQUEO)
# ============================================================

def _ensure_diagnosis_columns():
    """Migración automática — agrega columnas diagnosis_1..12 si no existen."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(claims)")
        cols = [r["name"] for r in cur.fetchall()]
        for i in range(1, 13):
            col = f"diagnosis_{i}"
            if col not in cols:
                conn.execute(f"ALTER TABLE claims ADD COLUMN {col} TEXT")
        conn.commit()


def update_claim_cms_fields(
    claim_id: int,
    # Casilla 10
    related_employment_10a: int = 0,
    related_auto_10b: int = 0,
    related_other_10c: int = 0,
    # Casilla 14-19
    date_current_illness_14: str | None = None,
    other_date_15: str | None = None,
    unable_work_from_16: str | None = None,
    unable_work_to_16: str | None = None,
    referring_provider_name: str | None = None,
    referring_provider_npi: str | None = None,
    hosp_from_18: str | None = None,
    hosp_to_18: str | None = None,
    reserved_local_use_19: str | None = None,
    # Casilla 22-23
    resubmission_code_22: str | None = None,
    original_ref_no_22: str | None = None,
    prior_authorization_23: str | None = None,
    # Casilla 27
    accept_assignment_27: int = 1,
    # Casilla 21 — diagnósticos A-L
    diagnosis_1: str | None = None,
    diagnosis_2: str | None = None,
    diagnosis_3: str | None = None,
    diagnosis_4: str | None = None,
    diagnosis_5: str | None = None,
    diagnosis_6: str | None = None,
    diagnosis_7: str | None = None,
    diagnosis_8: str | None = None,
    diagnosis_9: str | None = None,
    diagnosis_10: str | None = None,
    diagnosis_11: str | None = None,
    diagnosis_12: str | None = None,
) -> bool:

    _ensure_diagnosis_columns()

    if is_claim_locked(claim_id):
        raise ValueError("Claim está congelado por snapshot")

    now = datetime.now(timezone.utc).isoformat()

    sql = """
    UPDATE claims SET
        related_employment_10a = ?,
        related_auto_10b = ?,
        related_other_10c = ?,
        date_current_illness_14 = ?,
        other_date_15 = ?,
        unable_work_from_16 = ?,
        unable_work_to_16 = ?,
        referring_provider_name = ?,
        referring_provider_npi = ?,
        hosp_from_18 = ?,
        hosp_to_18 = ?,
        reserved_local_use_19 = ?,
        resubmission_code_22 = ?,
        original_ref_no_22 = ?,
        prior_authorization_23 = ?,
        accept_assignment_27 = ?,
        diagnosis_1 = ?, diagnosis_2 = ?, diagnosis_3 = ?,
        diagnosis_4 = ?, diagnosis_5 = ?, diagnosis_6 = ?,
        diagnosis_7 = ?, diagnosis_8 = ?, diagnosis_9 = ?,
        diagnosis_10 = ?, diagnosis_11 = ?, diagnosis_12 = ?,
        updated_at = ?
    WHERE id = ?
    """

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (
            related_employment_10a, related_auto_10b, related_other_10c,
            date_current_illness_14, other_date_15,
            unable_work_from_16, unable_work_to_16,
            referring_provider_name, referring_provider_npi,
            hosp_from_18, hosp_to_18,
            reserved_local_use_19,
            resubmission_code_22, original_ref_no_22,
            prior_authorization_23, accept_assignment_27,
            diagnosis_1, diagnosis_2, diagnosis_3,
            diagnosis_4, diagnosis_5, diagnosis_6,
            diagnosis_7, diagnosis_8, diagnosis_9,
            diagnosis_10, diagnosis_11, diagnosis_12,
            now, claim_id,
        ))
        conn.commit()

    from app.db.event_ledger import log_event
    log_event(
        entity_type="claim",
        entity_id=claim_id,
        event_type="claim_cms_fields_updated",
    )
    return True


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