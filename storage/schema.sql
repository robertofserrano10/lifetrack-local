PRAGMA foreign_keys = ON;

-- =========================
-- Provider Settings (GLOBAL) — 31–33
-- =========================
CREATE TABLE IF NOT EXISTS provider_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 31 Signature
    signature TEXT NOT NULL DEFAULT 'Signature on File',
    signature_date TEXT,

    -- 32 Service Facility Location
    facility_name TEXT,
    facility_address TEXT,
    facility_city TEXT,
    facility_state TEXT,
    facility_zip TEXT,

    -- 33 Billing Provider
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
-- Patients — 2, 3, 8
-- =========================
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 2 Patient Name
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,

    -- 3 DOB / Sex
    date_of_birth TEXT NOT NULL,
    sex TEXT CHECK (sex IN ('M','F','U')) DEFAULT 'U',

    -- 8 Patient Status
    marital_status TEXT,      -- single / married / other
    employment_status TEXT,   -- employed / unemployed
    student_status TEXT,      -- full-time / part-time / none

    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================
-- Coverages — 1, 1a, 4, 6, 7, 9, 11
-- =========================
CREATE TABLE IF NOT EXISTS coverages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,

    -- 1 Insurance Type / Plan
    insurer_name TEXT NOT NULL,
    plan_name TEXT NOT NULL,

    -- 1a Insured ID
    insured_id TEXT,

    -- 4 Insured Name
    insured_first_name TEXT,
    insured_last_name  TEXT,

    -- 6 Relationship to Insured
    relationship_to_insured TEXT CHECK (
        relationship_to_insured IN ('self','spouse','child','other')
    ) DEFAULT 'self',

    -- 7 Insured Address
    insured_address TEXT,
    insured_city TEXT,
    insured_state TEXT,
    insured_zip TEXT,

    -- 9 Other Insured (9a–9d)
    other_insured_name TEXT,
    other_insured_policy TEXT,
    other_insured_dob TEXT,
    other_insured_sex TEXT,

    -- 11 Policy / Group
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
-- Claims — 10, 14–23, 26, 27
-- =========================
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    coverage_id INTEGER NOT NULL,

    claim_number TEXT,
    status TEXT NOT NULL DEFAULT 'draft',

    -- 10 Condition Related To
    related_employment_10a INTEGER NOT NULL DEFAULT 0,
    related_auto_10b INTEGER NOT NULL DEFAULT 0,
    related_other_10c INTEGER NOT NULL DEFAULT 0,
    related_state_10d TEXT,

    -- 14–16 Dates
    date_current_illness_14 TEXT,
    other_date_15 TEXT,
    unable_work_from_16 TEXT,
    unable_work_to_16 TEXT,

    -- 17 Referring Provider
    referring_provider_name TEXT,
    referring_provider_npi TEXT,

    -- 18 Hospitalization
    hosp_from_18 TEXT,
    hosp_to_18 TEXT,

    -- 19 Reserved for Local Use
    reserved_local_use_19 TEXT,

    -- 22 Resubmission
    resubmission_code_22 TEXT,
    original_ref_no_22 TEXT,

    -- 23 Prior Authorization
    prior_authorization_23 TEXT,

    -- 26 Patient Account No
    patient_account_no_26 TEXT,

    -- 27 Accept Assignment
    accept_assignment_27 INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (coverage_id) REFERENCES coverages(id)
);

-- =========================
-- Services — 24A–24J + 20
-- =========================
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,

    -- 24A Date(s) of Service
    service_date TEXT NOT NULL,

    -- 24B Place of Service
    place_of_service_24b TEXT,

    -- 24C EMG
    emergency_24c INTEGER NOT NULL DEFAULT 0,

    -- 24D Procedures / CPT
    cpt_code TEXT NOT NULL,
    modifier1 TEXT,
    modifier2 TEXT,
    modifier3 TEXT,
    modifier4 TEXT,

    -- 24E Diagnosis Pointer
    diagnosis_pointer_24e TEXT,

    -- 24F Charges
    charge_amount_24f REAL NOT NULL,

    -- 24G Units
    units_24g INTEGER NOT NULL,

    -- 24H EPSDT / Family Plan
    epsdt_24h TEXT,

    -- 24I ID Qualifier
    id_qualifier_24i TEXT,

    -- 24J Rendering Provider NPI
    rendering_npi_24j TEXT,

    -- 20 Outside Lab (SERVICE-LEVEL)
    outside_lab_20 INTEGER NOT NULL DEFAULT 0,
    lab_charges_20 REAL,

    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES claims(id)
);

-- =========================
-- Charges (Financial Core)
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
-- Applications (EOB Lines)
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
-- CMS-1500 Snapshots (Immutable)
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
