"""
Test del Invariante 7.1 (README): "Un pago no puede aplicarse por encima de su monto original."

Estrategia:
- DB temporal aislada (no toca lifetrack.db).
- Monkey-patch de get_connection en los modulos relevantes ANTES de invocar.
- Datos minimos: 1 patient -> 1 coverage -> 1 encounter -> 1 claim -> 1 service -> 1 charge ($100).
- 1 payment $50 (via create_payment).
- Intentar create_application(payment, charge, 100.00).
- Resultado esperado: ValueError mencionando "monto disponible" en el payment.

Salida:
  exit code 0  => INVARIANTE PROTEGIDO (codigo bloquea sobreaplicacion).
  exit code 1  => INVARIANTE VIOLADO (codigo deja sobreaplicar). FALLA.
"""
import os
import sys
import sqlite3
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEST_DB = os.path.join(ROOT, "storage", "lifetrack_test_invariant_payment_ceiling.db")
SCHEMA = os.path.join(ROOT, "storage", "schema.sql")

# 1) Recrear DB temporal con schema oficial
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
conn = sqlite3.connect(TEST_DB)
with open(SCHEMA, "r", encoding="utf-8") as f:
    conn.executescript(f.read())
conn.commit()
conn.close()

# 2) Monkey-patch get_connection antes de cargar logica
from app.db import connection as _conn_mod  # noqa: E402

def _test_get_connection():
    c = sqlite3.connect(TEST_DB)
    c.row_factory = sqlite3.Row
    return c

_conn_mod.get_connection = _test_get_connection

# Forzar el override en modulos que ya importaron get_connection
import app.db.applications as _apps_mod  # noqa: E402
_apps_mod.get_connection = _test_get_connection

import app.db.payments as _pay_mod  # noqa: E402
if hasattr(_pay_mod, "get_connection"):
    _pay_mod.get_connection = _test_get_connection

import app.db.financial_lock as _lock_mod  # noqa: E402
if hasattr(_lock_mod, "get_connection"):
    _lock_mod.get_connection = _test_get_connection

# 3) Insertar datos minimos
now = datetime.now(timezone.utc).isoformat()
c = _test_get_connection()
cur = c.cursor()

cur.execute(
    "INSERT INTO patients (first_name, last_name, date_of_birth, created_at, updated_at) "
    "VALUES (?, ?, ?, ?, ?)",
    ("Test", "Patient", "1990-01-01", now, now),
)
patient_id = cur.lastrowid

cur.execute(
    "INSERT INTO coverages (patient_id, insurer_name, plan_name, policy_number, start_date, "
    "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
    (patient_id, "Test Insurer", "Test Plan", "POL-001", "2026-01-01", now, now),
)
coverage_id = cur.lastrowid

cur.execute(
    "INSERT INTO encounters (patient_id, encounter_date, status) VALUES (?, ?, ?)",
    (patient_id, "2026-05-01", "OPEN"),
)
encounter_id = cur.lastrowid

cur.execute(
    "INSERT INTO claims (patient_id, coverage_id, status, created_at, updated_at) "
    "VALUES (?, ?, ?, ?, ?)",
    (patient_id, coverage_id, "DRAFT", now, now),
)
claim_id = cur.lastrowid

cur.execute(
    "INSERT INTO services (claim_id, service_date, cpt_code, charge_amount_24f, units_24g, "
    "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
    (claim_id, "2026-05-01", "90837", 100.00, 1, now, now),
)
service_id = cur.lastrowid

cur.execute(
    "INSERT INTO charges (service_id, amount, created_at, updated_at) "
    "VALUES (?, ?, ?, ?)",
    (service_id, 100.00, now, now),
)
charge_id = cur.lastrowid

c.commit()
c.close()

# 4) Crear payment de $50
from app.db.payments import create_payment  # noqa: E402
payment_id = create_payment(50.00, "check", "TEST-REF-1", "2026-05-01")
print(f"[setup] payment_id={payment_id} amount=$50.00 charge_id={charge_id} charge_amount=$100.00")

# 5) Probar invariante
from app.db.applications import create_application  # noqa: E402

print("[test] Intentando aplicar $100.00 sobre payment de $50.00 (debe FALLAR)")
try:
    create_application(payment_id=payment_id, charge_id=charge_id, amount_applied=100.00)
except ValueError as e:
    msg = str(e).lower()
    if "monto disponible" in msg or "payment" in msg:
        print(f"[PASS] Invariante protegido. Error esperado: {e}")
        # cleanup DB temporal
        try:
            os.remove(TEST_DB)
        except OSError:
            pass
        sys.exit(0)
    else:
        print(f"[FAIL] ValueError pero mensaje inesperado: {e}")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Excepcion inesperada (tipo {type(e).__name__}): {e}")
    sys.exit(1)

print("[FAIL] No hubo excepcion. INVARIANTE VIOLADO: el sistema dejo sobreaplicar.")
sys.exit(1)
