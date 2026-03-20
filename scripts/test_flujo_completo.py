"""
TEST FLUJO COMPLETO — LifeTrack
Prueba todo el flujo de la oficina de extremo a extremo:

1. Paciente llega → Check-in
2. Doctora crea encounter y nota SOAP
3. Facturación crea service, charge, claim
4. Scrubber valida el claim
5. Snapshot CMS-1500 generado
6. Verificación campo por campo

Correr desde lifetrack-local:
  python -m scripts.test_flujo_completo
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")

print("=" * 60)
print("LIFETRACK — TEST FLUJO COMPLETO")
print(f"Fecha: {today} — Puerto Rico")
print("=" * 60)

errors_found = []

def ok(msg): print(f"  ✅ {msg}")
def fail(msg):
    print(f"  ❌ {msg}")
    errors_found.append(msg)
def warn(msg): print(f"  ⚠️  {msg}")
def section(msg): print(f"\n{'─'*50}\n{msg}\n{'─'*50}")

# ─────────────────────────────────────────
# 1. PACIENTE COMPLETO
# ─────────────────────────────────────────
section("1. REGISTRO DE PACIENTE")
from app.db.patients import create_patient, get_patient_by_id

patient_id = create_patient(
    first_name="Carmen",
    last_name="Rosario",
    date_of_birth="1978-04-20",
    sex="F",
    marital_status="married",
    employment_status="employed",
    student_status=None,
    address="45 Calle Luna",
    city="San Juan",
    state="PR",
    zip_code="00901",
    phone="787-555-9876",
)
patient = get_patient_by_id(patient_id)
ok(f"Paciente creado: {patient['last_name']}, {patient['first_name']} (ID {patient_id})")
ok(f"Dirección: {patient['address']}, {patient['city']}, {patient['state']} {patient['zip_code']}")
ok(f"Teléfono: {patient['phone']}")

# ─────────────────────────────────────────
# 2. COVERAGE COMPLETA
# ─────────────────────────────────────────
section("2. COBERTURA DE SEGURO")
from app.db.coverages import create_coverage

coverage_id = create_coverage(
    patient_id=patient_id,
    insurer_name="Triple-S Salud",
    plan_name="Vital",
    policy_number="TSS-2026-001",
    group_number="GRP-PR-001",
    insured_id="TSS12345678",
    start_date="2026-01-01",
    end_date=None,
    insured_first_name="Carmen",
    insured_last_name="Rosario",
    relationship_to_insured="self",
    insured_address="45 Calle Luna",
    insured_city="San Juan",
    insured_state="PR",
    insured_zip="00901",
    other_health_plan_11d=0,
)
ok(f"Coverage creada: Triple-S Salud / Vital (ID {coverage_id})")
ok(f"Póliza: TSS-2026-001 | Grupo: GRP-PR-001")
ok(f"Asegurado: Carmen Rosario (self)")

# ─────────────────────────────────────────
# 3. CHECK-IN (Recepción)
# ─────────────────────────────────────────
section("3. CHECK-IN — RECEPCIÓN")
from app.db.visit_sessions import (
    create_visit_session, update_visit_status,
    get_session_by_id, check_patient_coverage
)

session_id = create_visit_session(
    patient_id=patient_id,
    appointment_date=today,
    notes="Primera visita del año",
    created_by="recepcion",
)
update_visit_status(session_id, "CHECKED_IN")
update_visit_status(session_id, "WAITING")
visit = get_session_by_id(session_id)
ok(f"Visit session creada (ID {session_id})")
ok(f"Status: {visit['status']}")

cov_check = check_patient_coverage(patient_id)
if cov_check['has_coverage']:
    ok(f"Seguro activo: {cov_check['coverage']['insurer_name']}")
else:
    fail("Paciente sin seguro activo")

# ─────────────────────────────────────────
# 4. ENCOUNTER (Doctora llama al paciente)
# ─────────────────────────────────────────
section("4. ENCOUNTER CLÍNICO")
from app.db.encounters import create_encounter

update_visit_status(session_id, "IN_SESSION")
encounter_id = create_encounter(
    patient_id=patient_id,
    encounter_date=today,
    status="OPEN",
    provider_id=None,
)
ok(f"Encounter creado (ID {encounter_id})")
ok(f"Status visita: IN_SESSION")

# ─────────────────────────────────────────
# 5. PROGRESS NOTE (SOAP)
# ─────────────────────────────────────────
section("5. NOTA CLÍNICA SOAP")
from app.db.progress_notes import create_note, sign_note, get_note_by_id

note_id = create_note(
    encounter_id=encounter_id,
    patient_name="Carmen Rosario",
    record_number="RN-2026-001",
    date_of_service=today,
    start_time="09:00",
    end_time="09:50",
    service_type="Individual",
    cpt_code="90837",
    diagnosis_code="F41.1",
    provider_name="Dra. Prueba",
    provider_credentials="PhD",
    subjective="Paciente reporta ansiedad moderada. Dificultad para dormir.",
    objective="Apariencia adecuada, contacto visual normal, discurso coherente.",
    assessment="Trastorno de ansiedad generalizada con progresión positiva.",
    plan="Continuar CBT. Tarea: registro de pensamientos automáticos.",
)
ok(f"Nota SOAP creada (ID {note_id})")

sign_note(note_id)
note = get_note_by_id(note_id)
if note['signed']:
    ok(f"Nota firmada: {note['signed_at'][:16]}")
else:
    fail("Nota no se firmó correctamente")

# ─────────────────────────────────────────
# 6. CLAIM CON DIAGNÓSTICOS
# ─────────────────────────────────────────
section("6. CLAIM")
from app.db.connection import get_connection
from app.db.claims import update_claim_cms_fields

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO claims (patient_id, coverage_id, status, created_at, updated_at)
        VALUES (?, ?, 'DRAFT', datetime('now'), datetime('now'))
    """, (patient_id, coverage_id))
    conn.commit()
    claim_id = cur.lastrowid
    cur.execute("UPDATE claims SET claim_number = ? WHERE id = ?",
                (f"CLM{claim_id:06d}", claim_id))
    conn.commit()

ok(f"Claim creado: CLM{claim_id:06d} (ID {claim_id})")

update_claim_cms_fields(
    claim_id=claim_id,
    diagnosis_1="F41.1",
    diagnosis_2="Z63.0",
)
ok("Diagnósticos: A=F41.1 (Ansiedad Generalizada), B=Z63.0")

# ─────────────────────────────────────────
# 7. SERVICE + CHARGE
# ─────────────────────────────────────────
section("7. SERVICE Y CHARGE")
from app.db.charges import create_charge

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO services (
            claim_id, service_date, cpt_code, units_24g,
            charge_amount_24f, place_of_service_24b,
            diagnosis_pointer_24e, diagnosis_code,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (claim_id, today, "90837", 1, 150.00, "11", "A", "F41.1"))
    conn.commit()
    service_id = cur.lastrowid

charge_id = create_charge(service_id=service_id, amount=150.00)
ok(f"Service: CPT 90837 | Psicoterapia 53+ min | ${150:.2f}")
ok(f"Charge creado (ID {charge_id})")

# ─────────────────────────────────────────
# 8. CLAIM SCRUBBER
# ─────────────────────────────────────────
section("8. CLAIM SCRUBBER")
from app.db.claim_scrubber import scrub_claim

result = scrub_claim(claim_id)

if result['ready']:
    ok("Claim LISTO para generar CMS-1500")
else:
    warn(f"Claim tiene {len(result['errors'])} error(es)")

if result['errors']:
    for e in result['errors']:
        fail(f"ERROR: {e}")

if result['warnings']:
    for w in result['warnings']:
        warn(f"ADVERTENCIA: {w}")

# ─────────────────────────────────────────
# 9. SNAPSHOT CMS-1500
# ─────────────────────────────────────────
section("9. SNAPSHOT CMS-1500")
from app.db.cms1500_snapshot import generate_cms1500_snapshot, get_latest_snapshot_by_claim

try:
    generate_cms1500_snapshot(claim_id)
    snap_wrapper = get_latest_snapshot_by_claim(claim_id)
    s = snap_wrapper["snapshot"]
    ok(f"Snapshot v{s['meta']['version_number']} generado")
    ok(f"Hash: {snap_wrapper['snapshot_hash'][:20]}...")
except Exception as e:
    fail(f"Error generando snapshot: {e}")
    s = None

# ─────────────────────────────────────────
# 10. VERIFICACIÓN CMS-1500 CAMPO POR CAMPO
# ─────────────────────────────────────────
section("10. VERIFICACIÓN CMS-1500 — CAMPOS CRÍTICOS")

if s:
    def check(casilla, desc, val):
        if val and str(val) not in ('', '—', 'None', 'U'):
            ok(f"Casilla {casilla}: {desc} = {val}")
        else:
            fail(f"Casilla {casilla}: {desc} = VACÍO")

    check("2",    "Nombre paciente",     f"{s['patient']['last_name']}, {s['patient']['first_name']}")
    check("3a",   "Fecha nacimiento",    s['patient']['date_of_birth'])
    check("3b",   "Sexo",               s['patient']['sex'])
    check("5",    "Dirección paciente",  s['patient']['address'])
    check("5b",   "Ciudad paciente",     s['patient']['city'])
    check("5d",   "Teléfono",           s['patient']['phone'])
    check("1",    "Plan médico",         s['insurance']['plan_name'])
    check("1a",   "Insured ID",          s['insurance']['insured_id'])
    check("4",    "Nombre asegurado",    s['insurance']['insured_name'])
    check("6",    "Relationship",        s['insurance']['relationship_to_insured'])
    check("7",    "Dir. asegurado",      s['insurance'].get('insured_address', {}).get('address'))
    check("11",   "Póliza",             s['insurance']['policy_number'])
    check("21A",  "Diagnóstico A",       s['diagnoses']['A'])
    check("21B",  "Diagnóstico B",       s['diagnoses']['B'])
    check("24A",  "Fecha servicio",      s['services'][0]['service_date'] if s['services'] else None)
    check("24D",  "CPT Code",           s['services'][0]['cpt_code'] if s['services'] else None)
    check("24F",  "Charge amount",       s['services'][0]['charge_amount_24f'] if s['services'] else None)
    check("25",   "Tax ID",             s['provider']['billing']['tax_id'])
    check("31",   "Firma provider",      s['provider']['signature'])
    check("32",   "Facility",           s['provider']['facility']['name'])
    check("33",   "Billing name",        s['provider']['billing']['name'])
    check("33b",  "Billing NPI",         s['provider']['billing']['npi'])
    check("28",   "Total Charge",        s['totals']['total_charge'])

# ─────────────────────────────────────────
# 11. COMPLETAR VISITA
# ─────────────────────────────────────────
section("11. COMPLETAR VISITA")
update_visit_status(session_id, "COMPLETED")
visit = get_session_by_id(session_id)
ok(f"Visita completada: {visit['completed_time'][:16] if visit['completed_time'] else 'OK'}")

# ─────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)
if errors_found:
    print(f"\n❌ {len(errors_found)} error(es) encontrado(s):")
    for e in errors_found:
        print(f"   • {e}")
else:
    print("\n✅ FLUJO COMPLETO SIN ERRORES")
    print(f"\nClaim ID: {claim_id}")
    print(f"URL CMS-1500: http://127.0.0.1:5000/cms1500/{claim_id}")
    print(f"URL Claim:    http://127.0.0.1:5000/admin/claims/{claim_id}")
    print(f"URL Paciente: http://127.0.0.1:5000/admin/patients/{patient_id}")

print("=" * 60)