import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "storage/lifetrack.db"
SCHEMA_PATH = "storage/schema.sql"

# =========================
# Crear DB y ejecutar schema.sql automáticamente
# =========================

db_exists = os.path.exists(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

if not db_exists:
    print("📦 Base de datos no existe. Creando y ejecutando schema.sql...")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)
    print("✅ schema.sql ejecutado correctamente")
else:
    print("ℹ️ Base de datos ya existe")

print("🔗 Conectado a DB")

# =========================
# Usuario inicial (ETAPA H8-1)
# =========================
cur.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='users'
""")
if not cur.fetchone():
    raise RuntimeError("La tabla 'users' no existe. Verifica storage/schema.sql.")

cur.execute("SELECT COUNT(*) FROM users")
if cur.fetchone()[0] == 0:
    password_hash = generate_password_hash("admin123")

    cur.execute("""
        INSERT INTO users (
            username,
            password_hash,
            role,
            active
        ) VALUES (?, ?, ?, 1)
    """, ("admin", password_hash, "ADMIN"))

    print("✅ usuario ADMIN creado (user: admin / pass: admin123)")
else:
    print("ℹ️ usuarios ya existen")

# =========================
# Provider Settings
# =========================
cur.execute("SELECT COUNT(*) FROM provider_settings")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO provider_settings (
            signature,
            active
        ) VALUES ('Signature on File', 1)
    """)
    print("✅ provider_settings creado")
else:
    print("ℹ️ provider_settings ya existe")

# =========================
# Patient
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
# Coverage
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
# Claim
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
# Service
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

conn.commit()
conn.close()

print("🎉 bootstrap_test_data finalizado correctamente")