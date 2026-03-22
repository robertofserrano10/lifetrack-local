"""
E2E INTEGRATION TEST — FULL PATIENT FLOW
LifeTrack — Psynántisi — Puerto Rico
2026-03-22

Tests the complete: Patient → Coverage → Appointment → CheckIn →
  Encounter → Note → Sign → Ready4Billing → Claim → Service →
  Scrubber → Snapshot → CMS-1500 Verification

DO NOT MODIFY APPLICATION SOURCE FILES.
This script creates test records in the DB only.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")

print("=" * 70)
print("LIFETRACK — E2E INTEGRATION TEST — FULL PATIENT FLOW")
print(f"Date: {today}  |  Run at: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

step_results = []   # list of (step_num, desc, passed, detail)
passed = 0
failed = 0
current_step = 0
current_desc = ""


def step(n, desc):
    global current_step, current_desc
    current_step = n
    current_desc = desc
    print(f"\n── Step {n:02d}: {desc}")


def ok(msg):
    global passed
    passed += 1
    step_results.append((current_step, current_desc, True, msg))
    print(f"  ✅ OK  — {msg}")


def err(msg):
    global failed
    failed += 1
    step_results.append((current_step, current_desc, False, msg))
    print(f"  ❌ ERR — {msg}")


# Keep handles for later steps
patient_id = None
coverage_id = None
appt_id = None
session_id = None
copago_payment_id = None
encounter_id = None
note_id = None
claim_id = None
service_id = None
charge_id = None
snap_wrapper = None


# ══════════════════════════════════════════════════════════
# PRE-FLIGHT: ensure provider_settings are complete
# (required for scrubber to pass — not modifying source files)
# ══════════════════════════════════════════════════════════
print("\n── Pre-flight: Provider Settings")
try:
    from app.db.provider_settings import get_provider_settings, update_provider_settings
    ps = get_provider_settings()
    needs_update = {}
    if not ps.get("billing_npi"):
        needs_update["billing_npi"] = "1234567890"
    if not ps.get("billing_tax_id"):
        needs_update["billing_tax_id"] = "66-1234567"
    if not ps.get("billing_name"):
        needs_update["billing_name"] = "Psynántisi — Dra. Test"
    if not ps.get("facility_name"):
        needs_update["facility_name"] = "Psynántisi Psychology"
    if not ps.get("facility_address"):
        needs_update["facility_address"] = "100 Calle Fortaleza"
    if not ps.get("facility_city"):
        needs_update["facility_city"] = "San Juan"
    if not ps.get("facility_state"):
        needs_update["facility_state"] = "PR"
    if not ps.get("facility_zip"):
        needs_update["facility_zip"] = "00901"
    if needs_update:
        update_provider_settings(**needs_update)
        print(f"  ℹ️  Provider settings updated: {list(needs_update.keys())}")
    else:
        print(f"  ℹ️  Provider settings OK: NPI={ps['billing_npi']}, Tax={ps['billing_tax_id']}")
except Exception as e:
    print(f"  ⚠️  Provider settings setup failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 1: Create patient with ALL fields
# ══════════════════════════════════════════════════════════
step(1, "Create patient with all fields (name, DOB, sex, address, city, state, zip, phone, marital_status, employment_status)")
try:
    from app.db.patients import create_patient, get_patient_by_id
    patient_id = create_patient(
        first_name="Ana",
        last_name="Colón",
        date_of_birth="1985-06-15",
        sex="F",
        marital_status="married",
        employment_status="employed",
        address="123 Calle Sol",
        city="San Juan",
        state="PR",
        zip_code="00901",
        phone="787-555-1234",
    )
    p = get_patient_by_id(patient_id)
    assert p["first_name"] == "Ana", f"first_name mismatch: {p['first_name']}"
    assert p["last_name"] == "Colón", f"last_name mismatch: {p['last_name']}"
    assert p["date_of_birth"] == "1985-06-15"
    assert p["sex"] == "F"
    assert p["address"] == "123 Calle Sol"
    assert p["city"] == "San Juan"
    assert p["state"] == "PR"
    assert p["zip_code"] == "00901"
    assert p["phone"] == "787-555-1234"
    assert p["marital_status"] == "married"
    assert p["employment_status"] == "employed"
    ok(f"Patient ID={patient_id}  |  {p['last_name']}, {p['first_name']}  |  DOB={p['date_of_birth']}  |  {p['city']}, {p['state']} {p['zip_code']}")
except Exception as e:
    err(f"Step 1 failed: {e}")
    patient_id = None


# ══════════════════════════════════════════════════════════
# STEP 2: Create coverage with all fields
# ══════════════════════════════════════════════════════════
step(2, "Create coverage with all fields (insurer, plan, policy, insured name, relationship=self, address, referral_required=0)")
try:
    from app.db.coverages import create_coverage, get_coverage_by_id
    from app.db.connection import get_connection
    coverage_id = create_coverage(
        patient_id=patient_id,
        insurer_name="Triple-S Salud",
        plan_name="Vital Plus",
        policy_number="TSS-E2E-2026",
        group_number="GRP-E2E-001",
        insured_id="TSS-INS-9999",
        start_date="2026-01-01",
        end_date=None,
        insured_first_name="Ana",
        insured_last_name="Colón",
        relationship_to_insured="self",
        insured_address="123 Calle Sol",
        insured_city="San Juan",
        insured_state="PR",
        insured_zip="00901",
        other_health_plan_11d=0,
    )
    cov = get_coverage_by_id(coverage_id)
    # Verify referral_required=0 (default)
    with get_connection() as conn:
        row = conn.execute("SELECT referral_required FROM coverages WHERE id=?", (coverage_id,)).fetchone()
        ref_req = row["referral_required"] if row else -1
    assert cov["insurer_name"] == "Triple-S Salud"
    assert cov["plan_name"] == "Vital Plus"
    assert cov["policy_number"] == "TSS-E2E-2026"
    assert cov["relationship_to_insured"] == "self"
    assert cov["insured_first_name"] == "Ana"
    assert cov["insured_address"] == "123 Calle Sol"
    assert ref_req == 0, f"referral_required={ref_req} (expected 0)"
    ok(f"Coverage ID={coverage_id}  |  {cov['insurer_name']} / {cov['plan_name']}  |  policy={cov['policy_number']}  |  relationship=self  |  referral_required=0")
except Exception as e:
    err(f"Step 2 failed: {e}")
    coverage_id = None


# ══════════════════════════════════════════════════════════
# STEP 3: Create appointment for today
# ══════════════════════════════════════════════════════════
step(3, "Create appointment for today")
try:
    from app.db.appointments import create_appointment, get_appointments_by_patient
    appt_id = create_appointment(
        patient_id=patient_id,
        scheduled_date=today,
        scheduled_time="10:00",
        service_type="Seguimiento",
        notes="E2E integration test appointment",
        created_by="test_e2e",
    )
    appts = get_appointments_by_patient(patient_id)
    appt = next((a for a in appts if a["id"] == appt_id), None)
    assert appt is not None, "Appointment not found after creation"
    assert appt["scheduled_date"] == today
    assert appt["status"] == "SCHEDULED"
    ok(f"Appointment ID={appt_id}  |  date={appt['scheduled_date']}  |  time={appt['scheduled_time']}  |  status={appt['status']}")
except Exception as e:
    err(f"Step 3 failed: {e}")
    appt_id = None


# ══════════════════════════════════════════════════════════
# STEP 4: Create visit_session with all check-in fields
# ══════════════════════════════════════════════════════════
step(4, "Create visit_session: eligibility_verified=1, copago=20.00/cash, referral_on_file=0, docs=hipaa+consent")
try:
    from app.db.payments import create_payment
    from app.db.visit_sessions import create_visit_session, update_visit_status, get_session_by_id

    # 1. Create copago payment
    copago_payment_id = create_payment(
        amount=20.00,
        method="cash",
        reference="COPAGO-E2E-TEST",
        received_date=today,
    )

    # 2. Create visit session with all check-in data
    documents = json.dumps({"hipaa": True, "consent": True})
    session_id = create_visit_session(
        patient_id=patient_id,
        appointment_date=today,
        notes="E2E test — check-in completo",
        created_by="recepcion_e2e",
        eligibility_verified=1,
        copago_amount=20.00,
        copago_payment_id=copago_payment_id,
        referral_on_file=0,
        documents_signed=documents,
    )

    # 3. Transition: ARRIVED → CHECKED_IN → WAITING
    update_visit_status(session_id, "CHECKED_IN")
    update_visit_status(session_id, "WAITING")

    ok(f"Visit session ID={session_id}  |  copago_payment_id={copago_payment_id}  |  docs=hipaa+consent  |  → WAITING")
except Exception as e:
    err(f"Step 4 failed: {e}")
    session_id = None
    copago_payment_id = None


# ══════════════════════════════════════════════════════════
# STEP 5: Verify visit_session status=WAITING, copago_payment_id set
# ══════════════════════════════════════════════════════════
step(5, "Verify visit_session: status=WAITING and copago_payment_id is set")
try:
    visit = get_session_by_id(session_id)
    assert visit["status"] == "WAITING", f"Expected WAITING, got {visit['status']}"
    assert visit["copago_payment_id"] is not None, "copago_payment_id is None"
    assert visit["copago_payment_id"] == copago_payment_id, f"copago_payment_id mismatch"
    assert visit["eligibility_verified"] == 1, f"eligibility_verified={visit['eligibility_verified']}"
    assert visit["copago_amount"] == 20.00, f"copago_amount={visit['copago_amount']}"
    docs = json.loads(visit["documents_signed"])
    assert docs.get("hipaa") is True, f"hipaa not True: {docs}"
    assert docs.get("consent") is True, f"consent not True: {docs}"
    ok(f"status={visit['status']}  |  copago_payment_id={visit['copago_payment_id']}  |  eligibility=1  |  copago_amount=$20.00  |  hipaa=✓  consent=✓")
except Exception as e:
    err(f"Step 5 failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 6: Create encounter
# ══════════════════════════════════════════════════════════
step(6, "Create encounter for patient")
try:
    from app.db.encounters import create_encounter, get_encounter_by_id
    update_visit_status(session_id, "IN_SESSION")
    encounter_id = create_encounter(
        patient_id=patient_id,
        encounter_date=today,
        status="OPEN",
        provider_id=None,
    )
    enc = get_encounter_by_id(encounter_id)
    assert enc is not None
    assert enc["patient_id"] == patient_id
    assert enc["encounter_date"] == today
    assert enc["status"] == "OPEN"
    ok(f"Encounter ID={encounter_id}  |  patient_id={patient_id}  |  date={today}  |  status=OPEN")
except Exception as e:
    err(f"Step 6 failed: {e}")
    encounter_id = None


# ══════════════════════════════════════════════════════════
# STEP 7: Create progress note
# ══════════════════════════════════════════════════════════
step(7, "Create progress note (SOAP) for encounter")
try:
    from app.db.progress_notes import create_note, get_note_by_id, sign_note
    note_id = create_note(
        encounter_id=encounter_id,
        patient_name="Ana Colón",
        record_number="RN-E2E-001",
        date_of_service=today,
        start_time="10:00",
        end_time="10:50",
        service_type="Individual",
        cpt_code="90837",
        diagnosis_code="F41.1",
        provider_name="Dra. E2E Prueba",
        provider_credentials="PhD, LMHC",
        subjective="Paciente reporta ansiedad generalizada. Dificultad para dormir 5/7 días.",
        objective="Apariencia apropiada. Contacto visual adecuado. Discurso coherente y fluido.",
        assessment="Trastorno de ansiedad generalizada (F41.1) con curso favorable.",
        plan="Continuar TCC. Tarea: registro de pensamientos automáticos. Próxima cita en 2 semanas.",
    )
    note = get_note_by_id(note_id)
    assert note is not None
    assert note["encounter_id"] == encounter_id
    assert note["signed"] == 0, f"Note should not be signed yet, got signed={note['signed']}"
    ok(f"Note ID={note_id}  |  encounter_id={encounter_id}  |  status=draft  |  signed=0")
except Exception as e:
    err(f"Step 7 failed: {e}")
    note_id = None


# ══════════════════════════════════════════════════════════
# STEP 8: Sign the note
# ══════════════════════════════════════════════════════════
step(8, "Sign the progress note")
try:
    sign_note(note_id)
    ok(f"Note {note_id} signed successfully")
except Exception as e:
    err(f"Step 8 failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 9: Verify note is signed=1
# ══════════════════════════════════════════════════════════
step(9, "Verify note signed=1")
try:
    note = get_note_by_id(note_id)
    assert note["signed"] == 1, f"Expected signed=1, got {note['signed']}"
    assert note["status"] == "signed", f"Expected status=signed, got {note['status']}"
    assert note["signed_at"] is not None, "signed_at is None"
    ok(f"signed=1  |  status={note['status']}  |  signed_at={note['signed_at'][:16]}")
except Exception as e:
    err(f"Step 9 failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 10: Mark encounter ready_for_billing
# ══════════════════════════════════════════════════════════
step(10, "Mark encounter ready_for_billing (validation: signed note + no referral required)")
try:
    from app.db.encounters import mark_ready_for_billing
    mark_ready_for_billing(encounter_id=encounter_id, marked_by="facturador_e2e")
    enc = get_encounter_by_id(encounter_id)
    assert enc["ready_for_billing"] == 1, f"ready_for_billing={enc['ready_for_billing']}"
    assert enc["ready_for_billing_at"] is not None
    assert enc["ready_for_billing_by"] == "facturador_e2e"
    ok(f"ready_for_billing=1  |  marked_by={enc['ready_for_billing_by']}  |  at={enc['ready_for_billing_at'][:16]}")
except Exception as e:
    err(f"Step 10 failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 11: Create claim from encounter
# ══════════════════════════════════════════════════════════
step(11, "Create claim from encounter (encounter_id must be set on claim)")
try:
    from app.db.claims import create_claim, get_claim_by_id
    claim_id = create_claim(
        patient_id=patient_id,
        coverage_id=coverage_id,
        encounter_id=encounter_id,
    )
    claim = get_claim_by_id(claim_id)
    assert claim is not None
    assert claim["encounter_id"] == encounter_id, f"encounter_id mismatch: {claim['encounter_id']} != {encounter_id}"
    assert claim["patient_id"] == patient_id
    assert claim["coverage_id"] == coverage_id
    assert claim["status"] == "DRAFT"
    assert claim["claim_number"] == f"CLM{claim_id:06d}"
    ok(f"Claim ID={claim_id}  |  {claim['claim_number']}  |  encounter_id={claim['encounter_id']}  |  status=DRAFT")
except Exception as e:
    err(f"Step 11 failed: {e}")
    claim_id = None


# ══════════════════════════════════════════════════════════
# STEP 12: Add service CPT=90837 + charge
# ══════════════════════════════════════════════════════════
step(12, "Add service: CPT=90837, date=today, charge=150.00, units=1, diagnosis_code=F41.1")
try:
    from app.db.services import create_service
    from app.db.charges import create_charge
    from app.db.connection import get_connection

    service_id = create_service(
        claim_id=claim_id,
        service_date=today,
        cpt_code="90837",
        units=1,
        diagnosis_code="F41.1",
        description="Psychotherapy 53+ min — E2E test",
        charge_amount_24f=150.00,
        place_of_service_24b="11",
        diagnosis_pointer_24e="A",
    )

    # Create charge in financial layer
    charge_id = create_charge(service_id=service_id, amount=150.00)

    # Verify
    with get_connection() as conn:
        svc = dict(conn.execute("SELECT * FROM services WHERE id=?", (service_id,)).fetchone())
        chg = dict(conn.execute("SELECT * FROM charges WHERE id=?", (charge_id,)).fetchone())

    assert svc["cpt_code"] == "90837"
    assert svc["claim_id"] == claim_id
    assert float(svc["charge_amount_24f"]) == 150.00
    assert int(svc["units_24g"]) == 1
    assert float(chg["amount"]) == 150.00
    assert chg["service_id"] == service_id

    ok(f"Service ID={service_id}  |  CPT=90837  |  charge_amount_24f=$150.00  |  units=1  |  Charge ID={charge_id} ($150.00)")
except Exception as e:
    err(f"Step 12 failed: {e}")
    service_id = None
    charge_id = None


# ══════════════════════════════════════════════════════════
# STEP 13: Add diagnosis_1=F41.1 to claim
# ══════════════════════════════════════════════════════════
step(13, "Add diagnosis_1=F41.1 to claim (casilla 21A)")
try:
    from app.db.claims import update_claim_cms_fields
    update_claim_cms_fields(
        claim_id=claim_id,
        diagnosis_1="F41.1",
    )
    claim = get_claim_by_id(claim_id)
    assert claim["diagnosis_1"] == "F41.1", f"Expected F41.1, got {claim['diagnosis_1']}"
    ok(f"diagnosis_1={claim['diagnosis_1']} set on claim {claim_id}")
except Exception as e:
    err(f"Step 13 failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 14: Run claim scrubber
# ══════════════════════════════════════════════════════════
step(14, "Run claim scrubber — expect ready=True with no blocking errors")
scrub_result = None
try:
    from app.db.claim_scrubber import scrub_claim
    scrub_result = scrub_claim(claim_id)
    if scrub_result["ready"]:
        ok(f"Scrubber ready=True  |  errors=0  |  warnings={len(scrub_result['warnings'])}")
        for w in scrub_result.get("warnings", []):
            print(f"    ⚠️  {w}")
    else:
        err(f"Scrubber ready=False  |  errors={len(scrub_result['errors'])}")
        for e_msg in scrub_result["errors"]:
            print(f"    ❌ {e_msg}")
        for w in scrub_result.get("warnings", []):
            print(f"    ⚠️  {w}")
except Exception as e:
    err(f"Step 14 failed: {e}")


# ══════════════════════════════════════════════════════════
# STEP 15: Generate CMS-1500 snapshot
# ══════════════════════════════════════════════════════════
step(15, "Generate CMS-1500 snapshot")
snapshot_result = None
try:
    from app.db.cms1500_snapshot import generate_cms1500_snapshot
    snapshot_result = generate_cms1500_snapshot(claim_id)
    assert snapshot_result is not None
    assert snapshot_result.get("snapshot_hash")
    assert snapshot_result.get("version_number") == 1
    ok(f"Snapshot generated  |  version={snapshot_result['version_number']}  |  hash={snapshot_result['snapshot_hash'][:16]}...")
except Exception as e:
    err(f"Step 15 failed: {e}")
    snapshot_result = None


# ══════════════════════════════════════════════════════════
# STEP 16: Verify snapshot hash exists
# ══════════════════════════════════════════════════════════
step(16, "Verify snapshot hash exists and is valid SHA-256")
snap_wrapper = None
try:
    from app.db.cms1500_snapshot import get_latest_snapshot_by_claim
    snap_wrapper = get_latest_snapshot_by_claim(claim_id)
    assert snap_wrapper is not None, "No snapshot found in DB"
    h = snap_wrapper["snapshot_hash"]
    assert h is not None, "snapshot_hash is None"
    assert len(h) == 64, f"Hash length {len(h)} != 64 (not SHA-256)"
    # Verify it's hex
    int(h, 16)
    ok(f"Hash: {h[:20]}...{h[-8:]}  |  length=64 chars  |  SHA-256 valid")
except Exception as e:
    err(f"Step 16 failed: {e}")
    snap_wrapper = None


# ══════════════════════════════════════════════════════════
# STEP 17: Verify all CMS-1500 fields
# ══════════════════════════════════════════════════════════
step(17, "Verify all CMS-1500 fields: patient, DOB, address, insurance, dx 21A, service 24D, NPI, total charge")
try:
    assert snap_wrapper is not None, "No snapshot to verify"
    s = snap_wrapper["snapshot"]

    cms_counts = [0, 0]  # [pass, fail]

    def chk(casilla, desc, val, expected=None):
        is_present = val is not None and str(val).strip() not in ('', 'None', 'null')
        if expected is not None:
            matches = str(val) == str(expected)
            if is_present and matches:
                cms_counts[0] += 1
                print(f"    ✅ CMS-{casilla:4s} {desc:30s} = {val}")
            else:
                cms_counts[1] += 1
                print(f"    ❌ CMS-{casilla:4s} {desc:30s} expected='{expected}' got='{val}'")
        else:
            if is_present:
                cms_counts[0] += 1
                print(f"    ✅ CMS-{casilla:4s} {desc:30s} = {val}")
            else:
                cms_counts[1] += 1
                print(f"    ❌ CMS-{casilla:4s} {desc:30s} = EMPTY/MISSING")

    pat = s["patient"]
    ins = s["insurance"]
    dx  = s["diagnoses"]
    svc = s["services"][0] if s["services"] else {}
    pro = s["provider"]

    print(f"  Patient:")
    chk("2",   "Patient name",          f"{pat['last_name']}, {pat['first_name']}", "Colón, Ana")
    chk("3a",  "Date of birth",         pat["date_of_birth"],                       "1985-06-15")
    chk("3b",  "Sex",                   pat["sex"],                                 "F")
    chk("5",   "Patient address",       pat["address"],                             "123 Calle Sol")
    chk("5b",  "City",                  pat["city"],                                "San Juan")
    chk("5c",  "State",                 pat["state"],                               "PR")
    chk("5d",  "ZIP",                   pat["zip_code"],                            "00901")
    chk("5e",  "Phone",                 pat["phone"],                               "787-555-1234")

    print(f"  Insurance:")
    chk("1",   "Insurer name",          ins["insurer_name"],          "Triple-S Salud")
    chk("1a",  "Plan name",             ins["plan_name"],             "Vital Plus")
    chk("1b",  "Insured ID",            ins["insured_id"],            "TSS-INS-9999")
    chk("4",   "Insured name",          ins["insured_name"],          "Ana Colón")
    chk("6",   "Relationship",          ins["relationship_to_insured"],"self")
    chk("11",  "Policy number",         ins["policy_number"],         "TSS-E2E-2026")
    chk("7",   "Insured address",       ins["insured_address"]["address"], "123 Calle Sol")

    print(f"  Diagnoses:")
    chk("21A", "Diagnosis code",        dx["A"],                      "F41.1")

    print(f"  Services:")
    chk("24A", "Service date",          svc.get("service_date"),      today)
    chk("24D", "CPT code",              svc.get("cpt_code"),          "90837")
    chk("24F", "Charge amount",         svc.get("charge_amount_24f"), 150.0)
    chk("24G", "Units",                 svc.get("units"),             1)

    print(f"  Provider:")
    chk("33",  "Billing name",          pro["billing"]["name"])
    chk("33b", "Billing NPI",           pro["billing"]["npi"])
    chk("25",  "Tax ID",                pro["billing"]["tax_id"])
    chk("32",  "Facility name",         pro["facility"]["name"])

    print(f"  Totals:")
    chk("28",  "Total charge",          s["totals"]["total_charge"],  150.0)

    if cms_counts[1] == 0:
        ok(f"All {cms_counts[0]} CMS-1500 fields verified correctly")
    else:
        err(f"{cms_counts[1]} CMS-1500 field(s) failed  |  {cms_counts[0]} passed")

except Exception as e:
    err(f"Step 17 failed: {e}")
    import traceback; traceback.print_exc()


# ══════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"  Steps PASSED: {passed}")
print(f"  Steps FAILED: {failed}")
print(f"  Total steps:  {passed + failed}")

if claim_id:
    print(f"\n  Claim:        http://127.0.0.1:5000/admin/claims/{claim_id}")
    print(f"  CMS-1500:     http://127.0.0.1:5000/cms1500/{claim_id}")
    print(f"  Patient:      http://127.0.0.1:5000/admin/patients/{patient_id}")
    print(f"  Encounter:    http://127.0.0.1:5000/admin/encounters/{encounter_id}")

if failed == 0:
    print("\n  ✅ ALL STEPS PASSED — FLOW COMPLETE")
else:
    print(f"\n  ❌ {failed} STEP(S) FAILED:")
    for sn, sdesc, spassed, smsg in step_results:
        if not spassed:
            print(f"     • Step {sn:02d} [{sdesc[:40]}]: {smsg}")

print("=" * 70)
