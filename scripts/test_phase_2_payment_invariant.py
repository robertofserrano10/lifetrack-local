import gc
import os
import sqlite3
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEST_DB = os.path.join(ROOT, "storage", "lifetrack_test_phase_2_payment_invariant.db")
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


def get_helpers():
    from app.db import (
        create_application,
        create_charge,
        create_claim,
        create_coverage,
        create_patient,
        create_payment,
        create_service,
        get_payment_balance,
    )
    from app.db.payments import get_payment_by_id, update_payment

    return {
        "create_application": create_application,
        "create_charge": create_charge,
        "create_claim": create_claim,
        "create_coverage": create_coverage,
        "create_patient": create_patient,
        "create_payment": create_payment,
        "create_service": create_service,
        "get_payment_balance": get_payment_balance,
        "get_payment_by_id": get_payment_by_id,
        "update_payment": update_payment,
    }


def count_applications(payment_id: int) -> int:
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM applications WHERE payment_id = ?", (payment_id,))
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def payment_amount(payment_id: int) -> float:
    conn = sqlite3.connect(TEST_DB)
    try:
        cur = conn.cursor()
        cur.execute("SELECT amount FROM payments WHERE id = ?", (payment_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Payment no existe en test DB")
        return float(row[0])
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


def main():
    recreate_test_db()
    configure_test_db_path()
    helpers = get_helpers()

    create_patient = helpers["create_patient"]
    create_coverage = helpers["create_coverage"]
    create_claim = helpers["create_claim"]
    create_service = helpers["create_service"]
    create_charge = helpers["create_charge"]
    create_payment = helpers["create_payment"]
    create_application = helpers["create_application"]
    get_payment_balance = helpers["get_payment_balance"]
    get_payment_by_id = helpers["get_payment_by_id"]
    update_payment = helpers["update_payment"]

    print("=== TEST PHASE 2 PAYMENT INVARIANT ===")

    patient_id = create_patient("Phase2", "Invariant", "1990-01-01")
    coverage_id = create_coverage(
        patient_id,
        "Test",
        "Plan",
        "P1",
        "G1",
        "I1",
        "2026-01-01",
        None,
    )
    claim_id = create_claim(patient_id, coverage_id)
    service_id = create_service(claim_id, "2026-02-14", "90834", 1, "F41.1", "Phase 2 test")
    charge_id = create_charge(service_id, 100.00)

    payment_id = create_payment(100.00, "check", "P2-REF", "2026-02-14")
    application_id = create_application(payment_id, charge_id, 80.00)

    print(f"[INFO] payment_id={payment_id} application_id={application_id}")
    print(f"[INFO] balance inicial={get_payment_balance(payment_id)}")

    initial_app_count = count_applications(payment_id)
    initial_amount = payment_amount(payment_id)

    try:
        update_payment(payment_id, 70.00, "check", "P2-REF", "2026-02-14")
        raise AssertionError("Se esperaba ValueError al bajar amount por debajo de lo aplicado")
    except ValueError as exc:
        amount_after_invalid = payment_amount(payment_id)
        app_count_after_invalid = count_applications(payment_id)
        assert amount_after_invalid == initial_amount, "amount cambió después del intento inválido"
        assert app_count_after_invalid == initial_app_count, "se creó o alteró una application en intento inválido"
        print(f"[PASS] rechaza 70 < 80 aplicado -> {exc}")
        print(f"[PASS] amount permanece en {amount_after_invalid} tras intento inválido")
        print(f"[PASS] applications siguen en {app_count_after_invalid} tras intento inválido")

    ok_equal = update_payment(payment_id, 80.00, "check", "P2-REF", "2026-02-14")
    assert ok_equal is True, "update_payment debe devolver True al permitir 80 == aplicado"
    assert payment_amount(payment_id) == 80.00, "amount no quedó en 80"
    assert count_applications(payment_id) == initial_app_count, "update válido no debe crear applications"
    print("[PASS] permite 80 == 80 aplicado")

    ok_higher = update_payment(payment_id, 120.00, "check", "P2-REF", "2026-02-14")
    assert ok_higher is True, "update_payment debe devolver True al permitir 120 > aplicado"
    assert payment_amount(payment_id) == 120.00, "amount no quedó en 120"
    assert count_applications(payment_id) == initial_app_count, "update mayor no debe crear applications"
    print("[PASS] permite 120 > 80 aplicado")

    balance_after = get_payment_balance(payment_id)
    assert balance_after["total_amount"] == 120.0, "balance derivado no refleja amount actualizado"
    assert balance_after["total_applied"] == 80.0, "total aplicado debe permanecer en 80"
    assert balance_after["remaining"] == 40.0, "remaining derivado debe ser 40"
    print(f"[PASS] balance derivado final={balance_after}")

    payment_row = get_payment_by_id(payment_id)
    assert payment_row["amount"] == 120.0, "payment final debe persistir amount=120"
    print("[PASS] payment final persiste solo el amount esperado")

    forbidden_columns = {"remaining", "balance", "total_applied", "financial_status"}
    payment_columns = set(table_columns("payments"))
    application_columns = set(table_columns("applications"))
    assert not (forbidden_columns & payment_columns), "payments no debe persistir balance derivado"
    assert not (forbidden_columns & application_columns), "applications no debe persistir balance derivado"
    print("[PASS] no se persiste estado financiero derivado en payments/applications")

    print("PAYMENT INVARIANT TEST PASSED")

    gc.collect()
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError as exc:
            print(f"[WARN] temp db cleanup skipped: {exc}")


if __name__ == "__main__":
    main()
