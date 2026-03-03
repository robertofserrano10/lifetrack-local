from app.db.claims import create_claim
from app.db.services import create_service
from app.db.charges import create_charge
from app.db.adjustments import create_adjustment
from app.db.applications import create_application
from app.db.payments import create_payment
from app.db.cms1500_snapshot import generate_cms1500_snapshot
from app.db.connection import get_connection


def main():
    print("=== PHASE 3 — CLAIM LOCK ENFORCEMENT TEST ===\n")

    # ======================================
    # 1. Crear claim base limpio
    # ======================================
    with get_connection() as conn:
        cur = conn.cursor()

        # Crear paciente
        cur.execute(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth, created_at, updated_at)
            VALUES ('Lock', 'Test', '1990-01-01', datetime('now'), datetime('now'))
            """
        )
        patient_id = cur.lastrowid

        # Crear coverage
        cur.execute(
            """
            INSERT INTO coverages (
                patient_id, insurer_name, plan_name, policy_number, start_date,
                created_at, updated_at
            )
            VALUES (?, 'TestInsurer', 'TestPlan', 'POL123', '2024-01-01',
                    datetime('now'), datetime('now'))
            """,
            (patient_id,),
        )
        coverage_id = cur.lastrowid

        conn.commit()

    claim_id = create_claim(patient_id, coverage_id)

    # ======================================
    # 2. Crear service y charge antes del snapshot
    # ======================================
    service_id = create_service(
        claim_id=claim_id,
        service_date="2024-01-01",
        cpt_code="90834",
        units=1,
        diagnosis_code="F32.9",
        description="Test",
        charge_amount_24f=100.0,
    )

    charge_id = create_charge(service_id, 100.0)

    # ======================================
    # 3. Generar snapshot (congela claim)
    # ======================================
    generate_cms1500_snapshot(claim_id)

    print("Snapshot generado. Claim debe estar bloqueado.\n")

    # ======================================
    # 4. Intentar mutaciones (deben fallar)
    # ======================================

    failures = 0

    # create_service
    try:
        create_service(
            claim_id=claim_id,
            service_date="2024-01-02",
            cpt_code="90834",
            units=1,
            diagnosis_code="F32.9",
            description="Test2",
            charge_amount_24f=50.0,
        )
    except ValueError:
        print("OK: create_service bloqueado")
    else:
        failures += 1

    # create_charge
    try:
        create_charge(service_id, 50.0)
    except ValueError:
        print("OK: create_charge bloqueado")
    else:
        failures += 1

    # create_adjustment
    try:
        create_adjustment(charge_id, 10.0, "Test")
    except ValueError:
        print("OK: create_adjustment bloqueado")
    else:
        failures += 1

    # create_application
    try:
        payment_id = create_payment(50.0, "cash", None, "2024-01-01")
        create_application(payment_id, charge_id, 10.0)
    except ValueError:
        print("OK: create_application bloqueado")
    else:
        failures += 1

    print("\n=== RESULT ===")

    if failures == 0:
        print("ALL MUTATIONS CORRECTLY BLOCKED")
    else:
        print(f"FAILURES DETECTED: {failures}")


if __name__ == "__main__":
    main()