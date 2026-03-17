from app.db.connection import get_connection
from app.db.event_ledger import log_event


def create_coverage(
    patient_id,
    insurer_name,
    plan_name,
    policy_number,
    group_number,
    insured_id,
    start_date,
    end_date,
    insured_first_name=None,
    insured_last_name=None,
    relationship_to_insured="self",
    insured_address=None,
    insured_city=None,
    insured_state=None,
    insured_zip=None,
    other_health_plan_11d=0,
):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO coverages (
                patient_id, insurer_name, plan_name, policy_number,
                group_number, insured_id, start_date, end_date,
                insured_first_name, insured_last_name, relationship_to_insured,
                insured_address, insured_city, insured_state, insured_zip,
                other_health_plan_11d
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id, insurer_name, plan_name, policy_number,
            group_number, insured_id, start_date, end_date,
            insured_first_name, insured_last_name, relationship_to_insured,
            insured_address, insured_city, insured_state, insured_zip,
            other_health_plan_11d,
        ))
        conn.commit()
        coverage_id = cur.lastrowid

    log_event(
        entity_type="coverage",
        entity_id=coverage_id,
        event_type="coverage_created",
        event_data={"patient_id": patient_id, "insurer": insurer_name, "plan": plan_name},
    )
    return coverage_id


def list_coverages_by_patient(patient_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM coverages WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_coverage_by_id(coverage_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM coverages WHERE id = ?", (coverage_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_coverage(
    coverage_id,
    insurer_name,
    plan_name,
    policy_number,
    group_number,
    insured_id,
    start_date,
    end_date,
    insured_first_name=None,
    insured_last_name=None,
    relationship_to_insured="self",
    insured_address=None,
    insured_city=None,
    insured_state=None,
    insured_zip=None,
    other_health_plan_11d=0,
):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE coverages SET
                insurer_name = ?,
                plan_name = ?,
                policy_number = ?,
                group_number = ?,
                insured_id = ?,
                start_date = ?,
                end_date = ?,
                insured_first_name = ?,
                insured_last_name = ?,
                relationship_to_insured = ?,
                insured_address = ?,
                insured_city = ?,
                insured_state = ?,
                insured_zip = ?,
                other_health_plan_11d = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            insurer_name, plan_name, policy_number,
            group_number, insured_id, start_date, end_date,
            insured_first_name, insured_last_name, relationship_to_insured,
            insured_address, insured_city, insured_state, insured_zip,
            other_health_plan_11d, coverage_id,
        ))
        conn.commit()

    log_event(
        entity_type="coverage",
        entity_id=coverage_id,
        event_type="coverage_updated",
        event_data={"insurer": insurer_name, "plan": plan_name},
    )
    return True


def delete_coverage(coverage_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM coverages WHERE id = ?", (coverage_id,))
        conn.commit()
        deleted = cur.rowcount > 0

    if deleted:
        log_event(
            entity_type="coverage",
            entity_id=coverage_id,
            event_type="coverage_deleted",
        )
    return deleted