from app.db import (
    create_patient,
    create_coverage,
    create_claim,
    create_service,
    create_charge,
    create_payment,
)
from app.db.applications import create_application
from app.db.balances import get_charge_balance, get_claim_balance

# Setup mínimo
pid = create_patient("Balance", "Test", "1990-01-01")
cov = create_coverage(
    pid,
    "Test",
    "Plan",
    "P1",
    "G1",
    "I1",
    "2025-01-01",
    None
)
claim_id = create_claim(pid, cov)

service_id = create_service(
    claim_id=claim_id,
    service_date="2026-02-04",
    cpt_code="90834",
    units=1,
    diagnosis_code="F41.1",
    description="Servicio balance"
)

charge_id = create_charge(service_id, 150.00)
payment_id = create_payment(150.00, "check", "EOB-BAL-1", "2026-02-04")
create_application(payment_id, charge_id, 150.00)

print("CHARGE BALANCE:", get_charge_balance(charge_id))
print("CLAIM BALANCE:", get_claim_balance(claim_id))
