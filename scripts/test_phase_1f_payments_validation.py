from app.db import create_payment

print("=== TEST PAYMENTS VALIDATION ===")

# Caso válido
pid = create_payment(100.00, "check", "EOB-VAL-1", "2026-02-10")
print("VALID PAYMENT ID:", pid)

# Caso monto inválido
try:
    create_payment(0, "check", None, "2026-02-10")
except Exception as e:
    print("EXPECTED ERROR (amount 0):", e)

# Caso método inválido
try:
    create_payment(100, "bitcoin", None, "2026-02-10")
except Exception as e:
    print("EXPECTED ERROR (method):", e)

# Caso fecha obligatoria
try:
    create_payment(100, "check", None, None)
except Exception as e:
    print("EXPECTED ERROR (date):", e)
