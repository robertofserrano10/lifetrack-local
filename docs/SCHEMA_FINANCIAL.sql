-- FASE F2 — Esquema Financiero (LifeTrack)
-- Aislado del snapshot CMS-1500

PRAGMA foreign_keys = ON;

-- ===== Charges =====
CREATE TABLE IF NOT EXISTS charges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id INTEGER NOT NULL,
  snapshot_hash TEXT NOT NULL,
  service_id INTEGER,
  amount NUMERIC NOT NULL CHECK (amount >= 0),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_charges_claim
  ON charges (claim_id);

CREATE INDEX IF NOT EXISTS idx_charges_snapshot
  ON charges (snapshot_hash);

-- ===== Payments =====
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL CHECK (source IN ('patient','insurer','other')),
  method TEXT NOT NULL CHECK (method IN ('cash','check','eft','credit','other')),
  reference TEXT,
  amount NUMERIC NOT NULL CHECK (amount >= 0),
  received_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ===== Applications =====
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payment_id INTEGER NOT NULL,
  charge_id INTEGER NOT NULL,
  amount_applied NUMERIC NOT NULL CHECK (amount_applied >= 0),
  applied_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (payment_id) REFERENCES payments(id),
  FOREIGN KEY (charge_id) REFERENCES charges(id)
);

CREATE INDEX IF NOT EXISTS idx_applications_payment
  ON applications (payment_id);

CREATE INDEX IF NOT EXISTS idx_applications_charge
  ON applications (charge_id);
