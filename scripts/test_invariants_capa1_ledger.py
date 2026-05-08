"""
Sprint 1 — Tests de invariantes Capa 1 (Ledger Core) de LifeTrack.

Cubre:
  A1  applied_amount > remaining_payment    -> reject  [duplicado en test_invariant_payment_ceiling.py]
  A2  applied_amount > remaining_charge     -> reject
  A3  applied_amount <= 0                   -> reject
  A4  multiples applications mismo payment, sum <= total
  A5  multiples applications mismo charge, sum <= total
  A6  eliminar application: balance recalcula correctamente (test estructural)
  A7  application bloqueada si claim locked por snapshot
  A8  charge_id inexistente                 -> reject
  A9  payment_id inexistente                -> reject
  B6  Schema NO contiene campo balance persistido (estructural)

Salida:
  exit code 0  => TODOS los invariantes protegidos
  exit code 1  => al menos uno violado
"""
import os
import sys
import gc
import sqlite3
import hashlib
import time
from datetime import datetime, timezone


# Connection subclass that ACTUALLY closes on context-manager exit.
# (sqlite3.Connection.__exit__ commits/rollbacks but does NOT close.)
class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, tb):
        try:
            super().__exit__(exc_type, exc_value, tb)
        finally:
            self.close()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEST_DB = os.path.join(ROOT, "storage", "lifetrack_test_invariants_capa1.db")
SCHEMA = os.path.join(ROOT, "storage", "schema.sql")


# ============================================================
# Setup helpers
# ============================================================
def fresh_db():
    """Recrea TEST_DB desde schema.sql oficial. Lidia con file-locking de Windows."""
    gc.collect()
    if os.path.exists(TEST_DB):
        for _ in range(5):
            try:
                os.remove(TEST_DB)
                break
            except PermissionError:
                gc.collect()
                time.sleep(0.1)
    c = sqlite3.connect(TEST_DB)
    with open(SCHEMA, "r", encoding="utf-8") as f:
        c.executescript(f.read())
    c.commit()
    c.close()


def get_test_conn():
    c = sqlite3.connect(TEST_DB, factory=ClosingConnection)
    c.row_factory = sqlite3.Row
    return c


# Monkey-patch get_connection en TODOS los modulos relevantes ANTES del primer uso
def patch_connection_modules():
    from app.db import connection as _conn_mod
    _conn_mod.get_connection = get_test_conn

    import app.db.applications as _apps
    _apps.get_connection = get_test_conn
    import app.db.payments as _pay
    if hasattr(_pay, "get_connection"):
        _pay.get_connection = get_test_conn
    import app.db.financial_lock as _lock
    if hasattr(_lock, "get_connection"):
        _lock.get_connection = get_test_conn


def make_minimal_claim(charge_amount: float = 100.00):
    """
    Crea: 1 patient, 1 coverage, 1 claim, 1 service, 1 charge.
    Retorna: (patient_id, coverage_id, claim_id, service_id, charge_id)
    """
    now = datetime.now(timezone.utc).isoformat()
    c = get_test_conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO patients (first_name, last_name, date_of_birth, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("Test", "Patient", "1990-01-01", now, now),
    )
    pid = cur.lastrowid
    cur.execute(
        "INSERT INTO coverages (patient_id, insurer_name, plan_name, policy_number, "
        "start_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (pid, "Ins", "Plan", "POL-1", "2026-01-01", now, now),
    )
    cov = cur.lastrowid
    cur.execute(
        "INSERT INTO claims (patient_id, coverage_id, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (pid, cov, "DRAFT", now, now),
    )
    claim_id = cur.lastrowid
    cur.execute(
        "INSERT INTO services (claim_id, service_date, cpt_code, charge_amount_24f, units_24g, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (claim_id, "2026-05-01", "90837", charge_amount, 1, now, now),
    )
    sid = cur.lastrowid
    cur.execute(
        "INSERT INTO charges (service_id, amount, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (sid, charge_amount, now, now),
    )
    chid = cur.lastrowid
    c.commit()
    c.close()
    return pid, cov, claim_id, sid, chid


def insert_snapshot(claim_id: int, version: int = 1):
    """Inserta un snapshot para activar lock financiero del claim."""
    c = get_test_conn()
    cur = c.cursor()
    payload = f'{{"claim_id":{claim_id},"version":{version}}}'
    h = hashlib.sha256(payload.encode()).hexdigest()
    cur.execute(
        "INSERT INTO cms1500_snapshots (claim_id, version_number, snapshot_json, snapshot_hash) "
        "VALUES (?, ?, ?, ?)",
        (claim_id, version, payload, h),
    )
    c.commit()
    c.close()


# ============================================================
# Cada test retorna (passed: bool, msg: str)
# ============================================================
def test_A2_charge_ceiling():
    """A2: applied_amount > remaining_charge -> reject."""
    fresh_db()
    _, _, _, _, charge_id = make_minimal_claim(charge_amount=50.00)
    from app.db.payments import create_payment
    from app.db.applications import create_application
    pid = create_payment(200.00, "check", "REF", "2026-05-01")
    try:
        create_application(payment_id=pid, charge_id=charge_id, amount_applied=100.00)
        return False, "Permitio aplicar $100 sobre charge de $50 (charge ceiling violado)"
    except ValueError as e:
        if "balance" in str(e).lower() or "charge" in str(e).lower():
            return True, f"OK: {e}"
        return False, f"ValueError pero mensaje inesperado: {e}"


def test_A3_amount_non_positive():
    """A3: amount_applied <= 0 -> reject."""
    fresh_db()
    _, _, _, _, charge_id = make_minimal_claim()
    from app.db.payments import create_payment
    from app.db.applications import create_application
    pid = create_payment(100.00, "check", "REF", "2026-05-01")
    casos = [0, -1, -50.00]
    for amt in casos:
        try:
            create_application(payment_id=pid, charge_id=charge_id, amount_applied=amt)
            return False, f"Permitio amount_applied={amt}"
        except ValueError:
            continue
    return True, "OK: rechazo 0, -1, -50"


def test_A4_multiple_apps_same_payment():
    """A4: 2 applications del mismo payment, suma > total -> 2da rechazada."""
    fresh_db()
    _, _, _, _, ch1 = make_minimal_claim(charge_amount=200.00)
    # crear segundo charge en mismo claim
    c = get_test_conn()
    cur = c.cursor()
    sid = cur.execute("SELECT id FROM services LIMIT 1").fetchone()[0]
    now = datetime.now(timezone.utc).isoformat()
    cur.execute("INSERT INTO charges (service_id, amount, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (sid, 200.00, now, now))
    ch2 = cur.lastrowid
    c.commit()
    c.close()
    from app.db.payments import create_payment
    from app.db.applications import create_application
    pid = create_payment(100.00, "check", "REF", "2026-05-01")
    create_application(payment_id=pid, charge_id=ch1, amount_applied=80.00)  # OK
    try:
        create_application(payment_id=pid, charge_id=ch2, amount_applied=50.00)  # 80+50>100
        return False, "Permitio segunda aplicacion que excede total del payment"
    except ValueError as e:
        return True, f"OK: 2da aplicacion rechazada: {e}"


def test_A5_multiple_apps_same_charge():
    """A5: 2 payments aplicados al mismo charge, suma > charge -> 2da rechazada."""
    fresh_db()
    _, _, _, _, charge_id = make_minimal_claim(charge_amount=100.00)
    from app.db.payments import create_payment
    from app.db.applications import create_application
    p1 = create_payment(80.00, "check", "REF1", "2026-05-01")
    p2 = create_payment(50.00, "check", "REF2", "2026-05-01")
    create_application(payment_id=p1, charge_id=charge_id, amount_applied=80.00)  # OK
    try:
        create_application(payment_id=p2, charge_id=charge_id, amount_applied=50.00)  # 80+50>100
        return False, "Permitio aplicar 2do pago que excede balance del charge"
    except ValueError as e:
        return True, f"OK: 2da aplicacion rechazada: {e}"


def test_A6_delete_application_recalculates():
    """A6: eliminar application via SQL -> SUM(amount_applied) recalcula correcto.
    NOTA: no existe API delete_application; se simula con DELETE raw + verifica
    que balance derivado refleja el cambio. WARN: trail audit no se emite si no
    hay API expuesta."""
    fresh_db()
    _, _, _, _, charge_id = make_minimal_claim(charge_amount=100.00)
    from app.db.payments import create_payment
    from app.db.applications import create_application
    pid = create_payment(100.00, "check", "REF", "2026-05-01")
    app_id = create_application(payment_id=pid, charge_id=charge_id, amount_applied=60.00)

    c = get_test_conn()
    cur = c.cursor()
    sum_before = cur.execute(
        "SELECT COALESCE(SUM(amount_applied), 0) FROM applications WHERE charge_id=?",
        (charge_id,)).fetchone()[0]
    cur.execute("DELETE FROM applications WHERE id=?", (app_id,))
    c.commit()
    sum_after = cur.execute(
        "SELECT COALESCE(SUM(amount_applied), 0) FROM applications WHERE charge_id=?",
        (charge_id,)).fetchone()[0]
    c.close()

    if float(sum_before) == 60.00 and float(sum_after) == 0.00:
        return True, "OK: balance derivado se recalcula tras DELETE. WARN: sin API audit-friendly"
    return False, f"Balance no recalcula bien: before={sum_before} after={sum_after}"


def test_A7_locked_claim_blocks_application():
    """A7: si existe snapshot del claim, create_application debe rechazar."""
    fresh_db()
    _, _, claim_id, _, charge_id = make_minimal_claim()
    insert_snapshot(claim_id)
    from app.db.payments import create_payment
    from app.db.applications import create_application
    pid = create_payment(50.00, "check", "REF", "2026-05-01")
    try:
        create_application(payment_id=pid, charge_id=charge_id, amount_applied=10.00)
        return False, "Permitio aplicacion sobre claim congelado por snapshot"
    except ValueError as e:
        if "congelado" in str(e).lower() or "lock" in str(e).lower() or "snapshot" in str(e).lower():
            return True, f"OK: lock activo: {e}"
        return False, f"ValueError pero mensaje inesperado: {e}"


def test_A8_nonexistent_charge():
    """A8: charge_id inexistente -> rechazo."""
    fresh_db()
    make_minimal_claim()
    from app.db.payments import create_payment
    from app.db.applications import create_application
    pid = create_payment(50.00, "check", "REF", "2026-05-01")
    try:
        create_application(payment_id=pid, charge_id=99999, amount_applied=10.00)
        return False, "Permitio aplicacion con charge_id inexistente"
    except ValueError as e:
        return True, f"OK: {e}"


def test_A9_nonexistent_payment():
    """A9: payment_id inexistente -> rechazo."""
    fresh_db()
    _, _, _, _, charge_id = make_minimal_claim()
    from app.db.applications import create_application
    try:
        create_application(payment_id=99999, charge_id=charge_id, amount_applied=10.00)
        return False, "Permitio aplicacion con payment_id inexistente"
    except ValueError as e:
        return True, f"OK: {e}"


def test_B6_no_persisted_balance():
    """B6: schema oficial NO debe contener columna 'balance' en charges/claims/payments."""
    fresh_db()
    c = get_test_conn()
    cur = c.cursor()
    offenders = []
    for tbl in ["charges", "claims", "payments"]:
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({tbl})").fetchall()]
        for col in cols:
            if col.lower() == "balance":
                offenders.append(f"{tbl}.{col}")
    c.close()
    if offenders:
        return False, f"Schema persiste balance: {offenders}"
    return True, "OK: schema no persiste campo 'balance'"


# ============================================================
# Runner
# ============================================================
def main():
    patch_connection_modules()
    suite = [
        ("A2 charge ceiling", test_A2_charge_ceiling),
        ("A3 amount no-positivo", test_A3_amount_non_positive),
        ("A4 sum payment <= total", test_A4_multiple_apps_same_payment),
        ("A5 sum charge <= total", test_A5_multiple_apps_same_charge),
        ("A6 delete recalcula balance", test_A6_delete_application_recalculates),
        ("A7 claim locked bloquea", test_A7_locked_claim_blocks_application),
        ("A8 charge inexistente", test_A8_nonexistent_charge),
        ("A9 payment inexistente", test_A9_nonexistent_payment),
        ("B6 sin balance persistido", test_B6_no_persisted_balance),
    ]
    failed = []
    for name, fn in suite:
        try:
            ok, msg = fn()
        except Exception as e:
            ok = False
            msg = f"EXCEPCION: {type(e).__name__}: {e}"
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not ok:
            failed.append(name)

    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass

    print()
    print(f"=== Resultado: {len(suite) - len(failed)}/{len(suite)} ===")
    if failed:
        print(f"FAIL: {failed}")
        sys.exit(1)
    print("Todos los invariantes Capa 1 protegidos.")
    sys.exit(0)


if __name__ == "__main__":
    main()
