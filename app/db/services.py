from datetime import datetime
from app.db.connection import get_connection
from app.db.financial_lock import is_claim_locked


def create_service(
    claim_id: int,
    service_date: str,
    cpt_code: str,
    units: int,
    diagnosis_code: str,
    description: str,
    outside_lab_20: int = 0,
    lab_charges_20: float | None = None,
    # === Compat CMS-1500 schema (NO rompe llamadas viejas) ===
    charge_amount_24f: float | None = None,
    place_of_service_24b: str | None = None,
    emergency_24c: int = 0,
    diagnosis_pointer_24e: str | None = None,
    epsdt_24h: str | None = None,
    id_qualifier_24i: str | None = None,
    rendering_npi_24j: str | None = None,
) -> int:
    """
    Crea un service asociado a un claim.

    Importante (compatibilidad):
    - El schema actual usa: units_24g, charge_amount_24f, diagnosis_pointer_24e, etc.
    - Los params diagnosis_code/description se aceptan para no romper scripts viejos,
      pero NO se guardan en services porque el schema no tiene esas columnas.
    - charge_amount_24f es NOT NULL en schema; si no se provee, se guarda 0.0.
      El monto real del core financiero debe vivir en la tabla charges.
    """

    # 🔒 BLOQUEO FINANCIERO
    if is_claim_locked(claim_id):
        raise ValueError("Claim está congelado por snapshot")

    now = datetime.utcnow().isoformat()

    if charge_amount_24f is None:
        charge_amount_24f = 0.0

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO services (
                claim_id,
                service_date,
                place_of_service_24b,
                emergency_24c,
                cpt_code,
                diagnosis_pointer_24e,
                charge_amount_24f,
                units_24g,
                epsdt_24h,
                id_qualifier_24i,
                rendering_npi_24j,
                outside_lab_20,
                lab_charges_20,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(claim_id),
                service_date,
                place_of_service_24b,
                int(emergency_24c),
                cpt_code,
                diagnosis_pointer_24e,
                float(charge_amount_24f),
                int(units),
                epsdt_24h,
                id_qualifier_24i,
                rendering_npi_24j,
                int(outside_lab_20),
                lab_charges_20,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def update_service_box20(
    service_id: int,
    outside_lab_20: int,
    lab_charges_20: float | None,
) -> bool:
    """
    Actualiza Box 20 a nivel service.
    Bloqueado si el claim está congelado.
    """

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cur = conn.cursor()

        # 1. Obtener claim_id desde services
        cur.execute(
            """
            SELECT claim_id
            FROM services
            WHERE id = ?
            """,
            (int(service_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Service no existe")

        claim_id = row["claim_id"]

        # 🔒 BLOQUEO FINANCIERO
        if is_claim_locked(claim_id):
            raise ValueError("Claim está congelado por snapshot")

        # 2. Actualizar
        cur.execute(
            """
            UPDATE services
            SET outside_lab_20 = ?, lab_charges_20 = ?, updated_at = ?
            WHERE id = ?
            """,
            (int(outside_lab_20), lab_charges_20, now, int(service_id)),
        )
        conn.commit()
        return cur.rowcount > 0
