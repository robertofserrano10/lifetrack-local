import gc
import os
import sqlite3
import sys
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEST_DB = os.path.join(ROOT, "storage", "lifetrack_test_phase_3_service_charge_invariant.db")
SCHEMA = os.path.join(ROOT, "storage", "schema.sql")


def recreate_test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    with open(SCHEMA, "r", encoding="utf-8") as handle:
        conn.executescript(handle.read())
    conn.commit()
    conn.close()


def configure_test_db_path():
    import app.config as config_mod

    config_mod.DB_PATH = TEST_DB

    import app.db.connection as connection_mod

    connection_mod.DB_PATH = TEST_DB

    import app.db.encounters as encounters_mod

    encounters_mod.DB_PATH = TEST_DB


def seed_admin_user():
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            ("admin_phase3", generate_password_hash("test-pass"), "ADMIN", now, now),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def load_helpers():
    from app.db import create_claim, create_coverage, create_patient
    from app.db.balances import get_claim_balance
    from app.db.charges import get_charge_by_service
    from app.db.encounters import create_encounter

    return {
        "create_claim": create_claim,
        "create_coverage": create_coverage,
        "create_encounter": create_encounter,
        "create_patient": create_patient,
        "get_charge_by_service": get_charge_by_service,
        "get_claim_balance": get_claim_balance,
    }


def load_app():
    import app.main as main_mod

    main_mod.DB_PATH = TEST_DB
    main_mod.app.testing = True
    return main_mod.app


def set_admin_session(client, user_id: int):
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id
        session["role"] = "ADMIN"


def fetch_one(sql: str, params=()):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_all(sql: str, params=()):
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def table_columns(table_name: str) -> list[str]:
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]
    finally:
        conn.close()


def count_snapshots() -> int:
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cms1500_snapshots")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def main():
    recreate_test_db()
    configure_test_db_path()
    helpers = load_helpers()
    app = load_app()

    create_patient = helpers["create_patient"]
    create_coverage = helpers["create_coverage"]
    create_claim = helpers["create_claim"]
    create_encounter = helpers["create_encounter"]
    get_claim_balance = helpers["get_claim_balance"]
    get_charge_by_service = helpers["get_charge_by_service"]

    admin_user_id = seed_admin_user()

    patient_id = create_patient("Phase3", "Invariant", "1990-01-01")
    coverage_id = create_coverage(
        patient_id,
        "Test",
        "Plan",
        "P3-001",
        "G1",
        "I1",
        "2026-01-01",
        None,
    )
    encounter_id = create_encounter(patient_id, "2026-03-01", provider_id=admin_user_id)
    claim_id_encounter = create_claim(patient_id, coverage_id, encounter_id=encounter_id)
    claim_id_direct = create_claim(patient_id, coverage_id)

    snapshots_before = count_snapshots()
    print("=== TEST PHASE 3 SERVICE -> CHARGE INVARIANT ===")
    print(f"[INFO] encounter_id={encounter_id} claim_encounter={claim_id_encounter} claim_direct={claim_id_direct}")

    with app.test_client() as client:
        set_admin_session(client, admin_user_id)

        response_encounter = client.post(
            f"/admin/encounters/{encounter_id}/service/new",
            data={
                "claim_id": str(claim_id_encounter),
                "service_date": "2026-03-01",
                "cpt_code": "90834",
                "units": "1",
                "charge_amount": "150.00",
            },
            follow_redirects=False,
        )
        assert response_encounter.status_code == 302, (
            f"encounter_add_service no redirigió en éxito: {response_encounter.status_code}"
        )

        encounter_services = fetch_all(
            "SELECT * FROM services WHERE claim_id = ? ORDER BY id",
            (claim_id_encounter,),
        )
        assert len(encounter_services) == 1, "encounter_add_service debe crear 1 service"
        encounter_service = encounter_services[0]
        print(f"[PASS] encounter_add_service crea service id={encounter_service['id']}")

        encounter_charges = fetch_all(
            "SELECT * FROM charges WHERE service_id = ? ORDER BY id",
            (encounter_service["id"],),
        )
        assert len(encounter_charges) == 1, "encounter_add_service debe crear 1 charge asociado"
        encounter_charge = encounter_charges[0]
        assert float(encounter_charge["amount"]) == 150.0, "charge amount debe coincidir con tarifa"
        assert get_charge_by_service(encounter_service["id"])["id"] == encounter_charge["id"]
        print(f"[PASS] encounter_add_service crea charge id={encounter_charge['id']} amount=150.0")
        print("[PASS] no se crea más de un charge para el mismo service")

        encounter_balance = get_claim_balance(claim_id_encounter)
        assert encounter_balance["total_charge"] == 150.0
        assert encounter_balance["balance_due"] == 150.0
        print(f"[PASS] balance derivado del claim encounter={encounter_balance}")

        response_claim = client.post(
            f"/admin/claims/{claim_id_direct}/service/new",
            data={
                "service_date": "2026-03-02",
                "cpt_code": "90837",
                "units": "1",
                "charge_amount": "175.00",
            },
            follow_redirects=False,
        )
        assert response_claim.status_code == 302, (
            f"claim_add_service no redirigió en éxito: {response_claim.status_code}"
        )

        direct_services = fetch_all(
            "SELECT * FROM services WHERE claim_id = ? ORDER BY id",
            (claim_id_direct,),
        )
        assert len(direct_services) == 1, "claim_add_service debe crear 1 service"
        direct_service = direct_services[0]

        direct_charges = fetch_all(
            "SELECT * FROM charges WHERE service_id = ? ORDER BY id",
            (direct_service["id"],),
        )
        assert len(direct_charges) == 1, "claim_add_service debe crear 1 charge"
        direct_charge = direct_charges[0]
        assert float(direct_charge["amount"]) == 175.0

        assert float(encounter_service["charge_amount_24f"]) == float(encounter_charge["amount"])
        assert float(direct_service["charge_amount_24f"]) == float(direct_charge["amount"])
        print("[PASS] ambos flujos dejan service + charge financieramente equivalentes")

        forbidden_columns = {"balance", "remaining", "total_applied", "financial_status"}
        assert not (forbidden_columns & set(table_columns("services")))
        assert not (forbidden_columns & set(table_columns("charges")))
        print("[PASS] no se persiste estado financiero derivado")

    snapshots_after = count_snapshots()
    assert snapshots_after == snapshots_before == 0, "el flujo no debe tocar snapshots/hash"
    print("[PASS] snapshots/hash no se tocan")
    print("SERVICE -> CHARGE INVARIANT TEST PASSED")

    gc.collect()
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError as exc:
            print(f"[WARN] temp db cleanup skipped: {exc}")


if __name__ == "__main__":
    main()
