PRAGMA foreign_keys = ON;

-- =========================
-- Users (Auth Minimal) — H8
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('DRA','RECEPCION','FACTURADOR','ADMIN')),
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- =========================
-- Provider Settings (GLOBAL) — 31–33
-- =========================
CREATE TABLE IF NOT EXISTS provider_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    signature TEXT NOT NULL DEFAULT 'Signature on File',
    signature_date TEXT,

    facility_name TEXT,
    facility_address TEXT,
    facility_city TEXT,
    facility_state TEXT,
    facility_zip TEXT,

    billing_name TEXT,
    billing_npi TEXT,
    billing_tax_id TEXT,
    billing_address TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_zip TEXT,

    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================
-- Patients
-- =========================
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    sex TEXT CHECK (sex IN ('M','F','U')) DEFAULT 'U',
    marital_status TEXT,
    employment_status TEXT,
    student_status TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================
-- Coverages
-- =========================
CREATE TABLE IF NOT EXISTS coverages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    insurer_name TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    insured_id TEXT,
    insured_first_name TEXT,
    insured_last_name  TEXT,
    relationship_to_insured TEXT CHECK (
        relationship_to_insured IN ('self','spouse','child','other')
    ) DEFAULT 'self',
    insured_address TEXT,
    insured_city TEXT,
    insured_state TEXT,
    insured_zip TEXT,
    other_insured_name TEXT,
    other_insured_policy TEXT,
    other_insured_dob TEXT,
    other_insured_sex TEXT,
    policy_number TEXT NOT NULL,
    group_number TEXT,
    other_health_plan_11d INTEGER NOT NULL DEFAULT 0,
    start_date TEXT NOT NULL,
    end_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- =========================
-- Claims
-- =========================
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    coverage_id INTEGER NOT NULL,
    claim_number TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    related_employment_10a INTEGER NOT NULL DEFAULT 0,
    related_auto_10b INTEGER NOT NULL DEFAULT 0,
    related_other_10c INTEGER NOT NULL DEFAULT 0,
    related_state_10d TEXT,
    date_current_illness_14 TEXT,
    other_date_15 TEXT,
    unable_work_from_16 TEXT,
    unable_work_to_16 TEXT,
    referring_provider_name TEXT,
    referring_provider_npi TEXT,
    hosp_from_18 TEXT,
    hosp_to_18 TEXT,
    reserved_local_use_19 TEXT,
    resubmission_code_22 TEXT,
    original_ref_no_22 TEXT,
    prior_authorization_23 TEXT,
    patient_account_no_26 TEXT,
    accept_assignment_27 INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (coverage_id) REFERENCES coverages(id)
);

-- =========================
-- Services
-- =========================
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    service_date TEXT NOT NULL,
    place_of_service_24b TEXT,
    emergency_24c INTEGER NOT NULL DEFAULT 0,
    cpt_code TEXT NOT NULL,
    modifier1 TEXT,
    modifier2 TEXT,
    modifier3 TEXT,
    modifier4 TEXT,
    diagnosis_pointer_24e TEXT,
    charge_amount_24f REAL NOT NULL,
    units_24g INTEGER NOT NULL,
    epsdt_24h TEXT,
    id_qualifier_24i TEXT,
    rendering_npi_24j TEXT,
    outside_lab_20 INTEGER NOT NULL DEFAULT 0,
    lab_charges_20 REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES claims(id)
);

-- =========================
-- Charges
-- =========================
CREATE TABLE IF NOT EXISTS charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- =========================
-- Payments
-- =========================
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    reference TEXT,
    received_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================
-- Applications
-- =========================
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL,
    charge_id INTEGER NOT NULL,
    amount_applied REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (payment_id) REFERENCES payments(id),
    FOREIGN KEY (charge_id) REFERENCES charges(id)
);

-- =========================
-- Adjustments
-- =========================
CREATE TABLE IF NOT EXISTS adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    charge_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (charge_id) REFERENCES charges(id)
);

-- =========================
-- CMS-1500 Snapshots
-- =========================
CREATE TABLE IF NOT EXISTS cms1500_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES claims(id)
);

CREATE INDEX IF NOT EXISTS idx_services_claim ON services(claim_id);
CREATE INDEX IF NOT EXISTS idx_charges_service ON charges(service_id);
CREATE INDEX IF NOT EXISTS idx_applications_charge ON applications(charge_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_charge ON adjustments(charge_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_claim ON cms1500_snapshots(claim_id);