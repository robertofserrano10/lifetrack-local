import sqlite3

DB = "storage/lifetrack.db"


def check_encounter_notes():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id as encounter_id,
            COUNT(n.id) as notes_count
        FROM encounters e
        LEFT JOIN progress_notes n
        ON n.encounter_id = e.id
        GROUP BY e.id
    """)

    rows = cur.fetchall()

    errors = 0

    for r in rows:

        if r["notes_count"] > 1:
            print(f"ERROR: encounter {r['encounter_id']} has {r['notes_count']} notes")
            errors += 1

    if errors == 0:
        print("PASS: encounter note constraint OK")

    conn.close()


def check_signed_notes_locked():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, status, signed
        FROM progress_notes
    """)

    rows = cur.fetchall()

    errors = 0

    for r in rows:

        if r["status"] == "SIGNED" and r["signed"] != 1:
            print(f"ERROR: note {r['id']} status SIGNED but signed flag not set")
            errors += 1

    if errors == 0:
        print("PASS: signature state OK")

    conn.close()


def check_addendums():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.id,
            a.note_id
        FROM progress_note_addendums a
        LEFT JOIN progress_notes n
        ON a.note_id = n.id
        WHERE n.id IS NULL
    """)

    rows = cur.fetchall()

    if len(rows) == 0:
        print("PASS: addendum integrity OK")
    else:
        print("ERROR: addendum without note detected")

    conn.close()


def check_print_dependencies():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            n.id,
            p.first_name,
            p.last_name
        FROM progress_notes n
        JOIN encounters e ON n.encounter_id = e.id
        JOIN patients p ON e.patient_id = p.id
    """)

    rows = cur.fetchall()

    if len(rows) == 0:
        print("WARNING: no notes available for print test")
    else:
        print("PASS: print dependencies OK")

    conn.close()


def run():

    print("\n--- CLINICAL SYSTEM TEST ---\n")

    check_encounter_notes()

    check_signed_notes_locked()

    check_addendums()

    check_print_dependencies()

    print("\n--- TEST COMPLETE ---\n")


if __name__ == "__main__":
    run()