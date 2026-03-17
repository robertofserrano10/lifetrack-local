import sqlite3
from datetime import datetime
from app.config import DB_PATH
from app.db.event_ledger import log_event


def _table_has_column(conn, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    columns = [r[1] for r in cur.fetchall()]
    return column in columns


def _ensure_progress_notes_schema():
    conn = sqlite3.connect(DB_PATH)
    try:
        if not _table_has_column(conn, "progress_notes", "patient_name"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN patient_name TEXT")
        if not _table_has_column(conn, "progress_notes", "record_number"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN record_number TEXT")
        if not _table_has_column(conn, "progress_notes", "date_of_service"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN date_of_service TEXT")
        if not _table_has_column(conn, "progress_notes", "start_time"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN start_time TEXT")
        if not _table_has_column(conn, "progress_notes", "end_time"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN end_time TEXT")
        if not _table_has_column(conn, "progress_notes", "service_type"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN service_type TEXT")
        if not _table_has_column(conn, "progress_notes", "cpt_code"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN cpt_code TEXT")
        if not _table_has_column(conn, "progress_notes", "diagnosis_code"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN diagnosis_code TEXT")
        if not _table_has_column(conn, "progress_notes", "provider_name"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN provider_name TEXT")
        if not _table_has_column(conn, "progress_notes", "provider_credentials"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN provider_credentials TEXT")
        if not _table_has_column(conn, "progress_notes", "subjective"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN subjective TEXT")
        if not _table_has_column(conn, "progress_notes", "objective"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN objective TEXT")
        if not _table_has_column(conn, "progress_notes", "assessment"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN assessment TEXT")
        if not _table_has_column(conn, "progress_notes", "plan"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN plan TEXT")
        if not _table_has_column(conn, "progress_notes", "note_text"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN note_text TEXT")
        if not _table_has_column(conn, "progress_notes", "parent_note_id"):
            conn.execute("ALTER TABLE progress_notes ADD COLUMN parent_note_id INTEGER DEFAULT NULL")
        conn.commit()
    finally:
        conn.close()


def get_notes_by_encounter(encounter_id):
    _ensure_progress_notes_schema()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM progress_notes
        WHERE encounter_id = ?
        AND parent_note_id IS NULL
        ORDER BY created_at DESC
    """, (encounter_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_note_by_id(note_id):
    _ensure_progress_notes_schema()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM progress_notes
        WHERE id = ?
    """, (note_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_addendums_by_note(parent_note_id):
    _ensure_progress_notes_schema()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM progress_notes
        WHERE parent_note_id = ?
        ORDER BY created_at ASC
    """, (parent_note_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_notes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT pn.*, e.encounter_date, p.first_name||' '||p.last_name AS patient_name
        FROM progress_notes pn
        JOIN encounters e ON e.id = pn.encounter_id
        JOIN patients p ON p.id = e.patient_id
        WHERE pn.parent_note_id IS NULL
        ORDER BY pn.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def create_note(encounter_id, patient_name, record_number, date_of_service, start_time,
                end_time, service_type, cpt_code, diagnosis_code, provider_name,
                provider_credentials, subjective, objective, assessment, plan,
                parent_note_id=None):
    _ensure_progress_notes_schema()

    note_text_combined = """
Patient Name: {patient_name}
Record Number: {record_number}
Date of Service: {date_of_service}
Start Time: {start_time}
End Time: {end_time}
Service Type: {service_type}
CPT Code: {cpt_code}
Diagnosis (ICD-10): {diagnosis_code}
Provider: {provider_name}
Provider Credentials: {provider_credentials}

S — Subjective
{subjective}

O — Objective
{objective}

A — Assessment
{assessment}

P — Plan
{plan}
""".format(
        patient_name=patient_name or "",
        record_number=record_number or "",
        date_of_service=date_of_service or "",
        start_time=start_time or "",
        end_time=end_time or "",
        service_type=service_type or "",
        cpt_code=cpt_code or "",
        diagnosis_code=diagnosis_code or "",
        provider_name=provider_name or "",
        provider_credentials=provider_credentials or "",
        subjective=subjective or "",
        objective=objective or "",
        assessment=assessment or "",
        plan=plan or "",
    )

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO progress_notes (
            encounter_id, patient_name, record_number, date_of_service,
            start_time, end_time, service_type, cpt_code, diagnosis_code,
            provider_name, provider_credentials, subjective, objective,
            assessment, plan, note_text, parent_note_id,
            status, signed, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        encounter_id, patient_name, record_number, date_of_service,
        start_time, end_time, service_type, cpt_code, diagnosis_code,
        provider_name, provider_credentials, subjective, objective,
        assessment, plan, note_text_combined, parent_note_id,
    ))

    note_id = cur.lastrowid
    conn.commit()
    conn.close()

    log_event(
        entity_type="encounter",
        entity_id=encounter_id,
        event_type="progress_note_created",
        event_data={"note_id": note_id},
    )

    return note_id


def sign_note(note_id):
    note = get_note_by_id(note_id)
    if not note:
        raise ValueError("Nota no existe")

    if note["signed"]:
        return note_id

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE progress_notes
        SET signed = 1,
            signed_at = CURRENT_TIMESTAMP,
            status = 'signed',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (note_id,))
    conn.commit()
    conn.close()

    log_event(
        entity_type="encounter",
        entity_id=note["encounter_id"],
        event_type="progress_note_signed",
        event_data={"note_id": note_id},
    )

    return note_id


def addendum_note(original_note_id, addendum_text):
    original_note = get_note_by_id(original_note_id)
    if not original_note:
        raise ValueError("Nota original no existe")

    note = dict(original_note)

    return create_note(
        encounter_id=note["encounter_id"],
        patient_name=note.get("patient_name", ""),
        record_number=note.get("record_number", ""),
        date_of_service=note.get("date_of_service", ""),
        start_time=note.get("start_time", ""),
        end_time=note.get("end_time", ""),
        service_type=note.get("service_type", ""),
        cpt_code=note.get("cpt_code", ""),
        diagnosis_code=note.get("diagnosis_code", ""),
        provider_name=note.get("provider_name", ""),
        provider_credentials=note.get("provider_credentials", ""),
        subjective=addendum_text,
        objective="",
        assessment="",
        plan="",
        parent_note_id=original_note_id,
    )