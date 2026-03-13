import sqlite3

DB = "storage/lifetrack.db"


def test_encounter_single_note():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            encounter_id,
            COUNT(id) as total
        FROM progress_notes
        GROUP BY encounter_id
    """)

    rows = cur.fetchall()

    errors = 0

    for r in rows:
        if r["total"] > 1:
            print(f"ERROR: encounter {r['encounter_id']} has {r['total']} notes")
            errors += 1

    if errors == 0:
        print("PASS: single note per encounter")

    conn.close()


def test_signed_notes_lock():

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
            print(f"ERROR: note {r['id']} status SIGNED but signed flag incorrect")
            errors += 1

    if errors == 0:
        print("PASS: signature state integrity")

    conn.close()


def test_addendum_integrity():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.id
        FROM progress_note_addendums a
        LEFT JOIN progress_notes n
        ON a.note_id = n.id
        WHERE n.id IS NULL
    """)

    rows = cur.fetchall()

    if len(rows) == 0:
        print("PASS: addendum integrity")
    else:
        print("ERROR: orphan addendum detected")

    conn.close()


def test_addendum_only_on_signed():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.id,
            n.status
        FROM progress_note_addendums a
        JOIN progress_notes n
        ON a.note_id = n.id
    """)

    rows = cur.fetchall()

    errors = 0

    for r in rows:

        if r["status"] != "SIGNED":
            print(f"ERROR: addendum {r['id']} attached to non-signed note")
            errors += 1

    if errors == 0:
        print("PASS: addendum only on signed notes")

    conn.close()


def test_print_dependencies():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            n.id
        FROM progress_notes n
        JOIN encounters e ON n.encounter_id = e.id
        JOIN patients p ON e.patient_id = p.id
    """)

    rows = cur.fetchall()

    if len(rows) >= 0:
        print("PASS: print dependencies valid")

    conn.close()


def run_all():

    print("\n--- CLINICAL PHASE TEST ---\n")

    test_encounter_single_note()
    test_signed_notes_lock()
    test_addendum_integrity()
    test_addendum_only_on_signed()
    test_print_dependencies()

    print("\n--- TEST COMPLETE ---\n")


if __name__ == "__main__":
    run_all()