import sqlite3

DB_PATH = "storage/lifetrack.db"

# =========================
# Conexión a la base de datos
# =========================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("🔗 Conectado a DB")

# =========================
# Provider Settings (31–33)
# =========================
cur.execute("SELECT COUNT(*) FROM provider_settings")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO provider_settings (
            signature,
            active
        ) VALUES (
            'Signature on File',
            1
        )
    """)
    print("✅ provider_settings creado")
else:
    print("ℹ️ provider_settings ya existe")

# =========================
# Patient (2,3,8)
# =========================
cur.execute("SELECT COUNT(*) FROM patients")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO patients (
            first_name,
            last_name,
            date_of_birth,
            sex
        ) VALUES (
            'Test',
            'Paciente',
            '1990-01-01',
            'U'
        )
    """)
    print("✅ patient creado")
else:
    print("ℹ️ patient ya existe")

# =========================
# Coverage (1,1a,4,6,7,9,11)
# =========================
cur.execute("SELECT COUNT(*) FROM coverages")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO coverages (
            patient_id,
            insurer_name,
            plan_name,
            insured_id,
            policy_number,
            relationship_to_insured,
            start_date
        ) VALUES (
            1,
            'TestInsurer',
            'TestPlan',
            'I1',
            'P1',
            'self',
            '2026-01-01'
        )
    """)
    print("✅ coverage creado")
else:
    print("ℹ️ coverage ya existe")

# =========================
# Claim (10,14–23,26,27)
# =========================
cur.execute("SELECT COUNT(*) FROM claims")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO claims (
            patient_id,
            coverage_id,
            status,
            accept_assignment_27
        ) VALUES (
            1,
            1,
            'draft',
            1
        )
    """)
    print("✅ claim creado")
else:
    print("ℹ️ claim ya existe")

# =========================
# Service (24A–24J + 20)
# =========================
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
            rendering_npi_24j,
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
            NULL,
            0,
            NULL
        )
    """)
    print("✅ service creado")
else:
    print("ℹ️ service ya existe")

# =========================
# Commit y cierre
# =========================
conn.commit()
conn.close()

print("🎉 bootstrap_test_data finalizado correctamente")
