from app.db import (
    create_patient,
    create_coverage,
    create_claim,
    create_service,
    create_charge,
    create_payment,
    create_application,
    create_adjustment,
    get_charge_balance,
    get_claim_balance,
)

print("=== SETUP ===")

# Paciente
pid = create_patient("Test", "Adjustments", "1990-01-01")

# Cobertura
cov_id = create_coverage(
    patient_id=pid,
    insurer_name="Test Insurance",
    plan_name="Test Plan",
    policy_number="POL-ADJ",
    group_number="GRP-ADJ",
    insured_id="INS-ADJ",
    start_date="2025-01-01",
    end_date=None
)

# Claim
claim_id = create_claim(pid, cov_id)

# Servicio
service_id = create_service(
    claim_id=claim_id,
    service_date="2026-02-04",
    cpt_code="90834",
    units=1,
    diagnosis_code="F41.1",
    description="Servicio con ajuste"
)

# Charge
charge_id = create_charge(service_id=service_id, amount=150.00)

# Payment
payment_id = create_payment(
    amount=150.00,
    method="check",
    reference="EOB-ADJ-001",
    received_date="2026-02-04"
)

# Application (pago completo)
create_application(
    payment_id=payment_id,
    charge_id=charge_id,
    amount_applied=150.00
)

print("\nBEFORE ADJUSTMENT")
print(get_charge_balance(charge_id))

# Adjustment (write-off)
create_adjustment(
    charge_id=charge_id,
    amount=20.00,
    reason="Contractual adjustment"
)

print("\nAFTER ADJUSTMENT")
print(get_charge_balance(charge_id))

print("\nCLAIM BALANCE")
print(get_claim_balance(claim_id))
