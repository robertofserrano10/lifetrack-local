-- =========================
-- Patients
-- =========================
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Coverages
-- =========================
CREATE TABLE coverages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    insurer_name TEXT NOT NULL,
    plan_name TEXT,
    policy_number TEXT,
    group_number TEXT,
    insured_id TEXT,
    start_date TEXT,
    end_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Claims
-- =========================
CREATE TABLE claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    coverage_id INTEGER NOT NULL,
    claim_number TEXT,
    status TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Services
-- =========================
CREATE TABLE services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    service_date TEXT NOT NULL,
    cpt_code TEXT NOT NULL,
    units INTEGER NOT NULL,
    diagnosis_code TEXT,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =========================
-- Charges
-- =========================
CREATE TABLE charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =========================
-- Payments
-- =========================
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    reference TEXT,
    received_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =========================
-- Applications (EOB)
-- =========================
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL,
    charge_id INTEGER NOT NULL,
    amount_applied REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- =========================
-- CMS-1500 Snapshots
-- =========================
CREATE TABLE cms1500_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
