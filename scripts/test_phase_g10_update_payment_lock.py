from app.db import (
    create_patient, create_coverage, create_claim, create_service,
    create_charge, create_payment, create_application, get_payment_balance,
)
from app.db.payments import update_payment

print("=== TEST G10: update_payment lock vs applications ===")

# Setup
pid = create_patient("G10", "PaymentLock", "1990-01-01")
cov = create_coverage(pid, "Test", "Plan", "P1", "G1", "I1", "2025-01-01", None)
claim = create_claim(pid, cov)
service = create_service(claim, "2026-02-14", "90834", 1, "F41.1", "G10 test")
charge = create_charge(service, 100.00)

payment_id = create_payment(100.00, "check", "G10-REF", "2026-02-14")
create_application(payment_id, charge, 100.00)

print("PAYMENT BALANCE BEFORE:", get_payment_balance(payment_id))

# Caso A: bajar amount por debajo de lo aplicado -> debe FALLAR
try:
    update_payment(payment_id, 50.00, "check", "G10-REF", "2026-02-14")
    print("ERROR: expected failure when lowering amount below applied")
except ValueError as e:
    print("EXPECTED ERROR (lower below applied):", str(e))

# Caso B: subir amount -> debe PASAR
ok = update_payment(payment_id, 120.00, "check", "G10-REF", "2026-02-14")
print("UPDATE UP OK:", ok)
print("PAYMENT BALANCE AFTER UP:", get_payment_balance(payment_id))

