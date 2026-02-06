PRAGMA foreign_keys = ON;

-- =========================
-- Provider Settings (GLOBAL)
-- =========================
CREATE TABLE IF NOT EXISTS provider_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Signatures (31)
    signature TEXT NOT NULL DEFAULT 'Signature on File',
    signature_date TEXT,

    -- Facility (32)
    facility_name TEXT,
    facility_address TEXT,
    facility_city TEXT,
    facility_state TEXT,
    facility_zip TEXT,

    -- Billing (33)
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
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
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
    policy_number TEXT NOT NULL,
    group_number TEXT,
    insured_id TEXT,
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

    -- NEW (CMS-1500 fields)
    -- Box 17 (Referring Provider)
    referring_provider_name TEXT,
    referring_provider_npi TEXT,

    -- Box 19 (Reserved for Local Use)
    reserved_local_use_19 TEXT,

    -- Box 22 (Resubmission)
    resubmission_code_22 TEXT,
    original_ref_no_22 TEXT,

    -- Box 23 (Prior Authorization)
    prior_authorization_23 TEXT,

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
    claim_id INTEGER,
    service_date TEXT NOT NULL,
    cpt_code TEXT NOT NULL,
    units INTEGER NOT NULL,
    diagnosis_code TEXT NOT NULL,
    description TEXT,

    -- NEW (CMS-1500 box 20 at service-level)
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
-- Applications (EOB lines)
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
-- Adjustments (EOB adjustments / write-offs)
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

-- =========================
-- Indexes
-- =========================
CREATE INDEX IF NOT EXISTS idx_services_claim ON services(claim_id);
CREATE INDEX IF NOT EXISTS idx_charges_service ON charges(service_id);
CREATE INDEX IF NOT EXISTS idx_applications_charge ON applications(charge_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_charge ON adjustments(charge_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_claim ON cms1500_snapshots(claim_id);
