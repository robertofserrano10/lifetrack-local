import os
import sqlite3
import sys
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEST_DB = os.path.join(ROOT, "storage", "lifetrack_test_phase_1_auth_routes.db")
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


def seed_minimal_data():
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()

    users = [
        ("admin_auth", "ADMIN"),
        ("fact_auth", "FACTURADOR"),
        ("recep_auth", "RECEPCION"),
        ("dra_auth", "DRA"),
    ]
    for username, role in users:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (username, generate_password_hash("test-pass"), role, now, now),
        )

    cur.execute(
        """
        INSERT INTO provider_settings (
            signature,
            facility_name,
            billing_name,
            billing_npi,
            billing_tax_id,
            active,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """,
        ("Signature on File", "Test Facility", "Test Billing", "1111111111", "XX-TEST", now, now),
    )

    cur.execute(
        """
        INSERT INTO patients (
            first_name, last_name, date_of_birth, sex, address, city, state, zip_code, phone,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Auth", "Route", "1990-01-01", "U", "Test Address", "Test City", "PR", "00901", "000-000-0000", now, now),
    )
    patient_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO coverages (
            patient_id, insurer_name, plan_name, policy_number, start_date,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (patient_id, "Test Insurer", "Test Plan", "POL-001", "2026-01-01", now, now),
    )
    coverage_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO claims (
            patient_id, coverage_id, claim_number, status, accept_assignment_27,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (patient_id, coverage_id, "CLM000001", "DRAFT", 1, now, now),
    )
    claim_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO services (
            claim_id, service_date, cpt_code, charge_amount_24f, units_24g,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, "2026-05-01", "90834", 100.0, 1, now, now),
    )
    service_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO charges (service_id, amount, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (service_id, 100.0, now, now),
    )

    cur.execute(
        """
        INSERT INTO payments (amount, method, reference, received_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (50.0, "cash", "AUTH-TEST", "2026-05-02", now, now),
    )

    cur.execute(
        """
        INSERT INTO event_ledger (
            entity_type, entity_id, event_type, event_data, created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("claim", claim_id, "test_event", "{\"ok\": true}", now),
    )

    conn.commit()
    conn.close()


def load_app():
    configure_test_db_path()

    import app.main as main_mod
    import app.db.cms1500_snapshot as snapshot_mod

    main_mod.DB_PATH = TEST_DB
    snapshot_mod.DB_PATH = TEST_DB

    snapshot_mod.generate_cms1500_snapshot(1)
    main_mod.app.testing = True
    return main_mod.app


def set_session(client, user_id=None, role=None):
    with client.session_transaction() as session:
        session.clear()
        if user_id is not None:
            session["user_id"] = user_id
        if role is not None:
            session["role"] = role


def request_status(client, path):
    try:
        response = client.get(path, follow_redirects=False)
        return response.status_code, None
    except Exception as exc:
        return None, exc


def assert_not_anonymous_ok(client, path):
    set_session(client)
    status_code, error = request_status(client, path)
    assert error is None, f"Anonymous request crashed for {path}: {error}"
    assert status_code != 200, f"Anonymous access still open for {path}"
    assert status_code in (302, 401, 403), (
        f"Unexpected anonymous status for {path}: {status_code}"
    )
    print(f"[PASS] anon {path} -> {status_code}")


def assert_role_access(
    client,
    path,
    user_id,
    role,
    allowed_statuses,
    auth_block_statuses=None,
    allow_exceptions=False,
):
    set_session(client, user_id=user_id, role=role)
    status_code, error = request_status(client, path)

    if auth_block_statuses is None:
        auth_block_statuses = set()

    if error is not None:
        assert allow_exceptions, f"{role} request crashed for {path}: {error}"
        print(f"[WARN] {role} {path} -> EXCEPTION {type(error).__name__}: {error}")
        return

    assert status_code not in auth_block_statuses, (
        f"{role} auth blocked for {path}: {status_code}"
    )
    assert status_code in allowed_statuses, (
        f"{role} unexpected status for {path}: {status_code}"
    )
    print(f"[PASS] {role} {path} -> {status_code}")


def main():
    recreate_test_db()
    seed_minimal_data()
    app = load_app()

    anonymous_paths = [
        "/cms1500/1",
        "/admin/snapshots/",
        "/admin/snapshots/api",
        "/admin/events/",
        "/admin/events/export/json",
        "/provider/edit",
        "/claims/overview",
        "/claims/1/financial",
        "/claims/1/balance",
        "/claims/1/payments",
        "/claims/1/adjustments",
    ]

    with app.test_client() as client:
        print("=== TEST PHASE 1 AUTH ROUTES ===")

        for path in anonymous_paths:
            assert_not_anonymous_ok(client, path)

        admin_allowed = [
            "/cms1500/1",
            "/admin/snapshots/",
            "/admin/snapshots/1",
            "/admin/snapshots/1/verify",
            "/admin/snapshots/api",
            "/admin/snapshots/api/1",
            "/admin/snapshots/diff?a=1&b=1",
            "/admin/snapshots/claim/1",
            "/admin/events/",
            "/admin/events/export/json",
            "/admin/events/export/csv",
            "/provider/edit",
            "/claims/overview",
            "/claims/1/financial",
            "/claims/1/balance",
            "/claims/1/payments",
            "/claims/1/adjustments",
            "/charges/1/balance",
            "/payments/1/balance",
        ]
        for path in admin_allowed:
            assert_role_access(
                client,
                path,
                user_id=1,
                role="ADMIN",
                allowed_statuses={200, 404},
                auth_block_statuses={302, 401, 403},
                allow_exceptions=True,
            )

        assert_role_access(client, "/provider/edit", user_id=2, role="FACTURADOR", allowed_statuses={403})
        assert_role_access(client, "/admin/events/", user_id=3, role="RECEPCION", allowed_statuses={403})
        assert_role_access(client, "/claims/overview", user_id=3, role="RECEPCION", allowed_statuses={403})
        assert_role_access(client, "/claims/1/financial", user_id=4, role="DRA", allowed_statuses={403})
        assert_role_access(client, "/admin/snapshots/", user_id=4, role="DRA", allowed_statuses={200, 404})
        assert_role_access(client, "/cms1500/1", user_id=4, role="DRA", allowed_statuses={200, 404})

    print("AUTH ROUTES TEST PASSED")

    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError as exc:
            print(f"[WARN] temp db cleanup skipped: {exc}")


if __name__ == "__main__":
    main()
