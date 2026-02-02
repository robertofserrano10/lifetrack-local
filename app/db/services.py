from app.db.connection import get_connection


def create_service(
    patient_id: int,
    service_date: str,
    cpt_code: str,
    units: int = 1,
    diagnosis_code: str | None = None,
    description: str | None = None,
) -> int:
    """
    Crea un servicio clínico y devuelve su ID.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO services (
                claim_id,
                service_date,
                cpt_code,
                units,
                diagnosis_code,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                None,              # claim_id (aún no asociado)
                service_date,
                cpt_code,
                units,
                diagnosis_code,
                description,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_services_by_patient(patient_id: int):
    """
    Devuelve todos los servicios de un paciente (vía claims futuros).
    Por ahora: todos los servicios sin claim, asociados lógicamente al paciente.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.*
            FROM services s
            WHERE s.claim_id IS NULL
            ORDER BY s.service_date, s.id
            """
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_service_by_id(service_id: int):
    """
    Devuelve un servicio por ID o None.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM services WHERE id = ?",
            (service_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_service(
    service_id: int,
    service_date: str,
    cpt_code: str,
    units: int,
    diagnosis_code: str | None,
    description: str | None,
) -> bool:
    """
    Actualiza un servicio clínico.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE services
            SET
                service_date = ?,
                cpt_code = ?,
                units = ?,
                diagnosis_code = ?,
                description = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                service_date,
                cpt_code,
                units,
                diagnosis_code,
                description,
                service_id,
            ),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_service(service_id: int) -> bool:
    """
    Elimina un servicio por ID.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM services WHERE id = ?",
            (service_id,),
        )
        conn.commit()
        return cur.rowcount > 0
