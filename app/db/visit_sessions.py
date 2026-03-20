"""
VISIT SESSIONS — Fase BC
Capa operacional pura. Solo refleja presencia física del paciente.
NO toca ledger, NO genera cargos, NO crea claims.
"""

import sqlite3
from datetime import datetime, timezone
from app.config import DB_PATH


VALID_STATUSES = ['ARRIVED', 'CHECKED_IN', 'WAITING', 'IN_SESSION', 'COMPLETED', 'CANCELLED']


def _ensure_table():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visit_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ARRIVED'
                    CHECK (status IN ('ARRIVED','CHECKED_IN','WAITING','IN_SESSION','COMPLETED','CANCELLED')),
                check_in_time TEXT,
                in_session_time TEXT,
                completed_time TEXT,
                notes TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def create_visit_session(patient_id: int, appointment_date: str, notes: str = None, created_by: str = None) -> int:
    _ensure_table()
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visit_sessions (
                patient_id, appointment_date, status,
                check_in_time, notes, created_by, created_at, updated_at
            ) VALUES (?, ?, 'ARRIVED', ?, ?, ?, ?, ?)
        """, (patient_id, appointment_date, now, notes, created_by, now, now))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_visit_status(session_id: int, new_status: str) -> bool:
    _ensure_table()
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Status inválido: {new_status}")

    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()

        # Set timestamp for specific transitions
        time_field = None
        if new_status == 'CHECKED_IN':
            time_field = "check_in_time"
        elif new_status == 'IN_SESSION':
            time_field = "in_session_time"
        elif new_status == 'COMPLETED':
            time_field = "completed_time"

        if time_field:
            cur.execute(f"""
                UPDATE visit_sessions
                SET status = ?, {time_field} = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, now, now, session_id))
        else:
            cur.execute("""
                UPDATE visit_sessions
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, now, session_id))

        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_sessions_today(date: str = None) -> list:
    _ensure_table()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                vs.*,
                p.first_name, p.last_name, p.date_of_birth,
                cov.insurer_name, cov.plan_name, cov.policy_number
            FROM visit_sessions vs
            JOIN patients p ON p.id = vs.patient_id
            LEFT JOIN coverages cov ON cov.patient_id = vs.patient_id
                AND (cov.end_date IS NULL OR cov.end_date >= ?)
            WHERE vs.appointment_date = ?
            GROUP BY vs.id
            ORDER BY vs.created_at ASC
        """, (date, date))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_session_by_id(session_id: int) -> dict:
    _ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT vs.*, p.first_name, p.last_name, p.date_of_birth,
                   p.address, p.city, p.state, p.zip_code, p.phone,
                   p.sex, p.marital_status
            FROM visit_sessions vs
            JOIN patients p ON p.id = vs.patient_id
            WHERE vs.id = ?
        """, (session_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_active_sessions_today() -> list:
    """Pacientes que están en sala ahora mismo — para el panel de la doctora."""
    _ensure_table()
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT vs.*, p.first_name, p.last_name
            FROM visit_sessions vs
            JOIN patients p ON p.id = vs.patient_id
            WHERE vs.appointment_date = ?
            AND vs.status IN ('CHECKED_IN', 'WAITING', 'IN_SESSION')
            ORDER BY vs.created_at ASC
        """, (date,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def check_patient_coverage(patient_id: int) -> dict:
    """
    Verifica el estado de coverage del paciente.
    Solo informativo — no asigna nada automáticamente.
    """
    _ensure_table()
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM coverages
            WHERE patient_id = ?
            AND start_date <= ?
            AND (end_date IS NULL OR end_date >= ?)
            ORDER BY id DESC
            LIMIT 1
        """, (patient_id, today, today))
        cov = cur.fetchone()
        if cov:
            return {"has_coverage": True, "coverage": dict(cov)}
        else:
            # Check if has any coverage at all (expired)
            cur.execute("SELECT * FROM coverages WHERE patient_id = ? ORDER BY id DESC LIMIT 1", (patient_id,))
            any_cov = cur.fetchone()
            if any_cov:
                return {"has_coverage": False, "expired": True, "coverage": dict(any_cov)}
            return {"has_coverage": False, "expired": False, "coverage": None}
    finally:
        conn.close()