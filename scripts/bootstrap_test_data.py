import sqlite3

DB_PATH = "storage/lifetrack.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("🔗 Conectado a DB")

# -------------------------
# Provider Settings
# -------------------------
cur.execute("SELECT COUNT(*) FROM provider_settings")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO provider_settings (
            signature, active
        ) VALUES (
            'Signature on File', 1
        )
    """)
    print("✅ provider_settings creado")
else:
    print("ℹ️ provider_settings ya existe")

# -------------------------
# Patient
# -------------------------
cur.execute("SELECT COUNT(*) FROM patients")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO patients (
            first_name, last_name, date_of_birth
        ) VALUES (
            'Test', 'Paciente', '1990-01-01'
        )
    """)
    print("✅ patient creado")

# -------------------------
# Coverage
# -------------------------
cur.execute("SELECT COUNT(*) FROM coverages")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO coverages (
            patient_id, insurer_name, plan_name,
            policy_number, start_date
        ) VALUES (
            1, 'TestInsurer', 'TestPlan',
            'P1', '2026-01-01'
        )
    """)
    print("✅ coverage creado")

# -------------------------
# Claim
# -------------------------
cur.execute("SELECT COUNT(*) FROM claims")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO claims (
            patient_id, coverage_id, status
        ) VALUES (
            1, 1, 'draft'
        )
    """)
    print("✅ claim creado")

# -------------------------
# Service (CMS-1500 real)
# -------------------------
cur.execute("SELECT COUNT(*) FROM services")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO services (
            claim_id,
            service_date,
            place_of_service_24b,
            emergency_24c,
            cpt_code,
            diagnosis_pointer_24e,
            charge_amount_24f,
            units_24g,
            outside_lab_20,
            lab_charges_20
        ) VALUES (
            1,
            '2026-02-05',
            '11',
            0,
            '90834',
            'A',
            150.00,
            1,
            0,
            NULL
        )
    """)
    print("✅ service creado")



conn.commit()
conn.close()

print("🎉 bootstrap_test_data finalizado correctamente")
