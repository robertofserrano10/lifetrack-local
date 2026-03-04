from app.db.connection import get_connection


def get_claim_with_services(claim_id: int):
    """
    Devuelve el claim y sus services asociados.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM claims WHERE id = ?",
            (claim_id,),
        )
        claim = cur.fetchone()
        if not claim:
            return None

        cur.execute(
            "SELECT * FROM services WHERE claim_id = ? ORDER BY service_date, id",
            (claim_id,),
        )
        services = cur.fetchall()

        return {
            "claim": dict(claim),
            "services": [dict(s) for s in services],
        }


def validate_claim_ready_for_snapshot(claim_id: int):
    """
    Valida si un claim está listo para CMS-1500 snapshot.
    Devuelve (True, []) si todo está OK,
    o (False, [errores]) si no.
    """
    data = get_claim_with_services(claim_id)
    if not data:
        return False, ["Claim no existe"]

    claim = data["claim"]
    services = data["services"]

    errors = []

    if claim["status"] != "draft":
        errors.append("Claim no está en estado draft")

    if not claim.get("patient_id"):
        errors.append("Claim sin patient_id")

    if not claim.get("coverage_id"):
        errors.append("Claim sin coverage_id")

    if len(services) == 0:
        errors.append("Claim no tiene services asociados")

    for idx, s in enumerate(services, start=1):
        if not s.get("service_date"):
            errors.append(f"Service #{idx} sin service_date")
        if not s.get("cpt_code"):
            errors.append(f"Service #{idx} sin cpt_code")
        if not s.get("units") or s["units"] <= 0:
            errors.append(f"Service #{idx} con units inválidas")

    return len(errors) == 0, errors
def validate_claim_ready_for_submission(claim_id: int) -> None:
    """
    Valida estructura mínima obligatoria antes de permitir transición a SUBMITTED.
    Lanza ValueError si algo no cumple.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        # 1️⃣ Claim existe
        cur.execute("SELECT id FROM claims WHERE id = ?", (claim_id,))
        if not cur.fetchone():
            raise ValueError("Claim no existe")

        # 2️⃣ Provider activo
        cur.execute(
            """
            SELECT 1
            FROM provider_settings
            WHERE active = 1
            LIMIT 1
            """
        )
        if not cur.fetchone():
            raise ValueError("No hay provider_settings activo")

        # 3️⃣ Al menos un service
        cur.execute(
            """
            SELECT 1
            FROM services
            WHERE claim_id = ?
            LIMIT 1
            """,
            (claim_id,),
        )
        if not cur.fetchone():
            raise ValueError("Claim no tiene services")

        # 4️⃣ Al menos un charge
        cur.execute(
            """
            SELECT 1
            FROM charges c
            JOIN services s ON s.id = c.service_id
            WHERE s.claim_id = ?
            LIMIT 1
            """,
            (claim_id,),
        )
        if not cur.fetchone():
            raise ValueError("Claim no tiene charges")

        # 5️⃣ total_charge > 0
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
        if total_charge <= 0:
            raise ValueError("Total charge debe ser mayor que 0")