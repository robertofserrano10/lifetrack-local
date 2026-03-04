import os
import sqlite3

from app.db.claims import get_claim_by_id, VALID_TRANSITIONS
from app.db.cms1500_snapshot import get_latest_snapshot_by_claim

DB_PATH = "storage/lifetrack.db"
SCHEMA_PATH = "storage/schema.sql"


def _reset_db():
    # Borrar DB anterior (evita contaminación por pruebas previas)
    try:
        os.remove(DB_PATH)
    except FileNotFoundError:
        pass

    schema = open(SCHEMA_PATH, "r", encoding="utf-8").read()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()


def _find_path_to_submitted() -> tuple[str, str]:
    """
    Encuentra un (source_status, submitted_status) usando VALID_TRANSITIONS.
    REGLA: source_status != submitted_status (evita claims ya 'SUBMITTED' y locks).
    """
    submitted_variants = set()
    for _src, dests in VALID_TRANSITIONS.items():
        for d in dests:
            if isinstance(d, str) and d.lower() == "submitted":
                submitted_variants.add(d)

    if not submitted_variants:
        raise RuntimeError("VALID_TRANSITIONS no contiene destino 'submitted' (ni variantes de casing).")

    # Preferir 'SUBMITTED' si existe para alinear con el resto del sistema
    if "SUBMITTED" in submitted_variants:
        submitted_status = "SUBMITTED"
    else:
        submitted_status = sorted(submitted_variants)[0]

    # Buscar source_status distinto a submitted_status
    candidates = []
    for src, dests in VALID_TRANSITIONS.items():
        if not isinstance(src, str):
            continue
        if src == submitted_status:
            continue
        if submitted_status in dests:
            candidates.append(src)

    if not candidates:
        raise RuntimeError(
            f"No existe transición a {submitted_status} desde un estado distinto. "
            f"VALID_TRANSITIONS={dict(VALID_TRANSITIONS)}"
        )

    # Determinístico
    source_status = sorted(candidates)[0]
    return source_status, submitted_status


def main():
    _reset_db()

    source_status, submitted_status = _find_path_to_submitted()

    # Dataset mínimo directo en DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Provider settings (opcional)
    cur.execute(
        """
        INSERT INTO provider_settings (signature, active, created_at, updated_at)
        VALUES ('Signature on File', 1, datetime('now'), datetime('now'))
        """
    )

    # Patient
    cur.execute(
        """
        INSERT INTO patients (first_name, last_name, date_of_birth, sex, created_at, updated_at)
        VALUES ('Test', 'Patient', '1990-01-01', 'U', datetime('now'), datetime('now'))
        """
    )
    patient_id = cur.lastrowid

    # Coverage
    cur.execute(
        """
        INSERT INTO coverages (
            patient_id, insurer_name, plan_name, policy_number, start_date, created_at, updated_at
        ) VALUES (
            ?, 'TestInsurer', 'TestPlan', 'POL123', '2026-01-01', datetime('now'), datetime('now')
        )
        """,
        (patient_id,),
    )
    coverage_id = cur.lastrowid

    # Claim: crear y forzar status al source_status que realmente puede llegar a submitted
    cur.execute(
        """
        INSERT INTO claims (patient_id, coverage_id, claim_number, status, created_at, updated_at)
        VALUES (?, ?, 'CLM-TEST-G37', ?, datetime('now'), datetime('now'))
        """,
        (patient_id, coverage_id, source_status),
    )
    claim_id = cur.lastrowid

    # Service
    cur.execute(
        """
        INSERT INTO services (
            claim_id, service_date, cpt_code, charge_amount_24f, units_24g,
            outside_lab_20, created_at, updated_at
        ) VALUES (
            ?, '2026-03-03', '90837', 150.0, 1,
            0, datetime('now'), datetime('now')
        )
        """,
        (claim_id,),
    )
    service_id = cur.lastrowid

    # Charge
    cur.execute(
        """
        INSERT INTO charges (service_id, amount, created_at, updated_at)
        VALUES (?, 150.0, datetime('now'), datetime('now'))
        """,
        (service_id,),
    )
    charge_id = cur.lastrowid

    # Payment + application + adjustment
    cur.execute(
        """
        INSERT INTO payments (amount, method, received_date, created_at, updated_at)
        VALUES (100.0, 'cash', '2026-03-03', datetime('now'), datetime('now'))
        """
    )
    payment_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO applications (payment_id, charge_id, amount_applied, created_at)
        VALUES (?, ?, 100.0, datetime('now'))
        """,
        (payment_id, charge_id),
    )

    cur.execute(
        """
        INSERT INTO adjustments (charge_id, amount, reason, created_at)
        VALUES (?, 50.0, 'writeoff', datetime('now'))
        """,
        (charge_id,),
    )

    conn.commit()
    conn.close()

    # Antes: no snapshot
    snap0 = get_latest_snapshot_by_claim(claim_id)
    assert snap0 is None, "No debe existir snapshot todavía"

    # POST real usando test_client
    from app.main import app

    with app.test_client() as client:
        resp = client.post(
            f"/admin/claims/{claim_id}/transition",
            data={"new_status": submitted_status},
            follow_redirects=False,
        )
        body = resp.get_data(as_text=True)
        assert resp.status_code in (302, 303), f"Debe redirigir. got {resp.status_code}. body={body}"

    # Después: snapshot existe
    snap1 = get_latest_snapshot_by_claim(claim_id)
    assert snap1 is not None, "Debe existir snapshot luego de submitted"
    assert snap1.get("snapshot_hash"), "Snapshot debe tener hash"

    # Claim status realmente cambió a submitted (casing real)
    claim2 = get_claim_by_id(claim_id)
    assert claim2["status"] == submitted_status, f"Claim debe quedar {submitted_status}"

    print(f"✅ G37 OK: '{source_status}' -> '{submitted_status}' crea snapshot y cambia status")


if __name__ == "__main__":
    main()