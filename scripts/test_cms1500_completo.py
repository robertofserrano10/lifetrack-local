"""
TEST CMS-1500 COMPLETO
Crea un paciente completo con todos los datos y verifica
campo por campo lo que aparece en el snapshot CMS-1500.

Correr desde la carpeta raiz del proyecto:
  python -m scripts.test_cms1500_completo
"""

import json
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim
from app.db.services import create_service
from app.db.charges import create_charge
from app.db.payments import create_payment
from app.db.applications import create_application
from app.db.cms1500_snapshot import generate_cms1500_snapshot, get_latest_snapshot_by_claim

print("=" * 60)
print("TEST CMS-1500 COMPLETO")
print("=" * 60)

# ─────────────────────────────────────────
# 1. PACIENTE
# ─────────────────────────────────────────
print("\n[1] Creando paciente...")
patient_id = create_patient(
    first_name="Maria",
    last_name="Rodriguez",
    date_of_birth="1985-06-15",
    sex="F",
    marital_status="married",
    employment_status="employed",
    student_status=None,
    address="200 Calle Roble",
    city="San Juan",
    state="PR",
    zip_code="00901",
    phone="787-555-1234",
)
print(f"    ✅ Paciente ID: {patient_id}")

# ─────────────────────────────────────────
# 2. COVERAGE
# ─────────────────────────────────────────
print("\n[2] Creando coverage...")
coverage_id = create_coverage(
    patient_id=patient_id,
    insurer_name="Triple-S",
    plan_name="Vital",
    policy_number="TSS-999888",
    group_number="GRP-001",
    insured_id="INS-12345",
    start_date="2026-01-01",
    end_date=None,
    insured_first_name="Jose",
    insured_last_name="Rodriguez",
    relationship_to_insured="spouse",
    insured_address="100 Calle Principal",
    insured_city="San Juan",
    insured_state="PR",
    insured_zip="00901",
    other_health_plan_11d=0,
)
print(f"    ✅ Coverage ID: {coverage_id}")

# ─────────────────────────────────────────
# 3. CLAIM
# ─────────────────────────────────────────
print("\n[3] Creando claim...")
from app.db.connection import get_connection
with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO claims (patient_id, coverage_id, status, created_at, updated_at)
        VALUES (?, ?, 'DRAFT', datetime('now'), datetime('now'))
    """, (patient_id, coverage_id))
    conn.commit()
    claim_id = cur.lastrowid
print(f"    ✅ Claim ID: {claim_id}")

# ─────────────────────────────────────────
# 3b. DIAGNÓSTICOS en el claim
# ─────────────────────────────────────────
print("\n[3b] Agregando diagnósticos al claim...")
from app.db.claims import update_claim_cms_fields
update_claim_cms_fields(
    claim_id=claim_id,
    diagnosis_1="F41.1",
    diagnosis_2="F32.9",
    diagnosis_3="Z63.0",
)
print("    ✅ Diagnósticos A=F41.1, B=F32.9, C=Z63.0")

# ─────────────────────────────────────────
# 4. SERVICE con diagnosis_code
# ─────────────────────────────────────────
print("\n[4] Creando service con CPT y diagnóstico...")

# Check if diagnosis_code column exists in services, add if not
with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(services)")
    cols = [r["name"] for r in cur.fetchall()]
    if "diagnosis_code" not in cols:
        conn.execute("ALTER TABLE services ADD COLUMN diagnosis_code TEXT")
        conn.commit()
        print("    ℹ️  Columna diagnosis_code agregada a services")

# Insert service directly to include diagnosis_code
with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO services (
            claim_id, service_date, cpt_code, units_24g,
            charge_amount_24f, place_of_service_24b,
            diagnosis_pointer_24e, diagnosis_code,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (
        claim_id, "2026-03-17", "90837", 1,
        150.00, "11",
        "A", "F41.1",
    ))
    conn.commit()
    service_id = cur.lastrowid
print(f"    ✅ Service ID: {service_id} | CPT: 90837 | Dx: F41.1")

# ─────────────────────────────────────────
# 5. CHARGE
# ─────────────────────────────────────────
print("\n[5] Creando charge...")
charge_id = create_charge(service_id=service_id, amount=150.00)
print(f"    ✅ Charge ID: {charge_id}")

# ─────────────────────────────────────────
# 6. SNAPSHOT
# ─────────────────────────────────────────
print("\n[6] Generando snapshot CMS-1500...")
try:
    snapshot_data = generate_cms1500_snapshot(claim_id)
    print(f"    ✅ Snapshot generado")
except Exception as e:
    print(f"    ❌ Error generando snapshot: {e}")
    sys.exit(1)

# ─────────────────────────────────────────
# 7. VERIFICACIÓN CAMPO POR CAMPO
# ─────────────────────────────────────────
snap = get_latest_snapshot_by_claim(claim_id)
if not snap:
    print("❌ No se pudo leer el snapshot")
    sys.exit(1)

s = snap["snapshot"]  # el payload real está dentro de snap["snapshot"]
print(f"    ✅ Snapshot hash: {snap.get('snapshot_hash','')[:16]}...")

print("\n" + "=" * 60)
print("VERIFICACIÓN CMS-1500 — CAMPO POR CAMPO")
print("=" * 60)

def check(casilla, descripcion, valor):
    if valor and valor != "—" and valor != "" and valor is not None:
        print(f"  ✅ Casilla {casilla}: {descripcion} = {valor}")
    else:
        print(f"  ❌ Casilla {casilla}: {descripcion} = VACÍO")

print("\n--- PACIENTE ---")
check("2",   "Patient Name",       f"{s.get('patient',{}).get('last_name')} {s.get('patient',{}).get('first_name')}")
check("3a",  "Date of Birth",      s.get('patient',{}).get('date_of_birth'))
check("3b",  "Sex",                s.get('patient',{}).get('sex'))
check("5a",  "Patient Address",    s.get('patient',{}).get('address'))
check("5b",  "Patient City",       s.get('patient',{}).get('city'))
check("5c",  "Patient ZIP",        s.get('patient',{}).get('zip_code'))
check("5d",  "Patient Phone",      s.get('patient',{}).get('phone'))
check("8a",  "Marital Status",     s.get('patient',{}).get('marital_status'))
check("8b",  "Employment Status",  s.get('patient',{}).get('employment_status'))

print("\n--- SEGURO ---")
check("1",   "Plan Name",          s.get('insurance',{}).get('plan_name'))
check("1a",  "Insured ID",         s.get('insurance',{}).get('insured_id'))
check("4",   "Insured Name",       s.get('insurance',{}).get('insured_name'))
check("6",   "Relationship",       s.get('insurance',{}).get('relationship_to_insured'))
check("7",   "Insured Address",    s.get('insurance',{}).get('insured_address',{}).get('address'))
check("7b",  "Insured City",       s.get('insurance',{}).get('insured_address',{}).get('city'))
check("11",  "Policy Number",      s.get('insurance',{}).get('policy_number'))
check("11c", "Insurer Name",       s.get('insurance',{}).get('insurer_name'))

print("\n--- DIAGNÓSTICOS ---")
diags = s.get('diagnoses', {})
for letter in 'ABCDEFGHIJKL':
    val = diags.get(letter)
    if val:
        print(f"  ✅ Casilla 21{letter}: {val}")
    else:
        print(f"  ⬜ Casilla 21{letter}: (vacío — normal si no aplica)")

print("\n--- SERVICES ---")
services = s.get('services', [])
for i, svc in enumerate(services):
    check(f"24A[{i+1}]", "Service Date",    svc.get('service_date'))
    check(f"24D[{i+1}]", "CPT Code",        svc.get('cpt_code'))
    check(f"24E[{i+1}]", "Dx Pointer",      svc.get('dx_pointer'))
    check(f"24F[{i+1}]", "Charge Amount",   str(svc.get('charge_amount_24f')))
    check(f"24G[{i+1}]", "Units",           str(svc.get('units')))
    check(f"diag[{i+1}]","Diagnosis Code",  svc.get('diagnosis_code'))

print("\n--- PROVIDER ---")
prov = s.get('provider', {})
check("25",  "Tax ID",             prov.get('billing',{}).get('tax_id'))
check("31",  "Signature",          prov.get('signature'))
check("32",  "Facility Name",      prov.get('facility',{}).get('name'))
check("33",  "Billing Name",       prov.get('billing',{}).get('name'))
check("33b", "Billing NPI",        prov.get('billing',{}).get('npi'))

print("\n--- TOTALES ---")
totals = s.get('totals', {})
tc = totals.get('total_charge')
ap = totals.get('amount_paid')
bd = totals.get('balance_due')
check("28",  "Total Charge",  f"${tc}" if tc is not None else None)
check("29",  "Amount Paid",   f"${ap}" if ap is not None else None)
check("30",  "Balance Due",   f"${bd}" if bd is not None else None)

print("\n" + "=" * 60)
print(f"Claim ID para ver en browser: {claim_id}")
print(f"URL: http://127.0.0.1:5000/cms1500/{claim_id}")
print("=" * 60)