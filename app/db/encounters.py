import sqlite3
from app.config import DB_PATH


def get_all_encounters():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            e.encounter_date,
            e.status,
            p.first_name,
            p.last_name
        FROM encounters e
        JOIN patients p ON p.id = e.patient_id
        ORDER BY e.encounter_date DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows