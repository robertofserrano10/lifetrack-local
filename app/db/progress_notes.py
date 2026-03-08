import sqlite3
from app.config import DB_PATH


def get_notes_by_encounter(encounter_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""

        SELECT
            id,
            note_text,
            status,
            signed,
            signed_at,
            created_at

        FROM progress_notes

        WHERE encounter_id = ?

        ORDER BY created_at DESC

    """, (encounter_id,))

    rows = cur.fetchall()

    conn.close()

    return rows