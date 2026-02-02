from app.db.connection import get_connection


def create_coverage(
    patient_id,
    insurer_name,
    plan_name,
    policy_number,
    group_number,
    insured_id,
    start_date,
    end_date,
):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO coverages (
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date,
            ),
        )
        conn.commit()
        return cur.lastrowid


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
        cur.execute(
            "SELECT * FROM coverages WHERE id = ?",
            (coverage_id,),
        )
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
):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE coverages
            SET
                insurer_name = ?,
                plan_name = ?,
                policy_number = ?,
                group_number = ?,
                insured_id = ?,
                start_date = ?,
                end_date = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                insurer_name,
                plan_name,
                policy_number,
                group_number,
                insured_id,
                start_date,
                end_date,
                coverage_id,
            ),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_coverage(coverage_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM coverages WHERE id = ?", (coverage_id,))
        conn.commit()
        return cur.rowcount > 0
