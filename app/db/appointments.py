"""
APPOINTMENTS — Fase BI-2
Citas formales. Agenda clínica.
No toca finanzas, no crea claims.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from app.config import DB_PATH


VALID_STATUSES = ['SCHEDULED', 'CONFIRMED', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']

SERVICE_TYPES = [
    'Evaluación',
    'Seguimiento',
    'Crisis',
    'Consulta',
    'Otro',
]


def _ensure_table():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                encounter_id INTEGER,
                scheduled_date TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                service_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'SCHEDULED'
                    CHECK (status IN ('SCHEDULED','CONFIRMED','ARRIVED','COMPLETED','CANCELLED','NO_SHOW')),
                notes TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (encounter_id) REFERENCES encounters(id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(scheduled_date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)"
        )
        conn.commit()
    finally:
        conn.close()


def _rows_with_patient(conn, sql, params=()):
    """Ejecuta query y devuelve lista de dicts con info del paciente."""
    cur = conn.cursor()
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def create_appointment(
    patient_id: int,
    scheduled_date: str,
    scheduled_time: str,
    service_type: str,
    notes: str = None,
    created_by: str = None,
    encounter_id: int = None,
) -> int:
    _ensure_table()
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO appointments (
                patient_id, encounter_id, scheduled_date, scheduled_time,
                service_type, status, notes, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'SCHEDULED', ?, ?, ?, ?)
        """, (patient_id, encounter_id, scheduled_date, scheduled_time,
              service_type, notes, created_by, now, now))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_appointments_by_date(date: str) -> list:
    _ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return _rows_with_patient(conn, """
            SELECT a.*, p.first_name, p.last_name, p.date_of_birth
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            WHERE a.scheduled_date = ?
            ORDER BY a.scheduled_time ASC
        """, (date,))
    finally:
        conn.close()


def get_appointments_by_patient(patient_id: int) -> list:
    _ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return _rows_with_patient(conn, """
            SELECT a.*, p.first_name, p.last_name, p.date_of_birth
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            WHERE a.patient_id = ?
            ORDER BY a.scheduled_date DESC, a.scheduled_time DESC
        """, (patient_id,))
    finally:
        conn.close()


def update_appointment_status(appointment_id: int, new_status: str) -> bool:
    _ensure_table()
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Status inválido: {new_status}")
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE appointments
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, now, appointment_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_upcoming_appointments(days: int = 7) -> list:
    """Citas desde hoy hasta N días hacia adelante, excluyendo canceladas."""
    _ensure_table()
    today = datetime.now().strftime("%Y-%m-%d")
    until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return _rows_with_patient(conn, """
            SELECT a.*, p.first_name, p.last_name, p.date_of_birth
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            WHERE a.scheduled_date BETWEEN ? AND ?
              AND a.status NOT IN ('CANCELLED', 'NO_SHOW')
            ORDER BY a.scheduled_date ASC, a.scheduled_time ASC
        """, (today, until))
    finally:
        conn.close()
