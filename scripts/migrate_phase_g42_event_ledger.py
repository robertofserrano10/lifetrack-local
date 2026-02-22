from app.db.connection import get_connection


def create_event_ledger_table():

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()

    print("G42: event_ledger table ready.")


if __name__ == "__main__":
    create_event_ledger_table()